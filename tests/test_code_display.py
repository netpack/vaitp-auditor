"""
Unit tests for code display components with syntax highlighting.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import customtkinter as ctk
from pygments.token import Token

from vaitp_auditor.gui.code_display import (
    SyntaxHighlighter, DiffHighlighter, CodePanel, EnhancedCodePanelsFrame
)
from vaitp_auditor.core.models import DiffLine, CodePair


class TestSyntaxHighlighter(unittest.TestCase):
    """Test cases for SyntaxHighlighter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.highlighter = SyntaxHighlighter()
    
    def test_init(self):
        """Test SyntaxHighlighter initialization."""
        self.assertIsInstance(self.highlighter._lexer_cache, dict)
        self.assertIsInstance(self.highlighter._token_style_cache, dict)
        self.assertIsInstance(self.highlighter._token_colors, dict)
        
        # Check that basic token colors are defined
        self.assertIn(Token.Keyword, self.highlighter._token_colors)
        self.assertIn(Token.String, self.highlighter._token_colors)
        self.assertIn(Token.Comment, self.highlighter._token_colors)
    
    def test_highlight_code_python(self):
        """Test syntax highlighting for Python code."""
        code = "def hello():\n    print('Hello, World!')\n    return True"
        
        result = self.highlighter.highlight_code(code, "python")
        
        # Should return list of (text, color) tuples
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        
        # Each item should be a tuple with text and color
        for text, color in result:
            self.assertIsInstance(text, str)
            self.assertIsInstance(color, str)
            self.assertTrue(color.startswith('#'))  # Should be hex color
    
    def test_highlight_code_empty(self):
        """Test syntax highlighting with empty code."""
        result = self.highlighter.highlight_code("", "python")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], ("", "#d4d4d4"))  # Default color
    
    def test_highlight_code_whitespace_only(self):
        """Test syntax highlighting with whitespace-only code."""
        result = self.highlighter.highlight_code("   \n  \t  ", "python")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], ("", "#d4d4d4"))  # Default color
    
    def test_highlight_code_invalid_language(self):
        """Test syntax highlighting with invalid language."""
        code = "def hello(): pass"
        
        # Should fallback gracefully
        result = self.highlighter.highlight_code(code, "invalid_language")
        
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
    
    @patch('vaitp_auditor.gui.code_display.get_lexer_by_name')
    def test_highlight_code_lexer_error(self, mock_get_lexer):
        """Test syntax highlighting when lexer fails."""
        mock_get_lexer.side_effect = Exception("Lexer error")
        
        code = "def hello(): pass"
        result = self.highlighter.highlight_code(code, "python")
        
        # Should fallback to plain text
        self.assertEqual(result, [(code, "#d4d4d4")])
    
    def test_get_token_color(self):
        """Test token color retrieval."""
        # Test exact match
        color = self.highlighter._get_token_color(Token.Keyword)
        self.assertEqual(color, "#569cd6")
        
        # Test default color for unknown token
        unknown_token = Token.Unknown
        color = self.highlighter._get_token_color(unknown_token)
        self.assertEqual(color, "#d4d4d4")
    
    def test_lexer_caching(self):
        """Test that lexers are properly cached."""
        code = "def test(): pass"
        
        # First call should create lexer
        self.highlighter.highlight_code(code, "python")
        self.assertIn("python", self.highlighter._lexer_cache)
        
        # Second call should use cached lexer
        cached_lexer = self.highlighter._lexer_cache["python"]
        self.highlighter.highlight_code(code, "python")
        self.assertIs(self.highlighter._lexer_cache["python"], cached_lexer)


