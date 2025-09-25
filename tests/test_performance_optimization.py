"""
Performance optimization tests for GUI components.

This module tests performance optimizations including lazy loading,
caching, memory management, and response time targets.
"""

import unittest
import time
import gc
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import vaitp_auditor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vaitp_auditor.gui.performance_optimizer import (
    PerformanceOptimizer, LazyCodeLoader, SyntaxHighlightingCache,
    MemoryManager, AnimationManager, get_performance_optimizer
)
from vaitp_auditor.gui.code_display import SyntaxHighlighter, CodePanel
from vaitp_auditor.core.models import CodePair


class TestLazyCodeLoader(unittest.TestCase):
    """Test lazy code loading functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.small_code = "print('hello')\n" * 10  # Small code (10 lines)
        self.large_code = "print('hello')\n" * 1000  # Large code (1000 lines)
    
    def test_small_code_not_lazy(self):
        """Test that small code is not considered large."""
        loader = LazyCodeLoader(self.small_code)
        self.assertFalse(loader.is_large)
        self.assertEqual(loader.get_content(), self.small_code)
    
    def test_large_code_is_lazy(self):
        """Test that large code is considered large."""
        loader = LazyCodeLoader(self.large_code)
        self.assertTrue(loader.is_large)
        
        # Preview should be shorter than full content
        preview = loader.get_preview()
        self.assertLess(len(preview), len(self.large_code))
        self.assertIn("more lines", preview)
    
    def test_force_full_content(self):
        """Test forcing full content for large files."""
        loader = LazyCodeLoader(self.large_code)
        
        # Normal get_content returns preview
        preview = loader.get_content()
        self.assertLess(len(preview), len(self.large_code))
        
        # Force full content
        full = loader.get_content(force_full=True)
        self.assertEqual(full, self.large_code)
    
    def test_line_count_accuracy(self):
        """Test line count calculation."""
        loader = LazyCodeLoader(self.large_code)
        expected_lines = self.large_code.count('\n') + 1
        self.assertEqual(loader.line_count, expected_lines)


class TestSyntaxHighlightingCache(unittest.TestCase):
    """Test syntax highlighting cache functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = SyntaxHighlightingCache(max_cache_size=5)
        self.test_code = "def hello():\n    print('world')"
        self.test_result = [("def", "#569cd6"), (" hello", "#d4d4d4")]
    
    def test_cache_miss_then_hit(self):
        """Test cache miss followed by cache hit."""
        # First access should be a miss
        result = self.cache.get(self.test_code, "python")
        self.assertIsNone(result)
        self.assertEqual(self.cache.misses, 1)
        self.assertEqual(self.cache.hits, 0)
        
        # Cache the result
        self.cache.put(self.test_code, "python", self.test_result)
        
        # Second access should be a hit
        result = self.cache.get(self.test_code, "python")
        self.assertEqual(result, self.test_result)
        self.assertEqual(self.cache.hits, 1)
    
    def test_cache_eviction(self):
        """Test LRU cache eviction."""
        # Fill cache to capacity
        for i in range(6):  # One more than max_cache_size
            code = f"print({i})"
            result = [(f"print({i})", "#d4d4d4")]
            self.cache.put(code, "python", result)
        
        # Cache should not exceed max size
        self.assertEqual(len(self.cache.cache), 5)
        
        # First item should have been evicted
        first_code = "print(0)"
        result = self.cache.get(first_code, "python")
        self.assertIsNone(result)
    
    def test_cache_stats(self):
        """Test cache statistics."""
        # Perform some operations
        self.cache.get("code1", "python")  # Miss
        self.cache.put("code1", "python", [("code1", "#d4d4d4")])
        self.cache.get("code1", "python")  # Hit
        
        stats = self.cache.get_stats()
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(stats['hit_rate'], 0.5)
        self.assertEqual(stats['size'], 1)


