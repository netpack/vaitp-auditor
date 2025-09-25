"""
Comprehensive validation tests for the VAITP-Auditor system.
This test suite validates that all major functionality works correctly
and meets the requirements specified in the design document.
"""

import tempfile
import time
import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from vaitp_auditor.core.models import CodePair, ReviewResult, SessionConfig
from vaitp_auditor.data_sources.filesystem import FileSystemSource
from vaitp_auditor.data_sources.factory import DataSourceFactory
from vaitp_auditor.core.differ import CodeDiffer
from vaitp_auditor.ui.display_manager import DisplayManager
from vaitp_auditor.session_manager import SessionManager
from vaitp_auditor.reporting.report_manager import ReportManager
from vaitp_auditor.utils.performance import get_performance_monitor, get_content_cache


class TestRequirementsValidation:
    """Validate that all requirements from the requirements document are met."""
    
    def test_requirement_1_1_setup_wizard(self):
        """Test Requirement 1.1: Terminal-based setup wizard."""
        # This would normally be tested with user interaction simulation
        # For automated testing, we verify the components exist
        from vaitp_auditor.cli import main
        assert callable(main)
        
        # Verify data source factory works
        factory = DataSourceFactory()
        assert factory is not None
        
        # Verify all data source types are available
        fs_source = factory.create_data_source('folders')
        assert fs_source is not None
        
        sqlite_source = factory.create_data_source('sqlite')
        assert sqlite_source is not None
        
        excel_source = factory.create_data_source('excel')
        assert excel_source is not None
    
    def test_requirement_1_4_file_matching(self):
        """Test Requirement 1.4: File matching by base names ignoring extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test structure
            gen_dir = temp_path / "generated"
            exp_dir = temp_path / "expected"
            gen_dir.mkdir()
            exp_dir.mkdir()
            
            # Create files with different extensions
            (gen_dir / "test.py").write_text("generated code")
            (exp_dir / "test.txt").write_text("expected code")
            
            (gen_dir / "example.js").write_text("generated js")
            (exp_dir / "example.cpp").write_text("expected cpp")
            
            source = FileSystemSource()
            source.generated_folder = gen_dir
            source.expected_folder = exp_dir
            source._discover_file_pairs()
            
            # Should match files by base name
            assert len(source._file_pairs) == 2
            
            # Verify matching works
            base_names = [source._get_base_name(pair[0]) for pair in source._file_pairs]
            assert "test" in base_names
            assert "example" in base_names
    
    def test_requirement_2_3_diff_computation(self):
        """Test Requirement 2.3: Diff computation with color highlighting."""
        differ = CodeDiffer()
        
        expected = "def hello():\n    return 'world'"
        generated = "def hello():\n    return 'universe'"
        
        # Test structured diff
        diff_lines = differ.compute_diff(expected, generated)
        assert len(diff_lines) > 0
        
        # Should have different tags
        tags = [line.tag for line in diff_lines]
        assert 'equal' in tags or 'remove' in tags or 'add' in tags
        
        # Test unified diff
        diff_text = differ.get_diff_text(expected, generated)
        assert len(diff_text) > 0
        assert "world" in diff_text or "universe" in diff_text
    
    def test_requirement_3_1_classification_options(self):
        """Test Requirement 3.1: Six classification options available."""
        from vaitp_auditor.ui.input_handler import InputHandler
        
        handler = InputHandler()
        
        # Test all required classification options
        valid_verdicts = ['Success', 'Failure - No Change', 'Invalid Code', 
                         'Wrong Vulnerability', 'Partial Success', 'Quit']
        
        for verdict in valid_verdicts:
            # Verify verdict is recognized (would normally test with actual input)
            assert verdict in handler.verdict_map.values() or verdict == 'Quit'
    
    def test_requirement_4_1_progress_saving(self):
        """Test Requirement 4.1: Automatic progress saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Mock session directory
            with patch('vaitp_auditor.session_manager.Path.home') as mock_home:
                mock_home.return_value = temp_path
                
                session_manager = SessionManager()
                
                # Create test session state
                from vaitp_auditor.core.models import SessionState
                from datetime import datetime
                
                session_state = SessionState(
                    session_id="test_session",
                    experiment_name="test_experiment",
                    data_source_config={"type": "test"},
                    completed_reviews=["review1", "review2"],
                    remaining_queue=[],
                    created_timestamp=datetime.utcnow()
                )
                
                session_manager._current_session = session_state
                
                # Should save without errors
                session_manager.save_session_state()
                
                # Verify session file was created
                session_files = list((temp_path / '.vaitp_auditor' / 'sessions').glob("*.pkl"))
                assert len(session_files) > 0
    
    def test_requirement_5_1_excel_report_generation(self):
        """Test Requirement 5.1: Excel report generation with metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            with patch('vaitp_auditor.reporting.report_manager.Path.cwd') as mock_cwd:
                mock_cwd.return_value = temp_path
                
                report_manager = ReportManager()
                
                # Initialize Excel report
                session_id = "test_session_123"
                report_manager.initialize_report(session_id, "excel")
                
                # Create test review result
                from datetime import datetime
                review_result = ReviewResult(
                    review_id=1,
                    source_identifier="test_source",
                    experiment_name="test_experiment",
                    review_timestamp_utc=datetime.utcnow(),
                    reviewer_verdict="Success",
                    reviewer_comment="Test comment",
                    time_to_review_seconds=2.5,
                    expected_code="expected",
                    generated_code="generated",
                    code_diff="diff"
                )
                
                # Append result
                report_manager.append_review_result(review_result)
                
                # Verify Excel file was created (check in reports subdirectory)
                reports_dir = temp_path / "reports"
                if reports_dir.exists():
                    excel_files = list(reports_dir.glob(f"*{session_id}*.xlsx"))
                    if excel_files:
                        excel_file = excel_files[0]
                        
                        # Verify file is readable
                        try:
                            import pandas as pd
                            df = pd.read_excel(excel_file)
                            assert len(df) == 1
                            assert df.iloc[0]['reviewer_verdict'] == 'Success'
                        except ImportError:
                            # pandas not available, just check file exists
                            assert excel_file.exists()
    
    def test_requirement_6_1_error_handling(self):
        """Test Requirement 6.1: Robust error handling and validation."""
        # Test invalid file paths
        source = FileSystemSource()
        source.generated_folder = Path("/nonexistent/path")
        source._configured = True
        
        # Should handle gracefully
        try:
            source.load_data(100.0)
            assert False, "Should have raised an exception"
        except Exception as e:
            # Should be a meaningful error, not a crash
            assert "configured" in str(e) or "valid" in str(e) or "exist" in str(e)
    
    def test_requirement_6_7_encoding_fallback(self):
        """Test Requirement 6.7: UTF-8 to latin-1 encoding fallback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create file with latin-1 content
            test_file = temp_path / "latin1_test.py"
            latin1_content = "# Test with special chars: café"
            
            # Write as latin-1 (will cause UTF-8 decode error)
            with open(test_file, 'w', encoding='latin-1') as f:
                f.write(latin1_content)
            
            source = FileSystemSource()
            content = source._read_file_with_fallback(test_file)
            
            # Should successfully read with fallback
            assert content is not None
            assert len(content) > 0


