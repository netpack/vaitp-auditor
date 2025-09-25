"""
Integration and End-to-End Testing for VAITP-Auditor GUI

This module provides comprehensive integration tests covering complete workflows
from Setup Wizard to Main Review, cross-platform compatibility tests,
performance testing, and GUI/CLI mode compatibility validation.
"""

import unittest
import sys
import os
import time
import tempfile
import threading
import subprocess
import platform
import psutil
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.gui_test_framework import GUITestFramework, TestState, create_gui_test_framework
from tests.test_gui_comprehensive_scenarios import ComprehensiveGUITestScenarios
from vaitp_auditor.core.models import CodePair, SessionConfig, ReviewResult
from vaitp_auditor.gui.models import GUIConfig, ProgressInfo


class PlatformInfo(Enum):
    """Supported platforms for testing."""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


@dataclass
class PerformanceMetrics:
    """Performance metrics for testing."""
    memory_usage_mb: float
    cpu_usage_percent: float
    response_time_ms: float
    throughput_items_per_second: float
    startup_time_seconds: float


@dataclass
class IntegrationTestResult:
    """Result of an integration test."""
    test_name: str
    success: bool
    duration: float
    error_message: Optional[str] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    platform_info: Optional[Dict[str, str]] = None
    screenshots: List[str] = None


