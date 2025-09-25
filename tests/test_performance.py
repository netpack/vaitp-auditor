"""
Performance tests for the VAITP-Auditor system.
"""

import gc
import os
import tempfile
import time
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from vaitp_auditor.utils.performance import (
    PerformanceMonitor, LazyLoader, ContentCache, ChunkedProcessor,
    performance_monitor, get_performance_monitor, get_content_cache
)
from vaitp_auditor.core.differ import CodeDiffer
from vaitp_auditor.ui.display_manager import DisplayManager
from vaitp_auditor.data_sources.filesystem import FileSystemSource
from vaitp_auditor.core.models import CodePair


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""
    
    def test_operation_monitoring(self):
        """Test basic operation monitoring."""
        monitor = PerformanceMonitor()
        
        context = monitor.start_operation("test_operation")
        time.sleep(0.1)  # Simulate work
        metrics = monitor.end_operation(context)
        
        assert metrics.operation == "test_operation"
        assert metrics.duration >= 0.1
        assert metrics.memory_before >= 0
        assert metrics.memory_after >= 0
    
    def test_performance_decorator(self):
        """Test performance monitoring decorator."""
        
        @performance_monitor("decorated_function")
        def test_function():
            time.sleep(0.05)
            return "result"
        
        result = test_function()
        assert result == "result"
        
        # Check that metrics were recorded
        monitor = get_performance_monitor()
        assert len(monitor.metrics) > 0
    
    def test_summary_statistics(self):
        """Test performance summary generation."""
        monitor = PerformanceMonitor()
        
        # Record multiple operations
        for i in range(3):
            context = monitor.start_operation("test_op")
            time.sleep(0.01)
            monitor.end_operation(context)
        
        summary = monitor.get_summary()
        assert "test_op" in summary
        assert summary["test_op"]["count"] == 3
        assert summary["test_op"]["avg_duration"] > 0


class TestLazyLoader:
    """Test lazy loading functionality."""
    
    def test_lazy_loading_basic(self):
        """Test basic lazy loading behavior."""
        call_count = 0
        
        def loader_func():
            nonlocal call_count
            call_count += 1
            return "loaded content"
        
        lazy_loader = LazyLoader(loader_func)
        
        # Content should not be loaded yet
        assert call_count == 0
        
        # Access content - should trigger loading
        content = lazy_loader.content
        assert content == "loaded content"
        assert call_count == 1
        
        # Second access should not trigger loading again
        content2 = lazy_loader.content
        assert content2 == "loaded content"
        assert call_count == 1
    
    def test_lazy_loader_size_estimation(self):
        """Test size estimation without loading."""
        def loader_func():
            return "x" * 1000
        
        lazy_loader = LazyLoader(loader_func, max_size=500)
        
        # Check if it's considered large
        assert lazy_loader.is_large
    
    def test_lazy_loader_preview(self):
        """Test preview functionality."""
        content = "\n".join([f"line {i}" for i in range(20)])
        
        def loader_func():
            return content
        
        lazy_loader = LazyLoader(loader_func)
        preview = lazy_loader.preview(5)
        
        expected_lines = content.split('\n')[:5]
        assert preview == '\n'.join(expected_lines)


class TestContentCache:
    """Test content caching functionality."""
    
    def test_cache_basic_operations(self):
        """Test basic cache operations."""
        cache = ContentCache(max_size_mb=1, max_items=10)
        
        # Test put and get
        cache.put("key1", "content1")
        assert cache.get("key1") == "content1"
        
        # Test cache miss
        assert cache.get("nonexistent") is None
        
        # Check statistics
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
    
    def test_cache_eviction_by_size(self):
        """Test cache eviction based on size limits."""
        cache = ContentCache(max_size_mb=1, max_items=100)  # 1MB limit
        
        # Add content that exceeds size limit
        large_content = "x" * (512 * 1024)  # 512KB
        cache.put("large1", large_content)
        cache.put("large2", large_content)
        cache.put("large3", large_content)  # This should trigger eviction
        
        stats = cache.get_stats()
        assert stats["evictions"] > 0
    
    def test_cache_eviction_by_items(self):
        """Test cache eviction based on item count."""
        cache = ContentCache(max_size_mb=100, max_items=2)  # 2 item limit
        
        cache.put("item1", "content1")
        cache.put("item2", "content2")
        cache.put("item3", "content3")  # This should trigger eviction
        
        stats = cache.get_stats()
        assert stats["items"] <= 2
        assert stats["evictions"] > 0