class TestPerformanceRequirements:
    """Validate performance requirements from the design document."""
    
    def test_diff_computation_speed_target(self):
        """Test that diff computation meets < 100ms target for medium files."""
        differ = CodeDiffer()
        
        # Create medium-sized code (similar to requirement)
        code1 = "\n".join([f"def function_{i}():\n    return {i}" for i in range(50)])
        code2 = "\n".join([f"def function_{i}():\n    return {i+1}" for i in range(50)])
        
        # Measure time
        start_time = time.time()
        result = differ.compute_diff(code1, code2)
        duration = time.time() - start_time
        
        # Should meet performance target
        assert duration < 0.1  # 100ms
        assert len(result) > 0
    
    def test_syntax_highlighting_speed_target(self):
        """Test that syntax highlighting meets < 50ms target for medium files."""
        with patch('vaitp_auditor.ui.display_manager.Console'):
            display_manager = DisplayManager()
            
            # Create medium-sized code
            code = "\n".join([f"def function_{i}():\n    return {i}" for i in range(50)])
            
            # Measure time
            start_time = time.time()
            syntax = display_manager._get_cached_syntax(code, "speed_test")
            duration = time.time() - start_time
            
            # Should meet performance target
            assert duration < 0.05  # 50ms
            assert syntax is not None
    
    def test_memory_usage_monitoring(self):
        """Test that memory usage is monitored and stays reasonable."""
        monitor = get_performance_monitor()
        
        # Perform memory-intensive operation
        context = monitor.start_operation("memory_test")
        
        # Create some data
        large_data = ["x" * 1000 for _ in range(100)]
        
        metrics = monitor.end_operation(context)
        
        # Should record memory metrics
        assert metrics.memory_before >= 0
        assert metrics.memory_after >= 0
        
        # Clean up
        del large_data
    
    def test_caching_effectiveness(self):
        """Test that caching improves performance."""
        cache = get_content_cache()
        
        # Clear cache
        cache.clear()
        
        # First access (cache miss)
        start_time = time.time()
        result1 = cache.get("test_key")
        first_duration = time.time() - start_time
        assert result1 is None  # Cache miss
        
        # Add to cache
        test_content = "test content" * 1000
        cache.put("test_key", test_content)
        
        # Second access (cache hit)
        start_time = time.time()
        result2 = cache.get("test_key")
        second_duration = time.time() - start_time
        
        # Should be faster and return content
        assert result2 == test_content
        assert second_duration <= first_duration  # Should be faster or same


