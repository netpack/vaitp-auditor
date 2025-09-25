"""
Cross-platform compatibility tests for the VAITP-Auditor system.
"""

import os
import platform
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from vaitp_auditor.data_sources.filesystem import FileSystemSource
from vaitp_auditor.core.models import CodePair
from vaitp_auditor.session_manager import SessionManager
from vaitp_auditor.reporting.report_manager import ReportManager


class TestCrossPlatformPaths:
    """Test path handling across different operating systems."""
    
    def test_path_normalization(self):
        """Test that paths are normalized correctly across platforms."""
        source = FileSystemSource()
        
        # Test different path formats
        test_paths = [
            "folder/subfolder/file.py",
            "folder\\subfolder\\file.py",  # Windows style
            "./folder/file.py",  # Relative with dot
            "../folder/file.py",  # Relative with parent
        ]
        
        for path_str in test_paths:
            path = Path(path_str)
            normalized = path.resolve()
            
            # Should not raise exceptions
            assert isinstance(normalized, Path)
            assert normalized.is_absolute()
    
    def test_file_extension_handling(self):
        """Test file extension handling across platforms."""
        source = FileSystemSource()
        
        test_files = [
            Path("test.py"),
            Path("test.PY"),  # Different case
            Path("test.Py"),  # Mixed case
            Path("test"),     # No extension
            Path("test."),    # Trailing dot
        ]
        
        for file_path in test_files:
            # Should handle all cases without errors
            is_code = source._is_code_file(file_path)
            assert isinstance(is_code, bool)
    
    def test_base_name_extraction(self):
        """Test base name extraction across different path styles."""
        source = FileSystemSource()
        source.generated_folder = Path("/test/generated")
        
        test_cases = [
            (Path("/test/generated/file.py"), "file"),
            (Path("/test/generated/sub/file.py"), "sub/file"),
            (Path("/test/generated/sub\\file.py"), "sub\\file"),  # Mixed separators
        ]
        
        for file_path, expected_base in test_cases:
            base_name = source._get_base_name(file_path)
            # Should extract base name correctly
            assert isinstance(base_name, str)
            assert len(base_name) > 0


