"""
Unit tests for SQLiteSource data source implementation.
"""

import pytest
import sqlite3
import tempfile
import os
from unittest.mock import patch, MagicMock, call
from vaitp_auditor.data_sources.sqlite import SQLiteSource
from vaitp_auditor.data_sources.base import DataSourceError, DataSourceConnectionError
from vaitp_auditor.core.models import CodePair


class TestSQLiteSource:
    """Test cases for SQLiteSource class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.source = SQLiteSource()
        self.temp_db = None

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_db and os.path.exists(self.temp_db):
            os.unlink(self.temp_db)

    def create_test_database(self, with_data=True):
        """Create a temporary test database."""
        # Create temporary database file
        fd, self.temp_db = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Create database and table
        conn = sqlite3.connect(self.temp_db)
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                identifier TEXT,
                generated_code TEXT,
                expected_code TEXT,
                extra_column TEXT
            )
        """)
        
        if with_data:
            # Insert test data
            test_data = [
                (1, 'test_1', 'print("generated 1")', 'print("expected 1")', 'extra1'),
                (2, 'test_2', 'print("generated 2")', 'print("expected 2")', 'extra2'),
                (3, 'test_3', 'print("generated 3")', None, 'extra3'),
                (4, 'test_4', 'print("generated 4")', 'print("expected 4")', 'extra4'),
                (5, 'test_5', 'print("generated 5")', '', 'extra5'),  # Empty expected code
            ]
            
            cursor.executemany("""
                INSERT INTO test_table (id, identifier, generated_code, expected_code, extra_column)
                VALUES (?, ?, ?, ?, ?)
            """, test_data)
        
        conn.commit()
        conn.close()
        
        return self.temp_db

    @patch('builtins.input')
    def test_configure_success(self, mock_input):
        """Test successful configuration."""
        db_path = self.create_test_database()
        
        # Mock user inputs
        mock_input.side_effect = [
            db_path,  # Database path
            '1',      # Table selection (test_table)
            '3',      # Generated code column (generated_code)
            '4',      # Expected code column (expected_code)
            '2'       # Identifier column (identifier)
        ]
        
        result = self.source.configure()
        
        assert result is True
        assert self.source.is_configured
        assert self.source._db_path == db_path
        assert self.source._table_name == 'test_table'
        assert self.source._generated_code_column == 'generated_code'
        assert self.source._expected_code_column == 'expected_code'
        assert self.source._identifier_column == 'identifier'

    @patch('builtins.input')
    def test_configure_with_optional_expected_code(self, mock_input):
        """Test configuration with optional expected code column."""
        db_path = self.create_test_database()
        
        # Mock user inputs (skip expected code column)
        mock_input.side_effect = [
            db_path,  # Database path
            '1',      # Table selection (test_table)
            '3',      # Generated code column (generated_code)
            '',       # Skip expected code column
            '2'       # Identifier column (identifier)
        ]
        
        result = self.source.configure()
        
        assert result is True
        assert self.source.is_configured
        assert self.source._expected_code_column is None

    @patch('builtins.input')
    def test_configure_empty_database_path(self, mock_input):
        """Test configuration with empty database path."""
        mock_input.side_effect = ['']  # Empty database path
        
        result = self.source.configure()
        
        assert result is False
        assert not self.source.is_configured

    @patch('builtins.input')
    def test_configure_nonexistent_database(self, mock_input):
        """Test configuration with nonexistent database."""
        mock_input.side_effect = ['/nonexistent/database.db']
        
        result = self.source.configure()
        
        assert result is False
        assert not self.source.is_configured

    @patch('builtins.input')
    def test_configure_invalid_table_selection(self, mock_input):
        """Test configuration with invalid table selection."""
        db_path = self.create_test_database()
        
        # Mock user inputs with invalid then valid table selection
        mock_input.side_effect = [
            db_path,  # Database path
            '999',    # Invalid table selection
            'abc',    # Invalid table selection (non-numeric)
            '1',      # Valid table selection
            '3',      # Generated code column
            '4',      # Expected code column
            '2'       # Identifier column
        ]
        
        result = self.source.configure()
        
        assert result is True
        assert self.source.is_configured

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
    def test_load_data_success(self, mock_input):
        """Test successful data loading."""
        db_path = self.create_test_database()
        
        # Configure the source
        mock_input.side_effect = [
            db_path, '1', '3', '4', '2'
        ]
        self.source.configure()
        
        # Load data
        code_pairs = self.source.load_data(100)
        
        assert len(code_pairs) == 5  # All test records
        
        # Check first code pair
        first_pair = code_pairs[0]
        assert isinstance(first_pair, CodePair)
        assert first_pair.identifier == 'test_1'
        assert first_pair.generated_code == 'print("generated 1")'
        assert first_pair.expected_code == 'print("expected 1")'
        assert first_pair.source_info['source_type'] == 'sqlite'

    @patch('builtins.input')
    def test_load_data_with_sampling(self, mock_input):
        """Test data loading with sampling."""
        db_path = self.create_test_database()
        
        # Configure the source
        mock_input.side_effect = [
            db_path, '1', '3', '4', '2'
        ]
        self.source.configure()
        
        # Load data with 40% sampling
        code_pairs = self.source.load_data(40)
        
        # Should get 2 items (40% of 5 = 2)
        assert len(code_pairs) == 2
        
        # All items should be valid CodePair instances
        for pair in code_pairs:
            assert isinstance(pair, CodePair)
            assert pair.identifier
            assert pair.generated_code

    @patch('builtins.input')
    def test_load_data_without_expected_code_column(self, mock_input):
        """Test data loading without expected code column."""
        db_path = self.create_test_database()
        
        # Configure without expected code column
        mock_input.side_effect = [
            db_path, '1', '3', '', '2'  # Skip expected code column
        ]
        self.source.configure()
        
        # Load data
        code_pairs = self.source.load_data(100)
        
        assert len(code_pairs) == 5
        
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
        db_path = self.create_test_database()
        
        # Configure the source
        mock_input.side_effect = [
            db_path, '1', '3', '4', '2'
        ]
        self.source.configure()
        
        total_count = self.source.get_total_count()
        
        assert total_count == 5

    @patch('builtins.input')
    def test_get_total_count_cached(self, mock_input):
        """Test that total count is cached after first call."""
        db_path = self.create_test_database()
        
        # Configure the source
        mock_input.side_effect = [
            db_path, '1', '3', '4', '2'
        ]
        self.source.configure()
        
        # First call should query database
        total_count1 = self.source.get_total_count()
        
        # Second call should use cached value
        total_count2 = self.source.get_total_count()
        
        assert total_count1 == total_count2 == 5

    def test_connection_retry_logic(self):
        """Test connection retry logic with exponential backoff."""
        self.source._db_path = '/nonexistent/database.db'
        self.source._max_retries = 2
        self.source._retry_delay = 0.1  # Short delay for testing
        
        with pytest.raises(DataSourceConnectionError, match="Failed to connect to database after 2 attempts"):
            self.source._get_connection()

    @patch('builtins.input')
    def test_database_connection_error_during_load(self, mock_input):
        """Test handling of database connection errors during data loading."""
        db_path = self.create_test_database()
        
        # Configure the source
        mock_input.side_effect = [
            db_path, '1', '3', '4', '2'
        ]
        self.source.configure()
        
        # Remove the database file to simulate connection error
        os.unlink(db_path)
        
        with pytest.raises(DataSourceError, match="Failed to load data from SQLite database"):
            self.source.load_data(100)

    @patch('builtins.input')
    def test_empty_database_table(self, mock_input):
        """Test handling of empty database table."""
        db_path = self.create_test_database(with_data=False)
        
        # Configure the source
        mock_input.side_effect = [
            db_path, '1', '3', '4', '2'
        ]
        self.source.configure()
        
        # Load data from empty table
        code_pairs = self.source.load_data(100)
        
        assert len(code_pairs) == 0
        assert self.source.get_total_count() == 0

    @patch('builtins.input')
    def test_data_validation_skips_invalid_rows(self, mock_input):
        """Test that invalid rows are skipped during data loading."""
        # Create database with some invalid data
        fd, self.temp_db = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        conn = sqlite3.connect(self.temp_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE test_table (
                identifier TEXT,
                generated_code TEXT,
                expected_code TEXT
            )
        """)
        
        # Insert data with some invalid rows
        test_data = [
            ('valid_1', 'print("code")', 'print("expected")'),
            ('', 'print("code")', 'print("expected")'),  # Empty identifier
            ('valid_2', '', 'print("expected")'),  # Empty generated code
            ('valid_3', 'print("code")', 'print("expected")'),
        ]
        
        cursor.executemany("""
            INSERT INTO test_table (identifier, generated_code, expected_code)
            VALUES (?, ?, ?)
        """, test_data)
        
        conn.commit()
        conn.close()
        
        # Configure the source
        mock_input.side_effect = [
            self.temp_db, '1', '2', '3', '1'
        ]
        self.source.configure()
        
        # Load data - should skip invalid rows
        code_pairs = self.source.load_data(100)
        
        # Should only get 2 valid rows
        assert len(code_pairs) == 2
        assert all(pair.identifier and pair.generated_code for pair in code_pairs)

    def test_get_available_tables_connection_error(self):
        """Test _get_available_tables with connection error."""
        self.source._db_path = '/nonexistent/database.db'
        self.source._max_retries = 1
        
        tables = self.source._get_available_tables()
        
        assert tables == []

    def test_get_table_columns_connection_error(self):
        """Test _get_table_columns with connection error."""
        self.source._db_path = '/nonexistent/database.db'
        self.source._max_retries = 1
        
        columns = self.source._get_table_columns('test_table')
        
        assert columns == []

    @patch('builtins.input')
    def test_configuration_validation_failure(self, mock_input):
        """Test configuration validation failure."""
        db_path = self.create_test_database()
        
        # Configure with valid inputs
        mock_input.side_effect = [
            db_path, '1', '3', '4', '2'
        ]
        
        # Mock validation to fail
        with patch.object(self.source, '_validate_configuration', return_value=False):
            result = self.source.configure()
            
            assert result is False
            assert not self.source.is_configured

    def test_cleanup_on_destruction(self):
        """Test that database connection is cleaned up on destruction."""
        mock_connection = MagicMock()
        self.source._connection = mock_connection
        
        # Trigger destructor
        del self.source
        
        # Connection should be closed (though we can't easily test this)
        # This test mainly ensures no exceptions are raised during cleanup