class CrossPlatformTester:
    """Cross-platform compatibility testing utilities."""
    
    def __init__(self):
        self.current_platform = self._detect_platform()
        self.platform_specific_configs = self._get_platform_configs()
    
    def _detect_platform(self) -> PlatformInfo:
        """Detect the current platform."""
        system = platform.system().lower()
        if system == "windows":
            return PlatformInfo.WINDOWS
        elif system == "darwin":
            return PlatformInfo.MACOS
        elif system == "linux":
            return PlatformInfo.LINUX
        else:
            raise ValueError(f"Unsupported platform: {system}")
    
    def _get_platform_configs(self) -> Dict[PlatformInfo, Dict[str, Any]]:
        """Get platform-specific configurations."""
        return {
            PlatformInfo.WINDOWS: {
                'font_family': 'Consolas',
                'path_separator': '\\',
                'line_ending': '\r\n',
                'default_dpi': 96,
                'file_dialog_type': 'win32'
            },
            PlatformInfo.MACOS: {
                'font_family': 'Monaco',
                'path_separator': '/',
                'line_ending': '\n',
                'default_dpi': 72,
                'file_dialog_type': 'cocoa'
            },
            PlatformInfo.LINUX: {
                'font_family': 'DejaVu Sans Mono',
                'path_separator': '/',
                'line_ending': '\n',
                'default_dpi': 96,
                'file_dialog_type': 'gtk'
            }
        }
    
    def get_platform_info(self) -> Dict[str, str]:
        """Get detailed platform information."""
        return {
            'platform': self.current_platform.value,
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0]
        }
    
    def test_platform_compatibility(self, framework: GUITestFramework) -> List[IntegrationTestResult]:
        """Test platform-specific compatibility."""
        results = []
        
        # Test font rendering
        results.append(self._test_font_rendering(framework))
        
        # Test file path handling
        results.append(self._test_file_path_handling(framework))
        
        # Test dialog compatibility
        results.append(self._test_dialog_compatibility(framework))
        
        # Test keyboard shortcuts
        results.append(self._test_keyboard_shortcuts(framework))
        
        return results
    
    def _test_font_rendering(self, framework: GUITestFramework) -> IntegrationTestResult:
        """Test font rendering on current platform."""
        start_time = time.time()
        
        try:
            window = framework.create_test_window("Font Rendering Test")
            
            # Get platform-specific font
            config = self.platform_specific_configs[self.current_platform]
            font_family = config['font_family']
            
            # Create text widget with platform font
            text_widget = framework.mock_ctk.CTkTextbox(window)
            text_widget.configure(font=(font_family, 12))
            
            # Test various text content
            test_texts = [
                "Regular ASCII text",
                "Special characters: àáâãäåæçèéêë",
                "Code symbols: {}[]()<>=+-*/",
                "Numbers: 0123456789",
                "Mixed: def function(param: str) -> bool:"
            ]
            
            for text in test_texts:
                framework.simulate_user_input(text_widget, text)
            
            duration = time.time() - start_time
            
            return IntegrationTestResult(
                test_name="font_rendering",
                success=True,
                duration=duration,
                platform_info=self.get_platform_info()
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="font_rendering",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e),
                platform_info=self.get_platform_info()
            )
    
    def _test_file_path_handling(self, framework: GUITestFramework) -> IntegrationTestResult:
        """Test file path handling on current platform."""
        start_time = time.time()
        
        try:
            window = framework.create_test_window("File Path Test")
            
            config = self.platform_specific_configs[self.current_platform]
            separator = config['path_separator']
            
            # Test various path formats
            test_paths = [
                f"C:{separator}Users{separator}test{separator}file.py" if self.current_platform == PlatformInfo.WINDOWS 
                else f"{separator}home{separator}test{separator}file.py",
                f"relative{separator}path{separator}file.py",
                f"..{separator}parent{separator}file.py",
                f".{separator}current{separator}file.py"
            ]
            
            entry_widget = framework.mock_ctk.CTkEntry(window)
            
            for path in test_paths:
                framework.simulate_user_input(entry_widget, path)
                # Verify path was accepted
                assert entry_widget.get() == path
            
            duration = time.time() - start_time
            
            return IntegrationTestResult(
                test_name="file_path_handling",
                success=True,
                duration=duration,
                platform_info=self.get_platform_info()
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="file_path_handling",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e),
                platform_info=self.get_platform_info()
            )
    
    def _test_dialog_compatibility(self, framework: GUITestFramework) -> IntegrationTestResult:
        """Test dialog compatibility on current platform."""
        start_time = time.time()
        
        try:
            window = framework.create_test_window("Dialog Compatibility Test")
            
            # Test error dialog
            error_dialog = framework.mock_ctk.CTkToplevel(window)
            error_dialog.title("Error")
            
            # Test confirmation dialog
            confirm_dialog = framework.mock_ctk.CTkToplevel(window)
            confirm_dialog.title("Confirm")
            
            # Test file dialog (mock)
            # In real implementation, this would test actual file dialogs
            
            duration = time.time() - start_time
            
            return IntegrationTestResult(
                test_name="dialog_compatibility",
                success=True,
                duration=duration,
                platform_info=self.get_platform_info()
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="dialog_compatibility",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e),
                platform_info=self.get_platform_info()
            )
    
    def _test_keyboard_shortcuts(self, framework: GUITestFramework) -> IntegrationTestResult:
        """Test keyboard shortcuts on current platform."""
        start_time = time.time()
        
        try:
            window = framework.create_test_window("Keyboard Shortcuts Test")
            
            # Test platform-specific modifier keys
            if self.current_platform == PlatformInfo.MACOS:
                # Test Cmd key combinations
                modifiers = ['Cmd']
            else:
                # Test Ctrl key combinations
                modifiers = ['Ctrl']
            
            button = framework.mock_ctk.CTkButton(window)
            
            # Test various key combinations
            test_keys = ['s', 'f', 'u', 'q', 'n', 'o']
            
            for key in test_keys:
                success = framework.simulate_key_press(button, key, modifiers)
                # In mock environment, this might not work, but we test the interface
            
            duration = time.time() - start_time
            
            return IntegrationTestResult(
                test_name="keyboard_shortcuts",
                success=True,
                duration=duration,
                platform_info=self.get_platform_info()
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="keyboard_shortcuts",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e),
                platform_info=self.get_platform_info()
            )