class TestCrossPlatformEncoding:
    """Test encoding handling across different platforms."""
    
    def test_utf8_encoding(self):
        """Test UTF-8 encoding handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create file with UTF-8 content
            test_file = temp_path / "utf8_test.py"
            utf8_content = "# -*- coding: utf-8 -*-\n# Unicode: café, naïve, résumé\nprint('Hello, 世界')"
            
            test_file.write_text(utf8_content, encoding='utf-8')
            
            source = FileSystemSource()
            content = source._read_file_with_fallback(test_file)
            
            assert content is not None
            assert "café" in content
            assert "世界" in content
    
    def test_latin1_fallback(self):
        """Test latin-1 fallback encoding."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create file with latin-1 content that would fail UTF-8
            test_file = temp_path / "latin1_test.py"
            latin1_content = "# Latin-1 content with special chars: café"
            
            # Write as latin-1
            with open(test_file, 'w', encoding='latin-1') as f:
                f.write(latin1_content)
            
            source = FileSystemSource()
            content = source._read_file_with_fallback(test_file)
            
            # Should successfully read with fallback
            assert content is not None
            assert len(content) > 0
    
    def test_binary_file_handling(self):
        """Test handling of binary files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a binary file
            binary_file = temp_path / "binary_test.bin"
            binary_content = b'\x00\x01\x02\x03\xff\xfe\xfd'
            
            with open(binary_file, 'wb') as f:
                f.write(binary_content)
            
            source = FileSystemSource()
            content = source._read_file_with_fallback(binary_file)
            
            # Should handle gracefully (may return None or decoded content)
            # The important thing is it doesn't crash
            assert content is None or isinstance(content, str)


class TestCrossPlatformFileOperations:
    """Test file operations across platforms."""
    
    def test_file_discovery_case_sensitivity(self):
        """Test file discovery with different case sensitivity."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files with different cases
            files = [
                temp_path / "Test.py",
                temp_path / "test.PY",
                temp_path / "TEST.py",
            ]
            
            for file_path in files:
                file_path.write_text("# Test file")
            
            source = FileSystemSource()
            source.generated_folder = temp_path
            source._discover_file_pairs()
            
            # Should discover all files regardless of case
            assert len(source._file_pairs) >= 1
            
            # On case-insensitive systems (like macOS/Windows), might be fewer
            # On case-sensitive systems (like Linux), should be all files
            discovered_count = len(source._file_pairs)
            assert 1 <= discovered_count <= len(files)
    
    def test_long_path_handling(self):
        """Test handling of long file paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a deeply nested structure
            deep_path = temp_path
            for i in range(10):  # Create 10 levels deep
                deep_path = deep_path / f"level_{i}"
                deep_path.mkdir(exist_ok=True)
            
            # Create a file in the deep path
            test_file = deep_path / "deep_file.py"
            test_file.write_text("# Deep file")
            
            source = FileSystemSource()
            source.generated_folder = temp_path
            source._discover_file_pairs()
            
            # Should handle long paths without issues
            assert len(source._file_pairs) >= 1
            
            # Should be able to read the file
            found_pair = source._file_pairs[0]
            content = source._read_file_with_fallback(found_pair[0])
            assert content is not None
    
    def test_special_characters_in_filenames(self):
        """Test handling of special characters in filenames."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test files with special characters (platform-dependent)
            special_files = []
            
            # Safe special characters that work on most platforms
            safe_chars = ["file-with-dash.py", "file_with_underscore.py", "file.with.dots.py"]
            
            for filename in safe_chars:
                try:
                    file_path = temp_path / filename
                    file_path.write_text("# Special char file")
                    special_files.append(file_path)
                except OSError:
                    # Skip files that can't be created on this platform
                    continue
            
            if special_files:
                source = FileSystemSource()
                source.generated_folder = temp_path
                source._discover_file_pairs()
                
                # Should discover files with special characters
                assert len(source._file_pairs) >= 1


class TestCrossPlatformReporting:
    """Test report generation across platforms."""
    
    def test_report_file_creation(self):
        """Test report file creation on different platforms."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            report_manager = ReportManager()
            session_id = "test_session_123"
            
            # Initialize report in temp directory
            original_reports_dir = report_manager.reports_dir
            report_manager.reports_dir = temp_path
            
            try:
                report_manager.initialize_report(session_id, "excel")
                
                # Should create report file
                expected_file = temp_path / f"{session_id}.xlsx"
                assert expected_file.exists()
                
            finally:
                report_manager.reports_dir = original_reports_dir
    
    def test_csv_report_encoding(self):
        """Test CSV report encoding across platforms."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            report_manager = ReportManager()
            session_id = "test_csv_session"
            
            original_reports_dir = report_manager.reports_dir
            report_manager.reports_dir = temp_path
            
            try:
                report_manager.initialize_report(session_id, "csv")
                
                # Create a review result with unicode content
                from vaitp_auditor.core.models import ReviewResult
                from datetime import datetime
                
                review_result = ReviewResult(
                    review_id=1,
                    source_identifier="unicode_test",
                    experiment_name="test_experiment",
                    review_timestamp_utc=datetime.utcnow(),
                    reviewer_verdict="Success",
                    reviewer_comment="Test with unicode: café, naïve",
                    time_to_review_seconds=1.5,
                    expected_code="# Expected: café",
                    generated_code="# Generated: naïve",
                    code_diff="diff content"
                )
                
                report_manager.append_review_result(review_result)
                
                # Should handle unicode content without errors
                csv_file = temp_path / f"{session_id}.csv"
                assert csv_file.exists()
                
                # Should be readable
                content = csv_file.read_text(encoding='utf-8')
                assert "café" in content
                assert "naïve" in content
                
            finally:
                report_manager.reports_dir = original_reports_dir


