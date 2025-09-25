"""
Keyboard input handler for capturing raw keyboard input including arrow keys.
"""

import sys
import select
import termios
import tty
from typing import Optional


class KeyboardInput:
    """
    Handles raw keyboard input capture for navigation keys.
    
    Provides non-blocking keyboard input with support for special keys
    like arrow keys, page up/down, etc.
    """

    def __init__(self):
        """Initialize the keyboard input handler."""
        self.old_settings = None
        self.raw_mode = False

    def __enter__(self):
        """Enter raw input mode."""
        self.enable_raw_mode()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit raw input mode."""
        self.disable_raw_mode()

    def enable_raw_mode(self) -> None:
        """Enable raw keyboard input mode."""
        if sys.stdin.isatty():
            self.old_settings = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())
            self.raw_mode = True

    def disable_raw_mode(self) -> None:
        """Disable raw keyboard input mode."""
        if self.raw_mode and self.old_settings:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.old_settings)
            self.raw_mode = False

    def get_key(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Get a single key press with optional timeout.
        
        Args:
            timeout: Timeout in seconds (None for blocking).
            
        Returns:
            Optional[str]: Key sequence or None if timeout.
        """
        if not sys.stdin.isatty():
            return None

        # Check if input is available
        if timeout is not None:
            ready, _, _ = select.select([sys.stdin], [], [], timeout)
            if not ready:
                return None

        try:
            # Read first character
            char = sys.stdin.read(1)
            
            # Handle escape sequences
            if char == '\x1b':  # ESC
                # Try to read more characters for escape sequences
                if self._has_input(0.1):  # Short timeout for escape sequences
                    char += sys.stdin.read(1)
                    if char == '\x1b[':  # CSI sequence
                        # Read until we get a letter (end of sequence)
                        while True:
                            if self._has_input(0.1):
                                next_char = sys.stdin.read(1)
                                char += next_char
                                # Most CSI sequences end with a letter or ~
                                if next_char.isalpha() or next_char == '~':
                                    break
                            else:
                                break
            
            return char
            
        except (KeyboardInterrupt, EOFError):
            return None

    def get_key_blocking(self) -> str:
        """
        Get a key press in blocking mode.
        
        Returns:
            str: Key sequence.
        """
        key = self.get_key()
        return key if key is not None else ''

    def _has_input(self, timeout: float) -> bool:
        """
        Check if input is available within timeout.
        
        Args:
            timeout: Timeout in seconds.
            
        Returns:
            bool: True if input is available.
        """
        if not sys.stdin.isatty():
            return False
        
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        return bool(ready)

    @staticmethod
    def is_navigation_key(key: str) -> bool:
        """
        Check if a key is a navigation key.
        
        Args:
            key: Key sequence to check.
            
        Returns:
            bool: True if it's a navigation key.
        """
        navigation_keys = {
            '\x1b[A',    # Up arrow
            '\x1b[B',    # Down arrow
            '\x1b[C',    # Right arrow
            '\x1b[D',    # Left arrow
            '\x1b[5~',   # Page Up
            '\x1b[6~',   # Page Down
            '\x1b[H',    # Home
            '\x1b[F',    # End
            'k', 'j', 'h', 'l',  # Vi-style navigation
            '\t',        # Tab
        }
        return key in navigation_keys

    @staticmethod
    def normalize_key(key: str) -> str:
        """
        Normalize key input for consistent handling.
        
        Args:
            key: Raw key input.
            
        Returns:
            str: Normalized key.
        """
        # Convert common variations
        key_mappings = {
            '\r': '\n',      # Convert CR to LF
            '\x7f': '\x08',  # Convert DEL to BS
        }
        
        return key_mappings.get(key, key)

    @staticmethod
    def get_key_name(key: str) -> str:
        """
        Get human-readable name for a key.
        
        Args:
            key: Key sequence.
            
        Returns:
            str: Human-readable key name.
        """
        key_names = {
            '\x1b[A': 'Up Arrow',
            '\x1b[B': 'Down Arrow',
            '\x1b[C': 'Right Arrow',
            '\x1b[D': 'Left Arrow',
            '\x1b[5~': 'Page Up',
            '\x1b[6~': 'Page Down',
            '\x1b[H': 'Home',
            '\x1b[F': 'End',
            '\t': 'Tab',
            '\n': 'Enter',
            '\x1b': 'Escape',
            ' ': 'Space',
            '\x08': 'Backspace',
            '\x7f': 'Delete',
        }
        
        if key in key_names:
            return key_names[key]
        elif len(key) == 1 and key.isprintable():
            return f"'{key}'"
        else:
            return f"Key({repr(key)})"