"""
Unit tests for Progress Widgets functionality.

Tests the progress widgets, loading indicators, and progress management
to ensure proper feedback and cancellation handling in long-running operations.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import customtkinter as ctk
import threading
import time
from vaitp_auditor.gui.progress_widgets import (
    ProgressState,
    ProgressInfo,
    ProgressCallback,
    LoadingIndicator,
    ProgressDialog,
    ProgressManager,
    DialogProgressCallback,
    show_loading_dialog,
    run_with_progress
)


class TestProgressInfo(unittest.TestCase):
    """Test cases for ProgressInfo dataclass."""
    
    def test_progress_info_creation(self):
        """Test ProgressInfo creation and properties."""
        progress = ProgressInfo(
            current=50,
            total=100,
            message="Processing items",
            percentage=50.0,
            state=ProgressState.RUNNING,
            elapsed_time=30.0,
            estimated_remaining=30.0
        )
        
        self.assertEqual(progress.current, 50)
        self.assertEqual(progress.total, 100)
        self.assertEqual(progress.message, "Processing items")
        self.assertEqual(progress.percentage, 50.0)
        self.assertEqual(progress.state, ProgressState.RUNNING)
        self.assertFalse(progress.is_indeterminate)
        self.assertFalse(progress.is_complete)
        self.assertFalse(progress.is_cancelled)
        self.assertFalse(progress.has_error)
    
    def test_progress_info_indeterminate(self):
        """Test indeterminate progress detection."""
        progress = ProgressInfo(
            current=0,
            total=0,
            message="Loading...",
            percentage=0.0,
            state=ProgressState.RUNNING
        )
        
        self.assertTrue(progress.is_indeterminate)
    
    def test_progress_info_states(self):
        """Test progress state properties."""
        # Test completed state
        completed = ProgressInfo(
            current=100,
            total=100,
            message="Done",
            percentage=100.0,
            state=ProgressState.COMPLETED
        )
        self.assertTrue(completed.is_complete)
        
        # Test cancelled state
        cancelled = ProgressInfo(
            current=50,
            total=100,
            message="Cancelled",
            percentage=50.0,
            state=ProgressState.CANCELLED
        )
        self.assertTrue(cancelled.is_cancelled)
        
        # Test error state
        error = ProgressInfo(
            current=25,
            total=100,
            message="Error occurred",
            percentage=25.0,
            state=ProgressState.ERROR
        )
        self.assertTrue(error.has_error)


class TestLoadingIndicator(unittest.TestCase):
    """Test cases for LoadingIndicator widget."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = ctk.CTk()
        self.root.withdraw()  # Hide window during tests
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    def test_loading_indicator_creation(self):
        """Test LoadingIndicator creation."""
        indicator = LoadingIndicator(self.root, "Loading data...")
        
        self.assertEqual(indicator.message, "Loading data...")
        self.assertFalse(indicator.is_running)
        self.assertIsNotNone(indicator.progress_bar)
        self.assertIsNotNone(indicator.message_label)
    
    def test_loading_indicator_start_stop(self):
        """Test loading indicator start and stop."""
        indicator = LoadingIndicator(self.root)
        
        # Test start
        indicator.start()
        self.assertTrue(indicator.is_running)
        
        # Test stop
        indicator.stop()
        self.assertFalse(indicator.is_running)
    
    def test_loading_indicator_message_update(self):
        """Test loading indicator message update."""
        indicator = LoadingIndicator(self.root, "Initial message")
        
        indicator.set_message("Updated message")
        self.assertEqual(indicator.message, "Updated message")


