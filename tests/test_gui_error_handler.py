"""
Unit tests for GUI Error Handler functionality.

Tests the GUIErrorHandler class and related error dialog functionality
to ensure proper error handling and user feedback in the GUI.
Includes comprehensive tests for error recovery strategies and memory handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import customtkinter as ctk
import tempfile
import json
from pathlib import Path
from vaitp_auditor.gui.error_handler import (
    GUIErrorHandler,
    ErrorDialogBuilder,
    ProgressErrorHandler,
    show_file_error,
    show_database_error,
    show_validation_error,
    show_performance_warning,
    show_network_error,
    show_permission_error
)


class TestGUIErrorHandler(unittest.TestCase):
    """Test cases for GUIErrorHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_parent = Mock(spec=ctk.CTk)
        self.test_title = "Test Error"
        self.test_message = "This is a test error message"
        self.test_details = "Additional error details"
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.showerror')
    def test_show_error_dialog_with_parent(self, mock_showerror):
        """Test show_error_dialog with parent window."""
        # Test basic error dialog
        GUIErrorHandler.show_error_dialog(
            self.mock_parent, 
            self.test_title, 
            self.test_message
        )
        
        # Verify parent window was disabled and re-enabled
        self.mock_parent.attributes.assert_any_call('-disabled', True)
        self.mock_parent.attributes.assert_any_call('-disabled', False)
        self.mock_parent.focus_force.assert_called_once()
        
        # Verify messagebox was called correctly
        mock_showerror.assert_called_once_with(
            self.test_title, 
            self.test_message, 
            parent=self.mock_parent
        )
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.showerror')
    def test_show_error_dialog_without_parent(self, mock_showerror):
        """Test show_error_dialog without parent window."""
        GUIErrorHandler.show_error_dialog(
            None, 
            self.test_title, 
            self.test_message
        )
        
        # Verify messagebox was called without parent
        mock_showerror.assert_called_once_with(self.test_title, self.test_message)
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.showerror')
    def test_show_error_dialog_with_details(self, mock_showerror):
        """Test show_error_dialog with details section."""
        GUIErrorHandler.show_error_dialog(
            self.mock_parent,
            self.test_title,
            self.test_message,
            self.test_details
        )
        
        expected_message = f"{self.test_message}\n\nDetails:\n{self.test_details}"
        mock_showerror.assert_called_once_with(
            self.test_title,
            expected_message,
            parent=self.mock_parent
        )
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askyesno')
    def test_show_confirmation_dialog_with_parent_yes(self, mock_askyesno):
        """Test show_confirmation_dialog with parent window returning True."""
        mock_askyesno.return_value = True
        
        result = GUIErrorHandler.show_confirmation_dialog(
            self.mock_parent,
            "Confirm Action",
            "Are you sure?"
        )
        
        self.assertTrue(result)
        self.mock_parent.attributes.assert_any_call('-disabled', True)
        self.mock_parent.attributes.assert_any_call('-disabled', False)
        self.mock_parent.focus_force.assert_called_once()
        mock_askyesno.assert_called_once_with(
            "Confirm Action",
            "Are you sure?",
            parent=self.mock_parent
        )
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askyesno')
    def test_show_confirmation_dialog_with_parent_no(self, mock_askyesno):
        """Test show_confirmation_dialog with parent window returning False."""
        mock_askyesno.return_value = False
        
        result = GUIErrorHandler.show_confirmation_dialog(
            self.mock_parent,
            "Confirm Action",
            "Are you sure?"
        )
        
        self.assertFalse(result)
        mock_askyesno.assert_called_once()
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askyesno')
    def test_show_confirmation_dialog_without_parent(self, mock_askyesno):
        """Test show_confirmation_dialog without parent window."""
        mock_askyesno.return_value = True
        
        result = GUIErrorHandler.show_confirmation_dialog(
            None,
            "Confirm Action", 
            "Are you sure?"
        )
        
        self.assertTrue(result)
        mock_askyesno.assert_called_once_with("Confirm Action", "Are you sure?")
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.showinfo')
    def test_show_info_dialog(self, mock_showinfo):
        """Test show_info_dialog functionality."""
        GUIErrorHandler.show_info_dialog(
            self.mock_parent,
            "Information",
            "This is an info message"
        )
        
        self.mock_parent.attributes.assert_any_call('-disabled', True)
        self.mock_parent.attributes.assert_any_call('-disabled', False)
        mock_showinfo.assert_called_once_with(
            "Information",
            "This is an info message",
            parent=self.mock_parent
        )
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.showwarning')
    def test_show_warning_dialog(self, mock_showwarning):
        """Test show_warning_dialog functionality."""
        GUIErrorHandler.show_warning_dialog(
            self.mock_parent,
            "Warning",
            "This is a warning message"
        )
        
        self.mock_parent.attributes.assert_any_call('-disabled', True)
        self.mock_parent.attributes.assert_any_call('-disabled', False)
        mock_showwarning.assert_called_once_with(
            "Warning",
            "This is a warning message",
            parent=self.mock_parent
        )
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.showerror')
    def test_error_dialog_exception_handling(self, mock_showerror):
        """Test that parent window is re-enabled even if dialog raises exception."""
        mock_showerror.side_effect = Exception("Dialog failed")
        
        with self.assertRaises(Exception):
            GUIErrorHandler.show_error_dialog(
                self.mock_parent,
                self.test_title,
                self.test_message
            )
        
        # Verify parent was still re-enabled despite exception
        self.mock_parent.attributes.assert_any_call('-disabled', False)