class TestDiffHighlighter(unittest.TestCase):
    """Test cases for DiffHighlighter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.highlighter = DiffHighlighter()
    
    def test_init(self):
        """Test DiffHighlighter initialization."""
        self.assertIsInstance(self.highlighter.diff_colors, dict)
        
        # Check that diff colors are defined
        self.assertIn('add', self.highlighter.diff_colors)
        self.assertIn('remove', self.highlighter.diff_colors)
        self.assertIn('modify', self.highlighter.diff_colors)
        self.assertIn('equal', self.highlighter.diff_colors)
    
    @patch('customtkinter.CTkTextbox')
    def test_configure_diff_tags(self, mock_textbox_class):
        """Test diff tag configuration."""
        mock_textbox = Mock()
        
        self.highlighter.configure_diff_tags(mock_textbox)
        
        # Should configure tags for each diff type
        mock_textbox.tag_config.assert_any_call("diff_add", background='#2d4a2d')
        mock_textbox.tag_config.assert_any_call("diff_remove", background='#4a2d2d')
        mock_textbox.tag_config.assert_any_call("diff_modify", background='#4a4a2d')
    
    @patch('customtkinter.CTkTextbox')
    def test_apply_diff_tags(self, mock_textbox_class):
        """Test applying diff tags to textbox."""
        mock_textbox = Mock()
        
        diff_lines = [
            DiffLine(tag='add', line_content='+ added line', line_number=1),
            DiffLine(tag='remove', line_content='- removed line', line_number=2),
            DiffLine(tag='equal', line_content='  unchanged line', line_number=3),
        ]
        
        self.highlighter.apply_diff_tags(mock_textbox, diff_lines)
        
        # Should remove existing tags first
        mock_textbox.tag_remove.assert_any_call("diff_add", "1.0", "end")
        mock_textbox.tag_remove.assert_any_call("diff_remove", "1.0", "end")
        mock_textbox.tag_remove.assert_any_call("diff_modify", "1.0", "end")
        
        # Should add tags for add and remove lines (not equal)
        mock_textbox.tag_add.assert_any_call("diff_add", "1.0", "1.end")
        mock_textbox.tag_add.assert_any_call("diff_remove", "2.0", "2.end")
    
    @patch('vaitp_auditor.core.differ.CodeDiffer')
    def test_create_diff_view(self, mock_differ_class):
        """Test creating diff views for both panels."""
        # Mock the CodeDiffer
        mock_differ = Mock()
        mock_differ_class.return_value = mock_differ
        
        # Mock diff computation result
        mock_diff_lines = [
            DiffLine(tag='equal', line_content='def function():', line_number=1),
            DiffLine(tag='remove', line_content='    old_line = True', line_number=2),
            DiffLine(tag='add', line_content='    new_line = False', line_number=3),
        ]
        mock_differ.compute_diff.return_value = mock_diff_lines
        
        expected_code = "def function():\n    old_line = True"
        generated_code = "def function():\n    new_line = False"
        
        expected_diff, generated_diff = self.highlighter.create_diff_view(expected_code, generated_code)
        
        # Should call CodeDiffer.compute_diff
        mock_differ.compute_diff.assert_called_once_with(expected_code, generated_code)
        
        # Should return appropriate diff lines for each panel
        self.assertEqual(len(expected_diff), 2)  # equal + remove
        self.assertEqual(len(generated_diff), 2)  # equal + add
        
        # Check expected panel diff lines
        self.assertEqual(expected_diff[0].tag, 'equal')
        self.assertEqual(expected_diff[1].tag, 'remove')
        
        # Check generated panel diff lines
        self.assertEqual(generated_diff[0].tag, 'equal')
        self.assertEqual(generated_diff[1].tag, 'add')
    
    def test_apply_diff_to_panels(self):
        """Test applying diff highlighting to both panels."""
        mock_expected_panel = Mock()
        mock_generated_panel = Mock()
        
        expected_code = "def old_function(): pass"
        generated_code = "def new_function(): pass"
        
        # Should not raise exception even if diff computation fails
        self.highlighter.apply_diff_to_panels(
            mock_expected_panel, mock_generated_panel, expected_code, generated_code
        )


class TestCodePanel(unittest.TestCase):
    """Test cases for CodePanel class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock parent frame
        self.mock_parent = Mock()
        
        # Mock all CTkTextbox methods and CTkFont to avoid GUI dependencies
        with patch('customtkinter.CTkTextbox.__init__', return_value=None):
            with patch('customtkinter.CTkTextbox.delete'):
                with patch('customtkinter.CTkTextbox.insert'):
                    with patch('customtkinter.CTkTextbox.tag_config'):
                        with patch('customtkinter.CTkTextbox.tag_add'):
                            with patch('customtkinter.CTkTextbox.tag_remove'):
                                with patch('customtkinter.CTkTextbox.index'):
                                    with patch('customtkinter.CTkFont'):
                                        self.panel = CodePanel(self.mock_parent, "Test Panel")
    
    def test_init(self):
        """Test CodePanel initialization."""
        self.assertEqual(self.panel.title, "Test Panel")
        self.assertIsInstance(self.panel._syntax_highlighter, SyntaxHighlighter)
        self.assertIsInstance(self.panel._diff_highlighter, DiffHighlighter)
        self.assertEqual(self.panel._current_language, "python")
        self.assertFalse(self.panel._has_syntax_highlighting)
    
    @patch('customtkinter.CTkTextbox.delete')
    @patch('customtkinter.CTkTextbox.insert')
    def test_set_code_content_empty(self, mock_insert, mock_delete):
        """Test setting empty code content."""
        self.panel.set_code_content("", "python")
        
        mock_delete.assert_called_with("1.0", "end")
        mock_insert.assert_called_with("1.0", "# No code available")
    
    @patch('customtkinter.CTkTextbox.delete')
    @patch('customtkinter.CTkTextbox.insert')
    @patch('customtkinter.CTkTextbox.tag_config')
    @patch('customtkinter.CTkTextbox.tag_add')
    @patch('customtkinter.CTkTextbox.index')
    def test_set_code_content_with_syntax(self, mock_index, mock_tag_add, 
                                         mock_tag_config, mock_insert, mock_delete):
        """Test setting code content with syntax highlighting."""
        mock_index.side_effect = ["1.0", "1.3", "1.3", "1.6"]  # Mock positions
        
        code = "def test(): pass"
        self.panel.set_code_content(code, "python", apply_syntax=True)
        
        mock_delete.assert_called_with("1.0", "end")
        self.assertEqual(self.panel._current_language, "python")
        self.assertTrue(self.panel._has_syntax_highlighting)
    
    @patch('customtkinter.CTkTextbox.delete')
    @patch('customtkinter.CTkTextbox.insert')
    def test_set_code_content_plain_text(self, mock_insert, mock_delete):
        """Test setting code content as plain text."""
        code = "def test(): pass"
        self.panel.set_code_content(code, "python", apply_syntax=False)
        
        mock_delete.assert_called_with("1.0", "end")
        mock_insert.assert_called_with("1.0", code)
        self.assertFalse(self.panel._has_syntax_highlighting)
    
    @patch('customtkinter.CTkTextbox.delete')
    def test_clear_content(self, mock_delete):
        """Test clearing panel content."""
        self.panel.clear_content()
        
        mock_delete.assert_called_with("1.0", "end")
        self.assertFalse(self.panel._has_syntax_highlighting)
    
    def test_get_current_language(self):
        """Test getting current language."""
        self.panel._current_language = "javascript"
        self.assertEqual(self.panel.get_current_language(), "javascript")
    
    def test_has_syntax_highlighting(self):
        """Test checking syntax highlighting status."""
        self.panel._has_syntax_highlighting = True
        self.assertTrue(self.panel.has_syntax_highlighting())
        
        self.panel._has_syntax_highlighting = False
        self.assertFalse(self.panel.has_syntax_highlighting())


