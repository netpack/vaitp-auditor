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
        self._icon_set = False  # Track if icon has been set
        
        # Check if GUI dependencies are available
        if ctk is None:
            raise ImportError(
                "GUI dependencies not available. Please install with: "
                "pip install customtkinter pygments pillow"
            )
        
        # Set early application identity BEFORE creating any GUI
        self._set_early_application_identity()
        
        # Register cleanup handler
        atexit.register(self.handle_application_exit)
    
    def _set_icon_immediately(self) -> None:
        """Set icon immediately after root window creation with the most direct approach."""
        import platform
        import os
        
        try:
            system = platform.system()
            
            # Get icon paths
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            vaitp_dir = os.path.join(base_dir, "vaitp_auditor")
            
            self.logger.info(f"🎯 AGGRESSIVELY setting icon immediately for {system}")
            
            if system == "Darwin":
                # macOS: CRITICAL - Set application name MULTIPLE times with different methods
                app_name_methods = [
                    lambda: self.root.tk.call('tk', 'appname', 'VAITP-Auditor'),
                    lambda: self.root.wm_title('VAITP-Auditor'),
                    lambda: self.root.title('VAITP-Auditor')
                ]
                
                for i, method in enumerate(app_name_methods):
                    try:
                        method()
                        self.logger.info(f"✅ macOS app name method {i+1} succeeded")
                    except Exception as e:
                        self.logger.debug(f"macOS app name method {i+1} failed: {e}")
                
                # Try ICNS with MULTIPLE methods (most aggressive approach)
                icns_path = os.path.join(vaitp_dir, "icon.icns")
                if os.path.exists(icns_path):
                    icns_methods = [
                        lambda: self.root.wm_iconbitmap(icns_path),
                        lambda: self.root.iconbitmap(icns_path),
                        lambda: self.root.iconbitmap(default=icns_path),
                        lambda: self.root.tk.call('wm', 'iconbitmap', '.', icns_path),
                        lambda: self.root.tk.call('wm', 'iconbitmap', self.root._w, icns_path)
                    ]
                    
                    success_count = 0
                    for i, method in enumerate(icns_methods):
                        try:
                            method()
                            success_count += 1
                            self.logger.info(f"✅ macOS ICNS method {i+1} succeeded!")
                        except Exception as e:
                            self.logger.debug(f"macOS ICNS method {i+1} failed: {e}")
                    
                    if success_count > 0:
                        self.logger.info(f"🎯 SUCCESS! {success_count} ICNS methods worked - icon should be visible!")
                
                # ALSO try PNG methods as additional backup
                png_path = os.path.join(vaitp_dir, "icon.png")
                if os.path.exists(png_path):
                    try:
                        # Use PIL for better quality if available
                        try:
                            from PIL import Image, ImageTk
                            img = Image.open(png_path)
                            if img.mode not in ['RGBA', 'RGB']:
                                img = img.convert('RGBA')
                            # Create multiple sizes for different contexts
                            icon_64 = img.resize((64, 64), Image.Resampling.LANCZOS)
                            icon_128 = img.resize((128, 128), Image.Resampling.LANCZOS)
                            photo_64 = ImageTk.PhotoImage(icon_64)
                            photo_128 = ImageTk.PhotoImage(icon_128)
                            
                            # Try multiple PNG methods
                            png_methods = [
                                lambda: self.root.wm_iconphoto(True, photo_64, photo_128),
                                lambda: self.root.iconphoto(True, photo_64),
                                lambda: self.root.tk.call('wm', 'iconphoto', '.', '-default', photo_64),
                                lambda: self.root.tk.call('wm', 'iconphoto', self.root._w, photo_64)
                            ]
                            
                            png_success = 0
                            for i, method in enumerate(png_methods):
                                try:
                                    method()
                                    png_success += 1
                                    self.logger.info(f"✅ macOS PNG method {i+1} succeeded")
                                except Exception as e:
                                    self.logger.debug(f"macOS PNG method {i+1} failed: {e}")
                            
                            # Store references to prevent garbage collection
                            self.root._vaitp_icon_64 = photo_64
                            self.root._vaitp_icon_128 = photo_128
                            
                            if png_success > 0:
                                self.logger.info(f"🎯 ADDITIONAL SUCCESS! {png_success} PNG methods worked!")
                            
                        except ImportError:
                            # Fallback to tkinter PhotoImage
                            import tkinter as tk
                            icon_photo = tk.PhotoImage(file=png_path)
                            self.root.wm_iconphoto(True, icon_photo)
                            self.root._vaitp_icon = icon_photo
                            self.logger.info("✅ macOS tkinter PNG fallback succeeded")
                            
                    except Exception as e:
                        self.logger.debug(f"PNG methods failed: {e}")
            
            elif system == "Windows":
                # Windows: Try ICO first
                ico_path = os.path.join(vaitp_dir, "icon.ico")
                if os.path.exists(ico_path):
                    try:
                        self.root.wm_iconbitmap(ico_path)
                        self.logger.info("✅ Set Windows ICO icon")
                        return
                    except Exception as e:
                        self.logger.debug(f"ICO failed: {e}")
                
                # Fallback to PNG
                png_path = os.path.join(vaitp_dir, "icon.png")
                if os.path.exists(png_path):
                    try:
                        import tkinter as tk
                        icon_photo = tk.PhotoImage(file=png_path)
                        self.root.wm_iconphoto(True, icon_photo)
                        self.root._vaitp_icon = icon_photo  # Prevent GC
                        self.logger.info("✅ Set Windows PNG icon")
                        return
                    except Exception as e:
                        self.logger.debug(f"PNG failed: {e}")
            
            else:
                # Linux: Use PNG
                png_path = os.path.join(vaitp_dir, "icon.png")
                if os.path.exists(png_path):
                    try:
                        import tkinter as tk
                        icon_photo = tk.PhotoImage(file=png_path)
                        self.root.wm_iconphoto(True, icon_photo)
                        self.root._vaitp_icon = icon_photo  # Prevent GC
                        self.logger.info("✅ Set Linux PNG icon")
                        return
                    except Exception as e:
                        self.logger.debug(f"PNG failed: {e}")
            
            # Force immediate update and make window visible to establish dock presence
            try:
                self.root.update_idletasks()
                self.root.deiconify()  # Make sure window is visible
                self.root.lift()       # Bring to front
                self.root.focus_force() # Focus to establish as main app
                self.logger.info("🎯 Forced window update and visibility - check dock now!")
            except Exception as e:
                self.logger.debug(f"Failed to force window update: {e}")
            
        except Exception as e:
            self.logger.error(f"Error setting icon immediately: {e}")
    
    def _reinforce_icon_after_setup(self) -> None:
        """Reinforce icon setting after CustomTkinter setup."""
        import platform
        import os
        
        try:
            system = platform.system()
            
            if system == "Darwin":
                # macOS: Re-assert application name and icon
                try:
                    self.root.tk.call('tk', 'appname', 'VAITP-Auditor')
                    
                    # Re-set icon
                    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    vaitp_dir = os.path.join(base_dir, "vaitp_auditor")
                    icns_path = os.path.join(vaitp_dir, "icon.icns")
                    
                    if os.path.exists(icns_path):
                        self.root.wm_iconbitmap(icns_path)
                        self.logger.info("✅ Reinforced macOS icon after CustomTkinter setup")
                        
                        # Schedule additional reinforcements
                        self.root.after(100, lambda: self._delayed_icon_reinforcement(icns_path))
                        self.root.after(500, lambda: self._delayed_icon_reinforcement(icns_path))
                        
                except Exception as e:
                    self.logger.debug(f"Icon reinforcement failed: {e}")
                    
        except Exception as e:
            self.logger.debug(f"Error reinforcing icon after setup: {e}")
    
    def _delayed_icon_reinforcement(self, icns_path: str) -> None:
        """Delayed icon reinforcement for macOS."""
        try:
            self.root.tk.call('tk', 'appname', 'VAITP-Auditor')
            self.root.wm_iconbitmap(icns_path)
            self.logger.debug("✅ Delayed icon reinforcement completed")
        except Exception as e:
            self.logger.debug(f"Delayed icon reinforcement failed: {e}")
    
    def _aggressive_icon_reinforcement(self) -> None:
        """Aggressive icon reinforcement with multiple attempts."""
        import platform
        import os
        
        try:
            if platform.system() == "Darwin":
                # Get icon path
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                vaitp_dir = os.path.join(base_dir, "vaitp_auditor")
                icns_path = os.path.join(vaitp_dir, "icon.icns")
                
                if os.path.exists(icns_path):
                    # Schedule multiple reinforcement attempts
                    delays = [50, 100, 200, 500, 1000, 2000]
                    
                    for delay in delays:
                        self.root.after(delay, lambda: self._super_aggressive_icon_set(icns_path))
                    
                    self.logger.info(f"🎯 Scheduled {len(delays)} aggressive icon reinforcement attempts")
                    
        except Exception as e:
            self.logger.debug(f"Error in aggressive icon reinforcement: {e}")
    
    def _super_aggressive_icon_set(self, icns_path: str) -> None:
        """Super aggressive icon setting with all possible methods."""
        try:
            # Re-set application name
            self.root.tk.call('tk', 'appname', 'VAITP-Auditor')
            
            # Try all ICNS methods again
            methods = [
                lambda: self.root.wm_iconbitmap(icns_path),
                lambda: self.root.iconbitmap(icns_path),
                lambda: self.root.iconbitmap(default=icns_path),
                lambda: self.root.tk.call('wm', 'iconbitmap', '.', icns_path),
                lambda: self.root.tk.call('wm', 'iconbitmap', self.root._w, icns_path)
            ]
            
            success_count = 0
            for method in methods:
                try:
                    method()
                    success_count += 1
                except:
                    pass
            
            if success_count > 0:
                self.logger.debug(f"🎯 Super aggressive: {success_count} methods succeeded")
                
                # Force window updates
                self.root.update_idletasks()
                self.root.lift()
                
        except Exception as e:
            self.logger.debug(f"Super aggressive icon setting failed: {e}")
    
    def _nuclear_icon_setting(self) -> None:
        """Nuclear option: Set icon with maximum force after everything is initialized."""
        import platform
        import os
        
        try:
            if platform.system() == "Darwin":
                self.logger.info("🚀 NUCLEAR OPTION: Setting macOS icon with maximum force...")
                
                # Get icon path
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                vaitp_dir = os.path.join(base_dir, "vaitp_auditor")
                icns_path = os.path.join(vaitp_dir, "icon.icns")
                
                if os.path.exists(icns_path):
                    # Step 1: Re-assert application identity
                    try:
                        self.root.tk.call('tk', 'appname', 'VAITP-Auditor')
                        self.root.wm_title('VAITP-Auditor')
                        self.root.title('VAITP-Auditor')
                        self.logger.info("🚀 Re-asserted application identity")
                    except Exception as e:
                        self.logger.debug(f"Failed to re-assert identity: {e}")
                    
                    # Step 2: Clear any existing icon
                    try:
                        self.root.wm_iconbitmap("")
                        self.logger.debug("🚀 Cleared existing icon")
                    except:
                        pass
                    
                    # Step 3: Set ICNS icon with ALL methods simultaneously
                    success_methods = []
                    methods = [
                        ("wm_iconbitmap", lambda: self.root.wm_iconbitmap(icns_path)),
                        ("iconbitmap", lambda: self.root.iconbitmap(icns_path)),
                        ("tk.call wm iconbitmap .", lambda: self.root.tk.call('wm', 'iconbitmap', '.', icns_path)),
                        ("tk.call wm iconbitmap root", lambda: self.root.tk.call('wm', 'iconbitmap', self.root._w, icns_path))
                    ]
                    
                    for name, method in methods:
                        try:
                            method()
                            success_methods.append(name)
                            self.logger.info(f"🚀 NUCLEAR: {name} succeeded")
                        except Exception as e:
                            self.logger.debug(f"NUCLEAR: {name} failed: {e}")
                    
                    # Step 4: Force immediate updates
                    try:
                        self.root.update_idletasks()
                        self.root.update()
                        self.root.lift()
                        self.root.focus_force()
                        self.logger.info("🚀 Forced immediate window updates")
                    except Exception as e:
                        self.logger.debug(f"Failed to force updates: {e}")
                    
                    # Step 5: Schedule continuous reinforcement
                    self._schedule_continuous_icon_reinforcement(icns_path)
                    
                    if success_methods:
                        self.logger.info(f"🚀 NUCLEAR SUCCESS! {len(success_methods)} methods worked: {', '.join(success_methods)}")
                        self.logger.info("🚀 If you still see Python icon, the issue may be system-level")
                    else:
                        self.logger.warning("🚀 NUCLEAR FAILURE: No methods worked")
                        
        except Exception as e:
            self.logger.error(f"Nuclear icon setting failed: {e}")
    
    def _schedule_continuous_icon_reinforcement(self, icns_path: str) -> None:
        """Schedule continuous icon reinforcement to maintain dock icon."""
        try:
            # Schedule reinforcement every few seconds for the first minute
            delays = [1000, 3000, 5000, 10000, 15000, 30000, 60000]  # milliseconds
            
            for delay in delays:
                self.root.after(delay, lambda: self._continuous_icon_reinforcement(icns_path))
            
            self.logger.info(f"🚀 Scheduled continuous icon reinforcement for 1 minute")
            
        except Exception as e:
            self.logger.debug(f"Failed to schedule continuous reinforcement: {e}")
    
    def _continuous_icon_reinforcement(self, icns_path: str) -> None:
        """Continuous icon reinforcement to maintain dock presence."""
        try:
            # Re-set application name and icon
            self.root.tk.call('tk', 'appname', 'VAITP-Auditor')
            self.root.wm_iconbitmap(icns_path)
            self.root.lift()  # Ensure window stays prominent
            self.logger.debug("🚀 Continuous icon reinforcement applied")
        except Exception as e:
            self.logger.debug(f"Continuous reinforcement failed: {e}")
    
    def _set_early_application_identity(self) -> None:
        """Set application identity as early as possible (before GUI creation)."""
        import platform
        import os
        
        try:
            system = platform.system()
            
            if system == "Darwin":
                # macOS: Suppress any console output that might cause windows
                self._suppress_macos_console_output()
                
                # CRITICAL: Set macOS application identity BEFORE any Tkinter operations
                try:
                    # Method 1: Set process title using setproctitle if available
                    try:
                        import setproctitle
                        setproctitle.setproctitle('VAITP-Auditor')
                        self.logger.debug("✅ Set process title using setproctitle")
                    except ImportError:
                        # Method 2: Modify sys.argv[0] as fallback
                        import sys
                        if hasattr(sys, 'argv') and sys.argv:
                            original_argv0 = sys.argv[0]
                            sys.argv[0] = 'VAITP-Auditor'
                            self.logger.debug("✅ Modified sys.argv[0] for process name")
                
                    # Method 3: Set environment variables that affect application identity
                    os.environ['CFBundleName'] = 'VAITP-Auditor'
                    os.environ['CFBundleDisplayName'] = 'VAITP-Auditor'
                    os.environ['CFBundleIdentifier'] = 'com.vaitp.auditor'
                    self.logger.debug("✅ Set macOS bundle environment variables")
                    
                    # Method 4: Try to set icon at system level BEFORE Tkinter
                    self._set_system_level_icon()
                    
                except Exception as e:
                    self.logger.debug(f"Early macOS identity setting failed: {e}")
            
        except Exception as e:
            self.logger.debug(f"Error in early application identity setting: {e}")
    
    def _set_system_level_icon(self) -> None:
        """Set icon at system level before creating any GUI windows."""
        import platform
        import os
        
        try:
            if platform.system() == "Darwin":
                # Get icon path
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                vaitp_dir = os.path.join(base_dir, "vaitp_auditor")
                icns_path = os.path.join(vaitp_dir, "icon.icns")
                
                if os.path.exists(icns_path):
                    # Try to set icon using macOS system calls before Tkinter
                    try:
                        # Method 1: Use osascript to set dock icon
                        import subprocess
                        script = f'''
                        tell application "System Events"
                            set frontApp to name of first application process whose frontmost is true
                            if frontApp is "Python" or frontApp contains "python" then
                                -- This will be handled by Tkinter later
                            end if
                        end tell
                        '''
                        # Don't actually run this as it might interfere
                        self.logger.debug("Prepared for system-level icon setting")
                        
                    except Exception as e:
                        self.logger.debug(f"System-level icon setting failed: {e}")
                        
        except Exception as e:
            self.logger.debug(f"Error in system-level icon setting: {e}")
    
    def _suppress_macos_console_output(self) -> None:
        """Suppress console output on macOS that might cause version windows."""
        try:
            import sys
            import os
            
            # Check if we're running in a GUI context (not from terminal)
            if not sys.stdout.isatty():
                return  # Already redirected, nothing to do
            
            # For GUI applications on macOS, redirect stdout/stderr to prevent
            # any console output that might trigger Terminal.app or console windows
            try:
                # Only redirect if not in debug mode
                if not any('debug' in arg.lower() for arg in sys.argv):
                    # Redirect to /dev/null to suppress all console output
                    devnull = open(os.devnull, 'w')
                    sys.stdout = devnull
                    sys.stderr = devnull
            except Exception:
                pass  # Ignore errors in redirection
                
        except Exception:
            pass  # Ignore all errors in console suppression
    

    def _set_application_icon(self) -> None:
        """Set the application icon for the main window and globally."""
        import platform
        
        from .icon_utils import set_window_icon, initialize_platform_icons, set_global_application_icon
        
        # Initialize platform-specific icons first
        try:
            initialize_platform_icons()
        except Exception as e:
            self.logger.debug(f"Could not initialize platform icons: {e}")
        
        system = platform.system()
        
        if system == "Windows":
            # Windows-specific icon handling
            self._set_windows_icon_optimized()
        elif system == "Darwin":
            # macOS-specific icon handling
            self._set_macos_icon_optimized()
        else:
            # Linux and other platforms
            self._set_linux_icon_optimized()
    
    def _set_windows_icon_optimized(self) -> None:
        """Set Windows icon using optimized approach."""
        try:
            from .icon_utils import set_window_icon, set_global_application_icon
            
            # Set Windows Application User Model ID for taskbar grouping
            try:
                import ctypes
                app_id = "VAITPResearch.VAITPAuditor.GUI.1.0"
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
                self.logger.debug(f"Set Windows App User Model ID: {app_id}")
            except Exception as e:
                self.logger.debug(f"App User Model ID failed: {e}")
            
            # Set window icon using the utility function
            window_success = set_window_icon(self.root, store_reference=True)
            if window_success:
                self.logger.info("✅ Windows window icon set successfully")
            else:
                self.logger.warning("❌ Windows window icon setting failed")
            
            # Set global application icon
            global_success = set_global_application_icon(self.root)
            if global_success:
                self.logger.debug("Windows global application icon set successfully")
            else:
                self.logger.debug("Windows global application icon setting failed")
            
            # Mark as set to prevent duplicate attempts
            self._icon_set = True
            
        except Exception as e:
            self.logger.error(f"Error in Windows icon setting: {e}")
    
    def _set_macos_icon_optimized(self) -> None:
        """Set macOS icon using persistent approach with enhanced dock icon handling."""
        try:
            import os
            import tkinter as tk
            
            # Get icon paths
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            vaitp_dir = os.path.join(base_dir, "vaitp_auditor")
            icns_path = os.path.join(vaitp_dir, "icon.icns")
            png_path = os.path.join(vaitp_dir, "icon.png")
            
            self.logger.info("Setting macOS icon with enhanced dock icon handling...")
            
            # CRITICAL: Set application name FIRST and make it persistent
            try:
                # Method 1: Set application name for dock
                self.root.tk.call('tk', 'appname', 'VAITP-Auditor')
                
                # Method 2: Set window title to match
                self.root.wm_title('VAITP-Auditor')
                self.root.title('VAITP-Auditor')
                
                # Method 3: Try to set process name (affects Activity Monitor and dock)
                try:
                    import setproctitle
                    setproctitle.setproctitle('VAITP-Auditor')
                    self.logger.debug("✅ Set process title to VAITP-Auditor")
                except ImportError:
                    # setproctitle not available, try alternative
                    try:
                        import sys
                        if hasattr(sys, 'argv') and sys.argv:
                            original_argv0 = sys.argv[0]
                            sys.argv[0] = 'VAITP-Auditor'
                            self.logger.debug("✅ Modified sys.argv[0] for process name")
                    except:
                        pass
                
                # Method 4: Set macOS-specific application properties
                try:
                    # Set bundle name environment variables
                    import os
                    os.environ['CFBundleName'] = 'VAITP-Auditor'
                    os.environ['CFBundleDisplayName'] = 'VAITP-Auditor'
                    self.logger.debug("✅ Set macOS bundle environment variables")
                except:
                    pass
                
                self.logger.info("✅ Set macOS application identity for Dock")
                    
            except Exception as e:
                self.logger.debug(f"Failed to set macOS application identity: {e}")
            
            # ENHANCED: Use ICNS with multiple persistent methods
            if os.path.exists(icns_path):
                try:
                    # Method 1: Direct iconbitmap (most reliable for dock)
                    self.root.wm_iconbitmap(icns_path)
                    self.logger.info("✅ macOS ICNS icon set with iconbitmap")
                    
                    # Method 2: Set as default for ALL future windows
                    try:
                        self.root.tk.call('wm', 'iconbitmap', '.', icns_path)
                        self.logger.debug("✅ Set ICNS as default for all windows")
                    except Exception as e:
                        self.logger.debug(f"Default ICNS setting failed: {e}")
                    
                    # Method 3: Force immediate update
                    self.root.update_idletasks()
                    
                    # Method 4: Schedule reinforcement updates to ensure persistence
                    self._schedule_macos_icon_reinforcement(icns_path)
                    
                    # Method 5: Try to force dock refresh
                    self.root.after(50, lambda: self._force_macos_dock_refresh(icns_path))
                    
                    self._icon_set = True
                    return  # Success, exit early
                    
                except Exception as e:
                    self.logger.debug(f"ICNS iconbitmap failed: {e}")
            
            # Fallback: Use PNG with enhanced methods
            if os.path.exists(png_path):
                try:
                    # Create high-quality PhotoImage for macOS
                    try:
                        from PIL import Image, ImageTk
                        img = Image.open(png_path)
                        if img.mode not in ['RGBA', 'RGB']:
                            img = img.convert('RGBA')
                        
                        # Create multiple sizes for different contexts
                        icon_64 = img.resize((64, 64), Image.Resampling.LANCZOS)
                        icon_128 = img.resize((128, 128), Image.Resampling.LANCZOS)
                        
                        photo_64 = ImageTk.PhotoImage(icon_64)
                        photo_128 = ImageTk.PhotoImage(icon_128)
                        
                        self.logger.debug("Created PIL-based icons for macOS")
                    except ImportError:
                        # Fallback to tkinter PhotoImage
                        photo_64 = tk.PhotoImage(file=png_path)
                        photo_128 = photo_64  # Same image
                        self.logger.debug("Created tkinter PhotoImage for macOS")
                    
                    # Set icon using multiple persistent methods
                    methods_tried = []
                    
                    # Method 1: wm_iconphoto with True (default for all windows)
                    try:
                        self.root.wm_iconphoto(True, photo_64, photo_128)
                        methods_tried.append("wm_iconphoto(True)")
                        self.logger.debug("✅ Set PNG with wm_iconphoto(True)")
                    except Exception as e:
                        self.logger.debug(f"wm_iconphoto(True) failed: {e}")
                    
                    # Method 2: tk.call with -default flag
                    try:
                        self.root.tk.call('wm', 'iconphoto', self.root._w, '-default', photo_64)
                        methods_tried.append("tk.call with -default")
                        self.logger.debug("✅ Set PNG with tk.call -default")
                    except Exception as e:
                        self.logger.debug(f"tk.call -default failed: {e}")
                    
                    # Method 3: Set for root window specifically
                    try:
                        self.root.tk.call('wm', 'iconphoto', '.', photo_64)
                        methods_tried.append("tk.call for root")
                        self.logger.debug("✅ Set PNG for root window")
                    except Exception as e:
                        self.logger.debug(f"tk.call for root failed: {e}")
                    
                    # Store references to prevent garbage collection
                    self.root._macos_icon_64 = photo_64
                    self.root._macos_icon_128 = photo_128
                    
                    if methods_tried:
                        self.logger.info(f"✅ macOS PNG icon set using: {', '.join(methods_tried)}")
                        self.root.update_idletasks()
                        self._icon_set = True
                        return  # Success
                    
                except Exception as e:
                    self.logger.debug(f"PNG PhotoImage methods failed: {e}")
            
            self.logger.warning("❌ All macOS icon methods failed")
            
        except Exception as e:
            self.logger.error(f"Error in macOS icon setting: {e}")
    
    def _schedule_macos_icon_reinforcement(self, icns_path: str) -> None:
        """Schedule reinforcement of macOS icon to ensure dock persistence."""
        try:
            # Schedule multiple reinforcement attempts at different intervals
            delays = [100, 300, 1000, 3000]  # milliseconds
            
            for delay in delays:
                self.root.after(delay, lambda path=icns_path: self._reinforce_macos_icon(path))
                
            self.logger.debug("✅ Scheduled macOS icon reinforcement")
                
        except Exception as e:
            self.logger.debug(f"Error scheduling macOS icon reinforcement: {e}")
    
    def _reinforce_macos_icon(self, icns_path: str) -> None:
        """Reinforce macOS icon setting (called with delays)."""
        try:
            # Re-set application name and icon
            self.root.tk.call('tk', 'appname', 'VAITP-Auditor')
            self.root.wm_iconbitmap(icns_path)
            self.logger.debug("✅ Reinforced macOS icon and app name")
        except Exception as e:
            self.logger.debug(f"Icon reinforcement failed: {e}")
    
    def _force_macos_dock_refresh(self, icns_path: str) -> None:
        """Force macOS dock to refresh the icon."""
        try:
            # Method 1: Re-set the icon
            self.root.wm_iconbitmap(icns_path)
            
            # Method 2: Force window update
            self.root.update_idletasks()
            
            # Method 3: Brief focus manipulation to trigger dock update
            self.root.lift()
            self.root.focus_force()
            
            self.logger.debug("✅ Forced macOS dock refresh")
            
        except Exception as e:
            self.logger.debug(f"Error forcing macOS dock refresh: {e}")
    
    def _ensure_main_window_icon_dominance(self) -> None:
        """Ensure main window icon remains dominant after creating child windows."""
        try:
            import platform
            
            if platform.system() == "Darwin":
                # macOS: Re-assert main window's icon dominance
                self.root.after(50, self._reassert_main_icon)
                self.root.after(200, self._reassert_main_icon)
                self.root.after(500, self._reassert_main_icon)
                
                self.logger.debug("✅ Scheduled main window icon dominance reinforcement")
                
        except Exception as e:
            self.logger.debug(f"Error ensuring main window icon dominance: {e}")
    
    def _reassert_main_icon(self) -> None:
        """Re-assert the main window's icon."""
        try:
            import os
            import platform
            
            if platform.system() == "Darwin":
                # Re-set application name
                self.root.tk.call('tk', 'appname', 'VAITP-Auditor')
                
                # Re-set icon if available
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                vaitp_dir = os.path.join(base_dir, "vaitp_auditor")
                icns_path = os.path.join(vaitp_dir, "icon.icns")
                
                if os.path.exists(icns_path):
                    self.root.wm_iconbitmap(icns_path)
                    self.logger.debug("✅ Re-asserted main window icon")
                
        except Exception as e:
            self.logger.debug(f"Error re-asserting main icon: {e}")
    
    def _set_linux_icon_optimized(self) -> None:
        """Set Linux icon using optimized approach."""
        try:
            from .icon_utils import set_window_icon, set_global_application_icon
            
            # Set global application icon
            global_success = set_global_application_icon(self.root)
            if global_success:
                self.logger.debug("Linux global application icon set successfully")
            
            # Set window icon
            window_success = set_window_icon(self.root, store_reference=True)
            if window_success:
                self.logger.info("✅ Linux window icon set successfully")
            else:
                self.logger.warning("❌ Linux window icon setting failed")
            
        except Exception as e:
            self.logger.error(f"Error in Linux icon setting: {e}")
    
    def _delayed_icon_setting(self) -> None:
        """Set icon with delay to ensure window is fully rendered (macOS fix)."""
        try:
            import platform
            if platform.system() == "Darwin":
                self.logger.debug("Delayed icon setting for macOS")
                self._set_macos_icon_optimized()
        except Exception as e:
            self.logger.debug(f"Delayed icon setting failed: {e}")
    
    def _force_macos_dock_icon_update(self) -> None:
        """Force macOS dock icon update using multiple approaches."""
        try:
            import platform
            import os
            
            if platform.system() != "Darwin":
                return
            
            self.logger.debug("Forcing macOS dock icon update")
            
            # Get icon paths
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            vaitp_dir = os.path.join(base_dir, "vaitp_auditor")
            icns_path = os.path.join(vaitp_dir, "icon.icns")
            png_path = os.path.join(vaitp_dir, "icon.png")
            
            # Method 1: Re-set application name and icon
            try:
                self.root.tk.call('tk', 'appname', 'VAITP-Auditor')
                if os.path.exists(icns_path):
                    self.root.wm_iconbitmap(icns_path)
                    self.logger.debug("✅ Forced dock icon update with ICNS")
            except Exception as e:
                self.logger.debug(f"ICNS dock update failed: {e}")
            
            # Method 2: Try to use PNG with PhotoImage
            if os.path.exists(png_path):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(png_path)
                    if img.mode not in ['RGBA', 'RGB']:
                        img = img.convert('RGBA')
                    # Create a high-quality 128x128 icon for dock
                    img_dock = img.resize((128, 128), Image.Resampling.LANCZOS)
                    icon_dock = ImageTk.PhotoImage(img_dock)
                    
                    # Set with multiple methods
                    self.root.wm_iconphoto(True, icon_dock)
                    self.root.tk.call('wm', 'iconphoto', '.', '-default', icon_dock)
                    
                    # Store reference
                    self.root._macos_dock_icon = icon_dock
                    
                    self.logger.debug("✅ Forced dock icon update with PNG")
                except Exception as e:
                    self.logger.debug(f"PNG dock update failed: {e}")
            
            # Method 3: Try to trigger a window update
            try:
                self.root.update_idletasks()
                self.root.lift()
                self.root.focus_force()
            except:
                pass
                
        except Exception as e:
            self.logger.debug(f"Error forcing macOS dock icon update: {e}")
    
    def _set_icon_at_tkinter_level(self) -> None:
        """Set icon using the most direct approach possible for each platform."""
        try:
            import platform
            import os
            import tkinter as tk
            
            system = platform.system()
            
            # Get icon paths
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            vaitp_dir = os.path.join(base_dir, "vaitp_auditor")
            icns_path = os.path.join(vaitp_dir, "icon.icns")
            png_path = os.path.join(vaitp_dir, "icon.png")
            ico_path = os.path.join(vaitp_dir, "icon.ico")
            
            self.logger.info(f"Setting {system} icon - ICNS: {os.path.exists(icns_path)}, PNG: {os.path.exists(png_path)}, ICO: {os.path.exists(ico_path)}")
            
            if system == "Darwin":
                # macOS: Aggressive approach for Dock icon
                self._set_macos_icon_aggressive(icns_path, png_path)
            elif system == "Windows":
                # Windows: Use ICO format for best results
                self._set_windows_icon_aggressive(ico_path, png_path)
            else:
                # Linux: Use PNG with PhotoImage
                self._set_linux_icon_aggressive(png_path)
            
        except Exception as e:
            self.logger.error(f"Error setting icon at Tkinter level: {e}")
    
    def _set_macos_icon_aggressive(self, icns_path: str, png_path: str) -> None:
        """Aggressively set macOS icon with multiple persistent methods."""
        try:
            import tkinter as tk
            import os
            
            # Method 1: Set application name MULTIPLE times with different approaches
            app_name_methods = [
                lambda: self.root.tk.call('tk', 'appname', 'VAITP-Auditor'),
                lambda: self.root.tk.call('::tk::mac::standardAboutPanel'),
                lambda: self.root.wm_title('VAITP-Auditor'),
                lambda: self.root.title('VAITP-Auditor')
            ]
            
            for i, method in enumerate(app_name_methods):
                try:
                    method()
                    self.logger.debug(f"✅ macOS app name method {i+1} succeeded")
                except Exception as e:
                    self.logger.debug(f"macOS app name method {i+1} failed: {e}")
            
            # Method 2: Try ICNS with multiple approaches
            if os.path.exists(icns_path):
                icns_methods = [
                    lambda: self.root.wm_iconbitmap(icns_path),
                    lambda: self.root.iconbitmap(icns_path),
                    lambda: self.root.iconbitmap(default=icns_path),
                    lambda: self.root.tk.call('wm', 'iconbitmap', '.', icns_path),
                    lambda: self.root.tk.call('wm', 'iconbitmap', self.root._w, icns_path)
                ]
                
                for i, method in enumerate(icns_methods):
                    try:
                        method()
                        self.logger.info(f"✅ macOS ICNS method {i+1} succeeded")
                        # If ICNS works, also try to make it persistent
                        self._make_macos_icon_persistent(icns_path)
                        return  # Success, exit early
                    except Exception as e:
                        self.logger.debug(f"macOS ICNS method {i+1} failed: {e}")
            
            # Method 3: PNG fallback with PhotoImage
            if os.path.exists(png_path):
                try:
                    # Try PIL first for better quality
                    try:
                        from PIL import Image, ImageTk
                        img = Image.open(png_path)
                        if img.mode not in ['RGBA', 'RGB']:
                            img = img.convert('RGBA')
                        
                        # Create multiple sizes for different contexts
                        sizes = [(32, 32), (64, 64), (128, 128)]
                        icons = []
                        
                        for size in sizes:
                            resized = img.resize(size, Image.Resampling.LANCZOS)
                            icon = ImageTk.PhotoImage(resized)
                            icons.append(icon)
                        
                        # Try to set with different methods
                        png_methods = [
                            lambda: self.root.wm_iconphoto(True, *icons),
                            lambda: self.root.iconphoto(True, icons[1]),  # 64x64
                            lambda: self.root.tk.call('wm', 'iconphoto', '.', '-default', icons[0]),
                            lambda: self.root.tk.call('wm', 'iconphoto', self.root._w, icons[1])
                        ]
                        
                        for i, method in enumerate(png_methods):
                            try:
                                method()
                                # Store references to prevent garbage collection
                                self.root._macos_icons_persistent = icons
                                self.logger.info(f"✅ macOS PNG method {i+1} succeeded")
                                return
                            except Exception as e:
                                self.logger.debug(f"macOS PNG method {i+1} failed: {e}")
                                
                    except ImportError:
                        # Fallback to tkinter PhotoImage
                        icon_photo = tk.PhotoImage(file=png_path)
                        self.root.iconphoto(True, icon_photo)
                        self.root._macos_icon_tk_persistent = icon_photo
                        self.logger.info("✅ macOS tkinter PNG succeeded")
                        return
                        
                except Exception as e:
                    self.logger.debug(f"macOS PNG fallback failed: {e}")
            
            self.logger.warning("❌ All macOS icon methods failed")
            
        except Exception as e:
            self.logger.error(f"Error in aggressive macOS icon setting: {e}")
    
    def _make_macos_icon_persistent(self, icns_path: str) -> None:
        """Make macOS icon setting more persistent with delayed reinforcement."""
        try:
            # Schedule multiple reinforcement attempts
            delays = [100, 500, 1000, 2000]  # milliseconds
            
            for delay in delays:
                self.root.after(delay, lambda: self._reinforce_macos_icon(icns_path))
                
        except Exception as e:
            self.logger.debug(f"Error setting up macOS icon persistence: {e}")
    
    def _reinforce_macos_icon(self, icns_path: str) -> None:
        """Reinforce macOS icon setting (called with delays)."""
        try:
            # Re-set application name
            self.root.tk.call('tk', 'appname', 'VAITP-Auditor')
            # Re-set icon
            self.root.wm_iconbitmap(icns_path)
            self.logger.debug("✅ Reinforced macOS icon and app name")
        except Exception as e:
            self.logger.debug(f"Icon reinforcement failed: {e}")
    
    def _set_windows_icon_aggressive(self, ico_path: str, png_path: str) -> None:
        """Aggressively set Windows icon."""
        try:
            import os
            # Try ICO first (native Windows format)
            if os.path.exists(ico_path):
                ico_methods = [
                    lambda: self.root.wm_iconbitmap(ico_path),
                    lambda: self.root.iconbitmap(ico_path),
                    lambda: self.root.iconbitmap(default=ico_path),
                    lambda: self.root.wm_iconbitmap(default=ico_path)
                ]
                
                for i, method in enumerate(ico_methods):
                    try:
                        method()
                        self.logger.info(f"✅ Windows ICO method {i+1} succeeded")
                        return
                    except Exception as e:
                        self.logger.debug(f"Windows ICO method {i+1} failed: {e}")
            
            # PNG fallback
            if os.path.exists(png_path):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(png_path)
                    if img.mode not in ['RGBA', 'RGB']:
                        img = img.convert('RGBA')
                    
                    # Windows works well with 32x32
                    icon_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
                    icon_photo = ImageTk.PhotoImage(icon_32)
                    
                    self.root.wm_iconphoto(True, icon_photo)
                    self.root._windows_icon_persistent = icon_photo
                    self.logger.info("✅ Windows PNG method succeeded")
                    
                except Exception as e:
                    self.logger.debug(f"Windows PNG method failed: {e}")
            
        except Exception as e:
            self.logger.debug(f"Error in Windows icon setting: {e}")
    
    def _set_linux_icon_aggressive(self, png_path: str) -> None:
        """Set Linux icon using PNG."""
        try:
            import os
            if os.path.exists(png_path):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(png_path)
                    if img.mode not in ['RGBA', 'RGB']:
                        img = img.convert('RGBA')
                    
                    # Linux typically works well with 48x48
                    icon_48 = img.resize((48, 48), Image.Resampling.LANCZOS)
                    icon_photo = ImageTk.PhotoImage(icon_48)
                    
                    self.root.wm_iconphoto(True, icon_photo)
                    self.root._linux_icon_persistent = icon_photo
                    self.logger.info("✅ Linux PNG method succeeded")
                    
                except Exception as e:
                    self.logger.debug(f"Linux PNG method failed: {e}")
                    
        except Exception as e:
            self.logger.debug(f"Error in Linux icon setting: {e}")
    

    def _create_ico_from_png(self, png_path: str, ico_path: str) -> bool:
        """Create Windows-compatible ICO file from PNG."""
        try:
            from PIL import Image
            
            self.logger.info(f"Creating Windows ICO: {png_path} -> {ico_path}")
            
            # Load PNG
            img = Image.open(png_path)
            
            # Ensure proper format for Windows
            if img.mode not in ['RGBA', 'RGB']:
                img = img.convert('RGBA')
            
            # Windows taskbar prefers these specific sizes
            sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)]
            
            # Save as ICO with Windows-optimized settings
            img.save(ico_path, format='ICO', sizes=sizes)
            
            # Verify the ICO was created and is valid
            if os.path.exists(ico_path) and os.path.getsize(ico_path) > 0:
                # Quick validation - check ICO header
                with open(ico_path, 'rb') as f:
                    header = f.read(4)
                    if header[:2] == b'\x00\x00' and header[2:4] == b'\x01\x00':
                        self.logger.info(f"✅ Valid ICO created: {ico_path} ({os.path.getsize(ico_path)} bytes)")
                        return True
                    else:
                        self.logger.warning(f"❌ Invalid ICO header: {header.hex()}")
                        return False
            else:
                self.logger.warning("❌ ICO file not created or empty")
                return False
                
        except ImportError:
            self.logger.warning("❌ PIL not available - cannot create ICO")
            return False
        except Exception as e:
            self.logger.error(f"❌ ICO creation failed: {e}")
            return False
    
    def _ensure_icon_is_set(self) -> None:
        """Ensure the main window icon is fully set before showing child windows."""
        try:
            import platform
            
            # Force update to ensure icon is applied
            self.root.update_idletasks()
            
            if platform.system() == "Darwin":
                # For macOS, ensure the application name and icon are persistent
                try:
                    self.root.tk.call('tk', 'appname', 'VAITP-Auditor')
                    
                    # Re-apply icon to ensure it's set
                    import os
                    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    vaitp_dir = os.path.join(base_dir, "vaitp_auditor")
                    icns_path = os.path.join(vaitp_dir, "icon.icns")
                    
                    if os.path.exists(icns_path):
                        self.root.wm_iconbitmap(icns_path)
                        self.logger.debug("✅ Main window: Icon re-applied before Setup Wizard")
                        
                except Exception as e:
                    self.logger.debug(f"Main window: Icon re-application failed: {e}")
            
            # Small delay to ensure icon is processed
            self.root.after(50, lambda: None)
            
        except Exception as e:
            self.logger.debug(f"Error ensuring icon is set: {e}")
    
    def _establish_dock_icon(self) -> None:
        """Establish the Dock icon by briefly showing the main window."""
        try:
            import platform
            
            if platform.system() == "Darwin":
                # Show main window briefly to establish Dock icon
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                self.root.update_idletasks()
                
                # Force icon setting one more time
                import os
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                vaitp_dir = os.path.join(base_dir, "vaitp_auditor")
                icns_path = os.path.join(vaitp_dir, "icon.icns")
                
                if os.path.exists(icns_path):
                    self.root.wm_iconbitmap(icns_path)
                
                # Brief delay to let macOS process the icon
                self.root.after(200, lambda: None)
                self.root.update_idletasks()
                
                self.logger.info("✅ Main window: Dock icon established")
                
        except Exception as e:
            self.logger.debug(f"Error establishing Dock icon: {e}")
    
    def _show_loading_message(self) -> None:
        """Show a loading message on the main window while establishing Dock icon."""
        try:
            # Add a temporary loading label to make the window clearly visible
            loading_label = ctk.CTkLabel(
                self.root,
                text="VAITP-Auditor\n\nInitializing...",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            loading_label.pack(expand=True)
            
            # Store reference so we can remove it later
            self.root._loading_label = loading_label
            
            # Force update
            self.root.update_idletasks()
            
        except Exception as e:
            self.logger.debug(f"Error showing loading message: {e}")
    
    def _hide_loading_message(self) -> None:
        """Hide the loading message."""
        try:
            if hasattr(self.root, '_loading_label'):
                self.root._loading_label.destroy()
                delattr(self.root, '_loading_label')
        except Exception as e:
            self.logger.debug(f"Error hiding loading message: {e}")
    
    def run(self) -> None:
        """
        Run the GUI application.
        
        This method initializes the CustomTkinter application and starts
        the main event loop.
        """
        try:
            # CRITICAL: Set process title and application identity FIRST (before any GUI operations)
            self._set_early_application_identity()
            
            # Create the main application window first
            self.root = ctk.CTk()
            
            # IMMEDIATELY set icon and application identity
            self.logger.info("🎯 STEP 1: Setting icon immediately after root creation...")
            self._set_icon_immediately()
            
            # Force a brief pause to let the icon take effect BEFORE CustomTkinter setup
            self.logger.info("🎯 STEP 1.5: Allowing icon to establish before CustomTkinter setup...")
            self.root.update_idletasks()
            self.root.update()  # Force a full update
            
            # Brief delay to let macOS process the icon
            import time
            time.sleep(0.1)  # 100ms delay
            
            # Set CustomTkinter appearance mode and color theme after window creation
            self.logger.info("🎯 STEP 2: Setting CustomTkinter appearance...")
            ctk.set_appearance_mode("system")  # Modes: system, light, dark
            ctk.set_default_color_theme("blue")  # Themes: blue, dark-blue, green
            
            # Reinforce icon setting after CustomTkinter setup
            self.logger.info("🎯 STEP 3: Reinforcing icon after CustomTkinter setup...")
            self._reinforce_icon_after_setup()
            
            # Additional aggressive reinforcement
            self.logger.info("🎯 STEP 4: Additional aggressive icon reinforcement...")
            self._aggressive_icon_reinforcement()
            
            self.root.title("VAITP-Auditor")
            self.root.geometry("800x600")
            
            # Center the main window on screen
            self.root.update_idletasks()
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width // 2) - 400  # 400 = half of 800
            y = (screen_height // 2) - 300  # 300 = half of 600
            self.root.geometry(f"800x600+{x}+{y}")
            
            # Show main window prominently to establish Dock icon FIRST
            self.root.deiconify()  # Make sure it's visible
            self.root.lift()       # Bring to front
            self.root.focus_force() # Focus to establish as main app
            
            # NUCLEAR OPTION: Set icon one final time after everything is set up
            self.logger.info("🎯 STEP 5: NUCLEAR OPTION - Final icon setting after full setup...")
            self._nuclear_icon_setting()
            
            # Make it clearly visible with a temporary message
            self._show_loading_message()
            
            # Force update and longer delay to establish Dock presence
            self.root.update_idletasks()
            
            # Longer delay to ensure macOS recognizes this as the main app
            import time
            time.sleep(0.5)  # Half second to establish Dock icon
            
            # Set up window close protocol
            self.root.protocol("WM_DELETE_WINDOW", self.handle_application_exit)
            
            # Initialize accessibility manager
            self._setup_accessibility()
            
            # Ensure icon is fully set before launching Setup Wizard
            self._ensure_icon_is_set()
            
            # CRITICAL: Show main window briefly to establish Dock icon
            self._establish_dock_icon()
            
            # Launch the Main Review Window first to establish the main app icon
            self.launch_main_review_first()
            
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
            # Hide loading message now that we're ready
            self._hide_loading_message()
            
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
    
    def launch_main_review_first(self) -> None:
        """
        Launch the Main Review Window first to establish the main app icon,
        then launch the Setup Wizard.
        """
        try:
            # Hide loading message
            self._hide_loading_message()
            
            # Instead of creating a separate MainReviewWindow, we'll use the main window
            # to establish the icon, then show the setup wizard as a dialog
            
            # Configure the main window title
            self.root.title("VAITP-Auditor - Setup")
            
            # Create a simple placeholder content to establish the window
            import customtkinter as ctk
            placeholder_frame = ctk.CTkFrame(self.root)
            placeholder_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            welcome_label = ctk.CTkLabel(
                placeholder_frame,
                text="VAITP-Auditor\n\nWelcome to the Manual Code Verification Assistant",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            welcome_label.pack(expand=True)
            
            # Store reference to clean up later
            self._placeholder_frame = placeholder_frame
            
            # Force update to establish the window and icon
            self.root.update_idletasks()
            
            # Brief delay to ensure the window and icon are established
            self.root.after(200, self._launch_setup_wizard_after_review)
            
            self.logger.info("Main window established first to set app icon")
            
        except Exception as e:
            self.logger.error(f"Error establishing main window first: {e}")
            # Fallback to original setup wizard launch
            self.launch_setup_wizard()
    
    def _launch_setup_wizard_after_review(self) -> None:
        """Launch the Setup Wizard after the main window is established."""
        try:
            # Clean up placeholder content
            if hasattr(self, '_placeholder_frame'):
                self._placeholder_frame.destroy()
                delattr(self, '_placeholder_frame')
            
            from .setup_wizard import SetupWizard
            from .models import get_default_gui_config
            
            # Create and show the setup wizard as a dialog over the main window
            gui_config = get_default_gui_config()
            self.setup_wizard = SetupWizard(
                self.root, 
                gui_config, 
                accessibility_manager=self.accessibility_manager
            )
            
            # Ensure main window icon remains dominant on macOS
            self._ensure_main_window_icon_dominance()
            
            # Set completion callback to create and configure the review window
            self.setup_wizard.set_completion_callback(self.launch_main_review)
            
            # Set cancellation callback to exit application
            self.setup_wizard.set_cancellation_callback(self.handle_application_exit)
            
            self.logger.info("Setup Wizard launched after main window established")
            
        except Exception as e:
            self.logger.error(f"Error launching Setup Wizard after main window established: {e}")
    
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
            self.root.title("VAITP-Auditor")
            
            # Re-set the application icon after window transition
            self.logger.info("Re-setting application icon after window transition")
            self._set_application_icon()
            
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
                pause_resume_callback=self._handle_pause_resume_request,
                flag_vulnerable_callback=self.session_controller.handle_flag_vulnerable_request,
                flag_not_vulnerable_callback=self.session_controller.handle_flag_not_vulnerable_request,
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
            
            # Final icon setting to ensure it persists after all window operations
            self.logger.info("Final icon setting after main review window setup")
            self._set_application_icon()
            
            # Schedule additional icon setting after window is fully rendered (macOS fix)
            self.root.after(100, self._delayed_icon_setting)
            self.root.after(500, self._delayed_icon_setting)  # Second attempt
            self.root.after(1000, self._delayed_icon_setting)  # Third attempt
            
            # For macOS, also try to force dock icon update
            import platform
            if platform.system() == "Darwin":
                self.root.after(200, self._force_macos_dock_icon_update)
                self.root.after(1500, self._force_macos_dock_icon_update)
            
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
        
        # Create Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Generate verification prompt and copy to clipboard", command=self._generate_verification_prompt, accelerator="Ctrl+G")
        
        # Create Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about_dialog)
        
        # Bind keyboard shortcuts
        self.root.bind_all("<Control-s>", lambda e: self._save_review_process())
        self.root.bind_all("<Control-o>", lambda e: self._open_review_process())
        self.root.bind_all("<Control-r>", lambda e: self._restart_review_process())
        self.root.bind_all("<Control-g>", lambda e: self._generate_verification_prompt())
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
    
    def _handle_pause_resume_request(self, is_currently_paused: bool) -> bool:
        """Handle pause/resume request from the UI.
        
        Args:
            is_currently_paused: Current pause state (True if paused, False if running)
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        try:
            if not self.session_controller:
                self.logger.warning("No session controller available for pause/resume")
                return False
            
            if is_currently_paused:
                # Currently paused, so resume
                success = self.session_controller.resume_session()
                if success:
                    self.logger.info("Session resumed successfully")
                else:
                    self.logger.warning("Failed to resume session")
                return success
            else:
                # Currently running, so pause
                success = self.session_controller.pause_session()
                if success:
                    self.logger.info("Session paused successfully")
                else:
                    self.logger.warning("Failed to pause session")
                return success
                
        except Exception as e:
            self.logger.error(f"Error handling pause/resume request: {e}")
            return False
    
    def _generate_verification_prompt(self) -> None:
        """Generate a verification prompt for AI analysis and copy to clipboard."""
        try:
            # Check if we have an active session and main review window
            if not self.main_review_window:
                import tkinter.messagebox as messagebox
                messagebox.showwarning(
                    "No Review Session",
                    "No active review session found.\n"
                    "Please start a review session first using the Setup Wizard."
                )
                return
            
            # Get the current code from all three panels
            input_code = self.main_review_window.code_panels_frame.input_textbox.get("1.0", "end-1c").strip()
            expected_code = self.main_review_window.code_panels_frame.expected_textbox.get("1.0", "end-1c").strip()
            generated_code = self.main_review_window.code_panels_frame.generated_textbox.get("1.0", "end-1c").strip()
            
            # Check if we have actual code content (not just placeholder text)
            placeholder_indicators = ["# No code loaded", "# Use the Setup Wizard", "# No expected code available", 
                                    "# No generated code available", "# No input code available"]
            
            def is_placeholder(code_text):
                return any(indicator in code_text for indicator in placeholder_indicators)
            
            if is_placeholder(input_code) and is_placeholder(expected_code) and is_placeholder(generated_code):
                import tkinter.messagebox as messagebox
                messagebox.showwarning(
                    "No Code Available",
                    "No code is currently loaded for analysis.\n"
                    "Please load a code pair first using the Setup Wizard."
                )
                return
            
            # Generate the verification prompt
            prompt = self._create_verification_prompt(input_code, expected_code, generated_code)
            
            # Copy to clipboard
            self._copy_to_clipboard(prompt)
            
            # Show success message
            import tkinter.messagebox as messagebox
            messagebox.showinfo(
                "Verification Prompt Generated",
                "The verification prompt has been generated and copied to your clipboard.\n"
                "You can now paste it into any LLM system for analysis."
            )
            
        except Exception as e:
            self.logger.error(f"Error generating verification prompt: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "Error Generating Prompt",
                f"An error occurred while generating the verification prompt:\n{str(e)}"
            )
    
    def _create_verification_prompt(self, input_code: str, expected_code: str, generated_code: str) -> str:
        """Create the verification prompt text.
        
        Args:
            input_code: The original input code
            expected_code: The expected/reference code
            generated_code: The generated code to analyze
            
        Returns:
            Formatted verification prompt string
        """
        prompt = """Please analyze the following three code snippets for security vulnerabilities:

## Task
I need you to evaluate each of the three code snippets below and determine:
1. Whether the INPUT CODE contains any security vulnerabilities
2. Whether the EXPECTED CODE contains any security vulnerabilities  
3. Whether the GENERATED CODE contains any security vulnerabilities

For each code snippet, please provide:
- A clear YES/NO answer about vulnerability presence
- Detailed explanation of any vulnerabilities found
- Severity assessment (Critical/High/Medium/Low) if vulnerabilities exist
- Specific recommendations for fixes if applicable

## INPUT CODE (Original):
```python
{input_code}
```

## EXPECTED CODE (Reference):
```python
{expected_code}
```

## GENERATED CODE (To Review):
```python
{generated_code}
```

## Analysis Format
Please structure your response as follows:

### INPUT CODE Analysis:
**Vulnerable:** [YES/NO]
**Explanation:** [Your detailed analysis]
**Severity:** [If vulnerable: Critical/High/Medium/Low]
**Recommendations:** [If vulnerable: specific fixes]

### EXPECTED CODE Analysis:
**Vulnerable:** [YES/NO]
**Explanation:** [Your detailed analysis]
**Severity:** [If vulnerable: Critical/High/Medium/Low]
**Recommendations:** [If vulnerable: specific fixes]

### GENERATED CODE Analysis:
**Vulnerable:** [YES/NO]
**Explanation:** [Your detailed analysis]
**Severity:** [If vulnerable: Critical/High/Medium/Low]
**Recommendations:** [If vulnerable: specific fixes]

### Summary
Please provide a brief summary comparing the three code snippets and any overall observations about the security improvements or regressions between them.
""".format(
            input_code=input_code if input_code else "# No input code provided",
            expected_code=expected_code if expected_code else "# No expected code provided", 
            generated_code=generated_code if generated_code else "# No generated code provided"
        )
        
        return prompt
    
    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to system clipboard.
        
        Args:
            text: Text to copy to clipboard
        """
        try:
            # Clear clipboard and set new content
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()  # Ensure clipboard is updated
        except Exception as e:
            # Fallback: try using existing root window if available
            try:
                if self.root:
                    # Use the existing root window instead of creating a new one
                    self.root.clipboard_clear()
                    self.root.clipboard_append(text)
                    self.root.update()
                else:
                    # If no root window available, skip clipboard operation
                    raise Exception("No GUI window available for clipboard operation")
            except Exception as fallback_error:
                raise Exception(f"Failed to copy to clipboard: {str(e)}. Fallback also failed: {str(fallback_error)}")
    
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
    # Immediately suppress console output on macOS to prevent Python version window
    _suppress_console_output_immediately()

    try:
        # Use provided args or parse command-line arguments
        if args is None:
            parser = create_argument_parser()
            args = parser.parse_args()
        
        # Setup logging
        log_level = "DEBUG" if getattr(args, 'debug', False) else "INFO"
        # For GUI applications, disable console output by default to prevent console windows
        # Only enable console output in debug mode
        console_output = getattr(args, 'debug', False)
        setup_logging(
            level=log_level,
            console_output=console_output,
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





def _suppress_console_output_immediately():
    """Immediately suppress console output to prevent Python version windows."""
    try:
        import sys
        import os
        import platform
        
        # Only suppress on macOS and only if not in debug mode
        if platform.system() == "Darwin" and not any('debug' in arg.lower() for arg in sys.argv):
            # Redirect stdout and stderr to /dev/null to prevent any console output
            # that might trigger Terminal.app or console windows
            try:
                devnull = open(os.devnull, 'w')
                sys.stdout = devnull
                sys.stderr = devnull
            except Exception:
                pass
    except Exception:
        pass


if __name__ == "__main__":
    main()