class TestChunkedProcessor:
    """Test chunked processing functionality."""
    
    def test_chunked_processing(self):
        """Test basic chunked processing."""
        processor = ChunkedProcessor(chunk_size=3)
        
        items = list(range(10))
        
        def process_chunk(chunk):
            return [x * 2 for x in chunk]
        
        results = processor.process_chunks(items, process_chunk)
        expected = [x * 2 for x in items]
        
        assert results == expected
    
    def test_chunked_processing_with_errors(self):
        """Test chunked processing with error handling."""
        processor = ChunkedProcessor(chunk_size=2)
        
        items = list(range(5))
        
        def process_chunk(chunk):
            if 2 in chunk:  # Simulate error for chunk containing 2
                raise ValueError("Test error")
            return [x * 2 for x in chunk]
        
        # Should continue processing other chunks despite error
        results = processor.process_chunks(items, process_chunk)
        
        # Should have results from chunks that didn't error
        assert len(results) > 0
        assert 0 in results  # From first chunk [0, 1]
        assert 8 in results  # From last chunk [4]


class TestCodeDifferPerformance:
    """Test CodeDiffer performance optimizations."""
    
    def test_diff_caching(self):
        """Test that diff computation results are cached."""
        differ = CodeDiffer()
        
        code1 = "def hello():\n    print('world')"
        code2 = "def hello():\n    print('universe')"
        
        # First computation
        start_time = time.time()
        result1 = differ.compute_diff(code1, code2)
        first_duration = time.time() - start_time
        
        # Second computation (should be cached)
        start_time = time.time()
        result2 = differ.compute_diff(code1, code2)
        second_duration = time.time() - start_time
        
        # Results should be identical
        assert len(result1) == len(result2)
        for i, (line1, line2) in enumerate(zip(result1, result2)):
            assert line1.tag == line2.tag
            assert line1.line_content == line2.line_content
        
        # Second computation should be faster (cached)
        assert second_duration < first_duration
    
    def test_large_file_diff_handling(self):
        """Test handling of large file diffs."""
        differ = CodeDiffer()
        
        # Create large content
        large_code1 = "\n".join([f"line {i} in file 1" for i in range(5000)])
        large_code2 = "\n".join([f"line {i} in file 2" for i in range(5000)])
        
        # Should handle large files without crashing
        start_time = time.time()
        result = differ.compute_diff(large_code1, large_code2)
        duration = time.time() - start_time
        
        assert len(result) > 0
        # Should complete within reasonable time (adjust threshold as needed)
        assert duration < 10.0  # 10 seconds max
    
    def test_diff_text_caching(self):
        """Test that unified diff text is cached."""
        differ = CodeDiffer()
        
        code1 = "original code"
        code2 = "modified code"
        
        # First call
        result1 = differ.get_diff_text(code1, code2)
        
        # Second call (should use cache)
        result2 = differ.get_diff_text(code1, code2)
        
        assert result1 == result2
        assert len(result1) > 0


class TestDisplayManagerPerformance:
    """Test DisplayManager performance optimizations."""
    
    def test_syntax_highlighting_cache(self):
        """Test that syntax highlighting is cached."""
        with patch('vaitp_auditor.ui.display_manager.Console'):
            display_manager = DisplayManager()
            
            code = "def test():\n    return True"
            
            # First call should create syntax object
            syntax1 = display_manager._get_cached_syntax(code, "test_key")
            
            # Second call should return cached object
            syntax2 = display_manager._get_cached_syntax(code, "test_key")
            
            # Should be the same object (cached)
            assert syntax1 is syntax2
    
    def test_large_content_handling(self):
        """Test handling of large content in display."""
        with patch('vaitp_auditor.ui.display_manager.Console'):
            display_manager = DisplayManager()
            
            # Create large content
            large_code = "\n".join([f"line {i}" for i in range(2000)])
            
            # Should handle large content without issues
            syntax = display_manager._get_cached_syntax(large_code, "large_test")
            assert syntax is not None
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        with patch('vaitp_auditor.ui.display_manager.Console'):
            display_manager = DisplayManager()
            
            # Add some cached content
            display_manager._get_cached_syntax("test code", "test_key")
            assert len(display_manager._syntax_cache) > 0
            
            # Clear caches
            display_manager.clear_caches()
            assert len(display_manager._syntax_cache) == 0


