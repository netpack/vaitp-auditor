"""
Unit tests for MainReviewWindow and related components.

Tests the layout structure, frame positioning, and basic functionality
of the main review interface.
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
    
    def bind(self, *args, **kwargs):
        pass
    
    def focus_set(self, *args, **kwargs):
        pass
    
    def cget(self, *args, **kwargs):
        return "normal"
    
    def after(self, *args, **kwargs):
        pass
    
    def winfo_toplevel(self, *args, **kwargs):
        return self

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

from vaitp_auditor.gui.main_review_window import (
    MainReviewWindow,
    HeaderFrame,
    CodePanelsFrame,
    ActionsFrame
)
from vaitp_auditor.gui.models import GUIConfig, ProgressInfo
from vaitp_auditor.core.models import CodePair


class TestHeaderFrame(unittest.TestCase):
    """Test cases for HeaderFrame component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_parent = Mock()
        self.header_frame = HeaderFrame(self.mock_parent)
    
    def test_header_frame_initialization(self):
        """Test HeaderFrame initializes with correct components."""
        # Verify frame was initialized with parent
        self.assertIsNotNone(self.header_frame)
        
        # Verify components exist
        self.assertTrue(hasattr(self.header_frame, 'current_file_label'))
        self.assertTrue(hasattr(self.header_frame, 'progress_bar'))
        self.assertTrue(hasattr(self.header_frame, 'progress_text_label'))
    
    def test_update_progress(self):
        """Test progress update functionality."""
        # Create mock progress info
        progress_info = ProgressInfo(
            current=5,
            total=10,
            current_file="test_file.py",
            experiment_name="test_experiment"
        )
        
        # Mock the label and progress bar methods
        self.header_frame.current_file_label = Mock()
        self.header_frame.progress_bar = Mock()
        self.header_frame.progress_text_label = Mock()
        
        # Update progress
        self.header_frame.update_progress(progress_info)
        
        # Verify methods were called with correct values
        self.header_frame.current_file_label.configure.assert_called_once()
        self.header_frame.progress_bar.set.assert_called_once_with(0.5)  # 5/10 = 0.5
        self.header_frame.progress_text_label.configure.assert_called_once()
        
        # Verify progress info is stored
        self.assertEqual(self.header_frame._current_progress, progress_info)
    
    def test_update_progress_validation(self):
        """Test progress update input validation."""
        # Test with invalid input
        with self.assertRaises(ValueError):
            self.header_frame.update_progress("invalid")
        
        with self.assertRaises(ValueError):
            self.header_frame.update_progress(None)
    
    def test_update_progress_boundary_values(self):
        """Test progress update with boundary values."""
        # Mock components
        self.header_frame.current_file_label = Mock()
        self.header_frame.progress_bar = Mock()
        self.header_frame.progress_text_label = Mock()
        
        # Test with 0% progress
        progress_info = ProgressInfo(
            current=0,
            total=10,
            current_file="start.py",
            experiment_name="test"
        )
        self.header_frame.update_progress(progress_info)
        self.header_frame.progress_bar.set.assert_called_with(0.0)
        
        # Test with 100% progress
        progress_info = ProgressInfo(
            current=10,
            total=10,
            current_file="end.py",
            experiment_name="test"
        )
        self.header_frame.update_progress(progress_info)
        self.header_frame.progress_bar.set.assert_called_with(1.0)
    
    def test_get_current_progress(self):
        """Test getting current progress information."""
        # Initially should be None
        self.assertIsNone(self.header_frame.get_current_progress())
        
        # Mock components for update
        self.header_frame.current_file_label = Mock()
        self.header_frame.progress_bar = Mock()
        self.header_frame.progress_text_label = Mock()
        
        # Set progress and verify retrieval
        progress_info = ProgressInfo(
            current=3,
            total=7,
            current_file="test.py",
            experiment_name="test"
        )
        self.header_frame.update_progress(progress_info)
        
        retrieved_progress = self.header_frame.get_current_progress()
        self.assertEqual(retrieved_progress, progress_info)
    
    def test_reset_progress(self):
        """Test resetting progress to initial state."""
        # Mock components
        self.header_frame.current_file_label = Mock()
        self.header_frame.progress_bar = Mock()
        self.header_frame.progress_text_label = Mock()
        
        # Set some progress first
        progress_info = ProgressInfo(
            current=5,
            total=10,
            current_file="test.py",
            experiment_name="test"
        )
        self.header_frame.update_progress(progress_info)
        
        # Reset progress
        self.header_frame.reset_progress()
        
        # Verify reset state
        self.assertIsNone(self.header_frame.get_current_progress())
        self.header_frame.current_file_label.configure.assert_called_with(text="No file loaded")
        self.header_frame.progress_bar.set.assert_called_with(0.0)
        self.header_frame.progress_text_label.configure.assert_called_with(text="0/0 (0.0%)")
    
    def test_set_loading_state(self):
        """Test setting loading state."""
        # Mock components
        self.header_frame.current_file_label = Mock()
        self.header_frame.progress_bar = Mock()
        self.header_frame.progress_text_label = Mock()
        
        # Test with default message
        self.header_frame.set_loading_state()
        
        self.header_frame.current_file_label.configure.assert_called_with(text="Loading...")
        self.header_frame.progress_bar.set.assert_called_with(0.0)
        self.header_frame.progress_text_label.configure.assert_called_with(text="Preparing...")
        
        # Test with custom message
        self.header_frame.set_loading_state("Custom loading message")
        self.header_frame.current_file_label.configure.assert_called_with(text="Custom loading message")
    
    def test_set_completion_state(self):
        """Test setting completion state."""
        # Mock components
        self.header_frame.current_file_label = Mock()
        self.header_frame.progress_bar = Mock()
        self.header_frame.progress_text_label = Mock()
        
        # Set completion state
        experiment_name = "test_experiment"
        self.header_frame.set_completion_state(experiment_name)
        
        # Verify completion state
        self.header_frame.current_file_label.configure.assert_called_with(
            text=f"Review Complete - {experiment_name}"
        )
        self.header_frame.progress_bar.set.assert_called_with(1.0)
        self.header_frame.progress_text_label.configure.assert_called_with(text="100% Complete")
    
    def test_set_static_progress(self):
        """Test static progress setting for placeholder state."""
        # Mock components
        self.header_frame.current_file_label = Mock()
        self.header_frame.progress_bar = Mock()
        self.header_frame.progress_text_label = Mock()
        
        # Set static progress
        test_text = "Test Progress"
        self.header_frame.set_static_progress(test_text)
        
        # Verify static values were set
        self.header_frame.current_file_label.configure.assert_called_with(text="Sample File")
        self.header_frame.progress_bar.set.assert_called_with(0.5)
        self.header_frame.progress_text_label.configure.assert_called_with(text=test_text)


