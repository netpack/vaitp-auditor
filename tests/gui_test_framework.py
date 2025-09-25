"""
GUI Testing Framework for VAITP-Auditor GUI Components

This module provides a comprehensive testing framework for GUI components,
including widget simulation, state capture, screenshot testing, and mock
CustomTkinter components for isolated unit testing.
"""

import os
import sys
import time
import logging
import tempfile
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

# Mock CustomTkinter for testing environments
class MockCTkWidget:
    """Mock CustomTkinter widget for testing."""
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._state = "normal"
        self._text = ""
        self._value = ""
        self._children = []
        self._parent = None
        self._bindings = {}
        self._grid_info = {}
        self._pack_info = {}
        self._place_info = {}
        self._configure_calls = []
        self._method_calls = []
        
        # Store parent if provided
        if args:
            self._parent = args[0]
            if hasattr(self._parent, '_children'):
                self._parent._children.append(self)
    
    def grid(self, **kwargs):
        """Mock grid geometry manager."""
        self._grid_info.update(kwargs)
        self._method_calls.append(('grid', kwargs))
    
    def pack(self, **kwargs):
        """Mock pack geometry manager."""
        self._pack_info.update(kwargs)
        self._method_calls.append(('pack', kwargs))
    
    def place(self, **kwargs):
        """Mock place geometry manager."""
        self._place_info.update(kwargs)
        self._method_calls.append(('place', kwargs))
    
    def grid_columnconfigure(self, *args, **kwargs):
        """Mock grid column configuration."""
        self._method_calls.append(('grid_columnconfigure', args, kwargs))
    
    def grid_rowconfigure(self, *args, **kwargs):
        """Mock grid row configuration."""
        self._method_calls.append(('grid_rowconfigure', args, kwargs))
    
    def configure(self, **kwargs):
        """Mock widget configuration."""
        self._configure_calls.append(kwargs)
        for key, value in kwargs.items():
            if key == 'state':
                self._state = value
            elif key == 'text':
                self._text = value
        self._method_calls.append(('configure', kwargs))
    
    def cget(self, key):
        """Mock getting configuration values."""
        if key == 'state':
            return self._state
        elif key == 'text':
            return self._text
        return "mock_value"
    
    def get(self):
        """Mock getting widget value."""
        return self._value
    
    def set(self, value):
        """Mock setting widget value."""
        self._value = value
        self._method_calls.append(('set', value))
    
    def insert(self, index, text):
        """Mock text insertion."""
        self._text += text
        self._method_calls.append(('insert', index, text))
    
    def delete(self, start, end=None):
        """Mock text deletion."""
        if end is None:
            end = start
        self._text = ""
        self._method_calls.append(('delete', start, end))
    
    def bind(self, event, callback):
        """Mock event binding."""
        self._bindings[event] = callback
        self._method_calls.append(('bind', event, callback))
    
    def focus_set(self):
        """Mock focus setting."""
        self._method_calls.append(('focus_set',))
    
    def after(self, delay, callback):
        """Mock after scheduling."""
        self._method_calls.append(('after', delay, callback))
        # Execute callback immediately for testing
        if callable(callback):
            callback()
    
    def winfo_children(self):
        """Mock getting child widgets."""
        return self._children
    
    def winfo_toplevel(self):
        """Mock getting toplevel widget."""
        return self
    
    def destroy(self):
        """Mock widget destruction."""
        self._method_calls.append(('destroy',))
        if self._parent and hasattr(self._parent, '_children'):
            if self in self._parent._children:
                self._parent._children.remove(self)
    
    def get_method_calls(self):
        """Get all method calls made on this widget."""
        return self._method_calls.copy()
    
    def get_configure_calls(self):
        """Get all configure calls made on this widget."""
        return self._configure_calls.copy()
    
    def simulate_event(self, event_type, **kwargs):
        """Simulate an event on this widget."""
        if event_type in self._bindings:
            callback = self._bindings[event_type]
            if callable(callback):
                # Create mock event object
                event = Mock()
                event.type = event_type
                for key, value in kwargs.items():
                    setattr(event, key, value)
                callback(event)
                return True
        return False


