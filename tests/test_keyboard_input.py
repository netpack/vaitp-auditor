"""
Unit tests for KeyboardInput class.
"""

import pytest
from unittest.mock import patch, MagicMock
from vaitp_auditor.ui.keyboard_input import KeyboardInput


class TestKeyboardInput:
    """Test cases for KeyboardInput functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.keyboard_input = KeyboardInput()

    def test_initialization(self):
        """Test KeyboardInput initialization."""
        ki = KeyboardInput()
        assert ki.old_settings is None
        assert ki.raw_mode is False

    @patch('sys.stdin.isatty')
    @patch('sys.stdin.fileno')
    @patch('termios.tcgetattr')
    @patch('tty.setraw')
    def test_enable_raw_mode(self, mock_setraw, mock_tcgetattr, mock_fileno, mock_isatty):
        """Test enabling raw mode."""
        mock_isatty.return_value = True
        mock_fileno.return_value = 0
        mock_tcgetattr.return_value = "mock_settings"
        
        self.keyboard_input.enable_raw_mode()
        
        assert self.keyboard_input.raw_mode is True
        assert self.keyboard_input.old_settings == "mock_settings"
        mock_setraw.assert_called_once()

    @patch('sys.stdin.isatty')
    def test_enable_raw_mode_not_tty(self, mock_isatty):
        """Test enabling raw mode when not a TTY."""
        mock_isatty.return_value = False
        
        self.keyboard_input.enable_raw_mode()
        
        assert self.keyboard_input.raw_mode is False
        assert self.keyboard_input.old_settings is None

    @patch('sys.stdin.fileno')
    @patch('termios.tcsetattr')
    def test_disable_raw_mode(self, mock_tcsetattr, mock_fileno):
        """Test disabling raw mode."""
        # Set up as if raw mode was enabled
        mock_fileno.return_value = 0
        self.keyboard_input.raw_mode = True
        self.keyboard_input.old_settings = "mock_settings"
        
        self.keyboard_input.disable_raw_mode()
        
        assert self.keyboard_input.raw_mode is False
        mock_tcsetattr.assert_called_once()

    def test_disable_raw_mode_not_enabled(self):
        """Test disabling raw mode when not enabled."""
        # Should not raise an error
        self.keyboard_input.disable_raw_mode()
        assert self.keyboard_input.raw_mode is False

    @patch('sys.stdin.isatty')
    @patch('select.select')
    @patch('sys.stdin.read')
    def test_get_key_simple(self, mock_read, mock_select, mock_isatty):
        """Test getting a simple key."""
        mock_isatty.return_value = True
        mock_select.return_value = ([True], [], [])
        mock_read.return_value = 'a'
        
        key = self.keyboard_input.get_key()
        assert key == 'a'

    @patch('sys.stdin.isatty')
    @patch('select.select')
    def test_get_key_timeout(self, mock_select, mock_isatty):
        """Test getting key with timeout."""
        mock_isatty.return_value = True
        mock_select.return_value = ([], [], [])  # No input available
        
        key = self.keyboard_input.get_key(timeout=0.1)
        assert key is None

    @patch('sys.stdin.isatty')
    @patch('select.select')
    @patch('sys.stdin.read')
    def test_get_key_arrow_sequence(self, mock_read, mock_select, mock_isatty):
        """Test getting arrow key sequence."""
        mock_isatty.return_value = True
        mock_select.side_effect = [
            ([True], [], []),  # Initial select
            ([True], [], []),  # For escape sequence
            ([True], [], []),  # For '[' 
            ([True], [], []),  # For 'A'
            ([], [], [])       # No more input
        ]
        
        # Simulate arrow up sequence: ESC [ A
        mock_read.side_effect = ['\x1b', '[', 'A']
        
        key = self.keyboard_input.get_key()
        assert key == '\x1b[A'

    @patch('sys.stdin.isatty')
    def test_get_key_not_tty(self, mock_isatty):
        """Test getting key when not a TTY."""
        mock_isatty.return_value = False
        
        key = self.keyboard_input.get_key()
        assert key is None

    @patch('sys.stdin.isatty')
    @patch('select.select')
    @patch('sys.stdin.read')
    def test_get_key_keyboard_interrupt(self, mock_read, mock_select, mock_isatty):
        """Test handling KeyboardInterrupt."""
        mock_isatty.return_value = True
        mock_select.return_value = ([True], [], [])
        mock_read.side_effect = KeyboardInterrupt()
        
        key = self.keyboard_input.get_key()
        assert key is None

    @patch('sys.stdin.isatty')
    @patch('select.select')
    @patch('sys.stdin.read')
    def test_get_key_eof_error(self, mock_read, mock_select, mock_isatty):
        """Test handling EOFError."""
        mock_isatty.return_value = True
        mock_select.return_value = ([True], [], [])
        mock_read.side_effect = EOFError()
        
        key = self.keyboard_input.get_key()
        assert key is None

    def test_is_navigation_key(self):
        """Test navigation key detection."""
        # Test arrow keys
        assert KeyboardInput.is_navigation_key('\x1b[A') is True  # Up
        assert KeyboardInput.is_navigation_key('\x1b[B') is True  # Down
        assert KeyboardInput.is_navigation_key('\x1b[C') is True  # Right
        assert KeyboardInput.is_navigation_key('\x1b[D') is True  # Left
        
        # Test page keys
        assert KeyboardInput.is_navigation_key('\x1b[5~') is True  # Page Up
        assert KeyboardInput.is_navigation_key('\x1b[6~') is True  # Page Down
        
        # Test home/end
        assert KeyboardInput.is_navigation_key('\x1b[H') is True  # Home
        assert KeyboardInput.is_navigation_key('\x1b[F') is True  # End
        
        # Test vi-style keys
        assert KeyboardInput.is_navigation_key('k') is True
        assert KeyboardInput.is_navigation_key('j') is True
        assert KeyboardInput.is_navigation_key('h') is True
        assert KeyboardInput.is_navigation_key('l') is True
        
        # Test tab
        assert KeyboardInput.is_navigation_key('\t') is True
        
        # Test non-navigation keys
        assert KeyboardInput.is_navigation_key('a') is False
        assert KeyboardInput.is_navigation_key('1') is False
        assert KeyboardInput.is_navigation_key('\n') is False

    def test_normalize_key(self):
        """Test key normalization."""
        # Test CR to LF conversion
        assert KeyboardInput.normalize_key('\r') == '\n'
        
        # Test DEL to BS conversion
        assert KeyboardInput.normalize_key('\x7f') == '\x08'
        
        # Test unchanged keys
        assert KeyboardInput.normalize_key('a') == 'a'
        assert KeyboardInput.normalize_key('\x1b[A') == '\x1b[A'

    def test_get_key_name(self):
        """Test getting human-readable key names."""
        # Test arrow keys
        assert KeyboardInput.get_key_name('\x1b[A') == 'Up Arrow'
        assert KeyboardInput.get_key_name('\x1b[B') == 'Down Arrow'
        assert KeyboardInput.get_key_name('\x1b[C') == 'Right Arrow'
        assert KeyboardInput.get_key_name('\x1b[D') == 'Left Arrow'
        
        # Test page keys
        assert KeyboardInput.get_key_name('\x1b[5~') == 'Page Up'
        assert KeyboardInput.get_key_name('\x1b[6~') == 'Page Down'
        
        # Test special keys
        assert KeyboardInput.get_key_name('\t') == 'Tab'
        assert KeyboardInput.get_key_name('\n') == 'Enter'
        assert KeyboardInput.get_key_name(' ') == 'Space'
        
        # Test printable characters
        assert KeyboardInput.get_key_name('a') == "'a'"
        assert KeyboardInput.get_key_name('1') == "'1'"
        
        # Test unknown keys
        result = KeyboardInput.get_key_name('\x99')
        assert result.startswith('Key(')

    def test_context_manager(self):
        """Test using KeyboardInput as context manager."""
        with patch.object(self.keyboard_input, 'enable_raw_mode') as mock_enable:
            with patch.object(self.keyboard_input, 'disable_raw_mode') as mock_disable:
                with self.keyboard_input:
                    pass
                
                mock_enable.assert_called_once()
                mock_disable.assert_called_once()

    @patch('sys.stdin.isatty')
    @patch('select.select')
    def test_has_input(self, mock_select, mock_isatty):
        """Test checking for available input."""
        mock_isatty.return_value = True
        
        # Test with input available
        mock_select.return_value = ([True], [], [])
        assert self.keyboard_input._has_input(0.1) is True
        
        # Test with no input available
        mock_select.return_value = ([], [], [])
        assert self.keyboard_input._has_input(0.1) is False

    @patch('sys.stdin.isatty')
    def test_has_input_not_tty(self, mock_isatty):
        """Test checking for input when not a TTY."""
        mock_isatty.return_value = False
        assert self.keyboard_input._has_input(0.1) is False

    @patch('sys.stdin.isatty')
    @patch('select.select')
    @patch('sys.stdin.read')
    def test_get_key_blocking(self, mock_read, mock_select, mock_isatty):
        """Test blocking key input."""
        mock_isatty.return_value = True
        mock_select.return_value = ([True], [], [])
        mock_read.return_value = 'x'
        
        key = self.keyboard_input.get_key_blocking()
        assert key == 'x'

    @patch('sys.stdin.isatty')
    @patch('select.select')
    @patch('sys.stdin.read')
    def test_complex_escape_sequence(self, mock_read, mock_select, mock_isatty):
        """Test handling complex escape sequences."""
        mock_isatty.return_value = True
        mock_select.side_effect = [
            ([True], [], []),  # Initial select
            ([True], [], []),  # For escape sequence
            ([True], [], []),  # For '[' 
            ([True], [], []),  # For '5'
            ([True], [], []),  # For '~'
            ([], [], [])       # No more input
        ]
        
        # Simulate Page Up sequence: ESC [ 5 ~
        mock_read.side_effect = ['\x1b', '[', '5', '~']
        
        key = self.keyboard_input.get_key()
        assert key == '\x1b[5~'

    @patch('sys.stdin.isatty')
    @patch('select.select')
    @patch('sys.stdin.read')
    def test_incomplete_escape_sequence(self, mock_read, mock_select, mock_isatty):
        """Test handling incomplete escape sequences."""
        mock_isatty.return_value = True
        mock_select.side_effect = [
            ([True], [], []),  # Initial select
            ([True], [], []),  # For escape sequence
            ([], [], [])       # No more input (timeout)
        ]
        
        # Simulate incomplete sequence: just ESC then [, then timeout
        mock_read.side_effect = ['\x1b', '[', '']  # Add empty string for when no more input
        
        key = self.keyboard_input.get_key()
        assert key == '\x1b['  # Should return what was read