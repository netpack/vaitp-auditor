"""
Unit tests for SessionManager core functionality.
"""

import os
import pickle
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from vaitp_auditor.core.models import CodePair, ReviewResult, SessionState, SessionConfig
from vaitp_auditor.data_sources.base import DataSource
from vaitp_auditor.session_manager import SessionManager
from vaitp_auditor.ui.review_controller import ReviewUIController
from vaitp_auditor.reporting.report_manager import ReportManager


class TestSessionManagerCore(unittest.TestCase):
    """Test SessionManager core functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_ui = Mock(spec=ReviewUIController)
        self.mock_report_manager = Mock(spec=ReportManager)
        self.mock_data_source = Mock(spec=DataSource)
        
        # Create session manager with mocked dependencies
        with patch('vaitp_auditor.session_manager.Path.home') as mock_home:
            mock_home.return_value = Path(self.temp_dir)
            self.session_manager = SessionManager(
                ui_controller=self.mock_ui,
                report_manager=self.mock_report_manager
            )
        
        # Sample test data
        self.sample_config = SessionConfig(
            experiment_name="test_experiment",
            data_source_type="folders",
            data_source_params={"generated_path": "/test/generated", "expected_path": "/test/expected"},
            sample_percentage=100.0,
            output_format="excel"
        )
        
        self.sample_code_pairs = [
            CodePair(
                identifier="test1",
                expected_code="def test(): pass",
                generated_code="def test(): return True",
                source_info={"file": "test1.py"}
            ),
            CodePair(
                identifier="test2",
                expected_code="print('hello')",
                generated_code="print('world')",
                source_info={"file": "test2.py"}
            )
        ]

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_start_session_success(self):
        """Test successful session start."""
        # Setup mock data source
        self.mock_data_source.load_data.return_value = self.sample_code_pairs
        
        # Start session
        session_id = self.session_manager.start_session(self.sample_config, self.mock_data_source)
        
        # Verify session was created
        self.assertIsNotNone(session_id)
        self.assertTrue(session_id.startswith("test_experiment_"))
        
        # Verify data source was called correctly
        self.mock_data_source.load_data.assert_called_once_with(100.0)
        
        # Verify report manager was initialized
        self.mock_report_manager.initialize_report.assert_called_once_with(session_id, "excel")
        
        # Verify session state
        progress = self.session_manager.get_session_progress()
        self.assertIsNotNone(progress)
        self.assertEqual(progress['experiment_name'], "test_experiment")
        self.assertEqual(progress['total_reviews'], 2)
        self.assertEqual(progress['completed_reviews'], 0)
        self.assertEqual(progress['remaining_reviews'], 2)

    def test_start_session_no_data(self):
        """Test session start with no data from source."""
        # Setup mock data source to return empty list
        self.mock_data_source.load_data.return_value = []
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.session_manager.start_session(self.sample_config, self.mock_data_source)
        
        self.assertIn("No code pairs loaded", str(context.exception))

    def test_start_session_data_source_error(self):
        """Test session start with data source error."""
        # Setup mock data source to raise exception
        self.mock_data_source.load_data.side_effect = Exception("Data source error")
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.session_manager.start_session(self.sample_config, self.mock_data_source)
        
        self.assertIn("Failed to load data from source", str(context.exception))

    def test_save_and_load_session_state(self):
        """Test session state saving and loading."""
        # Start a session
        self.mock_data_source.load_data.return_value = self.sample_code_pairs
        session_id = self.session_manager.start_session(self.sample_config, self.mock_data_source)
        
        # Verify session file was created
        session_file = self.session_manager._session_dir / f"{session_id}.pkl"
        self.assertTrue(session_file.exists())
        
        # Verify file contents
        with open(session_file, 'rb') as f:
            session_data = pickle.load(f)
        
        self.assertIn('session_state', session_data)
        self.assertIn('next_review_id', session_data)
        self.assertEqual(session_data['session_state'].session_id, session_id)
        self.assertEqual(session_data['session_state'].experiment_name, "test_experiment")

    def test_get_review_for_pair(self):
        """Test getting review for a code pair."""
        # Start a session
        self.mock_data_source.load_data.return_value = self.sample_code_pairs
        session_id = self.session_manager.start_session(self.sample_config, self.mock_data_source)
        
        # Setup mock UI response
        mock_review = ReviewResult(
            review_id=1,
            source_identifier="test1",
            experiment_name="test_experiment",
            review_timestamp_utc=datetime.utcnow(),
            reviewer_verdict="Success",
            reviewer_comment="Looks good",
            time_to_review_seconds=10.0,
            expected_code="def test(): pass",
            generated_code="def test(): return True",
            code_diff="- def test(): pass\n+ def test(): return True"
        )
        self.mock_ui.display_code_pair.return_value = mock_review
        
        # Get review for first code pair
        code_pair = self.sample_code_pairs[0]
        result = self.session_manager.get_review_for_pair(code_pair)
        
        # Verify result
        self.assertEqual(result.source_identifier, "test1")
        self.assertEqual(result.reviewer_verdict, "Success")
        self.assertEqual(result.reviewer_comment, "Looks good")
        self.assertEqual(result.experiment_name, "test_experiment")
        self.assertGreater(result.time_to_review_seconds, 0)

    def test_process_review_queue(self):
        """Test processing the review queue."""
        # Start a session
        self.mock_data_source.load_data.return_value = self.sample_code_pairs
        session_id = self.session_manager.start_session(self.sample_config, self.mock_data_source)
        
        # Setup mock UI responses
        mock_reviews = [
            ReviewResult(
                review_id=1,
                source_identifier="test1",
                experiment_name="test_experiment",
                review_timestamp_utc=datetime.utcnow(),
                reviewer_verdict="Success",
                reviewer_comment="Good",
                time_to_review_seconds=5.0,
                expected_code="def test(): pass",
                generated_code="def test(): return True",
                code_diff="diff1"
            ),
            ReviewResult(
                review_id=2,
                source_identifier="test2",
                experiment_name="test_experiment",
                review_timestamp_utc=datetime.utcnow(),
                reviewer_verdict="Failure - No Change",
                reviewer_comment="Not fixed",
                time_to_review_seconds=8.0,
                expected_code="print('hello')",
                generated_code="print('world')",
                code_diff="diff2"
            )
        ]
        self.mock_ui.display_code_pair.side_effect = mock_reviews
        
        # Process the queue
        self.session_manager.process_review_queue()
        
        # Verify all pairs were processed
        self.assertEqual(self.mock_ui.display_code_pair.call_count, 2)
        self.assertEqual(self.mock_report_manager.append_review_result.call_count, 2)
        
        # Verify session state was updated
        progress = self.session_manager.get_session_progress()
        self.assertEqual(progress['completed_reviews'], 2)
        self.assertEqual(progress['remaining_reviews'], 0)
        self.assertEqual(progress['progress_percentage'], 100.0)

    def test_process_review_queue_quit(self):
        """Test processing queue with quit command."""
        # Start a session
        self.mock_data_source.load_data.return_value = self.sample_code_pairs
        session_id = self.session_manager.start_session(self.sample_config, self.mock_data_source)
        
        # Setup mock UI to return quit on first review
        quit_review = ReviewResult(
            review_id=1,
            source_identifier="test1",
            experiment_name="test_experiment",
            review_timestamp_utc=datetime.utcnow(),
            reviewer_verdict="Quit",
            reviewer_comment="",
            time_to_review_seconds=1.0,
            expected_code="def test(): pass",
            generated_code="def test(): return True",
            code_diff=""
        )
        self.mock_ui.display_code_pair.return_value = quit_review
        
        # Process the queue
        self.session_manager.process_review_queue()
        
        # Verify only one pair was processed
        self.assertEqual(self.mock_ui.display_code_pair.call_count, 1)
        self.assertEqual(self.mock_report_manager.append_review_result.call_count, 0)  # Quit doesn't get saved
        
        # Verify session state
        progress = self.session_manager.get_session_progress()
        self.assertEqual(progress['completed_reviews'], 0)
        self.assertEqual(progress['remaining_reviews'], 1)  # One pair was removed from queue

    def test_process_review_queue_no_session(self):
        """Test processing queue without active session."""
        from vaitp_auditor.utils.error_handling import SessionError
        with self.assertRaises(SessionError) as context:
            self.session_manager.process_review_queue()
        
        self.assertIn("No active session", str(context.exception))

    def test_finalize_session(self):
        """Test session finalization."""
        # Start a session
        self.mock_data_source.load_data.return_value = self.sample_code_pairs
        session_id = self.session_manager.start_session(self.sample_config, self.mock_data_source)
        
        # Setup mock report manager
        self.mock_report_manager.finalize_report.return_value = "/path/to/report.xlsx"
        
        # Finalize session
        report_path = self.session_manager.finalize_session()
        
        # Verify report was finalized
        self.assertEqual(report_path, "/path/to/report.xlsx")
        self.mock_report_manager.finalize_report.assert_called_once_with('excel')
        
        # Verify session was cleared
        progress = self.session_manager.get_session_progress()
        self.assertIsNone(progress)
        
        # Verify session file was cleaned up
        session_file = self.session_manager._session_dir / f"{session_id}.pkl"
        self.assertFalse(session_file.exists())

    def test_finalize_session_no_active(self):
        """Test finalizing when no session is active."""
        result = self.session_manager.finalize_session()
        self.assertIsNone(result)

    def test_list_available_sessions(self):
        """Test listing available sessions."""
        # Initially no sessions
        sessions = self.session_manager.list_available_sessions()
        self.assertEqual(len(sessions), 0)
        
        # Start a session
        self.mock_data_source.load_data.return_value = self.sample_code_pairs
        session_id = self.session_manager.start_session(self.sample_config, self.mock_data_source)
        
        # Should now have one session
        sessions = self.session_manager.list_available_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0], session_id)

    def test_get_session_info(self):
        """Test getting session information."""
        # Start a session
        self.mock_data_source.load_data.return_value = self.sample_code_pairs
        session_id = self.session_manager.start_session(self.sample_config, self.mock_data_source)
        
        # Get session info
        info = self.session_manager.get_session_info(session_id)
        
        # Verify info
        self.assertIsNotNone(info)
        self.assertEqual(info['session_id'], session_id)
        self.assertEqual(info['experiment_name'], "test_experiment")
        self.assertEqual(info['total_reviews'], 2)
        self.assertEqual(info['completed_reviews'], 0)
        self.assertEqual(info['remaining_reviews'], 2)

    def test_get_session_info_nonexistent(self):
        """Test getting info for nonexistent session."""
        info = self.session_manager.get_session_info("nonexistent")
        self.assertIsNone(info)

    def test_atomic_state_saving(self):
        """Test that state saving is atomic."""
        # Start a session
        self.mock_data_source.load_data.return_value = self.sample_code_pairs
        session_id = self.session_manager.start_session(self.sample_config, self.mock_data_source)
        
        session_file = self.session_manager._session_dir / f"{session_id}.pkl"
        temp_file = session_file.with_suffix('.tmp')
        
        # Verify temp file doesn't exist after successful save
        self.assertTrue(session_file.exists())
        self.assertFalse(temp_file.exists())
        
        # Test that temp file is cleaned up on error
        with patch('builtins.open', side_effect=OSError("Disk full")):
            with self.assertRaises(OSError):
                self.session_manager.save_session_state()
        
        # Temp file should be cleaned up
        self.assertFalse(temp_file.exists())


class TestSessionManagerErrorHandling(unittest.TestCase):
    """Test SessionManager error handling scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_ui = Mock(spec=ReviewUIController)
        self.mock_report_manager = Mock(spec=ReportManager)
        
        with patch('vaitp_auditor.session_manager.Path.home') as mock_home:
            mock_home.return_value = Path(self.temp_dir)
            self.session_manager = SessionManager(
                ui_controller=self.mock_ui,
                report_manager=self.mock_report_manager
            )

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_session_no_active_session(self):
        """Test saving state when no session is active."""
        with self.assertRaises(RuntimeError) as context:
            self.session_manager.save_session_state()
        
        self.assertIn("No active session", str(context.exception))

    def test_get_review_no_active_session(self):
        """Test getting review when no session is active."""
        code_pair = CodePair(
            identifier="test",
            expected_code="test",
            generated_code="test",
            source_info={}
        )
        
        with self.assertRaises(RuntimeError) as context:
            self.session_manager.get_review_for_pair(code_pair)
        
        self.assertIn("No active session", str(context.exception))

    def test_process_queue_with_ui_error(self):
        """Test processing queue when UI raises an error."""
        # Start a session
        mock_data_source = Mock(spec=DataSource)
        sample_code_pairs = [
            CodePair(
                identifier="test1",
                expected_code="def test(): pass",
                generated_code="def test(): return True",
                source_info={"file": "test1.py"}
            )
        ]
        mock_data_source.load_data.return_value = sample_code_pairs
        
        config = SessionConfig(
            experiment_name="test_experiment",
            data_source_type="folders",
            data_source_params={},
            sample_percentage=100.0,
            output_format="excel"
        )
        
        session_id = self.session_manager.start_session(config, mock_data_source)
        
        # Setup UI to raise an error
        self.mock_ui.display_code_pair.side_effect = Exception("UI Error")
        
        # Process queue should handle the error gracefully
        self.session_manager.process_review_queue()
        
        # Verify session state is still valid
        progress = self.session_manager.get_session_progress()
        self.assertIsNotNone(progress)


