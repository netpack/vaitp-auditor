"""
Integration tests for enhanced progress tracking functionality.

Tests the complete progress tracking workflow from initialization
through updates to completion.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create comprehensive CustomTkinter mock
class MockCTkWidget:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    
    def grid(self, *args, **kwargs):
        pass
    
    def grid_columnconfigure(self, *args, **kwargs):
        pass
    
    def grid_rowconfigure(self, *args, **kwargs):
        pass
    
    def configure(self, *args, **kwargs):
        pass
    
    def delete(self, *args, **kwargs):
        pass
    
    def insert(self, *args, **kwargs):
        pass
    
    def get(self, *args, **kwargs):
        return "mock_value"
    
    def set(self, *args, **kwargs):
        pass

class MockCTk(MockCTkWidget):
    def title(self, *args, **kwargs):
        pass
    
    def geometry(self, *args, **kwargs):
        pass
    
    def minsize(self, *args, **kwargs):
        pass
    
    def mainloop(self, *args, **kwargs):
        pass

# Mock the entire customtkinter module
mock_ctk = MagicMock()
mock_ctk.CTk = MockCTk
mock_ctk.CTkFrame = MockCTkWidget
mock_ctk.CTkLabel = MockCTkWidget
mock_ctk.CTkTextbox = MockCTkWidget
mock_ctk.CTkButton = MockCTkWidget
mock_ctk.CTkEntry = MockCTkWidget
mock_ctk.CTkProgressBar = MockCTkWidget
mock_ctk.CTkFont = Mock(return_value=Mock())
mock_ctk.set_appearance_mode = Mock()
mock_ctk.set_default_color_theme = Mock()

sys.modules['customtkinter'] = mock_ctk

from vaitp_auditor.gui.main_review_window import MainReviewWindow, HeaderFrame
from vaitp_auditor.gui.models import GUIConfig, ProgressInfo
from vaitp_auditor.core.models import CodePair


class TestProgressTrackingIntegration(unittest.TestCase):
    """Integration tests for progress tracking functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('vaitp_auditor.gui.main_review_window.get_default_verdict_buttons') as mock_buttons:
            mock_buttons.return_value = []
            self.main_window = MainReviewWindow()
    
    def test_complete_progress_workflow(self):
        """Test complete progress tracking workflow from start to finish."""
        # Mock the header frame components
        self.main_window.header_frame.current_file_label = Mock()
        self.main_window.header_frame.progress_bar = Mock()
        self.main_window.header_frame.progress_text_label = Mock()
        
        # Test initial state
        self.assertIsNone(self.main_window.get_current_progress())
        
        # Test loading state
        self.main_window.set_loading_state("Loading test session...")
        
        # Verify loading state was set
        self.main_window.header_frame.current_file_label.configure.assert_called_with(
            text="Loading test session..."
        )
        self.main_window.header_frame.progress_bar.set.assert_called_with(0.0)
        self.main_window.header_frame.progress_text_label.configure.assert_called_with(
            text="Preparing..."
        )
        
        # Test progress updates throughout session
        progress_updates = [
            ProgressInfo(current=1, total=5, current_file="file1.py", experiment_name="test_exp"),
            ProgressInfo(current=2, total=5, current_file="file2.py", experiment_name="test_exp"),
            ProgressInfo(current=3, total=5, current_file="file3.py", experiment_name="test_exp"),
            ProgressInfo(current=4, total=5, current_file="file4.py", experiment_name="test_exp"),
            ProgressInfo(current=5, total=5, current_file="file5.py", experiment_name="test_exp"),
        ]
        
        expected_progress_values = [0.2, 0.4, 0.6, 0.8, 1.0]
        
        for i, progress_info in enumerate(progress_updates):
            # Update progress
            self.main_window.update_progress(progress_info)
            
            # Verify progress was stored
            current_progress = self.main_window.get_current_progress()
            self.assertEqual(current_progress, progress_info)
            
            # Verify progress bar was updated with correct value
            expected_calls = self.main_window.header_frame.progress_bar.set.call_args_list
            # The last call should have the expected progress value
            last_call_args = expected_calls[-1][0]
            self.assertAlmostEqual(last_call_args[0], expected_progress_values[i], places=2)
        
        # Test completion state
        self.main_window.set_completion_state("test_exp")
        
        # Verify completion state was set
        self.main_window.header_frame.current_file_label.configure.assert_called_with(
            text="Review Complete - test_exp"
        )
        self.main_window.header_frame.progress_bar.set.assert_called_with(1.0)
        self.main_window.header_frame.progress_text_label.configure.assert_called_with(
            text="100% Complete"
        )
    
    def test_progress_tracking_with_code_pairs(self):
        """Test progress tracking integrated with code pair loading."""
        # Mock components
        self.main_window.header_frame.current_file_label = Mock()
        self.main_window.header_frame.progress_bar = Mock()
        self.main_window.header_frame.progress_text_label = Mock()
        self.main_window.code_panels_frame = Mock()
        self.main_window.actions_frame = Mock()
        
        # Create test code pair
        code_pair = CodePair(
            identifier="test_id",
            expected_code="def expected():\n    pass",
            generated_code="def generated():\n    return True",
            source_info={"file": "test.py"}
        )
        
        # Create progress info
        progress_info = ProgressInfo(
            current=3,
            total=10,
            current_file="test.py",
            experiment_name="integration_test"
        )
        
        # Load code pair and update progress
        self.main_window.load_code_pair(code_pair)
        self.main_window.update_progress(progress_info)
        
        # Verify code was loaded
        self.main_window.code_panels_frame.load_code_pair.assert_called_once_with(code_pair)
        self.main_window.actions_frame.set_buttons_enabled.assert_called_once_with(True)
        
        # Verify progress was updated
        current_progress = self.main_window.get_current_progress()
        self.assertEqual(current_progress, progress_info)
        
        # Verify progress bar shows 30% (3/10)
        progress_calls = self.main_window.header_frame.progress_bar.set.call_args_list
        last_progress_call = progress_calls[-1][0][0]
        self.assertAlmostEqual(last_progress_call, 0.3, places=2)
    
    def test_progress_reset_and_clear_workflow(self):
        """Test progress reset and content clearing workflow."""
        # Mock components
        self.main_window.header_frame.current_file_label = Mock()
        self.main_window.header_frame.progress_bar = Mock()
        self.main_window.header_frame.progress_text_label = Mock()
        self.main_window.code_panels_frame = Mock()
        self.main_window.actions_frame = Mock()
        
        # Set some progress first
        progress_info = ProgressInfo(
            current=7,
            total=10,
            current_file="test.py",
            experiment_name="test"
        )
        self.main_window.update_progress(progress_info)
        
        # Verify progress was set
        self.assertIsNotNone(self.main_window.get_current_progress())
        
        # Clear all content (which should reset progress)
        self.main_window.clear_content()
        
        # Verify all components were cleared/reset
        self.main_window.code_panels_frame.clear_content.assert_called_once()
        self.main_window.actions_frame.clear_comment.assert_called_once()
        
        # Verify progress was reset
        self.main_window.header_frame.current_file_label.configure.assert_called_with(
            text="No file loaded"
        )
        self.main_window.header_frame.progress_bar.set.assert_called_with(0.0)
        self.main_window.header_frame.progress_text_label.configure.assert_called_with(
            text="0/0 (0.0%)"
        )
    
    def test_progress_boundary_conditions(self):
        """Test progress tracking with boundary conditions."""
        # Mock components
        self.main_window.header_frame.current_file_label = Mock()
        self.main_window.header_frame.progress_bar = Mock()
        self.main_window.header_frame.progress_text_label = Mock()
        
        # Test 0% progress
        progress_zero = ProgressInfo(
            current=0,
            total=100,
            current_file="start.py",
            experiment_name="boundary_test"
        )
        self.main_window.update_progress(progress_zero)
        
        # Verify 0% progress
        progress_calls = self.main_window.header_frame.progress_bar.set.call_args_list
        self.assertEqual(progress_calls[-1][0][0], 0.0)
        
        # Test 100% progress
        progress_complete = ProgressInfo(
            current=100,
            total=100,
            current_file="end.py",
            experiment_name="boundary_test"
        )
        self.main_window.update_progress(progress_complete)
        
        # Verify 100% progress
        progress_calls = self.main_window.header_frame.progress_bar.set.call_args_list
        self.assertEqual(progress_calls[-1][0][0], 1.0)
        
        # Test empty total (edge case)
        progress_empty = ProgressInfo(
            current=0,
            total=0,
            current_file="empty.py",
            experiment_name="boundary_test"
        )
        self.main_window.update_progress(progress_empty)
        
        # Should handle gracefully (100% when total is 0)
        progress_calls = self.main_window.header_frame.progress_bar.set.call_args_list
        self.assertEqual(progress_calls[-1][0][0], 1.0)  # 100% when total is 0
    
    def test_window_title_updates_with_progress(self):
        """Test that window title updates correctly with progress changes."""
        # Create progress info
        progress_info = ProgressInfo(
            current=5,
            total=10,
            current_file="current_file.py",
            experiment_name="title_test_experiment"
        )
        
        # Mock the title method
        with patch.object(self.main_window, 'title') as mock_title:
            # Update progress
            self.main_window.update_progress(progress_info)
            
            # Verify title was updated with experiment name
            mock_title.assert_called_with("VAITP-Auditor - Reviewing: title_test_experiment")
        
        # Test loading state title
        with patch.object(self.main_window, 'title') as mock_title:
            self.main_window.set_loading_state("Loading custom message")
            mock_title.assert_called_with("VAITP-Auditor - Loading...")
        
        # Test completion state title
        with patch.object(self.main_window, 'title') as mock_title:
            self.main_window.set_completion_state("completed_experiment")
            mock_title.assert_called_with("VAITP-Auditor - Complete: completed_experiment")