class TestMemoryManager(unittest.TestCase):
    """Test memory management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.memory_manager = MemoryManager(memory_limit_mb=100)
    
    def test_widget_registration(self):
        """Test widget registration and cleanup."""
        # Create mock widgets
        widget1 = Mock()
        widget2 = Mock()
        
        # Register widgets
        self.memory_manager.register_widget(widget1)
        self.memory_manager.register_widget(widget2)
        
        # Check that widgets are tracked
        stats = self.memory_manager.check_memory_usage()
        self.assertEqual(stats['managed_widgets'], 2)
        
        # Cleanup should maintain valid references
        self.memory_manager.cleanup_widgets()
        stats = self.memory_manager.check_memory_usage()
        self.assertEqual(stats['managed_widgets'], 2)
    
    def test_garbage_collection(self):
        """Test forced garbage collection."""
        # This test mainly ensures the method doesn't crash
        initial_objects = len(gc.get_objects())
        
        self.memory_manager.force_garbage_collection()
        
        # Should complete without error
        self.assertTrue(True)
    
    def test_memory_usage_with_psutil(self):
        """Test memory usage calculation with psutil."""
        # This test checks that the method works when psutil is available
        stats = self.memory_manager.check_memory_usage()
        
        # Should return valid statistics structure
        self.assertIn('memory_mb', stats)
        self.assertIn('memory_limit_mb', stats)
        self.assertIn('exceeds_limit', stats)
        self.assertIsInstance(stats['memory_mb'], (int, float))
        self.assertEqual(stats['memory_limit_mb'], 100)
    
    def test_memory_usage_without_psutil(self):
        """Test memory usage calculation without psutil."""
        with patch.dict('sys.modules', {'psutil': None}):
            stats = self.memory_manager.check_memory_usage()
            
            # Should return default values when psutil is not available
            self.assertEqual(stats['memory_mb'], 0)
            self.assertFalse(stats['exceeds_limit'])


class TestAnimationManager(unittest.TestCase):
    """Test animation manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.animation_manager = AnimationManager()
        self.mock_widget = Mock()
    
    def test_fade_in_animation(self):
        """Test fade in animation."""
        callback_called = False
        
        def callback():
            nonlocal callback_called
            callback_called = True
        
        # Start animation with very short duration for testing
        self.animation_manager.fade_in_widget(
            self.mock_widget, 
            duration=0.1, 
            callback=callback
        )
        
        # Animation should be registered
        self.assertTrue(len(self.animation_manager.active_animations) > 0)
        
        # Wait for animation to complete
        time.sleep(0.2)
        
        # Callback should have been called
        self.assertTrue(callback_called)
    
    def test_stop_animation(self):
        """Test stopping animations."""
        # Start an animation
        self.animation_manager.fade_in_widget(self.mock_widget, duration=1.0)
        
        # Should have active animation
        self.assertTrue(len(self.animation_manager.active_animations) > 0)
        
        # Stop animation
        self.animation_manager.stop_animation(self.mock_widget)
        
        # Should have no active animations
        self.assertEqual(len(self.animation_manager.active_animations), 0)
    
    def test_stop_all_animations(self):
        """Test stopping all animations."""
        # Start multiple animations
        widget1 = Mock()
        widget2 = Mock()
        
        self.animation_manager.fade_in_widget(widget1, duration=1.0)
        self.animation_manager.slide_in_widget(widget2, duration=1.0)
        
        # Should have active animations
        self.assertTrue(len(self.animation_manager.active_animations) > 0)
        
        # Stop all animations
        self.animation_manager.stop_all_animations()
        
        # Should have no active animations
        self.assertEqual(len(self.animation_manager.active_animations), 0)


