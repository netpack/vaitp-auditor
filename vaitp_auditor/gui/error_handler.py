"""
GUI Error Handler Module

Provides centralized error handling and dialog management for GUI components.
Implements standardized modal dialogs for error messages and confirmations.
Includes comprehensive error recovery strategies and memory constraint handling.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional, Callable, Dict, Any, List, Tuple
import customtkinter as ctk
import threading
import time
import psutil
import os
import logging
from pathlib import Path


class GUIErrorHandler:
    """
    Centralized error handling for GUI components.
    
    Provides standardized modal dialog boxes for error messages and confirmations
    as required by acceptance criteria 8.1 and 8.9. Includes comprehensive error
    recovery strategies, memory constraint handling, and crash recovery.
    """
    
    # Memory thresholds (in MB)
    MEMORY_WARNING_THRESHOLD = 500
    MEMORY_CRITICAL_THRESHOLD = 800
    
    # Error recovery strategies
    _recovery_strategies: Dict[str, List[Callable]] = {}
    _session_state_backup: Optional[Dict[str, Any]] = None
    
    @staticmethod
    def show_error_dialog(
        parent: Optional[ctk.CTk], 
        title: str, 
        message: str, 
        details: Optional[str] = None
    ) -> None:
        """
        Display a standardized error dialog with optional details section.
        
        Args:
            parent: Parent window for modal dialog (can be None)
            title: Dialog title text
            message: Main error message
            details: Optional detailed error information
        """
        # Create the main error message
        full_message = message
        
        # Add details section if provided
        if details:
            full_message += f"\n\nDetails:\n{details}"
        
        # Use tkinter messagebox for consistent cross-platform behavior
        # This ensures the dialog is modal and properly styled
        if parent:
            # Show error dialog with parent (CustomTkinter doesn't support -disabled attribute)
            try:
                messagebox.showerror(title, full_message, parent=parent)
                parent.focus_force()
            except Exception:
                # Fallback if parent doesn't support messagebox
                messagebox.showerror(title, full_message)
        else:
            messagebox.showerror(title, full_message)
    
    @staticmethod
    def show_confirmation_dialog(
        parent: Optional[ctk.CTk], 
        title: str, 
        message: str
    ) -> bool:
        """
        Display a confirmation dialog and return user's choice.
        
        Args:
            parent: Parent window for modal dialog (can be None)
            title: Dialog title text
            message: Confirmation message
            
        Returns:
            True if user confirmed (clicked Yes/OK), False otherwise
        """
        if parent:
            # Show confirmation dialog with parent (CustomTkinter doesn't support -disabled attribute)
            try:
                result = messagebox.askyesno(title, message, parent=parent)
                parent.focus_force()
                return result
            except Exception:
                # Fallback if parent doesn't support messagebox
                return messagebox.askyesno(title, message)
        else:
            return messagebox.askyesno(title, message)
    
    @staticmethod
    def show_info_dialog(
        parent: Optional[ctk.CTk], 
        title: str, 
        message: str,
        auto_close_ms: Optional[int] = None
    ) -> None:
        """
        Display an informational dialog.
        
        Args:
            parent: Parent window for modal dialog (can be None)
            title: Dialog title text
            message: Information message
            auto_close_ms: Optional auto-close timeout in milliseconds
        """
        if auto_close_ms and parent:
            # Create a custom auto-closing dialog
            GUIErrorHandler._show_auto_close_dialog(parent, title, message, auto_close_ms)
        elif parent:
            # Show dialog with parent (CustomTkinter doesn't support -disabled attribute)
            try:
                messagebox.showinfo(title, message, parent=parent)
                parent.focus_force()
            except Exception:
                # Fallback if parent doesn't support messagebox
                messagebox.showinfo(title, message)
        else:
            messagebox.showinfo(title, message)
    
    @staticmethod
    def _show_auto_close_dialog(
        parent: ctk.CTk,
        title: str,
        message: str,
        auto_close_ms: int
    ) -> None:
        """
        Show an auto-closing dialog window.
        
        Args:
            parent: Parent window
            title: Dialog title
            message: Dialog message
            auto_close_ms: Auto-close timeout in milliseconds
        """
        # Create a simple auto-closing dialog
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        
        # Center the dialog on parent
        dialog.transient(parent)
        dialog.grab_set()
        
        # Add message label
        label = ctk.CTkLabel(
            dialog,
            text=message,
            wraplength=350,
            justify="center"
        )
        label.pack(pady=20, padx=20, expand=True)
        
        # Add countdown label
        countdown_label = ctk.CTkLabel(
            dialog,
            text=f"Auto-closing in {auto_close_ms // 1000} seconds...",
            font=ctk.CTkFont(size=10)
        )
        countdown_label.pack(pady=(0, 10))
        
        # Add OK button
        ok_button = ctk.CTkButton(
            dialog,
            text="OK",
            command=dialog.destroy,
            width=80
        )
        ok_button.pack(pady=(0, 20))
        
        # Auto-close functionality
        remaining_ms = auto_close_ms
        
        def update_countdown():
            nonlocal remaining_ms
            if remaining_ms <= 0:
                dialog.destroy()
                return
            
            remaining_seconds = remaining_ms // 1000
            countdown_label.configure(text=f"Auto-closing in {remaining_seconds} seconds...")
            remaining_ms -= 100
            dialog.after(100, update_countdown)
        
        # Start countdown
        dialog.after(100, update_countdown)
        
        # Auto-close after specified time
        dialog.after(auto_close_ms, dialog.destroy)
    
    @staticmethod
    def show_warning_dialog(
        parent: Optional[ctk.CTk], 
        title: str, 
        message: str
    ) -> None:
        """
        Display a warning dialog.
        
        Args:
            parent: Parent window for modal dialog (can be None)
            title: Dialog title text
            message: Warning message
        """
        if parent:
            # Show warning dialog with parent (CustomTkinter doesn't support -disabled attribute)
            try:
                messagebox.showwarning(title, message, parent=parent)
                parent.focus_force()
            except Exception:
                # Fallback if parent doesn't support messagebox
                messagebox.showwarning(title, message)
        else:
            messagebox.showwarning(title, message)
    
    @classmethod
    def handle_file_dialog_error(cls, parent: Optional[ctk.CTk], operation: str, error: Exception) -> Optional[str]:
        """
        Handle file dialog failures with retry options.
        
        Args:
            parent: Parent window
            operation: Description of the operation (e.g., "select file", "save file")
            error: The exception that occurred
            
        Returns:
            Selected file path if retry succeeds, None if user cancels
        """
        builder = ErrorDialogBuilder()
        builder.set_title("File Dialog Error")
        builder.set_message(f"Failed to {operation}")
        builder.add_details(str(error))
        builder.add_suggestion("Try again with a different location")
        builder.add_suggestion("Check file permissions and disk space")
        builder.add_suggestion("Restart the application if the problem persists")
        
        # Show error with retry option
        retry = cls.show_retry_dialog(
            parent,
            "File Dialog Error",
            f"Failed to {operation}. Would you like to try again?",
            builder.build_details()
        )
        
        if retry:
            try:
                # Attempt to open file dialog again
                if "save" in operation.lower():
                    return filedialog.asksaveasfilename(parent=parent)
                elif "folder" in operation.lower() or "directory" in operation.lower():
                    return filedialog.askdirectory(parent=parent)
                else:
                    return filedialog.askopenfilename(parent=parent)
            except Exception as retry_error:
                cls.show_error_dialog(
                    parent,
                    "File Dialog Error",
                    "File dialog failed again. Please try manually entering the path.",
                    str(retry_error)
                )
        
        return None
    
    @classmethod
    def handle_database_connection_error(cls, parent: Optional[ctk.CTk], database_path: str, error: Exception) -> bool:
        """
        Handle database connection issues with recovery strategies.
        
        Args:
            parent: Parent window
            database_path: Path to the database file
            error: The connection error
            
        Returns:
            True if user wants to retry, False to cancel
        """
        builder = ErrorDialogBuilder()
        builder.set_title("Database Connection Error")
        builder.set_message(f"Failed to connect to database: {os.path.basename(database_path)}")
        builder.add_details(str(error))
        
        # Add specific troubleshooting based on error type
        error_str = str(error).lower()
        if "permission" in error_str or "access" in error_str:
            builder.add_suggestion("Check file permissions - you may need read/write access")
            builder.add_suggestion("Close any other applications that might be using the database")
        elif "corrupt" in error_str or "malformed" in error_str:
            builder.add_suggestion("The database file may be corrupted - try a backup copy")
            builder.add_suggestion("Use a database repair tool if available")
        elif "not found" in error_str:
            builder.add_suggestion("Verify the file path is correct")
            builder.add_suggestion("Check if the file was moved or deleted")
        else:
            builder.add_suggestion("Verify the file is a valid SQLite database")
            builder.add_suggestion("Try selecting a different database file")
        
        builder.add_suggestion("Consider using a different data source type (Folders or Excel)")
        
        return cls.show_retry_dialog(
            parent,
            "Database Connection Failed",
            "Would you like to try selecting a different database file?",
            builder.build_details()
        )
    
    @classmethod
    def handle_memory_constraint(cls, parent: Optional[ctk.CTk], current_usage_mb: float, operation: str) -> bool:
        """
        Handle memory constraint issues gracefully.
        
        Args:
            parent: Parent window
            current_usage_mb: Current memory usage in MB
            operation: Description of the operation causing memory issues
            
        Returns:
            True if user wants to continue, False to cancel
        """
        if current_usage_mb > cls.MEMORY_CRITICAL_THRESHOLD:
            title = "Critical Memory Usage"
            message = f"Memory usage is critically high ({current_usage_mb:.1f} MB). The application may become unstable."
            suggestions = [
                "Close other applications to free up memory",
                "Restart the application to clear memory",
                "Consider processing smaller files or datasets",
                "Save your current progress before continuing"
            ]
        else:
            title = "High Memory Usage"
            message = f"Memory usage is high ({current_usage_mb:.1f} MB) during {operation}."
            suggestions = [
                "Close unnecessary applications",
                "Consider processing in smaller batches",
                "Monitor system performance"
            ]
        
        builder = ErrorDialogBuilder()
        builder.set_title(title)
        builder.set_message(message)
        for suggestion in suggestions:
            builder.add_suggestion(suggestion)
        
        return cls.show_confirmation_dialog(
            parent,
            title,
            f"{message}\n\nDo you want to continue anyway?\n\n{builder.build_details()}"
        )
    
    @classmethod
    def handle_parsing_error(cls, parent: Optional[ctk.CTk], file_path: str, error: Exception) -> bool:
        """
        Handle file parsing errors with recovery options.
        
        Args:
            parent: Parent window
            file_path: Path to the file that failed to parse
            error: The parsing error
            
        Returns:
            True if user wants to try a different file, False to cancel
        """
        builder = ErrorDialogBuilder()
        builder.set_title("File Parsing Error")
        builder.set_message(f"Failed to parse file: {os.path.basename(file_path)}")
        builder.add_details(str(error))
        
        # Add specific suggestions based on file type
        file_ext = Path(file_path).suffix.lower()
        if file_ext in ['.xlsx', '.xls']:
            builder.add_suggestion("Verify the Excel file is not corrupted")
            builder.add_suggestion("Check if the file is password protected")
            builder.add_suggestion("Try opening the file in Excel to verify it's valid")
            builder.add_suggestion("Consider converting to CSV format")
        elif file_ext == '.csv':
            builder.add_suggestion("Check the CSV file encoding (try UTF-8)")
            builder.add_suggestion("Verify the delimiter is correct (comma, semicolon, tab)")
            builder.add_suggestion("Check for malformed rows or special characters")
        elif file_ext in ['.db', '.sqlite', '.sqlite3']:
            builder.add_suggestion("Verify the database file is not corrupted")
            builder.add_suggestion("Check if another application is using the database")
            builder.add_suggestion("Try using a database viewer to verify the structure")
        else:
            builder.add_suggestion("Verify the file format is supported")
            builder.add_suggestion("Check if the file is corrupted or incomplete")
        
        builder.add_suggestion("Try selecting a different file")
        
        return cls.show_retry_dialog(
            parent,
            "File Parsing Failed",
            "Would you like to try selecting a different file?",
            builder.build_details()
        )
    
    @classmethod
    def handle_session_crash(cls, parent: Optional[ctk.CTk], crash_info: Dict[str, Any]) -> bool:
        """
        Handle application crashes with recovery options.
        
        Args:
            parent: Parent window (may be None if app crashed)
            crash_info: Information about the crash
            
        Returns:
            True if session recovery should be attempted, False otherwise
        """
        builder = ErrorDialogBuilder()
        builder.set_title("Application Crash Detected")
        builder.set_message("The application encountered an unexpected error and needs to restart.")
        
        if crash_info.get('session_backup_available'):
            builder.add_details("A session backup was found and can be restored.")
            builder.add_suggestion("Click 'Yes' to attempt session recovery")
            builder.add_suggestion("Click 'No' to start with a fresh session")
        else:
            builder.add_details("No session backup is available.")
            builder.add_suggestion("You will need to start a new session")
        
        if crash_info.get('error_details'):
            builder.add_details(f"Error details: {crash_info['error_details']}")
        
        builder.add_suggestion("Consider saving your work more frequently")
        builder.add_suggestion("Report this issue if it happens repeatedly")
        
        if crash_info.get('session_backup_available'):
            return cls.show_confirmation_dialog(
                parent,
                "Recover Session?",
                f"A previous session backup was found. Would you like to recover it?\n\n{builder.build_details()}"
            )
        else:
            cls.show_error_dialog(
                parent,
                "Application Crash",
                "The application crashed and no session backup is available.",
                builder.build_details()
            )
            return False
    
    @classmethod
    def show_retry_dialog(cls, parent: Optional[ctk.CTk], title: str, message: str, details: Optional[str] = None) -> bool:
        """
        Show a dialog with retry/cancel options.
        
        Args:
            parent: Parent window
            title: Dialog title
            message: Main message
            details: Optional detailed information
            
        Returns:
            True if user wants to retry, False to cancel
        """
        full_message = message
        if details:
            full_message += f"\n\nDetails:\n{details}"
        
        if parent:
            # Show retry dialog with parent (CustomTkinter doesn't support -disabled attribute)
            try:
                result = messagebox.askretrycancel(title, full_message, parent=parent)
                parent.focus_force()
                return result
            except Exception:
                # Fallback if parent doesn't support messagebox
                return messagebox.askretrycancel(title, full_message)
        else:
            return messagebox.askretrycancel(title, full_message)
    
    @classmethod
    def get_memory_usage(cls) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            Current memory usage in megabytes
        """
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert bytes to MB
        except Exception:
            return 0.0
    
    @classmethod
    def check_memory_constraints(cls, parent: Optional[ctk.CTk], operation: str) -> bool:
        """
        Check memory constraints before performing an operation.
        
        Args:
            parent: Parent window
            operation: Description of the operation
            
        Returns:
            True if operation should proceed, False if cancelled due to memory
        """
        current_usage = cls.get_memory_usage()
        
        if current_usage > cls.MEMORY_CRITICAL_THRESHOLD:
            return cls.handle_memory_constraint(parent, current_usage, operation)
        elif current_usage > cls.MEMORY_WARNING_THRESHOLD:
            cls.show_warning_dialog(
                parent,
                "High Memory Usage",
                f"Memory usage is high ({current_usage:.1f} MB). Consider closing other applications."
            )
        
        return True
    
    @classmethod
    def backup_session_state(cls, session_data: Dict[str, Any]) -> None:
        """
        Backup session state for crash recovery.
        
        Args:
            session_data: Current session state to backup
        """
        cls._session_state_backup = session_data.copy()
        
        # Also save to file for persistence across app restarts
        try:
            import json
            backup_path = Path.home() / '.vaitp_auditor_session_backup.json'
            with open(backup_path, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
        except Exception as e:
            logging.warning(f"Failed to save session backup to file: {e}")
    
    @classmethod
    def restore_session_state(cls) -> Optional[Dict[str, Any]]:
        """
        Restore session state from backup.
        
        Returns:
            Restored session data if available, None otherwise
        """
        # Try in-memory backup first
        if cls._session_state_backup:
            return cls._session_state_backup.copy()
        
        # Try file backup
        try:
            import json
            backup_path = Path.home() / '.vaitp_auditor_session_backup.json'
            if backup_path.exists():
                with open(backup_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to restore session backup from file: {e}")
        
        return None
    
    @classmethod
    def clear_session_backup(cls) -> None:
        """Clear session backup after successful completion."""
        cls._session_state_backup = None
        
        try:
            backup_path = Path.home() / '.vaitp_auditor_session_backup.json'
            if backup_path.exists():
                backup_path.unlink()
        except Exception as e:
            logging.warning(f"Failed to clear session backup file: {e}")
    
    @classmethod
    def register_recovery_strategy(cls, error_type: str, recovery_function: Callable) -> None:
        """
        Register a recovery strategy for a specific error type.
        
        Args:
            error_type: Type of error (e.g., 'database_connection', 'file_parsing')
            recovery_function: Function to call for recovery
        """
        if error_type not in cls._recovery_strategies:
            cls._recovery_strategies[error_type] = []
        cls._recovery_strategies[error_type].append(recovery_function)
    
    @classmethod
    def execute_recovery_strategies(cls, error_type: str, *args, **kwargs) -> bool:
        """
        Execute registered recovery strategies for an error type.
        
        Args:
            error_type: Type of error
            *args, **kwargs: Arguments to pass to recovery functions
            
        Returns:
            True if any recovery strategy succeeded, False otherwise
        """
        strategies = cls._recovery_strategies.get(error_type, [])
        
        for strategy in strategies:
            try:
                if strategy(*args, **kwargs):
                    return True
            except Exception as e:
                logging.warning(f"Recovery strategy failed: {e}")
        
        return False


class ErrorDialogBuilder:
    """
    Builder class for creating standardized error messages.
    
    Helps create consistent error messages with proper formatting
    and troubleshooting suggestions.
    """
    
    def __init__(self):
        self.title = "Error"
        self.message = ""
        self.details = None
        self.suggestions = []
    
    def set_title(self, title: str) -> 'ErrorDialogBuilder':
        """Set the dialog title."""
        self.title = title
        return self
    
    def set_message(self, message: str) -> 'ErrorDialogBuilder':
        """Set the main error message."""
        self.message = message
        return self
    
    def add_details(self, details: str) -> 'ErrorDialogBuilder':
        """Add detailed error information."""
        self.details = details
        return self
    
    def add_suggestion(self, suggestion: str) -> 'ErrorDialogBuilder':
        """Add a troubleshooting suggestion."""
        self.suggestions.append(suggestion)
        return self
    
    def build_details(self) -> Optional[str]:
        """Build the complete details string."""
        parts = []
        
        if self.details:
            parts.append(self.details)
        
        if self.suggestions:
            parts.append("Troubleshooting suggestions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                parts.append(f"{i}. {suggestion}")
        
        return "\n".join(parts) if parts else None
    
    def show(self, parent: Optional[ctk.CTk] = None) -> None:
        """Show the error dialog with built content."""
        details = self.build_details()
        GUIErrorHandler.show_error_dialog(parent, self.title, self.message, details)


# Enhanced convenience functions for common error scenarios
def show_file_error(parent: Optional[ctk.CTk], operation: str, file_path: str, error: Exception) -> bool:
    """
    Show a standardized file operation error dialog with recovery options.
    
    Returns:
        True if user wants to retry, False otherwise
    """
    return GUIErrorHandler.handle_file_dialog_error(parent, f"{operation} file: {file_path}", error) is not None


def show_database_error(parent: Optional[ctk.CTk], database_path: str, error: Exception) -> bool:
    """
    Show a standardized database connection error dialog with recovery options.
    
    Returns:
        True if user wants to retry, False otherwise
    """
    return GUIErrorHandler.handle_database_connection_error(parent, database_path, error)


def show_validation_error(parent: Optional[ctk.CTk], field_name: str, validation_message: str) -> None:
    """Show a standardized validation error dialog."""
    builder = ErrorDialogBuilder()
    builder.set_title("Validation Error")
    builder.set_message(f"Invalid {field_name}: {validation_message}")
    builder.add_suggestion("Please correct the highlighted field and try again")
    builder.show(parent)


def show_performance_warning(parent: Optional[ctk.CTk], operation: str, file_size_mb: float) -> bool:
    """
    Show a performance warning for large files.
    
    Args:
        parent: Parent window
        operation: Description of the operation
        file_size_mb: File size in megabytes
        
    Returns:
        True if user wants to continue, False to cancel
    """
    builder = ErrorDialogBuilder()
    builder.set_title("Performance Warning")
    builder.set_message(f"Large file detected ({file_size_mb:.1f} MB) for {operation}")
    builder.add_suggestion("This operation may take longer than usual")
    builder.add_suggestion("Consider using a smaller file or dataset")
    builder.add_suggestion("Ensure you have sufficient system resources")
    
    return GUIErrorHandler.show_confirmation_dialog(
        parent,
        "Large File Warning",
        f"Processing a large file ({file_size_mb:.1f} MB) may impact performance.\n\nDo you want to continue?\n\n{builder.build_details()}"
    )


def show_network_error(parent: Optional[ctk.CTk], operation: str, error: Exception) -> bool:
    """
    Show a network error dialog with retry options.
    
    Args:
        parent: Parent window
        operation: Description of the network operation
        error: The network error
        
    Returns:
        True if user wants to retry, False otherwise
    """
    builder = ErrorDialogBuilder()
    builder.set_title("Network Error")
    builder.set_message(f"Network operation failed: {operation}")
    builder.add_details(str(error))
    builder.add_suggestion("Check your internet connection")
    builder.add_suggestion("Verify firewall settings")
    builder.add_suggestion("Try again in a few moments")
    
    return GUIErrorHandler.show_retry_dialog(
        parent,
        "Network Error",
        f"Failed to {operation}. Would you like to try again?",
        builder.build_details()
    )


def show_permission_error(parent: Optional[ctk.CTk], resource: str, error: Exception) -> bool:
    """
    Show a permission error dialog with suggestions.
    
    Args:
        parent: Parent window
        resource: Description of the resource (file, folder, etc.)
        error: The permission error
        
    Returns:
        True if user wants to retry, False otherwise
    """
    builder = ErrorDialogBuilder()
    builder.set_title("Permission Error")
    builder.set_message(f"Access denied to {resource}")
    builder.add_details(str(error))
    builder.add_suggestion("Check file/folder permissions")
    builder.add_suggestion("Run the application as administrator if needed")
    builder.add_suggestion("Verify the resource is not in use by another application")
    builder.add_suggestion("Try selecting a different location")
    
    return GUIErrorHandler.show_retry_dialog(
        parent,
        "Permission Denied",
        f"Access denied to {resource}. Would you like to try again?",
        builder.build_details()
    )


class ProgressErrorHandler:
    """
    Specialized error handler for progress-related operations.
    Provides context-aware error handling during long-running tasks.
    """
    
    @staticmethod
    def handle_operation_timeout(parent: Optional[ctk.CTk], operation: str, timeout_seconds: int) -> bool:
        """
        Handle operation timeout errors.
        
        Args:
            parent: Parent window
            operation: Description of the timed-out operation
            timeout_seconds: Timeout duration in seconds
            
        Returns:
            True if user wants to retry with longer timeout, False to cancel
        """
        builder = ErrorDialogBuilder()
        builder.set_title("Operation Timeout")
        builder.set_message(f"Operation timed out after {timeout_seconds} seconds: {operation}")
        builder.add_suggestion("Try again with a longer timeout")
        builder.add_suggestion("Check system performance and close other applications")
        builder.add_suggestion("Consider processing smaller datasets")
        
        return GUIErrorHandler.show_retry_dialog(
            parent,
            "Operation Timeout",
            f"The operation '{operation}' timed out after {timeout_seconds} seconds. Would you like to try again?",
            builder.build_details()
        )
    
    @staticmethod
    def handle_cancellation_error(parent: Optional[ctk.CTk], operation: str) -> None:
        """
        Handle operation cancellation gracefully.
        
        Args:
            parent: Parent window
            operation: Description of the cancelled operation
        """
        GUIErrorHandler.show_info_dialog(
            parent,
            "Operation Cancelled",
            f"The operation '{operation}' was cancelled by the user.",
            auto_close_ms=3000
        )
    
    @staticmethod
    def handle_progress_error(parent: Optional[ctk.CTk], operation: str, progress: float, error: Exception) -> bool:
        """
        Handle errors that occur during progress operations.
        
        Args:
            parent: Parent window
            operation: Description of the operation
            progress: Progress percentage (0.0 to 1.0)
            error: The error that occurred
            
        Returns:
            True if user wants to retry from current position, False to cancel
        """
        builder = ErrorDialogBuilder()
        builder.set_title("Operation Error")
        builder.set_message(f"Error occurred during {operation} at {progress*100:.1f}% completion")
        builder.add_details(str(error))
        builder.add_suggestion("Try resuming from the current position")
        builder.add_suggestion("Restart the operation from the beginning")
        builder.add_suggestion("Check system resources and try again")
        
        return GUIErrorHandler.show_retry_dialog(
            parent,
            "Operation Failed",
            f"An error occurred during '{operation}' at {progress*100:.1f}% completion. Would you like to try resuming?",
            builder.build_details()
        )