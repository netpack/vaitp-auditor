"""
Unit tests for GUI Session Controller.

Tests the controller that coordinates between GUI components and backend SessionManager.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from vaitp_auditor.gui.gui_session_controller import GUISessionController
from vaitp_auditor.gui.models import GUIConfig, ProgressInfo
from vaitp_auditor.core.models import CodePair, ReviewResult, SessionConfig


class TestGUISessionController:
    """Test cases for GUISessionController class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.gui_config = GUIConfig()
        self.controller = GUISessionController(self.gui_config)
        
        # Mock GUI components
        self.mock_main_window = Mock()
        self.mock_setup_wizard = Mock()
        
        # Mock backend components
        self.mock_session_manager = Mock()
        self.mock_report_manager = Mock()
        
    def test_initialization(self):
        """Test controller initialization."""
        # Test with default config
        controller = GUISessionController()
        assert controller.gui_config is not None
        assert not controller.is_session_active()
        assert controller.get_session_config() is None
        
        # Test with custom config
        custom_config = GUIConfig(window_width=1200, window_height=700)
        controller = GUISessionController(custom_config)
        assert controller.gui_config.window_width == 1200
        assert controller.gui_config.window_height == 700
    
    def test_set_main_window(self):
        """Test setting main window reference."""
        self.controller.set_main_window(self.mock_main_window)
        assert self.controller._main_window == self.mock_main_window
    
    def test_set_setup_wizard(self):
        """Test setting setup wizard reference."""
        self.controller.set_setup_wizard(self.mock_setup_wizard)
        assert self.controller._setup_wizard == self.mock_setup_wizard
    
    def test_set_callbacks(self):
        """Test setting callback functions."""
        wizard_callback = Mock()
        session_callback = Mock()
        
        self.controller.set_wizard_completion_callback(wizard_callback)
        self.controller.set_session_completion_callback(session_callback)
        
        assert self.controller._wizard_completion_callback == wizard_callback
        assert self.controller._session_completion_callback == session_callback
    
    @patch('vaitp_auditor.gui.gui_session_controller.SessionManager')
    @patch('vaitp_auditor.gui.gui_session_controller.ReportManager')
    def test_start_session_from_config_success(self, mock_report_manager_class, mock_session_manager_class):
        """Test successful session start from configuration."""
        # Setup mocks
        mock_session_manager = Mock()
        mock_session_manager.start_session.return_value = "test_session_123"
        mock_session_manager_class.return_value = mock_session_manager
        
        mock_report_manager = Mock()
        mock_report_manager_class.return_value = mock_report_manager
        
        # Setup wizard completion callback
        wizard_callback = Mock()
        self.controller.set_wizard_completion_callback(wizard_callback)
        
        # Test configuration
        config = {
            'experiment_name': 'test_experiment',
            'data_source_type': 'folders',
            'generated_code_path': '/tmp/generated',
            'expected_code_path': '/tmp/expected',
            'sampling_percentage': 100,
            'output_format': 'excel'
        }
        
        # Start session
        result = self.controller.start_session_from_config(config)
        
        # Verify results
        assert result is True
        assert self.controller.is_session_active()
        assert self.controller.get_session_config() == config
        
        # Verify session manager was called
        mock_session_manager.start_session.assert_called_once()
        
        # Verify callback was called
        wizard_callback.assert_called_once_with(config)
    
    @patch('vaitp_auditor.gui.gui_session_controller.SessionManager')
    def test_start_session_from_config_failure(self, mock_session_manager_class):
        """Test session start failure handling."""
        # Setup mock to raise exception
        mock_session_manager = Mock()
        mock_session_manager.start_session.side_effect = Exception("Test error")
        mock_session_manager_class.return_value = mock_session_manager
        
        config = {
            'experiment_name': 'test_experiment',
            'data_source_type': 'folders'
        }
        
        # Start session (should fail)
        result = self.controller.start_session_from_config(config)
        
        # Verify failure
        assert result is False
        assert not self.controller.is_session_active()
    
    def test_create_session_config_from_dict(self):
        """Test SessionConfig creation from dictionary."""
        config_dict = {
            'experiment_name': 'test_exp',
            'data_source_type': 'folders',
            'generated_code_path': '/path/to/generated',
            'expected_code_path': '/path/to/expected',
            'sampling_percentage': 50,
            'output_format': 'csv'
        }
        
        session_config = self.controller._create_session_config_from_dict(config_dict)
        
        assert isinstance(session_config, SessionConfig)
        assert session_config.experiment_name == 'test_exp'
        assert session_config.data_source_type == 'folders'
        assert session_config.sample_percentage == 50
        assert session_config.output_format == 'csv'
    
    def test_create_session_config_with_defaults(self):
        """Test SessionConfig creation with default values."""
        config_dict = {}
        
        session_config = self.controller._create_session_config_from_dict(config_dict)
        
        assert isinstance(session_config, SessionConfig)
        assert session_config.experiment_name == 'gui_experiment'
        assert session_config.data_source_type == 'folders'
        assert session_config.sample_percentage == 100
        assert session_config.output_format == 'excel'
    
    @patch('vaitp_auditor.gui.gui_session_controller.DataSourceFactory')
    def test_create_data_source_from_config(self, mock_factory_class):
        """Test data source creation from configuration."""
        config = {
            'data_source_type': 'folders',
            'generated_code_path': '/test/generated',
            'expected_code_path': '/test/expected'
        }
        
        mock_source = Mock()
        mock_factory = Mock()
        mock_factory.create_data_source.return_value = mock_source
        mock_factory_class.return_value = mock_factory
        
        # Create new controller to use mocked factory
        controller = GUISessionController()
        result = controller._create_data_source_from_config(config)
        
        # Verify data source factory was used
        mock_factory.create_data_source.assert_called_once_with('folders')
        assert result == mock_source
    
    @patch('vaitp_auditor.gui.gui_session_controller.DataSourceFactory')
    def test_create_data_source_default_fallback(self, mock_factory_class):
        """Test data source creation with default fallback."""
        config = {
            'data_source_type': 'unknown_type'
        }
        
        mock_source = Mock()
        mock_factory = Mock()
        mock_factory.create_data_source.return_value = mock_source
        mock_factory_class.return_value = mock_factory
        
        # Create new controller to use mocked factory
        controller = GUISessionController()
        result = controller._create_data_source_from_config(config)
        
        # Should still call factory with the unknown type (factory handles fallback)
        mock_factory.create_data_source.assert_called_once_with('unknown_type')
        assert result == mock_source
    
    def test_process_review_queue_gui_no_session(self):
        """Test review queue processing without active session."""
        # Should handle gracefully when no session is active
        self.controller.process_review_queue_gui()
        
        # No exceptions should be raised
        assert not self.controller.is_session_active()
    
    def test_process_review_queue_gui_no_window(self):
        """Test review queue processing without main window."""
        # Set session as active but no window
        self.controller._is_session_active = True
        self.controller._session_manager = self.mock_session_manager
        
        # Should handle gracefully when no window is available
        self.controller.process_review_queue_gui()
        
        # No exceptions should be raised
    
    def test_load_next_code_pair_success(self):
        """Test successful loading of next code pair."""
        # Setup mocks
        self.controller._session_manager = self.mock_session_manager
        self.controller._main_window = self.mock_main_window
        
        # Create mock session with code pairs
        mock_session = Mock()
        code_pair = CodePair(
            identifier="test_pair_1",
            expected_code="print('expected')",
            generated_code="print('generated')",
            source_info={}
        )
        mock_session.remaining_queue = [code_pair]
        mock_session.completed_reviews = []
        mock_session.experiment_name = "test_experiment"
        mock_session.get_total_reviews.return_value = 5
        
        self.controller._session_manager._current_session = mock_session
        
        # Load next code pair
        self.controller.load_next_code_pair()
        
        # Verify main window methods were called
        self.mock_main_window.load_code_pair.assert_called_once_with(code_pair)
        self.mock_main_window.update_progress.assert_called_once()
    
    def test_load_next_code_pair_empty_queue(self):
        """Test loading next code pair when queue is empty."""
        # Setup mocks
        self.controller._session_manager = self.mock_session_manager
        self.controller._main_window = self.mock_main_window
        
        # Create mock session with empty queue
        mock_session = Mock()
        mock_session.remaining_queue = []
        mock_session.completed_reviews = ["review1", "review2"]  # Add some completed reviews
        mock_session.experiment_name = "test_experiment"
        mock_session.get_total_reviews.return_value = 2
        self.controller._session_manager._current_session = mock_session
        
        # Mock completion callback
        completion_callback = Mock()
        self.controller.set_session_completion_callback(completion_callback)
        
        # Mock the error handler to avoid GUI dialogs in tests
        self.controller._error_handler = Mock()
        
        # Mock the main window methods that are called during completion
        self.mock_main_window.set_completion_state = Mock()
        
        # Load next code pair (should trigger completion)
        self.controller.load_next_code_pair()
        
        # Verify completion was handled
        completion_callback.assert_called_once()
        self.mock_main_window.set_completion_state.assert_called_once_with("test_experiment")
    
    def test_submit_verdict_success(self):
        """Test successful verdict submission."""
        # Setup mocks
        self.controller._session_manager = self.mock_session_manager
        self.controller._main_window = self.mock_main_window
        self.controller._report_manager = self.mock_report_manager
        
        # Create mock session with code pair
        mock_session = Mock()
        code_pair = CodePair(
            identifier="test_pair_1",
            expected_code="print('expected')",
            generated_code="print('generated')",
            source_info={}
        )
        mock_session.remaining_queue = [code_pair]
        mock_session.completed_reviews = []
        self.controller._session_manager._current_session = mock_session
        
        # Submit verdict
        self.controller.submit_verdict("SUCCESS", "Test comment")
        
        # Verify code pair was removed from queue
        assert len(mock_session.remaining_queue) == 0
        
        # Verify completed reviews was updated
        assert "test_pair_1" in mock_session.completed_reviews
        
        # Verify report manager was called
        self.mock_report_manager.append_review_result.assert_called_once()
        
        # Verify comment was cleared
        self.mock_main_window.clear_comment.assert_called_once()
    
    def test_submit_verdict_no_code_pair(self):
        """Test verdict submission when no code pair is available."""
        # Setup mocks
        self.controller._session_manager = self.mock_session_manager
        self.controller._main_window = self.mock_main_window
        
        # Create mock session with empty queue
        mock_session = Mock()
        mock_session.remaining_queue = []
        self.controller._session_manager._current_session = mock_session
        
        # Submit verdict (should handle gracefully)
        self.controller.submit_verdict("SUCCESS", "Test comment")
        
        # No exceptions should be raised
    
    def test_handle_undo_request_success(self):
        """Test successful undo request handling."""
        # Setup mocks
        self.controller._session_manager = self.mock_session_manager
        self.controller._main_window = self.mock_main_window
        
        # Mock session with empty queue to avoid load_next_code_pair issues
        mock_session = Mock()
        mock_session.remaining_queue = []
        mock_session.completed_reviews = ["review1"]
        mock_session.experiment_name = "test_exp"
        mock_session.get_total_reviews.return_value = 1
        self.mock_session_manager._current_session = mock_session
        
        # Mock undo capability and info
        self.mock_session_manager.can_undo.return_value = True
        self.mock_session_manager.get_undo_info.return_value = {
            'review_id': 5,
            'source_identifier': 'test_file.py',
            'review_count': 5
        }
        self.mock_session_manager.undo_last_review.return_value = True
        
        # Mock the error handler to avoid GUI dialogs in tests
        self.controller._error_handler = Mock()
        self.controller._error_handler.show_confirmation_dialog.return_value = True
        
        # Handle undo request
        self.controller.handle_undo_request()
        
        # Verify undo was called (can_undo may be called multiple times)
        assert self.mock_session_manager.can_undo.call_count >= 1
        self.mock_session_manager.get_undo_info.assert_called_once()
        self.controller._error_handler.show_confirmation_dialog.assert_called_once()
        self.mock_session_manager.undo_last_review.assert_called_once()
    
    def test_handle_undo_request_no_reviews(self):
        """Test undo request when no reviews to undo."""
        # Setup mocks
        self.controller._session_manager = self.mock_session_manager
        
        # Mock no undo capability
        self.mock_session_manager.can_undo.return_value = False
        
        # Handle undo request
        self.controller.handle_undo_request()
        
        # Verify undo was not attempted
        self.mock_session_manager.can_undo.assert_called_once()
        self.mock_session_manager.undo_last_review.assert_not_called()
    
    def test_handle_quit_request(self):
        """Test quit request handling."""
        # Setup completion callback
        completion_callback = Mock()
        self.controller.set_session_completion_callback(completion_callback)
        
        # Handle quit request
        self.controller.handle_quit_request()
        
        # Verify callback was called
        completion_callback.assert_called_once()
    
    def test_get_current_progress_no_session(self):
        """Test progress retrieval without active session."""
        progress_info = self.controller._get_current_progress()
        
        assert isinstance(progress_info, ProgressInfo)
        assert progress_info.current == 0
        assert progress_info.total == 0
        assert progress_info.current_file == "No session"
        assert progress_info.experiment_name == "Unknown"
    
    def test_get_current_progress_with_session(self):
        """Test progress retrieval with active session."""
        # Setup mock session
        self.controller._session_manager = self.mock_session_manager
        
        mock_session = Mock()
        mock_session.completed_reviews = ["review1", "review2"]
        mock_session.get_total_reviews.return_value = 10
        mock_session.experiment_name = "test_experiment"
        
        code_pair = CodePair(
            identifier="current_pair",
            expected_code="test",
            generated_code="test",
            source_info={}
        )
        mock_session.remaining_queue = [code_pair]
        
        self.controller._session_manager._current_session = mock_session
        
        # Get progress
        progress_info = self.controller._get_current_progress()
        
        assert progress_info.current == 3  # 2 completed + 1 current
        assert progress_info.total == 10
        assert progress_info.current_file == "current_pair"
        assert progress_info.experiment_name == "test_experiment"
    
    def test_get_current_progress_dict(self):
        """Test progress retrieval as dictionary."""
        # Setup mock session
        self.controller._session_manager = self.mock_session_manager
        
        mock_session = Mock()
        mock_session.completed_reviews = ["review1"]
        mock_session.get_total_reviews.return_value = 5
        mock_session.experiment_name = "test_exp"
        mock_session.remaining_queue = []  # Empty queue means session is complete
        
        self.controller._session_manager._current_session = mock_session
        
        # Get progress as dict
        progress_dict = self.controller.get_current_progress()
        
        assert isinstance(progress_dict, dict)
        assert progress_dict['current'] == 1  # When queue is empty, current = completed
        assert progress_dict['total'] == 5
        assert progress_dict['percentage'] == 20.0  # 1/5 * 100
        assert progress_dict['experiment_name'] == "test_exp"
        assert 'is_complete' in progress_dict
    
    def test_cleanup(self):
        """Test controller cleanup."""
        # Setup some state
        self.controller._session_manager = self.mock_session_manager
        self.controller._report_manager = self.mock_report_manager
        self.controller._main_window = self.mock_main_window
        self.controller._is_session_active = True
        self.controller._current_session_config = {'test': 'config'}
        
        # Cleanup
        self.controller.cleanup()
        
        # Verify state was cleared
        assert self.controller._session_manager is None
        assert self.controller._report_manager is None
        assert self.controller._main_window is None
        assert not self.controller._is_session_active
        assert self.controller._current_session_config is None
    
    def test_cleanup_with_active_session(self):
        """Test cleanup with active session saves state."""
        # Setup active session
        self.controller._session_manager = self.mock_session_manager
        self.controller._is_session_active = True
        
        # Cleanup
        self.controller.cleanup()
        
        # Verify session state was saved
        self.mock_session_manager.save_session_state.assert_called_once()


