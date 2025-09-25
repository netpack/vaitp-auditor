"""
Resource management utilities for VAITP-Auditor.
"""

import atexit
import gc
import os
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from .logging_config import get_logger
from .error_handling import ResourceError, handle_errors


class ResourceManager:
    """
    Manages application resources including files, memory, and cleanup.
    """
    
    def __init__(self):
        self.logger = get_logger('resource_manager')
        self._temp_files: Set[Path] = set()
        self._open_files: Dict[str, Any] = {}
        self._cleanup_callbacks: List[callable] = []
        self._lock = threading.Lock()
        
        # Register cleanup on exit
        atexit.register(self.cleanup_all)
    
    @handle_errors(error_types=(OSError, PermissionError), reraise=False)
    def create_temp_file(
        self, 
        suffix: str = '.tmp', 
        prefix: str = 'vaitp_', 
        directory: Optional[str] = None
    ) -> Optional[Path]:
        """
        Create a temporary file that will be cleaned up automatically.
        
        Args:
            suffix: File suffix/extension.
            prefix: File prefix.
            directory: Directory to create file in (uses system temp if None).
            
        Returns:
            Optional[Path]: Path to created temporary file, or None if failed.
        """
        try:
            if directory is None:
                # Use application-specific temp directory
                temp_dir = Path.home() / '.vaitp_auditor' / 'temp'
                temp_dir.mkdir(parents=True, exist_ok=True)
                directory = str(temp_dir)
            
            # Create temporary file
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=directory)
            os.close(fd)  # Close the file descriptor, we just need the path
            
            temp_file = Path(temp_path)
            
            with self._lock:
                self._temp_files.add(temp_file)
            
            self.logger.debug(f"Created temporary file: {temp_file}")
            return temp_file
            
        except Exception as e:
            self.logger.error(f"Failed to create temporary file: {e}")
            return None
    
    @handle_errors(error_types=(OSError, PermissionError), reraise=False)
    def register_temp_file(self, file_path: Path) -> bool:
        """
        Register an existing file for cleanup.
        
        Args:
            file_path: Path to file to register for cleanup.
            
        Returns:
            bool: True if registered successfully.
        """
        try:
            with self._lock:
                self._temp_files.add(Path(file_path))
            
            self.logger.debug(f"Registered temporary file: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register temporary file {file_path}: {e}")
            return False
    
    @handle_errors(error_types=(OSError, PermissionError), reraise=False)
    def cleanup_temp_file(self, file_path: Path) -> bool:
        """
        Clean up a specific temporary file.
        
        Args:
            file_path: Path to file to clean up.
            
        Returns:
            bool: True if cleaned up successfully.
        """
        try:
            file_path = Path(file_path)
            
            if file_path.exists():
                file_path.unlink()
                self.logger.debug(f"Cleaned up temporary file: {file_path}")
            
            with self._lock:
                self._temp_files.discard(file_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup temporary file {file_path}: {e}")
            return False
    
    def register_cleanup_callback(self, callback: callable) -> None:
        """
        Register a callback to be called during cleanup.
        
        Args:
            callback: Function to call during cleanup.
        """
        with self._lock:
            self._cleanup_callbacks.append(callback)
        
        self.logger.debug(f"Registered cleanup callback: {callback.__name__}")
    
    @handle_errors(error_types=Exception, reraise=False)
    def cleanup_all(self) -> None:
        """Clean up all managed resources."""
        self.logger.info("Starting resource cleanup")
        
        # Run cleanup callbacks
        with self._lock:
            callbacks = self._cleanup_callbacks.copy()
        
        for callback in callbacks:
            try:
                callback()
                self.logger.debug(f"Executed cleanup callback: {callback.__name__}")
            except Exception as e:
                self.logger.error(f"Cleanup callback {callback.__name__} failed: {e}")
        
        # Clean up temporary files
        with self._lock:
            temp_files = self._temp_files.copy()
        
        cleaned_count = 0
        for temp_file in temp_files:
            if self.cleanup_temp_file(temp_file):
                cleaned_count += 1
        
        # Close any open files
        with self._lock:
            open_files = list(self._open_files.items())
        
        for file_id, file_obj in open_files:
            try:
                if hasattr(file_obj, 'close'):
                    file_obj.close()
                    self.logger.debug(f"Closed file: {file_id}")
            except Exception as e:
                self.logger.error(f"Failed to close file {file_id}: {e}")
        
        with self._lock:
            self._open_files.clear()
        
        self.logger.info(f"Resource cleanup completed - {cleaned_count} temp files cleaned")
    
    @contextmanager
    def managed_file(self, file_path: str, mode: str = 'r', **kwargs):
        """
        Context manager for automatically managed file operations.
        
        Args:
            file_path: Path to file to open.
            mode: File open mode.
            **kwargs: Additional arguments for open().
            
        Yields:
            File object.
        """
        file_obj = None
        file_id = f"{file_path}:{mode}"
        
        try:
            file_obj = open(file_path, mode, **kwargs)
            
            with self._lock:
                self._open_files[file_id] = file_obj
            
            self.logger.debug(f"Opened managed file: {file_path} ({mode})")
            yield file_obj
            
        except Exception as e:
            self.logger.error(f"Error with managed file {file_path}: {e}")
            raise
        finally:
            if file_obj:
                try:
                    file_obj.close()
                    self.logger.debug(f"Closed managed file: {file_path}")
                except Exception as e:
                    self.logger.error(f"Error closing file {file_path}: {e}")
                finally:
                    with self._lock:
                        self._open_files.pop(file_id, None)
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage information.
        
        Returns:
            Dict[str, Any]: Memory usage statistics.
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
                'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
                'percent': process.memory_percent(),
                'available_mb': psutil.virtual_memory().available / 1024 / 1024
            }
        except ImportError:
            # Fallback if psutil not available
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return {
                'max_rss_mb': usage.ru_maxrss / 1024,  # Peak memory usage
                'note': 'Limited memory info (psutil not available)'
            }
        except Exception as e:
            self.logger.error(f"Failed to get memory usage: {e}")
            return {'error': str(e)}
    
    def check_memory_limit(self, limit_mb: float = 1000.0) -> bool:
        """
        Check if memory usage is within acceptable limits.
        
        Args:
            limit_mb: Memory limit in megabytes.
            
        Returns:
            bool: True if within limits, False if exceeded.
        """
        try:
            memory_info = self.get_memory_usage()
            
            if 'rss_mb' in memory_info:
                current_mb = memory_info['rss_mb']
            elif 'max_rss_mb' in memory_info:
                current_mb = memory_info['max_rss_mb']
            else:
                return True  # Can't check, assume OK
            
            if current_mb > limit_mb:
                self.logger.warning(
                    f"Memory usage ({current_mb:.1f} MB) exceeds limit ({limit_mb:.1f} MB)"
                )
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check memory limit: {e}")
            return True  # Assume OK if we can't check
    
    def force_garbage_collection(self) -> Dict[str, int]:
        """
        Force garbage collection and return statistics.
        
        Returns:
            Dict[str, int]: Garbage collection statistics.
        """
        self.logger.debug("Forcing garbage collection")
        
        # Get initial counts
        initial_counts = gc.get_count()
        
        # Force collection of all generations
        collected = {
            'gen0': gc.collect(0),
            'gen1': gc.collect(1), 
            'gen2': gc.collect(2)
        }
        
        # Get final counts
        final_counts = gc.get_count()
        
        stats = {
            'collected_gen0': collected['gen0'],
            'collected_gen1': collected['gen1'],
            'collected_gen2': collected['gen2'],
            'total_collected': sum(collected.values()),
            'objects_before': sum(initial_counts),
            'objects_after': sum(final_counts)
        }
        
        self.logger.info(f"Garbage collection completed: {stats['total_collected']} objects collected")
        return stats
    
    def get_resource_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive resource usage statistics.
        
        Returns:
            Dict[str, Any]: Resource statistics.
        """
        with self._lock:
            temp_files_count = len(self._temp_files)
            open_files_count = len(self._open_files)
            cleanup_callbacks_count = len(self._cleanup_callbacks)
        
        memory_info = self.get_memory_usage()
        
        return {
            'temp_files': temp_files_count,
            'open_files': open_files_count,
            'cleanup_callbacks': cleanup_callbacks_count,
            'memory': memory_info,
            'gc_stats': {
                'counts': gc.get_count(),
                'thresholds': gc.get_threshold(),
                'stats': gc.get_stats() if hasattr(gc, 'get_stats') else None
            }
        }


# Global resource manager instance
_global_resource_manager = ResourceManager()


def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance."""
    return _global_resource_manager