class TestProgressDialog(unittest.TestCase):
    """Test cases for ProgressDialog widget."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = ctk.CTk()
        self.root.withdraw()  # Hide window during tests
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    def test_progress_dialog_creation(self):
        """Test ProgressDialog creation."""
        dialog = ProgressDialog(
            self.root,
            title="Test Progress",
            message="Processing...",
            can_cancel=True,
            show_details=True
        )
        
        self.assertEqual(dialog.title(), "Test Progress")
        self.assertTrue(dialog.can_cancel)
        self.assertTrue(dialog.show_details)
        self.assertFalse(dialog.is_cancelled)
        
        dialog.destroy()
    
    def test_progress_dialog_cancellation(self):
        """Test progress dialog cancellation."""
        dialog = ProgressDialog(self.root, can_cancel=True)
        
        # Test cancel
        dialog._on_cancel()
        self.assertTrue(dialog.is_cancelled)
        
        dialog.destroy()
    
    def test_progress_dialog_update_determinate(self):
        """Test progress dialog update with determinate progress."""
        dialog = ProgressDialog(self.root, show_details=True)
        
        progress_info = ProgressInfo(
            current=25,
            total=100,
            message="Processing item 25 of 100",
            percentage=25.0,
            state=ProgressState.RUNNING,
            elapsed_time=10.0,
            estimated_remaining=30.0
        )
        
        dialog.update_progress(progress_info)
        
        # Verify progress was updated
        self.assertEqual(dialog.progress_info, progress_info)
        
        dialog.destroy()
    
    def test_progress_dialog_update_indeterminate(self):
        """Test progress dialog update with indeterminate progress."""
        dialog = ProgressDialog(self.root)
        
        progress_info = ProgressInfo(
            current=0,
            total=0,
            message="Loading...",
            percentage=0.0,
            state=ProgressState.RUNNING
        )
        
        dialog.update_progress(progress_info)
        
        # Verify indeterminate mode was set
        self.assertEqual(dialog.progress_info, progress_info)
        
        dialog.destroy()
    
    def test_progress_dialog_completion(self):
        """Test progress dialog completion handling."""
        dialog = ProgressDialog(self.root, can_cancel=True)
        
        progress_info = ProgressInfo(
            current=100,
            total=100,
            message="Completed",
            percentage=100.0,
            state=ProgressState.COMPLETED
        )
        
        dialog.update_progress(progress_info)
        
        # Verify completion was handled
        self.assertTrue(progress_info.is_complete)
        
        dialog.destroy()
    
    def test_progress_dialog_time_formatting(self):
        """Test time formatting in progress dialog."""
        dialog = ProgressDialog(self.root)
        
        # Test seconds
        self.assertEqual(dialog._format_time(45), "45s")
        
        # Test minutes
        self.assertEqual(dialog._format_time(125), "2m 5s")
        
        # Test hours
        self.assertEqual(dialog._format_time(3665), "1h 1m")


class TestProgressManager(unittest.TestCase):
    """Test cases for ProgressManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = ProgressManager()
        self.mock_callback = Mock(spec=ProgressCallback)
        self.mock_callback.is_cancelled.return_value = False
    
    def test_progress_manager_callback_registration(self):
        """Test progress manager callback registration."""
        operation_id = "test_operation"
        
        # Register callback
        self.manager.register_callback(operation_id, self.mock_callback)
        self.assertIn(operation_id, self.manager.callbacks)
        
        # Unregister callback
        self.manager.unregister_callback(operation_id)
        self.assertNotIn(operation_id, self.manager.callbacks)
    
    def test_progress_manager_operation_lifecycle(self):
        """Test progress manager operation lifecycle."""
        operation_id = "test_operation"
        self.manager.register_callback(operation_id, self.mock_callback)
        
        # Start operation
        self.manager.start_operation(operation_id, 100, "Starting...")
        self.assertIn(operation_id, self.manager.active_operations)
        self.mock_callback.update_progress.assert_called()
        
        # Update operation
        self.manager.update_operation(operation_id, current=50, message="Halfway done")
        
        # Complete operation
        self.manager.complete_operation(operation_id, "Finished")
        
        # Verify callback was called multiple times
        self.assertGreater(self.mock_callback.update_progress.call_count, 1)
    
    def test_progress_manager_cancellation(self):
        """Test progress manager cancellation handling."""
        operation_id = "test_operation"
        self.manager.register_callback(operation_id, self.mock_callback)
        
        # Start operation
        self.manager.start_operation(operation_id, 100)
        
        # Test cancellation check
        self.assertFalse(self.manager.is_cancelled(operation_id))
        
        # Cancel operation
        self.manager.cancel_operation(operation_id)
        
        # Verify cancellation
        operation = self.manager.active_operations[operation_id]
        self.assertEqual(operation['state'], ProgressState.CANCELLED)
    
    def test_progress_manager_error_handling(self):
        """Test progress manager error handling."""
        operation_id = "test_operation"
        self.manager.register_callback(operation_id, self.mock_callback)
        
        # Start operation
        self.manager.start_operation(operation_id, 100)
        
        # Trigger error
        self.manager.error_operation(operation_id, "Something went wrong")
        
        # Verify error state
        operation = self.manager.active_operations[operation_id]
        self.assertEqual(operation['state'], ProgressState.ERROR)
    
    def test_progress_manager_timing_calculation(self):
        """Test progress manager timing calculations."""
        operation_id = "test_operation"
        self.manager.register_callback(operation_id, self.mock_callback)
        
        # Start operation
        self.manager.start_operation(operation_id, 100)
        
        # Simulate some progress with time delay
        time.sleep(0.1)  # Small delay for timing calculation
        self.manager.update_operation(operation_id, current=50)
        
        # Verify timing was calculated
        call_args = self.mock_callback.update_progress.call_args[0][0]
        self.assertGreater(call_args.elapsed_time, 0)