class TestEnhancedCodePanelsFrame(unittest.TestCase):
    """Test cases for EnhancedCodePanelsFrame class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_parent = Mock()
        
        # Mock the frame and panel creation
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            with patch('customtkinter.CTkFrame.grid_columnconfigure'):
                with patch('customtkinter.CTkFrame.grid_rowconfigure'):
                    with patch('customtkinter.CTkLabel'):
                        with patch('vaitp_auditor.gui.code_display.CodePanel') as mock_panel:
                            mock_panel.return_value = Mock()
                            self.frame = EnhancedCodePanelsFrame(self.mock_parent)
    
    def test_init(self):
        """Test EnhancedCodePanelsFrame initialization."""
        self.assertIsNotNone(self.frame.expected_panel)
        self.assertIsNotNone(self.frame.generated_panel)
    
    def test_load_code_pair(self):
        """Test loading a code pair."""
        code_pair = CodePair(
            identifier="test_1",
            expected_code="def expected(): pass",
            generated_code="def generated(): pass",
            source_info={}
        )
        
        self.frame.load_code_pair(code_pair, "python", True)
        
        # Should call set_code_content on both panels
        self.frame.expected_panel.set_code_content.assert_called_with(
            "def expected(): pass", "python", True
        )
        self.frame.generated_panel.set_code_content.assert_called_with(
            "def generated(): pass", "python", True
        )
    
    def test_load_code_pair_no_expected(self):
        """Test loading a code pair with no expected code."""
        code_pair = CodePair(
            identifier="test_1",
            expected_code=None,
            generated_code="def generated(): pass",
            source_info={}
        )
        
        self.frame.load_code_pair(code_pair, "python", True)
        
        # Should use fallback text for expected code
        self.frame.expected_panel.set_code_content.assert_called_with(
            "# No expected code available", "python", True
        )
    
    def test_apply_diff_highlighting(self):
        """Test applying diff highlighting."""
        expected_diff = [DiffLine(tag='remove', line_content='old line', line_number=1)]
        generated_diff = [DiffLine(tag='add', line_content='new line', line_number=1)]
        
        self.frame.apply_diff_highlighting(expected_diff, generated_diff)
        
        # Should call apply_diff_highlighting on both panels
        self.frame.expected_panel.apply_diff_highlighting.assert_called_with(expected_diff)
        self.frame.generated_panel.apply_diff_highlighting.assert_called_with(generated_diff)
    
    def test_clear_content(self):
        """Test clearing content from both panels."""
        self.frame.clear_content()
        
        # Should call clear_content on both panels
        self.frame.expected_panel.clear_content.assert_called_once()
        self.frame.generated_panel.clear_content.assert_called_once()
    
    def test_load_code_pair_with_diff(self):
        """Test loading a code pair with diff highlighting enabled."""
        code_pair = CodePair(
            identifier="test_1",
            expected_code="def expected(): pass",
            generated_code="def generated(): pass",
            source_info={}
        )
        
        with patch.object(self.frame, 'apply_diff_highlighting_from_code_pair') as mock_diff:
            self.frame.load_code_pair(code_pair, "python", True, True)
            
            # Should call diff highlighting
            mock_diff.assert_called_once_with(code_pair)
    
    def test_load_code_pair_without_diff(self):
        """Test loading a code pair with diff highlighting disabled."""
        code_pair = CodePair(
            identifier="test_1",
            expected_code="def expected(): pass",
            generated_code="def generated(): pass",
            source_info={}
        )
        
        with patch.object(self.frame, 'apply_diff_highlighting_from_code_pair') as mock_diff:
            self.frame.load_code_pair(code_pair, "python", True, False)
            
            # Should not call diff highlighting
            mock_diff.assert_not_called()
    
    @patch('vaitp_auditor.gui.code_display.DiffHighlighter')
    def test_apply_diff_highlighting_from_code_pair(self, mock_diff_highlighter_class):
        """Test applying diff highlighting from a code pair."""
        mock_diff_highlighter = Mock()
        mock_diff_highlighter_class.return_value = mock_diff_highlighter
        
        code_pair = CodePair(
            identifier="test_1",
            expected_code="def expected(): pass",
            generated_code="def generated(): pass",
            source_info={}
        )
        
        self.frame.apply_diff_highlighting_from_code_pair(code_pair)
        
        # Should create DiffHighlighter and call apply_diff_to_panels
        mock_diff_highlighter_class.assert_called_once()
        mock_diff_highlighter.apply_diff_to_panels.assert_called_once_with(
            self.frame.expected_panel,
            self.frame.generated_panel,
            "def expected(): pass",
            "def generated(): pass"
        )


class TestCodePanelScrolling(unittest.TestCase):
    """Test cases for CodePanel scrolling and navigation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_parent = Mock()
        
        # Mock all necessary methods for scrolling tests
        with patch('customtkinter.CTkTextbox.__init__', return_value=None):
            with patch('customtkinter.CTkTextbox.bind'):
                with patch('customtkinter.CTkTextbox.see'):
                    with patch('customtkinter.CTkTextbox.mark_set'):
                        with patch('customtkinter.CTkTextbox.index', return_value="1.0"):
                            with patch('customtkinter.CTkTextbox.xview', return_value=(0.0, 1.0)):
                                with patch('customtkinter.CTkTextbox.yview', return_value=(0.0, 1.0)):
                                    with patch('customtkinter.CTkTextbox.xview_moveto'):
                                        with patch('customtkinter.CTkTextbox.yview_moveto'):
                                            with patch('customtkinter.CTkTextbox.winfo_height', return_value=400):
                                                with patch('customtkinter.CTkTextbox.tag_config'):
                                                    with patch('customtkinter.CTkFont'):
                                                        self.panel = CodePanel(self.mock_parent, "Test Panel")
    
    def test_scroll_to_line(self):
        """Test scrolling to a specific line."""
        with patch.object(self.panel, 'see') as mock_see:
            with patch.object(self.panel, 'mark_set') as mock_mark_set:
                self.panel.scroll_to_line(10)
                
                mock_see.assert_called_with("10.0")
                mock_mark_set.assert_called_with("insert", "10.0")
    
    def test_get_scroll_position(self):
        """Test getting scroll position."""
        with patch.object(self.panel, 'xview', return_value=(0.2, 0.8)):
            with patch.object(self.panel, 'yview', return_value=(0.1, 0.9)):
                position = self.panel.get_scroll_position()
                
                self.assertEqual(position["x"], 0.2)
                self.assertEqual(position["y"], 0.1)
    
    def test_set_scroll_position(self):
        """Test setting scroll position."""
        with patch.object(self.panel, 'xview_moveto') as mock_x:
            with patch.object(self.panel, 'yview_moveto') as mock_y:
                self.panel.set_scroll_position(0.3, 0.4)
                
                mock_x.assert_called_with(0.3)
                mock_y.assert_called_with(0.4)
    
    def test_get_visible_range(self):
        """Test getting visible line range."""
        with patch.object(self.panel, 'index') as mock_index:
            with patch.object(self.panel, 'winfo_height', return_value=400):
                mock_index.side_effect = ["5.0", "15.0"]
                
                first, last = self.panel.get_visible_range()
                
                self.assertEqual(first, 5)
                self.assertEqual(last, 15)
    
    def test_navigation_key_bindings(self):
        """Test that navigation key bindings are set up."""
        with patch.object(self.panel, 'bind') as mock_bind:
            self.panel._setup_scrolling_and_navigation()
            
            # Check that key bindings were set up
            expected_bindings = [
                "<Control-Home>", "<Control-End>", "<Control-Up>", "<Control-Down>",
                "<Control-Left>", "<Control-Right>", "<Page_Up>", "<Page_Down>",
                "<MouseWheel>", "<Button-4>", "<Button-5>", "<Shift-MouseWheel>"
            ]
            
            for binding in expected_bindings:
                mock_bind.assert_any_call(binding, unittest.mock.ANY)