class TestHeaderFrameStandalone(unittest.TestCase):
    """Standalone tests for HeaderFrame progress tracking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_parent = Mock()
        self.header_frame = HeaderFrame(self.mock_parent)
        
        # Mock the UI components
        self.header_frame.current_file_label = Mock()
        self.header_frame.progress_bar = Mock()
        self.header_frame.progress_text_label = Mock()
    
    def test_progress_info_storage_and_retrieval(self):
        """Test that progress info is properly stored and retrieved."""
        # Initially should be None
        self.assertIsNone(self.header_frame.get_current_progress())
        
        # Create and set progress info
        progress_info = ProgressInfo(
            current=3,
            total=7,
            current_file="storage_test.py",
            experiment_name="storage_test"
        )
        
        self.header_frame.update_progress(progress_info)
        
        # Verify storage
        retrieved_progress = self.header_frame.get_current_progress()
        self.assertEqual(retrieved_progress, progress_info)
        self.assertEqual(retrieved_progress.current, 3)
        self.assertEqual(retrieved_progress.total, 7)
        self.assertEqual(retrieved_progress.current_file, "storage_test.py")
        self.assertEqual(retrieved_progress.experiment_name, "storage_test")
    
    def test_progress_percentage_calculation_accuracy(self):
        """Test that progress percentage calculations are accurate."""
        test_cases = [
            (0, 10, 0.0),
            (1, 10, 0.1),
            (5, 10, 0.5),
            (7, 10, 0.7),
            (10, 10, 1.0),
            (33, 100, 0.33),
            (67, 100, 0.67),
            (1, 3, 0.3333333333333333),
        ]
        
        for current, total, expected_progress in test_cases:
            progress_info = ProgressInfo(
                current=current,
                total=total,
                current_file=f"test_{current}_{total}.py",
                experiment_name="accuracy_test"
            )
            
            self.header_frame.update_progress(progress_info)
            
            # Get the last call to progress_bar.set
            progress_calls = self.header_frame.progress_bar.set.call_args_list
            actual_progress = progress_calls[-1][0][0]
            
            self.assertAlmostEqual(actual_progress, expected_progress, places=5)


if __name__ == '__main__':
    unittest.main()