class TestErrorDialogBuilder(unittest.TestCase):
    """Test cases for ErrorDialogBuilder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.builder = ErrorDialogBuilder()
    
    def test_builder_initialization(self):
        """Test ErrorDialogBuilder initialization."""
        self.assertEqual(self.builder.title, "Error")
        self.assertEqual(self.builder.message, "")
        self.assertIsNone(self.builder.details)
        self.assertEqual(self.builder.suggestions, [])
    
    def test_builder_fluent_interface(self):
        """Test ErrorDialogBuilder fluent interface."""
        result = (self.builder
                 .set_title("Custom Title")
                 .set_message("Custom Message")
                 .add_details("Custom Details")
                 .add_suggestion("Suggestion 1")
                 .add_suggestion("Suggestion 2"))
        
        # Verify fluent interface returns self
        self.assertIs(result, self.builder)
        
        # Verify values were set
        self.assertEqual(self.builder.title, "Custom Title")
        self.assertEqual(self.builder.message, "Custom Message")
        self.assertEqual(self.builder.details, "Custom Details")
        self.assertEqual(self.builder.suggestions, ["Suggestion 1", "Suggestion 2"])
    
    def test_build_details_with_details_only(self):
        """Test build_details with only details."""
        self.builder.add_details("Error details")
        
        result = self.builder.build_details()
        self.assertEqual(result, "Error details")
    
    def test_build_details_with_suggestions_only(self):
        """Test build_details with only suggestions."""
        self.builder.add_suggestion("Try this").add_suggestion("Try that")
        
        result = self.builder.build_details()
        expected = "Troubleshooting suggestions:\n1. Try this\n2. Try that"
        self.assertEqual(result, expected)
    
    def test_build_details_with_both(self):
        """Test build_details with both details and suggestions."""
        self.builder.add_details("Error occurred").add_suggestion("Fix it")
        
        result = self.builder.build_details()
        expected = "Error occurred\nTroubleshooting suggestions:\n1. Fix it"
        self.assertEqual(result, expected)
    
    def test_build_details_empty(self):
        """Test build_details with no content."""
        result = self.builder.build_details()
        self.assertIsNone(result)
    
    @patch('vaitp_auditor.gui.error_handler.GUIErrorHandler.show_error_dialog')
    def test_builder_show(self, mock_show_error):
        """Test ErrorDialogBuilder show method."""
        mock_parent = Mock()
        
        self.builder.set_title("Test Title").set_message("Test Message")
        self.builder.show(mock_parent)
        
        mock_show_error.assert_called_once_with(
            mock_parent,
            "Test Title",
            "Test Message",
            None
        )


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience error functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_parent = Mock(spec=ctk.CTk)
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askretrycancel')
    def test_show_file_error(self, mock_retry):
        """Test show_file_error convenience function."""
        mock_retry.return_value = True
        
        test_error = FileNotFoundError("File not found")
        
        with patch('vaitp_auditor.gui.error_handler.filedialog.askopenfilename') as mock_filedialog:
            mock_filedialog.return_value = "/new/path/file.txt"
            
            result = show_file_error(self.mock_parent, "read", "/path/to/file.txt", test_error)
            
            self.assertTrue(result)
            mock_retry.assert_called_once()
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askretrycancel')
    def test_show_database_error(self, mock_retry):
        """Test show_database_error convenience function."""
        mock_retry.return_value = False
        
        test_error = Exception("Connection failed")
        
        result = show_database_error(self.mock_parent, "/path/to/db.sqlite", test_error)
        
        self.assertFalse(result)
        mock_retry.assert_called_once()
    
    @patch('vaitp_auditor.gui.error_handler.ErrorDialogBuilder')
    def test_show_validation_error(self, mock_builder_class):
        """Test show_validation_error convenience function."""
        mock_builder = Mock()
        mock_builder_class.return_value = mock_builder
        mock_builder.set_title.return_value = mock_builder
        mock_builder.set_message.return_value = mock_builder
        mock_builder.add_suggestion.return_value = mock_builder
        
        show_validation_error(self.mock_parent, "experiment name", "cannot be empty")
        
        # Verify builder was configured correctly
        mock_builder.set_title.assert_called_once_with("Validation Error")
        mock_builder.set_message.assert_called_once_with("Invalid experiment name: cannot be empty")
        mock_builder.add_suggestion.assert_called_once_with("Please correct the highlighted field and try again")
        mock_builder.show.assert_called_once_with(self.mock_parent)


class TestErrorHandlerIntegration(unittest.TestCase):
    """Integration tests for error handler functionality."""
    
    @patch('vaitp_auditor.gui.error_handler.messagebox')
    def test_modal_dialog_behavior(self, mock_messagebox):
        """Test that dialogs properly handle modal behavior."""
        mock_parent = Mock(spec=ctk.CTk)
        
        # Test error dialog modal behavior
        GUIErrorHandler.show_error_dialog(mock_parent, "Error", "Message")
        
        # Verify modal behavior sequence
        calls = mock_parent.attributes.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0], ('-disabled', True))
        self.assertEqual(calls[1][0], ('-disabled', False))
        
        # Verify focus is restored
        mock_parent.focus_force.assert_called_once()
    
    def test_error_handler_import(self):
        """Test that error handler can be imported from GUI package."""
        from vaitp_auditor.gui import GUIErrorHandler, ErrorDialogBuilder
        
        # Verify classes are available
        self.assertTrue(callable(GUIErrorHandler.show_error_dialog))
        self.assertTrue(callable(GUIErrorHandler.show_confirmation_dialog))
        self.assertTrue(callable(ErrorDialogBuilder))


class TestComprehensiveErrorHandling(unittest.TestCase):
    """Test cases for comprehensive error handling features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_parent = Mock(spec=ctk.CTk)
        GUIErrorHandler._session_state_backup = None
        GUIErrorHandler._recovery_strategies.clear()
    
    @patch('vaitp_auditor.gui.error_handler.filedialog.askopenfilename')
    @patch('vaitp_auditor.gui.error_handler.messagebox.askretrycancel')
    def test_handle_file_dialog_error_retry_success(self, mock_retry, mock_filedialog):
        """Test file dialog error handling with successful retry."""
        mock_retry.return_value = True
        mock_filedialog.return_value = "/path/to/selected/file.txt"
        
        result = GUIErrorHandler.handle_file_dialog_error(
            self.mock_parent,
            "select file",
            FileNotFoundError("Dialog failed")
        )
        
        self.assertEqual(result, "/path/to/selected/file.txt")
        mock_retry.assert_called_once()
        mock_filedialog.assert_called_once()
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askretrycancel')
    def test_handle_file_dialog_error_user_cancels(self, mock_retry):
        """Test file dialog error handling when user cancels."""
        mock_retry.return_value = False
        
        result = GUIErrorHandler.handle_file_dialog_error(
            self.mock_parent,
            "select file",
            FileNotFoundError("Dialog failed")
        )
        
        self.assertIsNone(result)
        mock_retry.assert_called_once()
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askretrycancel')
    def test_handle_database_connection_error_permission(self, mock_retry):
        """Test database connection error with permission issues."""
        mock_retry.return_value = True
        
        permission_error = PermissionError("Access denied")
        result = GUIErrorHandler.handle_database_connection_error(
            self.mock_parent,
            "/path/to/database.db",
            permission_error
        )
        
        self.assertTrue(result)
        mock_retry.assert_called_once()
        
        # Check that permission-specific suggestions were included
        call_args = mock_retry.call_args[0]
        self.assertIn("permission", call_args[1].lower())
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askretrycancel')
    def test_handle_database_connection_error_corruption(self, mock_retry):
        """Test database connection error with corruption issues."""
        mock_retry.return_value = False
        
        corruption_error = Exception("database disk image is malformed")
        result = GUIErrorHandler.handle_database_connection_error(
            self.mock_parent,
            "/path/to/database.db",
            corruption_error
        )
        
        self.assertFalse(result)
        
        # Check that corruption-specific suggestions were included
        call_args = mock_retry.call_args[0]
        self.assertIn("corrupt", call_args[1].lower())
    
    @patch('vaitp_auditor.gui.error_handler.psutil.Process')
    def test_get_memory_usage(self, mock_process_class):
        """Test memory usage monitoring."""
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 500 * 1024 * 1024  # 500 MB
        mock_process_class.return_value = mock_process
        
        usage = GUIErrorHandler.get_memory_usage()
        self.assertEqual(usage, 500.0)
    
    @patch('vaitp_auditor.gui.error_handler.GUIErrorHandler.get_memory_usage')
    @patch('vaitp_auditor.gui.error_handler.messagebox.askyesno')
    def test_handle_memory_constraint_critical(self, mock_confirm, mock_memory):
        """Test critical memory constraint handling."""
        mock_memory.return_value = 900.0  # Critical level
        mock_confirm.return_value = True
        
        result = GUIErrorHandler.handle_memory_constraint(
            self.mock_parent,
            900.0,
            "loading large file"
        )
        
        self.assertTrue(result)
        mock_confirm.assert_called_once()
        
        # Check that critical warning was shown
        call_args = mock_confirm.call_args[0]
        self.assertIn("Critical", call_args[0])
    
    @patch('vaitp_auditor.gui.error_handler.GUIErrorHandler.get_memory_usage')
    @patch('vaitp_auditor.gui.error_handler.messagebox.showwarning')
    def test_check_memory_constraints_warning_level(self, mock_warning, mock_memory):
        """Test memory constraint checking at warning level."""
        mock_memory.return_value = 600.0  # Warning level
        
        result = GUIErrorHandler.check_memory_constraints(
            self.mock_parent,
            "processing data"
        )
        
        self.assertTrue(result)
        mock_warning.assert_called_once()
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askretrycancel')
    def test_handle_parsing_error_excel(self, mock_retry):
        """Test parsing error handling for Excel files."""
        mock_retry.return_value = True
        
        parsing_error = Exception("Invalid Excel format")
        result = GUIErrorHandler.handle_parsing_error(
            self.mock_parent,
            "/path/to/file.xlsx",
            parsing_error
        )
        
        self.assertTrue(result)
        
        # Check that Excel-specific suggestions were included
        call_args = mock_retry.call_args[0]
        self.assertIn("Excel", call_args[1])
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askretrycancel')
    def test_handle_parsing_error_csv(self, mock_retry):
        """Test parsing error handling for CSV files."""
        mock_retry.return_value = False
        
        parsing_error = Exception("Invalid CSV format")
        result = GUIErrorHandler.handle_parsing_error(
            self.mock_parent,
            "/path/to/file.csv",
            parsing_error
        )
        
        self.assertFalse(result)
        
        # Check that CSV-specific suggestions were included
        call_args = mock_retry.call_args[0]
        self.assertIn("CSV", call_args[1])
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askyesno')
    def test_handle_session_crash_with_backup(self, mock_confirm):
        """Test session crash handling with available backup."""
        mock_confirm.return_value = True
        
        crash_info = {
            'session_backup_available': True,
            'error_details': 'Unexpected exception occurred'
        }
        
        result = GUIErrorHandler.handle_session_crash(self.mock_parent, crash_info)
        
        self.assertTrue(result)
        mock_confirm.assert_called_once()
        
        # Check that recovery option was presented
        call_args = mock_confirm.call_args[0]
        self.assertIn("recover", call_args[1].lower())
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.showerror')
    def test_handle_session_crash_no_backup(self, mock_error):
        """Test session crash handling without backup."""
        crash_info = {
            'session_backup_available': False,
            'error_details': 'Critical system error'
        }
        
        result = GUIErrorHandler.handle_session_crash(self.mock_parent, crash_info)
        
        self.assertFalse(result)
        mock_error.assert_called_once()
    
    def test_backup_and_restore_session_state(self):
        """Test session state backup and restore functionality."""
        test_session = {
            'experiment_name': 'test_session',
            'current_index': 5,
            'total_items': 100
        }
        
        # Test backup
        GUIErrorHandler.backup_session_state(test_session)
        self.assertEqual(GUIErrorHandler._session_state_backup, test_session)
        
        # Test restore
        restored = GUIErrorHandler.restore_session_state()
        self.assertEqual(restored, test_session)
        
        # Test clear
        GUIErrorHandler.clear_session_backup()
        self.assertIsNone(GUIErrorHandler._session_state_backup)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('vaitp_auditor.gui.error_handler.Path.home')
    def test_backup_session_state_to_file(self, mock_home, mock_file):
        """Test session state backup to file."""
        mock_home.return_value = Path('/home/user')
        
        test_session = {'test': 'data'}
        GUIErrorHandler.backup_session_state(test_session)
        
        # Verify file was written
        mock_file.assert_called_once()
        handle = mock_file()
        handle.write.assert_called()
    
    def test_recovery_strategy_registration(self):
        """Test recovery strategy registration and execution."""
        # Register a mock recovery strategy
        mock_strategy = Mock(return_value=True)
        GUIErrorHandler.register_recovery_strategy('test_error', mock_strategy)
        
        # Execute recovery strategies
        result = GUIErrorHandler.execute_recovery_strategies('test_error', 'arg1', kwarg1='value1')
        
        self.assertTrue(result)
        mock_strategy.assert_called_once_with('arg1', kwarg1='value1')
    
    def test_recovery_strategy_failure_handling(self):
        """Test recovery strategy failure handling."""
        # Register a failing strategy
        failing_strategy = Mock(side_effect=Exception("Strategy failed"))
        GUIErrorHandler.register_recovery_strategy('test_error', failing_strategy)
        
        # Execute should not raise exception
        result = GUIErrorHandler.execute_recovery_strategies('test_error')
        
        self.assertFalse(result)
        failing_strategy.assert_called_once()


