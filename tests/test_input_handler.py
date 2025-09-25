"""
Unit tests for InputHandler class.
"""

import pytest
from unittest.mock import Mock, patch, call
from rich.console import Console

from vaitp_auditor.ui.input_handler import InputHandler


class TestInputHandler:
    """Test cases for InputHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.input_handler = InputHandler()

    def test_init_default_console(self):
        """Test InputHandler initialization with default console."""
        handler = InputHandler()
        assert isinstance(handler.console, Console)
        assert len(handler.valid_verdicts) == 7

    def test_init_custom_console(self):
        """Test InputHandler initialization with custom console."""
        custom_console = Mock(spec=Console)
        handler = InputHandler(custom_console)
        assert handler.console is custom_console

    def test_valid_verdicts_structure(self):
        """Test that valid verdicts are properly structured."""
        expected_verdicts = {
            's': 'Success',
            'f': 'Failure - No Change', 
            'i': 'Invalid Code',
            'w': 'Wrong Vulnerability',
            'p': 'Partial Success',
            'u': 'Undo',
            'q': 'Quit'
        }
        assert self.input_handler.valid_verdicts == expected_verdicts

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_confirmation_yes(self, mock_console_class):
        """Test get_confirmation with yes response."""
        mock_console = Mock()
        mock_console.input.return_value = 'y'
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        result = handler.get_confirmation("Test message")
        
        assert result is True
        mock_console.input.assert_called_once_with("[bold yellow]Test message (y/n): [/bold yellow]")

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_confirmation_no(self, mock_console_class):
        """Test get_confirmation with no response."""
        mock_console = Mock()
        mock_console.input.return_value = 'n'
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        result = handler.get_confirmation("Test message")
        
        assert result is False

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_confirmation_yes_full_word(self, mock_console_class):
        """Test get_confirmation with 'yes' response."""
        mock_console = Mock()
        mock_console.input.return_value = 'yes'
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        result = handler.get_confirmation("Test message")
        
        assert result is True

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_confirmation_no_full_word(self, mock_console_class):
        """Test get_confirmation with 'no' response."""
        mock_console = Mock()
        mock_console.input.return_value = 'no'
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        result = handler.get_confirmation("Test message")
        
        assert result is False

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_confirmation_invalid_then_yes(self, mock_console_class):
        """Test get_confirmation with invalid input then yes."""
        mock_console = Mock()
        mock_console.input.side_effect = ['invalid', 'y']
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        result = handler.get_confirmation("Test message")
        
        assert result is True
        assert mock_console.input.call_count == 2
        mock_console.print.assert_called_with("[red]Please enter 'y' for yes or 'n' for no.[/red]")

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_confirmation_keyboard_interrupt(self, mock_console_class):
        """Test get_confirmation with KeyboardInterrupt."""
        mock_console = Mock()
        mock_console.input.side_effect = KeyboardInterrupt()
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        result = handler.get_confirmation("Test message")
        
        assert result is False

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_confirmation_eof_error(self, mock_console_class):
        """Test get_confirmation with EOFError."""
        mock_console = Mock()
        mock_console.input.side_effect = EOFError()
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        result = handler.get_confirmation("Test message")
        
        assert result is False

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_display_help(self, mock_console_class):
        """Test display_help functionality."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        handler.display_help()
        
        mock_console.print.assert_called_once()

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_user_verdict_success(self, mock_console_class):
        """Test get_user_verdict with success selection."""
        mock_console = Mock()
        mock_console.input.side_effect = ['s', 'y', 'Great success!']
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        verdict, comment = handler.get_user_verdict()
        
        assert verdict == 'Success'
        assert comment == 'Great success!'

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_user_verdict_quit(self, mock_console_class):
        """Test get_user_verdict with quit selection."""
        mock_console = Mock()
        mock_console.input.return_value = 'q'
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        verdict, comment = handler.get_user_verdict()
        
        assert verdict == 'Quit'
        assert comment == ''

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_user_verdict_invalid_then_valid(self, mock_console_class):
        """Test get_user_verdict with invalid input then valid."""
        mock_console = Mock()
        mock_console.input.side_effect = ['x', 'f', 'y', 'No changes made']
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        verdict, comment = handler.get_user_verdict()
        
        assert verdict == 'Failure - No Change'
        assert comment == 'No changes made'

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_user_verdict_help_then_selection(self, mock_console_class):
        """Test get_user_verdict with help request then selection."""
        mock_console = Mock()
        mock_console.input.side_effect = ['h', 'i', 'y', 'Invalid syntax']
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        verdict, comment = handler.get_user_verdict()
        
        assert verdict == 'Invalid Code'
        assert comment == 'Invalid syntax'

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_user_verdict_confirmation_no_then_yes(self, mock_console_class):
        """Test get_user_verdict with confirmation no then yes."""
        mock_console = Mock()
        mock_console.input.side_effect = ['w', 'n', 'w', 'y', 'Wrong vulnerability type']
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        verdict, comment = handler.get_user_verdict()
        
        assert verdict == 'Wrong Vulnerability'
        assert comment == 'Wrong vulnerability type'

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_user_verdict_empty_input(self, mock_console_class):
        """Test get_user_verdict with empty input."""
        mock_console = Mock()
        mock_console.input.side_effect = ['', 'p', 'y', 'Partially correct']
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        verdict, comment = handler.get_user_verdict()
        
        assert verdict == 'Partial Success'
        assert comment == 'Partially correct'

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_user_verdict_keyboard_interrupt(self, mock_console_class):
        """Test get_user_verdict with KeyboardInterrupt."""
        mock_console = Mock()
        mock_console.input.side_effect = [KeyboardInterrupt(), 's', 'y', '']
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        verdict, comment = handler.get_user_verdict()
        
        assert verdict == 'Success'
        assert comment == ''

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_user_verdict_eof_error(self, mock_console_class):
        """Test get_user_verdict with EOFError."""
        mock_console = Mock()
        mock_console.input.side_effect = EOFError()
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        verdict, comment = handler.get_user_verdict()
        
        assert verdict == 'Quit'
        assert comment == ''

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_comment_with_input(self, mock_console_class):
        """Test _get_comment with user input."""
        mock_console = Mock()
        mock_console.input.return_value = 'Test comment'
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        comment = handler._get_comment()
        
        assert comment == 'Test comment'

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_comment_empty(self, mock_console_class):
        """Test _get_comment with empty input."""
        mock_console = Mock()
        mock_console.input.return_value = ''
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        comment = handler._get_comment()
        
        assert comment == ''

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_comment_keyboard_interrupt(self, mock_console_class):
        """Test _get_comment with KeyboardInterrupt."""
        mock_console = Mock()
        mock_console.input.side_effect = KeyboardInterrupt()
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        comment = handler._get_comment()
        
        assert comment == ''

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_get_undo_confirmation(self, mock_console_class):
        """Test get_undo_confirmation."""
        mock_console = Mock()
        mock_console.input.return_value = 'y'
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        result = handler.get_undo_confirmation()
        
        assert result is True

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_prompt_for_input_with_default(self, mock_console_class):
        """Test prompt_for_input with default value."""
        mock_console = Mock()
        mock_console.input.return_value = ''
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        result = handler.prompt_for_input("Enter value", "default_value")
        
        assert result == 'default_value'

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_prompt_for_input_with_user_input(self, mock_console_class):
        """Test prompt_for_input with user input."""
        mock_console = Mock()
        mock_console.input.return_value = 'user_input'
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        result = handler.prompt_for_input("Enter value", "default_value")
        
        assert result == 'user_input'

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_prompt_for_input_no_default(self, mock_console_class):
        """Test prompt_for_input without default value."""
        mock_console = Mock()
        mock_console.input.return_value = 'user_input'
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        result = handler.prompt_for_input("Enter value")
        
        assert result == 'user_input'

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_show_error_message(self, mock_console_class):
        """Test show_error_message."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        handler.show_error_message("Test error")
        
        mock_console.print.assert_called_once_with("[bold red]Error:[/bold red] Test error")

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_show_info_message(self, mock_console_class):
        """Test show_info_message."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        handler.show_info_message("Test info")
        
        mock_console.print.assert_called_once_with("[bold blue]Info:[/bold blue] Test info")

    @patch('vaitp_auditor.ui.input_handler.Console')
    def test_show_success_message(self, mock_console_class):
        """Test show_success_message."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        handler = InputHandler()
        handler.show_success_message("Test success")
        
        mock_console.print.assert_called_once_with("[bold green]Success:[/bold green] Test success")

    def test_validate_verdict_valid(self):
        """Test validate_verdict with valid verdicts."""
        assert self.input_handler.validate_verdict('Success') is True
        assert self.input_handler.validate_verdict('Failure - No Change') is True
        assert self.input_handler.validate_verdict('Invalid Code') is True
        assert self.input_handler.validate_verdict('Wrong Vulnerability') is True
        assert self.input_handler.validate_verdict('Partial Success') is True
        assert self.input_handler.validate_verdict('Quit') is True

    def test_validate_verdict_invalid(self):
        """Test validate_verdict with invalid verdicts."""
        assert self.input_handler.validate_verdict('Invalid Verdict') is False
        assert self.input_handler.validate_verdict('') is False
        assert self.input_handler.validate_verdict('success') is False  # case sensitive

    def test_get_verdict_key_valid(self):
        """Test get_verdict_key with valid verdicts."""
        assert self.input_handler.get_verdict_key('Success') == 's'
        assert self.input_handler.get_verdict_key('Failure - No Change') == 'f'
        assert self.input_handler.get_verdict_key('Invalid Code') == 'i'
        assert self.input_handler.get_verdict_key('Wrong Vulnerability') == 'w'
        assert self.input_handler.get_verdict_key('Partial Success') == 'p'
        assert self.input_handler.get_verdict_key('Quit') == 'q'

    def test_get_verdict_key_invalid(self):
        """Test get_verdict_key with invalid verdicts."""
        assert self.input_handler.get_verdict_key('Invalid Verdict') is None
        assert self.input_handler.get_verdict_key('') is None
        assert self.input_handler.get_verdict_key('success') is None  # case sensitive