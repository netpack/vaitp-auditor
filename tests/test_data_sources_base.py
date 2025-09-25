"""
Unit tests for the abstract DataSource base class.
"""

import pytest
import logging
from unittest.mock import Mock, patch, mock_open
from typing import List

from vaitp_auditor.data_sources.base import (
    DataSource, 
    DataSourceError, 
    DataSourceConfigurationError,
    DataSourceConnectionError,
    DataSourceValidationError
)
from vaitp_auditor.core.models import CodePair


class ConcreteDataSource(DataSource):
    """Concrete implementation for testing the abstract base class."""
    
    def configure(self) -> bool:
        """Test implementation of configure method."""
        self._configured = True
        return True
    
    def load_data(self, sample_percentage: float) -> List[CodePair]:
        """Test implementation of load_data method."""
        self._validate_configured()
        self._validate_sample_percentage(sample_percentage)
        
        # Create test data
        test_data = [
            CodePair(
                identifier=f"test_{i}",
                expected_code=f"expected_code_{i}",
                generated_code=f"generated_code_{i}",
                source_info={"index": i}
            )
            for i in range(10)
        ]
        
        return self._sample_data(test_data, sample_percentage)
    
    def get_total_count(self) -> int:
        """Test implementation of get_total_count method."""
        self._validate_configured()
        return 10


class TestDataSourceExceptions:
    """Test custom exception classes."""
    
    def test_data_source_error_inheritance(self):
        """Test that custom exceptions inherit from base exception."""
        assert issubclass(DataSourceError, Exception)
        assert issubclass(DataSourceConfigurationError, DataSourceError)
        assert issubclass(DataSourceConnectionError, DataSourceError)
        assert issubclass(DataSourceValidationError, DataSourceError)
    
    def test_exception_messages(self):
        """Test that exceptions can carry messages."""
        msg = "Test error message"
        
        error = DataSourceError(msg)
        assert str(error) == msg
        
        config_error = DataSourceConfigurationError(msg)
        assert str(config_error) == msg
        
        conn_error = DataSourceConnectionError(msg)
        assert str(conn_error) == msg
        
        val_error = DataSourceValidationError(msg)
        assert str(val_error) == msg


