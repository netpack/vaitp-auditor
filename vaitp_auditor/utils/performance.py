"""
Performance optimization utilities for the VAITP-Auditor system.
"""

import gc
import hashlib
import time
import weakref
from functools import lru_cache, wraps
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from threading import Lock
import os

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from .logging_config import get_logger


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    operation: str
    start_time: float
    end_time: float
    memory_before: float
    memory_after: float
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def duration(self) -> float:
        """Get operation duration in seconds."""
        return self.end_time - self.start_time
    
    @property
    def memory_delta(self) -> float:
        """Get memory usage change in MB."""
        return self.memory_after - self.memory_before


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self):
        self.logger = get_logger('performance')
        self.metrics: List[PerformanceMetrics] = []
        self._lock = Lock()
    
    def start_operation(self, operation: str) -> Dict[str, Any]:
        """Start monitoring an operation."""
        return {
            'operation': operation,
            'start_time': time.time(),
            'memory_before': self._get_memory_usage()
        }
    
    def end_operation(self, context: Dict[str, Any], cache_hits: int = 0, cache_misses: int = 0) -> PerformanceMetrics:
        """End monitoring an operation and record metrics."""
        end_time = time.time()
        memory_after = self._get_memory_usage()
        
        metrics = PerformanceMetrics(
            operation=context['operation'],
            start_time=context['start_time'],
            end_time=end_time,
            memory_before=context['memory_before'],
            memory_after=memory_after,
            cache_hits=cache_hits,
            cache_misses=cache_misses
        )
        
        with self._lock:
            self.metrics.append(metrics)
        
        # Log if operation took too long or used too much memory
        if metrics.duration > 1.0:  # More than 1 second
            self.logger.warning(f"Slow operation: {metrics.operation} took {metrics.duration:.2f}s")
        
        if metrics.memory_delta > 50.0:  # More than 50MB increase
            self.logger.warning(f"High memory usage: {metrics.operation} used {metrics.memory_delta:.2f}MB")
        
        return metrics
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if not HAS_PSUTIL:
            return 0.0
        
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.metrics:
            return {}
        
        operations = {}
        for metric in self.metrics:
            if metric.operation not in operations:
                operations[metric.operation] = {
                    'count': 0,
                    'total_duration': 0.0,
                    'total_memory': 0.0,
                    'max_duration': 0.0,
                    'max_memory': 0.0
                }
            
            op_stats = operations[metric.operation]
            op_stats['count'] += 1
            op_stats['total_duration'] += metric.duration
            op_stats['total_memory'] += metric.memory_delta
            op_stats['max_duration'] = max(op_stats['max_duration'], metric.duration)
            op_stats['max_memory'] = max(op_stats['max_memory'], metric.memory_delta)
        
        # Calculate averages
        for op_stats in operations.values():
            op_stats['avg_duration'] = op_stats['total_duration'] / op_stats['count']
            op_stats['avg_memory'] = op_stats['total_memory'] / op_stats['count']
        
        return operations


class LazyLoader:
    """Lazy loading utility for large content."""
    
    def __init__(self, loader_func: Callable[[], str], max_size: int = 1024 * 1024):  # 1MB default
        self._loader_func = loader_func
        self._content: Optional[str] = None
        self._loaded = False
        self._max_size = max_size
        self._size_estimate: Optional[int] = None
    
    def __len__(self) -> int:
        """Get estimated size without loading content."""
        if self._size_estimate is None:
            # Try to estimate size without loading full content
            try:
                # For file-based loaders, we can check file size
                if hasattr(self._loader_func, '__self__') and hasattr(self._loader_func.__self__, 'stat'):
                    self._size_estimate = self._loader_func.__self__.stat().st_size
                else:
                    # Load a small sample to estimate
                    sample = self._loader_func()[:1000]  # First 1KB
                    self._size_estimate = len(sample) * 10  # Rough estimate
            except Exception:
                self._size_estimate = 0
        
        return self._size_estimate or 0
    
    @property
    def content(self) -> str:
        """Get the content, loading it if necessary."""
        if not self._loaded:
            self._content = self._loader_func()
            self._loaded = True
            self._size_estimate = len(self._content) if self._content else 0
        
        return self._content or ""
    
    @property
    def is_large(self) -> bool:
        """Check if content is considered large."""
        return len(self) > self._max_size
    
    def preview(self, lines: int = 10) -> str:
        """Get a preview of the content without loading it all."""
        if self._loaded:
            content_lines = self.content.split('\n')
            return '\n'.join(content_lines[:lines])
        
        # Try to load just the preview
        try:
            full_content = self._loader_func()
            content_lines = full_content.split('\n')
            preview_content = '\n'.join(content_lines[:lines])
            
            # If the full content is small, cache it
            if len(full_content) <= self._max_size:
                self._content = full_content
                self._loaded = True
                self._size_estimate = len(full_content)
            
            return preview_content
        except Exception:
            return ""


