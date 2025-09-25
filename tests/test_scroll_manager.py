"""
Unit tests for ScrollManager class.
"""

import pytest
from vaitp_auditor.ui.scroll_manager import ScrollManager, ScrollDirection, ScrollState


class TestScrollManager:
    """Test cases for ScrollManager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scroll_manager = ScrollManager()
        
        # Sample content for testing
        self.sample_content = [
            "line 1 - short",
            "line 2 - this is a much longer line that exceeds normal terminal width",
            "line 3 - medium length line",
            "line 4 - short",
            "line 5 - another very long line that definitely exceeds the viewport width",
            "line 6 - short",
            "line 7 - medium",
            "line 8 - final line"
        ]
        
        # Set up content dimensions
        self.viewport_height = 4
        self.viewport_width = 20
        
        self.scroll_manager.set_content_dimensions(
            "left", 
            self.sample_content, 
            self.viewport_height, 
            self.viewport_width
        )

    def test_initialization(self):
        """Test ScrollManager initialization."""
        sm = ScrollManager()
        
        assert sm.active_panel == "left"
        assert sm.left_panel_state.vertical_offset == 0
        assert sm.left_panel_state.horizontal_offset == 0
        assert sm.right_panel_state.vertical_offset == 0
        assert sm.right_panel_state.horizontal_offset == 0

    def test_set_content_dimensions(self):
        """Test setting content dimensions."""
        content = ["line1", "line2", "line3", "line4", "line5"]
        viewport_height = 3
        viewport_width = 10
        
        self.scroll_manager.set_content_dimensions("right", content, viewport_height, viewport_width)
        
        state = self.scroll_manager._get_panel_state("right")
        assert state.max_vertical == 2  # 5 lines - 3 viewport = 2
        assert state.viewport_height == viewport_height
        assert state.viewport_width == viewport_width

    def test_vertical_scrolling_down(self):
        """Test vertical scrolling down."""
        # Should be able to scroll down
        result = self.scroll_manager.scroll(ScrollDirection.DOWN, "left")
        assert result is True
        
        state = self.scroll_manager._get_panel_state("left")
        assert state.vertical_offset == 1

    def test_vertical_scrolling_up(self):
        """Test vertical scrolling up."""
        # First scroll down
        self.scroll_manager.scroll(ScrollDirection.DOWN, "left")
        
        # Then scroll up
        result = self.scroll_manager.scroll(ScrollDirection.UP, "left")
        assert result is True
        
        state = self.scroll_manager._get_panel_state("left")
        assert state.vertical_offset == 0

    def test_vertical_scrolling_boundaries(self):
        """Test vertical scrolling boundaries."""
        # Try to scroll up when already at top
        result = self.scroll_manager.scroll(ScrollDirection.UP, "left")
        assert result is False
        
        state = self.scroll_manager._get_panel_state("left")
        assert state.vertical_offset == 0
        
        # Scroll to bottom
        for _ in range(10):  # More than needed
            self.scroll_manager.scroll(ScrollDirection.DOWN, "left")
        
        state = self.scroll_manager._get_panel_state("left")
        assert state.vertical_offset == state.max_vertical
        
        # Try to scroll down when at bottom
        result = self.scroll_manager.scroll(ScrollDirection.DOWN, "left")
        assert result is False

    def test_horizontal_scrolling(self):
        """Test horizontal scrolling."""
        # Should be able to scroll right (long lines exist)
        result = self.scroll_manager.scroll(ScrollDirection.RIGHT, "left")
        assert result is True
        
        state = self.scroll_manager._get_panel_state("left")
        assert state.horizontal_offset == 1
        
        # Should be able to scroll left
        result = self.scroll_manager.scroll(ScrollDirection.LEFT, "left")
        assert result is True
        
        state = self.scroll_manager._get_panel_state("left")
        assert state.horizontal_offset == 0

    def test_horizontal_scrolling_boundaries(self):
        """Test horizontal scrolling boundaries."""
        # Try to scroll left when already at leftmost
        result = self.scroll_manager.scroll(ScrollDirection.LEFT, "left")
        assert result is False
        
        # Scroll to rightmost
        state = self.scroll_manager._get_panel_state("left")
        for _ in range(state.max_horizontal + 5):  # More than needed
            self.scroll_manager.scroll(ScrollDirection.RIGHT, "left")
        
        state = self.scroll_manager._get_panel_state("left")
        assert state.horizontal_offset == state.max_horizontal
        
        # Try to scroll right when at rightmost
        result = self.scroll_manager.scroll(ScrollDirection.RIGHT, "left")
        assert result is False

    def test_page_scrolling(self):
        """Test page up/down scrolling."""
        # Page down
        result = self.scroll_manager.scroll(ScrollDirection.PAGE_DOWN, "left")
        assert result is True
        
        state = self.scroll_manager._get_panel_state("left")
        expected_offset = min(state.max_vertical, self.viewport_height - 1)
        assert state.vertical_offset == expected_offset
        
        # Page up
        result = self.scroll_manager.scroll(ScrollDirection.PAGE_UP, "left")
        assert result is True
        
        state = self.scroll_manager._get_panel_state("left")
        assert state.vertical_offset == 0

    def test_home_end_scrolling(self):
        """Test home and end scrolling."""
        # Scroll to middle
        self.scroll_manager.scroll(ScrollDirection.DOWN, "left")
        self.scroll_manager.scroll(ScrollDirection.RIGHT, "left")
        
        # Home should reset both offsets
        result = self.scroll_manager.scroll(ScrollDirection.HOME, "left")
        assert result is True
        
        state = self.scroll_manager._get_panel_state("left")
        assert state.vertical_offset == 0
        assert state.horizontal_offset == 0
        
        # End should go to bottom, reset horizontal
        result = self.scroll_manager.scroll(ScrollDirection.END, "left")
        assert result is True
        
        state = self.scroll_manager._get_panel_state("left")
        assert state.vertical_offset == state.max_vertical
        assert state.horizontal_offset == 0

    def test_panel_switching(self):
        """Test switching active panels."""
        assert self.scroll_manager.get_active_panel() == "left"
        
        self.scroll_manager.switch_active_panel()
        assert self.scroll_manager.get_active_panel() == "right"
        
        self.scroll_manager.switch_active_panel()
        assert self.scroll_manager.get_active_panel() == "left"

    def test_handle_scroll_input(self):
        """Test keyboard input handling."""
        # Test tab for panel switching
        result = self.scroll_manager.handle_scroll_input('\t')
        assert result is True
        assert self.scroll_manager.get_active_panel() == "right"
        
        # Test arrow keys
        result = self.scroll_manager.handle_scroll_input('\x1b[B')  # Down arrow
        assert result is True
        
        # Test invalid key
        result = self.scroll_manager.handle_scroll_input('x')
        assert result is False

    def test_get_visible_content(self):
        """Test getting visible content."""
        # Test initial state
        visible_lines, start_line, scroll_indicator = self.scroll_manager.get_visible_content("left", self.sample_content)
        
        assert len(visible_lines) == self.viewport_height
        assert start_line == 1
        assert visible_lines[0] == "line 1 - short"
        
        # Test after scrolling down
        self.scroll_manager.scroll(ScrollDirection.DOWN, "left")
        visible_lines, start_line, scroll_indicator = self.scroll_manager.get_visible_content("left", self.sample_content)
        
        assert start_line == 2
        assert visible_lines[0] == "line 2 - this is a much longer line that exceeds normal terminal width"[:self.viewport_width]

    def test_get_visible_content_with_horizontal_scroll(self):
        """Test getting visible content with horizontal scrolling."""
        # Scroll right to test horizontal clipping
        self.scroll_manager.scroll(ScrollDirection.RIGHT, "left")
        
        visible_lines, start_line, scroll_indicator = self.scroll_manager.get_visible_content("left", self.sample_content)
        
        # Check that long line is clipped from the left
        long_line = "line 2 - this is a much longer line that exceeds normal terminal width"
        expected_clipped = long_line[1:1+self.viewport_width]  # Skip first character due to horizontal scroll
        
        # The long line should be at index 1 in the visible content (since we start from line 1)
        if len(visible_lines) > 1:
            actual_line = visible_lines[1]  # Second line in viewport
            assert actual_line == expected_clipped, f"Expected '{expected_clipped}', got '{actual_line}'"
        else:
            # If not enough lines, check if any line contains the expected content
            found_long_line = False
            for i, line in enumerate(visible_lines):
                if "ine 2" in line:  # "line 2" with first char removed
                    assert line == expected_clipped, f"Line {i}: Expected '{expected_clipped}', got '{line}'"
                    found_long_line = True
                    break
            
            assert found_long_line, f"Long line not found in visible content: {visible_lines}"

    def test_scroll_info(self):
        """Test getting scroll information."""
        info = self.scroll_manager.get_scroll_info("left")
        
        assert info['vertical_offset'] == 0
        assert info['horizontal_offset'] == 0
        assert info['can_scroll_down'] is True  # Content is longer than viewport
        assert info['can_scroll_up'] is False   # At top
        assert info['is_active'] is True        # Left panel is active

    def test_reset_scroll_state(self):
        """Test resetting scroll state."""
        # Scroll to some position
        self.scroll_manager.scroll(ScrollDirection.DOWN, "left")
        self.scroll_manager.scroll(ScrollDirection.RIGHT, "left")
        
        # Reset left panel
        self.scroll_manager.reset_scroll_state("left")
        
        state = self.scroll_manager._get_panel_state("left")
        assert state.vertical_offset == 0
        assert state.horizontal_offset == 0

    def test_can_scroll(self):
        """Test can_scroll method."""
        # At initial position
        assert self.scroll_manager.can_scroll("left", ScrollDirection.DOWN) is True
        assert self.scroll_manager.can_scroll("left", ScrollDirection.UP) is False
        assert self.scroll_manager.can_scroll("left", ScrollDirection.RIGHT) is True
        assert self.scroll_manager.can_scroll("left", ScrollDirection.LEFT) is False
        
        # After scrolling
        self.scroll_manager.scroll(ScrollDirection.DOWN, "left")
        assert self.scroll_manager.can_scroll("left", ScrollDirection.UP) is True

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test with empty content
        empty_content = []
        self.scroll_manager.set_content_dimensions("right", empty_content, 5, 10)
        
        visible_lines, start_line, scroll_indicator = self.scroll_manager.get_visible_content("right", empty_content)
        assert visible_lines == []
        assert start_line == 1
        
        # Test with single line content
        single_line = ["only line"]
        self.scroll_manager.set_content_dimensions("right", single_line, 5, 10)
        
        state = self.scroll_manager._get_panel_state("right")
        assert state.max_vertical == 0  # Can't scroll vertically
        
        # Test invalid panel
        with pytest.raises(ValueError):
            self.scroll_manager._get_panel_state("invalid")

    def test_scroll_with_very_long_lines(self):
        """Test scrolling with very long lines."""
        very_long_content = [
            "a" * 100,  # Very long line
            "b" * 50,   # Medium long line
            "c" * 10    # Short line
        ]
        
        self.scroll_manager.set_content_dimensions("left", very_long_content, 3, 20)
        
        # Should be able to scroll horizontally
        state = self.scroll_manager._get_panel_state("left")
        assert state.max_horizontal > 0
        
        # Test horizontal scrolling
        result = self.scroll_manager.scroll(ScrollDirection.RIGHT, "left")
        assert result is True

    def test_scroll_with_small_viewport(self):
        """Test scrolling with very small viewport."""
        self.scroll_manager.set_content_dimensions("left", self.sample_content, 1, 5)
        
        state = self.scroll_manager._get_panel_state("left")
        assert state.max_vertical == len(self.sample_content) - 1
        
        # Page scrolling should still work with minimum page size
        result = self.scroll_manager.scroll(ScrollDirection.PAGE_DOWN, "left")
        assert result is True
        
        # Should scroll by at least 1 line
        assert state.vertical_offset >= 1

    def test_navigation_help(self):
        """Test navigation help text."""
        help_text = self.scroll_manager.get_navigation_help()
        assert "Arrow Keys" in help_text
        assert "Tab" in help_text
        assert "Page Up/Down" in help_text