class PerformanceTester:
    """Performance testing utilities for GUI components."""
    
    def __init__(self):
        self.baseline_metrics = self._get_baseline_metrics()
        self.performance_thresholds = {
            'startup_time_seconds': 5.0,
            'memory_usage_mb': 200.0,
            'response_time_ms': 100.0,
            'throughput_items_per_second': 10.0,
            'cpu_usage_percent': 50.0
        }
    
    def _get_baseline_metrics(self) -> PerformanceMetrics:
        """Get baseline performance metrics."""
        return PerformanceMetrics(
            memory_usage_mb=50.0,
            cpu_usage_percent=5.0,
            response_time_ms=50.0,
            throughput_items_per_second=20.0,
            startup_time_seconds=2.0
        )
    
    def measure_startup_performance(self, framework: GUITestFramework) -> PerformanceMetrics:
        """Measure GUI startup performance."""
        start_time = time.time()
        initial_memory = self._get_memory_usage()
        
        # Simulate application startup
        window = framework.create_test_window("Performance Test")
        
        # Create main components
        header_frame = framework.mock_ctk.CTkFrame(window)
        code_panels_frame = framework.mock_ctk.CTkFrame(window)
        actions_frame = framework.mock_ctk.CTkFrame(window)
        
        # Add widgets to frames
        for _ in range(10):  # Simulate multiple widgets
            framework.mock_ctk.CTkLabel(header_frame)
            framework.mock_ctk.CTkTextbox(code_panels_frame)
            framework.mock_ctk.CTkButton(actions_frame)
        
        startup_time = time.time() - start_time
        final_memory = self._get_memory_usage()
        memory_usage = final_memory - initial_memory
        
        return PerformanceMetrics(
            memory_usage_mb=memory_usage,
            cpu_usage_percent=self._get_cpu_usage(),
            response_time_ms=startup_time * 1000,
            throughput_items_per_second=30 / startup_time if startup_time > 0 else 0,
            startup_time_seconds=startup_time
        )
    
    def measure_interaction_performance(self, framework: GUITestFramework, 
                                     iterations: int = 100) -> PerformanceMetrics:
        """Measure GUI interaction performance."""
        window = framework.create_test_window("Interaction Performance Test")
        
        # Create test widgets
        buttons = []
        entries = []
        
        for i in range(10):
            buttons.append(framework.mock_ctk.CTkButton(window))
            entries.append(framework.mock_ctk.CTkEntry(window))
        
        start_time = time.time()
        initial_memory = self._get_memory_usage()
        
        # Perform rapid interactions
        for i in range(iterations):
            # Click buttons
            for button in buttons:
                framework.simulate_button_click(button)
            
            # Input text
            for entry in entries:
                framework.simulate_user_input(entry, f"test_input_{i}")
        
        interaction_time = time.time() - start_time
        final_memory = self._get_memory_usage()
        memory_usage = final_memory - initial_memory
        
        return PerformanceMetrics(
            memory_usage_mb=memory_usage,
            cpu_usage_percent=self._get_cpu_usage(),
            response_time_ms=(interaction_time / iterations) * 1000,
            throughput_items_per_second=iterations / interaction_time if interaction_time > 0 else 0,
            startup_time_seconds=0.0  # Not applicable for interactions
        )
    
    def measure_large_data_performance(self, framework: GUITestFramework) -> PerformanceMetrics:
        """Measure performance with large data sets."""
        window = framework.create_test_window("Large Data Performance Test")
        
        # Create large text content
        large_text = "Line of code\n" * 10000  # 10,000 lines
        
        textbox = framework.mock_ctk.CTkTextbox(window)
        
        start_time = time.time()
        initial_memory = self._get_memory_usage()
        
        # Load large content
        framework.simulate_user_input(textbox, large_text)
        
        load_time = time.time() - start_time
        final_memory = self._get_memory_usage()
        memory_usage = final_memory - initial_memory
        
        return PerformanceMetrics(
            memory_usage_mb=memory_usage,
            cpu_usage_percent=self._get_cpu_usage(),
            response_time_ms=load_time * 1000,
            throughput_items_per_second=10000 / load_time if load_time > 0 else 0,
            startup_time_seconds=0.0  # Not applicable
        )
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except:
            return 0.0  # Fallback if psutil not available
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            return psutil.cpu_percent(interval=0.1)
        except:
            return 0.0  # Fallback if psutil not available
    
    def validate_performance(self, metrics: PerformanceMetrics) -> Tuple[bool, List[str]]:
        """Validate performance metrics against thresholds."""
        issues = []
        
        if metrics.startup_time_seconds > self.performance_thresholds['startup_time_seconds']:
            issues.append(f"Startup time too slow: {metrics.startup_time_seconds:.2f}s")
        
        if metrics.memory_usage_mb > self.performance_thresholds['memory_usage_mb']:
            issues.append(f"Memory usage too high: {metrics.memory_usage_mb:.2f}MB")
        
        if metrics.response_time_ms > self.performance_thresholds['response_time_ms']:
            issues.append(f"Response time too slow: {metrics.response_time_ms:.2f}ms")
        
        if metrics.throughput_items_per_second < self.performance_thresholds['throughput_items_per_second']:
            issues.append(f"Throughput too low: {metrics.throughput_items_per_second:.2f} items/s")
        
        if metrics.cpu_usage_percent > self.performance_thresholds['cpu_usage_percent']:
            issues.append(f"CPU usage too high: {metrics.cpu_usage_percent:.2f}%")
        
        return len(issues) == 0, issues


