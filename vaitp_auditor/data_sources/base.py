"""
Abstract base class for data source implementations.
"""

import logging
import random
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..core.models import CodePair


class DataSourceError(Exception):
    """Base exception for data source related errors."""
    pass


class DataSourceConfigurationError(DataSourceError):
    """Raised when data source configuration is invalid."""
    pass


class DataSourceConnectionError(DataSourceError):
    """Raised when data source connection fails."""
    pass


class DataSourceValidationError(DataSourceError):
    """Raised when data validation fails."""
    pass


class DataSource(ABC):
    """
    Abstract base class for all data source implementations.
    
    Data sources are responsible for loading code pairs from various sources
    such as file systems, databases, or Excel files.
    """

    def __init__(self):
        """Initialize the data source with common attributes."""
        self._configured = False
        self._logger = logging.getLogger(self.__class__.__name__)
        self._total_count: Optional[int] = None

    @abstractmethod
    def configure(self) -> bool:
        """
        Configure the data source with user-provided parameters.
        
        Returns:
            bool: True if configuration was successful, False otherwise.
        """
        pass

    @abstractmethod
    def load_data(self, sample_percentage: float) -> List[CodePair]:
        """
        Load code pairs from the configured source.
        
        Args:
            sample_percentage: Percentage of data to sample (1-100).
            
        Returns:
            List[CodePair]: List of code pairs ready for review.
            
        Raises:
            ValueError: If sample_percentage is not between 1 and 100.
            RuntimeError: If data source is not properly configured.
        """
        pass

    @abstractmethod
    def get_total_count(self) -> int:
        """
        Get the total number of available code pairs before sampling.
        
        Returns:
            int: Total count of available code pairs.
            
        Raises:
            RuntimeError: If data source is not properly configured.
        """
        pass

    def _validate_sample_percentage(self, sample_percentage: float) -> None:
        """
        Validate sample percentage parameter.
        
        Args:
            sample_percentage: Percentage to validate.
            
        Raises:
            ValueError: If sample_percentage is not between 1 and 100.
        """
        if not isinstance(sample_percentage, (int, float)):
            raise ValueError("sample_percentage must be a number")
        
        if not (1 <= sample_percentage <= 100):
            raise ValueError("sample_percentage must be between 1 and 100")

    def _validate_configured(self) -> None:
        """
        Validate that the data source is properly configured.
        
        Raises:
            RuntimeError: If data source is not configured.
        """
        if not self._configured:
            raise RuntimeError(f"{self.__class__.__name__} is not properly configured")

    def _sample_data(self, data: List[CodePair], sample_percentage: float) -> List[CodePair]:
        """
        Sample data based on the given percentage.
        
        Args:
            data: List of code pairs to sample from.
            sample_percentage: Percentage of data to sample (1-100).
            
        Returns:
            List[CodePair]: Sampled code pairs.
        """
        if sample_percentage >= 100:
            return data
        
        sample_size = max(1, int(len(data) * sample_percentage / 100))
        return random.sample(data, sample_size)

    def _handle_encoding_error(self, file_path: str, error: UnicodeError) -> Optional[str]:
        """
        Handle encoding errors with fallback strategy.
        
        Args:
            file_path: Path to the file with encoding issues.
            error: The encoding error that occurred.
            
        Returns:
            Optional[str]: File content with fallback encoding, or None if failed.
        """
        self._logger.warning(f"UTF-8 encoding failed for {file_path}: {error}")
        
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            self._logger.warning(f"Successfully read {file_path} using latin-1 encoding")
            return content
        except Exception as fallback_error:
            self._logger.error(f"Failed to read {file_path} with latin-1 fallback: {fallback_error}")
            return None

    def _validate_code_pair(self, code_pair: CodePair) -> bool:
        """
        Validate a code pair for integrity.
        
        Args:
            code_pair: The code pair to validate.
            
        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            return code_pair.validate_integrity()
        except Exception as e:
            self._logger.error(f"Code pair validation failed: {e}")
            return False

    def _log_error_with_context(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Log error with additional context information.
        
        Args:
            error: The exception that occurred.
            context: Additional context information.
        """
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        self._logger.error(f"{error.__class__.__name__}: {error} (Context: {context_str})")

    @property
    def is_configured(self) -> bool:
        """Check if the data source is configured."""
        return self._configured