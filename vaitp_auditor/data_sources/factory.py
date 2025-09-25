"""
Data source factory for creating appropriate data source instances.
"""

from typing import Optional, Dict, Any
from .base import DataSource
from .filesystem import FileSystemSource
from .sqlite import SQLiteSource
from .excel import ExcelSource
from ..utils.logging_config import get_logger
from ..utils.error_handling import DataSourceError, handle_errors, safe_execute


class DataSourceFactory:
    """
    Factory class for creating data source instances based on type.
    
    Provides a centralized way to create and configure data sources
    with proper error handling and validation.
    """
    
    # Registry of available data source types
    _DATA_SOURCES = {
        'folders': FileSystemSource,
        'sqlite': SQLiteSource,
        'excel': ExcelSource
    }
    
    _logger = get_logger('data_source_factory')
    
    @classmethod
    def get_available_types(cls) -> Dict[str, str]:
        """
        Get available data source types with descriptions.
        
        Returns:
            Dict[str, str]: Mapping of type keys to human-readable descriptions.
        """
        return {
            'folders': 'File System Folders',
            'sqlite': 'SQLite Database',
            'excel': 'Excel/CSV File'
        }
    
    @classmethod
    @handle_errors(error_types=Exception, reraise=False)
    def create_data_source(cls, source_type: str) -> Optional[DataSource]:
        """
        Create a data source instance of the specified type.
        
        Args:
            source_type: Type of data source to create ('folders', 'sqlite', 'excel').
            
        Returns:
            Optional[DataSource]: Data source instance, or None if type is invalid.
        """
        cls._logger.debug(f"Creating data source of type: {source_type}")
        
        if source_type not in cls._DATA_SOURCES:
            cls._logger.error(f"Invalid data source type: {source_type}")
            return None
        
        try:
            data_source_class = cls._DATA_SOURCES[source_type]
            instance = data_source_class()
            cls._logger.debug(f"Successfully created {source_type} data source")
            return instance
        except Exception as e:
            cls._logger.error(f"Failed to create {source_type} data source: {e}")
            return None
    
    @classmethod
    def validate_source_type(cls, source_type: str) -> bool:
        """
        Validate that a data source type is supported.
        
        Args:
            source_type: Type to validate.
            
        Returns:
            bool: True if supported, False otherwise.
        """
        return source_type in cls._DATA_SOURCES
    
    @classmethod
    def get_source_description(cls, source_type: str) -> Optional[str]:
        """
        Get human-readable description for a data source type.
        
        Args:
            source_type: Type to get description for.
            
        Returns:
            Optional[str]: Description, or None if type is invalid.
        """
        descriptions = cls.get_available_types()
        return descriptions.get(source_type)
    
    @classmethod
    @handle_errors(error_types=Exception, reraise=False)
    def configure_data_source_interactive(cls, source_type: str) -> Optional[DataSource]:
        """
        Create and interactively configure a data source.
        
        Args:
            source_type: Type of data source to create and configure.
            
        Returns:
            Optional[DataSource]: Configured data source, or None if configuration failed.
        """
        cls._logger.info(f"Starting interactive configuration for {source_type} data source")
        
        # Create data source instance
        data_source = cls.create_data_source(source_type)
        if not data_source:
            error_msg = f"Unsupported data source type '{source_type}'"
            cls._logger.error(error_msg)
            print(f"Error: {error_msg}")
            return None
        
        # Display configuration instructions
        description = cls.get_source_description(source_type)
        print(f"\nConfiguring {description}")
        print("-" * (len(description) + 12))
        
        # Provide source-specific instructions
        if source_type == 'folders':
            print("You will be prompted to specify folders containing your code files.")
            print("Files are matched by base name (ignoring extensions).")
        elif source_type == 'sqlite':
            print("You will be prompted to specify database connection details.")
            print("Make sure your SQLite database file is accessible.")
        elif source_type == 'excel':
            print("You will be prompted to specify Excel or CSV file details.")
            print("Supported formats: .xlsx, .xls, .csv")
        
        print()
        
        # Configure the data source with comprehensive error handling
        try:
            cls._logger.debug(f"Starting configuration for {source_type}")
            
            if data_source.configure():
                # Display success information
                total_count = safe_execute(
                    data_source.get_total_count,
                    error_types=Exception,
                    default_return=0,
                    context={'operation': 'get_total_count', 'source_type': source_type}
                )
                
                print(f"\nData source configured successfully!")
                print(f"Total items found: {total_count}")
                
                cls._logger.info(f"Successfully configured {source_type} data source with {total_count} items")
                return data_source
            else:
                error_msg = "Data source configuration failed"
                cls._logger.error(error_msg)
                print(error_msg + ".")
                return None
                
        except KeyboardInterrupt:
            cls._logger.info("Data source configuration cancelled by user")
            print("\nConfiguration cancelled by user.")
            return None
        except Exception as e:
            error_msg = f"Error configuring data source: {e}"
            cls._logger.error(error_msg)
            print(error_msg)
            return None