class TestCodePanelsFrame(unittest.TestCase):
    """Test cases for CodePanelsFrame component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_parent = Mock()
        self.code_panels_frame = CodePanelsFrame(self.mock_parent)
    
    def test_code_panels_frame_initialization(self):
        """Test CodePanelsFrame initializes with correct components."""
        # Verify frame was initialized
        self.assertIsNotNone(self.code_panels_frame)
        
        # Verify components exist
        self.assertTrue(hasattr(self.code_panels_frame, 'expected_label'))
        self.assertTrue(hasattr(self.code_panels_frame, 'expected_textbox'))
        self.assertTrue(hasattr(self.code_panels_frame, 'generated_label'))
        self.assertTrue(hasattr(self.code_panels_frame, 'generated_textbox'))
    
    def test_load_code_pair(self):
        """Test loading code pair into panels."""
        # Mock textboxes
        self.code_panels_frame.expected_textbox = Mock()
        self.code_panels_frame.generated_textbox = Mock()
        
        # Create test code pair
        code_pair = CodePair(
            identifier="test_id",
            expected_code="def expected():\n    pass",
            generated_code="def generated():\n    return True",
            source_info={"file": "test.py"}
        )
        
        # Load code pair
        self.code_panels_frame.load_code_pair(code_pair)
        
        # Verify textboxes were cleared and populated
        self.code_panels_frame.expected_textbox.delete.assert_called()
        self.code_panels_frame.generated_textbox.delete.assert_called()
        self.code_panels_frame.expected_textbox.insert.assert_called()
        self.code_panels_frame.generated_textbox.insert.assert_called()
    
    def test_load_code_pair_with_none_values(self):
        """Test loading code pair with None values."""
        # Mock textboxes
        self.code_panels_frame.expected_textbox = Mock()
        self.code_panels_frame.generated_textbox = Mock()
        
        # Create code pair with None expected_code
        code_pair = CodePair(
            identifier="test_id",
            expected_code=None,
            generated_code="def test():\n    pass",
            source_info={"file": "test.py"}
        )
        
        # Load code pair
        self.code_panels_frame.load_code_pair(code_pair)
        
        # Verify fallback message was inserted for expected code
        expected_calls = self.code_panels_frame.expected_textbox.insert.call_args_list
        generated_calls = self.code_panels_frame.generated_textbox.insert.call_args_list
        
        # Check that fallback message was used for expected code
        self.assertTrue(any("No expected code available" in str(call) for call in expected_calls))
        # Check that actual generated code was inserted
        self.assertTrue(any("def test():" in str(call) for call in generated_calls))
    
    def test_clear_content(self):
        """Test clearing content from both panels."""
        # Mock textboxes
        self.code_panels_frame.expected_textbox = Mock()
        self.code_panels_frame.generated_textbox = Mock()
        
        # Clear content
        self.code_panels_frame.clear_content()
        
        # Verify both textboxes were cleared
        self.code_panels_frame.expected_textbox.delete.assert_called_with("1.0", "end")
        self.code_panels_frame.generated_textbox.delete.assert_called_with("1.0", "end")
    
    def test_set_placeholder_content(self):
        """Test setting placeholder content."""
        # Mock textboxes
        self.code_panels_frame.expected_textbox = Mock()
        self.code_panels_frame.generated_textbox = Mock()
        
        # Set placeholder content
        self.code_panels_frame.set_placeholder_content()
        
        # Verify placeholder text was inserted
        self.code_panels_frame.expected_textbox.insert.assert_called()
        self.code_panels_frame.generated_textbox.insert.assert_called()


class TestActionsFrame(unittest.TestCase):
    """Test cases for ActionsFrame component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_parent = Mock()
        self.verdict_callback = Mock()
        self.undo_callback = Mock()
        self.quit_callback = Mock()
        
        # Mock verdict button configs with full VerdictButtonConfig objects
        mock_config1 = Mock()
        mock_config1.verdict_id = "SUCCESS"
        mock_config1.display_text = "Success"
        mock_config1.key_binding = "s"
        mock_config1.color_theme = "success"
        mock_config1.tooltip = "Success tooltip"
        mock_config1.get_display_with_shortcut.return_value = "Success (s)"
        
        mock_config2 = Mock()
        mock_config2.verdict_id = "FAILURE"
        mock_config2.display_text = "Failure"
        mock_config2.key_binding = "f"
        mock_config2.color_theme = "error"
        mock_config2.tooltip = "Failure tooltip"
        mock_config2.get_display_with_shortcut.return_value = "Failure (f)"
        
        with patch('vaitp_auditor.gui.main_review_window.get_default_verdict_buttons') as mock_buttons:
            mock_buttons.return_value = [mock_config1, mock_config2]
            self.actions_frame = ActionsFrame(
                self.mock_parent,
                verdict_callback=self.verdict_callback,
                undo_callback=self.undo_callback,
                quit_callback=self.quit_callback
            )
    
    def test_actions_frame_initialization(self):
        """Test ActionsFrame initializes with correct components."""
        # Verify frame was initialized
        self.assertIsNotNone(self.actions_frame)
        
        # Verify components exist
        self.assertTrue(hasattr(self.actions_frame, 'verdict_frame'))
        self.assertTrue(hasattr(self.actions_frame, 'controls_frame'))
        self.assertTrue(hasattr(self.actions_frame, 'verdict_buttons'))
        self.assertTrue(hasattr(self.actions_frame, 'comment_entry'))
        self.assertTrue(hasattr(self.actions_frame, 'undo_button'))
        self.assertTrue(hasattr(self.actions_frame, 'quit_button'))
        
        # Verify callbacks are stored
        self.assertEqual(self.actions_frame.verdict_callback, self.verdict_callback)
        self.assertEqual(self.actions_frame.undo_callback, self.undo_callback)
        self.assertEqual(self.actions_frame.quit_callback, self.quit_callback)
        
        # Verify verdict configurations and key bindings are stored
        self.assertTrue(hasattr(self.actions_frame, 'verdict_configs'))
        self.assertTrue(hasattr(self.actions_frame, 'key_bindings'))
    
    def test_enhanced_verdict_button_creation(self):
        """Test enhanced verdict button creation with full configuration."""
        # Verify verdict buttons were created with configurations
        self.assertIn("SUCCESS", self.actions_frame.verdict_buttons)
        self.assertIn("FAILURE", self.actions_frame.verdict_buttons)
        
        # Verify configurations are stored
        self.assertIn("SUCCESS", self.actions_frame.verdict_configs)
        self.assertIn("FAILURE", self.actions_frame.verdict_configs)
        
        # Verify key bindings are set up
        self.assertIn("s", self.actions_frame.key_bindings)
        self.assertIn("f", self.actions_frame.key_bindings)
        self.assertEqual(self.actions_frame.key_bindings["s"], "SUCCESS")
        self.assertEqual(self.actions_frame.key_bindings["f"], "FAILURE")
    
    def test_get_button_colors(self):
        """Test button color scheme selection."""
        # Test success theme
        colors = self.actions_frame._get_button_colors("success")
        self.assertEqual(colors["fg_color"], "#2d8f47")
        self.assertEqual(colors["hover_color"], "#1e6b35")
        self.assertEqual(colors["text_color"], "white")
        
        # Test error theme
        colors = self.actions_frame._get_button_colors("error")
        self.assertEqual(colors["fg_color"], "#d32f2f")
        self.assertEqual(colors["hover_color"], "#b71c1c")
        self.assertEqual(colors["text_color"], "white")
        
        # Test warning theme
        colors = self.actions_frame._get_button_colors("warning")
        self.assertEqual(colors["fg_color"], "#f57c00")
        self.assertEqual(colors["hover_color"], "#e65100")
        self.assertEqual(colors["text_color"], "white")
        
        # Test info theme
        colors = self.actions_frame._get_button_colors("info")
        self.assertEqual(colors["fg_color"], "#1976d2")
        self.assertEqual(colors["hover_color"], "#0d47a1")
        self.assertEqual(colors["text_color"], "white")
        
        # Test primary theme
        colors = self.actions_frame._get_button_colors("primary")
        self.assertEqual(colors["fg_color"], "#6366f1")
        self.assertEqual(colors["hover_color"], "#4f46e5")
        self.assertEqual(colors["text_color"], "white")
        
        # Test default theme
        colors = self.actions_frame._get_button_colors("default")
        self.assertIsNone(colors["fg_color"])
        self.assertIsNone(colors["hover_color"])
        self.assertIsNone(colors["text_color"])
        
        # Test unknown theme (should return default)
        colors = self.actions_frame._get_button_colors("unknown")
        self.assertIsNone(colors["fg_color"])
    
    def test_add_tooltip(self):
        """Test tooltip addition to widgets."""
        mock_widget = Mock()
        tooltip_text = "Test tooltip"
        
        # Add tooltip
        self.actions_frame._add_tooltip(mock_widget, tooltip_text)
        
        # Verify tooltip text was stored as widget attribute
        self.assertEqual(mock_widget._tooltip_text, tooltip_text)
    
    def test_enhanced_comment_field(self):
        """Test enhanced comment field with proper clearing behavior."""
        # Mock comment entry
        self.actions_frame.comment_entry = Mock()
        
        # Test getting comment
        self.actions_frame.comment_entry.get.return_value = "test comment"
        comment = self.actions_frame.get_comment()
        self.assertEqual(comment, "test comment")
        
        # Test clearing comment with focus setting
        # Mock the comment entry to use set method (CustomTkinter behavior)
        self.actions_frame.clear_comment()
        self.actions_frame.comment_entry.set.assert_called_with("")
    
    def test_enhanced_control_buttons_styling(self):
        """Test enhanced control buttons with proper styling."""
        # Verify undo button has enhanced styling
        self.assertTrue(hasattr(self.actions_frame, 'undo_button'))
        
        # Verify quit button has enhanced styling
        self.assertTrue(hasattr(self.actions_frame, 'quit_button'))
    
    def test_verdict_button_callback(self):
        """Test verdict button callback functionality."""
        # Mock comment entry and validation
        self.actions_frame.get_validated_comment = Mock(return_value=("test comment", True, ""))
        
        # Mock set_verdict_buttons_enabled method
        self.actions_frame.set_verdict_buttons_enabled = Mock()
        
        mock_button = Mock()
        mock_button.cget.side_effect = lambda key: {
            "state": "normal",
            "fg_color": "#default",
            "hover_color": "#default"
        }.get(key, "mock_value")
        self.actions_frame.verdict_buttons = {"SUCCESS": mock_button}
        
        # Mock the after method for visual feedback
        self.actions_frame.after = Mock()
        
        # Mock clear_comment method
        self.actions_frame.clear_comment = Mock()
        
        # Trigger verdict click
        self.actions_frame._on_verdict_clicked("SUCCESS")
        
        # Verify callback was called with correct parameters
        self.verdict_callback.assert_called_once_with("SUCCESS", "test comment")
        
        # Verify buttons were disabled to prevent double-clicks
        self.actions_frame.set_verdict_buttons_enabled.assert_any_call(False)
        
        # Verify visual feedback was applied (color changes)
        mock_button.configure.assert_called()
        self.actions_frame.after.assert_called()
        
        # Verify comment was cleared
        self.actions_frame.clear_comment.assert_called_once()
    
    def test_undo_button_callback(self):
        """Test undo button callback functionality."""
        # Mock undo button
        self.actions_frame.undo_button = Mock()
        self.actions_frame.undo_button.cget.side_effect = lambda key: {
            "state": "normal",
            "fg_color": "#default",
            "hover_color": "#default"
        }.get(key, "mock_value")
        
        # Mock set_verdict_buttons_enabled method
        self.actions_frame.set_verdict_buttons_enabled = Mock()
        
        # Mock the after method for visual feedback
        self.actions_frame.after = Mock()
        
        # Trigger undo click
        self.actions_frame._on_undo_clicked()
        
        # Verify callback was called
        self.undo_callback.assert_called_once()
        
        # Verify buttons were disabled during processing
        self.actions_frame.set_verdict_buttons_enabled.assert_any_call(False)
        
        # Verify visual feedback was applied (button disabled and color changes)
        self.actions_frame.undo_button.configure.assert_called()
        self.actions_frame.after.assert_called()
    
    def test_quit_button_callback(self):
        """Test quit button callback functionality."""
        # Mock quit button
        self.actions_frame.quit_button = Mock()
        self.actions_frame.quit_button.cget.side_effect = lambda key: {
            "state": "normal",
            "fg_color": "#default",
            "hover_color": "#default"
        }.get(key, "mock_value")
        
        # Mock the after method for visual feedback
        self.actions_frame.after = Mock()
        
        # Trigger quit click
        self.actions_frame._on_quit_clicked()
        
        # Verify callback was called
        self.quit_callback.assert_called_once()
        
        # Verify visual feedback was applied (button disabled and color changes)
        self.actions_frame.quit_button.configure.assert_called()
        self.actions_frame.after.assert_called()
    
    def test_keyboard_shortcuts(self):
        """Test keyboard shortcut functionality."""
        # Mock buttons and comment entry
        mock_success_button = Mock()
        mock_success_button.cget.return_value = "normal"
        mock_failure_button = Mock()
        mock_failure_button.cget.return_value = "normal"
        
        self.actions_frame.verdict_buttons = {
            "SUCCESS": mock_success_button,
            "FAILURE": mock_failure_button
        }
        self.actions_frame.comment_entry = Mock()
        self.actions_frame.comment_entry.get.return_value = ""
        self.actions_frame.after = Mock()
        
        # Test verdict key shortcuts
        result = self.actions_frame.simulate_key_press("s")
        self.assertTrue(result)
        self.verdict_callback.assert_called_with("SUCCESS", "")
        
        result = self.actions_frame.simulate_key_press("f")
        self.assertTrue(result)
        self.verdict_callback.assert_called_with("FAILURE", "")
        
        # Test control key shortcuts
        self.actions_frame.undo_button = Mock()
        self.actions_frame.undo_button.cget.return_value = "normal"
        self.actions_frame.quit_button = Mock()
        self.actions_frame.quit_button.cget.return_value = "normal"
        
        result = self.actions_frame.simulate_key_press("u")
        self.assertTrue(result)
        self.undo_callback.assert_called()
        
        result = self.actions_frame.simulate_key_press("q")
        self.assertTrue(result)
        self.quit_callback.assert_called()
        
        # Test invalid key
        result = self.actions_frame.simulate_key_press("x")
        self.assertFalse(result)
    
    def test_button_state_management(self):
        """Test button state management functionality."""
        # Mock buttons
        mock_verdict_button = Mock()
        mock_undo_button = Mock()
        mock_quit_button = Mock()
        
        self.actions_frame.verdict_buttons = {"SUCCESS": mock_verdict_button}
        self.actions_frame.undo_button = mock_undo_button
        self.actions_frame.quit_button = mock_quit_button
        
        # Test enabling all buttons
        self.actions_frame.set_buttons_enabled(True)
        mock_verdict_button.configure.assert_called_with(state="normal")
        mock_undo_button.configure.assert_called_with(state="normal")
        mock_quit_button.configure.assert_called_with(state="normal")
        
        # Test disabling all buttons
        self.actions_frame.set_buttons_enabled(False)
        mock_verdict_button.configure.assert_called_with(state="disabled")
        mock_undo_button.configure.assert_called_with(state="disabled")
        mock_quit_button.configure.assert_called_with(state="disabled")
        
        # Test enabling only verdict buttons
        self.actions_frame.set_verdict_buttons_enabled(True)
        mock_verdict_button.configure.assert_called_with(state="normal")
        
        # Test disabling only verdict buttons
        self.actions_frame.set_verdict_buttons_enabled(False)
        mock_verdict_button.configure.assert_called_with(state="disabled")
        
        # Test undo button state management
        self.actions_frame.set_undo_enabled(True)
        mock_undo_button.configure.assert_called_with(state="normal")
        
        self.actions_frame.set_undo_enabled(False)
        mock_undo_button.configure.assert_called_with(state="disabled")
    
    def test_get_verdict_config(self):
        """Test getting verdict configuration."""
        # Test getting existing config
        config = self.actions_frame.get_verdict_config("SUCCESS")
        self.assertIsNotNone(config)
        
        # Test getting non-existent config
        config = self.actions_frame.get_verdict_config("NONEXISTENT")
        self.assertIsNone(config)
    
    def test_accessibility_features(self):
        """Test accessibility features."""
        # Verify keyboard shortcuts are set up
        self.assertTrue(hasattr(self.actions_frame, 'key_bindings'))
        self.assertGreater(len(self.actions_frame.key_bindings), 0)
        
        # Verify tooltips can be added
        mock_widget = Mock()
        self.actions_frame._add_tooltip(mock_widget, "Test accessibility tooltip")
        self.assertEqual(mock_widget._tooltip_text, "Test accessibility tooltip")
    
    def test_disabled_button_keyboard_handling(self):
        """Test that disabled buttons don't respond to keyboard shortcuts."""
        # Mock disabled button
        mock_button = Mock()
        mock_button.cget.return_value = "disabled"
        self.actions_frame.verdict_buttons = {"SUCCESS": mock_button}
        
        # Try to trigger disabled button via keyboard
        result = self.actions_frame.simulate_key_press("s")
        self.assertFalse(result)
        
        # Verify callback was not called
        self.verdict_callback.assert_not_called()


