"""
Integration tests for GUI application entry point and complete application flow.

Tests the complete workflow from application launch through setup wizard
to main review window, including error handling and cleanup.
"""

import unittest
import sys
import tempfile
import os
from unittest.mock import patch, MagicMock, call
from pathlib import Path

# Mock CustomTkinter before importing GUI modules
sys.modules['customtkinter'] = MagicMock()

from vaitp_auditor.gui.gui_app import GUIApplication, create_argument_parser, main
from vaitp_auditor.core.models import SessionConfig


class TestGUIApplicationIntegration(unittest.TestCase):
    """Test complete GUI application integration and lifecycle."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock all GUI dependencies
        self.ctk_mock = MagicMock()
        self.setup_wizard_mock = MagicMock()
        self.main_review_window_mock = MagicMock()
        self.session_controller_mock = MagicMock()
        
        # Create test session config
        self.test_session_config = SessionConfig(
            experiment_name="test_experiment_20250924_120000",
            data_source_type="folders",
            data_source_params={},
            sample_percentage=100.0,
            output_format="excel"
        )
    
    @patch('vaitp_auditor.gui.gui_app.ctk')
    @patch('vaitp_auditor.gui.gui_app.setup_logging')
    @patch('vaitp_auditor.gui.gui_app.cleanup_resources')
    def test_complete_application_lifecycle(self, mock_cleanup, mock_setup_logging, mock_ctk):
        """Test complete application lifecycle from start to finish."""
        # Setup mocks
        mock_root = MagicMock()
        mock_ctk.CTk.return_value = mock_root
        mock_ctk.set_appearance_mode = MagicMock()
        mock_ctk.set_default_color_theme = MagicMock()
        
        # Create application
        app = GUIApplication()
        
        # Mock setup wizard and main review window
        with patch.object(app, 'launch_setup_wizard') as mock_launch_wizard:
            with patch.object(app, 'handle_application_exit') as mock_exit:
                # Mock mainloop to prevent blocking
                mock_root.mainloop = MagicMock()
                
                # Run application
                app.run()
                
                # Verify initialization
                mock_ctk.set_appearance_mode.assert_called_once_with("system")
                mock_ctk.set_default_color_theme.assert_called_once_with("blue")
                mock_ctk.CTk.assert_called_once()
                mock_root.title.assert_called_once_with("VAITP-Auditor")
                mock_root.geometry.assert_called_once_with("800x600")
                mock_root.withdraw.assert_called_once()
                mock_root.protocol.assert_called_once_with("WM_DELETE_WINDOW", app.handle_application_exit)
                
                # Verify setup wizard launch
                mock_launch_wizard.assert_called_once()
                
                # Verify mainloop started
                mock_root.mainloop.assert_called_once()
    
    @patch('vaitp_auditor.gui.gui_app.ctk')
    def test_setup_wizard_to_main_review_flow(self, mock_ctk):
        """Test seamless flow from Setup Wizard to Main Review Window."""
        # Setup mocks
        mock_root = MagicMock()
        mock_ctk.CTk.return_value = mock_root
        
        app = GUIApplication()
        app.root = mock_root
        
        # Mock setup wizard
        with patch('vaitp_auditor.gui.setup_wizard.SetupWizard') as mock_wizard_class:
            with patch('vaitp_auditor.gui.models.get_default_gui_config') as mock_config:
                mock_wizard = MagicMock()
                mock_wizard_class.return_value = mock_wizard
                mock_config.return_value = {}
                
                # Launch setup wizard
                app.launch_setup_wizard()
                
                # Verify wizard creation and configuration
                mock_wizard_class.assert_called_once_with(mock_root, {})
                mock_wizard.set_completion_callback.assert_called_once_with(app.launch_main_review)
                mock_wizard.set_cancellation_callback.assert_called_once_with(app.handle_application_exit)
        
        # Mock main review window launch
        with patch('vaitp_auditor.gui.main_review_window.MainReviewWindow') as mock_window_class:
            with patch('vaitp_auditor.gui.gui_session_controller.GUISessionController') as mock_controller_class:
                mock_window = MagicMock()
                mock_controller = MagicMock()
                mock_window_class.return_value = mock_window
                mock_controller_class.return_value = mock_controller
                mock_controller.start_session_from_config.return_value = True
                
                # Set up setup wizard mock for destruction
                mock_setup_wizard = MagicMock()
                app.setup_wizard = mock_setup_wizard
                
                # Launch main review
                app.launch_main_review(self.test_session_config)
                
                # Verify setup wizard cleanup
                mock_setup_wizard.destroy.assert_called_once()
                
                # Verify main window setup
                mock_root.deiconify.assert_called_once()
                mock_root.title.assert_called_once_with("VAITP-Auditor")
                
                # Verify main review window creation
                mock_window_class.assert_called_once_with(mock_root)
                
                # Verify session controller creation and start
                mock_controller_class.assert_called_once_with(mock_window)
                mock_controller.start_session_from_config.assert_called_once_with(self.test_session_config)
    
    @patch('vaitp_auditor.gui.gui_app.ctk')
    def test_error_handling_during_setup_wizard_launch(self, mock_ctk):
        """Test error handling when Setup Wizard fails to launch."""
        mock_root = MagicMock()
        mock_ctk.CTk.return_value = mock_root
        
        app = GUIApplication()
        app.root = mock_root
        
        # Mock setup wizard to raise exception
        with patch('vaitp_auditor.gui.setup_wizard.SetupWizard', side_effect=Exception("Setup failed")):
            with patch('vaitp_auditor.gui.error_handler.GUIErrorHandler') as mock_error_handler:
                with patch.object(app, 'handle_application_exit') as mock_exit:
                    
                    # Launch setup wizard (should handle error)
                    app.launch_setup_wizard()
                    
                    # Verify error dialog shown
                    mock_error_handler.show_error_dialog.assert_called_once()
                    
                    # Verify application exit called
                    mock_exit.assert_called_once()
    
    @patch('vaitp_auditor.gui.gui_app.ctk')
    def test_error_handling_during_main_review_launch(self, mock_ctk):
        """Test error handling when Main Review Window fails to launch."""
        mock_root = MagicMock()
        mock_ctk.CTk.return_value = mock_root
        
        app = GUIApplication()
        app.root = mock_root
        app.setup_wizard = MagicMock()
        
        # Mock main review window to raise exception
        with patch('vaitp_auditor.gui.main_review_window.MainReviewWindow', side_effect=Exception("Launch failed")):
            with patch('vaitp_auditor.gui.error_handler.GUIErrorHandler') as mock_error_handler:
                with patch.object(app, 'handle_application_exit') as mock_exit:
                    
                    # Launch main review (should handle error)
                    app.launch_main_review(self.test_session_config)
                    
                    # Verify error dialog shown
                    mock_error_handler.show_error_dialog.assert_called_once()
                    
                    # Verify application exit called
                    mock_exit.assert_called_once()
    
    @patch('vaitp_auditor.gui.gui_app.ctk')
    def test_session_start_failure_handling(self, mock_ctk):
        """Test handling of session start failure."""
        mock_root = MagicMock()
        mock_ctk.CTk.return_value = mock_root
        
        app = GUIApplication()
        app.root = mock_root
        app.setup_wizard = MagicMock()
        
        # Mock components with session start failure
        with patch('vaitp_auditor.gui.main_review_window.MainReviewWindow') as mock_window_class:
            with patch('vaitp_auditor.gui.gui_session_controller.GUISessionController') as mock_controller_class:
                with patch('vaitp_auditor.gui.error_handler.GUIErrorHandler') as mock_error_handler:
                    with patch.object(app, 'handle_application_exit') as mock_exit:
                        
                        mock_window = MagicMock()
                        mock_controller = MagicMock()
                        mock_window_class.return_value = mock_window
                        mock_controller_class.return_value = mock_controller
                        mock_controller.start_session_from_config.return_value = False  # Failure
                        
                        # Launch main review
                        app.launch_main_review(self.test_session_config)
                        
                        # Verify error dialog shown
                        mock_error_handler.show_error_dialog.assert_called_once()
                        
                        # Verify application exit called
                        mock_exit.assert_called_once()
    
    @patch('vaitp_auditor.gui.gui_app.ctk')
    @patch('vaitp_auditor.gui.gui_app.cleanup_resources')
    @patch('sys.exit')
    def test_application_cleanup(self, mock_exit, mock_cleanup, mock_ctk):
        """Test proper application cleanup on exit."""
        mock_root = MagicMock()
        mock_ctk.CTk.return_value = mock_root
        
        app = GUIApplication()
        app.root = mock_root
        app.setup_wizard = MagicMock()
        app.main_review_window = MagicMock()
        app.session_controller = MagicMock()
        
        # Handle application exit
        app.handle_application_exit()
        
        # Verify cleanup calls
        app.session_controller.cleanup.assert_called_once()
        app.setup_wizard.destroy.assert_called_once()
        app.main_review_window.destroy.assert_called_once()
        mock_cleanup.assert_called_once()
        mock_root.quit.assert_called_once()
        mock_root.destroy.assert_called_once()
        mock_exit.assert_called_once_with(0)
    
    @patch('vaitp_auditor.gui.gui_app.ctk')
    @patch('vaitp_auditor.gui.gui_app.cleanup_resources')
    @patch('sys.exit')
    def test_cleanup_with_errors(self, mock_exit, mock_cleanup, mock_ctk):
        """Test cleanup handling when errors occur during cleanup."""
        mock_root = MagicMock()
        mock_ctk.CTk.return_value = mock_root
        
        app = GUIApplication()
        app.root = mock_root
        app.session_controller = MagicMock()
        app.session_controller.cleanup.side_effect = Exception("Cleanup error")
        
        # Handle application exit (should not raise)
        app.handle_application_exit()
        
        # Verify exit called despite errors
        mock_exit.assert_called_once_with(0)
    
    @patch('vaitp_auditor.gui.gui_app.ctk')
    def test_menu_setup_integration(self, mock_ctk):
        """Test menu setup methods exist in GUI app."""
        mock_root = MagicMock()
        mock_ctk.CTk.return_value = mock_root
        
        app = GUIApplication()
        app.root = mock_root
        
        # Verify _setup_menu method exists
        self.assertTrue(hasattr(app, '_setup_menu'))
        self.assertTrue(callable(getattr(app, '_setup_menu')))
        
        # Verify _show_about_dialog method exists
        self.assertTrue(hasattr(app, '_show_about_dialog'))
        self.assertTrue(callable(getattr(app, '_show_about_dialog')))
    
    @patch('vaitp_auditor.gui.about_dialog.show_about_dialog')
    @patch('vaitp_auditor.gui.gui_app.ctk')
    def test_about_dialog_from_gui_app(self, mock_ctk, mock_show_about):
        """Test About dialog can be shown from GUI app."""
        mock_root = MagicMock()
        mock_ctk.CTk.return_value = mock_root
        
        app = GUIApplication()
        app.root = mock_root
        
        # Call _show_about_dialog method
        app._show_about_dialog()
        
        # Verify about dialog was called with correct parent
        mock_show_about.assert_called_once_with(mock_root)
    
    @patch('vaitp_auditor.gui.gui_app.ctk')
    def test_file_menu_methods_exist(self, mock_ctk):
        """Test that File menu methods exist in GUI app."""
        mock_root = MagicMock()
        mock_ctk.CTk.return_value = mock_root
        
        app = GUIApplication()
        app.root = mock_root
        
        # Verify File menu methods exist
        self.assertTrue(hasattr(app, '_save_review_process'))
        self.assertTrue(callable(getattr(app, '_save_review_process')))
        
        self.assertTrue(hasattr(app, '_open_review_process'))
        self.assertTrue(callable(getattr(app, '_open_review_process')))
        
        self.assertTrue(hasattr(app, '_restart_review_process'))
        self.assertTrue(callable(getattr(app, '_restart_review_process')))
    
    @patch('tkinter.messagebox.showwarning')
    @patch('vaitp_auditor.gui.gui_app.ctk')
    def test_save_without_active_session(self, mock_ctk, mock_warning):
        """Test save functionality when no session is active."""
        mock_root = MagicMock()
        mock_ctk.CTk.return_value = mock_root
        
        app = GUIApplication()
        app.root = mock_root
        app.session_controller = None
        
        # Call save method
        app._save_review_process()
        
        # Verify warning was shown
        mock_warning.assert_called_once()
    
    @patch('tkinter.messagebox.showwarning')
    @patch('vaitp_auditor.gui.gui_app.ctk')
    def test_restart_without_active_session(self, mock_ctk, mock_warning):
        """Test restart functionality when no session is active."""
        mock_root = MagicMock()
        mock_ctk.CTk.return_value = mock_root
        
        app = GUIApplication()
        app.root = mock_root
        app.session_controller = None
        
        # Call restart method
        app._restart_review_process()
        
        # Verify warning was shown
        mock_warning.assert_called_once()


class TestCLIGUIIntegration(unittest.TestCase):
    """Test CLI and GUI mode integration."""
    
    def test_argument_parser_gui_cli_modes(self):
        """Test argument parser supports GUI and CLI mode selection."""
        from vaitp_auditor.cli import create_argument_parser
        
        parser = create_argument_parser()
        
        # Test GUI mode
        args = parser.parse_args(['--gui'])
        self.assertTrue(args.gui)
        self.assertFalse(args.cli)
        
        # Test CLI mode
        args = parser.parse_args(['--cli'])
        self.assertTrue(args.cli)
        self.assertFalse(args.gui)
        
        # Test default (no mode specified)
        args = parser.parse_args([])
        self.assertFalse(args.gui)
        self.assertFalse(args.cli)
        
        # Test mutual exclusion
        with self.assertRaises(SystemExit):
            parser.parse_args(['--gui', '--cli'])
    
    @patch('sys.stdin')
    @patch('sys.stdout')
    def test_should_use_gui_mode_logic(self, mock_stdout, mock_stdin):
        """Test GUI mode detection logic."""
        from vaitp_auditor.cli import should_use_gui_mode
        
        # Mock arguments
        args_gui = MagicMock()
        args_gui.gui = True
        args_gui.cli = False
        
        args_cli = MagicMock()
        args_cli.gui = False
        args_cli.cli = True
        
        args_default = MagicMock()
        args_default.gui = False
        args_default.cli = False
        
        # Test explicit GUI mode
        self.assertTrue(should_use_gui_mode(args_gui))
        
        # Test explicit CLI mode
        self.assertFalse(should_use_gui_mode(args_cli))
        
        # Test default with interactive terminal and GUI available
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = True
        
        with patch('builtins.__import__', side_effect=lambda name, *args: MagicMock() if name == 'customtkinter' else __import__(name, *args)):
            self.assertTrue(should_use_gui_mode(args_default))
        
        # Test default with non-interactive terminal
        mock_stdin.isatty.return_value = False
        self.assertFalse(should_use_gui_mode(args_default))
        
        # Test default with GUI not available
        mock_stdin.isatty.return_value = True
        def mock_import(name, *args):
            if name == 'customtkinter':
                raise ImportError("No module named 'customtkinter'")
            return __import__(name, *args)
        
        with patch('builtins.__import__', side_effect=mock_import):
            self.assertFalse(should_use_gui_mode(args_default))
    
    @patch('vaitp_auditor.gui.gui_app.main')
    @patch('vaitp_auditor.cli.setup_logging')
    def test_launch_gui_mode(self, mock_setup_logging, mock_gui_main):
        """Test launching GUI mode from CLI."""
        from vaitp_auditor.cli import launch_gui_mode
        
        # Mock arguments
        args = MagicMock()
        args.debug = True
        args.log_file = "test.log"
        
        # Launch GUI mode
        launch_gui_mode(args)
        
        # Verify logging setup
        mock_setup_logging.assert_called_once_with(
            level="DEBUG",
            console_output=True,
            session_id=None,
            log_file="test.log"
        )
        
        # Verify GUI main called
        mock_gui_main.assert_called_once()
    
    @patch('vaitp_auditor.gui.gui_app.main', side_effect=ImportError("GUI not available"))
    @patch('sys.exit')
    @patch('builtins.print')
    def test_launch_gui_mode_import_error(self, mock_print, mock_exit, mock_gui_main):
        """Test GUI mode launch with import error."""
        from vaitp_auditor.cli import launch_gui_mode
        
        args = MagicMock()
        
        # Launch GUI mode (should handle error)
        launch_gui_mode(args)
        
        # Verify error handling
        mock_print.assert_called()
        mock_exit.assert_called_with(1)


class TestMainEntryPointIntegration(unittest.TestCase):
    """Test main entry point integration."""
    
    @patch('vaitp_auditor.gui.gui_app.GUIApplication')
    @patch('vaitp_auditor.gui.gui_app.setup_logging')
    @patch('sys.argv', ['vaitp-auditor-gui', '--debug'])
    def test_gui_main_function(self, mock_setup_logging, mock_gui_app_class):
        """Test GUI main function with debug flag."""
        from vaitp_auditor.gui.gui_app import main
        
        mock_app = MagicMock()
        mock_gui_app_class.return_value = mock_app
        
        # Run main function
        main()
        
        # Verify logging setup
        mock_setup_logging.assert_called_once()
        
        # Verify app creation and run
        mock_gui_app_class.assert_called_once()
        mock_app.run.assert_called_once()
    
    @patch('vaitp_auditor.cli.should_use_gui_mode', return_value=True)
    @patch('vaitp_auditor.cli.launch_gui_mode')
    @patch('sys.argv', ['vaitp-auditor'])
    def test_cli_main_launches_gui(self, mock_launch_gui, mock_should_use_gui):
        """Test CLI main function launches GUI when appropriate."""
        from vaitp_auditor.cli import main
        
        # Run main function
        main()
        
        # Verify GUI mode detection and launch
        mock_should_use_gui.assert_called_once()
        mock_launch_gui.assert_called_once()
    
    @patch('vaitp_auditor.cli.should_use_gui_mode', return_value=False)
    @patch('vaitp_auditor.cli.run_cli_mode')
    @patch('sys.argv', ['vaitp-auditor', '--cli'])
    def test_cli_main_runs_cli_mode(self, mock_run_cli, mock_should_use_gui):
        """Test CLI main function runs CLI mode when appropriate."""
        from vaitp_auditor.cli import main
        
        # Run main function
        main()
        
        # Verify CLI mode detection and run
        mock_should_use_gui.assert_called_once()
        mock_run_cli.assert_called_once()


if __name__ == '__main__':
    unittest.main()