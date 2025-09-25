"""
Unit tests for enhanced undo and quit functionality.

Tests undo functionality with proper state validation and quit confirmation
dialog with session save confirmation.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock CustomTkinter
class MockCTkWidget:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    
    def grid(self, *args, **kwargs):
        pass
    
    def configure(self, *args, **kwargs):
        pass
    
    def set_processing_state(self, processing):
        pass
    
    def show_verdict_feedback(self, verdict_id, success):
        pass

mock_ctk = MagicMock()
mock_ctk.CTk = MockCTkWidget
mock_ctk.CTkFrame = MockCTkWidget
mock_ctk.CTkLabel = MockCTkWidget
mock_ctk.CTkTextbox = MockCTkWidget
mock_ctk.CTkButton = MockCTkWidget
mock_ctk.CTkEntry = MockCTkWidget
mock_ctk.CTkProgressBar = MockCTkWidget
mock_ctk.CTkFont = Mock(return_value=Mock())

sys.modules['customtkinter'] = mock_ctk

from vaitp_auditor.gui.gui_session_controller import GUISessionController
from vaitp_auditor.gui.models import GUIConfig, ProgressInfo
from vaitp_auditor.gui.error_handler import GUIErrorHandler


class TestUndoFunctionality(unittest.TestCase):
    """Test cases for enhanced undo functionality with proper state validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.controller = GUISessionController(GUIConfig())
        self.mock_main_window = Mock()
        self.mock_session_manager = Mock()
        self.mock_error_handler = Mock()
        
        self.controller.set_main_window(self.mock_main_window)
        self.controller._session_manager = self.mock_session_manager
        self.controller._error_handler = self.mock_error_handler
        self.controller._is_session_active = True
        self.controller._session_paused = False
    
    def test_undo_with_no_active_session(self):
        """Test undo request with no active session."""
        self.controller._session_manager = None
        
        # Call undo
        self.controller.handle_undo_request()
        
        # Verify error was logged and no processing occurred
        self.mock_main_window.set_processing_state.assert_not_called()
    
    def test_undo_with_paused_session(self):
        """Test undo request with paused session."""
        self.controller._session_paused = True
        
        # Call undo
        self.controller.handle_undo_request()
        
        # Verify processing state was not set
        self.mock_main_window.set_processing_state.assert_not_called()
    
    def test_undo_with_no_reviews_to_undo(self):
        """Test undo request when no reviews can be undone (first review edge case)."""
        # Mock session manager to indicate no undo possible
        self.mock_session_manager.can_undo.return_value = False
        
        # Call undo
        self.controller.handle_undo_request()
        
        # Verify processing state was set and cleared
        self.mock_main_window.set_processing_state.assert_any_call(True)
        self.mock_main_window.set_processing_state.assert_any_call(False)
        
        # Verify info dialog was shown
        self.mock_error_handler.show_info_dialog.assert_called_once()
        
        # Verify undo was not attempted
        self.mock_session_manager.undo_last_review.assert_not_called()
    
    def test_undo_with_empty_session_edge_case(self):
        """Test undo request with empty session (no completed reviews)."""
        # Mock session with no completed reviews
        mock_session = Mock()
        mock_session.completed_reviews = []
        self.mock_session_manager._current_session = mock_session
        self.mock_session_manager.can_undo.return_value = False
        
        # Call undo
        self.controller.handle_undo_request()
        
        # Verify appropriate error dialog was shown
        self.mock_error_handler.show_info_dialog.assert_called_once()
        args = self.mock_error_handler.show_info_dialog.call_args[0]
        self.assertIn("first review", args[2])
    
    def test_undo_user_confirmation_cancelled(self):
        """Test undo request cancelled by user."""
        # Mock session manager to allow undo
        self.mock_session_manager.can_undo.return_value = True
        self.mock_session_manager.get_undo_info.return_value = {
            'review_id': 1,
            'source_identifier': 'test_file.py'
        }
        
        # Mock user cancelling confirmation
        self.mock_error_handler.show_confirmation_dialog.return_value = False
        
        # Call undo
        self.controller.handle_undo_request()
        
        # Verify processing state was cleared
        self.mock_main_window.set_processing_state.assert_any_call(False)
        
        # Verify undo was not performed
        self.mock_session_manager.undo_last_review.assert_not_called()
    
    def test_undo_successful_execution(self):
        """Test successful undo execution."""
        # Mock session with proper structure
        mock_session = Mock()
        mock_session.completed_reviews = ['review1']  # Has completed reviews
        self.mock_session_manager._current_session = mock_session
        
        # Mock session manager for successful undo
        self.mock_session_manager.can_undo.return_value = True
        self.mock_session_manager.get_undo_info.return_value = {
            'review_id': 1,
            'source_identifier': 'test_file.py'
        }
        self.mock_session_manager.undo_last_review.return_value = True
        
        # Mock user confirming undo
        self.mock_error_handler.show_confirmation_dialog.return_value = True
        
        # Mock controller methods
        self.controller.load_next_code_pair = Mock()
        self.controller._update_button_states = Mock()
        
        # Call undo
        self.controller.handle_undo_request()
        
        # Verify processing state was managed
        self.mock_main_window.set_processing_state.assert_any_call(True)
        self.mock_main_window.set_processing_state.assert_any_call(False)
        
        # Verify undo was performed
        self.mock_session_manager.undo_last_review.assert_called_once()
        
        # Verify state was updated
        self.controller.load_next_code_pair.assert_called_once()
        self.controller._update_button_states.assert_called_once()
        
        # Verify success dialog was shown
        self.mock_error_handler.show_info_dialog.assert_called()
    
    def test_undo_failed_execution(self):
        """Test failed undo execution."""
        # Mock session with proper structure
        mock_session = Mock()
        mock_session.completed_reviews = ['review1']  # Has completed reviews
        self.mock_session_manager._current_session = mock_session
        
        # Mock session manager for failed undo
        self.mock_session_manager.can_undo.return_value = True
        self.mock_session_manager.get_undo_info.return_value = {
            'review_id': 1,
            'source_identifier': 'test_file.py'
        }
        self.mock_session_manager.undo_last_review.return_value = False
        
        # Mock user confirming undo
        self.mock_error_handler.show_confirmation_dialog.return_value = True
        
        # Call undo
        self.controller.handle_undo_request()
        
        # Verify error dialog was shown
        self.mock_error_handler.show_error_dialog.assert_called_once()
        args = self.mock_error_handler.show_error_dialog.call_args[0]
        self.assertEqual(args[1], "Undo Failed")
    
    def test_undo_exception_handling(self):
        """Test undo exception handling."""
        # Mock session manager to raise exception
        self.mock_session_manager.can_undo.return_value = True
        self.mock_session_manager.get_undo_info.side_effect = Exception("Test error")
        
        # Call undo
        self.controller.handle_undo_request()
        
        # Verify processing state was cleared even on error
        self.mock_main_window.set_processing_state.assert_any_call(False)


