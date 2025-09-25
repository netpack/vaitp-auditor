"""
End-to-end integration tests for VAITP-Auditor.

This module tests the complete application workflow from setup through completion,
ensuring all components work together correctly.
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from vaitp_auditor.session_manager import SessionManager
from vaitp_auditor.data_sources.filesystem import FileSystemSource
from vaitp_auditor.ui.review_controller import ReviewUIController
from vaitp_auditor.reporting.report_manager import ReportManager
from vaitp_auditor.core.models import SessionConfig, CodePair, ReviewResult


class TestEndToEndIntegration:
    """
    End-to-end integration tests covering complete review sessions.
    
    These tests validate that the walking skeleton works correctly for the
    primary use case of reviewing code pairs from file system sources.
    """

    def test_complete_filesystem_workflow(self):
        """
        Test complete application workflow from setup through completion.
        
        This test wires together SessionManager, FileSystemSource, UI, and 
        ReportManager components to validate the core workflow integration.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test data structure
            generated_dir = temp_path / "generated"
            expected_dir = temp_path / "expected"
            generated_dir.mkdir()
            expected_dir.mkdir()
            
            # Create test files with matching names
            test_files = [
                ("test1", "def vulnerable_func():\n    return eval(input())", "def safe_func():\n    return input()"),
                ("test2", "import os\nos.system('rm -rf /')", "import subprocess\nsubprocess.run(['ls'], check=True)"),
                ("test3", "password = 'admin123'", "password = os.environ.get('PASSWORD')")
            ]
            
            for name, generated_code, expected_code in test_files:
                (generated_dir / f"{name}.py").write_text(generated_code)
                (expected_dir / f"{name}.py").write_text(expected_code)
            
            # Create session configuration
            config = SessionConfig(
                experiment_name="test_experiment_20241201_120000",
                data_source_type="folders",
                data_source_params={},
                sample_percentage=100.0,
                output_format="excel"
            )
            
            # Create and configure data source
            data_source = FileSystemSource()
            
            # Mock user input for data source configuration
            with patch('builtins.input', side_effect=[
                str(generated_dir),  # Generated folder path
                str(expected_dir)    # Expected folder path
            ]):
                with patch('builtins.print'):  # Suppress output
                    assert data_source.configure() is True
            
            # Verify data source is properly configured
            assert data_source.get_total_count() == 3
            
            # Create mock UI controller that simulates user reviews
            mock_ui_controller = MagicMock(spec=ReviewUIController)
            
            # Define mock review responses
            mock_reviews = [
                ReviewResult(
                    review_id=1,
                    source_identifier="test1",
                    experiment_name=config.experiment_name,
                    review_timestamp_utc=datetime.utcnow(),
                    reviewer_verdict="Success",
                    reviewer_comment="Good fix for eval vulnerability",
                    time_to_review_seconds=15.5,
                    expected_code="def safe_func():\n    return input()",
                    generated_code="def vulnerable_func():\n    return eval(input())",
                    code_diff="- def vulnerable_func():\n-     return eval(input())\n+ def safe_func():\n+     return input()"
                ),
                ReviewResult(
                    review_id=2,
                    source_identifier="test2",
                    experiment_name=config.experiment_name,
                    review_timestamp_utc=datetime.utcnow(),
                    reviewer_verdict="Partial Success",
                    reviewer_comment="Better but could use more validation",
                    time_to_review_seconds=22.3,
                    expected_code="import subprocess\nsubprocess.run(['ls'], check=True)",
                    generated_code="import os\nos.system('rm -rf /')",
                    code_diff="- import os\n- os.system('rm -rf /')\n+ import subprocess\n+ subprocess.run(['ls'], check=True)"
                ),
                ReviewResult(
                    review_id=3,
                    source_identifier="test3",
                    experiment_name=config.experiment_name,
                    review_timestamp_utc=datetime.utcnow(),
                    reviewer_verdict="Success",
                    reviewer_comment="Proper environment variable usage",
                    time_to_review_seconds=8.7,
                    expected_code="password = os.environ.get('PASSWORD')",
                    generated_code="password = 'admin123'",
                    code_diff="- password = 'admin123'\n+ password = os.environ.get('PASSWORD')"
                )
            ]
            
            # Configure mock UI controller to return our test reviews
            mock_ui_controller.display_code_pair.side_effect = mock_reviews
            
            # Create mock report manager to capture results
            mock_report_manager = MagicMock(spec=ReportManager)
            
            # Create session manager with mocked components
            session_manager = SessionManager(
                ui_controller=mock_ui_controller,
                report_manager=mock_report_manager
            )
            
            # Start the session
            session_id = session_manager.start_session(config, data_source)
            
            # Verify session was created
            assert session_id is not None
            assert config.experiment_name in session_id
            
            # Verify session progress before processing
            progress = session_manager.get_session_progress()
            assert progress is not None
            assert progress['total_reviews'] == 3
            assert progress['completed_reviews'] == 0
            assert progress['remaining_reviews'] == 3
            assert progress['progress_percentage'] == 0.0
            
            # Process the review queue
            session_manager.process_review_queue()
            
            # Verify all reviews were processed
            assert mock_ui_controller.display_code_pair.call_count == 3
            assert mock_report_manager.append_review_result.call_count == 3
            
            # Verify session progress after processing
            final_progress = session_manager.get_session_progress()
            assert final_progress['completed_reviews'] == 3
            assert final_progress['remaining_reviews'] == 0
            assert final_progress['progress_percentage'] == 100.0
            
            # Verify report manager was initialized correctly
            mock_report_manager.initialize_report.assert_called_once_with(session_id, 'excel')
            
            # Verify all review results were passed to report manager
            for i, expected_review in enumerate(mock_reviews):
                call_args = mock_report_manager.append_review_result.call_args_list[i]
                actual_review = call_args[0][0]  # First positional argument
                
                # Verify key fields match (allowing for generated review_id)
                assert actual_review.source_identifier == expected_review.source_identifier
                assert actual_review.experiment_name == expected_review.experiment_name
                assert actual_review.reviewer_verdict == expected_review.reviewer_verdict
                assert actual_review.reviewer_comment == expected_review.reviewer_comment
            
            # Finalize session
            mock_report_manager.finalize_report.return_value = "/path/to/report.xlsx"
            report_path = session_manager.finalize_session()
            
            # Verify finalization
            assert report_path == "/path/to/report.xlsx"
            mock_report_manager.finalize_report.assert_called_once_with('excel')

    def test_filesystem_workflow_with_sampling(self):
        """
        Test complete workflow with sampling to verify random selection works.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create larger test dataset
            generated_dir = temp_path / "generated"
            generated_dir.mkdir()
            
            # Create 10 test files
            for i in range(10):
                (generated_dir / f"test{i}.py").write_text(f"def func{i}(): pass")
            
            # Create session configuration with 30% sampling
            config = SessionConfig(
                experiment_name="sampling_test_20241201_120000",
                data_source_type="folders",
                data_source_params={},
                sample_percentage=30.0,
                output_format="csv"
            )
            
            # Create and configure data source
            data_source = FileSystemSource()
            
            with patch('builtins.input', side_effect=[str(generated_dir), ""]):
                with patch('builtins.print'):
                    assert data_source.configure() is True
            
            # Verify total count
            assert data_source.get_total_count() == 10
            
            # Create mock components
            mock_ui_controller = MagicMock(spec=ReviewUIController)
            mock_report_manager = MagicMock(spec=ReportManager)
            
            # Create session manager
            session_manager = SessionManager(
                ui_controller=mock_ui_controller,
                report_manager=mock_report_manager
            )
            
            # Start session
            session_id = session_manager.start_session(config, data_source)
            
            # Verify sampling worked correctly
            progress = session_manager.get_session_progress()
            expected_sample_size = int(10 * 0.30)  # 30% of 10 = 3
            assert progress['total_reviews'] == expected_sample_size
            assert progress['remaining_reviews'] == expected_sample_size
            
            # Mock UI responses for sampled items
            mock_reviews = []
            for i in range(expected_sample_size):
                mock_reviews.append(ReviewResult(
                    review_id=i+1,
                    source_identifier=f"test{i}",
                    experiment_name=config.experiment_name,
                    review_timestamp_utc=datetime.utcnow(),
                    reviewer_verdict="Success",
                    reviewer_comment=f"Review {i+1}",
                    time_to_review_seconds=10.0,
                    expected_code=None,
                    generated_code=f"def func{i}(): pass",
                    code_diff=""
                ))
            
            mock_ui_controller.display_code_pair.side_effect = mock_reviews
            
            # Process reviews
            session_manager.process_review_queue()
            
            # Verify correct number of reviews processed
            assert mock_ui_controller.display_code_pair.call_count == expected_sample_size
            assert mock_report_manager.append_review_result.call_count == expected_sample_size

    def test_session_interruption_and_resumption(self):
        """
        Test session interruption and resumption workflow.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test data
            generated_dir = temp_path / "generated"
            generated_dir.mkdir()
            
            for i in range(5):
                (generated_dir / f"test{i}.py").write_text(f"def func{i}(): pass")
            
            config = SessionConfig(
                experiment_name="interruption_test_20241201_120000",
                data_source_type="folders",
                data_source_params={},
                sample_percentage=100.0,
                output_format="excel"
            )
            
            # Create and configure data source
            data_source = FileSystemSource()
            
            with patch('builtins.input', side_effect=[str(generated_dir), ""]):
                with patch('builtins.print'):
                    assert data_source.configure() is True
            
            # Create mock components
            mock_ui_controller = MagicMock(spec=ReviewUIController)
            mock_report_manager = MagicMock(spec=ReportManager)
            
            # Create session manager
            session_manager = SessionManager(
                ui_controller=mock_ui_controller,
                report_manager=mock_report_manager
            )
            
            # Start session
            session_id = session_manager.start_session(config, data_source)
            
            # Process only 2 reviews, then simulate interruption
            mock_reviews = [
                ReviewResult(
                    review_id=1,
                    source_identifier="test0",
                    experiment_name=config.experiment_name,
                    review_timestamp_utc=datetime.utcnow(),
                    reviewer_verdict="Success",
                    reviewer_comment="First review",
                    time_to_review_seconds=10.0,
                    expected_code=None,
                    generated_code="def func0(): pass",
                    code_diff=""
                ),
                ReviewResult(
                    review_id=2,
                    source_identifier="test1",
                    experiment_name=config.experiment_name,
                    review_timestamp_utc=datetime.utcnow(),
                    reviewer_verdict="Success",
                    reviewer_comment="Second review",
                    time_to_review_seconds=12.0,
                    expected_code=None,
                    generated_code="def func1(): pass",
                    code_diff=""
                )
            ]
            
            # Configure mock to return 2 reviews, then simulate interruption
            mock_ui_controller.display_code_pair.side_effect = [
                mock_reviews[0],  # First review succeeds
                mock_reviews[1],  # Second review succeeds  
                KeyboardInterrupt("Simulated user interruption")  # Third call raises exception
            ]
            
            # Process reviews (should be interrupted after 2)
            session_manager.process_review_queue()
            
            # Verify partial processing
            # KeyboardInterrupt happens on the 3rd call, but it's caught and handled
            assert mock_ui_controller.display_code_pair.call_count == 3  # Called 3 times, 3rd raises exception
            assert mock_report_manager.append_review_result.call_count == 2  # Only 2 successful reviews
            
            # Verify session state shows partial completion
            progress = session_manager.get_session_progress()
            assert progress['completed_reviews'] == 2
            assert progress['remaining_reviews'] == 3  # 3rd item was put back in queue after interruption
            assert progress['progress_percentage'] == 40.0  # 2/5 = 40%
            
            # Save session state
            session_manager.save_session_state()
            
            # Create new session manager to simulate resumption
            new_session_manager = SessionManager(
                ui_controller=mock_ui_controller,
                report_manager=mock_report_manager
            )
            
            # Resume the session
            resume_success = new_session_manager.resume_session(session_id)
            assert resume_success is True
            
            # Verify resumed session state
            resumed_progress = new_session_manager.get_session_progress()
            assert resumed_progress['completed_reviews'] == 2
            assert resumed_progress['remaining_reviews'] == 3
            
            # Reset mock call counts for remaining reviews
            mock_ui_controller.reset_mock()
            mock_report_manager.reset_mock()
            
            # Configure mock for remaining 3 reviews
            remaining_reviews = []
            for i in range(2, 5):
                remaining_reviews.append(ReviewResult(
                    review_id=i+1,
                    source_identifier=f"test{i}",
                    experiment_name=config.experiment_name,
                    review_timestamp_utc=datetime.utcnow(),
                    reviewer_verdict="Success",
                    reviewer_comment=f"Review {i+1}",
                    time_to_review_seconds=10.0,
                    expected_code=None,
                    generated_code=f"def func{i}(): pass",
                    code_diff=""
                ))
            
            mock_ui_controller.display_code_pair.side_effect = remaining_reviews
            
            # Complete the remaining reviews
            new_session_manager.process_review_queue()
            
            # Verify completion
            assert mock_ui_controller.display_code_pair.call_count == 3
            assert mock_report_manager.append_review_result.call_count == 3
            
            final_progress = new_session_manager.get_session_progress()
            assert final_progress['completed_reviews'] == 5
            assert final_progress['remaining_reviews'] == 0
            assert final_progress['progress_percentage'] == 100.0

    def test_error_handling_during_workflow(self):
        """
        Test error handling during the complete workflow.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test data
            generated_dir = temp_path / "generated"
            generated_dir.mkdir()
            
            # Create files with potential encoding issues
            (generated_dir / "test1.py").write_text("def func1(): pass")
            (generated_dir / "test2.py").write_text("def func2(): pass")
            
            config = SessionConfig(
                experiment_name="error_test_20241201_120000",
                data_source_type="folders",
                data_source_params={},
                sample_percentage=100.0,
                output_format="excel"
            )
            
            # Create and configure data source
            data_source = FileSystemSource()
            
            with patch('builtins.input', side_effect=[str(generated_dir), ""]):
                with patch('builtins.print'):
                    assert data_source.configure() is True
            
            # Create mock components
            mock_ui_controller = MagicMock(spec=ReviewUIController)
            mock_report_manager = MagicMock(spec=ReportManager)
            
            # Configure UI controller to succeed on first call, fail on second
            mock_ui_controller.display_code_pair.side_effect = [
                ReviewResult(
                    review_id=1,
                    source_identifier="test1",
                    experiment_name=config.experiment_name,
                    review_timestamp_utc=datetime.utcnow(),
                    reviewer_verdict="Success",
                    reviewer_comment="First review",
                    time_to_review_seconds=10.0,
                    expected_code=None,
                    generated_code="def func1(): pass",
                    code_diff=""
                ),
                Exception("Simulated UI error")  # Second call raises exception
            ]
            
            # Create session manager
            session_manager = SessionManager(
                ui_controller=mock_ui_controller,
                report_manager=mock_report_manager
            )
            
            # Start session
            session_id = session_manager.start_session(config, data_source)
            
            # Process reviews (should handle error gracefully)
            session_manager.process_review_queue()
            
            # Verify first review was processed successfully, second failed
            assert mock_ui_controller.display_code_pair.call_count == 2
            assert mock_report_manager.append_review_result.call_count == 1  # Only first review succeeded
            
            # Verify session continues despite error
            progress = session_manager.get_session_progress()
            assert progress['completed_reviews'] == 1
            # Should have processed both items (one successfully, one with error)
            assert progress['remaining_reviews'] == 0

    def test_real_component_integration(self):
        """
        Test integration with real components (not mocked) to ensure compatibility.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal test data
            generated_dir = temp_path / "generated"
            generated_dir.mkdir()
            
            (generated_dir / "test.py").write_text("print('hello world')")
            
            config = SessionConfig(
                experiment_name="real_component_test_20241201_120000",
                data_source_type="folders",
                data_source_params={},
                sample_percentage=100.0,
                output_format="excel"
            )
            
            # Create real data source
            data_source = FileSystemSource()
            
            with patch('builtins.input', side_effect=[str(generated_dir), ""]):
                with patch('builtins.print'):
                    assert data_source.configure() is True
            
            # Create real report manager with temporary output
            report_manager = ReportManager()
            
            # Mock only the UI controller to avoid interactive input
            mock_ui_controller = MagicMock(spec=ReviewUIController)
            mock_ui_controller.display_code_pair.return_value = ReviewResult(
                review_id=1,
                source_identifier="test",
                experiment_name=config.experiment_name,
                review_timestamp_utc=datetime.utcnow(),
                reviewer_verdict="Success",
                reviewer_comment="Test review",
                time_to_review_seconds=5.0,
                expected_code=None,
                generated_code="print('hello world')",
                code_diff=""
            )
            
            # Create session manager with real report manager
            session_manager = SessionManager(
                ui_controller=mock_ui_controller,
                report_manager=report_manager
            )
            
            # Test complete workflow with real components
            session_id = session_manager.start_session(config, data_source)
            assert session_id is not None
            
            # Process the single review
            session_manager.process_review_queue()
            
            # Verify processing completed
            progress = session_manager.get_session_progress()
            assert progress['completed_reviews'] == 1
            assert progress['remaining_reviews'] == 0
            
            # Test finalization with real report manager
            # Note: This will create actual files in temp directory
            with patch.object(report_manager, 'finalize_report') as mock_finalize:
                mock_finalize.return_value = str(temp_path / "test_report.xlsx")
                report_path = session_manager.finalize_session()
                assert report_path is not None
                mock_finalize.assert_called_once_with('excel')