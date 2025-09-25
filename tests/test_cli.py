"""
Tests for the CLI entry point and setup wizard.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import sys

from vaitp_auditor.cli import (
    create_argument_parser,
    get_experiment_name,
    get_sampling_percentage,
    get_output_format,
    confirm_configuration,
    display_configuration_summary
)
from vaitp_auditor.core.models import SessionConfig


class TestArgumentParser:
    """Test the command-line argument parser."""
    
    def test_create_argument_parser(self):
        """Test that argument parser is created correctly."""
        parser = create_argument_parser()
        
        assert parser.prog == 'vaitp-auditor'
        assert 'Manual Code Verification Assistant' in parser.description
    
    def test_parser_version(self):
        """Test version argument."""
        parser = create_argument_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--version'])
    
    def test_parser_help(self):
        """Test help argument."""
        parser = create_argument_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--help'])
    
    def test_parser_no_resume_flag(self):
        """Test --no-resume flag parsing."""
        parser = create_argument_parser()
        
        args = parser.parse_args(['--no-resume'])
        assert args.no_resume is True
        
        args = parser.parse_args([])
        assert args.no_resume is False


class TestSetupWizardFunctions:
    """Test individual setup wizard functions."""
    
    @patch('builtins.input')
    def test_get_experiment_name_valid(self, mock_input):
        """Test getting valid experiment name."""
        mock_input.return_value = 'test_experiment'
        
        with patch('vaitp_auditor.cli.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20231201_143000'
            
            result = get_experiment_name()
            
            assert result == 'test_experiment_20231201_143000'
    
    @patch('builtins.input')
    def test_get_experiment_name_with_spaces(self, mock_input):
        """Test experiment name with spaces gets cleaned up."""
        mock_input.return_value = 'my test experiment'
        
        with patch('vaitp_auditor.cli.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20231201_143000'
            
            result = get_experiment_name()
            
            assert result == 'my_test_experiment_20231201_143000'
    
    @patch('builtins.input')
    def test_get_experiment_name_empty_retry(self, mock_input):
        """Test that empty names are rejected and user is prompted again."""
        mock_input.side_effect = ['', 'valid_name']
        
        with patch('vaitp_auditor.cli.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20231201_143000'
            
            result = get_experiment_name()
            
            assert result == 'valid_name_20231201_143000'
            assert mock_input.call_count == 2
    
    @patch('builtins.input')
    def test_get_experiment_name_keyboard_interrupt(self, mock_input):
        """Test keyboard interrupt handling."""
        mock_input.side_effect = KeyboardInterrupt()
        
        result = get_experiment_name()
        
        assert result is None
    
    @patch('builtins.input')
    def test_get_sampling_percentage_default(self, mock_input):
        """Test default sampling percentage."""
        mock_input.return_value = ''
        
        result = get_sampling_percentage()
        
        assert result == 100.0
    
    @patch('builtins.input')
    def test_get_sampling_percentage_valid(self, mock_input):
        """Test valid sampling percentage."""
        mock_input.return_value = '50'
        
        result = get_sampling_percentage()
        
        assert result == 50.0
    
    @patch('builtins.input')
    def test_get_sampling_percentage_float(self, mock_input):
        """Test float sampling percentage."""
        mock_input.return_value = '75.5'
        
        result = get_sampling_percentage()
        
        assert result == 75.5
    
    @patch('builtins.input')
    def test_get_sampling_percentage_invalid_retry(self, mock_input):
        """Test invalid values are rejected and user is prompted again."""
        mock_input.side_effect = ['0', '101', 'invalid', '50']
        
        result = get_sampling_percentage()
        
        assert result == 50.0
        assert mock_input.call_count == 4
    
    @patch('builtins.input')
    def test_get_sampling_percentage_keyboard_interrupt(self, mock_input):
        """Test keyboard interrupt handling."""
        mock_input.side_effect = KeyboardInterrupt()
        
        result = get_sampling_percentage()
        
        assert result is None
    
    @patch('builtins.input')
    def test_get_output_format_default(self, mock_input):
        """Test default output format."""
        mock_input.return_value = ''
        
        result = get_output_format()
        
        assert result == 'excel'
    
    @patch('builtins.input')
    def test_get_output_format_excel(self, mock_input):
        """Test Excel format selection."""
        mock_input.return_value = '1'
        
        result = get_output_format()
        
        assert result == 'excel'
    
    @patch('builtins.input')
    def test_get_output_format_csv(self, mock_input):
        """Test CSV format selection."""
        mock_input.return_value = '2'
        
        result = get_output_format()
        
        assert result == 'csv'
    
    @patch('builtins.input')
    def test_get_output_format_invalid_retry(self, mock_input):
        """Test invalid choices are rejected and user is prompted again."""
        mock_input.side_effect = ['3', 'invalid', '2']
        
        result = get_output_format()
        
        assert result == 'csv'
        assert mock_input.call_count == 3
    
    @patch('builtins.input')
    def test_get_output_format_keyboard_interrupt(self, mock_input):
        """Test keyboard interrupt handling."""
        mock_input.side_effect = KeyboardInterrupt()
        
        result = get_output_format()
        
        assert result is None
    
    @patch('builtins.input')
    def test_confirm_configuration_yes(self, mock_input):
        """Test configuration confirmation - yes."""
        mock_input.return_value = 'y'
        
        result = confirm_configuration()
        
        assert result is True
    
    @patch('builtins.input')
    def test_confirm_configuration_no(self, mock_input):
        """Test configuration confirmation - no."""
        mock_input.return_value = 'n'
        
        result = confirm_configuration()
        
        assert result is False
    
    @patch('builtins.input')
    def test_confirm_configuration_invalid_retry(self, mock_input):
        """Test invalid confirmation responses are rejected."""
        mock_input.side_effect = ['maybe', 'invalid', 'yes']
        
        result = confirm_configuration()
        
        assert result is True
        assert mock_input.call_count == 3
    
    @patch('builtins.input')
    def test_confirm_configuration_keyboard_interrupt(self, mock_input):
        """Test keyboard interrupt handling."""
        mock_input.side_effect = KeyboardInterrupt()
        
        result = confirm_configuration()
        
        assert result is False


class TestConfigurationDisplay:
    """Test configuration display functionality."""
    
    def test_display_configuration_summary(self, capsys):
        """Test configuration summary display."""
        config = SessionConfig(
            experiment_name='test_experiment_20231201_143000',
            data_source_type='folders',
            data_source_params={},
            sample_percentage=75.0,
            output_format='excel'
        )
        
        display_configuration_summary(config)
        
        captured = capsys.readouterr()
        assert 'Configuration Summary' in captured.out
        assert 'test_experiment_20231201_143000' in captured.out
        assert 'File System Folders' in captured.out
        assert '75.0%' in captured.out
        assert 'EXCEL' in captured.out


class TestMainCLIIntegration:
    """Test main CLI integration scenarios."""
    
    @patch('vaitp_auditor.cli.SessionManager')
    @patch('vaitp_auditor.cli.handle_session_resumption')
    @patch('vaitp_auditor.cli.start_new_session')
    @patch('vaitp_auditor.cli.finalize_session')
    def test_main_new_session_flow(self, mock_finalize, mock_start_new, mock_handle_resume, mock_session_manager):
        """Test main function with new session flow."""
        # Mock session resumption to return False (no resumption)
        mock_handle_resume.return_value = False
        
        # Mock session manager
        mock_sm_instance = Mock()
        mock_session_manager.return_value = mock_sm_instance
        
        with patch('sys.argv', ['vaitp-auditor']):
            from vaitp_auditor.cli import main
            
            main()
            
            # Verify the flow
            mock_session_manager.assert_called_once()
            mock_handle_resume.assert_called_once_with(mock_sm_instance)
            mock_start_new.assert_called_once()
            mock_finalize.assert_called_once_with(mock_sm_instance)
    
    @patch('vaitp_auditor.cli.SessionManager')
    @patch('vaitp_auditor.cli.handle_session_resumption')
    @patch('vaitp_auditor.cli.finalize_session')
    def test_main_resume_session_flow(self, mock_finalize, mock_handle_resume, mock_session_manager):
        """Test main function with session resumption flow."""
        # Mock session resumption to return True (session resumed)
        mock_handle_resume.return_value = True
        
        # Mock session manager
        mock_sm_instance = Mock()
        mock_session_manager.return_value = mock_sm_instance
        
        with patch('sys.argv', ['vaitp-auditor']):
            from vaitp_auditor.cli import main
            
            main()
            
            # Verify the flow
            mock_session_manager.assert_called_once()
            mock_handle_resume.assert_called_once_with(mock_sm_instance)
            mock_sm_instance.process_review_queue.assert_called_once()
            mock_finalize.assert_called_once_with(mock_sm_instance)
    
    @patch('vaitp_auditor.cli.SessionManager')
    @patch('vaitp_auditor.cli.handle_session_resumption')
    def test_main_keyboard_interrupt(self, mock_handle_resume, mock_session_manager):
        """Test main function handles keyboard interrupt gracefully."""
        mock_handle_resume.side_effect = KeyboardInterrupt()
        
        with patch('sys.argv', ['vaitp-auditor']):
            with pytest.raises(SystemExit) as exc_info:
                from vaitp_auditor.cli import main
                main()
            
            assert exc_info.value.code == 0
    
    @patch('vaitp_auditor.cli.SessionManager')
    @patch('vaitp_auditor.cli.handle_session_resumption')
    def test_main_exception_handling(self, mock_handle_resume, mock_session_manager):
        """Test main function handles exceptions gracefully."""
        mock_handle_resume.side_effect = Exception("Test error")
        
        with patch('sys.argv', ['vaitp-auditor']):
            with pytest.raises(SystemExit) as exc_info:
                from vaitp_auditor.cli import main
                main()
            
            assert exc_info.value.code == 1
    
    def test_cli_component_integration_verification(self):
        """Test that CLI properly integrates with core components."""
        # This test verifies that the CLI imports and uses the correct components
        # without running the full interactive workflow
        
        from vaitp_auditor.cli import (
            create_argument_parser, 
            run_setup_wizard,
            create_data_source,
            get_experiment_name,
            get_sampling_percentage,
            get_output_format
        )
        from vaitp_auditor.session_manager import SessionManager
        from vaitp_auditor.data_sources.filesystem import FileSystemSource
        from vaitp_auditor.core.models import SessionConfig
        
        # Verify CLI can create argument parser
        parser = create_argument_parser()
        assert parser is not None
        assert parser.prog == 'vaitp-auditor'
        
        # Verify CLI can import and instantiate core components
        session_manager = SessionManager()
        assert session_manager is not None
        
        filesystem_source = FileSystemSource()
        assert filesystem_source is not None
        
        # Verify CLI can create session config
        config = SessionConfig(
            experiment_name="test_integration",
            data_source_type="folders",
            data_source_params={},
            sample_percentage=100.0,
            output_format="excel"
        )
        assert config is not None
        assert config.experiment_name == "test_integration"
        
        # Test individual CLI functions with mocked input
        with patch('builtins.input', return_value="test_experiment"):
            with patch('builtins.print'):
                experiment_name = get_experiment_name()
                assert "test_experiment" in experiment_name
        
        with patch('builtins.input', return_value="50"):
            sampling = get_sampling_percentage()
            assert sampling == 50.0
        
        with patch('builtins.input', return_value="2"):
            output_format = get_output_format()
            assert output_format == "csv"

    @patch('sys.argv', ['vaitp-auditor', '--help'])
    def test_cli_help_display(self):
        """Test that CLI help is displayed correctly."""
        from vaitp_auditor.cli import create_argument_parser
        
        parser = create_argument_parser()
        
        # Verify parser configuration
        assert parser.prog == 'vaitp-auditor'
        assert 'Manual Code Verification Assistant' in parser.description
        
        # Test help output contains expected sections
        help_text = parser.format_help()
        assert 'usage:' in help_text
        assert '--version' in help_text
        assert '--no-resume' in help_text
        assert 'Examples:' in help_text