class TestMainReviewWindow(unittest.TestCase):
    """Test cases for MainReviewWindow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.verdict_callback = Mock()
        self.undo_callback = Mock()
        self.quit_callback = Mock()
        
        with patch('vaitp_auditor.gui.main_review_window.get_default_verdict_buttons') as mock_buttons, \
             patch.object(MainReviewWindow, 'setup_menu'):
            mock_buttons.return_value = []
            self.main_window = MainReviewWindow(
                verdict_callback=self.verdict_callback,
                undo_callback=self.undo_callback,
                quit_callback=self.quit_callback
            )
    
    def test_main_review_window_initialization(self):
        """Test MainReviewWindow initializes correctly."""
        # Verify window was initialized
        self.assertIsNotNone(self.main_window)
        
        # Verify configuration
        self.assertIsInstance(self.main_window.gui_config, GUIConfig)
        
        # Verify callbacks are stored
        self.assertEqual(self.main_window.verdict_callback, self.verdict_callback)
        self.assertEqual(self.main_window.undo_callback, self.undo_callback)
        self.assertEqual(self.main_window.quit_callback, self.quit_callback)
        
        # Verify frames were created
        self.assertTrue(hasattr(self.main_window, 'header_frame'))
        self.assertTrue(hasattr(self.main_window, 'code_panels_frame'))
        self.assertTrue(hasattr(self.main_window, 'actions_frame'))
    
    def test_main_review_window_with_custom_config(self):
        """Test MainReviewWindow with custom configuration."""
        custom_config = GUIConfig(window_width=1200, window_height=900)
        
        with patch('vaitp_auditor.gui.main_review_window.get_default_verdict_buttons') as mock_buttons, \
             patch.object(MainReviewWindow, 'setup_menu'):
            mock_buttons.return_value = []
            window = MainReviewWindow(custom_config)
        
        # Verify custom config was used
        self.assertEqual(window.gui_config.window_width, 1200)
        self.assertEqual(window.gui_config.window_height, 900)
    
    def test_load_code_pair(self):
        """Test loading code pair into window."""
        # Mock frames
        self.main_window.code_panels_frame = Mock()
        self.main_window.actions_frame = Mock()
        
        # Create test code pair
        code_pair = CodePair(
            identifier="test_id",
            expected_code="test expected",
            generated_code="test generated",
            source_info={"file": "test.py"}
        )
        
        # Load code pair
        self.main_window.load_code_pair(code_pair)
        
        # Verify code was loaded and buttons enabled
        self.main_window.code_panels_frame.load_code_pair.assert_called_once_with(code_pair)
        self.main_window.actions_frame.set_buttons_enabled.assert_called_once_with(True)
    
    def test_update_progress(self):
        """Test updating progress display."""
        # Mock header frame
        self.main_window.header_frame = Mock()
        
        # Create test progress info
        progress_info = ProgressInfo(
            current=3,
            total=10,
            current_file="test.py",
            experiment_name="test_experiment"
        )
        
        # Update progress
        self.main_window.update_progress(progress_info)
        
        # Verify progress was updated
        self.main_window.header_frame.update_progress.assert_called_once_with(progress_info)
    
    def test_update_progress_validation(self):
        """Test progress update input validation."""
        # Test with invalid input
        with self.assertRaises(ValueError):
            self.main_window.update_progress("invalid")
        
        with self.assertRaises(ValueError):
            self.main_window.update_progress(None)
    
    def test_get_current_progress(self):
        """Test getting current progress from header frame."""
        # Mock header frame
        self.main_window.header_frame = Mock()
        mock_progress = Mock()
        self.main_window.header_frame.get_current_progress.return_value = mock_progress
        
        # Get current progress
        result = self.main_window.get_current_progress()
        
        # Verify delegation to header frame
        self.main_window.header_frame.get_current_progress.assert_called_once()
        self.assertEqual(result, mock_progress)
    
    def test_set_loading_state(self):
        """Test setting loading state."""
        # Mock components
        self.main_window.header_frame = Mock()
        self.main_window.actions_frame = Mock()
        
        # Test with default message
        self.main_window.set_loading_state()
        
        # Verify loading state was set
        self.main_window.header_frame.set_loading_state.assert_called_once_with("Loading session...")
        self.main_window.actions_frame.set_buttons_enabled.assert_called_once_with(False)
        
        # Test with custom message
        custom_message = "Custom loading message"
        self.main_window.set_loading_state(custom_message)
        self.main_window.header_frame.set_loading_state.assert_called_with(custom_message)
    
    def test_set_completion_state(self):
        """Test setting completion state."""
        # Mock components
        self.main_window.header_frame = Mock()
        self.main_window.actions_frame = Mock()
        mock_verdict_button = Mock()
        self.main_window.actions_frame.verdict_buttons = {"SUCCESS": mock_verdict_button}
        
        # Set completion state
        experiment_name = "test_experiment"
        self.main_window.set_completion_state(experiment_name)
        
        # Verify completion state was set
        self.main_window.header_frame.set_completion_state.assert_called_once_with(experiment_name)
        mock_verdict_button.configure.assert_called_once_with(state="disabled")
    
    def test_clear_content(self):
        """Test clearing all content."""
        # Mock frames
        self.main_window.code_panels_frame = Mock()
        self.main_window.actions_frame = Mock()
        self.main_window.header_frame = Mock()
        
        # Clear content
        self.main_window.clear_content()
        
        # Verify all components were cleared
        self.main_window.code_panels_frame.clear_content.assert_called_once()
        self.main_window.actions_frame.clear_comment.assert_called_once()
        self.main_window.header_frame.reset_progress.assert_called_once()
        self.main_window.actions_frame.set_buttons_enabled.assert_called_once_with(False)
    
    def test_get_comment(self):
        """Test getting comment from actions frame."""
        # Mock actions frame
        self.main_window.actions_frame = Mock()
        self.main_window.actions_frame.get_comment.return_value = "test comment"
        
        # Get comment
        comment = self.main_window.get_comment()
        
        # Verify comment was retrieved
        self.assertEqual(comment, "test comment")
        self.main_window.actions_frame.get_comment.assert_called_once()
    
    def test_clear_comment(self):
        """Test clearing comment field."""
        # Mock actions frame
        self.main_window.actions_frame = Mock()
        
        # Clear comment
        self.main_window.clear_comment()
        
        # Verify comment was cleared
        self.main_window.actions_frame.clear_comment.assert_called_once()
    
    def test_enhanced_button_state_management(self):
        """Test enhanced button state management methods."""
        # Mock actions frame
        self.main_window.actions_frame = Mock()
        
        # Test verdict buttons state management
        self.main_window.set_verdict_buttons_enabled(True)
        self.main_window.actions_frame.set_verdict_buttons_enabled.assert_called_once_with(True)
        
        self.main_window.set_verdict_buttons_enabled(False)
        self.main_window.actions_frame.set_verdict_buttons_enabled.assert_called_with(False)
        
        # Test undo button state management
        self.main_window.set_undo_enabled(True)
        self.main_window.actions_frame.set_undo_enabled.assert_called_once_with(True)
        
        self.main_window.set_undo_enabled(False)
        self.main_window.actions_frame.set_undo_enabled.assert_called_with(False)
    
    def test_keyboard_shortcut_simulation(self):
        """Test keyboard shortcut simulation."""
        # Mock actions frame
        self.main_window.actions_frame = Mock()
        self.main_window.actions_frame.simulate_key_press.return_value = True
        
        # Test key press simulation
        result = self.main_window.simulate_key_press("s")
        
        # Verify delegation to actions frame
        self.main_window.actions_frame.simulate_key_press.assert_called_once_with("s")
        self.assertTrue(result)
    
    def test_get_verdict_config(self):
        """Test getting verdict configuration."""
        # Mock actions frame
        self.main_window.actions_frame = Mock()
        mock_config = Mock()
        self.main_window.actions_frame.get_verdict_config.return_value = mock_config
        
        # Get verdict config
        result = self.main_window.get_verdict_config("SUCCESS")
        
        # Verify delegation to actions frame
        self.main_window.actions_frame.get_verdict_config.assert_called_once_with("SUCCESS")
        self.assertEqual(result, mock_config)
    
    def test_callback_integration(self):
        """Test that callbacks are properly passed to actions frame."""
        # Verify that the actions frame was created with the correct callbacks
        self.assertEqual(self.main_window.actions_frame.verdict_callback, self.verdict_callback)
        self.assertEqual(self.main_window.actions_frame.undo_callback, self.undo_callback)
        self.assertEqual(self.main_window.actions_frame.quit_callback, self.quit_callback)
    
    def test_menu_functionality(self):
        """Test that menu methods exist."""
        # Test setup_menu method exists
        self.assertTrue(hasattr(self.main_window, 'setup_menu'))
        self.assertTrue(callable(getattr(self.main_window, 'setup_menu')))
        
        # Test show_about_dialog method exists
        self.assertTrue(hasattr(self.main_window, 'show_about_dialog'))
        self.assertTrue(callable(getattr(self.main_window, 'show_about_dialog')))
        
        # Test File menu methods exist
        self.assertTrue(hasattr(self.main_window, 'save_review_process'))
        self.assertTrue(callable(getattr(self.main_window, 'save_review_process')))
        
        self.assertTrue(hasattr(self.main_window, 'open_review_process'))
        self.assertTrue(callable(getattr(self.main_window, 'open_review_process')))
        
        self.assertTrue(hasattr(self.main_window, 'restart_review_process'))
        self.assertTrue(callable(getattr(self.main_window, 'restart_review_process')))
        
        self.assertTrue(hasattr(self.main_window, 'quit_application'))
        self.assertTrue(callable(getattr(self.main_window, 'quit_application')))
    
    @patch('vaitp_auditor.gui.about_dialog.show_about_dialog')
    def test_about_dialog_integration(self, mock_show_about):
        """Test About dialog integration."""
        # Call show_about_dialog method
        self.main_window.show_about_dialog()
        
        # Verify about dialog was called with correct parent
        mock_show_about.assert_called_once_with(self.main_window)
    
    def test_file_menu_callbacks(self):
        """Test File menu callback functionality."""
        # Create mock callbacks
        save_callback = Mock()
        open_callback = Mock()
        restart_callback = Mock()
        
        # Create window with callbacks
        with patch('vaitp_auditor.gui.main_review_window.get_default_verdict_buttons') as mock_buttons, \
             patch.object(MainReviewWindow, 'setup_menu'):
            mock_buttons.return_value = []
            window = MainReviewWindow(
                save_callback=save_callback,
                open_callback=open_callback,
                restart_callback=restart_callback
            )
        
        # Test save callback
        window.save_review_process()
        save_callback.assert_called_once()
        
        # Test open callback
        window.open_review_process()
        open_callback.assert_called_once()
        
        # Test restart callback
        window.restart_review_process()
        restart_callback.assert_called_once()
    
    @patch('tkinter.messagebox.showwarning')
    def test_file_menu_without_callbacks(self, mock_warning):
        """Test File menu methods when no callbacks are provided."""
        # Test save without callback
        self.main_window.save_review_process()
        mock_warning.assert_called()
        
        # Reset mock
        mock_warning.reset_mock()
        
        # Test open without callback
        self.main_window.open_review_process()
        mock_warning.assert_called()
        
        # Reset mock
        mock_warning.reset_mock()
        
        # Test restart without callback
        self.main_window.restart_review_process()
        mock_warning.assert_called()


class TestMainReviewWindowIntegration(unittest.TestCase):
    """Integration tests for MainReviewWindow layout and positioning."""
    
    def test_layout_structure_integration(self):
        """Test that the three-row layout structure is properly configured."""
        with patch('vaitp_auditor.gui.main_review_window.get_default_verdict_buttons') as mock_buttons, \
             patch.object(MainReviewWindow, 'setup_menu'):
            mock_buttons.return_value = []
            
            window = MainReviewWindow()
            
            # Verify window has the required frames
            self.assertTrue(hasattr(window, 'header_frame'))
            self.assertTrue(hasattr(window, 'code_panels_frame'))
            self.assertTrue(hasattr(window, 'actions_frame'))
            
            # Verify frames are of correct types
            self.assertIsInstance(window.header_frame, HeaderFrame)
            self.assertIsInstance(window.code_panels_frame, CodePanelsFrame)
            self.assertIsInstance(window.actions_frame, ActionsFrame)


if __name__ == '__main__':
    unittest.main()