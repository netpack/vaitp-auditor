"""
Unit tests for the CodeDiffer class.
"""

import unittest
from vaitp_auditor.core.differ import CodeDiffer
from vaitp_auditor.core.models import DiffLine


class TestCodeDiffer(unittest.TestCase):
    """Test cases for CodeDiffer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.differ = CodeDiffer()
    
    def test_identical_code(self):
        """Test diff computation with identical code."""
        code = "def hello():\n    print('Hello, World!')\n    return True"
        
        result = self.differ.compute_diff(code, code)
        
        # All lines should be marked as equal
        self.assertEqual(len(result), 3)
        for diff_line in result:
            self.assertEqual(diff_line.tag, 'equal')
        
        # Check specific content
        self.assertEqual(result[0].line_content, "def hello():")
        self.assertEqual(result[1].line_content, "    print('Hello, World!')")
        self.assertEqual(result[2].line_content, "    return True")
    
    def test_empty_expected_code(self):
        """Test diff computation when expected code is None."""
        generated = "def new_function():\n    pass"
        
        result = self.differ.compute_diff(None, generated)
        
        # All lines should be marked as added
        self.assertEqual(len(result), 2)
        for diff_line in result:
            self.assertEqual(diff_line.tag, 'add')
        
        self.assertEqual(result[0].line_content, "def new_function():")
        self.assertEqual(result[1].line_content, "    pass")
    
    def test_empty_generated_code(self):
        """Test diff computation when generated code is empty."""
        expected = "def old_function():\n    pass"
        
        result = self.differ.compute_diff(expected, "")
        
        # All lines should be marked as removed
        self.assertEqual(len(result), 2)
        for diff_line in result:
            self.assertEqual(diff_line.tag, 'remove')
        
        self.assertEqual(result[0].line_content, "def old_function():")
        self.assertEqual(result[1].line_content, "    pass")
    
    def test_both_empty(self):
        """Test diff computation when both codes are empty."""
        result = self.differ.compute_diff("", "")
        
        # Should return empty list
        self.assertEqual(len(result), 0)
    
    def test_line_addition(self):
        """Test diff computation with added lines."""
        expected = "def hello():\n    print('Hello')"
        generated = "def hello():\n    print('Hello')\n    print('World')"
        
        result = self.differ.compute_diff(expected, generated)
        
        # Should have 2 equal lines and 1 added line
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].tag, 'equal')
        self.assertEqual(result[1].tag, 'equal')
        self.assertEqual(result[2].tag, 'add')
        self.assertEqual(result[2].line_content, "    print('World')")
    
    def test_line_removal(self):
        """Test diff computation with removed lines."""
        expected = "def hello():\n    print('Hello')\n    print('World')"
        generated = "def hello():\n    print('Hello')"
        
        result = self.differ.compute_diff(expected, generated)
        
        # Should have 2 equal lines and 1 removed line
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].tag, 'equal')
        self.assertEqual(result[1].tag, 'equal')
        self.assertEqual(result[2].tag, 'remove')
        self.assertEqual(result[2].line_content, "    print('World')")
    
    def test_line_modification(self):
        """Test diff computation with modified lines."""
        expected = "def hello():\n    print('Hello, World!')"
        generated = "def hello():\n    print('Hello, Universe!')"
        
        result = self.differ.compute_diff(expected, generated)
        
        # Should have 1 equal line, 1 removed line, and 1 added line
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].tag, 'equal')
        self.assertEqual(result[1].tag, 'remove')
        self.assertEqual(result[1].line_content, "    print('Hello, World!')")
        self.assertEqual(result[2].tag, 'add')
        self.assertEqual(result[2].line_content, "    print('Hello, Universe!')")
    
    def test_complex_changes(self):
        """Test diff computation with multiple types of changes."""
        expected = """def calculate(a, b):
    result = a + b
    print(f"Result: {result}")
    return result"""
        
        generated = """def calculate(x, y):
    # Added comment
    result = x * y
    print(f"Product: {result}")
    log_result(result)
    return result"""
        
        result = self.differ.compute_diff(expected, generated)
        
        # Verify we have the expected mix of operations
        tags = [diff_line.tag for diff_line in result]
        self.assertIn('equal', tags)  # return result line should be equal
        self.assertIn('remove', tags)  # original lines removed
        self.assertIn('add', tags)    # new lines added
        
        # Check that return statement is preserved
        return_lines = [dl for dl in result if 'return result' in dl.line_content]
        self.assertTrue(len(return_lines) > 0)
    
    def test_whitespace_differences(self):
        """Test diff computation with whitespace-only differences."""
        expected = "def hello():\n    print('Hello')"
        generated = "def hello():\n        print('Hello')"  # Extra spaces
        
        result = self.differ.compute_diff(expected, generated)
        
        # Should detect the whitespace difference
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].tag, 'equal')  # Function definition unchanged
        self.assertEqual(result[1].tag, 'remove')  # Original indentation
        self.assertEqual(result[2].tag, 'add')     # New indentation
    
    def test_line_numbers(self):
        """Test that line numbers are assigned correctly."""
        expected = "line1\nline2\nline3"
        generated = "line1\nmodified_line2\nline3"
        
        result = self.differ.compute_diff(expected, generated)
        
        # Check line number assignment
        for i, diff_line in enumerate(result, 1):
            self.assertEqual(diff_line.line_number, i)
    
    def test_get_diff_text_identical(self):
        """Test unified diff text generation with identical code."""
        code = "def hello():\n    print('Hello')"
        
        diff_text = self.differ.get_diff_text(code, code)
        
        # Identical code should produce empty diff
        self.assertEqual(diff_text, "")
    
    def test_get_diff_text_with_changes(self):
        """Test unified diff text generation with changes."""
        expected = "def hello():\n    print('Hello')"
        generated = "def hello():\n    print('Hi')"
        
        diff_text = self.differ.get_diff_text(expected, generated)
        
        # Should contain unified diff markers
        self.assertIn("--- expected_code", diff_text)
        self.assertIn("+++ generated_code", diff_text)
        self.assertIn("-    print('Hello')", diff_text)
        self.assertIn("+    print('Hi')", diff_text)
    
    def test_get_diff_text_none_expected(self):
        """Test unified diff text generation when expected is None."""
        generated = "def new_function():\n    pass"
        
        diff_text = self.differ.get_diff_text(None, generated)
        
        # Should show all lines as additions
        self.assertIn("--- expected_code", diff_text)
        self.assertIn("+++ generated_code", diff_text)
        self.assertIn("+def new_function():", diff_text)
        self.assertIn("+    pass", diff_text)
    
    def test_edge_case_single_line(self):
        """Test diff computation with single line codes."""
        expected = "print('hello')"
        generated = "print('world')"
        
        result = self.differ.compute_diff(expected, generated)
        
        # Should have one removed and one added line
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].tag, 'remove')
        self.assertEqual(result[0].line_content, "print('hello')")
        self.assertEqual(result[1].tag, 'add')
        self.assertEqual(result[1].line_content, "print('world')")
    
    def test_edge_case_trailing_newlines(self):
        """Test diff computation with trailing newlines."""
        expected = "def hello():\n    pass\n"
        generated = "def hello():\n    pass"
        
        result = self.differ.compute_diff(expected, generated)
        
        # Should handle trailing newlines correctly
        self.assertTrue(len(result) >= 2)
        # First two lines should be equal
        self.assertEqual(result[0].tag, 'equal')
        self.assertEqual(result[1].tag, 'equal')
    
    def test_edge_case_unicode_content(self):
        """Test diff computation with unicode characters."""
        expected = "def greet():\n    print('Hello 世界')"
        generated = "def greet():\n    print('Hello 🌍')"
        
        result = self.differ.compute_diff(expected, generated)
        
        # Should handle unicode correctly
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].tag, 'equal')
        self.assertEqual(result[1].tag, 'remove')
        self.assertEqual(result[1].line_content, "    print('Hello 世界')")
        self.assertEqual(result[2].tag, 'add')
        self.assertEqual(result[2].line_content, "    print('Hello 🌍')")
    
    def test_large_code_blocks(self):
        """Test diff computation with larger code blocks."""
        # Generate larger code blocks
        expected_lines = [f"line_{i} = {i}" for i in range(100)]
        generated_lines = expected_lines.copy()
        # Modify some lines in the middle
        generated_lines[50] = "modified_line_50 = 999"
        generated_lines[75] = "modified_line_75 = 888"
        
        expected = "\n".join(expected_lines)
        generated = "\n".join(generated_lines)
        
        result = self.differ.compute_diff(expected, generated)
        
        # Should have mostly equal lines with some modifications
        equal_count = sum(1 for dl in result if dl.tag == 'equal')
        remove_count = sum(1 for dl in result if dl.tag == 'remove')
        add_count = sum(1 for dl in result if dl.tag == 'add')
        
        # Most lines should be equal
        self.assertGreater(equal_count, 90)
        # Should have 2 removals and 2 additions for the modifications
        self.assertEqual(remove_count, 2)
        self.assertEqual(add_count, 2)


if __name__ == '__main__':
    unittest.main()