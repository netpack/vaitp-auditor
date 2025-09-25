"""
Report manager for output file generation and management.
"""

import csv
import os
import tempfile
import threading
import time
import errno
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from ..core.models import ReviewResult

# Handle platform-specific file locking
try:
    import fcntl
    FCNTL_AVAILABLE = True
except ImportError:
    FCNTL_AVAILABLE = False
    # On Windows, we'll use a different approach

try:
    import msvcrt
    MSVCRT_AVAILABLE = True
except ImportError:
    MSVCRT_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class ReportManager:
    """
    Manages output file generation with atomic writes.
    
    Handles both Excel and CSV formats with proper data integrity.
    Supports atomic result appending and undo functionality.
    """

    def __init__(self):
        """Initialize the report manager."""
        self._current_session_id: Optional[str] = None
        self._output_file_path: Optional[str] = None
        self._temp_file_path: Optional[str] = None
        self._output_format: str = 'excel'
        self._lock = threading.Lock()
        self._review_data: List[Dict[str, Any]] = []
        self._last_review_id: Optional[int] = None

    def initialize_report(self, session_id: str, output_format: str = 'excel') -> None:
        """
        Initialize a new report file for the session.
        
        Args:
            session_id: Unique session identifier.
            output_format: Output format ('excel' or 'csv').
            
        Raises:
            ValueError: If output_format is invalid or pandas not available for Excel.
            OSError: If unable to create output directory or temp file.
        """
        if output_format not in ['excel', 'csv']:
            raise ValueError(f"Invalid output format: {output_format}. Must be 'excel' or 'csv'")
        
        if output_format == 'excel' and not PANDAS_AVAILABLE:
            raise ValueError("Excel output requires pandas library. Please install pandas or use CSV format.")
        
        with self._lock:
            self._current_session_id = session_id
            self._output_format = output_format
            self._review_data = []
            self._last_review_id = None
            
            # Create output directory if it doesn't exist
            output_dir = Path("reports")
            try:
                output_dir.mkdir(exist_ok=True)
            except PermissionError:
                # Try alternative locations if reports directory is not writable
                alternative_dirs = [
                    Path.home() / "vaitp_reports",
                    Path.cwd() / "temp_reports",
                    Path("/tmp") / "vaitp_reports" if os.name != 'nt' else Path.cwd() / "temp_reports"
                ]
                
                output_dir = None
                for alt_dir in alternative_dirs:
                    try:
                        alt_dir.mkdir(exist_ok=True)
                        output_dir = alt_dir
                        print(f"Warning: Using alternative output directory: {output_dir}")
                        break
                    except (PermissionError, OSError):
                        continue
                
                if output_dir is None:
                    raise OSError("Unable to create output directory. Please check permissions or specify a writable directory.")
            
            # Generate output file path with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_extension = 'xlsx' if output_format == 'excel' else 'csv'
            filename = f"{session_id}_{timestamp}.{file_extension}"
            self._output_file_path = output_dir / filename
            
            # Create temporary file for atomic operations
            temp_dir = output_dir / "temp"
            try:
                temp_dir.mkdir(exist_ok=True)
                temp_fd, self._temp_file_path = tempfile.mkstemp(
                    suffix=f".{file_extension}",
                    prefix=f"{session_id}_temp_",
                    dir=temp_dir
                )
                os.close(temp_fd)  # Close the file descriptor, we'll manage the file ourselves
            except (PermissionError, OSError) as e:
                raise OSError(f"Unable to create temporary file in {temp_dir}. Error: {e}. "
                            f"Please ensure the directory is writable or try a different location.")
            
            # Initialize the file with headers
            self._write_headers()

    def append_review_result(self, result: ReviewResult) -> None:
        """
        Append a review result to the report file atomically.
        
        Args:
            result: The review result to append.
            
        Raises:
            ValueError: If report not initialized or result validation fails.
            OSError: If unable to write to file.
        """
        if not self._current_session_id or not self._temp_file_path:
            raise ValueError("Report not initialized. Call initialize_report() first.")
        
        # Validate the review result
        if not result.validate_integrity():
            raise ValueError("Invalid review result data")
        
        with self._lock:
            # Convert ReviewResult to dictionary for storage
            result_dict = {
                'review_id': result.review_id,
                'source_identifier': result.source_identifier,
                'experiment_name': result.experiment_name,
                'review_timestamp_utc': result.review_timestamp_utc.isoformat(),
                'reviewer_verdict': result.reviewer_verdict,
                'reviewer_comment': result.reviewer_comment,
                'time_to_review_seconds': result.time_to_review_seconds,
                'expected_code': result.expected_code or '',
                'generated_code': result.generated_code,
                'code_diff': result.code_diff
            }
            
            # Add to in-memory data
            self._review_data.append(result_dict)
            self._last_review_id = result.review_id
            
            # Write to temporary file atomically with locking
            success = self._write_data_to_temp_file_with_locking()
            if not success:
                # Fallback to basic write method
                try:
                    self._write_data_to_temp_file()
                except Exception as e:
                    # If both methods fail, remove the added data and raise
                    self._review_data.pop()
                    if self._review_data:
                        self._last_review_id = self._review_data[-1]['review_id']
                    else:
                        self._last_review_id = None
                    raise OSError(f"Failed to write review result to file: {e}")

    def get_last_review_id(self) -> Optional[int]:
        """
        Get the ID of the last review for undo functionality.
        
        Returns:
            Optional[int]: Last review ID or None if no reviews exist.
        """
        with self._lock:
            return self._last_review_id

    def remove_last_review(self) -> bool:
        """
        Remove the last review from the report (for undo functionality).
        
        Implements atomic undo operations with proper error recovery and
        file locking to handle concurrent access gracefully.
        
        Returns:
            bool: True if removal was successful, False otherwise.
        """
        with self._lock:
            if not self._review_data:
                return False
            
            # Create backup of current state for rollback
            backup_data = self._review_data.copy()
            backup_last_id = self._last_review_id
            
            try:
                # Remove the last review
                removed_review = self._review_data.pop()
                
                # Update last review ID
                if self._review_data:
                    self._last_review_id = self._review_data[-1]['review_id']
                else:
                    self._last_review_id = None
                
                # Attempt to rewrite the temporary file with file locking
                success = self._write_data_to_temp_file_with_locking()
                
                if not success:
                    # Rollback on failure
                    self._review_data = backup_data
                    self._last_review_id = backup_last_id
                    return False
                
                return True
                
            except Exception as e:
                # Rollback on any exception
                self._review_data = backup_data
                self._last_review_id = backup_last_id
                # Log the error but don't raise to maintain graceful degradation
                print(f"Warning: Failed to remove last review due to error: {e}")
                return False

    def finalize_report(self, output_format: Optional[str] = None) -> str:
        """
        Finalize the report and return the output file path.
        
        Args:
            output_format: Final output format ('excel' or 'csv'). 
                          If None, uses the format from initialization.
            
        Returns:
            str: Path to the finalized report file.
            
        Raises:
            ValueError: If report not initialized or invalid format.
            OSError: If unable to finalize the file.
        """
        if not self._current_session_id or not self._temp_file_path:
            raise ValueError("Report not initialized. Call initialize_report() first.")
        
        final_format = output_format or self._output_format
        
        if final_format not in ['excel', 'csv']:
            raise ValueError(f"Invalid output format: {final_format}")
        
        if final_format == 'excel' and not PANDAS_AVAILABLE:
            raise ValueError("Excel output requires pandas library")
        
        with self._lock:
            try:
                # Update output file path if format changed
                if final_format != self._output_format:
                    file_extension = 'xlsx' if final_format == 'excel' else 'csv'
                    self._output_file_path = self._output_file_path.with_suffix(f'.{file_extension}')
                
                # Move temp file to final location
                if Path(self._temp_file_path).exists():
                    # If format conversion is needed, do it now
                    if final_format != self._output_format:
                        self._convert_format(self._temp_file_path, self._output_file_path, final_format)
                    else:
                        # Simple move
                        Path(self._temp_file_path).rename(self._output_file_path)
                else:
                    # Create final file directly if temp doesn't exist
                    self._write_final_file(final_format)
                
                # Clean up temp file if it still exists
                if Path(self._temp_file_path).exists():
                    Path(self._temp_file_path).unlink()
                
                return str(self._output_file_path)
                
            except Exception as e:
                raise OSError(f"Failed to finalize report: {e}")

    def _write_headers(self) -> None:
        """Write column headers to the temporary file."""
        headers = [
            'review_id',
            'source_identifier', 
            'experiment_name',
            'review_timestamp_utc',
            'reviewer_verdict',
            'reviewer_comment',
            'time_to_review_seconds',
            'expected_code',
            'generated_code',
            'code_diff'
        ]
        
        if self._output_format == 'csv':
            with open(self._temp_file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
        elif self._output_format == 'excel' and PANDAS_AVAILABLE:
            # Create empty DataFrame with headers for Excel
            df = pd.DataFrame(columns=headers)
            df.to_excel(self._temp_file_path, index=False, engine='openpyxl')

    def _write_data_to_temp_file(self) -> None:
        """Write all current data to the temporary file."""
        if self._output_format == 'csv':
            self._write_csv_data()
        elif self._output_format == 'excel' and PANDAS_AVAILABLE:
            self._write_excel_data()

    def _write_data_to_temp_file_with_locking(self) -> bool:
        """
        Write all current data to the temporary file with file locking.
        
        Implements proper file locking and permission error handling
        to support concurrent access and graceful degradation.
        
        Returns:
            bool: True if write was successful, False otherwise.
        """
        try:
            if self._output_format == 'csv':
                return self._write_csv_data_with_locking()
            elif self._output_format == 'excel' and PANDAS_AVAILABLE:
                return self._write_excel_data_with_locking()
            else:
                return False
        except (OSError, IOError, PermissionError) as e:
            print(f"Warning: Failed to write to temporary file: {e}")
            if e.errno == errno.EACCES:
                print("Suggestion: Check file permissions or try running with appropriate privileges")
            elif e.errno == errno.ENOSPC:
                print("Suggestion: Free up disk space and try again")
            elif e.errno == errno.EROFS:
                print("Suggestion: The file system is read-only, try a different output directory")
            return False
        except Exception as e:
            print(f"Warning: Unexpected error writing to temporary file: {e}")
            return False

    def _write_csv_data(self) -> None:
        """Write data to CSV format."""
        headers = [
            'review_id',
            'source_identifier', 
            'experiment_name',
            'review_timestamp_utc',
            'reviewer_verdict',
            'reviewer_comment',
            'time_to_review_seconds',
            'expected_code',
            'generated_code',
            'code_diff'
        ]
        
        with open(self._temp_file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for row_data in self._review_data:
                row = [row_data.get(header, '') for header in headers]
                writer.writerow(row)

    def _write_excel_data(self) -> None:
        """Write data to Excel format."""
        if not PANDAS_AVAILABLE:
            raise ValueError("Pandas required for Excel output")
        
        df = pd.DataFrame(self._review_data)
        
        # Ensure proper column order
        column_order = [
            'review_id',
            'source_identifier', 
            'experiment_name',
            'review_timestamp_utc',
            'reviewer_verdict',
            'reviewer_comment',
            'time_to_review_seconds',
            'expected_code',
            'generated_code',
            'code_diff'
        ]
        
        # Reorder columns and fill missing ones
        for col in column_order:
            if col not in df.columns:
                df[col] = ''
        
        df = df[column_order]
        df.to_excel(self._temp_file_path, index=False, engine='openpyxl')

    def _convert_format(self, source_path: str, target_path: Path, target_format: str) -> None:
        """Convert between CSV and Excel formats."""
        if target_format == 'csv':
            # Convert Excel to CSV
            if PANDAS_AVAILABLE:
                df = pd.read_excel(source_path, engine='openpyxl')
                df.to_csv(target_path, index=False)
            else:
                raise ValueError("Pandas required for format conversion")
        elif target_format == 'excel':
            # Convert CSV to Excel
            if PANDAS_AVAILABLE:
                df = pd.read_csv(source_path)
                df.to_excel(target_path, index=False, engine='openpyxl')
            else:
                raise ValueError("Pandas required for Excel output")

    def _write_final_file(self, output_format: str) -> None:
        """Write final file directly from in-memory data."""
        if output_format == 'csv':
            self._write_csv_data_to_path(self._output_file_path)
        elif output_format == 'excel':
            self._write_excel_data_to_path(self._output_file_path)

    def _write_csv_data_to_path(self, file_path: Path) -> None:
        """Write CSV data to specified path."""
        headers = [
            'review_id',
            'source_identifier', 
            'experiment_name',
            'review_timestamp_utc',
            'reviewer_verdict',
            'reviewer_comment',
            'time_to_review_seconds',
            'expected_code',
            'generated_code',
            'code_diff'
        ]
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for row_data in self._review_data:
                row = [row_data.get(header, '') for header in headers]
                writer.writerow(row)

    def _write_excel_data_to_path(self, file_path: Path) -> None:
        """Write Excel data to specified path."""
        if not PANDAS_AVAILABLE:
            raise ValueError("Pandas required for Excel output")
        
        df = pd.DataFrame(self._review_data)
        
        # Ensure proper column order
        column_order = [
            'review_id',
            'source_identifier', 
            'experiment_name',
            'review_timestamp_utc',
            'reviewer_verdict',
            'reviewer_comment',
            'time_to_review_seconds',
            'expected_code',
            'generated_code',
            'code_diff'
        ]
        
        # Reorder columns and fill missing ones
        for col in column_order:
            if col not in df.columns:
                df[col] = ''
        
        df = df[column_order]
        df.to_excel(file_path, index=False, engine='openpyxl')

    def _write_csv_data_with_locking(self) -> bool:
        """
        Write CSV data to temporary file with file locking.
        
        Returns:
            bool: True if write was successful, False otherwise.
        """
        headers = [
            'review_id',
            'source_identifier', 
            'experiment_name',
            'review_timestamp_utc',
            'reviewer_verdict',
            'reviewer_comment',
            'time_to_review_seconds',
            'expected_code',
            'generated_code',
            'code_diff'
        ]
        
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                with open(self._temp_file_path, 'w', newline='', encoding='utf-8') as f:
                    # Attempt to acquire exclusive lock (platform-specific)
                    lock_acquired = self._acquire_file_lock(f)
                    if not lock_acquired:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                            continue
                        else:
                            return False
                    
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    
                    for row_data in self._review_data:
                        row = [row_data.get(header, '') for header in headers]
                        writer.writerow(row)
                    
                    # Lock is automatically released when file is closed
                    return True
                    
            except (OSError, IOError, PermissionError):
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    return False
        
        return False

    def _write_excel_data_with_locking(self) -> bool:
        """
        Write Excel data to temporary file with file locking.
        
        Returns:
            bool: True if write was successful, False otherwise.
        """
        if not PANDAS_AVAILABLE:
            return False
        
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                # Create DataFrame
                df = pd.DataFrame(self._review_data)
                
                # Ensure proper column order
                column_order = [
                    'review_id',
                    'source_identifier', 
                    'experiment_name',
                    'review_timestamp_utc',
                    'reviewer_verdict',
                    'reviewer_comment',
                    'time_to_review_seconds',
                    'expected_code',
                    'generated_code',
                    'code_diff'
                ]
                
                # Reorder columns and fill missing ones
                for col in column_order:
                    if col not in df.columns:
                        df[col] = ''
                
                df = df[column_order]
                
                # Write to temporary file first, then move to avoid corruption
                # Use .xlsx extension for pandas compatibility
                temp_excel_path = f"{self._temp_file_path}.writing.xlsx"
                
                try:
                    df.to_excel(temp_excel_path, index=False, engine='openpyxl')
                    
                    # Remove existing temp file if it exists
                    if os.path.exists(self._temp_file_path):
                        os.unlink(self._temp_file_path)
                    
                    # Atomic move to final temp location
                    os.rename(temp_excel_path, self._temp_file_path)
                    return True
                    
                except (OSError, IOError, PermissionError):
                    # Clean up temporary file if it exists
                    if os.path.exists(temp_excel_path):
                        try:
                            os.unlink(temp_excel_path)
                        except:
                            pass
                    
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        return False
                        
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    return False
        
        return False

    def _acquire_file_lock(self, file_obj) -> bool:
        """
        Acquire an exclusive file lock in a cross-platform manner.
        
        Args:
            file_obj: Open file object to lock.
            
        Returns:
            bool: True if lock was acquired, False otherwise.
        """
        try:
            if FCNTL_AVAILABLE:
                # Unix/Linux/macOS
                fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            elif MSVCRT_AVAILABLE:
                # Windows
                msvcrt.locking(file_obj.fileno(), msvcrt.LK_NBLCK, 1)
                return True
            else:
                # Fallback: no locking available, but don't fail
                return True
        except (OSError, IOError):
            return False