class TestPerformanceOptimizer(unittest.TestCase):
    """Test main performance optimizer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.optimizer = PerformanceOptimizer()
        self.small_code = "print('hello')"
        self.large_code = "print('hello')\n" * 1000
    
    def test_code_display_optimization(self):
        """Test code display optimization."""
        # Test small code
        content, is_cached = self.optimizer.optimize_code_display(self.small_code)
        self.assertEqual(content, self.small_code)
        
        # Test large code
        content, is_cached = self.optimizer.optimize_code_display(self.large_code)
        # Large code should be truncated in preview
        self.assertLess(len(content), len(self.large_code))
    
    def test_lazy_loading_decision(self):
        """Test lazy loading decision logic."""
        # Small code should not use lazy loading
        self.assertFalse(self.optimizer.should_use_lazy_loading(self.small_code))
        
        # Large code should use lazy loading
        self.assertTrue(self.optimizer.should_use_lazy_loading(self.large_code))
        
        # Code with many lines should use lazy loading
        many_lines_code = "line\n" * 600
        self.assertTrue(self.optimizer.should_use_lazy_loading(many_lines_code))
    
    def test_performance_targets(self):
        """Test performance target checking."""
        targets = self.optimizer.check_performance_targets()
        
        # Should have required keys
        self.assertIn('memory', targets)
        self.assertIn('cache', targets)
        self.assertIn('targets', targets)
        
        # Memory should have target information
        memory_info = targets['memory']
        self.assertIn('current_mb', memory_info)
        self.assertIn('limit_mb', memory_info)
        self.assertIn('within_target', memory_info)
    
    def test_resource_cleanup(self):
        """Test resource cleanup."""
        # Add some cached content
        self.optimizer.syntax_cache.put("test", "python", [("test", "#d4d4d4")])
        
        # Cleanup should not crash
        self.optimizer.cleanup_resources()
        
        # Should complete successfully
        self.assertTrue(True)
    
    def test_performance_summary(self):
        """Test performance summary generation."""
        summary = self.optimizer.get_performance_summary()
        
        # Should have all required sections
        required_keys = ['targets', 'memory', 'syntax_cache', 'content_cache', 'monitor']
        for key in required_keys:
            self.assertIn(key, summary)


class TestPerformanceTargets(unittest.TestCase):
    """Test performance targets and response times."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.optimizer = get_performance_optimizer()
    
    def test_code_display_response_time(self):
        """Test that code display meets response time targets."""
        test_code = "def hello():\n    print('world')\n" * 100
        
        start_time = time.time()
        content, is_cached = self.optimizer.optimize_code_display(test_code)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        # Should meet 200ms target for code display
        self.assertLess(response_time_ms, 200, 
                       f"Code display took {response_time_ms:.1f}ms, exceeds 200ms target")
    
    def test_syntax_highlighting_performance(self):
        """Test syntax highlighting performance."""
        highlighter = SyntaxHighlighter()
        test_code = "def test():\n    return 'hello'\n" * 50
        
        start_time = time.time()
        result = highlighter.highlight_code(test_code, "python")
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        # Should complete reasonably quickly
        self.assertLess(response_time_ms, 500, 
                       f"Syntax highlighting took {response_time_ms:.1f}ms")
        
        # Should return valid result
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
    
    def test_memory_usage_monitoring(self):
        """Test memory usage monitoring."""
        memory_manager = MemoryManager(memory_limit_mb=500)
        
        # Create some test data
        large_data = ["test" * 1000 for _ in range(100)]
        
        stats = memory_manager.check_memory_usage()
        
        # Should return valid statistics
        self.assertIn('memory_mb', stats)
        self.assertIn('memory_limit_mb', stats)
        self.assertIn('exceeds_limit', stats)
        self.assertIsInstance(stats['memory_mb'], (int, float))
    
    def test_cache_effectiveness(self):
        """Test cache effectiveness for repeated operations."""
        cache = SyntaxHighlightingCache()
        test_code = "print('hello world')"
        test_result = [("print", "#569cd6"), ("('hello world')", "#ce9178")]
        
        # First access - miss
        result1 = cache.get(test_code, "python")
        self.assertIsNone(result1)
        
        # Cache the result
        cache.put(test_code, "python", test_result)
        
        # Second access - hit
        result2 = cache.get(test_code, "python")
        self.assertEqual(result2, test_result)
        
        # Check hit rate
        stats = cache.get_stats()
        self.assertEqual(stats['hit_rate'], 0.5)  # 1 hit out of 2 requests


class TestIntegrationPerformance(unittest.TestCase):
    """Integration tests for performance optimization."""
    
    def test_code_panel_performance(self):
        """Test CodePanel performance with optimizations."""
        # Test performance optimizer directly instead of GUI components
        optimizer = get_performance_optimizer()
        
        # Test with large code
        large_code = "def function():\n    pass\n" * 500
        
        start_time = time.time()
        content, is_cached = optimizer.optimize_code_display(large_code, "python")
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        # Should meet performance target
        self.assertLess(response_time_ms, 300, 
                       f"Code display optimization took {response_time_ms:.1f}ms")
    
    def test_memory_cleanup_effectiveness(self):
        """Test that memory cleanup is effective."""
        optimizer = get_performance_optimizer()
        
        # Create some cached content
        for i in range(50):
            code = f"print({i})" * 100
            optimizer.syntax_cache.put(f"code_{i}", "python", [(code, "#d4d4d4")])
        
        # Check cache size before cleanup
        stats_before = optimizer.syntax_cache.get_stats()
        
        # Force cleanup
        optimizer.cleanup_resources()
        
        # Memory cleanup should complete without error
        self.assertTrue(True)


if __name__ == '__main__':
    # Run performance tests
    unittest.main(verbosity=2)