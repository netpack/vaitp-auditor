"""
Performance optimization utilities for GUI components.

This module provides performance optimizations including lazy loading,
caching, memory management, and smooth animations for the GUI interface.
"""

import gc
import time
import threading
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass
from functools import lru_cache
import customtkinter as ctk

from ..utils.performance import (
    PerformanceMonitor, ContentCache, LazyLoader,
    get_performance_monitor, get_content_cache
)
from ..utils.logging_config import get_logger


@dataclass
class GUIPerformanceMetrics:
    """Performance metrics specific to GUI operations."""
    operation: str
    start_time: float
    end_time: float
    memory_before: float
    memory_after: float
    ui_response_time: float
    cache_hit: bool = False
    
    @property
    def duration(self) -> float:
        """Get operation duration in seconds."""
        return self.end_time - self.start_time
    
    @property
    def meets_target(self) -> bool:
        """Check if operation meets performance targets."""
        # Target: < 200ms for code display, < 100ms for UI response
        if "code_display" in self.operation:
            return self.duration < 0.2
        elif "ui_response" in self.operation:
            return self.ui_response_time < 0.1
        return True


class LazyCodeLoader:
    """Lazy loader specifically for code content with size optimization."""
    
    def __init__(self, code_content: str, max_preview_lines: int = 50):
        """Initialize lazy code loader.
        
        Args:
            code_content: Full code content
            max_preview_lines: Maximum lines to show in preview mode
        """
        self.full_content = code_content
        self.max_preview_lines = max_preview_lines
        self._preview_content: Optional[str] = None
        self._is_large = len(code_content) > 10000  # 10KB threshold
        self._line_count = code_content.count('\n') + 1
        
    @property
    def is_large(self) -> bool:
        """Check if content is considered large."""
        return self._is_large
    
    @property
    def line_count(self) -> int:
        """Get total line count."""
        return self._line_count
    
    def get_preview(self) -> str:
        """Get preview content for large files."""
        if self._preview_content is None:
            lines = self.full_content.split('\n')
            if len(lines) > self.max_preview_lines:
                preview_lines = lines[:self.max_preview_lines]
                preview_lines.append(f"... ({len(lines) - self.max_preview_lines} more lines)")
                self._preview_content = '\n'.join(preview_lines)
            else:
                self._preview_content = self.full_content
        
        return self._preview_content
    
    def get_content(self, force_full: bool = False) -> str:
        """Get content, using preview for large files unless forced.
        
        Args:
            force_full: If True, always return full content
            
        Returns:
            Content string (preview or full based on size and force_full)
        """
        if force_full or not self.is_large:
            return self.full_content
        return self.get_preview()


class SyntaxHighlightingCache:
    """Cache for syntax highlighting results with performance optimization."""
    
    def __init__(self, max_cache_size: int = 100):
        """Initialize syntax highlighting cache.
        
        Args:
            max_cache_size: Maximum number of cached highlighting results
        """
        self.cache: Dict[str, List[Tuple[str, str]]] = {}
        self.max_cache_size = max_cache_size
        self.access_times: Dict[str, float] = {}
        self.logger = get_logger('syntax_cache')
        
        # Performance tracking
        self.hits = 0
        self.misses = 0
    
    def _generate_cache_key(self, content: str, language: str) -> str:
        """Generate cache key for content and language."""
        # Use hash of content + language for key
        content_hash = hash(content)
        return f"{language}_{content_hash}"
    
    def get(self, content: str, language: str) -> Optional[List[Tuple[str, str]]]:
        """Get cached highlighting result.
        
        Args:
            content: Code content
            language: Programming language
            
        Returns:
            Cached highlighting result or None if not found
        """
        cache_key = self._generate_cache_key(content, language)
        
        if cache_key in self.cache:
            self.hits += 1
            self.access_times[cache_key] = time.time()
            return self.cache[cache_key]
        
        self.misses += 1
        return None
    
    def put(self, content: str, language: str, highlighted_parts: List[Tuple[str, str]]) -> None:
        """Cache highlighting result.
        
        Args:
            content: Code content
            language: Programming language
            highlighted_parts: Highlighting result to cache
        """
        cache_key = self._generate_cache_key(content, language)
        
        # Evict old entries if cache is full
        if len(self.cache) >= self.max_cache_size:
            self._evict_lru()
        
        self.cache[cache_key] = highlighted_parts
        self.access_times[cache_key] = time.time()
    
    def _evict_lru(self) -> None:
        """Evict least recently used cache entry."""
        if not self.access_times:
            return
        
        # Find least recently used key
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        
        # Remove from cache
        self.cache.pop(lru_key, None)
        self.access_times.pop(lru_key, None)
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'max_size': self.max_cache_size
        }


