#!/usr/bin/env python3
"""
Cross-platform GUI launcher for VAITP-Auditor.

This script provides a reliable way to launch the GUI application
without console windows on Windows.
"""

import sys
import os
import platform


def suppress_windows_console():
    """Suppress console window on Windows."""
    if platform.system() == "Windows":
        try:
            import ctypes
            
            # Get console window
            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32
            console_window = kernel32.GetConsoleWindow()
            
            if console_window != 0:
                # Hide console window
                SW_HIDE = 0
                user32.ShowWindow(console_window, SW_HIDE)
                
                # Free console
                try:
                    kernel32.FreeConsole()
                except:
                    pass
        except Exception:
            pass


def main():
    """Launch the GUI application."""
    # Suppress console on Windows
    suppress_windows_console()
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    try:
        # Import and launch GUI
        from vaitp_auditor.gui.gui_app import main as gui_main
        gui_main()
    except ImportError as e:
        # Fallback error handling
        if platform.system() == "Windows":
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0, 
                f"Failed to launch VAITP-Auditor GUI: {e}\n\nPlease ensure the application is properly installed.",
                "VAITP-Auditor Error",
                0x10  # MB_ICONERROR
            )
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()