"""
Unit tests for the ReportManager class.
"""

import csv
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from vaitp_auditor.core.models import ReviewResult
from vaitp_auditor.reporting.report_manager import ReportManager

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class TestReportManager(unittest.TestCase):
    """Test cases for ReportManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.report_manager = ReportManager()
        self.test_session_id = "test_session_123"
        
        # Create sample ReviewResult
        self.sample_review_result = ReviewResult(
            review_id=1,
            source_identifier="test_file_1",
            experiment_name="test_experiment",
            review_timestamp_utc=datetime(2023, 1, 1, 12, 0, 0),
            reviewer_verdict="Success",
            reviewer_comment="Test comment",
            time_to_review_seconds=45.5,
            expected_code="def test(): pass",
            generated_code="def test(): return True",
            code_diff="+ return True"
        )
        
        # Create temp directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialize_report_csv(self):
        """Test report initialization with CSV format."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        self.assertEqual(self.report_manager._current_session_id, self.test_session_id)
        self.assertEqual(self.report_manager._output_format, 'csv')
        self.assertIsNotNone(self.report_manager._output_file_path)
        self.assertIsNotNone(self.report_manager._temp_file_path)
        
        # Check that temp file exists and has headers
        self.assertTrue(Path(self.report_manager._temp_file_path).exists())

    @unittest.skipUnless(PANDAS_AVAILABLE, "Pandas not available")
    def test_initialize_report_excel(self):
        """Test report initialization with Excel format."""
        self.report_manager.initialize_report(self.test_session_id, 'excel')
        
        self.assertEqual(self.report_manager._current_session_id, self.test_session_id)
        self.assertEqual(self.report_manager._output_format, 'excel')
        self.assertIsNotNone(self.report_manager._output_file_path)
        self.assertIsNotNone(self.report_manager._temp_file_path)
        
        # Check that temp file exists
        self.assertTrue(Path(self.report_manager._temp_file_path).exists())

    def test_initialize_report_invalid_format(self):
        """Test report initialization with invalid format."""
        with self.assertRaises(ValueError) as context:
            self.report_manager.initialize_report(self.test_session_id, 'invalid')
        
        self.assertIn("Invalid output format", str(context.exception))

    @unittest.skipIf(PANDAS_AVAILABLE, "Test for when pandas is not available")
    def test_initialize_report_excel_without_pandas(self):
        """Test Excel initialization fails without pandas."""
        with self.assertRaises(ValueError) as context:
            self.report_manager.initialize_report(self.test_session_id, 'excel')
        
        self.assertIn("Excel output requires pandas", str(context.exception))

    def test_append_review_result_csv(self):
        """Test appending review results to CSV format."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        # Append a review result
        self.report_manager.append_review_result(self.sample_review_result)
        
        # Check that data was added
        self.assertEqual(len(self.report_manager._review_data), 1)
        self.assertEqual(self.report_manager._last_review_id, 1)
        
        # Check that temp file contains the data
        with open(self.report_manager._temp_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
        self.assertEqual(len(rows), 2)  # Header + 1 data row
        self.assertEqual(rows[1][0], '1')  # review_id
        self.assertEqual(rows[1][1], 'test_file_1')  # source_identifier

    @unittest.skipUnless(PANDAS_AVAILABLE, "Pandas not available")
    def test_append_review_result_excel(self):
        """Test appending review results to Excel format."""
        self.report_manager.initialize_report(self.test_session_id, 'excel')
        
        # Append a review result
        self.report_manager.append_review_result(self.sample_review_result)
        
        # Check that data was added
        self.assertEqual(len(self.report_manager._review_data), 1)
        self.assertEqual(self.report_manager._last_review_id, 1)
        
        # Check that temp file contains the data
        df = pd.read_excel(self.report_manager._temp_file_path, engine='openpyxl')
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['review_id'], 1)
        self.assertEqual(df.iloc[0]['source_identifier'], 'test_file_1')

    def test_append_review_result_without_initialization(self):
        """Test that appending fails without initialization."""
        with self.assertRaises(ValueError) as context:
            self.report_manager.append_review_result(self.sample_review_result)
        
        self.assertIn("Report not initialized", str(context.exception))

    def test_append_multiple_review_results(self):
        """Test appending multiple review results."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        # Create multiple review results
        results = []
        for i in range(3):
            result = ReviewResult(
                review_id=i + 1,
                source_identifier=f"test_file_{i + 1}",
                experiment_name="test_experiment",
                review_timestamp_utc=datetime(2023, 1, 1, 12, i, 0),
                reviewer_verdict="Success",
                reviewer_comment=f"Test comment {i + 1}",
                time_to_review_seconds=45.5 + i,
                expected_code=f"def test_{i}(): pass",
                generated_code=f"def test_{i}(): return True",
                code_diff=f"+ return True {i}"
            )
            results.append(result)
            self.report_manager.append_review_result(result)
        
        # Check that all data was added
        self.assertEqual(len(self.report_manager._review_data), 3)
        self.assertEqual(self.report_manager._last_review_id, 3)

    def test_get_last_review_id(self):
        """Test getting the last review ID."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        # Initially should be None
        self.assertIsNone(self.report_manager.get_last_review_id())
        
        # After adding a review
        self.report_manager.append_review_result(self.sample_review_result)
        self.assertEqual(self.report_manager.get_last_review_id(), 1)

    def test_remove_last_review(self):
        """Test removing the last review (undo functionality)."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        # Add two reviews
        result1 = self.sample_review_result
        result2 = ReviewResult(
            review_id=2,
            source_identifier="test_file_2",
            experiment_name="test_experiment",
            review_timestamp_utc=datetime(2023, 1, 1, 12, 1, 0),
            reviewer_verdict="Failure - No Change",
            reviewer_comment="Test comment 2",
            time_to_review_seconds=30.0,
            expected_code="def test2(): pass",
            generated_code="def test2(): pass",
            code_diff=""
        )
        
        self.report_manager.append_review_result(result1)
        self.report_manager.append_review_result(result2)
        
        # Check initial state
        self.assertEqual(len(self.report_manager._review_data), 2)
        self.assertEqual(self.report_manager._last_review_id, 2)
        
        # Remove last review
        success = self.report_manager.remove_last_review()
        self.assertTrue(success)
        
        # Check state after removal
        self.assertEqual(len(self.report_manager._review_data), 1)
        self.assertEqual(self.report_manager._last_review_id, 1)
        
        # Verify temp file was updated correctly
        with open(self.report_manager._temp_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)  # Header + 1 data row
        self.assertEqual(rows[1][0], '1')  # Only first review should remain
        
        # Remove last remaining review
        success = self.report_manager.remove_last_review()
        self.assertTrue(success)
        
        # Check state after removing all
        self.assertEqual(len(self.report_manager._review_data), 0)
        self.assertIsNone(self.report_manager._last_review_id)
        
        # Verify temp file has only headers
        with open(self.report_manager._temp_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 1)  # Only header row
        
        # Try to remove from empty list
        success = self.report_manager.remove_last_review()
        self.assertFalse(success)

    def test_finalize_report_csv(self):
        """Test finalizing a CSV report."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        self.report_manager.append_review_result(self.sample_review_result)
        
        # Finalize the report
        output_path = self.report_manager.finalize_report()
        
        # Check that output file exists
        self.assertTrue(Path(output_path).exists())
        self.assertTrue(output_path.endswith('.csv'))
        
        # Check content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)  # Header + 1 data row
        self.assertEqual(rows[1][0], '1')  # review_id

    @unittest.skipUnless(PANDAS_AVAILABLE, "Pandas not available")
    def test_finalize_report_excel(self):
        """Test finalizing an Excel report."""
        self.report_manager.initialize_report(self.test_session_id, 'excel')
        self.report_manager.append_review_result(self.sample_review_result)
        
        # Finalize the report
        output_path = self.report_manager.finalize_report()
        
        # Check that output file exists
        self.assertTrue(Path(output_path).exists())
        self.assertTrue(output_path.endswith('.xlsx'))
        
        # Check content
        df = pd.read_excel(output_path, engine='openpyxl')
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['review_id'], 1)

    @unittest.skipUnless(PANDAS_AVAILABLE, "Pandas not available")
    def test_finalize_report_format_conversion(self):
        """Test finalizing with format conversion."""
        # Initialize as CSV but finalize as Excel
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        self.report_manager.append_review_result(self.sample_review_result)
        
        # Finalize as Excel
        output_path = self.report_manager.finalize_report('excel')
        
        # Check that output file exists and is Excel
        self.assertTrue(Path(output_path).exists())
        self.assertTrue(output_path.endswith('.xlsx'))
        
        # Check content
        df = pd.read_excel(output_path, engine='openpyxl')
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['review_id'], 1)

    def test_finalize_report_without_initialization(self):
        """Test that finalizing fails without initialization."""
        with self.assertRaises(ValueError) as context:
            self.report_manager.finalize_report()
        
        self.assertIn("Report not initialized", str(context.exception))

    def test_thread_safety(self):
        """Test thread safety of report operations."""
        import threading
        import time
        
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        results = []
        errors = []
        
        def append_result(review_id):
            try:
                result = ReviewResult(
                    review_id=review_id,
                    source_identifier=f"test_file_{review_id}",
                    experiment_name="test_experiment",
                    review_timestamp_utc=datetime.utcnow(),
                    reviewer_verdict="Success",
                    reviewer_comment=f"Test comment {review_id}",
                    time_to_review_seconds=45.5,
                    expected_code=f"def test_{review_id}(): pass",
                    generated_code=f"def test_{review_id}(): return True",
                    code_diff=f"+ return True {review_id}"
                )
                self.report_manager.append_review_result(result)
                results.append(review_id)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=append_result, args=(i + 1,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)
        self.assertEqual(len(self.report_manager._review_data), 5)

    def test_data_validation(self):
        """Test data validation in append_review_result."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        # Test with invalid ReviewResult (negative review_id)
        with self.assertRaises(ValueError) as context:
            invalid_result = ReviewResult(
                review_id=-1,  # Invalid
                source_identifier="test_file_1",
                experiment_name="test_experiment",
                review_timestamp_utc=datetime(2023, 1, 1, 12, 0, 0),
                reviewer_verdict="Success",
                reviewer_comment="Test comment",
                time_to_review_seconds=45.5,
                expected_code="def test(): pass",
                generated_code="def test(): return True",
                code_diff="+ return True"
            )
        
        self.assertIn("review_id must be non-negative", str(context.exception))
        
        # Test with a valid result that fails integrity check
        # Create a mock result that passes __post_init__ but fails validate_integrity
        valid_result = self.sample_review_result
        
        # Mock the validate_integrity method to return False
        with patch.object(valid_result, 'validate_integrity', return_value=False):
            with self.assertRaises(ValueError) as context:
                self.report_manager.append_review_result(valid_result)
            
            self.assertIn("Invalid review result data", str(context.exception))

    def test_file_path_generation(self):
        """Test that file paths are generated correctly."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        # Check that paths contain session ID and timestamp
        output_path = str(self.report_manager._output_file_path)
        self.assertIn(self.test_session_id, output_path)
        self.assertTrue(output_path.endswith('.csv'))
        
        temp_path = str(self.report_manager._temp_file_path)
        self.assertIn(self.test_session_id, temp_path)

    def test_empty_report_finalization(self):
        """Test finalizing an empty report."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        # Finalize without adding any data
        output_path = self.report_manager.finalize_report()
        
        # Check that output file exists with just headers
        self.assertTrue(Path(output_path).exists())
        
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 1)  # Just header row

    def test_comprehensive_metadata_columns(self):
        """Test that all required metadata columns are present."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        self.report_manager.append_review_result(self.sample_review_result)
        
        output_path = self.report_manager.finalize_report()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Check headers
        expected_headers = [
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
        
        self.assertEqual(rows[0], expected_headers)
        
        # Check data row has all columns
        self.assertEqual(len(rows[1]), len(expected_headers))


    def test_undo_with_file_write_failure(self):
        """Test undo functionality when file write fails."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        # Add a review
        self.report_manager.append_review_result(self.sample_review_result)
        
        # Mock the file write method to fail
        with patch.object(self.report_manager, '_write_data_to_temp_file_with_locking', return_value=False):
            success = self.report_manager.remove_last_review()
            self.assertFalse(success)
            
            # Data should be restored after failed undo
            self.assertEqual(len(self.report_manager._review_data), 1)
            self.assertEqual(self.report_manager._last_review_id, 1)

    def test_undo_data_consistency_on_exception(self):
        """Test that data is properly restored when undo encounters an exception."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        # Add two reviews
        result1 = self.sample_review_result
        result2 = ReviewResult(
            review_id=2,
            source_identifier="test_file_2",
            experiment_name="test_experiment",
            review_timestamp_utc=datetime(2023, 1, 1, 12, 1, 0),
            reviewer_verdict="Success",
            reviewer_comment="Test comment 2",
            time_to_review_seconds=30.0,
            expected_code="def test2(): pass",
            generated_code="def test2(): return True",
            code_diff="+ return True"
        )
        
        self.report_manager.append_review_result(result1)
        self.report_manager.append_review_result(result2)
        
        # Mock the file write method to raise an exception
        with patch.object(self.report_manager, '_write_data_to_temp_file_with_locking', side_effect=Exception("Test exception")):
            success = self.report_manager.remove_last_review()
            self.assertFalse(success)
            
            # Data should be restored after exception
            self.assertEqual(len(self.report_manager._review_data), 2)
            self.assertEqual(self.report_manager._last_review_id, 2)

    def test_concurrent_undo_operations(self):
        """Test thread safety of undo operations."""
        import threading
        import time
        
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        # Add multiple reviews
        for i in range(5):
            result = ReviewResult(
                review_id=i + 1,
                source_identifier=f"test_file_{i + 1}",
                experiment_name="test_experiment",
                review_timestamp_utc=datetime.utcnow(),
                reviewer_verdict="Success",
                reviewer_comment=f"Test comment {i + 1}",
                time_to_review_seconds=45.5,
                expected_code=f"def test_{i}(): pass",
                generated_code=f"def test_{i}(): return True",
                code_diff=f"+ return True {i}"
            )
            self.report_manager.append_review_result(result)
        
        results = []
        errors = []
        
        def undo_operation():
            try:
                success = self.report_manager.remove_last_review()
                results.append(success)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads trying to undo simultaneously
        threads = []
        for i in range(3):
            thread = threading.Thread(target=undo_operation)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results - some should succeed, some should fail gracefully
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 3)
        
        # At least one should succeed, others might fail due to empty list
        success_count = sum(1 for r in results if r)
        self.assertGreaterEqual(success_count, 1)
        
        # Final state should be consistent
        remaining_count = 5 - success_count
        self.assertEqual(len(self.report_manager._review_data), remaining_count)

    def test_file_permission_error_handling(self):
        """Test handling of file permission errors during initialization."""
        # Mock Path.mkdir to raise PermissionError
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            # Mock the alternative directory creation to also fail initially
            with patch('pathlib.Path.home') as mock_home:
                mock_home.return_value = Path("/nonexistent")
                
                # This should try alternatives and eventually succeed with temp_reports
                try:
                    self.report_manager.initialize_report(self.test_session_id, 'csv')
                    # If we get here, it found an alternative directory
                    self.assertIsNotNone(self.report_manager._output_file_path)
                except OSError:
                    # This is expected if all alternatives fail
                    pass

    def test_file_locking_cross_platform(self):
        """Test file locking works across platforms."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        # Test the file locking method directly
        with open(self.report_manager._temp_file_path, 'w') as f:
            lock_acquired = self.report_manager._acquire_file_lock(f)
            # Should return True regardless of platform (fallback behavior)
            self.assertTrue(lock_acquired)

    @unittest.skipUnless(PANDAS_AVAILABLE, "Pandas not available")
    def test_undo_excel_format(self):
        """Test undo functionality with Excel format."""
        self.report_manager.initialize_report(self.test_session_id, 'excel')
        
        # Add two reviews
        result1 = self.sample_review_result
        result2 = ReviewResult(
            review_id=2,
            source_identifier="test_file_2",
            experiment_name="test_experiment",
            review_timestamp_utc=datetime(2023, 1, 1, 12, 1, 0),
            reviewer_verdict="Failure - No Change",
            reviewer_comment="Test comment 2",
            time_to_review_seconds=30.0,
            expected_code="def test2(): pass",
            generated_code="def test2(): pass",
            code_diff=""
        )
        
        self.report_manager.append_review_result(result1)
        self.report_manager.append_review_result(result2)
        
        # Remove last review
        success = self.report_manager.remove_last_review()
        self.assertTrue(success)
        
        # Check state after removal
        self.assertEqual(len(self.report_manager._review_data), 1)
        self.assertEqual(self.report_manager._last_review_id, 1)
        
        # Verify Excel file was updated correctly
        df = pd.read_excel(self.report_manager._temp_file_path, engine='openpyxl')
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['review_id'], 1)

    def test_append_with_write_failure_recovery(self):
        """Test that append_review_result handles write failures gracefully."""
        self.report_manager.initialize_report(self.test_session_id, 'csv')
        
        # Mock both write methods to fail
        with patch.object(self.report_manager, '_write_data_to_temp_file_with_locking', return_value=False):
            with patch.object(self.report_manager, '_write_data_to_temp_file', side_effect=OSError("Write failed")):
                with self.assertRaises(OSError) as context:
                    self.report_manager.append_review_result(self.sample_review_result)
                
                self.assertIn("Failed to write review result to file", str(context.exception))
                
                # Data should not be added if write fails
                self.assertEqual(len(self.report_manager._review_data), 0)
                self.assertIsNone(self.report_manager._last_review_id)


if __name__ == '__main__':
    unittest.main()