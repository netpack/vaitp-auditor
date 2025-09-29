"""
Keyboard input handler for capturing raw keyboard input including arrow keys.
"""

import sys
from typing import Optional

# Platform-specific imports
try:
    import termios
    import tty
    import select
    UNIX_PLATFORM = True
except ImportError:
    UNIX_PLATFORM = False
    # Windows-specific imports
    try:
        import msvcrt
        WINDOWS_PLATFORM = True
    except ImportError:
        WINDOWS_PLATFORM = False


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
        if UNIX_PLATFORM and sys.stdin.isatty():
            self.old_settings = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())
            self.raw_mode = True
        elif WINDOWS_PLATFORM:
            # Windows doesn't need special setup for raw mode
            self.raw_mode = True

    def disable_raw_mode(self) -> None:
        """Disable raw keyboard input mode."""
        if UNIX_PLATFORM and self.raw_mode and self.old_settings:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.old_settings)
            self.raw_mode = False
        elif WINDOWS_PLATFORM:
            self.raw_mode = False

    def get_key(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Get a single key press with optional timeout.
        
        Args:
            timeout: Timeout in seconds (None for blocking).
            
        Returns:
            Optional[str]: Key sequence or None if timeout.
        """
        if WINDOWS_PLATFORM:
            return self._get_key_windows(timeout)
        elif UNIX_PLATFORM:
            return self._get_key_unix(timeout)
        else:
            # Fallback for unsupported platforms
            return input() if timeout is None else None

    def _get_key_windows(self, timeout: Optional[float] = None) -> Optional[str]:
        """Windows-specific key input handling."""
        import time
        
        if timeout is not None:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if msvcrt.kbhit():
                    break
                time.sleep(0.01)
            else:
                return None
        
        if not msvcrt.kbhit():
            if timeout is not None:
                return None
            # Blocking wait for Windows
            while not msvcrt.kbhit():
                time.sleep(0.01)
        
        try:
            char = msvcrt.getch().decode('utf-8', errors='ignore')
            
            # Handle special keys on Windows
            if char == '\x00' or char == '\xe0':  # Special key prefix
                char2 = msvcrt.getch().decode('utf-8', errors='ignore')
                # Convert Windows special keys to Unix-style escape sequences
                windows_key_map = {
                    'H': '\x1b[A',    # Up arrow
                    'P': '\x1b[B',    # Down arrow
                    'M': '\x1b[C',    # Right arrow
                    'K': '\x1b[D',    # Left arrow
                    'I': '\x1b[5~',   # Page Up
                    'Q': '\x1b[6~',   # Page Down
                    'G': '\x1b[H',    # Home
                    'O': '\x1b[F',    # End
                }
                return windows_key_map.get(char2, char2)
            
            return char
            
        except (KeyboardInterrupt, EOFError, UnicodeDecodeError):
            return None

    def _get_key_unix(self, timeout: Optional[float] = None) -> Optional[str]:
        """Unix-specific key input handling."""
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
        if WINDOWS_PLATFORM:
            import time
            start_time = time.time()
            while time.time() - start_time < timeout:
                if msvcrt.kbhit():
                    return True
                time.sleep(0.01)
            return False
        elif UNIX_PLATFORM and sys.stdin.isatty():
            ready, _, _ = select.select([sys.stdin], [], [], timeout)
            return bool(ready)
        else:
            return False

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