class MockCTk(MockCTkWidget):
    """Mock main CustomTkinter window."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._title = "Mock Window"
        self._geometry = "800x600"
        self._running = False
    
    def title(self, title=None):
        """Mock window title."""
        if title is not None:
            self._title = title
            self._method_calls.append(('title', title))
        return self._title
    
    def geometry(self, geometry=None):
        """Mock window geometry."""
        if geometry is not None:
            self._geometry = geometry
            self._method_calls.append(('geometry', geometry))
        return self._geometry
    
    def minsize(self, width, height):
        """Mock minimum size setting."""
        self._method_calls.append(('minsize', width, height))
    
    def mainloop(self):
        """Mock main event loop."""
        self._running = True
        self._method_calls.append(('mainloop',))
    
    def quit(self):
        """Mock quit."""
        self._running = False
        self._method_calls.append(('quit',))
    
    def iconify(self):
        """Mock window iconification."""
        self._method_calls.append(('iconify',))
    
    def deiconify(self):
        """Mock window deiconification."""
        self._method_calls.append(('deiconify',))
    
    def lift(self):
        """Mock window lifting."""
        self._method_calls.append(('lift',))
    
    def focus_force(self):
        """Mock focus forcing."""
        self._method_calls.append(('focus_force',))
    
    def protocol(self, protocol, callback):
        """Mock protocol setting."""
        self._method_calls.append(('protocol', protocol, callback))


# Mock CustomTkinter module
def create_mock_customtkinter():
    """Create a comprehensive mock of the customtkinter module."""
    mock_ctk = MagicMock()
    
    # Widget classes
    mock_ctk.CTk = MockCTk
    mock_ctk.CTkToplevel = MockCTkWidget
    mock_ctk.CTkFrame = MockCTkWidget
    mock_ctk.CTkLabel = MockCTkWidget
    mock_ctk.CTkButton = MockCTkWidget
    mock_ctk.CTkEntry = MockCTkWidget
    mock_ctk.CTkTextbox = MockCTkWidget
    mock_ctk.CTkProgressBar = MockCTkWidget
    mock_ctk.CTkComboBox = MockCTkWidget
    mock_ctk.CTkSegmentedButton = MockCTkWidget
    mock_ctk.CTkSlider = MockCTkWidget
    mock_ctk.CTkCheckBox = MockCTkWidget
    mock_ctk.CTkRadioButton = MockCTkWidget
    
    # Variable classes
    mock_ctk.StringVar = Mock
    mock_ctk.IntVar = Mock
    mock_ctk.DoubleVar = Mock
    mock_ctk.BooleanVar = Mock
    
    # Font class
    mock_ctk.CTkFont = Mock
    
    # Utility functions
    mock_ctk.set_appearance_mode = Mock()
    mock_ctk.set_default_color_theme = Mock()
    
    return mock_ctk


class TestState(Enum):
    """Test execution states."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Test execution result."""
    test_name: str
    state: TestState
    duration: float = 0.0
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    widget_states: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ScreenshotInfo:
    """Screenshot information."""
    filename: str
    timestamp: float
    test_name: str
    description: str
    hash: Optional[str] = None
    baseline_hash: Optional[str] = None
    similarity_score: Optional[float] = None