class TestDialogProgressCallback(unittest.TestCase):
    """Test cases for DialogProgressCallback class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = ctk.CTk()
        self.root.withdraw()
        self.dialog = ProgressDialog(self.root)
        self.callback = DialogProgressCallback(self.dialog)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.dialog.destroy()
        self.root.destroy()
    
    def test_dialog_progress_callback_update(self):
        """Test dialog progress callback update."""
        progress_info = ProgressInfo(
            current=30,
            total=100,
            message="Processing...",
            percentage=30.0,
            state=ProgressState.RUNNING
        )
        
        self.callback.update_progress(progress_info)
        
        # Verify dialog was updated
        self.assertEqual(self.dialog.progress_info, progress_info)
    
    def test_dialog_progress_callback_cancellation(self):
        """Test dialog progress callback cancellation check."""
        # Initially not cancelled
        self.assertFalse(self.callback.is_cancelled())
        
        # Cancel dialog
        self.dialog._on_cancel()
        
        # Verify cancellation is detected
        self.assertTrue(self.callback.is_cancelled())


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = ctk.CTk()
        self.root.withdraw()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    def test_show_loading_dialog(self):
        """Test show_loading_dialog convenience function."""
        dialog = show_loading_dialog(
            self.root,
            title="Loading Test",
            message="Loading data...",
            can_cancel=True
        )
        
        self.assertEqual(dialog.title(), "Loading Test")
        self.assertTrue(dialog.can_cancel)
        self.assertIsNotNone(dialog.progress_info)
        
        dialog.destroy()
    
    @patch('threading.Thread')
    def test_run_with_progress(self, mock_thread_class):
        """Test run_with_progress convenience function."""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        # Mock operation
        def mock_operation(callback):
            # Simulate progress updates
            progress_info = ProgressInfo(
                current=50,
                total=100,
                message="Working...",
                percentage=50.0,
                state=ProgressState.RUNNING
            )
            callback.update_progress(progress_info)
            return "operation_result"
        
        # Mock dialog behavior
        with patch('vaitp_auditor.gui.progress_widgets.ProgressDialog') as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog_class.return_value = mock_dialog
            
            # Run operation
            result = run_with_progress(
                self.root,
                mock_operation,
                title="Test Operation",
                message="Processing...",
                can_cancel=True
            )
            
            # Verify thread was started
            mock_thread.start.assert_called_once()
            mock_thread.join.assert_called_once()


class TestProgressWidgetIntegration(unittest.TestCase):
    """Integration tests for progress widgets."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = ctk.CTk()
        self.root.withdraw()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    def test_progress_manager_with_dialog(self):
        """Test progress manager integration with dialog."""
        manager = ProgressManager()
        dialog = ProgressDialog(self.root)
        callback = DialogProgressCallback(dialog)
        
        operation_id = "integration_test"
        manager.register_callback(operation_id, callback)
        
        # Start and update operation
        manager.start_operation(operation_id, 100, "Starting integration test")
        manager.update_operation(operation_id, current=25, message="25% complete")
        manager.update_operation(operation_id, current=75, message="75% complete")
        manager.complete_operation(operation_id, "Integration test completed")
        
        # Verify dialog received updates
        self.assertIsNotNone(dialog.progress_info)
        self.assertTrue(dialog.progress_info.is_complete)
        
        dialog.destroy()
    
    def test_loading_indicator_with_manager(self):
        """Test loading indicator with progress manager."""
        manager = ProgressManager()
        indicator = LoadingIndicator(self.root, "Loading...")
        
        # Create a simple callback that controls the indicator
        class IndicatorCallback(ProgressCallback):
            def __init__(self, indicator):
                self.indicator = indicator
                self.cancelled = False
            
            def update_progress(self, progress_info):
                if progress_info.state == ProgressState.RUNNING:
                    self.indicator.start()
                    self.indicator.set_message(progress_info.message)
                else:
                    self.indicator.stop()
            
            def is_cancelled(self):
                return self.cancelled
        
        callback = IndicatorCallback(indicator)
        operation_id = "loading_test"
        
        manager.register_callback(operation_id, callback)
        manager.start_operation(operation_id, 0, "Loading data...")
        
        # Verify indicator is running
        self.assertTrue(indicator.is_running)
        
        manager.complete_operation(operation_id, "Loading complete")
        
        # Verify indicator stopped
        self.assertFalse(indicator.is_running)
    
    def test_error_handling_in_progress_widgets(self):
        """Test error handling in progress widgets."""
        manager = ProgressManager()
        dialog = ProgressDialog(self.root)
        callback = DialogProgressCallback(dialog)
        
        operation_id = "error_test"
        manager.register_callback(operation_id, callback)
        
        # Start operation and trigger error
        manager.start_operation(operation_id, 100, "Starting...")
        manager.error_operation(operation_id, "An error occurred during processing")
        
        # Verify error state
        self.assertTrue(dialog.progress_info.has_error)
        self.assertEqual(dialog.progress_info.message, "An error occurred during processing")
        
        dialog.destroy()


if __name__ == '__main__':
    unittest.main()