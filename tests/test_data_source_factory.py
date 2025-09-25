"""
Unit tests for DataSourceFactory.
"""

import pytest
from unittest.mock import patch, MagicMock
from vaitp_auditor.data_sources.factory import DataSourceFactory
from vaitp_auditor.data_sources import FileSystemSource, SQLiteSource, ExcelSource


class TestDataSourceFactory:
    """Test cases for DataSourceFactory class."""

    def test_get_available_types(self):
        """Test getting available data source types."""
        types = DataSourceFactory.get_available_types()
        
        assert isinstance(types, dict)
        assert 'folders' in types
        assert 'sqlite' in types
        assert 'excel' in types
        assert types['folders'] == 'File System Folders'
        assert types['sqlite'] == 'SQLite Database'
        assert types['excel'] == 'Excel/CSV File'

    def test_create_data_source_filesystem(self):
        """Test creating FileSystemSource."""
        source = DataSourceFactory.create_data_source('folders')
        
        assert isinstance(source, FileSystemSource)
        assert not source.is_configured

    def test_create_data_source_sqlite(self):
        """Test creating SQLiteSource."""
        source = DataSourceFactory.create_data_source('sqlite')
        
        assert isinstance(source, SQLiteSource)
        assert not source.is_configured

    def test_create_data_source_excel(self):
        """Test creating ExcelSource."""
        source = DataSourceFactory.create_data_source('excel')
        
        assert isinstance(source, ExcelSource)
        assert not source.is_configured

    def test_create_data_source_invalid_type(self):
        """Test creating data source with invalid type."""
        source = DataSourceFactory.create_data_source('invalid_type')
        
        assert source is None

    def test_validate_source_type_valid(self):
        """Test validating valid source types."""
        assert DataSourceFactory.validate_source_type('folders') is True
        assert DataSourceFactory.validate_source_type('sqlite') is True
        assert DataSourceFactory.validate_source_type('excel') is True

    def test_validate_source_type_invalid(self):
        """Test validating invalid source type."""
        assert DataSourceFactory.validate_source_type('invalid') is False
        assert DataSourceFactory.validate_source_type('') is False
        assert DataSourceFactory.validate_source_type(None) is False

    def test_get_source_description_valid(self):
        """Test getting description for valid source types."""
        assert DataSourceFactory.get_source_description('folders') == 'File System Folders'
        assert DataSourceFactory.get_source_description('sqlite') == 'SQLite Database'
        assert DataSourceFactory.get_source_description('excel') == 'Excel/CSV File'

    def test_get_source_description_invalid(self):
        """Test getting description for invalid source type."""
        assert DataSourceFactory.get_source_description('invalid') is None

    @patch('builtins.print')
    @patch('builtins.input')
    def test_configure_data_source_interactive_success(self, mock_input, mock_print):
        """Test successful interactive configuration."""
        # Mock the data source configuration
        mock_source = MagicMock()
        mock_source.configure.return_value = True
        mock_source.get_total_count.return_value = 10
        
        with patch.object(DataSourceFactory, 'create_data_source', return_value=mock_source):
            result = DataSourceFactory.configure_data_source_interactive('folders')
            
            assert result == mock_source
            mock_source.configure.assert_called_once()
            mock_source.get_total_count.assert_called_once()

    @patch('builtins.print')
    def test_configure_data_source_interactive_invalid_type(self, mock_print):
        """Test interactive configuration with invalid type."""
        result = DataSourceFactory.configure_data_source_interactive('invalid_type')
        
        assert result is None

    @patch('builtins.print')
    def test_configure_data_source_interactive_configuration_failed(self, mock_print):
        """Test interactive configuration when data source configuration fails."""
        mock_source = MagicMock()
        mock_source.configure.return_value = False
        
        with patch.object(DataSourceFactory, 'create_data_source', return_value=mock_source):
            result = DataSourceFactory.configure_data_source_interactive('folders')
            
            assert result is None
            mock_source.configure.assert_called_once()

    @patch('builtins.print')
    def test_configure_data_source_interactive_exception(self, mock_print):
        """Test interactive configuration when exception occurs."""
        mock_source = MagicMock()
        mock_source.configure.side_effect = Exception("Configuration error")
        
        with patch.object(DataSourceFactory, 'create_data_source', return_value=mock_source):
            result = DataSourceFactory.configure_data_source_interactive('folders')
            
            assert result is None

    @patch('builtins.print')
    def test_configure_data_source_interactive_instructions_folders(self, mock_print):
        """Test that correct instructions are displayed for folders."""
        mock_source = MagicMock()
        mock_source.configure.return_value = True
        mock_source.get_total_count.return_value = 5
        
        with patch.object(DataSourceFactory, 'create_data_source', return_value=mock_source):
            DataSourceFactory.configure_data_source_interactive('folders')
            
            # Check that folder-specific instructions were printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("folders containing your code files" in call for call in print_calls)

    @patch('builtins.print')
    def test_configure_data_source_interactive_instructions_sqlite(self, mock_print):
        """Test that correct instructions are displayed for SQLite."""
        mock_source = MagicMock()
        mock_source.configure.return_value = True
        mock_source.get_total_count.return_value = 5
        
        with patch.object(DataSourceFactory, 'create_data_source', return_value=mock_source):
            DataSourceFactory.configure_data_source_interactive('sqlite')
            
            # Check that SQLite-specific instructions were printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("database connection details" in call for call in print_calls)

    @patch('builtins.print')
    def test_configure_data_source_interactive_instructions_excel(self, mock_print):
        """Test that correct instructions are displayed for Excel."""
        mock_source = MagicMock()
        mock_source.configure.return_value = True
        mock_source.get_total_count.return_value = 5
        
        with patch.object(DataSourceFactory, 'create_data_source', return_value=mock_source):
            DataSourceFactory.configure_data_source_interactive('excel')
            
            # Check that Excel-specific instructions were printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("Excel or CSV file details" in call for call in print_calls)