"""
Integration tests for ReviewUIController class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from rich.console import Console

from vaitp_auditor.ui.review_controller import ReviewUIController
from vaitp_auditor.core.models import CodePair, ReviewResult


class TestReviewUIController:
    """Test cases for ReviewUIController class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Disable scrolling for tests to avoid hanging on input
        self.controller = ReviewUIController(enable_scrolling=False)
        
        # Sample code pair for testing
        self.sample_code_pair = CodePair(
            identifier="test_pair_1",
            expected_code="def test():\n    return True",
            generated_code="def test():\n    return False",
            source_info={"file": "test.py"}
        )
        
        self.progress_info = {
            "current": 1,
            "total": 10,
            "percentage": 10.0
        }

    def test_init_default_console(self):
        """Test ReviewUIController initialization with default console."""
        controller = ReviewUIController()
        assert isinstance(controller.console, Console)
        assert controller.display_manager is not None
        assert controller.input_handler is not None
        assert controller.diff_renderer is not None
        assert controller.code_differ is not None
        assert controller._review_id_counter == 1

    def test_init_custom_console(self):
        """Test ReviewUIController initialization with custom console."""
        custom_console = Mock(spec=Console)
        controller = ReviewUIController(custom_console)
        assert controller.console is custom_console

    @patch('vaitp_auditor.ui.review_controller.time.time')
    @patch('vaitp_auditor.ui.review_controller.datetime')
    def test_display_code_pair_success(self, mock_datetime, mock_time):
        """Test successful display_code_pair execution."""
        # Mock time
        mock_time.side_effect = [1000.0, 1005.0]  # 5 second review
        mock_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        
        # Mock the UI components
        with patch.object(self.controller, '_render_code_pair_display') as mock_render, \
             patch.object(self.controller, 'handle_user_input') as mock_input, \
             patch.object(self.controller, '_get_diff_text') as mock_diff:
            
            mock_input.return_value = ('Success', 'Great work!')
            mock_diff.return_value = 'diff content'
            
            result = self.controller.display_code_pair(
                self.sample_code_pair,
                self.progress_info,
                "test_experiment"
            )
            
            # Verify the result
            assert isinstance(result, ReviewResult)
            assert result.review_id == 1
            assert result.source_identifier == "test_pair_1"
            assert result.experiment_name == "test_experiment"
            assert result.reviewer_verdict == "Success"
            assert result.reviewer_comment == "Great work!"
            assert result.time_to_review_seconds == 5.0
            assert result.expected_code == self.sample_code_pair.expected_code
            assert result.generated_code == self.sample_code_pair.generated_code
            assert result.code_diff == 'diff content'
            
            # Verify methods were called
            mock_render.assert_called_once_with(self.sample_code_pair, self.progress_info)
            mock_input.assert_called_once()

    @patch('vaitp_auditor.ui.review_controller.time.time')
    def test_display_code_pair_with_exception(self, mock_time):
        """Test display_code_pair with rendering exception."""
        mock_time.side_effect = [1000.0, 1003.0]  # 3 second review
        
        # Mock components to raise exception on render
        with patch.object(self.controller, '_render_code_pair_display') as mock_render, \
             patch.object(self.controller, '_render_fallback_display') as mock_fallback, \
             patch.object(self.controller, 'handle_user_input') as mock_input, \
             patch.object(self.controller.input_handler, 'show_error_message') as mock_error:
            
            mock_render.side_effect = Exception("Rendering failed")
            mock_input.return_value = ('Failure - No Change', 'Error occurred')
            
            result = self.controller.display_code_pair(
                self.sample_code_pair,
                self.progress_info,
                "test_experiment"
            )
            
            # Should still return a valid result
            assert isinstance(result, ReviewResult)
            assert result.reviewer_verdict == "Failure - No Change"
            assert result.reviewer_comment == "Error occurred"
            
            # Verify error handling was called
            mock_error.assert_called_once()
            mock_fallback.assert_called_once()

    def test_handle_user_input(self):
        """Test handle_user_input delegation."""
        with patch.object(self.controller.input_handler, 'get_user_verdict') as mock_verdict:
            mock_verdict.return_value = ('Success', 'Test comment')
            
            verdict, comment = self.controller.handle_user_input()
            
            assert verdict == 'Success'
            assert comment == 'Test comment'
            mock_verdict.assert_called_once()

    def test_render_diff_success(self):
        """Test successful diff rendering."""
        with patch.object(self.controller.code_differ, 'compute_diff') as mock_compute, \
             patch.object(self.controller.diff_renderer, 'create_diff_summary') as mock_summary, \
             patch.object(self.controller.diff_renderer, 'get_color_legend') as mock_legend, \
             patch.object(self.controller.diff_renderer, 'render_diff_with_context') as mock_context:
            
            mock_compute.return_value = []
            mock_summary.return_value = "Summary"
            mock_legend.return_value = "Legend"
            mock_context.return_value = "Context"
            
            self.controller.render_diff("expected", "generated")
            
            mock_compute.assert_called_once_with("expected", "generated")
            mock_summary.assert_called_once()
            mock_legend.assert_called_once()
            mock_context.assert_called_once()

    def test_render_diff_with_exception(self):
        """Test diff rendering with exception."""
        with patch.object(self.controller.code_differ, 'compute_diff') as mock_compute, \
             patch.object(self.controller, '_render_fallback_diff') as mock_fallback, \
             patch.object(self.controller.input_handler, 'show_error_message') as mock_error:
            
            mock_compute.side_effect = Exception("Diff failed")
            
            self.controller.render_diff("expected", "generated")
            
            mock_error.assert_called_once()
            mock_fallback.assert_called_once_with("expected", "generated")

    def test_show_diff_view(self):
        """Test show_diff_view functionality."""
        with patch.object(self.controller.console, 'clear') as mock_clear, \
             patch.object(self.controller.console, 'print') as mock_print, \
             patch.object(self.controller, 'render_diff') as mock_render, \
             patch.object(self.controller.input_handler, 'prompt_for_input') as mock_prompt:
            
            mock_prompt.return_value = ""
            
            self.controller.show_diff_view(self.sample_code_pair)
            
            mock_clear.assert_called_once()
            mock_render.assert_called_once_with(
                self.sample_code_pair.expected_code,
                self.sample_code_pair.generated_code
            )
            mock_prompt.assert_called_once()

    def test_render_code_pair_display(self):
        """Test _render_code_pair_display method."""
        with patch.object(self.controller.display_manager, 'render_code_panels') as mock_render:
            
            self.controller._render_code_pair_display(self.sample_code_pair, self.progress_info)
            
            mock_render.assert_called_once_with(
                expected=self.sample_code_pair.expected_code,
                generated=self.sample_code_pair.generated_code,
                progress_info=self.progress_info,
                source_identifier=self.sample_code_pair.identifier
            )

    def test_render_fallback_display(self):
        """Test _render_fallback_display method."""
        with patch.object(self.controller.console, 'clear') as mock_clear, \
             patch.object(self.controller.console, 'print') as mock_print:
            
            self.controller._render_fallback_display(self.sample_code_pair, self.progress_info)
            
            mock_clear.assert_called_once()
            # Should have multiple print calls for the fallback display
            assert mock_print.call_count >= 4

    def test_render_fallback_display_no_expected(self):
        """Test _render_fallback_display with no expected code."""
        code_pair_no_expected = CodePair(
            identifier="test_pair_2",
            expected_code=None,
            generated_code="def test():\n    return False",
            source_info={"file": "test.py"}
        )
        
        with patch.object(self.controller.console, 'clear') as mock_clear, \
             patch.object(self.controller.console, 'print') as mock_print:
            
            self.controller._render_fallback_display(code_pair_no_expected, self.progress_info)
            
            mock_clear.assert_called_once()
            # Should handle None expected code gracefully
            assert mock_print.call_count >= 4

    def test_render_fallback_diff_with_diff(self):
        """Test _render_fallback_diff with actual diff content."""
        with patch.object(self.controller.code_differ, 'get_diff_text') as mock_diff, \
             patch.object(self.controller.console, 'print') as mock_print:
            
            mock_diff.return_value = "diff content"
            
            self.controller._render_fallback_diff("expected", "generated")
            
            mock_diff.assert_called_once_with("expected", "generated")
            assert mock_print.call_count == 2  # Header and content

    def test_render_fallback_diff_no_diff(self):
        """Test _render_fallback_diff with no diff content."""
        with patch.object(self.controller.code_differ, 'get_diff_text') as mock_diff, \
             patch.object(self.controller.console, 'print') as mock_print:
            
            mock_diff.return_value = ""
            
            self.controller._render_fallback_diff("expected", "generated")
            
            mock_diff.assert_called_once_with("expected", "generated")
            mock_print.assert_called_once_with("\n=== NO DIFFERENCES FOUND ===")

    def test_get_diff_text_success(self):
        """Test _get_diff_text successful execution."""
        with patch.object(self.controller.code_differ, 'get_diff_text') as mock_diff:
            mock_diff.return_value = "diff content"
            
            result = self.controller._get_diff_text("expected", "generated")
            
            assert result == "diff content"
            mock_diff.assert_called_once_with("expected", "generated")

    def test_get_diff_text_exception(self):
        """Test _get_diff_text with exception."""
        with patch.object(self.controller.code_differ, 'get_diff_text') as mock_diff:
            mock_diff.side_effect = Exception("Diff error")
            
            result = self.controller._get_diff_text("expected", "generated")
            
            assert result == "Error computing diff"

    def test_get_next_review_id(self):
        """Test review ID generation."""
        assert self.controller._get_next_review_id() == 1
        assert self.controller._get_next_review_id() == 2
        assert self.controller._get_next_review_id() == 3

    def test_set_review_id_counter(self):
        """Test setting review ID counter."""
        self.controller.set_review_id_counter(100)
        assert self.controller._get_next_review_id() == 100
        assert self.controller._get_next_review_id() == 101

    def test_show_help(self):
        """Test show_help delegation."""
        with patch.object(self.controller.input_handler, 'display_help') as mock_help:
            self.controller.show_help()
            mock_help.assert_called_once()

    def test_confirm_action(self):
        """Test confirm_action delegation."""
        with patch.object(self.controller.input_handler, 'get_confirmation') as mock_confirm:
            mock_confirm.return_value = True
            
            result = self.controller.confirm_action("Test message")
            
            assert result is True
            mock_confirm.assert_called_once_with("Test message")

    def test_show_message_info(self):
        """Test show_message with info type."""
        with patch.object(self.controller.input_handler, 'show_info_message') as mock_info:
            self.controller.show_message("Test message", "info")
            mock_info.assert_called_once_with("Test message")

    def test_show_message_error(self):
        """Test show_message with error type."""
        with patch.object(self.controller.input_handler, 'show_error_message') as mock_error:
            self.controller.show_message("Test message", "error")
            mock_error.assert_called_once_with("Test message")

    def test_show_message_success(self):
        """Test show_message with success type."""
        with patch.object(self.controller.input_handler, 'show_success_message') as mock_success:
            self.controller.show_message("Test message", "success")
            mock_success.assert_called_once_with("Test message")

    def test_show_message_warning(self):
        """Test show_message with warning type."""
        with patch.object(self.controller.display_manager, 'show_warning') as mock_warning:
            self.controller.show_message("Test message", "warning")
            mock_warning.assert_called_once_with("Test message")

    def test_show_message_default(self):
        """Test show_message with default type."""
        with patch.object(self.controller.input_handler, 'show_info_message') as mock_info:
            self.controller.show_message("Test message")
            mock_info.assert_called_once_with("Test message")

    def test_multiple_code_pairs_review_id_increment(self):
        """Test that review IDs increment correctly across multiple reviews."""
        with patch.object(self.controller, '_render_code_pair_display'), \
             patch.object(self.controller, 'handle_user_input') as mock_input, \
             patch.object(self.controller, '_get_diff_text'):
            
            mock_input.return_value = ('Success', 'Test')
            
            # First review
            result1 = self.controller.display_code_pair(
                self.sample_code_pair, self.progress_info, "test"
            )
            
            # Second review
            result2 = self.controller.display_code_pair(
                self.sample_code_pair, self.progress_info, "test"
            )
            
            assert result1.review_id == 1
            assert result2.review_id == 2

    def test_integration_with_real_components(self):
        """Test integration with real component instances (not mocked)."""
        # This test uses real components to ensure they work together
        code_pair = CodePair(
            identifier="integration_test",
            expected_code="print('hello')",
            generated_code="print('world')",
            source_info={}
        )
        
        # Test diff computation
        diff_lines = self.controller.code_differ.compute_diff(
            code_pair.expected_code,
            code_pair.generated_code
        )
        
        # Should have some diff lines
        assert len(diff_lines) > 0
        
        # Test diff text generation
        diff_text = self.controller._get_diff_text(
            code_pair.expected_code,
            code_pair.generated_code
        )
        
        # Should have diff content
        assert diff_text != ""
        assert "hello" in diff_text or "world" in diff_text