"""
Unit tests for DiffRenderer class.
"""

import pytest
from unittest.mock import Mock, patch
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns

from vaitp_auditor.ui.diff_renderer import DiffRenderer
from vaitp_auditor.core.models import DiffLine


class TestDiffRenderer:
    """Test cases for DiffRenderer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.diff_renderer = DiffRenderer()

    def test_init_default_console(self):
        """Test DiffRenderer initialization with default console."""
        renderer = DiffRenderer()
        assert isinstance(renderer.console, Console)

    def test_init_custom_console(self):
        """Test DiffRenderer initialization with custom console."""
        custom_console = Mock(spec=Console)
        renderer = DiffRenderer(custom_console)
        assert renderer.console is custom_console

    def test_render_diff_lines_empty(self):
        """Test rendering empty diff lines list."""
        result = self.diff_renderer.render_diff_lines([])
        assert isinstance(result, Text)
        assert str(result) == ""

    def test_render_diff_lines_equal(self):
        """Test rendering equal diff lines."""
        diff_lines = [
            DiffLine(tag='equal', line_content='def test():', line_number=1),
            DiffLine(tag='equal', line_content='    return True', line_number=2)
        ]
        
        result = self.diff_renderer.render_diff_lines(diff_lines)
        assert isinstance(result, Text)
        # Should contain the line content
        result_str = str(result)
        assert 'def test():' in result_str
        assert 'return True' in result_str

    def test_render_diff_lines_add(self):
        """Test rendering added diff lines."""
        diff_lines = [
            DiffLine(tag='add', line_content='new_function()', line_number=3)
        ]
        
        result = self.diff_renderer.render_diff_lines(diff_lines)
        assert isinstance(result, Text)
        result_str = str(result)
        assert 'new_function()' in result_str
        assert '+' in result_str

    def test_render_diff_lines_remove(self):
        """Test rendering removed diff lines."""
        diff_lines = [
            DiffLine(tag='remove', line_content='old_function()', line_number=4)
        ]
        
        result = self.diff_renderer.render_diff_lines(diff_lines)
        assert isinstance(result, Text)
        result_str = str(result)
        assert 'old_function()' in result_str
        assert '-' in result_str

    def test_render_diff_lines_modify(self):
        """Test rendering modified diff lines."""
        diff_lines = [
            DiffLine(tag='modify', line_content='modified_function()', line_number=5)
        ]
        
        result = self.diff_renderer.render_diff_lines(diff_lines)
        assert isinstance(result, Text)
        result_str = str(result)
        assert 'modified_function()' in result_str
        assert '~' in result_str

    def test_render_diff_lines_no_line_number(self):
        """Test rendering diff lines without line numbers."""
        diff_lines = [
            DiffLine(tag='equal', line_content='test line')
        ]
        
        result = self.diff_renderer.render_diff_lines(diff_lines)
        assert isinstance(result, Text)
        result_str = str(result)
        assert 'test line' in result_str

    def test_render_diff_lines_mixed_tags(self):
        """Test rendering diff lines with mixed tags."""
        diff_lines = [
            DiffLine(tag='equal', line_content='unchanged line', line_number=1),
            DiffLine(tag='add', line_content='added line', line_number=2),
            DiffLine(tag='remove', line_content='removed line', line_number=3),
            DiffLine(tag='modify', line_content='modified line', line_number=4)
        ]
        
        result = self.diff_renderer.render_diff_lines(diff_lines)
        assert isinstance(result, Text)
        result_str = str(result)
        
        # All content should be present
        assert 'unchanged line' in result_str
        assert 'added line' in result_str
        assert 'removed line' in result_str
        assert 'modified line' in result_str
        
        # Appropriate symbols should be present
        assert '+' in result_str
        assert '-' in result_str
        assert '~' in result_str

    def test_render_side_by_side_diff(self):
        """Test side-by-side diff rendering."""
        expected_lines = [
            DiffLine(tag='equal', line_content='def test():', line_number=1),
            DiffLine(tag='remove', line_content='    return False', line_number=2)
        ]
        
        generated_lines = [
            DiffLine(tag='equal', line_content='def test():', line_number=1),
            DiffLine(tag='add', line_content='    return True', line_number=2)
        ]
        
        result = self.diff_renderer.render_side_by_side_diff(expected_lines, generated_lines)
        assert isinstance(result, Columns)

    def test_render_unified_diff(self):
        """Test unified diff rendering."""
        diff_lines = [
            DiffLine(tag='equal', line_content='def test():', line_number=1),
            DiffLine(tag='remove', line_content='    return False', line_number=2),
            DiffLine(tag='add', line_content='    return True', line_number=3)
        ]
        
        result = self.diff_renderer.render_unified_diff(diff_lines)
        assert isinstance(result, Panel)

    def test_create_diff_summary_no_changes(self):
        """Test diff summary with no changes."""
        diff_lines = [
            DiffLine(tag='equal', line_content='line 1'),
            DiffLine(tag='equal', line_content='line 2')
        ]
        
        result = self.diff_renderer.create_diff_summary(diff_lines)
        assert isinstance(result, Text)
        result_str = str(result)
        assert 'No differences' in result_str

    def test_create_diff_summary_with_changes(self):
        """Test diff summary with various changes."""
        diff_lines = [
            DiffLine(tag='add', line_content='added line'),
            DiffLine(tag='remove', line_content='removed line'),
            DiffLine(tag='modify', line_content='modified line'),
            DiffLine(tag='equal', line_content='equal line')
        ]
        
        result = self.diff_renderer.create_diff_summary(diff_lines)
        assert isinstance(result, Text)
        result_str = str(result)
        
        # Should contain counts
        assert '+1' in result_str
        assert '-1' in result_str
        assert '~1' in result_str
        assert '=1' in result_str

    def test_create_diff_summary_only_additions(self):
        """Test diff summary with only additions."""
        diff_lines = [
            DiffLine(tag='add', line_content='added line 1'),
            DiffLine(tag='add', line_content='added line 2')
        ]
        
        result = self.diff_renderer.create_diff_summary(diff_lines)
        assert isinstance(result, Text)
        result_str = str(result)
        assert '+2' in result_str

    def test_create_diff_summary_only_removals(self):
        """Test diff summary with only removals."""
        diff_lines = [
            DiffLine(tag='remove', line_content='removed line 1'),
            DiffLine(tag='remove', line_content='removed line 2'),
            DiffLine(tag='remove', line_content='removed line 3')
        ]
        
        result = self.diff_renderer.create_diff_summary(diff_lines)
        assert isinstance(result, Text)
        result_str = str(result)
        assert '-3' in result_str

    def test_render_diff_with_context_empty(self):
        """Test contextual diff rendering with empty input."""
        result = self.diff_renderer.render_diff_with_context([])
        assert isinstance(result, Text)
        result_str = str(result)
        assert 'No differences found' in result_str

    def test_render_diff_with_context_no_changes(self):
        """Test contextual diff rendering with no changes."""
        diff_lines = [
            DiffLine(tag='equal', line_content='line 1'),
            DiffLine(tag='equal', line_content='line 2')
        ]
        
        result = self.diff_renderer.render_diff_with_context(diff_lines)
        assert isinstance(result, Text)
        result_str = str(result)
        assert 'No differences found' in result_str

    def test_render_diff_with_context_with_changes(self):
        """Test contextual diff rendering with changes."""
        diff_lines = [
            DiffLine(tag='equal', line_content='line 1', line_number=1),
            DiffLine(tag='equal', line_content='line 2', line_number=2),
            DiffLine(tag='add', line_content='added line', line_number=3),
            DiffLine(tag='equal', line_content='line 4', line_number=4),
            DiffLine(tag='equal', line_content='line 5', line_number=5)
        ]
        
        result = self.diff_renderer.render_diff_with_context(diff_lines, context_lines=1)
        assert isinstance(result, Text)
        result_str = str(result)
        
        # Should include the change and context
        assert 'added line' in result_str
        assert 'line 2' in result_str  # context before
        assert 'line 4' in result_str  # context after

    def test_render_diff_with_context_multiple_changes(self):
        """Test contextual diff rendering with multiple separated changes."""
        diff_lines = [
            DiffLine(tag='add', line_content='added line 1', line_number=1),
            DiffLine(tag='equal', line_content='line 2', line_number=2),
            DiffLine(tag='equal', line_content='line 3', line_number=3),
            DiffLine(tag='equal', line_content='line 4', line_number=4),
            DiffLine(tag='equal', line_content='line 5', line_number=5),
            DiffLine(tag='remove', line_content='removed line', line_number=6),
            DiffLine(tag='equal', line_content='line 7', line_number=7)
        ]
        
        result = self.diff_renderer.render_diff_with_context(diff_lines, context_lines=1)
        assert isinstance(result, Text)
        result_str = str(result)
        
        # Should include both changes and their contexts
        assert 'added line 1' in result_str
        assert 'removed line' in result_str
        # Should include separator for gaps
        assert '...' in result_str

    def test_get_color_legend(self):
        """Test color legend generation."""
        result = self.diff_renderer.get_color_legend()
        assert isinstance(result, Panel)

    def test_render_diff_lines_large_line_numbers(self):
        """Test rendering with large line numbers."""
        diff_lines = [
            DiffLine(tag='equal', line_content='line content', line_number=9999)
        ]
        
        result = self.diff_renderer.render_diff_lines(diff_lines)
        assert isinstance(result, Text)
        result_str = str(result)
        assert '9999' in result_str
        assert 'line content' in result_str

    def test_render_diff_lines_special_characters(self):
        """Test rendering with special characters in content."""
        diff_lines = [
            DiffLine(tag='add', line_content='special chars: àáâãäå ñ ç 🐍', line_number=1)
        ]
        
        result = self.diff_renderer.render_diff_lines(diff_lines)
        assert isinstance(result, Text)
        result_str = str(result)
        assert 'àáâãäå' in result_str
        assert '🐍' in result_str

    def test_render_diff_lines_empty_content(self):
        """Test rendering with empty line content."""
        diff_lines = [
            DiffLine(tag='equal', line_content='', line_number=1)
        ]
        
        result = self.diff_renderer.render_diff_lines(diff_lines)
        assert isinstance(result, Text)
        # Should handle empty content gracefully

    def test_render_diff_lines_whitespace_only(self):
        """Test rendering with whitespace-only content."""
        diff_lines = [
            DiffLine(tag='modify', line_content='    ', line_number=1),
            DiffLine(tag='add', line_content='\t\t', line_number=2)
        ]
        
        result = self.diff_renderer.render_diff_lines(diff_lines)
        assert isinstance(result, Text)
        # Should preserve whitespace in rendering