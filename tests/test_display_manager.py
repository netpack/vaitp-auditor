"""
Unit tests for DisplayManager class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console

from vaitp_auditor.ui.display_manager import DisplayManager


class TestDisplayManager:
    """Test cases for DisplayManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.display_manager = DisplayManager()

    def test_init(self):
        """Test DisplayManager initialization."""
        assert isinstance(self.display_manager.console, Console)
        assert self.display_manager.layout is not None
        
        # Check layout structure by trying to access them
        try:
            header = self.display_manager.layout["header"]
            main = self.display_manager.layout["main"]
            footer = self.display_manager.layout["footer"]
            expected = self.display_manager.layout["main"]["expected"]
            generated = self.display_manager.layout["main"]["generated"]
            # If we get here without exceptions, the layout is properly structured
            assert True
        except KeyError as e:
            pytest.fail(f"Layout structure is incorrect: {e}")

    @patch('vaitp_auditor.ui.display_manager.Console')
    def test_clear_screen(self, mock_console_class):
        """Test screen clearing functionality."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        display_manager = DisplayManager()
        display_manager.clear_screen()
        
        mock_console.clear.assert_called_once()

    @patch('vaitp_auditor.ui.display_manager.Console')
    def test_show_message(self, mock_console_class):
        """Test message display functionality."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        display_manager = DisplayManager()
        display_manager.show_message("Test message", "blue")
        
        mock_console.print.assert_called_once_with("Test message", style="blue")

    @patch('vaitp_auditor.ui.display_manager.Console')
    def test_show_message_default_style(self, mock_console_class):
        """Test message display with default style."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        display_manager = DisplayManager()
        display_manager.show_message("Test message")
        
        mock_console.print.assert_called_once_with("Test message", style="white")

    @patch('vaitp_auditor.ui.display_manager.Console')
    def test_show_error(self, mock_console_class):
        """Test error message display."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        display_manager = DisplayManager()
        display_manager.show_error("Test error")
        
        mock_console.print.assert_called_once_with("[bold red]Error:[/bold red] Test error")

    @patch('vaitp_auditor.ui.display_manager.Console')
    def test_show_success(self, mock_console_class):
        """Test success message display."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        display_manager = DisplayManager()
        display_manager.show_success("Test success")
        
        mock_console.print.assert_called_once_with("[bold green]Success:[/bold green] Test success")

    @patch('vaitp_auditor.ui.display_manager.Console')
    def test_show_warning(self, mock_console_class):
        """Test warning message display."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        display_manager = DisplayManager()
        display_manager.show_warning("Test warning")
        
        mock_console.print.assert_called_once_with("[bold yellow]Warning:[/bold yellow] Test warning")

    @patch('vaitp_auditor.ui.display_manager.Console')
    def test_prompt_user(self, mock_console_class):
        """Test user prompt functionality."""
        mock_console = Mock()
        mock_console.input.return_value = "user input"
        mock_console_class.return_value = mock_console
        
        display_manager = DisplayManager()
        result = display_manager.prompt_user("Enter something")
        
        assert result == "user input"
        mock_console.input.assert_called_once_with("[bold cyan]Enter something[/bold cyan] ")

    @patch('vaitp_auditor.ui.display_manager.Console')
    def test_get_terminal_size(self, mock_console_class):
        """Test terminal size retrieval."""
        mock_console = Mock()
        mock_console.size = (80, 24)
        mock_console_class.return_value = mock_console
        
        display_manager = DisplayManager()
        width, height = display_manager.get_terminal_size()
        
        assert width == 80
        assert height == 24

    @patch('vaitp_auditor.ui.display_manager.Console')
    def test_render_code_panels_with_expected(self, mock_console_class):
        """Test rendering code panels with expected code."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        display_manager = DisplayManager()
        
        expected_code = "def expected_function():\n    return True"
        generated_code = "def generated_function():\n    return False"
        progress_info = {"current": 5, "total": 10, "percentage": 50.0}
        
        display_manager.render_code_panels(
            expected_code, 
            generated_code, 
            progress_info,
            "test_identifier"
        )
        
        # Verify console methods were called
        mock_console.clear.assert_called_once()
        mock_console.print.assert_called_once()

    @patch('vaitp_auditor.ui.display_manager.Console')
    def test_render_code_panels_without_expected(self, mock_console_class):
        """Test rendering code panels without expected code."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        display_manager = DisplayManager()
        
        generated_code = "def generated_function():\n    return False"
        progress_info = {"current": 3, "total": 8, "percentage": 37.5}
        
        display_manager.render_code_panels(
            None, 
            generated_code, 
            progress_info,
            "test_identifier_2"
        )
        
        # Verify console methods were called
        mock_console.clear.assert_called_once()
        mock_console.print.assert_called_once()

    @patch('vaitp_auditor.ui.display_manager.Console')
    def test_render_code_panels_empty_progress(self, mock_console_class):
        """Test rendering with empty progress info."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        display_manager = DisplayManager()
        
        generated_code = "print('hello')"
        progress_info = {}
        
        display_manager.render_code_panels(
            None, 
            generated_code, 
            progress_info
        )
        
        # Should handle missing progress info gracefully
        mock_console.clear.assert_called_once()
        mock_console.print.assert_called_once()

    def test_render_code_panels_syntax_highlighting(self):
        """Test that syntax highlighting is properly configured."""
        expected_code = "def test():\n    x = 1\n    return x"
        generated_code = "def test():\n    y = 2\n    return y"
        progress_info = {"current": 1, "total": 1, "percentage": 100.0}
        
        # This should not raise any exceptions
        self.display_manager.render_code_panels(
            expected_code,
            generated_code,
            progress_info,
            "syntax_test"
        )

    def test_render_code_panels_long_code(self):
        """Test rendering with long code content."""
        long_code = "\n".join([f"line_{i} = {i}" for i in range(100)])
        progress_info = {"current": 1, "total": 1, "percentage": 100.0}
        
        # This should handle long content without issues
        self.display_manager.render_code_panels(
            long_code,
            long_code,
            progress_info,
            "long_code_test"
        )

    def test_render_code_panels_special_characters(self):
        """Test rendering with special characters and unicode."""
        special_code = "# Special chars: àáâãäå ñ ç\ndef test():\n    return 'unicode: 🐍'"
        progress_info = {"current": 1, "total": 1, "percentage": 100.0}
        
        # This should handle special characters gracefully
        self.display_manager.render_code_panels(
            special_code,
            special_code,
            progress_info,
            "special_chars_test"
        )

    @patch('vaitp_auditor.ui.display_manager.Console')
    def test_layout_structure_integrity(self, mock_console_class):
        """Test that layout structure remains intact after operations."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        display_manager = DisplayManager()
        
        # Perform multiple operations
        display_manager.show_message("test")
        display_manager.clear_screen()
        display_manager.render_code_panels(
            "test", "test", {"current": 1, "total": 1, "percentage": 100.0}
        )
        
        # Layout should still be properly structured
        try:
            header = display_manager.layout["header"]
            main = display_manager.layout["main"]
            footer = display_manager.layout["footer"]
            expected = display_manager.layout["main"]["expected"]
            generated = display_manager.layout["main"]["generated"]
            # If we get here without exceptions, the layout is properly structured
            assert True
        except KeyError as e:
            pytest.fail(f"Layout structure is incorrect: {e}")