class TestDataSourceBase:
    """Test the abstract DataSource base class functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.data_source = ConcreteDataSource()
    
    def test_initialization(self):
        """Test proper initialization of base class."""
        assert not self.data_source._configured
        assert self.data_source._logger is not None
        assert self.data_source._total_count is None
        assert not self.data_source.is_configured
    
    def test_configure_sets_configured_flag(self):
        """Test that configure method sets the configured flag."""
        assert not self.data_source.is_configured
        result = self.data_source.configure()
        assert result is True
        assert self.data_source.is_configured
    
    def test_validate_sample_percentage_valid_values(self):
        """Test sample percentage validation with valid values."""
        # Should not raise exceptions
        self.data_source._validate_sample_percentage(1)
        self.data_source._validate_sample_percentage(50)
        self.data_source._validate_sample_percentage(100)
        self.data_source._validate_sample_percentage(1.5)
        self.data_source._validate_sample_percentage(99.9)
    
    def test_validate_sample_percentage_invalid_values(self):
        """Test sample percentage validation with invalid values."""
        with pytest.raises(ValueError, match="sample_percentage must be between 1 and 100"):
            self.data_source._validate_sample_percentage(0)
        
        with pytest.raises(ValueError, match="sample_percentage must be between 1 and 100"):
            self.data_source._validate_sample_percentage(101)
        
        with pytest.raises(ValueError, match="sample_percentage must be between 1 and 100"):
            self.data_source._validate_sample_percentage(-5)
        
        with pytest.raises(ValueError, match="sample_percentage must be a number"):
            self.data_source._validate_sample_percentage("50")
        
        with pytest.raises(ValueError, match="sample_percentage must be a number"):
            self.data_source._validate_sample_percentage(None)
    
    def test_validate_configured_when_not_configured(self):
        """Test validation fails when not configured."""
        with pytest.raises(RuntimeError, match="ConcreteDataSource is not properly configured"):
            self.data_source._validate_configured()
    
    def test_validate_configured_when_configured(self):
        """Test validation passes when configured."""
        self.data_source.configure()
        # Should not raise exception
        self.data_source._validate_configured()
    
    def test_sample_data_full_sample(self):
        """Test sampling with 100% returns all data."""
        test_data = [
            CodePair(f"id_{i}", f"exp_{i}", f"gen_{i}", {"i": i})
            for i in range(5)
        ]
        
        result = self.data_source._sample_data(test_data, 100)
        assert len(result) == 5
        assert result == test_data
    
    def test_sample_data_partial_sample(self):
        """Test sampling with less than 100%."""
        test_data = [
            CodePair(f"id_{i}", f"exp_{i}", f"gen_{i}", {"i": i})
            for i in range(10)
        ]
        
        # Test 50% sampling
        result = self.data_source._sample_data(test_data, 50)
        assert len(result) == 5
        assert all(item in test_data for item in result)
        
        # Test 20% sampling
        result = self.data_source._sample_data(test_data, 20)
        assert len(result) == 2
        assert all(item in test_data for item in result)
    
    def test_sample_data_minimum_one_item(self):
        """Test that sampling always returns at least one item."""
        test_data = [CodePair("id_1", "exp_1", "gen_1", {})]
        
        # Even with 1% of 1 item, should return 1 item
        result = self.data_source._sample_data(test_data, 1)
        assert len(result) == 1
        assert result[0] == test_data[0]
    
    @patch('builtins.open', mock_open(read_data="test content"))
    def test_handle_encoding_error_fallback_success(self):
        """Test successful encoding fallback."""
        error = UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')
        
        result = self.data_source._handle_encoding_error("test_file.py", error)
        assert result == "test content"
    
    @patch('builtins.open')
    def test_handle_encoding_error_fallback_failure(self, mock_file):
        """Test encoding fallback failure."""
        # Mock the open function to raise an exception on latin-1 attempt
        mock_file.side_effect = IOError("File not found")
        
        error = UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')
        
        result = self.data_source._handle_encoding_error("test_file.py", error)
        assert result is None
    
    def test_validate_code_pair_valid(self):
        """Test code pair validation with valid data."""
        valid_pair = CodePair("test_id", "expected", "generated", {"key": "value"})
        
        result = self.data_source._validate_code_pair(valid_pair)
        assert result is True
    
    def test_validate_code_pair_invalid(self):
        """Test code pair validation with invalid data."""
        # Create an invalid code pair by bypassing validation
        invalid_pair = CodePair.__new__(CodePair)
        invalid_pair.identifier = ""  # Invalid empty identifier
        invalid_pair.expected_code = "expected"
        invalid_pair.generated_code = "generated"
        invalid_pair.source_info = {}
        
        result = self.data_source._validate_code_pair(invalid_pair)
        assert result is False
    
    def test_log_error_with_context(self, caplog):
        """Test error logging with context."""
        error = ValueError("Test error")
        context = {"file": "test.py", "line": 42}
        
        with caplog.at_level(logging.ERROR):
            self.data_source._log_error_with_context(error, context)
        
        assert "ValueError: Test error" in caplog.text
        assert "file=test.py" in caplog.text
        assert "line=42" in caplog.text
    
    def test_load_data_requires_configuration(self):
        """Test that load_data requires configuration."""
        with pytest.raises(RuntimeError, match="ConcreteDataSource is not properly configured"):
            self.data_source.load_data(50)
    
    def test_load_data_validates_sample_percentage(self):
        """Test that load_data validates sample percentage."""
        self.data_source.configure()
        
        with pytest.raises(ValueError, match="sample_percentage must be between 1 and 100"):
            self.data_source.load_data(0)
    
    def test_load_data_success(self):
        """Test successful data loading."""
        self.data_source.configure()
        
        result = self.data_source.load_data(100)
        assert len(result) == 10
        assert all(isinstance(pair, CodePair) for pair in result)
        assert all(pair.identifier.startswith("test_") for pair in result)
    
    def test_get_total_count_requires_configuration(self):
        """Test that get_total_count requires configuration."""
        with pytest.raises(RuntimeError, match="ConcreteDataSource is not properly configured"):
            self.data_source.get_total_count()
    
    def test_get_total_count_success(self):
        """Test successful total count retrieval."""
        self.data_source.configure()
        
        result = self.data_source.get_total_count()
        assert result == 10


class TestDataSourceIntegration:
    """Integration tests for DataSource functionality."""
    
    def test_full_workflow(self):
        """Test complete workflow from configuration to data loading."""
        data_source = ConcreteDataSource()
        
        # Step 1: Configure
        assert data_source.configure() is True
        assert data_source.is_configured
        
        # Step 2: Get total count
        total_count = data_source.get_total_count()
        assert total_count == 10
        
        # Step 3: Load full data
        full_data = data_source.load_data(100)
        assert len(full_data) == 10
        
        # Step 4: Load sampled data
        sampled_data = data_source.load_data(50)
        assert len(sampled_data) == 5
        assert all(item in full_data for item in sampled_data)
    
    def test_error_handling_workflow(self):
        """Test error handling in typical workflow."""
        data_source = ConcreteDataSource()
        
        # Should fail before configuration
        with pytest.raises(RuntimeError):
            data_source.get_total_count()
        
        with pytest.raises(RuntimeError):
            data_source.load_data(50)
        
        # Configure and test invalid parameters
        data_source.configure()
        
        with pytest.raises(ValueError):
            data_source.load_data(0)
        
        with pytest.raises(ValueError):
            data_source.load_data(101)