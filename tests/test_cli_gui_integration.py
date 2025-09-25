"""
Integration tests for CLI and GUI mode selection.

Tests the enhanced CLI integration and application entry point functionality
including mode detection, argument parsing, and backward compatibility.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from vaitp_auditor.cli import (
    main,
    should_use_gui_mode,
    launch_gui_mode,
    run_cli_mode,
    create_argument_parser,
    _check_gui_dependencies,
    _is_interactive_environment
)


class TestModeDetection:
    """Test GUI/CLI mode detection logic."""
    
    def test_should_use_gui_mode_explicit_cli_flag(self):
        """Test that --cli flag forces CLI mode."""
        args = Mock()
        args.cli = True
        args.gui = False
        
        result = should_use_gui_mode(args)
        
        assert result is False
    
    def test_should_use_gui_mode_explicit_gui_flag_with_dependencies(self):
        """Test that --gui flag forces GUI mode when dependencies available."""
        args = Mock()
        args.cli = False
        args.gui = True
        
        with patch('vaitp_auditor.cli._check_gui_dependencies', return_value=True):
            result = should_use_gui_mode(args)
            
            assert result is True
    
    def test_should_use_gui_mode_explicit_gui_flag_without_dependencies(self):
        """Test that --gui flag fails when dependencies unavailable."""
        args = Mock()
        args.cli = False
        args.gui = True
        
        with patch('vaitp_auditor.cli._check_gui_dependencies', return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                should_use_gui_mode(args)
            
            assert exc_info.value.code == 1
    
    def test_should_use_gui_mode_default_interactive_with_dependencies(self):
        """Test default behavior in interactive environment with GUI dependencies."""
        args = Mock()
        args.cli = False
        args.gui = False
        
        with patch('vaitp_auditor.cli._is_interactive_environment', return_value=True):
            with patch('vaitp_auditor.cli._check_gui_dependencies', return_value=True):
                result = should_use_gui_mode(args)
                
                assert result is True
    
    def test_should_use_gui_mode_default_interactive_without_dependencies(self):
        """Test default behavior in interactive environment without GUI dependencies."""
        args = Mock()
        args.cli = False
        args.gui = False
        
        with patch('vaitp_auditor.cli._is_interactive_environment', return_value=True):
            with patch('vaitp_auditor.cli._check_gui_dependencies', return_value=False):
                result = should_use_gui_mode(args)
                
                assert result is False
    
    def test_should_use_gui_mode_default_non_interactive(self):
        """Test default behavior in non-interactive environment."""
        args = Mock()
        args.cli = False
        args.gui = False
        
        with patch('vaitp_auditor.cli._is_interactive_environment', return_value=False):
            result = should_use_gui_mode(args)
            
            assert result is False
    
    def test_should_use_gui_mode_exception_handling(self):
        """Test that exceptions in mode detection fall back to CLI mode."""
        args = Mock()
        args.cli = False
        args.gui = False
        
        with patch('vaitp_auditor.cli._is_interactive_environment', side_effect=Exception("Test error")):
            result = should_use_gui_mode(args)
            
            assert result is False


class TestGUIDependencyCheck:
    """Test GUI dependency checking functionality."""
    
    def test_check_gui_dependencies_all_available(self):
        """Test dependency check when all GUI dependencies are available."""
        with patch.dict('sys.modules', {
            'customtkinter': Mock(),
            'pygments': Mock(),
            'PIL': Mock()
        }):
            result = _check_gui_dependencies()
            
            assert result is True
    
    def test_check_gui_dependencies_customtkinter_missing(self):
        """Test dependency check when customtkinter is missing."""
        # Mock the import to raise ImportError for customtkinter
        original_import = __builtins__['__import__']
        
        def mock_import(name, *args, **kwargs):
            if name == 'customtkinter':
                raise ImportError("No module named 'customtkinter'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            result = _check_gui_dependencies()
            
            assert result is False
    
    def test_check_gui_dependencies_pygments_missing(self):
        """Test dependency check when pygments is missing."""
        # Mock the import to raise ImportError for pygments
        original_import = __builtins__['__import__']
        
        def mock_import(name, *args, **kwargs):
            if name == 'pygments':
                raise ImportError("No module named 'pygments'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            result = _check_gui_dependencies()
            
            assert result is False
    
    def test_check_gui_dependencies_pil_missing(self):
        """Test dependency check when PIL is missing."""
        # Mock the import to raise ImportError for PIL
        original_import = __builtins__['__import__']
        
        def mock_import(name, *args, **kwargs):
            if name == 'PIL':
                raise ImportError("No module named 'PIL'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            result = _check_gui_dependencies()
            
            assert result is False


class TestInteractiveEnvironmentDetection:
    """Test interactive environment detection."""
    
    def test_is_interactive_environment_tty_available(self):
        """Test interactive detection when TTY is available."""
        with patch('sys.stdin.isatty', return_value=True):
            with patch('sys.stdout.isatty', return_value=True):
                with patch.dict('os.environ', {}, clear=True):
                    result = _is_interactive_environment()
                    
                    assert result is True
    
    def test_is_interactive_environment_no_stdin_tty(self):
        """Test interactive detection when stdin is not a TTY."""
        with patch('sys.stdin.isatty', return_value=False):
            with patch('sys.stdout.isatty', return_value=True):
                result = _is_interactive_environment()
                
                assert result is False
    
    def test_is_interactive_environment_no_stdout_tty(self):
        """Test interactive detection when stdout is not a TTY."""
        with patch('sys.stdin.isatty', return_value=True):
            with patch('sys.stdout.isatty', return_value=False):
                result = _is_interactive_environment()
                
                assert result is False
    
    def test_is_interactive_environment_ci_detected(self):
        """Test interactive detection in CI environment."""
        with patch('sys.stdin.isatty', return_value=True):
            with patch('sys.stdout.isatty', return_value=True):
                with patch.dict('os.environ', {'CI': 'true'}):
                    result = _is_interactive_environment()
                    
                    assert result is False
    
    def test_is_interactive_environment_github_actions(self):
        """Test interactive detection in GitHub Actions."""
        with patch('sys.stdin.isatty', return_value=True):
            with patch('sys.stdout.isatty', return_value=True):
                with patch.dict('os.environ', {'GITHUB_ACTIONS': 'true'}):
                    result = _is_interactive_environment()
                    
                    assert result is False
    
    def test_is_interactive_environment_ssh_without_display(self):
        """Test interactive detection in SSH without X11 forwarding."""
        with patch('sys.stdin.isatty', return_value=True):
            with patch('sys.stdout.isatty', return_value=True):
                with patch.dict('os.environ', {'SSH_CLIENT': '192.168.1.1 12345 22'}, clear=True):
                    result = _is_interactive_environment()
                    
                    assert result is False
    
    def test_is_interactive_environment_ssh_with_display(self):
        """Test interactive detection in SSH with X11 forwarding."""
        with patch('sys.stdin.isatty', return_value=True):
            with patch('sys.stdout.isatty', return_value=True):
                with patch.dict('os.environ', {
                    'SSH_CLIENT': '192.168.1.1 12345 22',
                    'DISPLAY': ':10.0'
                }):
                    result = _is_interactive_environment()
                    
                    assert result is True
    
    def test_is_interactive_environment_exception_handling(self):
        """Test that exceptions in interactive detection return False."""
        with patch('sys.stdin.isatty', side_effect=Exception("Test error")):
            result = _is_interactive_environment()
            
            assert result is False


class TestArgumentParser:
    """Test enhanced argument parser functionality."""
    
    def test_create_argument_parser_structure(self):
        """Test that argument parser is created with correct structure."""
        parser = create_argument_parser()
        
        assert parser.prog == 'vaitp-auditor'
        assert 'Manual Code Verification Assistant' in parser.description
        
        # Check that help text contains mode information
        help_text = parser.format_help()
        assert '--gui' in help_text
        assert '--cli' in help_text
        assert 'Interface Mode Selection' in help_text
    
    def test_argument_parser_gui_flag(self):
        """Test parsing --gui flag."""
        parser = create_argument_parser()
        
        args = parser.parse_args(['--gui'])
        
        assert args.gui is True
        assert args.cli is False
    
    def test_argument_parser_cli_flag(self):
        """Test parsing --cli flag."""
        parser = create_argument_parser()
        
        args = parser.parse_args(['--cli'])
        
        assert args.cli is True
        assert args.gui is False
    
    def test_argument_parser_mutually_exclusive_flags(self):
        """Test that --gui and --cli are mutually exclusive."""
        parser = create_argument_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--gui', '--cli'])
    
    def test_argument_parser_default_values(self):
        """Test default values when no mode flags provided."""
        parser = create_argument_parser()
        
        args = parser.parse_args([])
        
        assert args.gui is False
        assert args.cli is False
        assert args.debug is False
        assert args.no_resume is False
    
    def test_argument_parser_debug_flag(self):
        """Test parsing --debug flag."""
        parser = create_argument_parser()
        
        args = parser.parse_args(['--debug'])
        
        assert args.debug is True
    
    def test_argument_parser_log_file(self):
        """Test parsing --log-file argument."""
        parser = create_argument_parser()
        
        args = parser.parse_args(['--log-file', '/path/to/log.txt'])
        
        assert args.log_file == '/path/to/log.txt'
    
    def test_argument_parser_no_resume_cli_only(self):
        """Test parsing --no-resume flag (CLI-specific)."""
        parser = create_argument_parser()
        
        args = parser.parse_args(['--no-resume'])
        
        assert args.no_resume is True


class TestGUIModeLaunch:
    """Test GUI mode launch functionality."""
    
    @patch('vaitp_auditor.cli.setup_logging')
    @patch('vaitp_auditor.cli.get_logger')
    def test_launch_gui_mode_success(self, mock_get_logger, mock_setup_logging):
        """Test successful GUI mode launch."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        args = Mock()
        args.debug = False
        args.log_file = None
        
        with patch('vaitp_auditor.gui.gui_app.main') as mock_gui_main:
            launch_gui_mode(args)
            
            mock_setup_logging.assert_called_once()
            mock_gui_main.assert_called_once_with(args)
            mock_logger.info.assert_called_with("Launching VAITP-Auditor in GUI mode")
    
    @patch('vaitp_auditor.cli.setup_logging')
    @patch('vaitp_auditor.cli.get_logger')
    def test_launch_gui_mode_debug_logging(self, mock_get_logger, mock_setup_logging):
        """Test GUI mode launch with debug logging."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        args = Mock()
        args.debug = True
        args.log_file = '/path/to/debug.log'
        
        with patch('vaitp_auditor.gui.gui_app.main') as mock_gui_main:
            launch_gui_mode(args)
            
            mock_setup_logging.assert_called_once_with(
                level="DEBUG",
                console_output=True,
                session_id=None,
                log_file='/path/to/debug.log'
            )
    
    @patch('vaitp_auditor.cli.setup_logging')
    @patch('vaitp_auditor.cli.get_logger')
    def test_launch_gui_mode_import_error(self, mock_get_logger, mock_setup_logging):
        """Test GUI mode launch when GUI module import fails."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        args = Mock()
        args.debug = False
        args.log_file = None
        
        with patch('builtins.__import__', side_effect=ImportError("GUI module not found")):
            with pytest.raises(SystemExit) as exc_info:
                launch_gui_mode(args)
            
            assert exc_info.value.code == 1
            mock_logger.error.assert_called()
    
    @patch('vaitp_auditor.cli.setup_logging')
    @patch('vaitp_auditor.cli.get_logger')
    def test_launch_gui_mode_general_exception(self, mock_get_logger, mock_setup_logging):
        """Test GUI mode launch when general exception occurs."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        args = Mock()
        args.debug = False
        args.log_file = None
        
        with patch('vaitp_auditor.gui.gui_app.main', side_effect=Exception("GUI launch failed")):
            with pytest.raises(SystemExit) as exc_info:
                launch_gui_mode(args)
            
            assert exc_info.value.code == 1
            mock_logger.error.assert_called()


class TestMainEntryPoint:
    """Test main entry point integration."""
    
    @patch('vaitp_auditor.cli.create_argument_parser')
    @patch('vaitp_auditor.cli.should_use_gui_mode')
    @patch('vaitp_auditor.cli.launch_gui_mode')
    @patch('vaitp_auditor.cli.run_cli_mode')
    def test_main_gui_mode_selected(self, mock_run_cli, mock_launch_gui, mock_should_use_gui, mock_create_parser):
        """Test main function when GUI mode is selected."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser
        mock_should_use_gui.return_value = True
        
        main()
        
        mock_create_parser.assert_called_once()
        mock_parser.parse_args.assert_called_once()
        mock_should_use_gui.assert_called_once_with(mock_args)
        mock_launch_gui.assert_called_once_with(mock_args)
        mock_run_cli.assert_not_called()
    
    @patch('vaitp_auditor.cli.create_argument_parser')
    @patch('vaitp_auditor.cli.should_use_gui_mode')
    @patch('vaitp_auditor.cli.launch_gui_mode')
    @patch('vaitp_auditor.cli.run_cli_mode')
    def test_main_cli_mode_selected(self, mock_run_cli, mock_launch_gui, mock_should_use_gui, mock_create_parser):
        """Test main function when CLI mode is selected."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser
        mock_should_use_gui.return_value = False
        
        main()
        
        mock_create_parser.assert_called_once()
        mock_parser.parse_args.assert_called_once()
        mock_should_use_gui.assert_called_once_with(mock_args)
        mock_run_cli.assert_called_once_with(mock_args)
        mock_launch_gui.assert_not_called()


class TestBackwardCompatibility:
    """Test backward compatibility with existing CLI workflows."""
    
    @patch('vaitp_auditor.cli.SessionManager')
    @patch('vaitp_auditor.cli.handle_session_resumption')
    @patch('vaitp_auditor.cli.start_new_session')
    @patch('vaitp_auditor.cli.finalize_session')
    def test_cli_mode_preserves_existing_workflow(self, mock_finalize, mock_start_new, mock_handle_resume, mock_session_manager):
        """Test that CLI mode preserves existing workflow functionality."""
        mock_handle_resume.return_value = False
        mock_sm_instance = Mock()
        mock_session_manager.return_value = mock_sm_instance
        
        args = Mock()
        args.no_resume = False
        
        run_cli_mode(args)
        
        # Verify existing workflow is preserved
        mock_session_manager.assert_called_once()
        mock_handle_resume.assert_called_once_with(mock_sm_instance)
        mock_start_new.assert_called_once()
        mock_finalize.assert_called_once_with(mock_sm_instance)
    
    @patch('sys.argv', ['vaitp-auditor'])
    @patch('vaitp_auditor.cli.should_use_gui_mode')
    @patch('vaitp_auditor.cli.launch_gui_mode')
    def test_no_arguments_defaults_to_gui_when_available(self, mock_launch_gui, mock_should_use_gui):
        """Test that no arguments defaults to GUI mode when available."""
        mock_should_use_gui.return_value = True
        
        main()
        
        mock_launch_gui.assert_called_once()
    
    @patch('sys.argv', ['vaitp-auditor'])
    @patch('vaitp_auditor.cli.should_use_gui_mode')
    @patch('vaitp_auditor.cli.run_cli_mode')
    def test_no_arguments_falls_back_to_cli_when_gui_unavailable(self, mock_run_cli, mock_should_use_gui):
        """Test that no arguments falls back to CLI mode when GUI unavailable."""
        mock_should_use_gui.return_value = False
        
        main()
        
        mock_run_cli.assert_called_once()
    
    def test_existing_cli_arguments_still_work(self):
        """Test that existing CLI arguments are still supported."""
        parser = create_argument_parser()
        
        # Test existing arguments
        args = parser.parse_args(['--debug', '--no-resume'])
        assert args.debug is True
        assert args.no_resume is True
        
        args = parser.parse_args(['--log-file', '/path/to/log'])
        assert args.log_file == '/path/to/log'
        
        # Test version still works
        with pytest.raises(SystemExit):
            parser.parse_args(['--version'])


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""
    
    @patch.dict('os.environ', {'CI': 'true'})
    def test_ci_environment_uses_cli_mode(self):
        """Test that CI environments automatically use CLI mode."""
        with patch('sys.stdin.isatty', return_value=False):
            with patch('vaitp_auditor.cli.run_cli_mode') as mock_run_cli:
                with patch('sys.argv', ['vaitp-auditor']):
                    main()
                    
                    mock_run_cli.assert_called_once()
    
    def test_interactive_terminal_with_gui_deps_uses_gui(self):
        """Test that interactive terminal with GUI deps uses GUI mode."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('sys.stdin.isatty', return_value=True):
                with patch('sys.stdout.isatty', return_value=True):
                    with patch('vaitp_auditor.cli._check_gui_dependencies', return_value=True):
                        with patch('vaitp_auditor.cli.launch_gui_mode') as mock_launch_gui:
                            with patch('sys.argv', ['vaitp-auditor']):
                                main()
                                
                                mock_launch_gui.assert_called_once()
    
    def test_interactive_terminal_without_gui_deps_uses_cli(self):
        """Test that interactive terminal without GUI deps uses CLI mode."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('sys.stdin.isatty', return_value=True):
                with patch('sys.stdout.isatty', return_value=True):
                    with patch('vaitp_auditor.cli._check_gui_dependencies', return_value=False):
                        with patch('vaitp_auditor.cli.run_cli_mode') as mock_run_cli:
                            with patch('sys.argv', ['vaitp-auditor']):
                                main()
                                
                                mock_run_cli.assert_called_once()
    
    @patch('vaitp_auditor.cli._check_gui_dependencies', return_value=True)
    @patch('vaitp_auditor.cli.launch_gui_mode')
    def test_explicit_gui_flag_overrides_environment(self, mock_launch_gui, mock_check_deps):
        """Test that --gui flag overrides environment detection."""
        with patch.dict('os.environ', {'CI': 'true'}):  # CI environment
            with patch('sys.argv', ['vaitp-auditor', '--gui']):
                main()
                
                mock_launch_gui.assert_called_once()
    
    @patch('vaitp_auditor.cli.run_cli_mode')
    def test_explicit_cli_flag_overrides_environment(self, mock_run_cli):
        """Test that --cli flag overrides environment detection."""
        with patch('sys.stdin.isatty', return_value=True):
            with patch('sys.stdout.isatty', return_value=True):
                with patch('vaitp_auditor.cli._check_gui_dependencies', return_value=True):
                    with patch('sys.argv', ['vaitp-auditor', '--cli']):
                        main()
                        
                        mock_run_cli.assert_called_once()