class TestFileSystemSourcePerformance:
    """Test FileSystemSource performance optimizations."""
    
    def test_lazy_loading_threshold(self):
        """Test that large files trigger lazy loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a large file
            large_file = temp_path / "large_file.py"
            large_content = "# Large file\n" + "x = 1\n" * 10000
            large_file.write_text(large_content)
            
            # Create a small file
            small_file = temp_path / "small_file.py"
            small_content = "# Small file\nx = 1"
            small_file.write_text(small_content)
            
            source = FileSystemSource()
            source.generated_folder = temp_path
            source._file_pairs = [(large_file, None), (small_file, None)]
            source._configured = True
            
            # Load data
            code_pairs = source.load_data(100.0)
            
            # Check that large file has lazy loading indicator
            large_pair = next(cp for cp in code_pairs if "large_file" in cp.identifier)
            small_pair = next(cp for cp in code_pairs if "small_file" in cp.identifier)
            
            # Large file should be marked as lazy loaded
            assert large_pair.source_info.get("lazy_loaded") is True
            # Small file should not be lazy loaded
            assert small_pair.source_info.get("lazy_loaded") is False
    
    def test_chunked_processing(self):
        """Test that file processing uses chunking for large datasets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple files
            files = []
            for i in range(50):  # Create enough files to trigger chunking
                file_path = temp_path / f"file_{i}.py"
                file_path.write_text(f"# File {i}\nprint({i})")
                files.append((file_path, None))
            
            source = FileSystemSource()
            source.generated_folder = temp_path
            source._file_pairs = files
            source._configured = True
            
            # Should process without memory issues
            code_pairs = source.load_data(100.0)
            assert len(code_pairs) == 50


class TestIntegrationPerformance:
    """Integration tests for performance optimizations."""
    
    def test_end_to_end_performance_monitoring(self):
        """Test that performance monitoring works end-to-end."""
        monitor = get_performance_monitor()
        initial_count = len(monitor.metrics)
        
        # Perform operations that should be monitored
        differ = CodeDiffer()
        differ.compute_diff("code1", "code2")
        differ.get_diff_text("code1", "code2")
        
        # Should have recorded metrics
        assert len(monitor.metrics) > initial_count
        
        # Get summary
        summary = monitor.get_summary()
        assert len(summary) > 0
    
    def test_memory_usage_monitoring(self):
        """Test memory usage monitoring during operations."""
        monitor = PerformanceMonitor()
        
        # Perform memory-intensive operation
        context = monitor.start_operation("memory_test")
        
        # Create some data
        large_data = ["x" * 1000 for _ in range(1000)]
        
        metrics = monitor.end_operation(context)
        
        # Should have recorded memory usage
        assert metrics.memory_before >= 0
        assert metrics.memory_after >= 0
        
        # Clean up
        del large_data
        gc.collect()


@pytest.mark.performance
class TestPerformanceTargets:
    """Test that performance targets are met."""
    
    def test_diff_computation_speed(self):
        """Test that diff computation meets speed targets."""
        differ = CodeDiffer()
        
        # Test with medium-sized code
        code1 = "\n".join([f"def function_{i}():" for i in range(100)])
        code2 = "\n".join([f"def function_{i}():" for i in range(50, 150)])
        
        start_time = time.time()
        result = differ.compute_diff(code1, code2)
        duration = time.time() - start_time
        
        # Should complete within 100ms for medium files
        assert duration < 0.1
        assert len(result) > 0
    
    def test_syntax_highlighting_speed(self):
        """Test that syntax highlighting meets speed targets."""
        with patch('vaitp_auditor.ui.display_manager.Console'):
            display_manager = DisplayManager()
            
            # Test with medium-sized code
            code = "\n".join([f"def function_{i}():\n    return {i}" for i in range(100)])
            
            start_time = time.time()
            syntax = display_manager._get_cached_syntax(code, "speed_test")
            duration = time.time() - start_time
            
            # Should complete within 50ms for medium files
            assert duration < 0.05
            assert syntax is not None
    
    def test_file_loading_speed(self):
        """Test that file loading meets speed targets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple medium-sized files
            for i in range(10):
                file_path = temp_path / f"file_{i}.py"
                content = "\n".join([f"def func_{j}(): return {j}" for j in range(50)])
                file_path.write_text(content)
            
            source = FileSystemSource()
            source.generated_folder = temp_path
            source._discover_file_pairs()
            source._configured = True
            
            start_time = time.time()
            code_pairs = source.load_data(100.0)
            duration = time.time() - start_time
            
            # Should load 10 medium files within 1 second
            assert duration < 1.0
            assert len(code_pairs) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])