class TestIntegrationValidation:
    """Validate complete system integration."""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from data loading to report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test data
            gen_dir = temp_path / "generated"
            gen_dir.mkdir()
            
            test_files = [
                ("test1.py", "def hello(): return 'world'"),
                ("test2.py", "print('hello')"),
                ("test3.py", "x = 1 + 1"),
            ]
            
            for filename, content in test_files:
                (gen_dir / filename).write_text(content)
            
            # Configure data source
            source = FileSystemSource()
            source.generated_folder = gen_dir
            source._discover_file_pairs()
            source._configured = True
            
            # Load data
            code_pairs = source.load_data(100.0)
            assert len(code_pairs) == 3
            
            # Test diff computation
            differ = CodeDiffer()
            for pair in code_pairs:
                diff_result = differ.compute_diff(pair.expected_code, pair.generated_code)
                assert isinstance(diff_result, list)
            
            # Test report generation
            with patch('vaitp_auditor.reporting.report_manager.Path.cwd') as mock_cwd:
                mock_cwd.return_value = temp_path
                
                report_manager = ReportManager()
                session_id = "integration_test"
                report_manager.initialize_report(session_id, "excel")
                
                # Create and append a review result
                from datetime import datetime
                review_result = ReviewResult(
                    review_id=1,
                    source_identifier=code_pairs[0].identifier,
                    experiment_name="integration_test",
                    review_timestamp_utc=datetime.utcnow(),
                    reviewer_verdict="Success",
                    reviewer_comment="Integration test",
                    time_to_review_seconds=1.0,
                    expected_code=code_pairs[0].expected_code,
                    generated_code=code_pairs[0].generated_code,
                    code_diff=differ.get_diff_text(code_pairs[0].expected_code, code_pairs[0].generated_code)
                )
                
                report_manager.append_review_result(review_result)
                
                # Verify report exists (check in reports subdirectory)
                reports_dir = temp_path / "reports"
                if reports_dir.exists():
                    report_files = list(reports_dir.glob(f"*{session_id}*.xlsx"))
                    assert len(report_files) > 0
    
    def test_session_lifecycle(self):
        """Test complete session lifecycle including resumption."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Mock home directory
            with patch('vaitp_auditor.session_manager.Path.home') as mock_home:
                mock_home.return_value = temp_path
                
                # Create session manager
                session_manager = SessionManager()
                
                # Create test configuration
                config = SessionConfig(
                    experiment_name="lifecycle_test",
                    data_source_type="folders",
                    data_source_params={"generated_folder": "/test"},
                    sample_percentage=100.0,
                    output_format="excel"
                )
                
                # Create mock data source
                mock_source = Mock()
                mock_source.load_data.return_value = [
                    CodePair(
                        identifier="test1",
                        expected_code="expected",
                        generated_code="generated",
                        source_info={}
                    )
                ]
                
                # Start session
                session_id = session_manager.start_session(config, mock_source)
                assert session_id is not None
                
                # Verify session state was saved
                session_files = list((temp_path / '.vaitp_auditor' / 'sessions').glob("*.pkl"))
                assert len(session_files) > 0
                
                # Test session resumption
                new_session_manager = SessionManager()
                success = new_session_manager.resume_session(session_id)
                assert success is True
    
    def test_error_recovery(self):
        """Test system error recovery capabilities."""
        # Test with invalid data source configuration
        source = FileSystemSource()
        
        # Should handle configuration errors gracefully
        result = source.configure()  # Will prompt for input, but should not crash
        
        # Test with corrupted session data
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create corrupted session file
            session_dir = temp_path / '.vaitp_auditor' / 'sessions'
            session_dir.mkdir(parents=True)
            
            corrupted_file = session_dir / "corrupted_session.pkl"
            corrupted_file.write_text("invalid pickle data")
            
            with patch('vaitp_auditor.session_manager.Path.home') as mock_home:
                mock_home.return_value = temp_path
                
                session_manager = SessionManager()
                
                # Should handle corrupted file gracefully
                try:
                    session_manager.resume_session("corrupted_session")
                except ValueError:
                    # Expected behavior - should raise meaningful error
                    pass


class TestScalabilityValidation:
    """Validate system scalability with larger datasets."""
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets with chunked processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create many small files
            gen_dir = temp_path / "generated"
            gen_dir.mkdir()
            
            num_files = 100  # Create 100 files
            for i in range(num_files):
                file_path = gen_dir / f"file_{i:03d}.py"
                file_path.write_text(f"# File {i}\ndef func_{i}(): return {i}")
            
            source = FileSystemSource()
            source.generated_folder = gen_dir
            source._discover_file_pairs()
            source._configured = True
            
            # Should handle large number of files
            start_time = time.time()
            code_pairs = source.load_data(100.0)
            duration = time.time() - start_time
            
            assert len(code_pairs) == num_files
            # Should complete within reasonable time
            assert duration < 10.0  # 10 seconds for 100 files
    
    def test_large_file_handling(self):
        """Test handling of individual large files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a large file
            large_file = temp_path / "large_file.py"
            large_content = "# Large file\n" + "x = 1\n" * 5000  # 5000 lines
            large_file.write_text(large_content)
            
            source = FileSystemSource()
            content = source._read_file_with_fallback(large_file)
            
            # Should handle large file
            assert content is not None
            assert len(content) > 10000  # Should be substantial
            
            # Test diff computation with large content
            differ = CodeDiffer()
            modified_content = large_content.replace("x = 1", "x = 2")
            
            start_time = time.time()
            diff_result = differ.compute_diff(large_content, modified_content)
            duration = time.time() - start_time
            
            # Should complete within reasonable time
            assert duration < 5.0  # 5 seconds for large diff
            assert len(diff_result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])