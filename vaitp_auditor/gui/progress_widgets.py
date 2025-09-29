"""
Progress Widgets Module

Provides loading indicators, progress dialogs, and progress callback systems
for long-running operations in the GUI. Includes cancel functionality for
interruptible operations.
"""

import customtkinter as ctk
import threading
import time
from typing import Optional, Callable, Any, Dict
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class ProgressState(Enum):
    """Enumeration of progress states."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class ProgressInfo:
    """Information about progress state."""
    current: int
    total: int
    message: str
    percentage: float
    state: ProgressState
    elapsed_time: float = 0.0
    estimated_remaining: float = 0.0
    
    @property
    def is_indeterminate(self) -> bool:
        """Check if progress is indeterminate (total unknown)."""
        return self.total <= 0
    
    @property
    def is_complete(self) -> bool:
        """Check if progress is complete."""
        return self.state == ProgressState.COMPLETED
    
    @property
    def is_cancelled(self) -> bool:
        """Check if progress was cancelled."""
        return self.state == ProgressState.CANCELLED
    
    @property
    def has_error(self) -> bool:
        """Check if progress encountered an error."""
        return self.state == ProgressState.ERROR


class ProgressCallback(ABC):
    """Abstract base class for progress callbacks."""
    
    @abstractmethod
    def update_progress(self, progress_info: ProgressInfo) -> None:
        """Update progress information."""
        pass
    
    @abstractmethod
    def is_cancelled(self) -> bool:
        """Check if operation should be cancelled."""
        pass


class LoadingIndicator(ctk.CTkFrame):
    """
    Simple loading indicator widget with spinning animation.
    
    Provides visual feedback for indeterminate operations.
    """
    
    def __init__(self, parent, message: str = "Loading..."):
        """
        Initialize loading indicator.
        
        Args:
            parent: Parent widget
            message: Loading message to display
        """
        super().__init__(parent)
        
        self.message = message
        self.is_running = False
        self.animation_thread: Optional[threading.Thread] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        
        # Progress bar (indeterminate)
        self.progress_bar = ctk.CTkProgressBar(
            self,
            mode="indeterminate",
            width=200,
            height=20
        )
        self.progress_bar.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="ew")
        
        # Message label
        self.message_label = ctk.CTkLabel(
            self,
            text=self.message,
            font=ctk.CTkFont(size=12)
        )
        self.message_label.grid(row=1, column=0, pady=(0, 20), padx=20)
    
    def start(self) -> None:
        """Start the loading animation."""
        if not self.is_running:
            self.is_running = True
            self.progress_bar.start()
    
    def stop(self) -> None:
        """Stop the loading animation."""
        if self.is_running:
            self.is_running = False
            self.progress_bar.stop()
    
    def set_message(self, message: str) -> None:
        """
        Update the loading message.
        
        Args:
            message: New message to display
        """
        self.message = message
        self.message_label.configure(text=message)


class ProgressDialog(ctk.CTkToplevel):
    """
    Modal progress dialog with cancel functionality.
    
    Provides detailed progress information and allows user cancellation
    of long-running operations.
    """
    
    def __init__(
        self,
        parent: ctk.CTk,
        title: str = "Progress",
        message: str = "Processing...",
        can_cancel: bool = True,
        show_details: bool = True
    ):
        """
        Initialize progress dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            message: Initial progress message
            can_cancel: Whether to show cancel button
            show_details: Whether to show detailed progress information
        """
        super().__init__(parent)
        
        self.parent_window = parent
        self.can_cancel = can_cancel
        self.show_details = show_details
        self.is_cancelled = False
        self.progress_info: Optional[ProgressInfo] = None
        
        self.title(title)
        self.geometry("400x250")
        self.resizable(False, False)
        
        # Set application icon
        try:
            from .icon_utils import set_window_icon
            set_window_icon(self, store_reference=True)
        except Exception:
            pass  # Silently fail for dialog icons
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self._center_on_parent()
        
        self._setup_ui(message)
    
    def _center_on_parent(self) -> None:
        """Center dialog on parent window."""
        self.update_idletasks()
        
        parent_x = self.parent_window.winfo_x()
        parent_y = self.parent_window.winfo_y()
        parent_width = self.parent_window.winfo_width()
        parent_height = self.parent_window.winfo_height()
        
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _setup_ui(self, message: str) -> None:
        """Set up the user interface."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Main message
        self.message_label = ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=350
        )
        self.message_label.grid(row=0, column=0, pady=20, padx=20, sticky="ew")
        
        # Progress frame
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.grid(row=1, column=0, pady=(0, 20), padx=20, sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=300,
            height=20
        )
        self.progress_bar.grid(row=0, column=0, pady=10, padx=20, sticky="ew")
        self.progress_bar.set(0)
        
        # Progress text
        self.progress_text = ctk.CTkLabel(
            self.progress_frame,
            text="0%",
            font=ctk.CTkFont(size=12)
        )
        self.progress_text.grid(row=1, column=0, pady=(0, 10))
        
        if self.show_details:
            # Details frame
            self.details_frame = ctk.CTkFrame(self.progress_frame)
            self.details_frame.grid(row=2, column=0, pady=10, padx=20, sticky="ew")
            self.details_frame.grid_columnconfigure((0, 1), weight=1)
            
            # Elapsed time
            self.elapsed_label = ctk.CTkLabel(
                self.details_frame,
                text="Elapsed: 0s",
                font=ctk.CTkFont(size=10)
            )
            self.elapsed_label.grid(row=0, column=0, pady=5, padx=5, sticky="w")
            
            # Remaining time
            self.remaining_label = ctk.CTkLabel(
                self.details_frame,
                text="Remaining: --",
                font=ctk.CTkFont(size=10)
            )
            self.remaining_label.grid(row=0, column=1, pady=5, padx=5, sticky="e")
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=2, column=0, pady=20, padx=20, sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1)
        
        if self.can_cancel:
            # Cancel button
            self.cancel_button = ctk.CTkButton(
                self.button_frame,
                text="Cancel",
                command=self._on_cancel,
                width=100,
                fg_color="red",
                hover_color="darkred"
            )
            self.cancel_button.grid(row=0, column=0, pady=10)
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        if self.can_cancel and not self.is_cancelled:
            self.is_cancelled = True
            if hasattr(self, 'cancel_button'):
                self.cancel_button.configure(text="Cancelling...", state="disabled")
    
    def update_progress(self, progress_info: ProgressInfo) -> None:
        """
        Update progress information.
        
        Args:
            progress_info: Current progress information
        """
        self.progress_info = progress_info
        
        # Update message
        self.message_label.configure(text=progress_info.message)
        
        # Update progress bar
        if progress_info.is_indeterminate:
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self.progress_text.configure(text="Processing...")
        else:
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(progress_info.percentage / 100.0)
            self.progress_text.configure(text=f"{progress_info.percentage:.1f}%")
        
        if self.show_details:
            # Update elapsed time
            elapsed_str = self._format_time(progress_info.elapsed_time)
            self.elapsed_label.configure(text=f"Elapsed: {elapsed_str}")
            
            # Update remaining time
            if progress_info.estimated_remaining > 0:
                remaining_str = self._format_time(progress_info.estimated_remaining)
                self.remaining_label.configure(text=f"Remaining: {remaining_str}")
            else:
                self.remaining_label.configure(text="Remaining: --")
        
        # Handle completion
        if progress_info.is_complete:
            self._on_completion()
        elif progress_info.has_error:
            self._on_error()
    
    def _format_time(self, seconds: float) -> str:
        """
        Format time duration for display.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:.0f}m {secs:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h {minutes:.0f}m"
    
    def _on_completion(self) -> None:
        """Handle operation completion."""
        if hasattr(self, 'cancel_button'):
            self.cancel_button.configure(text="Close", fg_color="green", hover_color="darkgreen")
            self.cancel_button.configure(command=self.destroy)
        
        # Auto-close after 2 seconds
        self.after(2000, self.destroy)
    
    def _on_error(self) -> None:
        """Handle operation error."""
        if hasattr(self, 'cancel_button'):
            self.cancel_button.configure(text="Close", fg_color="red", hover_color="darkred")
            self.cancel_button.configure(command=self.destroy)


class ProgressManager:
    """
    Manager for coordinating progress operations and callbacks.
    
    Provides a centralized way to manage progress tracking, callbacks,
    and cancellation for long-running operations.
    """
    
    def __init__(self):
        """Initialize progress manager."""
        self.callbacks: Dict[str, ProgressCallback] = {}
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.start_times: Dict[str, float] = {}
    
    def register_callback(self, operation_id: str, callback: ProgressCallback) -> None:
        """
        Register a progress callback for an operation.
        
        Args:
            operation_id: Unique identifier for the operation
            callback: Progress callback to register
        """
        self.callbacks[operation_id] = callback
    
    def unregister_callback(self, operation_id: str) -> None:
        """
        Unregister a progress callback.
        
        Args:
            operation_id: Operation identifier to unregister
        """
        self.callbacks.pop(operation_id, None)
        self.active_operations.pop(operation_id, None)
        self.start_times.pop(operation_id, None)
    
    def start_operation(self, operation_id: str, total_items: int = 0, message: str = "Processing...") -> None:
        """
        Start tracking a new operation.
        
        Args:
            operation_id: Unique identifier for the operation
            total_items: Total number of items to process (0 for indeterminate)
            message: Initial progress message
        """
        self.start_times[operation_id] = time.time()
        self.active_operations[operation_id] = {
            'total': total_items,
            'current': 0,
            'message': message,
            'state': ProgressState.RUNNING
        }
        
        # Send initial progress update
        self._update_progress(operation_id)
    
    def update_operation(
        self,
        operation_id: str,
        current: Optional[int] = None,
        message: Optional[str] = None,
        state: Optional[ProgressState] = None
    ) -> None:
        """
        Update operation progress.
        
        Args:
            operation_id: Operation identifier
            current: Current progress value
            message: Updated progress message
            state: Updated progress state
        """
        if operation_id not in self.active_operations:
            return
        
        operation = self.active_operations[operation_id]
        
        if current is not None:
            operation['current'] = current
        if message is not None:
            operation['message'] = message
        if state is not None:
            operation['state'] = state
        
        self._update_progress(operation_id)
    
    def complete_operation(self, operation_id: str, message: str = "Completed") -> None:
        """
        Mark operation as completed.
        
        Args:
            operation_id: Operation identifier
            message: Completion message
        """
        self.update_operation(operation_id, message=message, state=ProgressState.COMPLETED)
    
    def cancel_operation(self, operation_id: str, message: str = "Cancelled") -> None:
        """
        Mark operation as cancelled.
        
        Args:
            operation_id: Operation identifier
            message: Cancellation message
        """
        self.update_operation(operation_id, message=message, state=ProgressState.CANCELLED)
    
    def error_operation(self, operation_id: str, message: str = "Error occurred") -> None:
        """
        Mark operation as having an error.
        
        Args:
            operation_id: Operation identifier
            message: Error message
        """
        self.update_operation(operation_id, message=message, state=ProgressState.ERROR)
    
    def is_cancelled(self, operation_id: str) -> bool:
        """
        Check if operation is cancelled.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            True if operation is cancelled, False otherwise
        """
        callback = self.callbacks.get(operation_id)
        if callback:
            return callback.is_cancelled()
        
        operation = self.active_operations.get(operation_id)
        if operation:
            return operation['state'] == ProgressState.CANCELLED
        
        return False
    
    def _update_progress(self, operation_id: str) -> None:
        """
        Send progress update to registered callback.
        
        Args:
            operation_id: Operation identifier
        """
        callback = self.callbacks.get(operation_id)
        operation = self.active_operations.get(operation_id)
        
        if not callback or not operation:
            return
        
        # Calculate progress information
        current = operation['current']
        total = operation['total']
        message = operation['message']
        state = operation['state']
        
        if total > 0:
            percentage = (current / total) * 100.0
        else:
            percentage = 0.0
        
        # Calculate timing
        start_time = self.start_times.get(operation_id, time.time())
        elapsed_time = time.time() - start_time
        
        if total > 0 and current > 0 and elapsed_time > 0:
            rate = current / elapsed_time
            remaining_items = total - current
            estimated_remaining = remaining_items / rate if rate > 0 else 0.0
        else:
            estimated_remaining = 0.0
        
        # Create progress info
        progress_info = ProgressInfo(
            current=current,
            total=total,
            message=message,
            percentage=percentage,
            state=state,
            elapsed_time=elapsed_time,
            estimated_remaining=estimated_remaining
        )
        
        # Send update
        callback.update_progress(progress_info)


class DialogProgressCallback(ProgressCallback):
    """
    Progress callback that updates a progress dialog.
    """
    
    def __init__(self, dialog: ProgressDialog):
        """
        Initialize callback with dialog.
        
        Args:
            dialog: Progress dialog to update
        """
        self.dialog = dialog
    
    def update_progress(self, progress_info: ProgressInfo) -> None:
        """Update the progress dialog."""
        self.dialog.update_progress(progress_info)
    
    def is_cancelled(self) -> bool:
        """Check if dialog was cancelled."""
        return self.dialog.is_cancelled


# Convenience functions for common progress operations
def show_loading_dialog(
    parent: ctk.CTk,
    title: str = "Loading",
    message: str = "Please wait...",
    can_cancel: bool = False
) -> ProgressDialog:
    """
    Show a simple loading dialog.
    
    Args:
        parent: Parent window
        title: Dialog title
        message: Loading message
        can_cancel: Whether to allow cancellation
        
    Returns:
        Progress dialog instance
    """
    dialog = ProgressDialog(parent, title, message, can_cancel, show_details=False)
    
    # Start indeterminate progress
    progress_info = ProgressInfo(
        current=0,
        total=0,
        message=message,
        percentage=0.0,
        state=ProgressState.RUNNING
    )
    dialog.update_progress(progress_info)
    
    return dialog


def run_with_progress(
    parent: ctk.CTk,
    operation: Callable[[ProgressCallback], Any],
    title: str = "Processing",
    message: str = "Please wait...",
    can_cancel: bool = True
) -> Any:
    """
    Run an operation with progress dialog.
    
    Args:
        parent: Parent window
        operation: Function to run (should accept ProgressCallback)
        title: Dialog title
        message: Initial message
        can_cancel: Whether to allow cancellation
        
    Returns:
        Result of the operation
    """
    dialog = ProgressDialog(parent, title, message, can_cancel)
    callback = DialogProgressCallback(dialog)
    result = None
    error = None
    
    def run_operation():
        nonlocal result, error
        try:
            result = operation(callback)
        except Exception as e:
            error = e
        finally:
            # Ensure dialog is closed
            dialog.after(100, dialog.destroy)
    
    # Run operation in thread
    thread = threading.Thread(target=run_operation, daemon=True)
    thread.start()
    
    # Show dialog (blocks until closed)
    dialog.wait_window()
    
    # Wait for thread to complete
    thread.join(timeout=1.0)
    
    if error:
        raise error
    
    return result