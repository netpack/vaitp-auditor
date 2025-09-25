"""
About Dialog for VAITP-Auditor GUI.

This module provides an About dialog with information about the application
and its creator.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional


class AboutDialog(ctk.CTkToplevel):
    """About dialog showing application information."""
    
    def __init__(self, parent: Optional[tk.Widget] = None):
        """Initialize the About dialog.
        
        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        
        # Configure dialog
        self.title("About VAITP-Auditor")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # Set application icon
        try:
            from .icon_utils import set_window_icon
            set_window_icon(self, store_reference=True)
        except Exception:
            pass  # Silently fail for dialog icons
        
        # Center the dialog on screen
        self.center_on_screen()
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Setup content
        self.setup_content()
        
        # Focus the dialog
        self.focus()
    
    def center_on_screen(self) -> None:
        """Center the dialog on the screen."""
        self.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calculate center position
        x = (screen_width // 2) - 250  # 250 = half of 500
        y = (screen_height // 2) - 200  # 200 = half of 400
        
        # Ensure dialog is visible on screen
        x = max(0, min(x, screen_width - 500))
        y = max(0, min(y, screen_height - 400))
        
        self.geometry(f"500x400+{x}+{y}")
    
    def setup_content(self) -> None:
        """Setup the dialog content."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        # Create main content frame
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Configure content frame grid
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text="VAITP-Auditor",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(20, 10), sticky="ew")
        
        # About text
        about_text = """This tool was created by Frédéric Bogaerts as part of his research at the University of Coimbra.

Frédéric is a cybersecurity researcher specializing in automating software security analysis, vulnerability injection, and the application of AI in cybersecurity. VAITP-Auditor is a practical component of his ongoing efforts to improve the evaluation and verification of AI-generated code.

To learn more about his publications or to explore other open-source projects, please visit:

ResearchGate: https://www.researchgate.net/profile/Frederic-Bogaerts
GitHub: https://www.github.com/netpack"""
        
        # Create scrollable text widget
        text_widget = ctk.CTkTextbox(
            content_frame,
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        text_widget.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        
        # Insert text and make it read-only
        text_widget.insert("1.0", about_text)
        text_widget.configure(state="disabled")
        
        # Close button
        close_button = ctk.CTkButton(
            self,
            text="✅ Close",
            command=self.destroy,
            width=100
        )
        close_button.grid(row=1, column=0, pady=(0, 20))
        
        # Bind Escape key to close
        self.bind("<Escape>", lambda e: self.destroy())


def show_about_dialog(parent: Optional[tk.Widget] = None) -> None:
    """Show the About dialog.
    
    Args:
        parent: Parent widget (optional)
    """
    AboutDialog(parent)


if __name__ == "__main__":
    # Test the dialog
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.withdraw()  # Hide the root window
    
    show_about_dialog()
    
    root.mainloop()