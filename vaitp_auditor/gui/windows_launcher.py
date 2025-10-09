"""
Windows-specific launcher to prevent console window creation.

This module provides a Windows-specific entry point that suppresses
console window creation for the GUI application.
"""

# Suppress console windows at module import level
try:
    import platform
    if platform.system() == "Windows":
        import ctypes
        import ctypes.wintypes
        
        # Immediate console suppression
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        
        # Get and hide console window
        console_window = kernel32.GetConsoleWindow()
        if console_window != 0:
            SW_HIDE = 0
            user32.ShowWindow(console_window, SW_HIDE)
            
        # Free console
        try:
            kernel32.FreeConsole()
        except:
            pass
            
        # Redirect stdout/stderr to null to prevent console creation
        import os
        import sys
        
        # Only redirect if not in debug mode
        if not any('debug' in arg.lower() for arg in sys.argv):
            try:
                # Redirect to null device
                null_device = os.devnull
                sys.stdout = open(null_device, 'w')
                sys.stderr = open(null_device, 'w')
            except:
                pass
                
except Exception:
    pass


import sys
import os


def suppress_console_window():
    """Suppress console window creation on Windows."""
    try:
        import platform
        if platform.system() == "Windows":
            import ctypes
            import ctypes.wintypes
            
            # Hide console window immediately
            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32
            
            # Get console window handle
            console_window = kernel32.GetConsoleWindow()
            
            if console_window != 0:
                # Hide the console window
                SW_HIDE = 0
                user32.ShowWindow(console_window, SW_HIDE)
            
            # Free console to prevent it from reappearing
            try:
                kernel32.FreeConsole()
            except:
                pass
                
    except Exception:
        pass  # Ignore all errors


def main():
    """Windows GUI entry point that suppresses console windows."""
    # Suppress console window immediately
    suppress_console_window()
    
    # Import and run the main GUI application
    try:
        from .gui_app import main as gui_main
        gui_main()
    except ImportError:
        # Fallback import path
        from vaitp_auditor.gui.gui_app import main as gui_main
        gui_main()


if __name__ == "__main__":
    main()