class TestProgressErrorHandler(unittest.TestCase):
    """Test cases for ProgressErrorHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_parent = Mock(spec=ctk.CTk)
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askretrycancel')
    def test_handle_operation_timeout(self, mock_retry):
        """Test operation timeout handling."""
        mock_retry.return_value = True
        
        result = ProgressErrorHandler.handle_operation_timeout(
            self.mock_parent,
            "processing large dataset",
            30
        )
        
        self.assertTrue(result)
        mock_retry.assert_called_once()
        
        # Check timeout information was included
        call_args = mock_retry.call_args[0]
        self.assertIn("30", call_args[1])
    
    @patch('vaitp_auditor.gui.error_handler.GUIErrorHandler.show_info_dialog')
    def test_handle_cancellation_error(self, mock_info):
        """Test operation cancellation handling."""
        ProgressErrorHandler.handle_cancellation_error(
            self.mock_parent,
            "file processing"
        )
        
        mock_info.assert_called_once()
        call_args = mock_info.call_args[0]
        self.assertIn("cancelled", call_args[2].lower())
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askretrycancel')
    def test_handle_progress_error(self, mock_retry):
        """Test progress operation error handling."""
        mock_retry.return_value = False
        
        test_error = Exception("Processing failed")
        result = ProgressErrorHandler.handle_progress_error(
            self.mock_parent,
            "data analysis",
            0.75,
            test_error
        )
        
        self.assertFalse(result)
        mock_retry.assert_called_once()
        
        # Check progress information was included
        call_args = mock_retry.call_args[0]
        self.assertIn("75.0", call_args[1])


class TestEnhancedConvenienceFunctions(unittest.TestCase):
    """Test cases for enhanced convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_parent = Mock(spec=ctk.CTk)
    
    @patch('vaitp_auditor.gui.error_handler.GUIErrorHandler.handle_file_dialog_error')
    def test_show_file_error_returns_boolean(self, mock_handle):
        """Test that show_file_error returns boolean based on recovery result."""
        mock_handle.return_value = "/path/to/file"
        
        result = show_file_error(
            self.mock_parent,
            "read",
            "/path/to/file.txt",
            FileNotFoundError("File not found")
        )
        
        self.assertTrue(result)
        mock_handle.assert_called_once()
    
    @patch('vaitp_auditor.gui.error_handler.GUIErrorHandler.handle_database_connection_error')
    def test_show_database_error_returns_boolean(self, mock_handle):
        """Test that show_database_error returns boolean based on recovery result."""
        mock_handle.return_value = False
        
        result = show_database_error(
            self.mock_parent,
            "/path/to/db.sqlite",
            Exception("Connection failed")
        )
        
        self.assertFalse(result)
        mock_handle.assert_called_once()
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askyesno')
    def test_show_performance_warning(self, mock_confirm):
        """Test performance warning for large files."""
        mock_confirm.return_value = True
        
        result = show_performance_warning(
            self.mock_parent,
            "syntax highlighting",
            150.5
        )
        
        self.assertTrue(result)
        mock_confirm.assert_called_once()
        
        # Check file size was included
        call_args = mock_confirm.call_args[0]
        self.assertIn("150.5 MB", call_args[1])
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askretrycancel')
    def test_show_network_error(self, mock_retry):
        """Test network error handling."""
        mock_retry.return_value = True
        
        network_error = ConnectionError("Network unreachable")
        result = show_network_error(
            self.mock_parent,
            "download update",
            network_error
        )
        
        self.assertTrue(result)
        mock_retry.assert_called_once()
        
        # Check network-specific suggestions
        call_args = mock_retry.call_args
        # call_args is (args, kwargs), we want the details which should be in args[2]
        if len(call_args[0]) > 2:
            self.assertIn("internet connection", call_args[0][2].lower())
        else:
            # Details might be in kwargs or combined with message
            full_message = call_args[0][1] if len(call_args[0]) > 1 else ""
            self.assertIn("internet", full_message.lower())
    
    @patch('vaitp_auditor.gui.error_handler.messagebox.askretrycancel')
    def test_show_permission_error(self, mock_retry):
        """Test permission error handling."""
        mock_retry.return_value = False
        
        permission_error = PermissionError("Access denied")
        result = show_permission_error(
            self.mock_parent,
            "configuration file",
            permission_error
        )
        
        self.assertFalse(result)
        mock_retry.assert_called_once()
        
        # Check permission-specific suggestions
        call_args = mock_retry.call_args
        # call_args is (args, kwargs), we want the details which should be in args[2]
        if len(call_args[0]) > 2:
            self.assertIn("administrator", call_args[0][2].lower())
        else:
            # Details might be in kwargs or combined with message
            full_message = call_args[0][1] if len(call_args[0]) > 1 else ""
            self.assertIn("administrator", full_message.lower())


