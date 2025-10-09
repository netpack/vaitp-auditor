"""
Excel/CSV data source implementation for the VAITP-Auditor system.
"""

import pandas as pd
import os
from typing import List, Optional, Dict, Any
from .base import DataSource, DataSourceError, DataSourceConfigurationError, DataSourceValidationError
from ..core.models import CodePair


class ExcelSource(DataSource):
    """
    Excel/CSV file data source implementation.
    
    Supports loading code pairs from Excel (.xlsx) and CSV files with configurable
    sheet and column selection, data validation, and proper error handling.
    """

    def __init__(self):
        """Initialize Excel data source."""
        super().__init__()
        self._file_path: Optional[str] = None
        self._sheet_name: Optional[str] = None
        self._generated_code_column: Optional[str] = None
        self._expected_code_column: Optional[str] = None
        self._input_code_column: Optional[str] = None
        self._identifier_column: Optional[str] = None
        self._model_column: Optional[str] = None
        self._prompting_strategy_column: Optional[str] = None
        self._dataframe: Optional[pd.DataFrame] = None

    def configure(self) -> bool:
        """
        Configure the Excel data source with user-provided parameters.
        
        Returns:
            bool: True if configuration was successful, False otherwise.
        """
        try:
            # Get file path
            self._file_path = input("Enter Excel/CSV file path: ").strip()
            if not self._file_path:
                print("Error: File path cannot be empty")
                return False

            # Validate file exists and has correct extension
            if not os.path.exists(self._file_path):
                print(f"Error: File '{self._file_path}' does not exist")
                return False

            file_ext = os.path.splitext(self._file_path)[1].lower()
            if file_ext not in ['.xlsx', '.xls', '.csv']:
                print(f"Error: Unsupported file format '{file_ext}'. Supported formats: .xlsx, .xls, .csv")
                return False

            # Handle sheet selection for Excel files
            if file_ext in ['.xlsx', '.xls']:
                sheets = self._get_available_sheets()
                if not sheets:
                    print("Error: No sheets found in Excel file or file is corrupted")
                    return False

                if len(sheets) == 1:
                    self._sheet_name = sheets[0]
                    print(f"Using sheet: {self._sheet_name}")
                else:
                    # Display available sheets
                    print("\nAvailable sheets:")
                    for i, sheet in enumerate(sheets, 1):
                        print(f"{i}. {sheet}")

                    # Get sheet selection
                    while True:
                        try:
                            sheet_choice = input(f"\nSelect sheet (1-{len(sheets)}): ").strip()
                            sheet_index = int(sheet_choice) - 1
                            if 0 <= sheet_index < len(sheets):
                                self._sheet_name = sheets[sheet_index]
                                break
                            else:
                                print(f"Error: Please enter a number between 1 and {len(sheets)}")
                        except ValueError:
                            print("Error: Please enter a valid number")
            else:
                # CSV files don't have sheets
                self._sheet_name = None

            # Load data to get column information
            try:
                self._dataframe = self._load_dataframe()
            except Exception as e:
                print(f"Error: Failed to load file data: {e}")
                return False

            # Get available columns
            columns = list(self._dataframe.columns)
            if not columns:
                print("Error: No columns found in file")
                return False

            # Display available columns
            print(f"\nAvailable columns:")
            for i, column in enumerate(columns, 1):
                print(f"{i}. {column}")

            # Get column selections
            self._generated_code_column = self._select_column(columns, "Generated Code")
            if not self._generated_code_column:
                return False

            self._expected_code_column = self._select_column(columns, "Expected Code (optional)", optional=True)
            
            self._input_code_column = self._select_column(columns, "Input Code (optional)", optional=True)
            
            self._identifier_column = self._select_column(columns, "Identifier")
            if not self._identifier_column:
                return False

            # Validate configuration
            if not self._validate_configuration():
                return False

            self._configured = True
            print(f"\nExcel source configured successfully:")
            print(f"  File: {self._file_path}")
            if self._sheet_name:
                print(f"  Sheet: {self._sheet_name}")
            print(f"  Generated Code Column: {self._generated_code_column}")
            print(f"  Expected Code Column: {self._expected_code_column or 'None'}")
            print(f"  Input Code Column: {self._input_code_column or 'None'}")
            print(f"  Identifier Column: {self._identifier_column}")

            return True

        except Exception as e:
            self._log_error_with_context(e, {
                'file_path': self._file_path,
                'sheet_name': self._sheet_name
            })
            return False

    def load_data(self, sample_percentage: float, selected_model: Optional[str] = None, selected_strategy: Optional[str] = None) -> List[CodePair]:
        """
        Load code pairs from the configured Excel/CSV file.
        
        Args:
            sample_percentage: Percentage of data to sample (1-100).
            selected_model: Optional specific model to filter by.
            selected_strategy: Optional specific prompting strategy to filter by.
            
        Returns:
            List[CodePair]: List of code pairs ready for review.
            
        Raises:
            ValueError: If sample_percentage is not between 1 and 100.
            RuntimeError: If data source is not properly configured.
        """
        self._validate_configured()
        self._validate_sample_percentage(sample_percentage)

        try:
            # Always reload dataframe to ensure file still exists and is accessible
            self._dataframe = self._load_dataframe()
            
            # Apply filtering if specified
            filtered_df = self._apply_filtering(self._dataframe, selected_model, selected_strategy)
            
            all_data = self._convert_dataframe_to_code_pairs(filtered_df)
            
            # Cache total count
            self._total_count = len(all_data)
            
            # Sample data if needed
            sampled_data = self._sample_data(all_data, sample_percentage)
            
            filter_info = []
            if selected_model:
                filter_info.append(f"model={selected_model}")
            if selected_strategy:
                filter_info.append(f"strategy={selected_strategy}")
            filter_str = f" (filtered by {', '.join(filter_info)})" if filter_info else ""
            
            self._logger.info(f"Loaded {len(sampled_data)} code pairs from Excel/CSV file "
                            f"({sample_percentage}% of {self._total_count} total{filter_str})")
            
            return sampled_data

        except Exception as e:
            self._log_error_with_context(e, {
                'file_path': self._file_path,
                'sheet_name': self._sheet_name,
                'sample_percentage': sample_percentage,
                'selected_model': selected_model,
                'selected_strategy': selected_strategy
            })
            raise DataSourceError(f"Failed to load data from Excel/CSV file: {e}")

    def get_total_count(self) -> int:
        """
        Get the total number of available code pairs before sampling.
        
        Returns:
            int: Total count of available code pairs.
            
        Raises:
            RuntimeError: If data source is not properly configured.
        """
        self._validate_configured()
        
        if self._total_count is not None:
            return self._total_count
        
        try:
            if self._dataframe is None:
                self._dataframe = self._load_dataframe()
            
            # Count non-empty rows
            count = len(self._dataframe.dropna(subset=[self._identifier_column, self._generated_code_column]))
            self._total_count = count
            return count
                
        except Exception as e:
            self._log_error_with_context(e, {
                'file_path': self._file_path,
                'sheet_name': self._sheet_name
            })
            raise DataSourceError(f"Failed to get total count from Excel/CSV file: {e}")

    def _get_available_sheets(self) -> List[str]:
        """
        Get list of available sheets in the Excel file.
        
        Returns:
            List[str]: List of sheet names.
        """
        try:
            excel_file = pd.ExcelFile(self._file_path)
            return excel_file.sheet_names
                
        except Exception as e:
            self._logger.error(f"Failed to get available sheets: {e}")
            return []

    def _load_dataframe(self) -> pd.DataFrame:
        """
        Load data from file into a pandas DataFrame.
        
        Returns:
            pd.DataFrame: Loaded data.
            
        Raises:
            DataSourceError: If file loading fails.
        """
        try:
            file_ext = os.path.splitext(self._file_path)[1].lower()
            
            if file_ext == '.csv':
                # Try different encodings for CSV files
                encodings = ['utf-8', 'latin-1', 'cp1252']
                df = None
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(self._file_path, encoding=encoding)
                        self._logger.info(f"Successfully loaded CSV with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if df is None:
                    raise DataSourceError("Failed to load CSV file with any supported encoding")
                    
            elif file_ext in ['.xlsx', '.xls']:
                if self._sheet_name:
                    df = pd.read_excel(self._file_path, sheet_name=self._sheet_name)
                else:
                    df = pd.read_excel(self._file_path)
            else:
                raise DataSourceError(f"Unsupported file format: {file_ext}")
            
            # Convert column names to strings to handle any numeric column names
            df.columns = df.columns.astype(str)
            
            return df
                
        except Exception as e:
            raise DataSourceError(f"Failed to load data from file: {e}")
    
    def _apply_filtering(self, df: pd.DataFrame, selected_model: Optional[str] = None, selected_strategy: Optional[str] = None) -> pd.DataFrame:
        """
        Apply model and strategy filtering to the dataframe.
        
        Args:
            df: Original dataframe.
            selected_model: Optional specific model to filter by.
            selected_strategy: Optional specific prompting strategy to filter by.
            
        Returns:
            pd.DataFrame: Filtered dataframe.
        """
        filtered_df = df.copy()
        
        # Apply model filtering
        if selected_model and self._model_column and self._model_column in df.columns:
            filtered_df = filtered_df[filtered_df[self._model_column] == selected_model]
            self._logger.info(f"Filtered by model '{selected_model}': {len(filtered_df)} rows remaining")
        
        # Apply strategy filtering
        if selected_strategy and self._prompting_strategy_column and self._prompting_strategy_column in df.columns:
            filtered_df = filtered_df[filtered_df[self._prompting_strategy_column] == selected_strategy]
            self._logger.info(f"Filtered by strategy '{selected_strategy}': {len(filtered_df)} rows remaining")
        
        return filtered_df

    def _select_column(self, columns: List[str], column_type: str, optional: bool = False) -> Optional[str]:
        """
        Helper method to select a column from available columns.
        
        Args:
            columns: List of available columns.
            column_type: Description of the column type for user prompt.
            optional: Whether the column selection is optional.
            
        Returns:
            Optional[str]: Selected column name, or None if optional and skipped.
        """
        if optional:
            print(f"\nSelect {column_type} column (or press Enter to skip):")
        else:
            print(f"\nSelect {column_type} column:")
            
        for i, column in enumerate(columns, 1):
            print(f"{i}. {column}")
        
        if optional:
            print(f"{len(columns) + 1}. Skip (no {column_type.lower()})")

        while True:
            try:
                choice = input(f"Enter choice (1-{len(columns) + (1 if optional else 0)}): ").strip()
                
                if optional and not choice:
                    return None
                
                choice_index = int(choice) - 1
                
                if optional and choice_index == len(columns):
                    return None
                
                if 0 <= choice_index < len(columns):
                    return columns[choice_index]
                else:
                    max_choice = len(columns) + (1 if optional else 0)
                    print(f"Error: Please enter a number between 1 and {max_choice}")
                    
            except ValueError:
                print("Error: Please enter a valid number")

    def _validate_configuration(self) -> bool:
        """
        Validate the current configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise.
        """
        try:
            # Verify file still exists
            if not os.path.exists(self._file_path):
                print(f"Error: File '{self._file_path}' no longer exists")
                return False
            
            # Verify dataframe was loaded successfully
            if self._dataframe is None:
                print("Error: Failed to load file data")
                return False
            
            # Verify columns exist in dataframe
            available_columns = set(self._dataframe.columns)
            
            required_columns = [self._generated_code_column, self._identifier_column]
            if self._expected_code_column:
                required_columns.append(self._expected_code_column)
            if self._input_code_column:
                required_columns.append(self._input_code_column)
            
            for column in required_columns:
                if column not in available_columns:
                    print(f"Error: Column '{column}' does not exist in file")
                    return False
            
            # Check if there's any data
            if len(self._dataframe) == 0:
                print("Warning: File contains no data rows")
                return True  # Allow empty files to be configured
            
            # Check for required columns having some non-null values
            non_null_identifiers = self._dataframe[self._identifier_column].notna().sum()
            non_null_generated = self._dataframe[self._generated_code_column].notna().sum()
            
            if non_null_identifiers == 0:
                print(f"Error: No non-null values found in identifier column '{self._identifier_column}'")
                return False
                
            if non_null_generated == 0:
                print(f"Error: No non-null values found in generated code column '{self._generated_code_column}'")
                return False
            
            return True
                
        except Exception as e:
            print(f"Error: Configuration validation failed: {e}")
            return False

    def _convert_dataframe_to_code_pairs(self, df: pd.DataFrame) -> List[CodePair]:
        """
        Convert pandas DataFrame to list of CodePair objects.
        
        Args:
            df: DataFrame to convert.
            
        Returns:
            List[CodePair]: List of code pairs.
        """
        code_pairs = []
        
        for index, row in df.iterrows():
            try:
                # Get identifier and generated code (required)
                identifier = row[self._identifier_column]
                generated_code = row[self._generated_code_column]
                
                # Skip rows with null/empty required fields
                if pd.isna(identifier) or pd.isna(generated_code):
                    self._logger.warning(f"Skipping row {index + 1} with null identifier or generated code")
                    continue
                
                identifier = str(identifier).strip()
                generated_code = str(generated_code).strip()
                
                if not identifier or not generated_code:
                    self._logger.warning(f"Skipping row {index + 1} with empty identifier or generated code")
                    continue
                
                # Get expected code (optional)
                expected_code = None
                if self._expected_code_column:
                    expected_value = row[self._expected_code_column]
                    if pd.notna(expected_value):
                        expected_code = str(expected_value).strip()
                        if not expected_code:  # Empty string
                            expected_code = None
                
                # Get input code (optional)
                input_code = None
                if self._input_code_column:
                    input_value = row[self._input_code_column]
                    if pd.notna(input_value):
                        input_code = str(input_value).strip()
                        if not input_code:  # Empty string
                            input_code = None
                
                # Get model name (optional)
                model_name = None
                if self._model_column:
                    model_value = row[self._model_column]
                    if pd.notna(model_value):
                        model_name = str(model_value).strip()
                        if not model_name:  # Empty string
                            model_name = None
                
                # Get prompting strategy (optional)
                prompting_strategy = None
                if self._prompting_strategy_column:
                    strategy_value = row[self._prompting_strategy_column]
                    if pd.notna(strategy_value):
                        prompting_strategy = str(strategy_value).strip()
                        if not prompting_strategy:  # Empty string
                            prompting_strategy = None
                
                source_info = {
                    'source_type': 'excel',
                    'file_path': self._file_path,
                    'sheet_name': self._sheet_name,
                    'row_number': index + 1,
                    'identifier_column': self._identifier_column,
                    'generated_code_column': self._generated_code_column,
                    'expected_code_column': self._expected_code_column,
                    'input_code_column': self._input_code_column,
                    'model_column': self._model_column,
                    'prompting_strategy_column': self._prompting_strategy_column,
                    'model_name': model_name,
                    'prompting_strategy': prompting_strategy
                }
                
                code_pair = CodePair(
                    identifier=identifier,
                    expected_code=expected_code,
                    generated_code=generated_code,
                    source_info=source_info,
                    input_code=input_code
                )
                
                if self._validate_code_pair(code_pair):
                    code_pairs.append(code_pair)
                else:
                    self._logger.warning(f"Skipping invalid code pair at row {index + 1} with identifier: {identifier}")
                    
            except Exception as e:
                self._logger.error(f"Error processing row {index + 1}: {e}")
                continue
        
        return code_pairs