class TestGUISessionControllerIntegration:
    """Integration tests for GUISessionController."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.controller = GUISessionController()
        
    def test_window_coordination_workflow(self):
        """Test the basic workflow of window coordination."""
        # Setup mock components
        mock_wizard = Mock()
        mock_main_window = Mock()
        wizard_callback = Mock()
        session_callback = Mock()
        
        # Set up controller
        self.controller.set_setup_wizard(mock_wizard)
        self.controller.set_main_window(mock_main_window)
        self.controller.set_wizard_completion_callback(wizard_callback)
        self.controller.set_session_completion_callback(session_callback)
        
        # Verify all components are set
        assert self.controller._setup_wizard == mock_wizard
        assert self.controller._main_window == mock_main_window
        assert self.controller._wizard_completion_callback == wizard_callback
        assert self.controller._session_completion_callback == session_callback
    
    def test_error_handling_robustness(self):
        """Test that controller handles errors gracefully."""
        # Test various operations without proper setup
        
        # Should not raise exceptions
        self.controller.process_review_queue_gui()
        self.controller.submit_verdict("SUCCESS")
        self.controller.handle_undo_request()
        self.controller.handle_quit_request()
        self.controller.load_next_code_pair()
        
        # Should return sensible defaults
        progress = self.controller.get_current_progress()
        assert isinstance(progress, dict)
        assert progress['current'] == 0
        assert progress['total'] == 0
        
        # Should handle cleanup gracefully
        self.controller.cleanup()
    
    def test_session_lifecycle_management(self):
        """Test complete session lifecycle management."""
        # Test pause/resume functionality
        assert not self.controller.is_session_paused()
        
        # Cannot pause inactive session
        assert not self.controller.pause_session()
        
        # Set up active session
        self.controller._is_session_active = True
        self.controller._session_manager = Mock()
        
        # Test pause
        assert self.controller.pause_session()
        assert self.controller.is_session_paused()
        
        # Test resume
        assert self.controller.resume_session()
        assert not self.controller.is_session_paused()
    
    def test_session_statistics(self):
        """Test session statistics retrieval."""
        # Test with no active session
        stats = self.controller.get_session_statistics()
        assert not stats['active']
        assert stats['completed_reviews'] == 0
        assert stats['experiment_name'] == 'No active session'
        
        # Test with active session
        self.controller._is_session_active = True
        self.controller._session_manager = Mock()
        
        mock_session = Mock()
        mock_session.completed_reviews = ['r1', 'r2']
        mock_session.remaining_queue = ['q1', 'q2', 'q3']
        mock_session.get_total_reviews.return_value = 5
        mock_session.experiment_name = 'test_exp'
        mock_session.session_id = 'test_session_123'
        mock_session.created_timestamp = datetime(2023, 1, 1, 12, 0, 0)
        
        self.controller._session_manager._current_session = mock_session
        
        stats = self.controller.get_session_statistics()
        assert stats['active']
        assert stats['completed_reviews'] == 2
        assert stats['remaining_reviews'] == 3
        assert stats['total_reviews'] == 5
        assert stats['progress_percentage'] == 40.0
        assert stats['experiment_name'] == 'test_exp'
        assert stats['session_id'] == 'test_session_123'
    
    def test_session_state_management(self):
        """Test complete session state management."""
        # Test save session state without active session
        assert not self.controller.save_session_state()
        
        # Test with active session
        self.controller._is_session_active = True
        self.controller._session_manager = Mock()
        
        # Test successful save
        assert self.controller.save_session_state()
        self.controller._session_manager.save_session_state.assert_called_once()
        
        # Test save failure
        self.controller._session_manager.save_session_state.side_effect = Exception("Save failed")
        assert not self.controller.save_session_state()
    
    def test_session_state_info(self):
        """Test session state information retrieval."""
        # Test with no active session
        assert self.controller.get_session_state_info() is None
        
        # Test with active session
        self.controller._is_session_active = True
        self.controller._session_manager = Mock()
        
        mock_session = Mock()
        mock_session.session_id = 'test_123'
        mock_session.experiment_name = 'test_exp'
        mock_session.created_timestamp = datetime(2023, 1, 1, 12, 0, 0)
        mock_session.data_source_config = {'type': 'folders'}
        mock_session.completed_reviews = ['r1']
        mock_session.remaining_queue = ['q1', 'q2']
        mock_session.get_total_reviews.return_value = 3
        
        self.controller._session_manager._current_session = mock_session
        self.controller._session_manager.can_undo.return_value = True
        
        info = self.controller.get_session_state_info()
        assert info is not None
        assert info['session_id'] == 'test_123'
        assert info['experiment_name'] == 'test_exp'
        assert info['completed_reviews'] == 1
        assert info['remaining_reviews'] == 2
        assert info['total_reviews'] == 3
        assert info['can_undo'] is True
    
    def test_force_session_completion(self):
        """Test forced session completion."""
        # Test with no active session
        assert not self.controller.force_session_completion()
        
        # Test with active session
        self.controller._is_session_active = True
        self.controller._session_manager = Mock()
        self.controller._main_window = Mock()
        
        # Mock session with proper structure
        mock_session = Mock()
        mock_session.completed_reviews = []
        mock_session.remaining_queue = []
        mock_session.experiment_name = 'test_exp'
        mock_session.get_total_reviews.return_value = 0
        self.controller._session_manager._current_session = mock_session
        
        completion_callback = Mock()
        self.controller.set_session_completion_callback(completion_callback)
        
        # Test successful forced completion
        assert self.controller.force_session_completion()
        assert not self.controller._is_session_active
        assert not self.controller._session_paused
        completion_callback.assert_called_once()
    
    def test_synchronize_session_state(self):
        """Test session state synchronization."""
        # Test with no active session
        assert not self.controller.synchronize_session_state()
        
        # Test with active session
        self.controller._is_session_active = True
        self.controller._session_manager = Mock()
        self.controller._main_window = Mock()
        
        mock_session = Mock()
        mock_session.remaining_queue = []
        mock_session.completed_reviews = []
        mock_session.experiment_name = 'test'
        mock_session.get_total_reviews.return_value = 0
        self.controller._session_manager._current_session = mock_session
        
        # Test successful synchronization
        assert self.controller.synchronize_session_state()
        self.controller._session_manager.save_session_state.assert_called_once()
    
    def test_resume_session_from_state(self):
        """Test session resumption from saved state."""
        mock_data_source = Mock()
        
        # Test successful resumption
        with patch('vaitp_auditor.gui.gui_session_controller.SessionManager') as mock_sm_class, \
             patch('vaitp_auditor.gui.gui_session_controller.ReportManager') as mock_rm_class:
            
            mock_session_manager = Mock()
            mock_session_manager.resume_session_with_fallback.return_value = True
            mock_session_manager._current_session = Mock()
            mock_session_manager._current_session.remaining_queue = []
            mock_sm_class.return_value = mock_session_manager
            
            mock_report_manager = Mock()
            mock_rm_class.return_value = mock_report_manager
            
            result = self.controller.resume_session_from_state('test_session', mock_data_source)
            
            assert result is True
            assert self.controller._is_session_active
            assert not self.controller._session_paused
            mock_session_manager.resume_session_with_fallback.assert_called_once_with('test_session', mock_data_source)
        
        # Test failed resumption
        with patch('vaitp_auditor.gui.gui_session_controller.SessionManager') as mock_sm_class:
            mock_session_manager = Mock()
            mock_session_manager.resume_session_with_fallback.return_value = False
            mock_sm_class.return_value = mock_session_manager
            
            result = self.controller.resume_session_from_state('test_session', mock_data_source)
            
            assert result is False


if __name__ == '__main__':
    pytest.main([__file__])