class MemoryManager:
    """Memory management for GUI components."""
    
    def __init__(self, memory_limit_mb: int = 500):
        """Initialize memory manager.
        
        Args:
            memory_limit_mb: Memory limit in megabytes
        """
        self.memory_limit_mb = memory_limit_mb
        self.logger = get_logger('memory_manager')
        self._weak_refs: List = []  # Weak references to managed objects
        
    def register_widget(self, widget: ctk.CTkBaseClass) -> None:
        """Register widget for memory management.
        
        Args:
            widget: Widget to manage
        """
        import weakref
        self._weak_refs.append(weakref.ref(widget))
    
    def cleanup_widgets(self) -> None:
        """Clean up destroyed widgets from weak references."""
        self._weak_refs = [ref for ref in self._weak_refs if ref() is not None]
    
    def force_garbage_collection(self) -> None:
        """Force garbage collection and cleanup."""
        self.cleanup_widgets()
        gc.collect()
        self.logger.debug("Forced garbage collection completed")
    
    def check_memory_usage(self) -> Dict[str, Any]:
        """Check current memory usage and return statistics."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            stats = {
                'memory_mb': memory_mb,
                'memory_limit_mb': self.memory_limit_mb,
                'memory_percent': (memory_mb / self.memory_limit_mb) * 100,
                'exceeds_limit': memory_mb > self.memory_limit_mb,
                'managed_widgets': len([ref for ref in self._weak_refs if ref() is not None])
            }
            
            if stats['exceeds_limit']:
                self.logger.warning(f"Memory usage ({memory_mb:.1f}MB) exceeds limit ({self.memory_limit_mb}MB)")
            
            return stats
            
        except ImportError:
            return {
                'memory_mb': 0,
                'memory_limit_mb': self.memory_limit_mb,
                'memory_percent': 0,
                'exceeds_limit': False,
                'managed_widgets': len([ref for ref in self._weak_refs if ref() is not None])
            }


class AnimationManager:
    """Manager for smooth animations and transitions."""
    
    def __init__(self):
        """Initialize animation manager."""
        self.active_animations: Dict[str, threading.Timer] = {}
        self.logger = get_logger('animation_manager')
    
    def fade_in_widget(self, widget: ctk.CTkBaseClass, duration: float = 0.3, 
                      callback: Optional[Callable] = None) -> None:
        """Fade in a widget smoothly.
        
        Args:
            widget: Widget to fade in
            duration: Animation duration in seconds
            callback: Optional callback when animation completes
        """
        animation_id = f"fade_in_{id(widget)}"
        
        # Cancel existing animation for this widget
        if animation_id in self.active_animations:
            self.active_animations[animation_id].cancel()
        
        steps = 20
        step_duration = duration / steps
        alpha_step = 1.0 / steps
        
        def animate_step(step: int):
            if step <= steps:
                try:
                    alpha = step * alpha_step
                    # For CustomTkinter, we can't directly set alpha, so we simulate with colors
                    # This is a simplified implementation
                    if hasattr(widget, 'configure'):
                        # Adjust appearance based on step
                        pass
                    
                    if step < steps:
                        timer = threading.Timer(step_duration, lambda: animate_step(step + 1))
                        timer.start()
                        self.active_animations[animation_id] = timer
                    else:
                        # Animation complete
                        self.active_animations.pop(animation_id, None)
                        if callback:
                            callback()
                except Exception as e:
                    self.logger.error(f"Error in fade animation: {e}")
                    self.active_animations.pop(animation_id, None)
        
        animate_step(0)
    
    def slide_in_widget(self, widget: ctk.CTkBaseClass, direction: str = "left", 
                       duration: float = 0.3, callback: Optional[Callable] = None) -> None:
        """Slide in a widget from specified direction.
        
        Args:
            widget: Widget to slide in
            direction: Direction to slide from ("left", "right", "top", "bottom")
            duration: Animation duration in seconds
            callback: Optional callback when animation completes
        """
        animation_id = f"slide_in_{id(widget)}_{direction}"
        
        # Cancel existing animation for this widget
        if animation_id in self.active_animations:
            self.active_animations[animation_id].cancel()
        
        # This is a simplified implementation for CustomTkinter
        # In a full implementation, you would manipulate widget positions
        try:
            # Simulate slide by adjusting padding or position
            if hasattr(widget, 'grid'):
                # For now, just show the widget (CustomTkinter doesn't support complex animations)
                widget.grid()
            
            if callback:
                # Call callback after duration
                timer = threading.Timer(duration, callback)
                timer.start()
                self.active_animations[animation_id] = timer
                
        except Exception as e:
            self.logger.error(f"Error in slide animation: {e}")
    
    def pulse_widget(self, widget: ctk.CTkBaseClass, duration: float = 0.5, 
                    pulses: int = 3, callback: Optional[Callable] = None) -> None:
        """Create a pulsing effect on a widget.
        
        Args:
            widget: Widget to pulse
            duration: Duration of each pulse in seconds
            pulses: Number of pulses
            callback: Optional callback when animation completes
        """
        animation_id = f"pulse_{id(widget)}"
        
        # Cancel existing animation for this widget
        if animation_id in self.active_animations:
            self.active_animations[animation_id].cancel()
        
        pulse_count = 0
        
        def pulse_step():
            nonlocal pulse_count
            try:
                if pulse_count < pulses:
                    # Simulate pulse effect (simplified for CustomTkinter)
                    if hasattr(widget, 'configure'):
                        # Could adjust colors or other properties here
                        pass
                    
                    pulse_count += 1
                    timer = threading.Timer(duration, pulse_step)
                    timer.start()
                    self.active_animations[animation_id] = timer
                else:
                    # Animation complete
                    self.active_animations.pop(animation_id, None)
                    if callback:
                        callback()
            except Exception as e:
                self.logger.error(f"Error in pulse animation: {e}")
                self.active_animations.pop(animation_id, None)
        
        pulse_step()
    
    def stop_animation(self, widget: ctk.CTkBaseClass) -> None:
        """Stop all animations for a widget.
        
        Args:
            widget: Widget to stop animations for
        """
        widget_id = id(widget)
        animations_to_stop = [
            anim_id for anim_id in self.active_animations.keys()
            if str(widget_id) in anim_id
        ]
        
        for anim_id in animations_to_stop:
            timer = self.active_animations.pop(anim_id, None)
            if timer:
                timer.cancel()
    
    def stop_all_animations(self) -> None:
        """Stop all active animations."""
        for timer in self.active_animations.values():
            timer.cancel()
        self.active_animations.clear()


class PerformanceOptimizer:
    """Main performance optimizer for GUI components."""
    
    def __init__(self):
        """Initialize performance optimizer."""
        self.syntax_cache = SyntaxHighlightingCache()
        self.memory_manager = MemoryManager()
        self.animation_manager = AnimationManager()
        self.performance_monitor = get_performance_monitor()
        self.content_cache = get_content_cache()
        self.logger = get_logger('performance_optimizer')
        
        # Performance targets
        self.targets = {
            'code_display_ms': 200,
            'ui_response_ms': 100,
            'memory_limit_mb': 500
        }
    
    def optimize_code_display(self, content: str, language: str = "python") -> Tuple[str, bool]:
        """Optimize code display with lazy loading and caching.
        
        Args:
            content: Code content to display
            language: Programming language
            
        Returns:
            Tuple of (optimized_content, is_cached)
        """
        start_time = time.time()
        
        # Create lazy loader for large content
        lazy_loader = LazyCodeLoader(content)
        
        # Use preview for large files
        display_content = lazy_loader.get_content()
        
        # Check if we should use cached highlighting
        cache_key = f"{language}_{hash(display_content)}"
        is_cached = self.content_cache.get(cache_key) is not None
        
        if not is_cached and len(display_content) < 50000:  # Only cache reasonable sizes
            self.content_cache.put(cache_key, display_content)
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        if duration_ms > self.targets['code_display_ms']:
            self.logger.warning(f"Code display optimization took {duration_ms:.1f}ms (target: {self.targets['code_display_ms']}ms)")
        
        return display_content, is_cached
    
    def should_use_lazy_loading(self, content: str) -> bool:
        """Determine if lazy loading should be used for content.
        
        Args:
            content: Content to evaluate
            
        Returns:
            True if lazy loading should be used
        """
        # Use lazy loading for content > 10KB or > 500 lines
        return len(content) > 10000 or content.count('\n') > 500
    
    def optimize_syntax_highlighting(self, content: str, language: str) -> Optional[List[Tuple[str, str]]]:
        """Get optimized syntax highlighting with caching.
        
        Args:
            content: Code content
            language: Programming language
            
        Returns:
            Cached highlighting result or None if not cached
        """
        return self.syntax_cache.get(content, language)
    
    def cache_syntax_highlighting(self, content: str, language: str, 
                                 highlighted_parts: List[Tuple[str, str]]) -> None:
        """Cache syntax highlighting result.
        
        Args:
            content: Code content
            language: Programming language
            highlighted_parts: Highlighting result to cache
        """
        self.syntax_cache.put(content, language, highlighted_parts)
    
    def check_performance_targets(self) -> Dict[str, Any]:
        """Check if performance targets are being met.
        
        Returns:
            Dictionary with performance status
        """
        memory_stats = self.memory_manager.check_memory_usage()
        cache_stats = self.syntax_cache.get_stats()
        
        return {
            'memory': {
                'current_mb': memory_stats['memory_mb'],
                'limit_mb': self.targets['memory_limit_mb'],
                'within_target': memory_stats['memory_mb'] <= self.targets['memory_limit_mb']
            },
            'cache': {
                'hit_rate': cache_stats['hit_rate'],
                'size': cache_stats['size'],
                'effective': cache_stats['hit_rate'] > 0.5  # 50% hit rate target
            },
            'targets': self.targets
        }
    
    def cleanup_resources(self) -> None:
        """Clean up resources and optimize memory usage."""
        self.memory_manager.force_garbage_collection()
        self.animation_manager.stop_all_animations()
        
        # Clear caches if memory usage is high
        memory_stats = self.memory_manager.check_memory_usage()
        if memory_stats['exceeds_limit']:
            self.logger.info("Memory limit exceeded, clearing caches")
            self.syntax_cache.clear()
            self.content_cache.clear()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary.
        
        Returns:
            Dictionary with performance metrics and statistics
        """
        return {
            'targets': self.check_performance_targets(),
            'memory': self.memory_manager.check_memory_usage(),
            'syntax_cache': self.syntax_cache.get_stats(),
            'content_cache': self.content_cache.get_stats(),
            'monitor': self.performance_monitor.get_summary()
        }


# Global performance optimizer instance
_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get the global performance optimizer instance."""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


def performance_optimized(operation_name: str):
    """Decorator to add performance optimization to GUI operations."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            optimizer = get_performance_optimizer()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                # Log if operation is slow
                if duration_ms > optimizer.targets.get('ui_response_ms', 100):
                    optimizer.logger.warning(
                        f"Slow GUI operation: {operation_name} took {duration_ms:.1f}ms"
                    )
                
                return result
                
            except Exception as e:
                optimizer.logger.error(f"Error in {operation_name}: {e}")
                raise
        
        return wrapper
    return decorator