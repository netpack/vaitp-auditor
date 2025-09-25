"""
Unit tests for the FileSystemSource data source implementation.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock, mock_open
from io import StringIO

from vaitp_auditor.data_sources.filesystem import FileSystemSource
from vaitp_auditor.data_sources.base import DataSourceValidationError
from vaitp_auditor.core.models import CodePair


class TestFileSystemSource:
    """Test the FileSystemSource implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fs_source = FileSystemSource()

    def test_initialization(self):
        """Test proper initialization."""
        assert self.fs_source.generated_folder is None
        assert self.fs_source.expected_folder is None
        assert self.fs_source._file_pairs == []
        assert not self.fs_source.is_configured

    def test_get_base_name_simple(self):
        """Test base name extraction for simple files."""
        # Create a temporary directory structure for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self.fs_source.generated_folder = temp_path
            
            file_path = temp_path / "test_file.py"
            base_name = self.fs_source._get_base_name(file_path)
            assert base_name == "test_file"

    def test_get_base_name_nested(self):
        """Test base name extraction for nested files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self.fs_source.generated_folder = temp_path
            
            file_path = temp_path / "subdir" / "nested_file.js"
            base_name = self.fs_source._get_base_name(file_path)
            assert base_name == "subdir/nested_file"

    def test_is_code_file_valid_extensions(self):
        """Test code file detection with valid extensions."""
        valid_files = [
            Path("test.py"), Path("script.js"), Path("app.ts"),
            Path("Main.java"), Path("program.cpp"), Path("header.h"),
            Path("style.css"), Path("data.json"), Path("config.yaml"),
            Path("readme.md"), Path("notes.txt")
        ]
        
        for file_path in valid_files:
            assert self.fs_source._is_code_file(file_path), f"{file_path} should be recognized as code file"

    def test_is_code_file_invalid_extensions(self):
        """Test code file detection with invalid extensions."""
        invalid_files = [
            Path("image.png"), Path("document.pdf"), Path("archive.zip"),
            Path("binary.exe"), Path("data.bin")
        ]
        
        for file_path in invalid_files:
            assert not self.fs_source._is_code_file(file_path), f"{file_path} should not be recognized as code file"

    def test_get_file_identifier_simple(self):
        """Test file identifier generation."""
        generated_file = Path("/path/to/test_file.py")
        expected_file = Path("/other/path/test_file.py")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self.fs_source.generated_folder = temp_path
            
            # Create the file structure
            generated_file = temp_path / "test_file.py"
            
            identifier = self.fs_source._get_file_identifier(generated_file, expected_file)
            assert identifier == "test_file"

    def test_get_file_identifier_with_special_chars(self):
        """Test file identifier generation with special characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self.fs_source.generated_folder = temp_path
            
            generated_file = temp_path / "test file with spaces.py"
            
            identifier = self.fs_source._get_file_identifier(generated_file, None)
            assert identifier == "test_file_with_spaces"

    @patch('builtins.open', mock_open(read_data="test content"))
    def test_read_file_with_fallback_utf8_success(self):
        """Test successful UTF-8 file reading."""
        file_path = Path("test.py")
        
        content = self.fs_source._read_file_with_fallback(file_path)
        assert content == "test content"

    @patch('builtins.open')
    def test_read_file_with_fallback_encoding_error(self, mock_file):
        """Test file reading with encoding fallback."""
        # First call (UTF-8) raises UnicodeDecodeError, second call (latin-1) succeeds
        mock_file.side_effect = [
            UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte'),
            mock_open(read_data="fallback content").return_value
        ]
        
        # Mock the _handle_encoding_error method to return fallback content
        self.fs_source._handle_encoding_error = Mock(return_value="fallback content")
        
        file_path = Path("test.py")
        content = self.fs_source._read_file_with_fallback(file_path)
        assert content == "fallback content"

    @patch('builtins.open')
    def test_read_file_with_fallback_complete_failure(self, mock_file):
        """Test file reading complete failure."""
        mock_file.side_effect = IOError("File not found")
        
        file_path = Path("nonexistent.py")
        content = self.fs_source._read_file_with_fallback(file_path)
        assert content is None

    def test_discover_file_pairs_no_folders(self):
        """Test file discovery with no folders configured."""
        self.fs_source._discover_file_pairs()
        assert self.fs_source._file_pairs == []

    def test_discover_file_pairs_generated_only(self):
        """Test file discovery with only generated folder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "file1.py").write_text("content1")
            (temp_path / "file2.js").write_text("content2")
            (temp_path / "subdir").mkdir()
            (temp_path / "subdir" / "file3.py").write_text("content3")
            
            self.fs_source.generated_folder = temp_path
            self.fs_source._discover_file_pairs()
            
            assert len(self.fs_source._file_pairs) == 3
            # All expected files should be None
            assert all(expected is None for _, expected in self.fs_source._file_pairs)

    def test_discover_file_pairs_with_matching(self):
        """Test file discovery with matching between folders."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            generated_dir = temp_path / "generated"
            expected_dir = temp_path / "expected"
            
            generated_dir.mkdir()
            expected_dir.mkdir()
            
            # Create matching files
            (generated_dir / "file1.py").write_text("generated1")
            (expected_dir / "file1.py").write_text("expected1")
            
            # Create non-matching file
            (generated_dir / "file2.py").write_text("generated2")
            
            # Create expected file without generated counterpart
            (expected_dir / "file3.py").write_text("expected3")
            
            self.fs_source.generated_folder = generated_dir
            self.fs_source.expected_folder = expected_dir
            self.fs_source._discover_file_pairs()
            
            assert len(self.fs_source._file_pairs) == 2  # Only generated files create pairs
            
            # Check that file1 has a match and file2 doesn't
            pairs_dict = {self.fs_source._get_base_name(gen): exp for gen, exp in self.fs_source._file_pairs}
            assert pairs_dict["file1"] is not None
            assert pairs_dict["file2"] is None

    @patch('builtins.input')
    def test_configure_success_generated_only(self, mock_input):
        """Test successful configuration with generated folder only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()
            (temp_path / "test.py").write_text("test content")
            
            mock_input.side_effect = [str(temp_path), ""]  # generated path, empty expected path
            
            result = self.fs_source.configure()
            
            assert result is True
            assert self.fs_source.is_configured
            assert self.fs_source.generated_folder == temp_path
            assert self.fs_source.expected_folder is None
            assert len(self.fs_source._file_pairs) == 1

    @patch('builtins.input')
    def test_configure_success_both_folders(self, mock_input):
        """Test successful configuration with both folders."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()
            generated_dir = temp_path / "generated"
            expected_dir = temp_path / "expected"
            
            generated_dir.mkdir()
            expected_dir.mkdir()
            (generated_dir / "test.py").write_text("generated")
            (expected_dir / "test.py").write_text("expected")
            
            mock_input.side_effect = [str(generated_dir), str(expected_dir)]
            
            result = self.fs_source.configure()
            
            assert result is True
            assert self.fs_source.is_configured
            assert self.fs_source.generated_folder == generated_dir.resolve()
            assert self.fs_source.expected_folder == expected_dir.resolve()
            assert len(self.fs_source._file_pairs) == 1

    @patch('builtins.input')
    def test_configure_nonexistent_generated_folder(self, mock_input):
        """Test configuration with nonexistent generated folder."""
        nonexistent_path = "/path/that/does/not/exist"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "test.py").write_text("test")
            
            # First try nonexistent path, then valid path, then empty expected
            mock_input.side_effect = [nonexistent_path, str(temp_path), ""]
            
            with patch('builtins.print') as mock_print:
                result = self.fs_source.configure()
                
                assert result is True
                # Should have printed error message for nonexistent path
                error_calls = [call for call in mock_print.call_args_list 
                             if "does not exist" in str(call)]
                assert len(error_calls) > 0

    @patch('builtins.input')
    def test_configure_empty_generated_folder(self, mock_input):
        """Test configuration with empty generated folder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Don't create any files - empty directory
            
            mock_input.side_effect = [str(temp_path), ""]
            
            with patch('builtins.print') as mock_print:
                result = self.fs_source.configure()
                
                assert result is False
                # Should have printed error about no files found
                error_calls = [call for call in mock_print.call_args_list 
                             if "No code files found" in str(call)]
                assert len(error_calls) > 0

    @patch('builtins.input')
    def test_configure_keyboard_interrupt(self, mock_input):
        """Test configuration cancellation with keyboard interrupt."""
        mock_input.side_effect = KeyboardInterrupt()
        
        with patch('builtins.print') as mock_print:
            result = self.fs_source.configure()
            
            assert result is False
            # Should have printed cancellation message
            cancel_calls = [call for call in mock_print.call_args_list 
                           if "cancelled" in str(call)]
            assert len(cancel_calls) > 0

    def test_load_data_not_configured(self):
        """Test load_data fails when not configured."""
        with pytest.raises(RuntimeError, match="FileSystemSource is not properly configured"):
            self.fs_source.load_data(50)

    def test_load_data_invalid_sample_percentage(self):
        """Test load_data validates sample percentage."""
        self.fs_source._configured = True
        
        with pytest.raises(ValueError, match="sample_percentage must be between 1 and 100"):
            self.fs_source.load_data(0)

    def test_load_data_success(self):
        """Test successful data loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "file1.py").write_text("print('hello')")
            (temp_path / "file2.js").write_text("console.log('world')")
            
            self.fs_source.generated_folder = temp_path
            self.fs_source.expected_folder = None
            self.fs_source._discover_file_pairs()
            self.fs_source._configured = True
            
            result = self.fs_source.load_data(100)
            
            assert len(result) == 2
            assert all(isinstance(pair, CodePair) for pair in result)
            assert all(pair.expected_code is None for pair in result)
            assert all(pair.generated_code is not None for pair in result)

    def test_load_data_with_sampling(self):
        """Test data loading with sampling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple test files
            for i in range(10):
                (temp_path / f"file{i}.py").write_text(f"print({i})")
            
            self.fs_source.generated_folder = temp_path
            self.fs_source.expected_folder = None
            self.fs_source._discover_file_pairs()
            self.fs_source._configured = True
            
            # Test 50% sampling
            result = self.fs_source.load_data(50)
            assert len(result) == 5
            
            # Test 20% sampling
            result = self.fs_source.load_data(20)
            assert len(result) == 2

    def test_load_data_no_valid_pairs(self):
        """Test load_data when no valid pairs can be created."""
        # Configure with empty file pairs
        self.fs_source._configured = True
        self.fs_source._file_pairs = []
        
        with pytest.raises(DataSourceValidationError, match="No valid code pairs could be loaded"):
            self.fs_source.load_data(100)

    def test_get_total_count_not_configured(self):
        """Test get_total_count fails when not configured."""
        with pytest.raises(RuntimeError, match="FileSystemSource is not properly configured"):
            self.fs_source.get_total_count()

    def test_get_total_count_success(self):
        """Test successful total count retrieval."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "file1.py").write_text("content1")
            (temp_path / "file2.py").write_text("content2")
            
            self.fs_source.generated_folder = temp_path
            self.fs_source._discover_file_pairs()
            self.fs_source._configured = True
            
            count = self.fs_source.get_total_count()
            assert count == 2