class TestQuitFunctionality(unittest.TestCase):
    """Test cases for enhanced quit functionality with session save confirmation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.controller = GUISessionController(GUIConfig())
        self.mock_main_window = Mock()
        self.mock_session_manager = Mock()
        self.mock_error_handler = Mock()
        
        self.controller.set_main_window(self.mock_main_window)
        self.controller._session_manager = self.mock_session_manager
        self.controller._error_handler = self.mock_error_handler
        self.controller._is_session_active = True
        self.controller._session_paused = False
        
        # Mock progress info
        self.controller._get_current_progress = Mock(return_value=ProgressInfo(
            current=5,
            total=10,
            current_file="test_file.py",
            experiment_name="test_experiment"
        ))
    
    def test_quit_with_no_main_window(self):
        """Test quit request with no main window."""
        self.controller._main_window = None
        self.controller._perform_quit = Mock()
        
        # Call quit
        self.controller.handle_quit_request()
        
        # Verify quit was performed directly
        self.controller._perform_quit.assert_called_once()
    
    def test_quit_with_active_session_user_confirms(self):
        """Test quit with active session where user confirms."""
        # Mock user confirming quit
        self.mock_error_handler.show_confirmation_dialog.return_value = True
        
        # Mock session save success
        self.mock_session_manager.save_session_state.return_value = None
        
        # Mock perform quit
        self.controller._perform_quit = Mock()
        
        # Call quit
        self.controller.handle_quit_request()
        
        # Verify processing state was set
        self.mock_main_window.set_processing_state.assert_called_with(True)
        
        # Verify confirmation dialog was shown with session details
        self.mock_error_handler.show_confirmation_dialog.assert_called()
        args = self.mock_error_handler.show_confirmation_dialog.call_args[0]
        self.assertEqual(args[1], "Save and Quit Session")
        self.assertIn("test_experiment", args[2])
        
        # Verify session was saved
        self.mock_session_manager.save_session_state.assert_called_once()
        
        # Verify quit was performed
        self.controller._perform_quit.assert_called_once()
    
    def test_quit_with_active_session_user_cancels(self):
        """Test quit with active session where user cancels."""
        # Mock user cancelling quit
        self.mock_error_handler.show_confirmation_dialog.return_value = False
        
        # Call quit
        self.controller.handle_quit_request()
        
        # Verify processing state was cleared
        self.mock_main_window.set_processing_state.assert_any_call(False)
        
        # Verify quit was not performed
        self.mock_session_manager.save_session_state.assert_not_called()
    
    def test_quit_with_session_save_failure(self):
        """Test quit with session save failure."""
        # Mock user confirming quit
        self.mock_error_handler.show_confirmation_dialog.side_effect = [True, True]  # Confirm quit, then confirm despite save failure
        
        # Mock session save failure
        self.mock_session_manager.save_session_state.side_effect = Exception("Save failed")
        
        # Mock perform quit
        self.controller._perform_quit = Mock()
        
        # Call quit
        self.controller.handle_quit_request()
        
        # Verify save failure dialog was shown
        self.assertEqual(self.mock_error_handler.show_confirmation_dialog.call_count, 2)
        
        # Verify quit was still performed after user confirmation
        self.controller._perform_quit.assert_called_once()
    
    def test_quit_with_no_active_session(self):
        """Test quit with no active session."""
        self.controller._is_session_active = False
        
        # Mock user confirming quit
        self.mock_error_handler.show_confirmation_dialog.return_value = True
        
        # Mock perform quit
        self.controller._perform_quit = Mock()
        
        # Call quit
        self.controller.handle_quit_request()
        
        # Verify different dialog was shown
        args = self.mock_error_handler.show_confirmation_dialog.call_args[0]
        self.assertEqual(args[1], "Quit Application")
        self.assertIn("No active review session", args[2])
        
        # Verify quit was performed
        self.controller._perform_quit.assert_called_once()
    
    def test_quit_exception_handling(self):
        """Test quit exception handling."""
        # Mock exception during quit processing
        self.mock_error_handler.show_confirmation_dialog.side_effect = Exception("Dialog error")
        
        # Mock perform quit and emergency confirmation
        self.controller._perform_quit = Mock()
        
        # Call quit
        self.controller.handle_quit_request()
        
        # Verify processing state was cleared
        self.mock_main_window.set_processing_state.assert_any_call(False)
        
        # Verify emergency quit was attempted
        self.controller._perform_quit.assert_called_once()
    
    def test_perform_quit_cleanup(self):
        """Test perform quit cleanup operations."""
        # Mock session completion callback
        completion_callback = Mock()
        self.controller.set_session_completion_callback(completion_callback)
        
        # Call perform quit
        self.controller._perform_quit()
        
        # Verify session state was saved
        self.mock_session_manager.save_session_state.assert_called_once()
        
        # Verify session was paused
        self.assertTrue(self.controller._session_paused)
        
        # Verify completion callback was called
        completion_callback.assert_called_once()


class TestSessionSaveConfirmation(unittest.TestCase):
    """Test cases for session save confirmation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.controller = GUISessionController(GUIConfig())
        self.mock_main_window = Mock()
        self.mock_session_manager = Mock()
        
        self.controller.set_main_window(self.mock_main_window)
        self.controller._session_manager = self.mock_session_manager
        self.controller._is_session_active = True
    
    def test_session_save_with_progress_details(self):
        """Test session save confirmation shows detailed progress information."""
        # Mock progress info
        progress_info = ProgressInfo(
            current=7,
            total=15,
            current_file="current_test.py",
            experiment_name="detailed_experiment"
        )
        self.controller._get_current_progress = Mock(return_value=progress_info)
        
        # Mock error handler
        self.controller._error_handler = Mock()
        self.controller._error_handler.show_confirmation_dialog.return_value = True
        
        # Mock perform quit
        self.controller._perform_quit = Mock()
        
        # Call quit
        self.controller.handle_quit_request()
        
        # Verify confirmation dialog included detailed progress
        args = self.controller._error_handler.show_confirmation_dialog.call_args[0]
        message = args[2]
        
        self.assertIn("detailed_experiment", message)
        self.assertIn("6/15", message)  # completed reviews
        self.assertIn("9 reviews", message)  # remaining reviews
        self.assertIn("46.7%", message)  # progress percentage (6/15 * 100 = 40%, but current-1 = 6, so 6/15 = 40%)
        self.assertIn("automatically saved", message)
        self.assertIn("resume this session", message)
    
    def test_auto_close_save_confirmation(self):
        """Test auto-closing save confirmation dialog."""
        # Mock successful save
        self.controller._error_handler = Mock()
        self.controller._error_handler.show_confirmation_dialog.return_value = True
        
        # Mock progress info
        progress_info = ProgressInfo(
            current=5,
            total=10,
            current_file="test.py",
            experiment_name="auto_close_test"
        )
        self.controller._get_current_progress = Mock(return_value=progress_info)
        
        # Mock perform quit
        self.controller._perform_quit = Mock()
        
        # Call quit
        self.controller.handle_quit_request()
        
        # Verify auto-close dialog was shown
        self.controller._error_handler.show_info_dialog.assert_called()
        args = self.controller._error_handler.show_info_dialog.call_args
        
        # Check for auto_close_ms parameter
        self.assertIn('auto_close_ms', args[1])
        self.assertEqual(args[1]['auto_close_ms'], 2000)


if __name__ == '__main__':
    unittest.main()