class TestEnhancedCodePanelsFrameScrolling(unittest.TestCase):
    """Test cases for EnhancedCodePanelsFrame scrolling functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_parent = Mock()
        
        # Mock the frame and panel creation with scrolling support
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            with patch('customtkinter.CTkFrame.grid_columnconfigure'):
                with patch('customtkinter.CTkFrame.grid_rowconfigure'):
                    with patch('customtkinter.CTkLabel'):
                        with patch('customtkinter.CTkFont'):
                            with patch('vaitp_auditor.gui.code_display.CodePanel') as mock_panel:
                                mock_panel.return_value = Mock()
                                with patch.object(EnhancedCodePanelsFrame, '_setup_synchronized_scrolling'):
                                    self.frame = EnhancedCodePanelsFrame(self.mock_parent)
    
    def test_synchronized_scrolling_setup(self):
        """Test that synchronized scrolling is set up correctly."""
        self.assertTrue(hasattr(self.frame, '_synchronized_scrolling'))
        self.assertTrue(self.frame._synchronized_scrolling)
    
    def test_set_synchronized_scrolling(self):
        """Test enabling/disabling synchronized scrolling."""
        self.frame.set_synchronized_scrolling(False)
        self.assertFalse(self.frame.is_synchronized_scrolling_enabled())
        
        self.frame.set_synchronized_scrolling(True)
        self.assertTrue(self.frame.is_synchronized_scrolling_enabled())
    
    def test_scroll_to_line_both_panels(self):
        """Test scrolling both panels to a line."""
        self.frame.scroll_to_line(20)
        
        # Should call scroll_to_line on both panels
        self.frame.expected_panel.scroll_to_line.assert_called_with(20)
        self.frame.generated_panel.scroll_to_line.assert_called_with(20)
    
    def test_get_visible_range_from_expected(self):
        """Test getting visible range from expected panel."""
        self.frame.expected_panel.get_visible_range.return_value = (5, 25)
        
        result = self.frame.get_visible_range()
        
        self.assertEqual(result, (5, 25))
        self.frame.expected_panel.get_visible_range.assert_called_once()


class TestSyntaxHighlightingIntegration(unittest.TestCase):
    """Integration tests for syntax highlighting functionality."""
    
    def test_syntax_highlighting_fallback(self):
        """Test that syntax highlighting falls back gracefully on errors."""
        highlighter = SyntaxHighlighter()
        
        # Test with malformed code that might cause lexer issues
        malformed_code = "def incomplete_function("
        
        # Should not raise exception
        result = highlighter.highlight_code(malformed_code, "python")
        
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
    
    def test_diff_highlighting_with_real_diff_lines(self):
        """Test diff highlighting with realistic diff data."""
        diff_highlighter = DiffHighlighter()
        
        # Create realistic diff lines
        diff_lines = [
            DiffLine(tag='equal', line_content='def function():', line_number=1),
            DiffLine(tag='remove', line_content='    old_code = True', line_number=2),
            DiffLine(tag='add', line_content='    new_code = False', line_number=3),
            DiffLine(tag='modify', line_content='    return result', line_number=4),
        ]
        
        # Mock textbox
        mock_textbox = Mock()
        
        # Should not raise exception
        diff_highlighter.apply_diff_tags(mock_textbox, diff_lines)
        
        # Verify that tags were applied
        self.assertTrue(mock_textbox.tag_add.called)
    
    def test_complete_code_display_workflow(self):
        """Test complete workflow with syntax highlighting, diff highlighting, and scrolling."""
        # This integration test verifies that all components work together
        
        # Create code pair
        code_pair = CodePair(
            identifier="test_integration",
            expected_code="def old_function():\n    return 'old'",
            generated_code="def new_function():\n    return 'new'",
            source_info={}
        )
        
        # Test that components can be created and used together
        syntax_highlighter = SyntaxHighlighter()
        diff_highlighter = DiffHighlighter()
        
        # Test syntax highlighting
        expected_highlighted = syntax_highlighter.highlight_code(code_pair.expected_code, "python")
        generated_highlighted = syntax_highlighter.highlight_code(code_pair.generated_code, "python")
        
        self.assertIsInstance(expected_highlighted, list)
        self.assertIsInstance(generated_highlighted, list)
        
        # Test diff computation
        expected_diff, generated_diff = diff_highlighter.create_diff_view(
            code_pair.expected_code, code_pair.generated_code
        )
        
        self.assertIsInstance(expected_diff, list)
        self.assertIsInstance(generated_diff, list)


if __name__ == '__main__':
    unittest.main()