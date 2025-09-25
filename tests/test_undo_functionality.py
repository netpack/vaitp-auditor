"""
Unit tests for undo functionality across the system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from vaitp_auditor.core.models import CodePair, ReviewResult, SessionState, SessionConfig
from vaitp_auditor.session_manager import SessionManager
from vaitp_auditor.ui.review_controller import ReviewUIController
from vaitp_auditor.reporting.report_manager import ReportManager
from vaitp_auditor.data_sources.base import DataSource


class TestUndoFunctionality:
    """Test cases for undo functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock components
        self.mock_ui = Mock(spec=ReviewUIController)
        self.mock_report_manager = Mock(spec=ReportManager)
        self.mock_data_source = Mock(spec=DataSource)
        
        # Create session manager with mocked components
        self.session_manager = SessionManager(
            ui_controller=self.mock_ui,
            report_manager=self.mock_report_manager
        )
        
        # Sample code pairs
        self.code_pair_1 = CodePair(
            identifier="test_1",
            expected_code="def test(): pass",
            generated_code="def test(): return True",
            source_info={"file": "test1.py"}
        )
        
        self.code_pair_2 = CodePair(
            identifier="test_2",
            expected_code="def foo(): return 1",
            generated_code="def foo(): return 2",
            source_info={"file": "test2.py"}
        )
        
        # Sample review result
        self.review_result = ReviewResult(
            review_id=1,
            source_identifier="test_1",
            experiment_name="test_experiment",
            review_timestamp_utc=datetime.now(timezone.utc),
            reviewer_verdict="Success",
            reviewer_comment="Good work",
            time_to_review_seconds=5.0,
            expected_code="def test(): pass",
            generated_code="def test(): return True",
            code_diff="+ return True"
        )

    def test_undo_with_no_active_session(self):
        """Test undo when no session is active."""
        with pytest.raises(RuntimeError, match="No active session"):
            self.session_manager.undo_last_review()

    def test_undo_with_no_completed_reviews(self):
        """Test undo when no reviews have been completed."""
        # Set up session with no completed reviews
        self.session_manager._current_session = SessionState(
            session_id="test_session",
            experiment_name="test",
            data_source_config={},
            completed_reviews=[],
            remaining_queue=[self.code_pair_1],
            created_timestamp=datetime.utcnow()
        )
        
        result = self.session_manager.undo_last_review()
        assert result is False

    def test_undo_with_no_last_reviewed_pair(self):
        """Test undo when no last reviewed pair is stored."""
        # Set up session with completed reviews but no stored pair
        self.session_manager._current_session = SessionState(
            session_id="test_session",
            experiment_name="test",
            data_source_config={},
            completed_reviews=["test_1"],
            remaining_queue=[],
            created_timestamp=datetime.utcnow()
        )
        self.session_manager._last_reviewed_pair = None
        
        result = self.session_manager.undo_last_review()
        assert result is False

    def test_undo_with_no_report_review_id(self):
        """Test undo when report manager has no last review ID."""
        # Set up session
        self.session_manager._current_session = SessionState(
            session_id="test_session",
            experiment_name="test",
            data_source_config={},
            completed_reviews=["test_1"],
            remaining_queue=[],
            created_timestamp=datetime.utcnow()
        )
        self.session_manager._last_reviewed_pair = self.code_pair_1
        
        # Mock report manager to return None for last review ID
        self.mock_report_manager.get_last_review_id.return_value = None
        
        result = self.session_manager.undo_last_review()
        assert result is False

    def test_undo_with_report_removal_failure(self):
        """Test undo when report manager fails to remove last review."""
        # Set up session
        self.session_manager._current_session = SessionState(
            session_id="test_session",
            experiment_name="test",
            data_source_config={},
            completed_reviews=["test_1"],
            remaining_queue=[],
            created_timestamp=datetime.utcnow()
        )
        self.session_manager._last_reviewed_pair = self.code_pair_1
        
        # Mock report manager
        self.mock_report_manager.get_last_review_id.return_value = 1
        self.mock_report_manager.remove_last_review.return_value = False
        
        result = self.session_manager.undo_last_review()
        assert result is False

    def test_successful_undo(self):
        """Test successful undo operation."""
        # Set up session
        self.session_manager._current_session = SessionState(
            session_id="test_session",
            experiment_name="test",
            data_source_config={},
            completed_reviews=["test_1"],
            remaining_queue=[self.code_pair_2],
            created_timestamp=datetime.utcnow()
        )
        self.session_manager._last_reviewed_pair = self.code_pair_1
        
        # Mock report manager
        self.mock_report_manager.get_last_review_id.return_value = 1
        self.mock_report_manager.remove_last_review.return_value = True
        
        # Mock save_session_state
        with patch.object(self.session_manager, 'save_session_state'):
            result = self.session_manager.undo_last_review()
        
        assert result is True
        assert len(self.session_manager._current_session.completed_reviews) == 0
        assert len(self.session_manager._current_session.remaining_queue) == 2
        assert self.session_manager._current_session.remaining_queue[0] == self.code_pair_1
        assert self.session_manager._last_reviewed_pair is None

    def test_undo_with_identifier_mismatch(self):
        """Test undo when stored pair identifier doesn't match completed review."""
        # Set up session with mismatched identifiers
        self.session_manager._current_session = SessionState(
            session_id="test_session",
            experiment_name="test",
            data_source_config={},
            completed_reviews=["test_2"],  # Different from stored pair
            remaining_queue=[],
            created_timestamp=datetime.utcnow()
        )
        self.session_manager._last_reviewed_pair = self.code_pair_1  # identifier is "test_1"
        
        # Mock report manager
        self.mock_report_manager.get_last_review_id.return_value = 1
        self.mock_report_manager.remove_last_review.return_value = True
        
        result = self.session_manager.undo_last_review()
        assert result is False
        # Should restore the completed review
        assert "test_2" in self.session_manager._current_session.completed_reviews

    def test_can_undo_with_no_session(self):
        """Test can_undo when no session is active."""
        result = self.session_manager.can_undo()
        assert result is False

    def test_can_undo_with_no_completed_reviews(self):
        """Test can_undo when no reviews are completed."""
        self.session_manager._current_session = SessionState(
            session_id="test_session",
            experiment_name="test",
            data_source_config={},
            completed_reviews=[],
            remaining_queue=[self.code_pair_1],
            created_timestamp=datetime.utcnow()
        )
        
        result = self.session_manager.can_undo()
        assert result is False

    def test_can_undo_with_completed_reviews(self):
        """Test can_undo when reviews are completed."""
        self.session_manager._current_session = SessionState(
            session_id="test_session",
            experiment_name="test",
            data_source_config={},
            completed_reviews=["test_1"],
            remaining_queue=[],
            created_timestamp=datetime.utcnow()
        )
        
        result = self.session_manager.can_undo()
        assert result is True

    def test_get_undo_info_with_no_undo_possible(self):
        """Test get_undo_info when undo is not possible."""
        result = self.session_manager.get_undo_info()
        assert result is None

    def test_get_undo_info_with_undo_possible(self):
        """Test get_undo_info when undo is possible."""
        self.session_manager._current_session = SessionState(
            session_id="test_session",
            experiment_name="test",
            data_source_config={},
            completed_reviews=["test_1", "test_2"],
            remaining_queue=[],
            created_timestamp=datetime.utcnow()
        )
        
        self.mock_report_manager.get_last_review_id.return_value = 2
        
        result = self.session_manager.get_undo_info()
        
        assert result is not None
        assert result['review_id'] == 2
        assert result['source_identifier'] == "test_2"
        assert result['review_count'] == 2

    def test_multiple_consecutive_undos(self):
        """Test multiple consecutive undo operations."""
        # Set up session with multiple completed reviews
        self.session_manager._current_session = SessionState(
            session_id="test_session",
            experiment_name="test",
            data_source_config={},
            completed_reviews=["test_1", "test_2"],
            remaining_queue=[],
            created_timestamp=datetime.utcnow()
        )
        
        # Mock report manager for first undo
        self.mock_report_manager.get_last_review_id.side_effect = [2, 1, None]
        self.mock_report_manager.remove_last_review.side_effect = [True, True, False]
        
        # First undo - should succeed
        self.session_manager._last_reviewed_pair = self.code_pair_2
        with patch.object(self.session_manager, 'save_session_state'):
            result1 = self.session_manager.undo_last_review()
        
        assert result1 is True
        assert len(self.session_manager._current_session.completed_reviews) == 1
        assert self.session_manager._current_session.remaining_queue[0] == self.code_pair_2
        
        # Second undo - should fail because no last_reviewed_pair
        result2 = self.session_manager.undo_last_review()
        assert result2 is False

    def test_undo_edge_case_empty_queue(self):
        """Test undo when queue becomes empty after undo."""
        # Set up session with one completed review
        self.session_manager._current_session = SessionState(
            session_id="test_session",
            experiment_name="test",
            data_source_config={},
            completed_reviews=["test_1"],
            remaining_queue=[],
            created_timestamp=datetime.utcnow()
        )
        self.session_manager._last_reviewed_pair = self.code_pair_1
        
        # Mock report manager
        self.mock_report_manager.get_last_review_id.return_value = 1
        self.mock_report_manager.remove_last_review.return_value = True
        
        with patch.object(self.session_manager, 'save_session_state'):
            result = self.session_manager.undo_last_review()
        
        assert result is True
        assert len(self.session_manager._current_session.completed_reviews) == 0
        assert len(self.session_manager._current_session.remaining_queue) == 1
        assert self.session_manager._current_session.remaining_queue[0] == self.code_pair_1

    def test_undo_preserves_queue_order(self):
        """Test that undo preserves the order of remaining queue items."""
        # Set up session with items in queue
        self.session_manager._current_session = SessionState(
            session_id="test_session",
            experiment_name="test",
            data_source_config={},
            completed_reviews=["test_1"],
            remaining_queue=[self.code_pair_2],  # This should remain second
            created_timestamp=datetime.utcnow()
        )
        self.session_manager._last_reviewed_pair = self.code_pair_1
        
        # Mock report manager
        self.mock_report_manager.get_last_review_id.return_value = 1
        self.mock_report_manager.remove_last_review.return_value = True
        
        with patch.object(self.session_manager, 'save_session_state'):
            result = self.session_manager.undo_last_review()
        
        assert result is True
        assert len(self.session_manager._current_session.remaining_queue) == 2
        assert self.session_manager._current_session.remaining_queue[0] == self.code_pair_1  # Undone item first
        assert self.session_manager._current_session.remaining_queue[1] == self.code_pair_2  # Original item second