class ContentCache:
    """LRU cache for content with size limits."""
    
    def __init__(self, max_size_mb: int = 100, max_items: int = 1000):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_items = max_items
        self._cache: Dict[str, Tuple[str, int, float]] = {}  # key -> (content, size, timestamp)
        self._lock = Lock()
        self.logger = get_logger('content_cache')
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, key: str) -> Optional[str]:
        """Get content from cache."""
        with self._lock:
            if key in self._cache:
                content, size, _ = self._cache[key]
                # Update timestamp
                self._cache[key] = (content, size, time.time())
                self.hits += 1
                return content
            else:
                self.misses += 1
                return None
    
    def put(self, key: str, content: str) -> None:
        """Put content in cache."""
        content_size = len(content.encode('utf-8'))
        
        with self._lock:
            # Check if we need to evict items
            self._evict_if_needed(content_size)
            
            # Add new item
            self._cache[key] = (content, content_size, time.time())
    
    def _evict_if_needed(self, new_item_size: int) -> None:
        """Evict items if cache is full."""
        current_size = sum(size for _, size, _ in self._cache.values())
        
        # Evict if we exceed size or item limits
        while (len(self._cache) >= self.max_items or 
               current_size + new_item_size > self.max_size_bytes):
            
            if not self._cache:
                break
            
            # Find least recently used item
            lru_key = min(self._cache.keys(), key=lambda k: self._cache[k][2])
            _, evicted_size, _ = self._cache.pop(lru_key)
            current_size -= evicted_size
            self.evictions += 1
    
    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_size = sum(size for _, size, _ in self._cache.values())
            return {
                'items': len(self._cache),
                'size_mb': total_size / 1024 / 1024,
                'hits': self.hits,
                'misses': self.misses,
                'evictions': self.evictions,
                'hit_rate': self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
            }


class ChunkedProcessor:
    """Process large datasets in chunks to manage memory."""
    
    def __init__(self, chunk_size: int = 100, memory_limit_mb: int = 500):
        self.chunk_size = chunk_size
        self.memory_limit_bytes = memory_limit_mb * 1024 * 1024
        self.logger = get_logger('chunked_processor')
    
    def process_chunks(self, items: List[Any], processor_func: Callable[[List[Any]], List[Any]]) -> List[Any]:
        """Process items in chunks with memory monitoring."""
        results = []
        total_items = len(items)
        
        for i in range(0, total_items, self.chunk_size):
            chunk = items[i:i + self.chunk_size]
            chunk_start = i + 1
            chunk_end = min(i + self.chunk_size, total_items)
            
            self.logger.debug(f"Processing chunk {chunk_start}-{chunk_end} of {total_items}")
            
            # Check memory before processing
            memory_before = self._get_memory_usage()
            
            try:
                chunk_results = processor_func(chunk)
                results.extend(chunk_results)
                
                # Check memory after processing
                memory_after = self._get_memory_usage()
                memory_used = memory_after - memory_before
                
                if memory_used > 50:  # More than 50MB for a chunk
                    self.logger.warning(f"Chunk used {memory_used:.1f}MB memory")
                
                # Force garbage collection if memory usage is high
                if memory_after * 1024 * 1024 > self.memory_limit_bytes:
                    self.logger.info("Memory limit approached, forcing garbage collection")
                    gc.collect()
                
            except Exception as e:
                self.logger.error(f"Error processing chunk {chunk_start}-{chunk_end}: {e}")
                # Continue with next chunk rather than failing entirely
                continue
        
        return results
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if not HAS_PSUTIL:
            return 0.0
        
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0


def performance_monitor(operation_name: str = None):
    """Decorator to monitor function performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = PerformanceMonitor()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            context = monitor.start_operation(op_name)
            try:
                result = func(*args, **kwargs)
                monitor.end_operation(context)
                return result
            except Exception as e:
                monitor.end_operation(context)
                raise
        return wrapper
    return decorator


def cached_content(cache_instance: ContentCache, key_func: Callable = None):
    """Decorator to cache function results in ContentCache."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Compute result and cache it
            result = func(*args, **kwargs)
            if isinstance(result, str):
                cache_instance.put(cache_key, result)
            
            return result
        return wrapper
    return decorator


# Global instances
_performance_monitor = PerformanceMonitor()
_content_cache = ContentCache()
_chunked_processor = ChunkedProcessor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _performance_monitor


def get_content_cache() -> ContentCache:
    """Get the global content cache instance."""
    return _content_cache


def get_chunked_processor() -> ChunkedProcessor:
    """Get the global chunked processor instance."""
    return _chunked_processor