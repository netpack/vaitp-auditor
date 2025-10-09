"""
SQLite data source implementation for the VAITP-Auditor system.
"""

import sqlite3
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from .base import DataSource, DataSourceError, DataSourceConnectionError, DataSourceConfigurationError
from ..core.models import CodePair


class SQLiteSource(DataSource):
    """
    SQLite database data source implementation.
    
    Supports loading code pairs from SQLite databases with configurable
    table and column selection, connection retry logic, and proper error handling.
    """

    def __init__(self):
        """Initialize SQLite data source."""
        super().__init__()
        self._db_path: Optional[str] = None
        self._table_name: Optional[str] = None
        self._generated_code_column: Optional[str] = None
        self._expected_code_column: Optional[str] = None
        self._input_code_column: Optional[str] = None
        self._identifier_column: Optional[str] = None
        self._model_column: Optional[str] = None
        self._prompting_strategy_column: Optional[str] = None
        self._connection: Optional[sqlite3.Connection] = None
        self._max_retries = 3
        self._retry_delay = 1.0  # seconds

    def configure(self) -> bool:
        """
        Configure the SQLite data source with user-provided parameters.
        
        Returns:
            bool: True if configuration was successful, False otherwise.
        """
        try:
            # Get database path
            self._db_path = input("Enter SQLite database file path: ").strip()
            if not self._db_path:
                print("Error: Database path cannot be empty")
                return False

            # Test connection and get available tables
            tables = self._get_available_tables()
            if not tables:
                print("Error: No tables found in database or connection failed")
                return False

            # Display available tables
            print("\nAvailable tables:")
            for i, table in enumerate(tables, 1):
                print(f"{i}. {table}")

            # Get table selection
            while True:
                try:
                    table_choice = input(f"\nSelect table (1-{len(tables)}): ").strip()
                    table_index = int(table_choice) - 1
                    if 0 <= table_index < len(tables):
                        self._table_name = tables[table_index]
                        break
                    else:
                        print(f"Error: Please enter a number between 1 and {len(tables)}")
                except ValueError:
                    print("Error: Please enter a valid number")

            # Get available columns for selected table
            columns = self._get_table_columns(self._table_name)
            if not columns:
                print(f"Error: No columns found in table '{self._table_name}'")
                return False

            # Display available columns
            print(f"\nAvailable columns in '{self._table_name}':")
            for i, column in enumerate(columns, 1):
                print(f"{i}. {column}")

            # Get column selections
            self._generated_code_column = self._select_column(columns, "Generated Code")
            if not self._generated_code_column:
                return False

            self._expected_code_column = self._select_column(columns, "Expected Code (optional)", optional=True)
            
            self._identifier_column = self._select_column(columns, "Identifier")
            if not self._identifier_column:
                return False

            # Validate configuration
            if not self._validate_configuration():
                return False

            self._configured = True
            print(f"\nSQLite source configured successfully:")
            print(f"  Database: {self._db_path}")
            print(f"  Table: {self._table_name}")
            print(f"  Generated Code Column: {self._generated_code_column}")
            print(f"  Expected Code Column: {self._expected_code_column or 'None'}")
            print(f"  Identifier Column: {self._identifier_column}")

            return True

        except Exception as e:
            self._log_error_with_context(e, {
                'db_path': self._db_path,
                'table_name': self._table_name
            })
            return False

    def load_data(self, sample_percentage: float, selected_model: Optional[str] = None, selected_strategy: Optional[str] = None) -> List[CodePair]:
        """
        Load code pairs from the configured SQLite database.
        
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
            # Get counts for better logging
            total_count = self.get_total_count()
            filtered_count = self.get_filtered_count(selected_model, selected_strategy)
            
            filter_info = []
            if selected_model:
                filter_info.append(f"model={selected_model}")
            if selected_strategy:
                filter_info.append(f"strategy={selected_strategy}")
            filter_str = f" (filtered by {', '.join(filter_info)})" if filter_info else ""
            
            self._logger.info(f"Database contains {total_count} total records")
            if filter_info:
                self._logger.info(f"After filtering{filter_str}: {filtered_count} records available")
                if filtered_count != total_count:
                    self._logger.warning(f"Filtering reduced dataset from {total_count} to {filtered_count} records")
            else:
                self._logger.info(f"No filtering applied - using all {total_count} records")
            
            # Load all data first (with optional filtering)
            all_data = self._load_all_data(selected_model, selected_strategy)
            
            # Cache total count
            self._total_count = len(all_data)
            
            # Debug logging for sampling
            self._logger.info(f"After loading and validation: {len(all_data)} valid records available")
            
            # Sample data if needed
            sampled_data = self._sample_data(all_data, sample_percentage)
            
            # Debug logging for sampling result
            expected_sample_size = max(1, int(len(all_data) * sample_percentage / 100))
            self._logger.info(f"Sampling {sample_percentage}% of {len(all_data)} records: "
                            f"expected {expected_sample_size}, got {len(sampled_data)}")
            
            self._logger.info(f"Final result: loaded {len(sampled_data)} code pairs from SQLite database "
                            f"({sample_percentage}% of {len(all_data)} valid records{filter_str})")
            
            # Add explanation if the result is different from what might be expected
            if filter_info and len(all_data) < filtered_count:
                self._logger.warning(f"Note: Some records were excluded during validation. "
                                   f"Started with {filtered_count} filtered records, "
                                   f"but only {len(all_data)} passed validation.")
            
            if sample_percentage < 100:
                naive_expectation = max(1, int(total_count * sample_percentage / 100))
                if len(sampled_data) != naive_expectation:
                    self._logger.info(f"Sampling explanation: {sample_percentage}% of {total_count} total records would be {naive_expectation}, "
                                    f"but filtering and validation resulted in {len(sampled_data)} records")
                    
            # Print user-friendly summary
            print(f"\n📊 Data Loading Summary:")
            print(f"   • Total records in database: {total_count}")
            if filter_info:
                print(f"   • Records after filtering{filter_str}: {filtered_count}")
                if len(all_data) < filtered_count:
                    excluded_count = filtered_count - len(all_data)
                    print(f"   • Records excluded (empty/invalid data): {excluded_count}")
                    print(f"   • Valid records after validation: {len(all_data)}")
            print(f"   • Sample percentage requested: {sample_percentage}%")
            print(f"   • Final records selected for review: {len(sampled_data)}")
            
            # Explain why the result might be different from expectations
            if filter_info:
                naive_expectation = max(1, int(total_count * sample_percentage / 100))
                if len(sampled_data) != naive_expectation:
                    print(f"   • Note: Expected {sample_percentage}% of {total_count} total = {naive_expectation}, but got {len(sampled_data)}")
                    print(f"     This is because filtering reduced the available dataset")
                    
                if len(all_data) < filtered_count:
                    print(f"   • Note: {excluded_count} records were excluded due to missing identifiers")
                    print(f"     Empty generated_code is included as reviewable failure cases")
            print()
            
            return sampled_data

        except Exception as e:
            self._log_error_with_context(e, {
                'db_path': self._db_path,
                'table_name': self._table_name,
                'sample_percentage': sample_percentage,
                'selected_model': selected_model,
                'selected_strategy': selected_strategy
            })
            raise DataSourceError(f"Failed to load data from SQLite database: {e}")

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
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {self._table_name}")
                count = cursor.fetchone()[0]
                self._total_count = count
                return count
                
        except Exception as e:
            self._log_error_with_context(e, {
                'db_path': self._db_path,
                'table_name': self._table_name
            })
            raise DataSourceError(f"Failed to get total count from SQLite database: {e}")
    
    def get_filtered_count(self, selected_model: Optional[str] = None, selected_strategy: Optional[str] = None) -> int:
        """
        Get the count of records after filtering but before sampling.
        
        Args:
            selected_model: Optional specific model to filter by.
            selected_strategy: Optional specific prompting strategy to filter by.
            
        Returns:
            int: Count of records matching the filter criteria.
        """
        self._validate_configured()
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause for filtering
                where_conditions = []
                query_params = []
                
                if selected_model and self._model_column:
                    where_conditions.append(f"{self._model_column} = ?")
                    query_params.append(selected_model)
                
                if selected_strategy and self._prompting_strategy_column:
                    where_conditions.append(f"{self._prompting_strategy_column} = ?")
                    query_params.append(selected_strategy)
                
                where_clause = f" WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
                query = f"SELECT COUNT(*) FROM {self._table_name}{where_clause}"
                
                cursor.execute(query, query_params)
                count = cursor.fetchone()[0]
                
                self._logger.debug(f"Filtered count query: {query}")
                self._logger.debug(f"Query parameters: {query_params}")
                self._logger.debug(f"Filtered count result: {count}")
                
                return count
                
        except Exception as e:
            self._log_error_with_context(e, {
                'db_path': self._db_path,
                'table_name': self._table_name,
                'selected_model': selected_model,
                'selected_strategy': selected_strategy
            })
            raise DataSourceError(f"Failed to get filtered count from SQLite database: {e}")

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get database connection with retry logic.
        
        Returns:
            sqlite3.Connection: Database connection.
            
        Raises:
            DataSourceConnectionError: If connection fails after retries.
        """
        for attempt in range(self._max_retries):
            try:
                conn = sqlite3.connect(self._db_path)
                conn.row_factory = sqlite3.Row  # Enable column access by name
                return conn
                
            except sqlite3.Error as e:
                if attempt < self._max_retries - 1:
                    self._logger.warning(f"Database connection attempt {attempt + 1} failed: {e}. "
                                       f"Retrying in {self._retry_delay} seconds...")
                    time.sleep(self._retry_delay)
                    self._retry_delay *= 2  # Exponential backoff
                else:
                    raise DataSourceConnectionError(f"Failed to connect to database after {self._max_retries} attempts: {e}")

    def _get_available_tables(self) -> List[str]:
        """
        Get list of available tables in the database.
        
        Returns:
            List[str]: List of table names.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in cursor.fetchall()]
                return tables
                
        except Exception as e:
            self._logger.error(f"Failed to get available tables: {e}")
            return []

    def _get_table_columns(self, table_name: str) -> List[str]:
        """
        Get list of columns for a specific table.
        
        Args:
            table_name: Name of the table.
            
        Returns:
            List[str]: List of column names.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]  # Column name is at index 1
                return columns
                
        except Exception as e:
            self._logger.error(f"Failed to get columns for table '{table_name}': {e}")
            return []

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
            # Test database connection
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Verify table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (self._table_name,))
                if not cursor.fetchone():
                    print(f"Error: Table '{self._table_name}' does not exist")
                    return False
                
                # Verify columns exist
                cursor.execute(f"PRAGMA table_info({self._table_name})")
                existing_columns = {row[1] for row in cursor.fetchall()}
                
                required_columns = [self._generated_code_column, self._identifier_column]
                if self._expected_code_column:
                    required_columns.append(self._expected_code_column)
                
                for column in required_columns:
                    if column not in existing_columns:
                        print(f"Error: Column '{column}' does not exist in table '{self._table_name}'")
                        return False
                
                # Test a sample query
                sample_query = f"""
                    SELECT {self._identifier_column}, {self._generated_code_column}
                    {f', {self._expected_code_column}' if self._expected_code_column else ''}
                    FROM {self._table_name} LIMIT 1
                """
                cursor.execute(sample_query)
                
                return True
                
        except Exception as e:
            print(f"Error: Configuration validation failed: {e}")
            return False

    def _load_all_data(self, selected_model: Optional[str] = None, selected_strategy: Optional[str] = None) -> List[CodePair]:
        """
        Load all data from the configured database table.
        
        Args:
            selected_model: Optional specific model to filter by.
            selected_strategy: Optional specific prompting strategy to filter by.
        
        Returns:
            List[CodePair]: List of all code pairs.
        """
        code_pairs = []
        skipped_count = 0
        processed_count = 0
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build query with all configured columns
                columns = [self._identifier_column, self._generated_code_column]
                if self._expected_code_column:
                    columns.append(self._expected_code_column)
                if self._input_code_column:
                    columns.append(self._input_code_column)
                if self._model_column:
                    columns.append(self._model_column)
                if self._prompting_strategy_column:
                    columns.append(self._prompting_strategy_column)
                
                # Build WHERE clause for filtering
                where_conditions = []
                query_params = []
                
                if selected_model and self._model_column:
                    where_conditions.append(f"{self._model_column} = ?")
                    query_params.append(selected_model)
                
                if selected_strategy and self._prompting_strategy_column:
                    where_conditions.append(f"{self._prompting_strategy_column} = ?")
                    query_params.append(selected_strategy)
                
                where_clause = f" WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
                query = f"SELECT {', '.join(columns)} FROM {self._table_name}{where_clause}"
                
                # Debug logging for query
                self._logger.debug(f"Executing query: {query}")
                self._logger.debug(f"Query parameters: {query_params}")
                
                cursor.execute(query, query_params)
                
                for row in cursor.fetchall():
                    processed_count += 1
                    try:
                        # Get row data by column name (row is a sqlite3.Row object)
                        identifier = str(row[0]) if row[0] else ""  # First column is identifier
                        generated_code = str(row[1]) if row[1] else ""  # Second column is generated code
                        expected_code = None
                        input_code = None
                        
                        # Handle expected code (third column if present)
                        col_index = 2
                        if self._expected_code_column and len(row) > col_index:
                            if row[col_index]:
                                expected_code = str(row[col_index])
                            col_index += 1
                        
                        # Handle input code (fourth column if present)
                        if self._input_code_column and len(row) > col_index:
                            if row[col_index]:
                                input_code = str(row[col_index])
                            col_index += 1
                        
                        # Handle model column (fifth column if present)
                        model_name = None
                        if self._model_column and len(row) > col_index:
                            if row[col_index]:
                                model_name = str(row[col_index])
                            col_index += 1
                        
                        # Handle prompting strategy column (sixth column if present)
                        prompting_strategy = None
                        if self._prompting_strategy_column and len(row) > col_index:
                            if row[col_index]:
                                prompting_strategy = str(row[col_index])
                        
                        # Skip rows with empty identifier (but allow empty generated_code for review)
                        if not identifier:
                            skipped_count += 1
                            self._logger.warning(f"Skipping row {processed_count} with empty identifier")
                            continue
                        
                        # Allow empty generated_code - it's a valid failure case for review
                        if not generated_code:
                            generated_code = ""  # Ensure it's an empty string, not None
                            self._logger.debug(f"Row {processed_count} has empty generated_code - including for review as failure case")
                        
                        # Debug logging for input code
                        if input_code:
                            self._logger.debug(f"Loaded input code for {identifier}: {len(input_code)} characters")
                        else:
                            self._logger.debug(f"No input code for {identifier}")
                        
                        source_info = {
                            'source_type': 'sqlite',
                            'database_path': self._db_path,
                            'table_name': self._table_name,
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
                            skipped_count += 1
                            self._logger.warning(f"Skipping invalid code pair with identifier: {identifier} "
                                               f"(validation failed)")
                            
                    except Exception as e:
                        skipped_count += 1
                        self._logger.error(f"Error processing row {processed_count}: {e}")
                        continue
                        
        except Exception as e:
            raise DataSourceError(f"Failed to load data from database: {e}")
        
        self._logger.info(f"_load_all_data completed: processed {processed_count} rows, "
                          f"loaded {len(code_pairs)} valid code pairs, skipped {skipped_count} invalid rows")
        return code_pairs

    def __del__(self):
        """Clean up database connection on destruction."""
        if hasattr(self, '_connection') and self._connection:
            try:
                self._connection.close()
            except Exception:
                pass  # Ignore cleanup errors