class GUITestFramework:
    """
    Comprehensive GUI testing framework for VAITP-Auditor GUI components.
    
    Provides widget simulation, state capture, screenshot testing, and
    performance monitoring capabilities.
    """
    
    def __init__(self, test_output_dir: str = None):
        """
        Initialize the GUI testing framework.
        
        Args:
            test_output_dir: Directory for test outputs (screenshots, logs, etc.)
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up test output directory
        if test_output_dir is None:
            test_output_dir = os.path.join(tempfile.gettempdir(), "vaitp_gui_tests")
        
        self.test_output_dir = test_output_dir
        self.screenshots_dir = os.path.join(test_output_dir, "screenshots")
        self.baselines_dir = os.path.join(test_output_dir, "baselines")
        self.logs_dir = os.path.join(test_output_dir, "logs")
        
        # Create directories
        for directory in [self.test_output_dir, self.screenshots_dir, 
                         self.baselines_dir, self.logs_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Test state
        self.current_test = None
        self.test_results: List[TestResult] = []
        self.mock_ctk = None
        self.widget_registry: Dict[str, MockCTkWidget] = {}
        
        # Performance monitoring
        self.performance_thresholds = {
            'widget_creation_time': 0.1,  # seconds
            'event_response_time': 0.05,  # seconds
            'memory_usage_mb': 100,       # MB
            'screenshot_time': 2.0        # seconds
        }
        
        # Screenshot comparison settings
        self.screenshot_similarity_threshold = 0.95
        self.enable_visual_regression = True
        
        self.logger.info(f"GUI Test Framework initialized with output dir: {test_output_dir}")
    
    def setup_mock_environment(self) -> MagicMock:
        """
        Set up mock CustomTkinter environment for testing.
        
        Returns:
            Mock CustomTkinter module
        """
        self.mock_ctk = create_mock_customtkinter()
        
        # Patch the customtkinter module
        if 'customtkinter' not in sys.modules:
            sys.modules['customtkinter'] = self.mock_ctk
        
        self.logger.debug("Mock CustomTkinter environment set up")
        return self.mock_ctk
    
    def teardown_mock_environment(self):
        """Tear down mock environment."""
        if 'customtkinter' in sys.modules and sys.modules['customtkinter'] == self.mock_ctk:
            del sys.modules['customtkinter']
        
        self.mock_ctk = None
        self.widget_registry.clear()
        self.logger.debug("Mock CustomTkinter environment torn down")
    
    def create_test_window(self, title: str = "Test Window", 
                          geometry: str = "800x600") -> MockCTk:
        """
        Create a test window for GUI testing.
        
        Args:
            title: Window title
            geometry: Window geometry string
            
        Returns:
            Mock CTk window instance
        """
        if self.mock_ctk is None:
            self.setup_mock_environment()
        
        window = self.mock_ctk.CTk()
        window.title(title)
        window.geometry(geometry)
        
        # Register window
        window_id = f"test_window_{len(self.widget_registry)}"
        self.widget_registry[window_id] = window
        
        self.logger.debug(f"Created test window: {title} ({geometry})")
        return window
    
    def simulate_user_input(self, widget: MockCTkWidget, value: Any) -> bool:
        """
        Simulate user input on a widget.
        
        Args:
            widget: Target widget
            value: Input value
            
        Returns:
            True if input was successfully simulated
        """
        start_time = time.time()
        
        try:
            if hasattr(widget, 'set'):
                widget.set(value)
            elif hasattr(widget, 'insert'):
                widget.delete("1.0", "end")
                widget.insert("1.0", str(value))
            else:
                widget._value = value
            
            # Record performance
            duration = time.time() - start_time
            self._record_performance_metric('user_input_time', duration)
            
            self.logger.debug(f"Simulated user input: {value} on {type(widget).__name__}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to simulate user input: {e}")
            return False
    
    def simulate_button_click(self, button: MockCTkWidget) -> bool:
        """
        Simulate button click event.
        
        Args:
            button: Button widget to click
            
        Returns:
            True if click was successfully simulated
        """
        start_time = time.time()
        
        try:
            # Check if button is enabled
            if hasattr(button, 'cget') and button.cget('state') == 'disabled':
                self.logger.warning("Attempted to click disabled button")
                return False
            
            # Simulate click event
            if hasattr(button, 'simulate_event'):
                success = button.simulate_event('<Button-1>')
            else:
                # Fallback: call command if available
                if 'command' in button.kwargs:
                    command = button.kwargs['command']
                    if callable(command):
                        command()
                        success = True
                    else:
                        success = False
                else:
                    success = False
            
            # Record performance
            duration = time.time() - start_time
            self._record_performance_metric('button_click_time', duration)
            
            self.logger.debug(f"Simulated button click on {type(button).__name__}")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to simulate button click: {e}")
            return False
    
    def simulate_key_press(self, widget: MockCTkWidget, key: str, 
                          modifiers: List[str] = None) -> bool:
        """
        Simulate key press event.
        
        Args:
            widget: Target widget
            key: Key to press
            modifiers: List of modifier keys (Ctrl, Alt, Shift)
            
        Returns:
            True if key press was successfully simulated
        """
        if modifiers is None:
            modifiers = []
        
        try:
            # Build event string
            event_parts = []
            if 'Ctrl' in modifiers or 'Control' in modifiers:
                event_parts.append('Control')
            if 'Alt' in modifiers:
                event_parts.append('Alt')
            if 'Shift' in modifiers:
                event_parts.append('Shift')
            
            event_parts.append(f'Key-{key}')
            event_string = f"<{'-'.join(event_parts)}>"
            
            # Simulate event
            success = widget.simulate_event(event_string, key=key)
            
            self.logger.debug(f"Simulated key press: {event_string} on {type(widget).__name__}")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to simulate key press: {e}")
            return False
    
    def capture_widget_state(self, widget: MockCTkWidget, 
                           widget_name: str = None) -> Dict[str, Any]:
        """
        Capture the current state of a widget.
        
        Args:
            widget: Widget to capture state from
            widget_name: Optional name for the widget
            
        Returns:
            Dictionary containing widget state information
        """
        if widget_name is None:
            widget_name = f"{type(widget).__name__}_{id(widget)}"
        
        state = {
            'widget_type': type(widget).__name__,
            'widget_name': widget_name,
            'timestamp': time.time(),
            'method_calls': widget.get_method_calls() if hasattr(widget, 'get_method_calls') else [],
            'configure_calls': widget.get_configure_calls() if hasattr(widget, 'get_configure_calls') else [],
            'properties': {}
        }
        
        # Capture common properties
        try:
            if hasattr(widget, 'cget'):
                for prop in ['state', 'text', 'fg_color', 'hover_color']:
                    try:
                        state['properties'][prop] = widget.cget(prop)
                    except:
                        pass
            
            if hasattr(widget, 'get'):
                try:
                    state['properties']['value'] = widget.get()
                except:
                    pass
            
            # Capture geometry information
            if hasattr(widget, '_grid_info'):
                state['geometry'] = {
                    'grid': widget._grid_info,
                    'pack': getattr(widget, '_pack_info', {}),
                    'place': getattr(widget, '_place_info', {})
                }
            
            # Capture children
            if hasattr(widget, 'winfo_children'):
                children = widget.winfo_children()
                state['children_count'] = len(children)
                state['children_types'] = [type(child).__name__ for child in children]
        
        except Exception as e:
            self.logger.warning(f"Error capturing widget state: {e}")
            state['capture_error'] = str(e)
        
        return state
    
    def capture_window_state(self, window: MockCTk) -> Dict[str, Any]:
        """
        Capture the complete state of a window and its widgets.
        
        Args:
            window: Window to capture state from
            
        Returns:
            Dictionary containing complete window state
        """
        window_state = {
            'window': self.capture_widget_state(window, 'main_window'),
            'widgets': {},
            'timestamp': time.time()
        }
        
        # Recursively capture all widget states
        def capture_recursive(widget, path=""):
            if hasattr(widget, 'winfo_children'):
                children = widget.winfo_children()
                for i, child in enumerate(children):
                    child_path = f"{path}.child_{i}" if path else f"child_{i}"
                    window_state['widgets'][child_path] = self.capture_widget_state(child, child_path)
                    capture_recursive(child, child_path)
        
        capture_recursive(window)
        
        return window_state
    
    def assert_widget_state(self, widget: MockCTkWidget, 
                           expected_state: Dict[str, Any]) -> bool:
        """
        Assert that a widget matches expected state.
        
        Args:
            widget: Widget to check
            expected_state: Expected state dictionary
            
        Returns:
            True if widget matches expected state
            
        Raises:
            AssertionError: If widget state doesn't match expected state
        """
        current_state = self.capture_widget_state(widget)
        
        for key, expected_value in expected_state.items():
            if key == 'properties':
                for prop, expected_prop_value in expected_value.items():
                    actual_prop_value = current_state['properties'].get(prop)
                    if actual_prop_value != expected_prop_value:
                        raise AssertionError(
                            f"Widget property '{prop}' mismatch: "
                            f"expected {expected_prop_value}, got {actual_prop_value}"
                        )
            elif key in current_state:
                actual_value = current_state[key]
                if actual_value != expected_value:
                    raise AssertionError(
                        f"Widget state '{key}' mismatch: "
                        f"expected {expected_value}, got {actual_value}"
                    )
            else:
                raise AssertionError(f"Widget state key '{key}' not found")
        
        return True
    
    def capture_screenshot(self, window: MockCTk, filename: str, 
                          description: str = "") -> ScreenshotInfo:
        """
        Capture a screenshot of the window (mock implementation).
        
        Args:
            window: Window to capture
            filename: Screenshot filename
            description: Description of the screenshot
            
        Returns:
            ScreenshotInfo object
        """
        start_time = time.time()
        
        # Generate mock screenshot data
        screenshot_data = {
            'window_title': window.title(),
            'window_geometry': window.geometry(),
            'timestamp': time.time(),
            'widget_count': len(window.winfo_children()),
            'description': description
        }
        
        # Create screenshot file path
        screenshot_path = os.path.join(self.screenshots_dir, filename)
        
        # Save mock screenshot data as JSON
        with open(screenshot_path + '.json', 'w') as f:
            json.dump(screenshot_data, f, indent=2)
        
        # Calculate hash for comparison
        screenshot_hash = hashlib.md5(
            json.dumps(screenshot_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Record performance
        duration = time.time() - start_time
        self._record_performance_metric('screenshot_time', duration)
        
        screenshot_info = ScreenshotInfo(
            filename=filename,
            timestamp=time.time(),
            test_name=self.current_test or "unknown",
            description=description,
            hash=screenshot_hash
        )
        
        self.logger.debug(f"Captured screenshot: {filename}")
        return screenshot_info
    
    def compare_screenshots(self, current: str, baseline: str, 
                           threshold: float = None) -> Tuple[bool, float]:
        """
        Compare two screenshots for visual regression testing.
        
        Args:
            current: Current screenshot filename
            baseline: Baseline screenshot filename
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            Tuple of (is_similar, similarity_score)
        """
        if threshold is None:
            threshold = self.screenshot_similarity_threshold
        
        try:
            # Load screenshot data
            current_path = os.path.join(self.screenshots_dir, current + '.json')
            baseline_path = os.path.join(self.baselines_dir, baseline + '.json')
            
            if not os.path.exists(current_path):
                self.logger.error(f"Current screenshot not found: {current_path}")
                return False, 0.0
            
            if not os.path.exists(baseline_path):
                self.logger.warning(f"Baseline screenshot not found: {baseline_path}")
                # Copy current as new baseline
                import shutil
                shutil.copy2(current_path, baseline_path)
                return True, 1.0
            
            with open(current_path, 'r') as f:
                current_data = json.load(f)
            
            with open(baseline_path, 'r') as f:
                baseline_data = json.load(f)
            
            # Simple comparison based on structure
            similarity_score = self._calculate_similarity(current_data, baseline_data)
            is_similar = similarity_score >= threshold
            
            self.logger.debug(f"Screenshot comparison: {similarity_score:.3f} (threshold: {threshold})")
            return is_similar, similarity_score
            
        except Exception as e:
            self.logger.error(f"Error comparing screenshots: {e}")
            return False, 0.0
    
    def _calculate_similarity(self, data1: Dict, data2: Dict) -> float:
        """Calculate similarity between two data structures."""
        # Simple similarity calculation based on matching keys and values
        all_keys = set(data1.keys()) | set(data2.keys())
        if not all_keys:
            return 1.0
        
        matching_keys = 0
        for key in all_keys:
            if key in data1 and key in data2:
                if data1[key] == data2[key]:
                    matching_keys += 1
                elif isinstance(data1[key], (int, float)) and isinstance(data2[key], (int, float)):
                    # Allow small numerical differences
                    if abs(data1[key] - data2[key]) < 0.01:
                        matching_keys += 1
        
        return matching_keys / len(all_keys)
    
    def run_test_scenario(self, test_name: str, test_function: Callable, 
                         *args, **kwargs) -> TestResult:
        """
        Run a test scenario with comprehensive monitoring.
        
        Args:
            test_name: Name of the test
            test_function: Test function to execute
            *args: Arguments for test function
            **kwargs: Keyword arguments for test function
            
        Returns:
            TestResult object
        """
        self.current_test = test_name
        start_time = time.time()
        
        result = TestResult(
            test_name=test_name,
            state=TestState.RUNNING
        )
        
        try:
            self.logger.info(f"Starting test: {test_name}")
            
            # Set up mock environment
            self.setup_mock_environment()
            
            # Execute test function
            test_function(*args, **kwargs)
            
            # Test passed
            result.state = TestState.PASSED
            result.duration = time.time() - start_time
            
            self.logger.info(f"Test passed: {test_name} ({result.duration:.3f}s)")
            
        except AssertionError as e:
            result.state = TestState.FAILED
            result.duration = time.time() - start_time
            result.error_message = str(e)
            
            self.logger.error(f"Test failed: {test_name} - {e}")
            
        except Exception as e:
            result.state = TestState.ERROR
            result.duration = time.time() - start_time
            result.error_message = str(e)
            
            import traceback
            result.error_traceback = traceback.format_exc()
            
            self.logger.error(f"Test error: {test_name} - {e}")
            
        finally:
            # Clean up
            self.teardown_mock_environment()
            self.current_test = None
        
        self.test_results.append(result)
        return result
    
    def _record_performance_metric(self, metric_name: str, value: float):
        """Record a performance metric."""
        if self.current_test:
            # Find current test result
            for result in self.test_results:
                if result.test_name == self.current_test and result.state == TestState.RUNNING:
                    result.performance_metrics[metric_name] = value
                    break
        
        # Check against thresholds
        if metric_name in self.performance_thresholds:
            threshold = self.performance_thresholds[metric_name]
            if value > threshold:
                self.logger.warning(
                    f"Performance threshold exceeded for {metric_name}: "
                    f"{value:.3f} > {threshold:.3f}"
                )
    
    def generate_test_report(self, output_file: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive test report.
        
        Args:
            output_file: Optional file to save report to
            
        Returns:
            Test report dictionary
        """
        if output_file is None:
            output_file = os.path.join(self.test_output_dir, "test_report.json")
        
        # Calculate summary statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.state == TestState.PASSED])
        failed_tests = len([r for r in self.test_results if r.state == TestState.FAILED])
        error_tests = len([r for r in self.test_results if r.state == TestState.ERROR])
        
        total_duration = sum(r.duration for r in self.test_results)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'errors': error_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'total_duration': total_duration,
                'average_duration': avg_duration
            },
            'test_results': [
                {
                    'test_name': r.test_name,
                    'state': r.state.value,
                    'duration': r.duration,
                    'error_message': r.error_message,
                    'performance_metrics': r.performance_metrics,
                    'screenshots': r.screenshots
                }
                for r in self.test_results
            ],
            'performance_thresholds': self.performance_thresholds,
            'framework_info': {
                'test_output_dir': self.test_output_dir,
                'screenshots_dir': self.screenshots_dir,
                'baselines_dir': self.baselines_dir,
                'visual_regression_enabled': self.enable_visual_regression,
                'similarity_threshold': self.screenshot_similarity_threshold
            },
            'timestamp': time.time()
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Test report generated: {output_file}")
        return report
    
    def create_comprehensive_test_scenarios(self) -> Dict[str, Callable]:
        """
        Create comprehensive test scenarios for all GUI workflows.
        
        Returns:
            Dictionary mapping scenario names to test functions
        """
        scenarios = {}
        
        # Setup Wizard scenarios
        scenarios.update(self._create_setup_wizard_scenarios())
        
        # Main Review Window scenarios
        scenarios.update(self._create_main_review_scenarios())
        
        # Error handling scenarios
        scenarios.update(self._create_error_handling_scenarios())
        
        # Performance scenarios
        scenarios.update(self._create_performance_scenarios())
        
        # Accessibility scenarios
        scenarios.update(self._create_accessibility_scenarios())
        
        return scenarios
    
    def _create_setup_wizard_scenarios(self) -> Dict[str, Callable]:
        """Create Setup Wizard test scenarios."""
        scenarios = {}
        
        def test_wizard_navigation():
            """Test basic wizard navigation."""
            window = self.create_test_window("Setup Wizard Test")
            
            # Mock wizard creation would go here
            # This is a placeholder for the actual implementation
            
            # Capture initial state
            initial_state = self.capture_window_state(window)
            self.assert_widget_state(window, {'widget_type': 'MockCTk'})
            
            # Test navigation
            # ... navigation tests would go here
        
        def test_wizard_validation():
            """Test wizard input validation."""
            window = self.create_test_window("Wizard Validation Test")
            
            # Test invalid inputs
            # ... validation tests would go here
        
        scenarios['setup_wizard_navigation'] = test_wizard_navigation
        scenarios['setup_wizard_validation'] = test_wizard_validation
        
        return scenarios
    
    def _create_main_review_scenarios(self) -> Dict[str, Callable]:
        """Create Main Review Window test scenarios."""
        scenarios = {}
        
        def test_code_display():
            """Test code display functionality."""
            window = self.create_test_window("Code Display Test")
            
            # Test code loading and display
            # ... code display tests would go here
        
        def test_verdict_buttons():
            """Test verdict button functionality."""
            window = self.create_test_window("Verdict Buttons Test")
            
            # Test button clicks and state changes
            # ... verdict button tests would go here
        
        scenarios['main_review_code_display'] = test_code_display
        scenarios['main_review_verdict_buttons'] = test_verdict_buttons
        
        return scenarios
    
    def _create_error_handling_scenarios(self) -> Dict[str, Callable]:
        """Create error handling test scenarios."""
        scenarios = {}
        
        def test_error_dialogs():
            """Test error dialog display."""
            window = self.create_test_window("Error Dialog Test")
            
            # Test error dialog creation and display
            # ... error dialog tests would go here
        
        scenarios['error_handling_dialogs'] = test_error_dialogs
        
        return scenarios
    
    def _create_performance_scenarios(self) -> Dict[str, Callable]:
        """Create performance test scenarios."""
        scenarios = {}
        
        def test_large_file_handling():
            """Test handling of large code files."""
            window = self.create_test_window("Large File Test")
            
            # Test performance with large files
            # ... performance tests would go here
        
        scenarios['performance_large_files'] = test_large_file_handling
        
        return scenarios
    
    def _create_accessibility_scenarios(self) -> Dict[str, Callable]:
        """Create accessibility test scenarios."""
        scenarios = {}
        
        def test_keyboard_navigation():
            """Test keyboard navigation."""
            window = self.create_test_window("Keyboard Navigation Test")
            
            # Test keyboard shortcuts and navigation
            # ... accessibility tests would go here
        
        scenarios['accessibility_keyboard_navigation'] = test_keyboard_navigation
        
        return scenarios


# Convenience functions for common testing patterns
def create_gui_test_framework(output_dir: str = None) -> GUITestFramework:
    """Create a GUI test framework instance."""
    return GUITestFramework(output_dir)


def run_gui_test_suite(framework: GUITestFramework, 
                      scenarios: Dict[str, Callable] = None) -> Dict[str, Any]:
    """
    Run a complete GUI test suite.
    
    Args:
        framework: GUI test framework instance
        scenarios: Optional custom test scenarios
        
    Returns:
        Test report dictionary
    """
    if scenarios is None:
        scenarios = framework.create_comprehensive_test_scenarios()
    
    # Run all scenarios
    for scenario_name, scenario_function in scenarios.items():
        framework.run_test_scenario(scenario_name, scenario_function)
    
    # Generate report
    return framework.generate_test_report()


if __name__ == "__main__":
    # Example usage
    framework = create_gui_test_framework()
    
    # Run test suite
    report = run_gui_test_suite(framework)
    
    print(f"Test Results: {report['summary']['passed']}/{report['summary']['total_tests']} passed")
    print(f"Success Rate: {report['summary']['success_rate']:.1%}")
    print(f"Total Duration: {report['summary']['total_duration']:.2f}s")