@contextmanager
def temp_file(suffix: str = '.tmp', prefix: str = 'vaitp_', directory: Optional[str] = None):
    """
    Context manager for temporary files that are automatically cleaned up.
    
    Args:
        suffix: File suffix/extension.
        prefix: File prefix.
        directory: Directory to create file in.
        
    Yields:
        Path: Path to temporary file.
    """
    temp_path = _global_resource_manager.create_temp_file(suffix, prefix, directory)
    if temp_path is None:
        raise ResourceError("Failed to create temporary file")
    
    try:
        yield temp_path
    finally:
        _global_resource_manager.cleanup_temp_file(temp_path)


@contextmanager
def managed_file(file_path: str, mode: str = 'r', **kwargs):
    """
    Context manager for automatically managed file operations.
    
    Args:
        file_path: Path to file to open.
        mode: File open mode.
        **kwargs: Additional arguments for open().
        
    Yields:
        File object.
    """
    with _global_resource_manager.managed_file(file_path, mode, **kwargs) as f:
        yield f


def cleanup_resources():
    """Clean up all managed resources."""
    _global_resource_manager.cleanup_all()


def check_memory_usage(limit_mb: float = 1000.0) -> bool:
    """
    Check if memory usage is within acceptable limits.
    
    Args:
        limit_mb: Memory limit in megabytes.
        
    Returns:
        bool: True if within limits, False if exceeded.
    """
    return _global_resource_manager.check_memory_limit(limit_mb)