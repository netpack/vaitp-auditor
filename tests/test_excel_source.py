"""
Unit tests for ExcelSource data source implementation.
"""

import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import patch, MagicMock
from vaitp_auditor.data_sources.excel import ExcelSource
from vaitp_auditor.data_sources.base import DataSourceError
from vaitp_auditor.core.models import CodePair


class TestExcelSource:
    """Test cases for ExcelSource class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.source = ExcelSource()
        self.temp_files = []

    def teardown_method(self):
        """Clean up test fixtures."""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def create_test_csv(self, with_data=True):
        """Create a temporary test CSV file."""
        fd, temp_file = tempfile.mkstemp(suffix='.csv')
        self.temp_files.append(temp_file)
        
        if with_data:
            # Create test data
            data = {
                'identifier': ['test_1', 'test_2', 'test_3', 'test_4', ''],
                'generated_code': ['print("gen1")', 'print("gen2")', 'print("gen3")', '', 'print("gen5")'],
                'expected_code': ['print("exp1")', 'print("exp2")', None, 'print("exp4")', 'print("exp5")'],
                'extra_column': ['extra1', 'extra2', 'extra3', 'extra4', 'extra5']
            }
            df = pd.DataFrame(data)
            df.to_csv(temp_file, index=False)
        else:
            # Create empty CSV with headers only
            df = pd.DataFrame(columns=['identifier', 'generated_code', 'expected_code'])
            df.to_csv(temp_file, index=False)
        
        os.close(fd)
        return temp_file

    def create_test_excel(self, with_data=True, multiple_sheets=False):
        """Create a temporary test Excel file."""
        fd, temp_file = tempfile.mkstemp(suffix='.xlsx')
        self.temp_files.append(temp_file)
        os.close(fd)
        
        if with_data:
            # Create test data
            data = {
                'identifier': ['test_1', 'test_2', 'test_3', 'test_4'],
                'generated_code': ['print("gen1")', 'print("gen2")', 'print("gen3")', 'print("gen4")'],
                'expected_code': ['print("exp1")', 'print("exp2")', None, 'print("exp4")'],
                'extra_column': ['extra1', 'extra2', 'extra3', 'extra4']
            }
            df = pd.DataFrame(data)
            
            if multiple_sheets:
                with pd.ExcelWriter(temp_file) as writer:
                    df.to_excel(writer, sheet_name='Sheet1', index=False)
                    df.to_excel(writer, sheet_name='Sheet2', index=False)
            else:
                df.to_excel(temp_file, index=False)
        else:
            # Create empty Excel with headers only
            df = pd.DataFrame(columns=['identifier', 'generated_code', 'expected_code'])
            df.to_excel(temp_file, index=False)
        
        return temp_file

    @patch('builtins.input')
    def test_configure_csv_success(self, mock_input):
        """Test successful configuration with CSV file."""
        csv_file = self.create_test_csv()
        
        # Mock user inputs
        mock_input.side_effect = [
            csv_file,  # File path
            '2',       # Generated code column
            '3',       # Expected code column
            '1'        # Identifier column
        ]
        
        result = self.source.configure()
        
        assert result is True
        assert self.source.is_configured
        assert self.source._file_path == csv_file
        assert self.source._sheet_name is None  # CSV files don't have sheets
        assert self.source._generated_code_column == 'generated_code'
        assert self.source._expected_code_column == 'expected_code'
        assert self.source._identifier_column == 'identifier'

    @patch('builtins.input')
    def test_configure_excel_single_sheet_success(self, mock_input):
        """Test successful configuration with single-sheet Excel file."""
        excel_file = self.create_test_excel()
        
        # Mock user inputs
        mock_input.side_effect = [
            excel_file,  # File path
            '2',         # Generated code column
            '3',         # Expected code column
            '1'          # Identifier column
        ]
        
        result = self.source.configure()
        
        assert result is True
        assert self.source.is_configured
        assert self.source._sheet_name is not None

    @patch('builtins.input')
    def test_configure_excel_multiple_sheets_success(self, mock_input):
        """Test successful configuration with multi-sheet Excel file."""
        excel_file = self.create_test_excel(multiple_sheets=True)
        
        # Mock user inputs
        mock_input.side_effect = [
            excel_file,  # File path
            '1',         # Sheet selection (Sheet1)
            '2',         # Generated code column
            '3',         # Expected code column
            '1'          # Identifier column
        ]
        
        result = self.source.configure()
        
        assert result is True
        assert self.source.is_configured
        assert self.source._sheet_name == 'Sheet1'

    @patch('builtins.input')
    def test_configure_with_optional_expected_code(self, mock_input):
        """Test configuration with optional expected code column."""
        csv_file = self.create_test_csv()
        
        # Mock user inputs (skip expected code column)
        mock_input.side_effect = [
            csv_file,  # File path
            '2',       # Generated code column
            '',        # Skip expected code column
            '1'        # Identifier column
        ]
        
        result = self.source.configure()
        
        assert result is True
        assert self.source.is_configured
        assert self.source._expected_code_column is None

    @patch('builtins.input')
    def test_configure_empty_file_path(self, mock_input):
        """Test configuration with empty file path."""
        mock_input.side_effect = ['']  # Empty file path
        
        result = self.source.configure()
        
        assert result is False
        assert not self.source.is_configured

    @patch('builtins.input')
    def test_configure_nonexistent_file(self, mock_input):
        """Test configuration with nonexistent file."""
        mock_input.side_effect = ['/nonexistent/file.xlsx']
        
        result = self.source.configure()
        
        assert result is False
        assert not self.source.is_configured

    @patch('builtins.input')
    def test_configure_unsupported_file_format(self, mock_input):
        """Test configuration with unsupported file format."""
        # Create a temporary text file
        fd, temp_file = tempfile.mkstemp(suffix='.txt')
        self.temp_files.append(temp_file)
        os.close(fd)
        
        mock_input.side_effect = [temp_file]
        
        result = self.source.configure()
        
        assert result is False
        assert not self.source.is_configured

    @patch('builtins.input')
    def test_configure_corrupted_excel_file(self, mock_input):
        """Test configuration with corrupted Excel file."""
        # Create a file with .xlsx extension but invalid content
        fd, temp_file = tempfile.mkstemp(suffix='.xlsx')
        self.temp_files.append(temp_file)
        
        with os.fdopen(fd, 'w') as f:
            f.write("This is not a valid Excel file")
        
        mock_input.side_effect = [temp_file]
        
        result = self.source.configure()
        
        assert result is False
        assert not self.source.is_configured

    def test_load_data_not_configured(self):
        """Test load_data when not configured."""
        with pytest.raises(RuntimeError, match="is not properly configured"):
            self.source.load_data(100)

    def test_load_data_invalid_sample_percentage(self):
        """Test load_data with invalid sample percentage."""
        self.source._configured = True
        
        with pytest.raises(ValueError, match="sample_percentage must be between 1 and 100"):
            self.source.load_data(0)
        
        with pytest.raises(ValueError, match="sample_percentage must be between 1 and 100"):
            self.source.load_data(101)

    @patch('builtins.input')
    def test_load_data_csv_success(self, mock_input):
        """Test successful data loading from CSV."""
        csv_file = self.create_test_csv()
        
        # Configure the source
        mock_input.side_effect = [
            csv_file, '2', '3', '1'
        ]
        self.source.configure()
        
        # Load data
        code_pairs = self.source.load_data(100)
        
        # Should get 3 valid pairs (excluding empty identifier and empty generated code)
        assert len(code_pairs) == 3
        
        # Check first code pair
        first_pair = code_pairs[0]
        assert isinstance(first_pair, CodePair)
        assert first_pair.identifier == 'test_1'
        assert first_pair.generated_code == 'print("gen1")'
        assert first_pair.expected_code == 'print("exp1")'
        assert first_pair.source_info['source_type'] == 'excel'

    @patch('builtins.input')
    def test_load_data_excel_success(self, mock_input):
        """Test successful data loading from Excel."""
        excel_file = self.create_test_excel()
        
        # Configure the source
        mock_input.side_effect = [
            excel_file, '2', '3', '1'
        ]
        self.source.configure()
        
        # Load data
        code_pairs = self.source.load_data(100)
        
        assert len(code_pairs) == 4  # All test records are valid
        
        # Check that all items are valid CodePair instances
        for pair in code_pairs:
            assert isinstance(pair, CodePair)
            assert pair.identifier
            assert pair.generated_code

    @patch('builtins.input')
    def test_load_data_with_sampling(self, mock_input):
        """Test data loading with sampling."""
        csv_file = self.create_test_csv()
        
        # Configure the source
        mock_input.side_effect = [
            csv_file, '2', '3', '1'
        ]
        self.source.configure()
        
        # Load data with 50% sampling
        code_pairs = self.source.load_data(50)
        
        # Should get 1-2 items (50% of 3 valid records)
        assert 1 <= len(code_pairs) <= 2
        
        # All items should be valid CodePair instances
        for pair in code_pairs:
            assert isinstance(pair, CodePair)
            assert pair.identifier
            assert pair.generated_code

    @patch('builtins.input')
    def test_load_data_without_expected_code_column(self, mock_input):
        """Test data loading without expected code column."""
        csv_file = self.create_test_csv()
        
        # Configure without expected code column
        mock_input.side_effect = [
            csv_file, '2', '', '1'  # Skip expected code column
        ]
        self.source.configure()
        
        # Load data
        code_pairs = self.source.load_data(100)
        
        assert len(code_pairs) == 3
        
        # All code pairs should have None for expected_code
        for pair in code_pairs:
            assert pair.expected_code is None

    def test_get_total_count_not_configured(self):
        """Test get_total_count when not configured."""
        with pytest.raises(RuntimeError, match="is not properly configured"):
            self.source.get_total_count()

    @patch('builtins.input')
    def test_get_total_count_success(self, mock_input):
        """Test successful total count retrieval."""
        csv_file = self.create_test_csv()
        
        # Configure the source
        mock_input.side_effect = [
            csv_file, '2', '3', '1'
        ]
        self.source.configure()
        
        total_count = self.source.get_total_count()
        
        assert total_count == 3  # 3 valid rows (excluding empty identifier and empty generated code)

    @patch('builtins.input')
    def test_get_total_count_cached(self, mock_input):
        """Test that total count is cached after first call."""
        csv_file = self.create_test_csv()
        
        # Configure the source
        mock_input.side_effect = [
            csv_file, '2', '3', '1'
        ]
        self.source.configure()
        
        # First call should load data
        total_count1 = self.source.get_total_count()
        
        # Second call should use cached value
        total_count2 = self.source.get_total_count()
        
        assert total_count1 == total_count2 == 3

    @patch('builtins.input')
    def test_empty_file(self, mock_input):
        """Test handling of empty file."""
        csv_file = self.create_test_csv(with_data=False)
        
        # Configure the source
        mock_input.side_effect = [
            csv_file, '2', '3', '1'
        ]
        self.source.configure()
        
        # Load data from empty file
        code_pairs = self.source.load_data(100)
        
        assert len(code_pairs) == 0
        assert self.source.get_total_count() == 0

    @patch('builtins.input')
    def test_csv_encoding_fallback(self, mock_input):
        """Test CSV encoding fallback mechanism."""
        # Create CSV with latin-1 encoding
        fd, temp_file = tempfile.mkstemp(suffix='.csv')
        self.temp_files.append(temp_file)
        
        # Write data with latin-1 encoding
        data = "identifier,generated_code,expected_code\ntest_1,print(\"café\"),print(\"café\")\n"
        with os.fdopen(fd, 'w', encoding='latin-1') as f:
            f.write(data)
        
        # Configure the source
        mock_input.side_effect = [
            temp_file, '2', '3', '1'
        ]
        
        result = self.source.configure()
        assert result is True
        
        # Load data should work with encoding fallback
        code_pairs = self.source.load_data(100)
        assert len(code_pairs) == 1

    @patch('builtins.input')
    def test_invalid_sheet_selection(self, mock_input):
        """Test invalid sheet selection handling."""
        excel_file = self.create_test_excel(multiple_sheets=True)
        
        # Mock user inputs with invalid then valid sheet selection
        mock_input.side_effect = [
            excel_file,  # File path
            '999',       # Invalid sheet selection
            'abc',       # Invalid sheet selection (non-numeric)
            '1',         # Valid sheet selection
            '2',         # Generated code column
            '3',         # Expected code column
            '1'          # Identifier column
        ]
        
        result = self.source.configure()
        
        assert result is True
        assert self.source.is_configured

    @patch('builtins.input')
    def test_invalid_column_selection(self, mock_input):
        """Test invalid column selection handling."""
        csv_file = self.create_test_csv()
        
        # Mock user inputs with invalid then valid column selection
        mock_input.side_effect = [
            csv_file,  # File path
            '999',     # Invalid generated code column
            'abc',     # Invalid generated code column (non-numeric)
            '2',       # Valid generated code column
            '3',       # Expected code column
            '1'        # Identifier column
        ]
        
        result = self.source.configure()
        
        assert result is True
        assert self.source.is_configured

    @patch('builtins.input')
    def test_configuration_validation_failure(self, mock_input):
        """Test configuration validation failure."""
        csv_file = self.create_test_csv()
        
        # Configure with valid inputs
        mock_input.side_effect = [
            csv_file, '2', '3', '1'
        ]
        
        # Mock validation to fail
        with patch.object(self.source, '_validate_configuration', return_value=False):
            result = self.source.configure()
            
            assert result is False
            assert not self.source.is_configured

    @patch('builtins.input')
    def test_file_deleted_after_configuration(self, mock_input):
        """Test handling when file is deleted after configuration."""
        csv_file = self.create_test_csv()
        
        # Configure the source
        mock_input.side_effect = [
            csv_file, '2', '3', '1'
        ]
        self.source.configure()
        
        # Delete the file
        os.unlink(csv_file)
        
        # Loading data should fail gracefully
        with pytest.raises(DataSourceError, match="Failed to load data from Excel/CSV file"):
            self.source.load_data(100)

    @patch('builtins.input')
    def test_data_validation_skips_invalid_rows(self, mock_input):
        """Test that invalid rows are skipped during data loading."""
        # Create CSV with mixed valid/invalid data
        fd, temp_file = tempfile.mkstemp(suffix='.csv')
        self.temp_files.append(temp_file)
        
        # Create data with some invalid rows
        data = {
            'identifier': ['valid_1', '', 'valid_2', None, 'valid_3'],
            'generated_code': ['print("code1")', 'print("code2")', '', 'print("code4")', 'print("code5")'],
            'expected_code': ['print("exp1")', 'print("exp2")', 'print("exp3")', 'print("exp4")', 'print("exp5")']
        }
        df = pd.DataFrame(data)
        df.to_csv(temp_file, index=False)
        os.close(fd)
        
        # Configure the source
        mock_input.side_effect = [
            temp_file, '2', '3', '1'
        ]
        self.source.configure()
        
        # Load data - should skip invalid rows
        code_pairs = self.source.load_data(100)
        
        # Should only get 2 valid rows (valid_1 and valid_3)
        assert len(code_pairs) == 2
        assert all(pair.identifier and pair.generated_code for pair in code_pairs)

    def test_get_available_sheets_error(self):
        """Test _get_available_sheets with file error."""
        self.source._file_path = '/nonexistent/file.xlsx'
        
        sheets = self.source._get_available_sheets()
        
        assert sheets == []