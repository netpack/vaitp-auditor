"""
GUI Application Entry Point

Main entry point for the VAITP-Auditor GUI application.
Handles application lifecycle, command-line argument parsing, and window management.
"""

import argparse
import sys
import logging
import atexit
from typing import Optional

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from ..utils.logging_config import setup_logging
from ..utils.resource_manager import cleanup_resources
from ..core.models import SessionConfig
from .accessibility import AccessibilityManager, AccessibilityConfig, create_accessibility_manager


class GUIApplication:
    """
    Main GUI application class that manages the application lifecycle.
    
    This class serves as the entry point for the GUI mode of VAITP-Auditor,
    handling initialization, window management, and cleanup.
    """
    
    def __init__(self):
        """Initialize the GUI application."""
        self.root: Optional[ctk.CTk] = None
        self.setup_wizard: Optional['SetupWizard'] = None
        self.main_review_window: Optional['MainReviewWindow'] = None
        self.session_controller: Optional['GUISessionController'] = None
        self.accessibility_manager: Optional[AccessibilityManager] = None
        self.logger = logging.getLogger(__name__)
        
        # Check if GUI dependencies are available
        if ctk is None:
            raise ImportError(
                "GUI dependencies not available. Please install with: "
                "pip install customtkinter pygments pillow"
            )
        
        # Register cleanup handler
        atexit.register(self.handle_application_exit)
    
    def _set_application_icon(self) -> None:
        """Set the application icon for the main window and globally."""
        from .icon_utils import set_window_icon, initialize_platform_icons, set_global_application_icon
        
        # Initialize platform-specific icons first
        try:
            initialize_platform_icons()
        except Exception as e:
            self.logger.debug(f"Could not initialize platform icons: {e}")
        
        # Set the global application icon (affects Dock on macOS)
        try:
            global_success = set_global_application_icon(self.root)
            if global_success:
                self.logger.debug("Global application icon set successfully")
            else:
                self.logger.debug("Could not set global application icon")
        except Exception as e:
            self.logger.debug(f"Error setting global application icon: {e}")
        
        # Set the window icon
        success = set_window_icon(self.root, store_reference=True)
        if success:
            self.logger.debug("Window icon set successfully")
        else:
            self.logger.debug("Could not set window icon")
    
    def run(self) -> None:
        """
        Run the GUI application.
        
        This method initializes the CustomTkinter application and starts
        the main event loop.
        """
        try:
            # Set CustomTkinter appearance mode and color theme
            ctk.set_appearance_mode("system")  # Modes: system, light, dark
            ctk.set_default_color_theme("blue")  # Themes: blue, dark-blue, green
            
            # Create the main application window (minimized initially)
            self.root = ctk.CTk()
            self.root.title("VAITP-Auditor")
            self.root.geometry("800x600")
            
            # Set application icon
            self._set_application_icon()
            
            # Center the main window on screen
            self.root.update_idletasks()
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width // 2) - 400  # 400 = half of 800
            y = (screen_height // 2) - 300  # 300 = half of 600
            self.root.geometry(f"800x600+{x}+{y}")
            
            # Minimize the main window initially (but don't hide it completely)
            self.root.iconify()
            
            # Set up window close protocol
            self.root.protocol("WM_DELETE_WINDOW", self.handle_application_exit)
            
            # Initialize accessibility manager
            self._setup_accessibility()
            
            # Launch the Setup Wizard immediately
            self.launch_setup_wizard()
            
            # Start the main event loop
            self.logger.info("Starting VAITP-Auditor GUI application")
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Error running GUI application: {e}")
            self.handle_application_exit()
            raise
    
    def _setup_accessibility(self) -> None:
        """
        Set up accessibility features for the application.
        """
        try:
            # Create accessibility configuration with enhanced features
            accessibility_config = AccessibilityConfig(
                enable_keyboard_navigation=True,
                tab_navigation=True,
                arrow_key_navigation=True,
                enable_screen_reader=True,
                announce_changes=True,
                verbose_descriptions=False,
                high_contrast_mode=False,
                font_scale_factor=1.0,
                focus_indicator_width=3,
                enable_audio_feedback=False,
                button_click_sound=False
            )
            
            # Create accessibility manager
            self.accessibility_manager = create_accessibility_manager(
                self.root, 
                accessibility_config
            )
            
            # Set up global accessibility shortcuts
            self._setup_global_accessibility_shortcuts()
            
            self.logger.info("Accessibility features initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error setting up accessibility: {e}")
            # Don't fail the application if accessibility setup fails
    
    def _setup_global_accessibility_shortcuts(self) -> None:
        """
        Set up global accessibility keyboard shortcuts.
        """
        try:
            if not self.accessibility_manager:
                return
            
            # Additional application-specific shortcuts
            self.root.bind("<Control-Shift-A>", self._show_accessibility_settings)
            self.root.bind("<F12>", self._toggle_accessibility_help)
            
            # Window management shortcuts
            self.root.bind("<Alt-F4>", lambda e: self.handle_application_exit())
            self.root.bind("<Control-q>", lambda e: self.handle_application_exit())
            
            self.logger.debug("Global accessibility shortcuts configured")
            
        except Exception as e:
            self.logger.error(f"Error setting up global accessibility shortcuts: {e}")
    
    def _show_accessibility_settings(self, event=None) -> None:
        """
        Show accessibility settings dialog.
        
        Args:
            event: Keyboard event (optional)
        """
        try:
            from .accessibility_settings import AccessibilitySettingsDialog
            
            if self.accessibility_manager:
                dialog = AccessibilitySettingsDialog(
                    self.root, 
                    self.accessibility_manager
                )
                dialog.show()
            
        except ImportError:
            # Fallback if settings dialog not implemented
            if self.accessibility_manager:
                self.accessibility_manager.announce(
                    "Accessibility settings dialog not available in this version",
                    priority="normal"
                )
        except Exception as e:
            self.logger.error(f"Error showing accessibility settings: {e}")
    
    def _toggle_accessibility_help(self, event=None) -> None:
        """
        Toggle accessibility help display.
        
        Args:
            event: Keyboard event (optional)
        """
        try:
            if self.accessibility_manager and self.accessibility_manager.keyboard_nav:
                self.accessibility_manager.keyboard_nav._show_help()
        except Exception as e:
            self.logger.error(f"Error toggling accessibility help: {e}")
    
    def launch_setup_wizard(self) -> None:
        """
        Launch the Setup Wizard window.
        """
        try:
            from .setup_wizard import SetupWizard
            from .models import get_default_gui_config
            
            # Create and show the setup wizard
            gui_config = get_default_gui_config()
            self.setup_wizard = SetupWizard(
                self.root, 
                gui_config, 
                accessibility_manager=self.accessibility_manager
            )
            
            # Set completion callback to launch main review window
            self.setup_wizard.set_completion_callback(self.launch_main_review)
            
            # Set cancellation callback to exit application
            self.setup_wizard.set_cancellation_callback(self.handle_application_exit)
            
            self.logger.info("Setup Wizard launched successfully")
            
        except Exception as e:
            self.logger.error(f"Error launching Setup Wizard: {e}")
            from .error_handler import GUIErrorHandler
            GUIErrorHandler.show_error_dialog(
                self.root,
                "Setup Error",
                f"Failed to launch Setup Wizard: {e}"
            )
            self.handle_application_exit()
    
    def launch_main_review(self, session_config_data) -> None:
        """
        Launch the Main Review Window with the provided session configuration.
        
        Args:
            session_config_data: Session configuration (dict from Setup Wizard or SessionConfig object)
        """
        try:
            from .main_review_window import MainReviewWindow
            from .gui_session_controller import GUISessionController
            
            # Handle both dictionary and SessionConfig object
            # Use the session config data directly (SessionConfig object will be created by the session controller)
            
            # Close the setup wizard
            if self.setup_wizard:
                self.setup_wizard.destroy()
                self.setup_wizard = None
            
            # Show and focus the main window
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.root.title(f"VAITP-Auditor - Reviewing: {session_config_data.get('experiment_name', 'Unknown')}")
            
            # Configure the main window for review
            from .models import get_default_gui_config
            gui_config = get_default_gui_config()
            
            # Center the window on screen
            self.root.update_idletasks()  # Ensure window is ready for geometry calculations
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Calculate center position
            x = (screen_width // 2) - (gui_config.window_width // 2)
            y = (screen_height // 2) - (gui_config.window_height // 2)
            
            # Ensure window is visible on screen
            x = max(0, min(x, screen_width - gui_config.window_width))
            y = max(0, min(y, screen_height - gui_config.window_height))
            
            self.root.geometry(f"{gui_config.window_width}x{gui_config.window_height}+{x}+{y}")
            self.root.minsize(800, 600)
            
            # Setup menu bar
            self._setup_menu()
            
            # Create and configure the session controller first
            self.session_controller = GUISessionController(gui_config)
            
            # Create the main review window content with callbacks connected to session controller
            from .main_review_window import MainReviewContent
            self.main_review_window = MainReviewContent(
                self.root, 
                gui_config,
                verdict_callback=self.session_controller.submit_verdict,
                undo_callback=self.session_controller.handle_undo_request,
                quit_callback=self.session_controller.handle_quit_request,
                save_callback=self._save_review_process,
                open_callback=self._open_review_process,
                restart_callback=self._restart_review_process,
                accessibility_manager=self.accessibility_manager
            )
            
            # Set the main window reference in the session controller
            self.session_controller.set_main_window(self.main_review_window)
            
            # Start the session
            success = self.session_controller.start_session_from_config(session_config_data)
            
            if not success:
                self.logger.error("Failed to start review session")
                from .error_handler import GUIErrorHandler
                GUIErrorHandler.show_error_dialog(
                    self.root,
                    "Session Error",
                    "Failed to start the review session. Please check your configuration and try again."
                )
                self.handle_application_exit()
                return
            
            self.logger.info(f"Main Review Window launched for experiment: {session_config_data.get('experiment_name', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Error launching Main Review Window: {e}")
            from .error_handler import GUIErrorHandler
            GUIErrorHandler.show_error_dialog(
                self.root,
                "Launch Error",
                f"Failed to launch Main Review Window: {e}"
            )
            self.handle_application_exit()
    
    def _setup_menu(self) -> None:
        """Setup the menu bar for the main window."""
        import tkinter as tk
        
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Create File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Review Process", command=self._save_review_process, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Open Review Process...", command=self._open_review_process, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Restart Review Process", command=self._restart_review_process, accelerator="Ctrl+R")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.handle_application_exit, accelerator="Ctrl+Q")
        
        # Create Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about_dialog)
        
        # Bind keyboard shortcuts
        self.root.bind_all("<Control-s>", lambda e: self._save_review_process())
        self.root.bind_all("<Control-o>", lambda e: self._open_review_process())
        self.root.bind_all("<Control-r>", lambda e: self._restart_review_process())
        self.root.bind_all("<Control-q>", lambda e: self.handle_application_exit())
    
    def _show_about_dialog(self) -> None:
        """Show the About dialog."""
        try:
            from .about_dialog import show_about_dialog
            show_about_dialog(self.root)
        except Exception as e:
            # Fallback error dialog if about dialog fails
            import tkinter.messagebox as messagebox
            messagebox.showinfo(
                "About VAITP-Auditor",
                "VAITP-Auditor\n\n"
                "This tool was created by Frédéric Bogaerts as part of his research "
                "at the University of Coimbra.\n\n"
                "For more information, visit:\n"
                "ResearchGate: https://www.researchgate.net/profile/Frederic-Bogaerts\n"
                "GitHub: https://www.github.com/netpack"
            )
    
    def _save_review_process(self) -> None:
        """Save the current review process."""
        try:
            if self.session_controller and self.session_controller.is_session_active():
                success = self.session_controller.save_session_state()
                import tkinter.messagebox as messagebox
                if success:
                    # Get session info for display
                    session_info = self.session_controller.get_session_state_info()
                    session_name = "Unknown"
                    if session_info and 'experiment_name' in session_info:
                        session_name = session_info['experiment_name']
                    
                    messagebox.showinfo(
                        "Save Review Process",
                        f"Review process '{session_name}' saved successfully!\n\n"
                        "You can resume this session later using 'Open Review Process'."
                    )
                else:
                    messagebox.showerror(
                        "Save Error",
                        "Failed to save the review process.\nPlease check the logs for details."
                    )
            else:
                import tkinter.messagebox as messagebox
                messagebox.showwarning(
                    "Save Review Process",
                    "No active review session to save.\n\n"
                    "Please start a review session first using the Setup Wizard."
                )
        except Exception as e:
            self.logger.error(f"Error saving review process: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "Save Error",
                f"An error occurred while saving:\n{str(e)}"
            )
    
    def _open_review_process(self) -> None:
        """Open another review process."""
        try:
            import tkinter.messagebox as messagebox
            
            # Check if there's an active session
            if self.session_controller and self.session_controller.is_session_active():
                result = messagebox.askyesno(
                    "Open Review Process",
                    "There is currently an active review session.\n\n"
                    "Do you want to save the current session before opening another one?",
                    icon="question"
                )
                if result:
                    self._save_review_process()
            
            # Launch the setup wizard to configure a new session or resume an existing one
            self.launch_setup_wizard()
            
        except Exception as e:
            self.logger.error(f"Error opening review process: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "Open Error",
                f"An error occurred while opening:\n{str(e)}"
            )
    
    def _restart_review_process(self) -> None:
        """Restart the current review process."""
        try:
            import tkinter.messagebox as messagebox
            
            if not self.session_controller or not self.session_controller.is_session_active():
                messagebox.showwarning(
                    "Restart Review Process",
                    "No active review session to restart.\n\n"
                    "Please start a review session first using the Setup Wizard."
                )
                return
            
            # Get current session info
            session_info = self.session_controller.get_session_state_info()
            session_name = "current session"
            if session_info and 'experiment_name' in session_info:
                session_name = f"'{session_info['experiment_name']}'"
            
            # Confirm restart action
            result = messagebox.askyesno(
                "Restart Review Process",
                f"Are you sure you want to restart {session_name}?\n\n"
                "This will reset all progress and start from the beginning.\n"
                "Any unsaved changes will be lost.",
                icon="warning"
            )
            
            if result:
                try:
                    # Get the current session config to restart with the same settings
                    current_config = self.session_controller.get_session_config()
                    
                    if current_config:
                        # Force session completion to clean up current state
                        self.session_controller.force_session_completion()
                        
                        # Start a new session with the same configuration
                        success = self.session_controller.start_session_from_config(current_config)
                        
                        if success:
                            messagebox.showinfo(
                                "Restart Review Process",
                                f"Review process {session_name} has been restarted successfully!\n\n"
                                "You can now begin reviewing from the first code pair."
                            )
                        else:
                            messagebox.showerror(
                                "Restart Error",
                                "Failed to restart the review process.\n"
                                "Please check the logs for details."
                            )
                    else:
                        messagebox.showerror(
                            "Restart Error",
                            "Could not retrieve session configuration for restart.\n"
                            "Please start a new session using the Setup Wizard."
                        )
                        
                except Exception as restart_error:
                    self.logger.error(f"Error during session restart: {restart_error}")
                    messagebox.showerror(
                        "Restart Error",
                        f"An error occurred during restart:\n{str(restart_error)}\n\n"
                        "Please try starting a new session using the Setup Wizard."
                    )
                    
        except Exception as e:
            self.logger.error(f"Error restarting review process: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "Restart Error",
                f"An error occurred while restarting:\n{str(e)}"
            )
    
    def handle_application_exit(self) -> None:
        """
        Handle application exit and cleanup.
        
        This method ensures proper cleanup when the application is closed.
        """
        # Prevent multiple cleanup calls
        if hasattr(self, '_cleanup_done') and self._cleanup_done:
            return
        
        try:
            self.logger.info("VAITP-Auditor GUI application shutting down")
            
            # Clean up accessibility manager
            if self.accessibility_manager:
                try:
                    self.accessibility_manager.cleanup()
                    self.accessibility_manager = None
                except Exception as e:
                    self.logger.error(f"Error cleaning up accessibility manager: {e}")
            
            # Clean up session controller
            if self.session_controller:
                try:
                    self.session_controller.cleanup()
                    self.session_controller = None
                except Exception as e:
                    self.logger.error(f"Error cleaning up session controller: {e}")
            
            # Clean up windows
            if self.setup_wizard:
                try:
                    self.setup_wizard.destroy()
                    self.setup_wizard = None
                except Exception as e:
                    self.logger.error(f"Error destroying setup wizard: {e}")
            
            if self.main_review_window:
                try:
                    self.main_review_window.destroy()
                    self.main_review_window = None
                except Exception as e:
                    self.logger.error(f"Error destroying main review window: {e}")
            
            # Clean up resources
            try:
                cleanup_resources()
            except Exception as e:
                self.logger.error(f"Error cleaning up resources: {e}")
            
            # Quit the application
            if self.root:
                try:
                    self.root.quit()
                    self.root.destroy()
                    self.root = None
                except Exception as e:
                    self.logger.error(f"Error quitting application: {e}")
            
            # Mark cleanup as done
            self._cleanup_done = True
                    
        except Exception as e:
            self.logger.error(f"Error during application exit: {e}")
        finally:
            # Force exit if needed
            sys.exit(0)


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command-line argument parser for GUI mode.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="VAITP-Auditor GUI - Desktop interface for manual code verification",
        prog="vaitp-auditor-gui"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file (default: logs to console)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="VAITP-Auditor GUI 1.0.0"
    )
    
    return parser


def main(args=None) -> None:
    """
    Main entry point for the GUI application.
    
    This function handles command-line argument parsing, logging setup,
    and application initialization.
    
    Args:
        args: Optional parsed arguments (for when called from CLI)
    """
    try:
        # Use provided args or parse command-line arguments
        if args is None:
            parser = create_argument_parser()
            args = parser.parse_args()
        
        # Setup logging
        log_level = "DEBUG" if getattr(args, 'debug', False) else "INFO"
        setup_logging(
            level=log_level,
            console_output=True,
            session_id=None,
            log_file=getattr(args, 'log_file', None)
        )
        
        # Create and run the GUI application
        app = GUIApplication()
        app.run()
        
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nApplication interrupted by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()