class TestReviewUIControllerUndo:
    """Test undo functionality in ReviewUIController."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_undo_callback = Mock(return_value=True)
        self.controller = ReviewUIController(enable_scrolling=False, undo_callback=self.mock_undo_callback)
        
        self.code_pair = CodePair(
            identifier="test_1",
            expected_code="def test(): pass",
            generated_code="def test(): return True",
            source_info={"file": "test1.py"}
        )
        
        self.progress_info = {
            'current': 1,
            'total': 5,
            'percentage': 20.0
        }

    @patch('vaitp_auditor.ui.review_controller.time.time')
    @patch('vaitp_auditor.ui.review_controller.datetime')
    def test_undo_command_successful(self, mock_datetime, mock_time):
        """Test successful undo command handling."""
        mock_time.side_effect = [1000.0, 1005.0]
        mock_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        
        with patch.object(self.controller, '_render_code_pair_display'), \
             patch.object(self.controller, 'handle_user_input') as mock_input:
            
            mock_input.return_value = ('Undo', '')
            
            result = self.controller.display_code_pair(
                self.code_pair,
                self.progress_info,
                "test_experiment"
            )
            
            # Should call undo callback
            self.mock_undo_callback.assert_called_once()
            
            # Should return special undo result
            assert result.reviewer_verdict == "Undo"
            assert result.source_identifier == "UNDO"
            assert result.review_id == 0

    @patch('vaitp_auditor.ui.review_controller.time.time')
    @patch('vaitp_auditor.ui.review_controller.datetime')
    def test_undo_command_failed(self, mock_datetime, mock_time):
        """Test undo command when undo fails."""
        mock_time.side_effect = [1000.0, 1005.0, 1010.0]
        mock_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        
        # Mock undo callback to return False (failure)
        self.mock_undo_callback.return_value = False
        
        with patch.object(self.controller, '_render_code_pair_display'), \
             patch.object(self.controller, 'handle_user_input') as mock_input, \
             patch.object(self.controller, 'show_message') as mock_show_message:
            
            # First call returns undo, second call returns success
            mock_input.side_effect = [('Undo', ''), ('Success', 'Good')]
            
            result = self.controller.display_code_pair(
                self.code_pair,
                self.progress_info,
                "test_experiment"
            )
            
            # Should call undo callback
            self.mock_undo_callback.assert_called_once()
            
            # Should show warning message
            mock_show_message.assert_called_once_with("No review to undo or undo failed.", "warning")
            
            # Should eventually return success result
            assert result.reviewer_verdict == "Success"
            assert result.reviewer_comment == "Good"

    def test_undo_command_no_callback(self):
        """Test undo command when no callback is provided."""
        controller = ReviewUIController(enable_scrolling=False, undo_callback=None)
        
        with patch.object(controller, '_render_code_pair_display'), \
             patch.object(controller, 'handle_user_input') as mock_input, \
             patch.object(controller, 'show_message') as mock_show_message:
            
            # First call returns undo, second call returns success
            mock_input.side_effect = [('Undo', ''), ('Success', 'Good')]
            
            result = controller.display_code_pair(
                self.code_pair,
                self.progress_info,
                "test_experiment"
            )
            
            # Should show warning message
            mock_show_message.assert_called_once_with("No review to undo or undo failed.", "warning")
            
            # Should eventually return success result
            assert result.reviewer_verdict == "Success"


class TestIntegratedUndoWorkflow:
    """Test integrated undo workflow across components."""

    def setup_method(self):
        """Set up integrated test fixtures."""
        self.report_manager = ReportManager()
        self.session_manager = SessionManager(report_manager=self.report_manager)
        
        # Sample data
        self.code_pairs = [
            CodePair(
                identifier="test_1",
                expected_code="def test1(): pass",
                generated_code="def test1(): return True",
                source_info={"file": "test1.py"}
            ),
            CodePair(
                identifier="test_2", 
                expected_code="def test2(): pass",
                generated_code="def test2(): return False",
                source_info={"file": "test2.py"}
            )
        ]

    def test_end_to_end_undo_workflow(self):
        """Test complete undo workflow from UI to report management."""
        # Initialize report manager
        self.report_manager.initialize_report("test_session", "csv")
        
        # Create session state
        self.session_manager._current_session = SessionState(
            session_id="test_session",
            experiment_name="test",
            data_source_config={},
            completed_reviews=[],
            remaining_queue=self.code_pairs.copy(),
            created_timestamp=datetime.utcnow()
        )
        
        # Simulate completing a review
        review_result = ReviewResult(
            review_id=1,
            source_identifier="test_1",
            experiment_name="test",
            review_timestamp_utc=datetime.now(timezone.utc),
            reviewer_verdict="Success",
            reviewer_comment="Good",
            time_to_review_seconds=5.0,
            expected_code="def test1(): pass",
            generated_code="def test1(): return True",
            code_diff="+ return True"
        )
        
        # Add review to report and session
        self.report_manager.append_review_result(review_result)
        self.session_manager._current_session.completed_reviews.append("test_1")
        self.session_manager._current_session.remaining_queue.pop(0)
        self.session_manager._last_reviewed_pair = self.code_pairs[0]
        
        # Verify initial state
        assert len(self.session_manager._current_session.completed_reviews) == 1
        assert len(self.session_manager._current_session.remaining_queue) == 1
        assert self.report_manager.get_last_review_id() == 1
        
        # Perform undo
        with patch.object(self.session_manager, 'save_session_state'):
            undo_success = self.session_manager.undo_last_review()
        
        # Verify undo results
        assert undo_success is True
        assert len(self.session_manager._current_session.completed_reviews) == 0
        assert len(self.session_manager._current_session.remaining_queue) == 2
        assert self.session_manager._current_session.remaining_queue[0] == self.code_pairs[0]
        assert self.report_manager.get_last_review_id() is None  # No reviews left