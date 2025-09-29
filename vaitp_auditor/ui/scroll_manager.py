"""
Scroll manager for handling vertical and horizontal scrolling in terminal UI.
"""

import sys
from typing import Tuple, Optional, List
from dataclasses import dataclass
from enum import Enum

# Platform-specific imports - not needed for scroll manager functionality
# but kept for compatibility
try:
    import termios
    import tty
    UNIX_PLATFORM = True
except ImportError:
    UNIX_PLATFORM = False


class ScrollDirection(Enum):
    """Enumeration for scroll directions."""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    PAGE_UP = "page_up"
    PAGE_DOWN = "page_down"
    HOME = "home"
    END = "end"


@dataclass
class ScrollState:
    """Represents the current scroll state for a panel."""
    vertical_offset: int = 0
    horizontal_offset: int = 0
    max_vertical: int = 0
    max_horizontal: int = 0
    viewport_height: int = 0
    viewport_width: int = 0


class ScrollManager:
    """
    Manages independent vertical and horizontal scrolling for code panels.
    
    Handles keyboard input for navigation and maintains scroll state with
    boundary checking and smooth scrolling behavior.
    """

    def __init__(self):
        """Initialize the scroll manager."""
        self.left_panel_state = ScrollState()
        self.right_panel_state = ScrollState()
        self.active_panel = "left"  # "left" or "right"
        
        # Key mappings for navigation
        self.key_mappings = {
            '\x1b[A': ScrollDirection.UP,        # Up arrow
            '\x1b[B': ScrollDirection.DOWN,      # Down arrow
            '\x1b[C': ScrollDirection.RIGHT,     # Right arrow
            '\x1b[D': ScrollDirection.LEFT,      # Left arrow
            '\x1b[5~': ScrollDirection.PAGE_UP,  # Page Up
            '\x1b[6~': ScrollDirection.PAGE_DOWN, # Page Down
            '\x1b[H': ScrollDirection.HOME,      # Home
            '\x1b[F': ScrollDirection.END,       # End
            'k': ScrollDirection.UP,             # Vi-style up
            'j': ScrollDirection.DOWN,           # Vi-style down
            'h': ScrollDirection.LEFT,           # Vi-style left
            'l': ScrollDirection.RIGHT,          # Vi-style right
        }

    def set_content_dimensions(
        self, 
        panel: str, 
        content_lines: List[str], 
        viewport_height: int, 
        viewport_width: int
    ) -> None:
        """
        Set content dimensions for a panel to calculate scroll boundaries.
        
        Args:
            panel: Panel identifier ("left" or "right").
            content_lines: List of content lines.
            viewport_height: Height of the viewport.
            viewport_width: Width of the viewport.
        """
        state = self._get_panel_state(panel)
        
        # Calculate maximum scroll offsets
        state.max_vertical = max(0, len(content_lines) - viewport_height)
        
        # Find the longest line for horizontal scrolling
        max_line_length = max(len(line) for line in content_lines) if content_lines else 0
        state.max_horizontal = max(0, max_line_length - viewport_width)
        
        state.viewport_height = viewport_height
        state.viewport_width = viewport_width
        
        # Clamp current offsets to new boundaries
        self._clamp_offsets(state)

    def handle_scroll_input(self, key_input: str) -> bool:
        """
        Handle keyboard input for scrolling.
        
        Args:
            key_input: The key input string.
            
        Returns:
            bool: True if the input was handled as a scroll command, False otherwise.
        """
        # Handle panel switching
        if key_input == '\t':  # Tab key
            self.switch_active_panel()
            return True
        
        # Handle scroll commands
        if key_input in self.key_mappings:
            direction = self.key_mappings[key_input]
            self.scroll(direction)
            return True
        
        return False

    def scroll(self, direction: ScrollDirection, panel: Optional[str] = None) -> bool:
        """
        Scroll in the specified direction.
        
        Args:
            direction: Direction to scroll.
            panel: Panel to scroll (defaults to active panel).
            
        Returns:
            bool: True if scrolling occurred, False if at boundary.
        """
        if panel is None:
            panel = self.active_panel
        
        state = self._get_panel_state(panel)
        old_vertical = state.vertical_offset
        old_horizontal = state.horizontal_offset
        
        if direction == ScrollDirection.UP:
            state.vertical_offset = max(0, state.vertical_offset - 1)
        elif direction == ScrollDirection.DOWN:
            state.vertical_offset = min(state.max_vertical, state.vertical_offset + 1)
        elif direction == ScrollDirection.LEFT:
            state.horizontal_offset = max(0, state.horizontal_offset - 1)
        elif direction == ScrollDirection.RIGHT:
            state.horizontal_offset = min(state.max_horizontal, state.horizontal_offset + 1)
        elif direction == ScrollDirection.PAGE_UP:
            page_size = max(1, state.viewport_height - 1)
            state.vertical_offset = max(0, state.vertical_offset - page_size)
        elif direction == ScrollDirection.PAGE_DOWN:
            page_size = max(1, state.viewport_height - 1)
            state.vertical_offset = min(state.max_vertical, state.vertical_offset + page_size)
        elif direction == ScrollDirection.HOME:
            state.vertical_offset = 0
            state.horizontal_offset = 0
        elif direction == ScrollDirection.END:
            state.vertical_offset = state.max_vertical
            state.horizontal_offset = 0
        
        # Return True if any offset changed
        return (old_vertical != state.vertical_offset or 
                old_horizontal != state.horizontal_offset)

    def get_visible_content(
        self, 
        panel: str, 
        content_lines: List[str]
    ) -> Tuple[List[str], int, int]:
        """
        Get the visible portion of content based on current scroll state.
        
        Args:
            panel: Panel identifier ("left" or "right").
            content_lines: Full content lines.
            
        Returns:
            Tuple[List[str], int, int]: (visible_lines, start_line_number, scroll_indicator)
        """
        state = self._get_panel_state(panel)
        
        # Get vertical slice
        start_line = state.vertical_offset
        end_line = start_line + state.viewport_height
        visible_lines = content_lines[start_line:end_line]
        
        # Apply horizontal scrolling to each line
        if state.horizontal_offset > 0:
            visible_lines = [
                line[state.horizontal_offset:state.horizontal_offset + state.viewport_width]
                if len(line) > state.horizontal_offset else ""
                for line in visible_lines
            ]
        else:
            visible_lines = [
                line[:state.viewport_width] if len(line) > state.viewport_width else line
                for line in visible_lines
            ]
        
        return visible_lines, start_line + 1, self._get_scroll_indicator(state)

    def switch_active_panel(self) -> None:
        """Switch the active panel for scrolling."""
        self.active_panel = "right" if self.active_panel == "left" else "left"

    def get_active_panel(self) -> str:
        """Get the currently active panel."""
        return self.active_panel

    def reset_scroll_state(self, panel: Optional[str] = None) -> None:
        """
        Reset scroll state for a panel or both panels.
        
        Args:
            panel: Panel to reset (None for both panels).
        """
        if panel is None or panel == "left":
            self.left_panel_state = ScrollState()
        if panel is None or panel == "right":
            self.right_panel_state = ScrollState()

    def get_scroll_info(self, panel: str) -> dict:
        """
        Get scroll information for display purposes.
        
        Args:
            panel: Panel identifier.
            
        Returns:
            dict: Scroll information including offsets and boundaries.
        """
        state = self._get_panel_state(panel)
        
        return {
            'vertical_offset': state.vertical_offset,
            'horizontal_offset': state.horizontal_offset,
            'max_vertical': state.max_vertical,
            'max_horizontal': state.max_horizontal,
            'can_scroll_up': state.vertical_offset > 0,
            'can_scroll_down': state.vertical_offset < state.max_vertical,
            'can_scroll_left': state.horizontal_offset > 0,
            'can_scroll_right': state.horizontal_offset < state.max_horizontal,
            'is_active': panel == self.active_panel
        }

    def _get_panel_state(self, panel: str) -> ScrollState:
        """
        Get the scroll state for a panel.
        
        Args:
            panel: Panel identifier ("left" or "right").
            
        Returns:
            ScrollState: The scroll state for the panel.
        """
        if panel == "left":
            return self.left_panel_state
        elif panel == "right":
            return self.right_panel_state
        else:
            raise ValueError(f"Invalid panel identifier: {panel}")

    def _clamp_offsets(self, state: ScrollState) -> None:
        """
        Clamp scroll offsets to valid boundaries.
        
        Args:
            state: ScrollState to clamp.
        """
        state.vertical_offset = max(0, min(state.max_vertical, state.vertical_offset))
        state.horizontal_offset = max(0, min(state.max_horizontal, state.horizontal_offset))

    def _get_scroll_indicator(self, state: ScrollState) -> int:
        """
        Get scroll indicator value for display.
        
        Args:
            state: ScrollState to analyze.
            
        Returns:
            int: Scroll indicator (0=no scroll, 1=can scroll, 2=scrolled).
        """
        if state.max_vertical == 0 and state.max_horizontal == 0:
            return 0  # No scrolling needed
        elif state.vertical_offset > 0 or state.horizontal_offset > 0:
            return 2  # Currently scrolled
        else:
            return 1  # Can scroll but not currently scrolled

    def get_navigation_help(self) -> str:
        """
        Get help text for navigation commands.
        
        Returns:
            str: Help text for navigation.
        """
        return """Navigation Commands:
        Arrow Keys / hjkl - Scroll in direction
        Page Up/Down - Scroll by page
        Home/End - Go to beginning/end
        Tab - Switch between panels
        """

    def can_scroll(self, panel: str, direction: ScrollDirection) -> bool:
        """
        Check if scrolling is possible in a given direction.
        
        Args:
            panel: Panel identifier.
            direction: Direction to check.
            
        Returns:
            bool: True if scrolling is possible.
        """
        state = self._get_panel_state(panel)
        
        if direction in [ScrollDirection.UP, ScrollDirection.PAGE_UP]:
            return state.vertical_offset > 0
        elif direction in [ScrollDirection.DOWN, ScrollDirection.PAGE_DOWN]:
            return state.vertical_offset < state.max_vertical
        elif direction == ScrollDirection.LEFT:
            return state.horizontal_offset > 0
        elif direction == ScrollDirection.RIGHT:
            return state.horizontal_offset < state.max_horizontal
        elif direction == ScrollDirection.HOME:
            return state.vertical_offset > 0 or state.horizontal_offset > 0
        elif direction == ScrollDirection.END:
            return state.vertical_offset < state.max_vertical
        
        return False