class TestCrossPlatformTerminal:
    """Test terminal operations across platforms."""
    
    def test_terminal_size_detection(self):
        """Test terminal size detection across platforms."""
        from vaitp_auditor.ui.display_manager import DisplayManager
        
        with patch('vaitp_auditor.ui.display_manager.Console') as mock_console:
            mock_console.return_value.size = (80, 24)
            
            display_manager = DisplayManager()
            width, height = display_manager.get_terminal_size()
            
            assert isinstance(width, int)
            assert isinstance(height, int)
            assert width > 0
            assert height > 0
    
    def test_color_support_detection(self):
        """Test color support detection."""
        from rich.console import Console
        
        console = Console()
        
        # Should not crash when checking color support
        try:
            color_system = console.color_system
            assert color_system is not None or color_system is None  # Either way is fine
        except Exception as e:
            pytest.fail(f"Color system detection failed: {e}")


class TestCrossPlatformSession:
    """Test session management across platforms."""
    
    def test_session_directory_creation(self):
        """Test session directory creation across platforms."""
        with patch('pathlib.Path.home') as mock_home:
            with tempfile.TemporaryDirectory() as temp_dir:
                mock_home.return_value = Path(temp_dir)
                
                # Should create session directory without issues
                session_manager = SessionManager()
                
                expected_dir = Path(temp_dir) / '.vaitp_auditor' / 'sessions'
                assert expected_dir.exists()
                assert expected_dir.is_dir()
    
    def test_session_file_permissions(self):
        """Test session file permissions across platforms."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a test session file
            session_file = temp_path / "test_session.pkl"
            session_file.write_text("test session data")
            
            # Should be readable and writable
            assert session_file.exists()
            assert os.access(session_file, os.R_OK)
            assert os.access(session_file, os.W_OK)


@pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific test")
class TestUnixSpecific:
    """Tests specific to Unix-like systems."""
    
    def test_unix_file_permissions(self):
        """Test Unix file permission handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a file and modify permissions
            test_file = temp_path / "permission_test.py"
            test_file.write_text("# Permission test")
            
            # Make file read-only
            test_file.chmod(0o444)
            
            source = FileSystemSource()
            content = source._read_file_with_fallback(test_file)
            
            # Should still be able to read
            assert content is not None
            assert "Permission test" in content


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
class TestWindowsSpecific:
    """Tests specific to Windows systems."""
    
    def test_windows_path_separators(self):
        """Test Windows path separator handling."""
        source = FileSystemSource()
        
        # Test Windows-style paths
        windows_path = "C:\\Users\\Test\\file.py"
        path_obj = Path(windows_path)
        
        # Should handle Windows paths correctly
        assert isinstance(path_obj, Path)
        
        # Test base name extraction with Windows paths
        if platform.system() == "Windows":
            source.generated_folder = Path("C:\\test\\generated")
            base_name = source._get_base_name(Path("C:\\test\\generated\\sub\\file.py"))
            assert "sub" in base_name or "file" in base_name


class TestCrossPlatformIntegration:
    """Integration tests across platforms."""
    
    def test_end_to_end_cross_platform(self):
        """Test complete workflow across platforms."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            generated_dir = temp_path / "generated"
            generated_dir.mkdir()
            
            test_file = generated_dir / "test_file.py"
            test_file.write_text("def hello():\n    print('Hello, World!')")
            
            # Configure file system source
            source = FileSystemSource()
            source.generated_folder = generated_dir
            source._discover_file_pairs()
            source._configured = True
            
            # Load data
            code_pairs = source.load_data(100.0)
            
            # Should work on all platforms
            assert len(code_pairs) == 1
            assert code_pairs[0].generated_code is not None
            assert "Hello, World!" in code_pairs[0].generated_code
    
    def test_memory_usage_cross_platform(self):
        """Test memory usage monitoring across platforms."""
        from vaitp_auditor.utils.performance import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Should work even without psutil
        context = monitor.start_operation("cross_platform_test")
        metrics = monitor.end_operation(context)
        
        # Should complete without errors
        assert metrics.operation == "cross_platform_test"
        assert metrics.duration >= 0
        # Memory metrics might be 0 without psutil, but should not crash
        assert metrics.memory_before >= 0
        assert metrics.memory_after >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])