"""
Integration tests for CLI with all data sources.
"""

import pytest
from unittest.mock import patch, MagicMock
from vaitp_auditor.cli import get_data_source_type, create_data_source
from vaitp_auditor.core.models import SessionConfig
from vaitp_auditor.data_sources import DataSourceFactory


class TestCLIIntegration:
    """Test cases for CLI integration with all data sources."""

    @patch('builtins.input')
    def test_get_data_source_type_folders(self, mock_input):
        """Test selecting folders data source type."""
        mock_input.side_effect = ['1']  # Select folders
        
        result = get_data_source_type()
        
        assert result == 'folders'

    @patch('builtins.input')
    def test_get_data_source_type_sqlite(self, mock_input):
        """Test selecting SQLite data source type."""
        mock_input.side_effect = ['2']  # Select SQLite
        
        result = get_data_source_type()
        
        assert result == 'sqlite'

    @patch('builtins.input')
    def test_get_data_source_type_excel(self, mock_input):
        """Test selecting Excel data source type."""
        mock_input.side_effect = ['3']  # Select Excel
        
        result = get_data_source_type()
        
        assert result == 'excel'

    @patch('builtins.input')
    def test_get_data_source_type_invalid_then_valid(self, mock_input):
        """Test invalid selection followed by valid selection."""
        mock_input.side_effect = ['999', 'abc', '1']  # Invalid, invalid, valid
        
        result = get_data_source_type()
        
        assert result == 'folders'

    @patch('builtins.input')
    def test_get_data_source_type_cancelled(self, mock_input):
        """Test cancelling data source type selection."""
        mock_input.side_effect = KeyboardInterrupt()
        
        result = get_data_source_type()
        
        assert result is None

    @patch.object(DataSourceFactory, 'configure_data_source_interactive')
    def test_create_data_source_folders_success(self, mock_configure):
        """Test successful creation of folders data source."""
        mock_source = MagicMock()
        mock_source.get_total_count.return_value = 10
        mock_configure.return_value = mock_source
        
        config = SessionConfig(
            experiment_name='test_exp',
            data_source_type='folders',
            data_source_params={},
            sample_percentage=50.0,
            output_format='excel'
        )
        
        result = create_data_source(config)
        
        assert result == mock_source
        mock_configure.assert_called_once_with('folders')

    @patch.object(DataSourceFactory, 'configure_data_source_interactive')
    def test_create_data_source_sqlite_success(self, mock_configure):
        """Test successful creation of SQLite data source."""
        mock_source = MagicMock()
        mock_source.get_total_count.return_value = 20
        mock_configure.return_value = mock_source
        
        config = SessionConfig(
            experiment_name='test_exp',
            data_source_type='sqlite',
            data_source_params={},
            sample_percentage=75.0,
            output_format='csv'
        )
        
        result = create_data_source(config)
        
        assert result == mock_source
        mock_configure.assert_called_once_with('sqlite')

    @patch.object(DataSourceFactory, 'configure_data_source_interactive')
    def test_create_data_source_excel_success(self, mock_configure):
        """Test successful creation of Excel data source."""
        mock_source = MagicMock()
        mock_source.get_total_count.return_value = 15
        mock_configure.return_value = mock_source
        
        config = SessionConfig(
            experiment_name='test_exp',
            data_source_type='excel',
            data_source_params={},
            sample_percentage=100.0,
            output_format='excel'
        )
        
        result = create_data_source(config)
        
        assert result == mock_source
        mock_configure.assert_called_once_with('excel')

    @patch.object(DataSourceFactory, 'configure_data_source_interactive')
    def test_create_data_source_configuration_failed(self, mock_configure):
        """Test data source creation when configuration fails."""
        mock_configure.return_value = None
        
        config = SessionConfig(
            experiment_name='test_exp',
            data_source_type='folders',
            data_source_params={},
            sample_percentage=100.0,
            output_format='excel'
        )
        
        result = create_data_source(config)
        
        assert result is None

    @patch.object(DataSourceFactory, 'configure_data_source_interactive')
    def test_create_data_source_exception(self, mock_configure):
        """Test data source creation when exception occurs."""
        mock_configure.side_effect = Exception("Configuration error")
        
        config = SessionConfig(
            experiment_name='test_exp',
            data_source_type='folders',
            data_source_params={},
            sample_percentage=100.0,
            output_format='excel'
        )
        
        result = create_data_source(config)
        
        assert result is None

    @patch('builtins.print')
    @patch.object(DataSourceFactory, 'configure_data_source_interactive')
    def test_create_data_source_sampling_calculation(self, mock_configure, mock_print):
        """Test that sampling calculation is displayed correctly."""
        mock_source = MagicMock()
        mock_source.get_total_count.return_value = 100
        mock_configure.return_value = mock_source
        
        config = SessionConfig(
            experiment_name='test_exp',
            data_source_type='folders',
            data_source_params={},
            sample_percentage=25.0,
            output_format='excel'
        )
        
        result = create_data_source(config)
        
        assert result == mock_source
        
        # Check that sampling information was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("25" in call for call in print_calls)  # 25% of 100 = 25

    def test_data_source_factory_integration(self):
        """Test that DataSourceFactory correctly creates all supported types."""
        # Test that all expected types are available
        available_types = DataSourceFactory.get_available_types()
        
        assert 'folders' in available_types
        assert 'sqlite' in available_types
        assert 'excel' in available_types
        
        # Test that all types can be created
        for source_type in available_types.keys():
            source = DataSourceFactory.create_data_source(source_type)
            assert source is not None
            assert not source.is_configured  # Should not be configured initially

    @patch('builtins.print')
    def test_data_source_descriptions(self, mock_print):
        """Test that data source descriptions are user-friendly."""
        descriptions = DataSourceFactory.get_available_types()
        
        # Check that descriptions are meaningful
        assert descriptions['folders'] == 'File System Folders'
        assert descriptions['sqlite'] == 'SQLite Database'
        assert descriptions['excel'] == 'Excel/CSV File'
        
        # All descriptions should be non-empty strings
        for desc in descriptions.values():
            assert isinstance(desc, str)
            assert len(desc) > 0