class TestFileSystemSourceIntegration:
    """Integration tests for FileSystemSource."""

    def test_full_workflow_generated_only(self):
        """Test complete workflow with generated folder only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "test1.py").write_text("def func1(): pass")
            (temp_path / "test2.js").write_text("function func2() {}")
            (temp_path / "subdir").mkdir()
            (temp_path / "subdir" / "test3.py").write_text("class Test: pass")
            
            fs_source = FileSystemSource()
            
            # Mock user input for configuration
            with patch('builtins.input', side_effect=[str(temp_path), ""]):
                with patch('builtins.print'):  # Suppress output
                    assert fs_source.configure() is True
            
            # Test total count
            assert fs_source.get_total_count() == 3
            
            # Test full data loading
            full_data = fs_source.load_data(100)
            assert len(full_data) == 3
            assert all(pair.expected_code is None for pair in full_data)
            assert all(pair.generated_code is not None for pair in full_data)
            
            # Test sampled data loading
            sampled_data = fs_source.load_data(50)
            assert len(sampled_data) == 1  # 50% of 3 = 1.5, rounded to 1

    def test_full_workflow_with_matching(self):
        """Test complete workflow with matching between folders."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            generated_dir = temp_path / "generated"
            expected_dir = temp_path / "expected"
            
            generated_dir.mkdir()
            expected_dir.mkdir()
            
            # Create matching files
            (generated_dir / "test1.py").write_text("def generated_func(): pass")
            (expected_dir / "test1.py").write_text("def expected_func(): pass")
            
            # Create non-matching file
            (generated_dir / "test2.py").write_text("def another_func(): pass")
            
            fs_source = FileSystemSource()
            
            # Mock user input for configuration
            with patch('builtins.input', side_effect=[str(generated_dir), str(expected_dir)]):
                with patch('builtins.print'):  # Suppress output
                    assert fs_source.configure() is True
            
            # Test data loading
            data = fs_source.load_data(100)
            assert len(data) == 2
            
            # Find the matched pair
            matched_pair = next((pair for pair in data if pair.expected_code is not None), None)
            assert matched_pair is not None
            assert "expected_func" in matched_pair.expected_code
            assert "generated_func" in matched_pair.generated_code
            
            # Find the unmatched pair
            unmatched_pair = next((pair for pair in data if pair.expected_code is None), None)
            assert unmatched_pair is not None
            assert "another_func" in unmatched_pair.generated_code