class TestErrorHandlerMemoryManagement(unittest.TestCase):
    """Test cases for memory management features."""
    
    @patch('vaitp_auditor.gui.error_handler.psutil.Process')
    def test_memory_usage_calculation_error(self, mock_process_class):
        """Test memory usage calculation when psutil fails."""
        mock_process_class.side_effect = Exception("Process access denied")
        
        usage = GUIErrorHandler.get_memory_usage()
        self.assertEqual(usage, 0.0)
    
    @patch('vaitp_auditor.gui.error_handler.GUIErrorHandler.get_memory_usage')
    def test_check_memory_constraints_normal_usage(self, mock_memory):
        """Test memory constraint checking with normal usage."""
        mock_memory.return_value = 200.0  # Normal level
        
        result = GUIErrorHandler.check_memory_constraints(
            Mock(),
            "normal operation"
        )
        
        self.assertTrue(result)
    
    @patch('vaitp_auditor.gui.error_handler.GUIErrorHandler.get_memory_usage')
    @patch('vaitp_auditor.gui.error_handler.GUIErrorHandler.handle_memory_constraint')
    def test_check_memory_constraints_critical_usage(self, mock_handle, mock_memory):
        """Test memory constraint checking with critical usage."""
        mock_memory.return_value = 900.0  # Critical level
        mock_handle.return_value = False
        
        result = GUIErrorHandler.check_memory_constraints(
            Mock(),
            "memory intensive operation"
        )
        
        self.assertFalse(result)
        # Check that handle_memory_constraint was called with correct arguments
        self.assertEqual(mock_handle.call_count, 1)
        call_args = mock_handle.call_args[0]
        self.assertEqual(call_args[1], 900.0)  # memory usage
        self.assertEqual(call_args[2], "memory intensive operation")  # operation


if __name__ == '__main__':
    unittest.main()