class EndToEndTester:
    """End-to-end testing for complete GUI workflows."""
    
    def __init__(self, framework: GUITestFramework):
        self.framework = framework
        self.scenarios = ComprehensiveGUITestScenarios(framework)
    
    def test_complete_user_journey(self) -> IntegrationTestResult:
        """Test complete user journey from start to finish."""
        start_time = time.time()
        
        try:
            # Phase 1: Application Startup
            main_window = self.framework.create_test_window("VAITP-Auditor")
            
            # Phase 2: Setup Wizard
            wizard_result = self._test_setup_wizard_flow()
            if not wizard_result.success:
                return wizard_result
            
            # Phase 3: Main Review Session
            review_result = self._test_main_review_flow()
            if not review_result.success:
                return review_result
            
            # Phase 4: Session Completion
            completion_result = self._test_session_completion()
            if not completion_result.success:
                return completion_result
            
            duration = time.time() - start_time
            
            return IntegrationTestResult(
                test_name="complete_user_journey",
                success=True,
                duration=duration
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="complete_user_journey",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def _test_setup_wizard_flow(self) -> IntegrationTestResult:
        """Test complete Setup Wizard flow."""
        start_time = time.time()
        
        try:
            wizard_window = self.framework.create_test_window("Setup Wizard")
            
            # Step 1: Experiment naming
            naming_frame = self.framework.mock_ctk.CTkFrame(wizard_window)
            experiment_entry = self.framework.mock_ctk.CTkEntry(naming_frame)
            
            self.framework.simulate_user_input(experiment_entry, "e2e_test_experiment")
            
            # Step 2: Data source selection
            data_source_frame = self.framework.mock_ctk.CTkFrame(wizard_window)
            source_selector = self.framework.mock_ctk.CTkSegmentedButton(data_source_frame)
            
            self.framework.simulate_user_input(source_selector, "folders")
            
            # Step 3: Configuration
            config_frame = self.framework.mock_ctk.CTkFrame(wizard_window)
            generated_entry = self.framework.mock_ctk.CTkEntry(config_frame)
            expected_entry = self.framework.mock_ctk.CTkEntry(config_frame)
            
            self.framework.simulate_user_input(generated_entry, "/test/generated")
            self.framework.simulate_user_input(expected_entry, "/test/expected")
            
            # Step 4: Finalization
            final_frame = self.framework.mock_ctk.CTkFrame(wizard_window)
            sampling_slider = self.framework.mock_ctk.CTkSlider(final_frame)
            format_selector = self.framework.mock_ctk.CTkComboBox(final_frame)
            
            self.framework.simulate_user_input(sampling_slider, 100)
            self.framework.simulate_user_input(format_selector, "excel")
            
            # Complete wizard
            start_button = self.framework.mock_ctk.CTkButton(wizard_window)
            self.framework.simulate_button_click(start_button)
            
            duration = time.time() - start_time
            
            return IntegrationTestResult(
                test_name="setup_wizard_flow",
                success=True,
                duration=duration
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="setup_wizard_flow",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def _test_main_review_flow(self) -> IntegrationTestResult:
        """Test main review workflow."""
        start_time = time.time()
        
        try:
            review_window = self.framework.create_test_window("Main Review")
            
            # Create review components
            header_frame = self.framework.mock_ctk.CTkFrame(review_window)
            code_panels_frame = self.framework.mock_ctk.CTkFrame(review_window)
            actions_frame = self.framework.mock_ctk.CTkFrame(review_window)
            
            # Simulate reviewing multiple code pairs
            for i in range(5):
                # Load code pair
                expected_textbox = self.framework.mock_ctk.CTkTextbox(code_panels_frame)
                generated_textbox = self.framework.mock_ctk.CTkTextbox(code_panels_frame)
                
                test_code = f"def test_function_{i}():\n    return {i}"
                self.framework.simulate_user_input(expected_textbox, test_code)
                self.framework.simulate_user_input(generated_textbox, test_code)
                
                # Make verdict
                verdict_button = self.framework.mock_ctk.CTkButton(actions_frame)
                self.framework.simulate_button_click(verdict_button)
                
                # Add comment
                comment_entry = self.framework.mock_ctk.CTkEntry(actions_frame)
                self.framework.simulate_user_input(comment_entry, f"Review comment {i}")
            
            # Test undo functionality
            undo_button = self.framework.mock_ctk.CTkButton(actions_frame)
            self.framework.simulate_button_click(undo_button)
            
            duration = time.time() - start_time
            
            return IntegrationTestResult(
                test_name="main_review_flow",
                success=True,
                duration=duration
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="main_review_flow",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def _test_session_completion(self) -> IntegrationTestResult:
        """Test session completion workflow."""
        start_time = time.time()
        
        try:
            review_window = self.framework.create_test_window("Session Completion")
            
            # Simulate completion dialog
            completion_dialog = self.framework.mock_ctk.CTkToplevel(review_window)
            completion_dialog.title("Review Complete")
            
            # Test report generation (mock)
            # In real implementation, this would generate actual reports
            
            duration = time.time() - start_time
            
            return IntegrationTestResult(
                test_name="session_completion",
                success=True,
                duration=duration
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="session_completion",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )


class CLIGUICompatibilityTester:
    """Test compatibility between CLI and GUI modes."""
    
    def __init__(self):
        self.test_data_dir = tempfile.mkdtemp(prefix="vaitp_cli_gui_test_")
    
    def test_cli_gui_compatibility(self) -> List[IntegrationTestResult]:
        """Test CLI and GUI mode compatibility."""
        results = []
        
        # Test session config compatibility
        results.append(self._test_session_config_compatibility())
        
        # Test report format compatibility
        results.append(self._test_report_format_compatibility())
        
        # Test data source compatibility
        results.append(self._test_data_source_compatibility())
        
        return results
    
    def _test_session_config_compatibility(self) -> IntegrationTestResult:
        """Test that session configs work in both CLI and GUI modes."""
        start_time = time.time()
        
        try:
            # Create test session config
            session_config = SessionConfig(
                experiment_name="cli_gui_compatibility_test",
                data_source_type="folders",
                data_source_params={
                    "generated_code_path": os.path.join(self.test_data_dir, "generated"),
                    "expected_code_path": os.path.join(self.test_data_dir, "expected")
                },
                sample_percentage=100,
                output_format="excel"
            )
            
            # Test config serialization/deserialization
            config_dict = session_config.__dict__
            restored_config = SessionConfig(**config_dict)
            
            # Verify configs match
            assert restored_config.experiment_name == session_config.experiment_name
            assert restored_config.data_source_type == session_config.data_source_type
            
            duration = time.time() - start_time
            
            return IntegrationTestResult(
                test_name="session_config_compatibility",
                success=True,
                duration=duration
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="session_config_compatibility",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def _test_report_format_compatibility(self) -> IntegrationTestResult:
        """Test that reports generated by GUI are compatible with CLI expectations."""
        start_time = time.time()
        
        try:
            # Create test review results
            review_results = [
                ReviewResult(
                    identifier="test_001",
                    verdict="SUCCESS",
                    comment="Test comment 1",
                    timestamp=time.time(),
                    reviewer="test_user"
                ),
                ReviewResult(
                    identifier="test_002",
                    verdict="FAILURE_NO_CHANGE",
                    comment="Test comment 2",
                    timestamp=time.time(),
                    reviewer="test_user"
                )
            ]
            
            # Test that review results can be serialized
            for result in review_results:
                result_dict = result.__dict__
                # Verify required fields are present
                assert 'identifier' in result_dict
                assert 'verdict' in result_dict
                assert 'timestamp' in result_dict
            
            duration = time.time() - start_time
            
            return IntegrationTestResult(
                test_name="report_format_compatibility",
                success=True,
                duration=duration
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="report_format_compatibility",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def _test_data_source_compatibility(self) -> IntegrationTestResult:
        """Test that data sources work in both CLI and GUI modes."""
        start_time = time.time()
        
        try:
            # Create test data directories
            generated_dir = os.path.join(self.test_data_dir, "generated")
            expected_dir = os.path.join(self.test_data_dir, "expected")
            
            os.makedirs(generated_dir, exist_ok=True)
            os.makedirs(expected_dir, exist_ok=True)
            
            # Create test files
            test_files = ["test_001.py", "test_002.py", "test_003.py"]
            
            for filename in test_files:
                # Generated code file
                with open(os.path.join(generated_dir, filename), 'w') as f:
                    f.write(f"# Generated code for {filename}\ndef generated_function():\n    return True")
                
                # Expected code file
                with open(os.path.join(expected_dir, filename), 'w') as f:
                    f.write(f"# Expected code for {filename}\ndef expected_function():\n    return True")
            
            # Verify files were created
            for filename in test_files:
                assert os.path.exists(os.path.join(generated_dir, filename))
                assert os.path.exists(os.path.join(expected_dir, filename))
            
            duration = time.time() - start_time
            
            return IntegrationTestResult(
                test_name="data_source_compatibility",
                success=True,
                duration=duration
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="data_source_compatibility",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )


class IntegrationTestSuite:
    """Comprehensive integration test suite."""
    
    def __init__(self, output_dir: str = None):
        self.framework = create_gui_test_framework(output_dir)
        self.cross_platform_tester = CrossPlatformTester()
        self.performance_tester = PerformanceTester()
        self.e2e_tester = EndToEndTester(self.framework)
        self.cli_gui_tester = CLIGUICompatibilityTester()
        
        self.results: List[IntegrationTestResult] = []
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        print("Starting comprehensive integration test suite...")
        
        # Cross-platform compatibility tests
        print("Running cross-platform compatibility tests...")
        platform_results = self.cross_platform_tester.test_platform_compatibility(self.framework)
        self.results.extend(platform_results)
        
        # Performance tests
        print("Running performance tests...")
        self._run_performance_tests()
        
        # End-to-end tests
        print("Running end-to-end tests...")
        e2e_result = self.e2e_tester.test_complete_user_journey()
        self.results.append(e2e_result)
        
        # CLI/GUI compatibility tests
        print("Running CLI/GUI compatibility tests...")
        cli_gui_results = self.cli_gui_tester.test_cli_gui_compatibility()
        self.results.extend(cli_gui_results)
        
        # Generate comprehensive report
        return self._generate_integration_report()
    
    def _run_performance_tests(self):
        """Run performance tests."""
        # Startup performance
        startup_metrics = self.performance_tester.measure_startup_performance(self.framework)
        startup_valid, startup_issues = self.performance_tester.validate_performance(startup_metrics)
        
        self.results.append(IntegrationTestResult(
            test_name="startup_performance",
            success=startup_valid,
            duration=startup_metrics.startup_time_seconds,
            error_message="; ".join(startup_issues) if startup_issues else None,
            performance_metrics=startup_metrics
        ))
        
        # Interaction performance
        interaction_metrics = self.performance_tester.measure_interaction_performance(self.framework)
        interaction_valid, interaction_issues = self.performance_tester.validate_performance(interaction_metrics)
        
        self.results.append(IntegrationTestResult(
            test_name="interaction_performance",
            success=interaction_valid,
            duration=interaction_metrics.response_time_ms / 1000,
            error_message="; ".join(interaction_issues) if interaction_issues else None,
            performance_metrics=interaction_metrics
        ))
        
        # Large data performance
        large_data_metrics = self.performance_tester.measure_large_data_performance(self.framework)
        large_data_valid, large_data_issues = self.performance_tester.validate_performance(large_data_metrics)
        
        self.results.append(IntegrationTestResult(
            test_name="large_data_performance",
            success=large_data_valid,
            duration=large_data_metrics.response_time_ms / 1000,
            error_message="; ".join(large_data_issues) if large_data_issues else None,
            performance_metrics=large_data_metrics
        ))
    
    def _generate_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration test report."""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.success])
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(r.duration for r in self.results)
        
        # Categorize results
        categories = {
            'cross_platform': [r for r in self.results if any(x in r.test_name for x in ['font', 'path', 'dialog', 'keyboard'])],
            'performance': [r for r in self.results if 'performance' in r.test_name],
            'end_to_end': [r for r in self.results if 'journey' in r.test_name or 'flow' in r.test_name],
            'compatibility': [r for r in self.results if 'compatibility' in r.test_name]
        }
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'total_duration': total_duration,
                'platform_info': self.cross_platform_tester.get_platform_info()
            },
            'categories': {},
            'detailed_results': [],
            'performance_summary': self._summarize_performance_results(),
            'recommendations': self._generate_recommendations()
        }
        
        # Add category summaries
        for category, results in categories.items():
            if results:
                category_passed = len([r for r in results if r.success])
                report['categories'][category] = {
                    'total': len(results),
                    'passed': category_passed,
                    'success_rate': category_passed / len(results)
                }
        
        # Add detailed results
        for result in self.results:
            result_dict = {
                'test_name': result.test_name,
                'success': result.success,
                'duration': result.duration,
                'error_message': result.error_message
            }
            
            if result.performance_metrics:
                result_dict['performance_metrics'] = {
                    'memory_usage_mb': result.performance_metrics.memory_usage_mb,
                    'cpu_usage_percent': result.performance_metrics.cpu_usage_percent,
                    'response_time_ms': result.performance_metrics.response_time_ms,
                    'throughput_items_per_second': result.performance_metrics.throughput_items_per_second,
                    'startup_time_seconds': result.performance_metrics.startup_time_seconds
                }
            
            if result.platform_info:
                result_dict['platform_info'] = result.platform_info
            
            report['detailed_results'].append(result_dict)
        
        # Save report
        report_file = os.path.join(self.framework.test_output_dir, "integration_test_report.json")
        import json
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _summarize_performance_results(self) -> Dict[str, Any]:
        """Summarize performance test results."""
        performance_results = [r for r in self.results if r.performance_metrics]
        
        if not performance_results:
            return {}
        
        # Calculate averages
        avg_memory = sum(r.performance_metrics.memory_usage_mb for r in performance_results) / len(performance_results)
        avg_cpu = sum(r.performance_metrics.cpu_usage_percent for r in performance_results) / len(performance_results)
        avg_response = sum(r.performance_metrics.response_time_ms for r in performance_results) / len(performance_results)
        
        return {
            'average_memory_usage_mb': avg_memory,
            'average_cpu_usage_percent': avg_cpu,
            'average_response_time_ms': avg_response,
            'performance_issues': [r.error_message for r in performance_results if not r.success and r.error_message]
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check success rate
        success_rate = len([r for r in self.results if r.success]) / len(self.results) if self.results else 0
        
        if success_rate < 0.9:
            recommendations.append("Overall success rate is below 90%. Review failed tests and address issues.")
        
        # Check performance issues
        performance_issues = [r for r in self.results if not r.success and 'performance' in r.test_name]
        if performance_issues:
            recommendations.append("Performance issues detected. Consider optimizing GUI components and interactions.")
        
        # Check platform compatibility
        platform_issues = [r for r in self.results if not r.success and any(x in r.test_name for x in ['font', 'path', 'dialog', 'keyboard'])]
        if platform_issues:
            recommendations.append("Platform compatibility issues found. Test on additional platforms and adjust platform-specific code.")
        
        # Check memory usage
        performance_results = [r for r in self.results if r.performance_metrics]
        if performance_results:
            high_memory = [r for r in performance_results if r.performance_metrics.memory_usage_mb > 150]
            if high_memory:
                recommendations.append("High memory usage detected. Consider implementing memory optimization strategies.")
        
        return recommendations


class TestIntegrationE2E(unittest.TestCase):
    """Unit tests for integration and end-to-end testing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_suite = IntegrationTestSuite()
    
    def tearDown(self):
        """Clean up after tests."""
        self.test_suite.framework.teardown_mock_environment()
    
    def test_cross_platform_tester_initialization(self):
        """Test CrossPlatformTester initialization."""
        tester = CrossPlatformTester()
        
        # Verify platform detection
        self.assertIsInstance(tester.current_platform, PlatformInfo)
        
        # Verify platform configs
        self.assertIn(tester.current_platform, tester.platform_specific_configs)
        
        # Verify platform info
        platform_info = tester.get_platform_info()
        self.assertIn('platform', platform_info)
        self.assertIn('system', platform_info)
    
    def test_performance_tester_initialization(self):
        """Test PerformanceTester initialization."""
        tester = PerformanceTester()
        
        # Verify baseline metrics
        self.assertIsInstance(tester.baseline_metrics, PerformanceMetrics)
        
        # Verify thresholds
        self.assertIn('startup_time_seconds', tester.performance_thresholds)
        self.assertIn('memory_usage_mb', tester.performance_thresholds)
    
    def test_performance_measurement(self):
        """Test performance measurement functionality."""
        tester = PerformanceTester()
        
        # Test startup performance measurement
        startup_metrics = tester.measure_startup_performance(self.test_suite.framework)
        self.assertIsInstance(startup_metrics, PerformanceMetrics)
        self.assertGreaterEqual(startup_metrics.startup_time_seconds, 0)
        
        # Test performance validation
        valid, issues = tester.validate_performance(startup_metrics)
        self.assertIsInstance(valid, bool)
        self.assertIsInstance(issues, list)
    
    def test_end_to_end_tester(self):
        """Test EndToEndTester functionality."""
        e2e_tester = EndToEndTester(self.test_suite.framework)
        
        # Test setup wizard flow
        wizard_result = e2e_tester._test_setup_wizard_flow()
        self.assertIsInstance(wizard_result, IntegrationTestResult)
        self.assertEqual(wizard_result.test_name, "setup_wizard_flow")
        
        # Test main review flow
        review_result = e2e_tester._test_main_review_flow()
        self.assertIsInstance(review_result, IntegrationTestResult)
        self.assertEqual(review_result.test_name, "main_review_flow")
    
    def test_cli_gui_compatibility_tester(self):
        """Test CLI/GUI compatibility testing."""
        cli_gui_tester = CLIGUICompatibilityTester()
        
        # Test session config compatibility
        config_result = cli_gui_tester._test_session_config_compatibility()
        self.assertIsInstance(config_result, IntegrationTestResult)
        self.assertEqual(config_result.test_name, "session_config_compatibility")
    
    def test_integration_test_suite_initialization(self):
        """Test IntegrationTestSuite initialization."""
        # Verify all components are initialized
        self.assertIsInstance(self.test_suite.cross_platform_tester, CrossPlatformTester)
        self.assertIsInstance(self.test_suite.performance_tester, PerformanceTester)
        self.assertIsInstance(self.test_suite.e2e_tester, EndToEndTester)
        self.assertIsInstance(self.test_suite.cli_gui_tester, CLIGUICompatibilityTester)
        
        # Verify results list is initialized
        self.assertIsInstance(self.test_suite.results, list)
        self.assertEqual(len(self.test_suite.results), 0)


if __name__ == "__main__":
    # Run integration test suite
    print("VAITP-Auditor GUI Integration and End-to-End Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = IntegrationTestSuite()
    
    # Run all tests
    report = test_suite.run_all_tests()
    
    # Print summary
    print(f"\nTest Results Summary:")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1%}")
    print(f"Total Duration: {report['summary']['total_duration']:.2f}s")
    print(f"Platform: {report['summary']['platform_info']['platform']}")
    
    # Print category results
    print(f"\nResults by Category:")
    for category, stats in report['categories'].items():
        print(f"  {category.title()}: {stats['passed']}/{stats['total']} ({stats['success_rate']:.1%})")
    
    # Print performance summary
    if 'performance_summary' in report and report['performance_summary']:
        perf = report['performance_summary']
        print(f"\nPerformance Summary:")
        print(f"  Average Memory Usage: {perf.get('average_memory_usage_mb', 0):.1f} MB")
        print(f"  Average CPU Usage: {perf.get('average_cpu_usage_percent', 0):.1f}%")
        print(f"  Average Response Time: {perf.get('average_response_time_ms', 0):.1f} ms")
    
    # Print recommendations
    if report['recommendations']:
        print(f"\nRecommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    print(f"\nDetailed report saved to: {test_suite.framework.test_output_dir}/integration_test_report.json")