class TestSessionResumption(unittest.TestCase):
    """Test SessionManager session resumption capabilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_ui = Mock(spec=ReviewUIController)
        self.mock_report_manager = Mock(spec=ReportManager)
        
        with patch('vaitp_auditor.session_manager.Path.home') as mock_home:
            mock_home.return_value = Path(self.temp_dir)
            self.session_manager = SessionManager(
                ui_controller=self.mock_ui,
                report_manager=self.mock_report_manager
            )
        
        # Create sample session data
        self.sample_config = SessionConfig(
            experiment_name="test_experiment",
            data_source_type="folders",
            data_source_params={"generated_path": "/test/generated"},
            sample_percentage=100.0,
            output_format="excel"
        )
        
        self.sample_code_pairs = [
            CodePair(
                identifier="test1",
                expected_code="def test(): pass",
                generated_code="def test(): return True",
                source_info={"file": "test1.py"}
            )
        ]

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_resume_session_success(self):
        """Test successful session resumption."""
        # Create a session first
        mock_data_source = Mock(spec=DataSource)
        mock_data_source.load_data.return_value = self.sample_code_pairs
        session_id = self.session_manager.start_session(self.sample_config, mock_data_source)
        
        # Clear current session to simulate restart
        self.session_manager._current_session = None
        self.session_manager._data_source = None
        
        # Resume the session
        success = self.session_manager.resume_session(session_id)
        
        # Verify resumption
        self.assertTrue(success)
        progress = self.session_manager.get_session_progress()
        self.assertIsNotNone(progress)
        self.assertEqual(progress['session_id'], session_id)
        self.assertEqual(progress['experiment_name'], "test_experiment")

    def test_resume_session_nonexistent(self):
        """Test resuming nonexistent session."""
        with self.assertRaises(FileNotFoundError):
            self.session_manager.resume_session("nonexistent_session")

    def test_resume_session_corrupted_file(self):
        """Test resuming session with corrupted file."""
        # Create a corrupted session file
        session_id = "corrupted_session"
        session_file = self.session_manager._session_dir / f"{session_id}.pkl"
        
        # Write invalid data
        with open(session_file, 'wb') as f:
            f.write(b"corrupted data")
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.session_manager.resume_session(session_id)
        
        self.assertIn("Corrupted session file", str(context.exception))

    def test_resume_session_invalid_format(self):
        """Test resuming session with invalid data format."""
        # Create session file with wrong format
        session_id = "invalid_format"
        session_file = self.session_manager._session_dir / f"{session_id}.pkl"
        
        # Write valid pickle but wrong structure
        with open(session_file, 'wb') as f:
            pickle.dump("not a dict", f)
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.session_manager.resume_session(session_id)
        
        self.assertIn("Invalid session file format", str(context.exception))

    def test_resume_session_missing_keys(self):
        """Test resuming session with missing required keys."""
        # Create session file with missing keys
        session_id = "missing_keys"
        session_file = self.session_manager._session_dir / f"{session_id}.pkl"
        
        # Write valid pickle but missing required keys
        incomplete_data = {"session_state": "something"}
        with open(session_file, 'wb') as f:
            pickle.dump(incomplete_data, f)
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.session_manager.resume_session(session_id)
        
        self.assertIn("Missing required session data", str(context.exception))

    def test_resume_session_failed_integrity(self):
        """Test resuming session that fails integrity validation."""
        # Create session with invalid state
        session_id = "invalid_state"
        session_file = self.session_manager._session_dir / f"{session_id}.pkl"
        
        # Create a valid session state first, then corrupt it with wrong data type
        valid_session_state = SessionState(
            session_id="valid_id",
            experiment_name="test",
            data_source_config={},
            completed_reviews=[],
            remaining_queue=[],
            created_timestamp=datetime.utcnow()
        )
        
        # Manually corrupt the data type after creation to fail integrity validation
        valid_session_state.completed_reviews = "not a list"  # This will fail integrity validation
        
        session_data = {
            'session_state': valid_session_state,
            'data_source_config': {},
            'next_review_id': 1
        }
        
        with open(session_file, 'wb') as f:
            pickle.dump(session_data, f)
        
        # Should raise ValueError due to integrity validation failure
        with self.assertRaises(ValueError) as context:
            self.session_manager.resume_session(session_id)
        
        self.assertIn("Session state failed integrity validation", str(context.exception))

    @patch('builtins.input')
    def test_prompt_for_session_resumption_no_sessions(self, mock_input):
        """Test prompting when no sessions are available."""
        result = self.session_manager.prompt_for_session_resumption()
        self.assertIsNone(result)

    @patch('builtins.input')
    @patch('builtins.print')
    def test_prompt_for_session_resumption_with_sessions(self, mock_print, mock_input):
        """Test prompting with available sessions."""
        # Create a session first
        mock_data_source = Mock(spec=DataSource)
        mock_data_source.load_data.return_value = self.sample_code_pairs
        session_id = self.session_manager.start_session(self.sample_config, mock_data_source)
        
        # Mock user selecting the session and confirming
        mock_input.side_effect = ['1', 'y']
        
        result = self.session_manager.prompt_for_session_resumption()
        self.assertEqual(result, session_id)

    @patch('builtins.input')
    @patch('builtins.print')
    def test_prompt_for_session_resumption_new_session(self, mock_print, mock_input):
        """Test prompting and choosing new session."""
        # Create a session first
        mock_data_source = Mock(spec=DataSource)
        mock_data_source.load_data.return_value = self.sample_code_pairs
        session_id = self.session_manager.start_session(self.sample_config, mock_data_source)
        
        # Mock user selecting new session option
        mock_input.side_effect = ['2']  # Assuming 2 is "start new session"
        
        result = self.session_manager.prompt_for_session_resumption()
        self.assertIsNone(result)

    @patch('builtins.input')
    @patch('builtins.print')
    def test_prompt_for_session_resumption_invalid_input(self, mock_print, mock_input):
        """Test prompting with invalid user input."""
        # Create a session first
        mock_data_source = Mock(spec=DataSource)
        mock_data_source.load_data.return_value = self.sample_code_pairs
        session_id = self.session_manager.start_session(self.sample_config, mock_data_source)
        
        # Mock user entering invalid input then valid input
        mock_input.side_effect = ['invalid', '0', '999', '1', 'y']
        
        result = self.session_manager.prompt_for_session_resumption()
        self.assertEqual(result, session_id)

    def test_resume_session_with_fallback_success(self):
        """Test successful session resumption with fallback method."""
        # Create a session first
        mock_data_source = Mock(spec=DataSource)
        mock_data_source.load_data.return_value = self.sample_code_pairs
        session_id = self.session_manager.start_session(self.sample_config, mock_data_source)
        
        # Clear current session
        self.session_manager._current_session = None
        self.session_manager._data_source = None
        
        # Resume with fallback
        success = self.session_manager.resume_session_with_fallback(session_id, mock_data_source)
        
        # Verify success
        self.assertTrue(success)
        progress = self.session_manager.get_session_progress()
        self.assertIsNotNone(progress)

    @patch('builtins.input')
    @patch('builtins.print')
    def test_resume_session_with_fallback_corrupted(self, mock_print, mock_input):
        """Test session resumption fallback with corrupted file."""
        # Create corrupted session file
        session_id = "corrupted_session"
        session_file = self.session_manager._session_dir / f"{session_id}.pkl"
        with open(session_file, 'wb') as f:
            f.write(b"corrupted")
        
        # Mock user choosing to start fresh session
        mock_input.side_effect = ['1']
        
        mock_data_source = Mock(spec=DataSource)
        success = self.session_manager.resume_session_with_fallback(session_id, mock_data_source)
        
        # Should return False (fallback used)
        self.assertFalse(success)

    @patch('builtins.input')
    @patch('builtins.print')
    def test_handle_session_fallback_delete_option(self, mock_print, mock_input):
        """Test session fallback delete option."""
        # Create corrupted session file
        session_id = "corrupted_session"
        session_file = self.session_manager._session_dir / f"{session_id}.pkl"
        with open(session_file, 'wb') as f:
            f.write(b"corrupted")
        
        # Mock user choosing delete option and confirming
        mock_input.side_effect = ['3', 'yes']
        
        result = self.session_manager._handle_session_fallback(session_id, "test error")
        
        # Should return False and file should be deleted
        self.assertFalse(result)
        self.assertFalse(session_file.exists())

    @patch('builtins.input')
    @patch('builtins.print')
    def test_handle_session_fallback_cancel(self, mock_print, mock_input):
        """Test session fallback cancel option."""
        mock_input.side_effect = ['4']
        
        with self.assertRaises(KeyboardInterrupt):
            self.session_manager._handle_session_fallback("test_session", "test error")

    def test_cleanup_old_sessions(self):
        """Test cleanup of old session files."""
        # Create some old session files
        old_session_file = self.session_manager._session_dir / "old_session.pkl"
        with open(old_session_file, 'wb') as f:
            pickle.dump({}, f)
        
        # Set file modification time to be old
        old_time = datetime.now().timestamp() - (40 * 24 * 60 * 60)  # 40 days ago
        os.utime(old_session_file, (old_time, old_time))
        
        # Create a recent session file
        recent_session_file = self.session_manager._session_dir / "recent_session.pkl"
        with open(recent_session_file, 'wb') as f:
            pickle.dump({}, f)
        
        # Cleanup sessions older than 30 days
        cleaned_count = self.session_manager.cleanup_old_sessions(30)
        
        # Should have cleaned up 1 file
        self.assertEqual(cleaned_count, 1)
        self.assertFalse(old_session_file.exists())
        self.assertTrue(recent_session_file.exists())

    def test_cleanup_old_sessions_invalid_days(self):
        """Test cleanup with invalid days parameter."""
        with self.assertRaises(ValueError):
            self.session_manager.cleanup_old_sessions(0)
        
        with self.assertRaises(ValueError):
            self.session_manager.cleanup_old_sessions(-1)


if __name__ == '__main__':
    unittest.main()