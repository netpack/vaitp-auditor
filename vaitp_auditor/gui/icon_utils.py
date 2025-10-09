"""
Icon utilities for VAITP-Auditor GUI.

This module provides utilities for loading and setting application icons
across different GUI components.
"""

import os
import logging
from typing import List, Optional, Union
import tkinter as tk

logger = logging.getLogger(__name__)


def get_icon_path() -> str:
    """Get the path to the application icon file.
    
    Returns:
        str: Path to the icon.png file
    """
    import platform
    
    # Get the base directory (vaitp_auditor)
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    # Try platform-specific icon formats first
    system = platform.system()
    if system == "Windows":
        # Try ICO format first on Windows
        ico_path = os.path.join(base_dir, "icon.ico")
        if os.path.exists(ico_path):
            return ico_path
    elif system == "Darwin":
        # Try ICNS format first on macOS
        icns_path = os.path.join(base_dir, "icon.icns")
        if os.path.exists(icns_path):
            return icns_path
    
    # Fallback to PNG
    png_path = os.path.join(base_dir, "icon.png")
    if os.path.exists(png_path):
        return png_path
    
    # Try GUI assets directory as fallback
    gui_icon_path = os.path.join(base_dir, "gui", "assets", "icons", "app_icon.png")
    if os.path.exists(gui_icon_path):
        return gui_icon_path
    
    # Final fallback - return PNG path even if it doesn't exist
    return png_path


def set_global_application_icon(root_window) -> bool:
    """Set the global application icon (affects Dock on macOS).
    
    Args:
        root_window: The main Tk root window
        
    Returns:
        bool: True if global icon was set successfully
    """
    import platform
    import tkinter as tk
    
    try:
        system = platform.system()
        
        if system == "Darwin":
            # macOS: Set application name and global icon
            try:
                # Set application name
                root_window.tk.call('tk', 'appname', 'VAITP-Auditor')
                logger.debug("Set application name to VAITP-Auditor")
                
                # Try ICNS format first (native macOS format)
                base_dir = os.path.dirname(os.path.dirname(__file__))
                icns_path = os.path.join(base_dir, "icon.icns")
                
                if os.path.exists(icns_path):
                    try:
                        # Use iconbitmap for ICNS files on macOS
                        root_window.wm_iconbitmap(icns_path)
                        logger.debug("Set macOS global icon using ICNS format")
                        return True
                    except Exception as e:
                        logger.debug(f"ICNS method failed: {e}")
                
                # Fallback to PNG with PhotoImage
                png_path = os.path.join(base_dir, "icon.png")
                if os.path.exists(png_path):
                    try:
                        # Create a properly sized icon for macOS
                        icon_photo = tk.PhotoImage(file=png_path)
                        
                        # Try both methods for maximum compatibility
                        try:
                            root_window.wm_iconphoto(True, icon_photo)
                            logger.debug("Set macOS global icon using wm_iconphoto")
                        except:
                            root_window.tk.call('wm', 'iconphoto', root_window._w, '-default', icon_photo)
                            logger.debug("Set macOS global icon using tk.call")
                        
                        # Store reference to prevent garbage collection
                        root_window._global_app_icon = icon_photo
                        return True
                    except Exception as e:
                        logger.debug(f"PNG PhotoImage method failed: {e}")
                else:
                    logger.debug("PNG file not found for global icon")
                
                return False
                    
            except Exception as e:
                logger.debug(f"Error setting macOS global icon: {e}")
                return False
        
        elif system == "Windows":
            # Windows: Try to set application icon with multiple methods
            try:
                base_dir = os.path.dirname(os.path.dirname(__file__))
                ico_path = os.path.join(base_dir, "icon.ico")
                
                # Ensure ICO file exists
                if not os.path.exists(ico_path) or not validate_icon_file(ico_path):
                    created_ico = create_ico_file()
                    if created_ico:
                        ico_path = created_ico
                
                if os.path.exists(ico_path):
                    # Method 1: Set with absolute path
                    try:
                        abs_ico_path = os.path.abspath(ico_path)
                        root_window.iconbitmap(abs_ico_path)
                        logger.debug(f"Set global Windows application icon: {abs_ico_path}")
                        return True
                    except Exception as e:
                        logger.debug(f"Absolute path method failed: {e}")
                    
                    # Method 2: Set with default parameter
                    try:
                        root_window.iconbitmap(default=ico_path)
                        logger.debug(f"Set global Windows application icon (default): {ico_path}")
                        return True
                    except Exception as e:
                        logger.debug(f"Default parameter method failed: {e}")
                
                # Method 3: Try PNG fallback
                png_path = os.path.join(base_dir, "icon.png")
                if os.path.exists(png_path):
                    try:
                        import tkinter as tk
                        icon_photo = tk.PhotoImage(file=png_path)
                        root_window.wm_iconphoto(True, icon_photo)
                        root_window._global_app_icon_png = icon_photo
                        logger.debug("Set global Windows application icon using PNG")
                        return True
                    except Exception as e:
                        logger.debug(f"PNG fallback method failed: {e}")
                
            except Exception as e:
                logger.debug(f"Error setting Windows global icon: {e}")
                return False
        
        # For other platforms, just return True (no global icon needed)
        return True
        
    except Exception as e:
        logger.debug(f"Error setting global application icon: {e}")
        return False


def initialize_platform_icons() -> bool:
    """Initialize platform-specific icon files if they don't exist.
    
    Returns:
        bool: True if icons were initialized successfully
    """
    import platform
    
    try:
        system = platform.system()
        
        if system == "Windows":
            # Ensure ICO file exists for Windows
            base_dir = os.path.dirname(os.path.dirname(__file__))
            ico_path = os.path.join(base_dir, "icon.ico")
            
            if os.path.exists(ico_path):
                logger.debug(f"Windows ICO icon already exists: {ico_path}")
                return True
            else:
                # Try to create ICO file
                created_ico = create_ico_file()
                if created_ico:
                    logger.debug("Windows ICO icon created")
                    return True
                else:
                    # Fallback: ensure PNG exists
                    png_path = os.path.join(base_dir, "icon.png")
                    if os.path.exists(png_path):
                        logger.debug("Windows: Using PNG fallback")
                        return True
                    
        elif system == "Darwin":
            # Ensure ICNS file exists for macOS
            base_dir = os.path.dirname(os.path.dirname(__file__))
            icns_path = os.path.join(base_dir, "icon.icns")
            
            if os.path.exists(icns_path):
                logger.debug(f"macOS ICNS icon already exists: {icns_path}")
                return True
            else:
                # Try to create ICNS file
                created_icns = create_icns_file()
                if created_icns:
                    logger.debug("macOS ICNS icon created")
                    return True
        
        # For Linux or if platform-specific creation failed, ensure PNG exists
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            logger.debug(f"Using existing icon: {icon_path}")
            return True
        
        logger.debug("No suitable icon found or created")
        return False
        
    except Exception as e:
        logger.debug(f"Error initializing platform icons: {e}")
        return False


def load_application_icons() -> Optional[List]:
    """Load application icons with minimal processing for best quality.
    
    Returns:
        List of PhotoImage objects or None if loading fails
    """
    try:
        # Initialize platform-specific icons if needed
        initialize_platform_icons()
        
        from PIL import Image, ImageTk
        
        icon_path = get_icon_path()
        if not os.path.exists(icon_path):
            logger.debug(f"Icon file not found at: {icon_path}")
            return None
        
        # Check if we have a Tkinter root window - avoid creating temporary windows
        # PIL/ImageTk can work without a root window for basic operations
        
        # Load the original image with minimal processing
        icon_image = Image.open(icon_path)
        
        # Only convert to RGBA if absolutely necessary
        if icon_image.mode not in ['RGBA', 'RGB']:
            icon_image = icon_image.convert('RGBA')
        
        # Create just one high-quality icon at 64x64 (good for most title bars)
        # Use the highest quality resampling available
        icon_64 = icon_image.resize((64, 64), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        icon_photo = ImageTk.PhotoImage(icon_64)
        
        logger.debug("Loaded single high-quality 64x64 icon")
        return [icon_photo]
        
    except ImportError as e:
        logger.debug(f"PIL not available for icon loading: {e}")
        return None
    except Exception as e:
        logger.debug(f"Error loading application icons: {e}")
        return None


def create_optimized_icon_variants() -> bool:
    """Create optimized icon variants for better quality at different sizes.
    
    Returns:
        bool: True if variants were created successfully
    """
    try:
        from PIL import Image, ImageFilter, ImageEnhance
        
        icon_path = get_icon_path()
        if not os.path.exists(icon_path):
            return False
        
        # Load the original image
        original = Image.open(icon_path)
        
        # Convert to RGBA if not already
        if original.mode != 'RGBA':
            original = original.convert('RGBA')
        
        # Create a high-quality 512x512 master icon for scaling
        master_path = icon_path.replace('.png', '_master.png')
        
        # Check if master already exists and is newer
        if os.path.exists(master_path):
            orig_mtime = os.path.getmtime(icon_path)
            master_mtime = os.path.getmtime(master_path)
            if master_mtime > orig_mtime:
                logger.debug("Master icon already up to date")
                return True
        
        # Create optimized master icon
        # First, crop to square if needed (use the smaller dimension)
        width, height = original.size
        size = min(width, height)
        
        # Calculate crop box to center the image
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size
        
        # Crop to square
        square_icon = original.crop((left, top, right, bottom))
        
        # Resize to 512x512 with high quality
        master_icon = square_icon.resize((512, 512), Image.Resampling.LANCZOS)
        
        # Apply subtle enhancement for better clarity
        enhancer = ImageEnhance.Sharpness(master_icon)
        master_icon = enhancer.enhance(1.1)  # Slight sharpening
        
        # Save the master icon
        master_icon.save(master_path, 'PNG', optimize=True)
        
        logger.debug(f"Created optimized master icon: {master_path}")
        return True
        
    except Exception as e:
        logger.debug(f"Error creating optimized icon variants: {e}")
        return False


def create_icns_file() -> Optional[str]:
    """Create a high-quality ICNS file for macOS compatibility.
    
    Returns:
        str: Path to the created ICNS file or None if creation fails
    """
    try:
        from PIL import Image
        import platform
        
        # Only create ICNS on macOS
        if platform.system() != "Darwin":
            return None
        
        icon_path = get_icon_path()
        if not os.path.exists(icon_path):
            return None
        
        # Create ICNS file path
        icns_path = icon_path.replace('.png', '.icns')
        
        # Check if ICNS already exists and is newer than PNG
        if os.path.exists(icns_path):
            png_mtime = os.path.getmtime(icon_path)
            icns_mtime = os.path.getmtime(icns_path)
            if icns_mtime > png_mtime:
                return icns_path
        
        # Try to use the optimized master icon if available
        master_path = icon_path.replace('.png', '_master.png')
        if os.path.exists(master_path):
            icon_image = Image.open(master_path)
        else:
            # Load the original image
            icon_image = Image.open(icon_path)
            
            # Convert to RGBA if not already
            if icon_image.mode != 'RGBA':
                icon_image = icon_image.convert('RGBA')
        
        # Create ICNS with standard macOS icon sizes
        # macOS expects specific sizes: 16, 32, 64, 128, 256, 512, 1024
        icns_sizes = [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512)]
        
        # Save as ICNS
        icon_image.save(icns_path, format='ICNS', sizes=icns_sizes)
        
        logger.debug(f"Created high-quality ICNS file: {icns_path}")
        return icns_path
        
    except Exception as e:
        logger.debug(f"Error creating ICNS file: {e}")
        return None


def validate_icon_file(icon_path: str) -> bool:
    """Validate that an icon file is readable and not corrupted.
    
    Args:
        icon_path: Path to the icon file
        
    Returns:
        bool: True if icon is valid, False otherwise
    """
    try:
        if not os.path.exists(icon_path):
            return False
        
        # Check file size (should be > 0)
        if os.path.getsize(icon_path) == 0:
            return False
        
        # Try to open with PIL if available
        try:
            from PIL import Image
            img = Image.open(icon_path)
            # Try to access basic properties
            _ = img.size
            _ = img.mode
            return True
        except ImportError:
            # PIL not available, just check if file exists and has size
            return True
        except Exception:
            return False
            
    except Exception:
        return False


def create_ico_file() -> Optional[str]:
    """Create a high-quality ICO file from the PNG icon for better Windows compatibility.
    
    Returns:
        str: Path to the created ICO file or None if creation fails
    """
    try:
        # Find source PNG icon
        base_dir = os.path.dirname(os.path.dirname(__file__))
        png_sources = [
            os.path.join(base_dir, "icon.png"),
            os.path.join(base_dir, "gui", "assets", "icons", "app_icon.png"),
            os.path.join(base_dir, "icon_master.png")
        ]
        
        source_path = None
        for path in png_sources:
            if os.path.exists(path) and validate_icon_file(path):
                source_path = path
                break
        
        if not source_path:
            logger.debug("No valid PNG source found for ICO creation")
            return None
        
        # Create ICO file path in the base directory
        ico_path = os.path.join(base_dir, "icon.ico")
        
        # Always try to create/recreate ICO for better reliability
        logger.debug(f"Creating ICO file from: {source_path}")
        
        # Try to create ICO using PIL
        try:
            from PIL import Image
            
            # Load the source image
            icon_image = Image.open(source_path)
            
            # Convert to RGBA if not already
            if icon_image.mode != 'RGBA':
                icon_image = icon_image.convert('RGBA')
            
            # Create Windows-optimized sizes (focus on commonly used sizes)
            ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)]
            
            # Save as ICO with multiple sizes
            icon_image.save(ico_path, format='ICO', sizes=ico_sizes)
            
            # Validate the created file
            if os.path.exists(ico_path) and os.path.getsize(ico_path) > 0:
                logger.debug(f"Successfully created ICO file: {ico_path} ({os.path.getsize(ico_path)} bytes)")
                return ico_path
            else:
                logger.debug("ICO file creation failed - file missing or empty")
                return None
                
        except ImportError:
            logger.debug("PIL not available for ICO creation")
            # Check if ICO already exists
            if os.path.exists(ico_path) and os.path.getsize(ico_path) > 0:
                logger.debug(f"Using existing ICO file: {ico_path}")
                return ico_path
            return None
        except Exception as e:
            logger.debug(f"PIL ICO creation failed: {e}")
            # Check if ICO already exists as fallback
            if os.path.exists(ico_path) and os.path.getsize(ico_path) > 0:
                logger.debug(f"Using existing ICO file after creation failure: {ico_path}")
                return ico_path
            return None
        
    except Exception as e:
        logger.debug(f"Error in ICO file creation: {e}")
        return None


def create_single_icon_for_macos() -> Optional:
    """Create a single optimized icon specifically for macOS title bars.
    
    Returns:
        PhotoImage object or None if creation fails
    """
    try:
        from PIL import Image, ImageTk
        
        icon_path = get_icon_path()
        if not os.path.exists(icon_path):
            return None
        
        # Load the master icon if available, otherwise original
        master_path = icon_path.replace('.png', '_master.png')
        if os.path.exists(master_path):
            icon_image = Image.open(master_path)
        else:
            icon_image = Image.open(icon_path)
            if icon_image.mode != 'RGBA':
                icon_image = icon_image.convert('RGBA')
        
        # Create a 64x64 icon specifically for macOS (good balance of quality and compatibility)
        macos_icon = icon_image.resize((64, 64), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(macos_icon)
        
        logger.debug("Created single optimized icon for macOS")
        return photo
        
    except Exception as e:
        logger.debug(f"Error creating single macOS icon: {e}")
        return None


def clear_default_icon(window: Union[tk.Tk, tk.Toplevel]) -> None:
    """Clear any default icon that might be cached.
    
    Args:
        window: The Tkinter window to clear icons from
    """
    try:
        # Try to clear any existing icon bitmap
        window.wm_iconbitmap("")
    except:
        pass
    
    # Note: Don't clear iconphoto with empty string as it causes errors
    # The new icon will override the old one anyway


def set_window_icon(window: Union[tk.Tk, tk.Toplevel], store_reference: bool = True) -> bool:
    """Set the icon for a Tkinter window with cross-platform compatibility.
    
    Args:
        window: The Tkinter window to set the icon for
        store_reference: Whether to store icon reference in window to prevent GC
        
    Returns:
        bool: True if icon was set successfully, False otherwise
    """
    import platform
    
    try:
        system = platform.system()
        icon_path = get_icon_path()
        
        if not os.path.exists(icon_path):
            logger.debug(f"Icon file not found at: {icon_path}")
            return False
        
        # Platform-specific icon setting
        if system == "Windows":
            return _set_windows_icon(window, icon_path, store_reference)
        elif system == "Darwin":
            return _set_macos_icon(window, icon_path, store_reference)
        else:  # Linux and others
            return _set_linux_icon(window, icon_path, store_reference)
            
    except Exception as e:
        logger.debug(f"Error setting window icon: {e}")
        return False


def _set_windows_icon(window: Union[tk.Tk, tk.Toplevel], icon_path: str, store_reference: bool) -> bool:
    """Set icon on Windows with enhanced ICO format handling."""
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # First, try to use existing ICO file
        ico_path = os.path.join(base_dir, "icon.ico")
        
        # If ICO doesn't exist or is invalid, create it immediately
        if not os.path.exists(ico_path) or not validate_icon_file(ico_path):
            logger.debug("Creating ICO file for Windows")
            # Try to create ICO from PNG
            png_path = os.path.join(base_dir, "icon.png")
            if os.path.exists(png_path):
                try:
                    # Try PIL first
                    from PIL import Image
                    img = Image.open(png_path)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    # Create ICO with Windows standard sizes
                    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)]
                    img.save(ico_path, format='ICO', sizes=sizes)
                    logger.debug(f"Created ICO file: {ico_path}")
                except ImportError:
                    logger.debug("PIL not available, cannot create ICO")
                except Exception as e:
                    logger.debug(f"Failed to create ICO: {e}")
        
        # Method 1: Try ICO with multiple approaches
        if os.path.exists(ico_path):
            # Try absolute path first
            abs_ico_path = os.path.abspath(ico_path)
            
            for method_name, method_call in [
                ("absolute path", lambda: window.wm_iconbitmap(abs_ico_path)),
                ("default parameter", lambda: window.wm_iconbitmap(default=abs_ico_path)),
                ("relative path", lambda: window.wm_iconbitmap(ico_path)),
                ("bitmap parameter", lambda: window.wm_iconbitmap(bitmap=ico_path))
            ]:
                try:
                    method_call()
                    logger.debug(f"Windows icon set using ICO ({method_name}): {ico_path}")
                    return True
                except Exception as e:
                    logger.debug(f"ICO {method_name} failed: {e}")
                    continue
        
        # Method 2: Try PNG with PhotoImage as fallback
        png_paths = [
            os.path.join(base_dir, "icon.png"),
            os.path.join(base_dir, "gui", "assets", "icons", "app_icon.png")
        ]
        
        for png_path in png_paths:
            if os.path.exists(png_path) and validate_icon_file(png_path):
                try:
                    result = _set_photoimage_icon(window, png_path, store_reference)
                    if result:
                        logger.debug(f"Windows icon set using PNG PhotoImage: {png_path}")
                        return True
                except Exception as e:
                    logger.debug(f"Failed to set PNG icon {png_path}: {e}")
                    continue
        
        # Method 3: Try PIL method if available
        try:
            from PIL import Image, ImageTk
            png_path = os.path.join(base_dir, "icon.png")
            if os.path.exists(png_path):
                img = Image.open(png_path)
                # Create a smaller icon for better Windows compatibility
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                icon_pil = ImageTk.PhotoImage(img)
                window.wm_iconphoto(True, icon_pil)
                
                if store_reference:
                    window._vaitp_icon_pil = icon_pil
                
                logger.debug("Windows icon set using PIL method")
                return True
        except ImportError:
            logger.debug("PIL not available for Windows icon")
        except Exception as e:
            logger.debug(f"PIL method failed: {e}")
        
        logger.debug("All Windows icon methods failed")
        return False
        
    except Exception as e:
        logger.debug(f"Error setting Windows icon: {e}")
        return False


def _set_macos_icon(window: Union[tk.Tk, tk.Toplevel], icon_path: str, store_reference: bool) -> bool:
    """Set icon on macOS with ICNS format preference."""
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Try ICNS format first (native macOS format)
        icns_path = os.path.join(base_dir, "icon.icns")
        if os.path.exists(icns_path):
            try:
                window.wm_iconbitmap(icns_path)
                logger.debug("macOS icon set using ICNS format")
                return True
            except Exception as e:
                logger.debug(f"Failed to set ICNS icon: {e}")
        
        # Try to create ICNS if it doesn't exist
        if not os.path.exists(icns_path):
            created_icns = create_icns_file()
            if created_icns and os.path.exists(created_icns):
                try:
                    window.wm_iconbitmap(created_icns)
                    logger.debug("macOS icon set using newly created ICNS")
                    return True
                except Exception as e:
                    logger.debug(f"Failed to set newly created ICNS icon: {e}")
        
        # Fallback to PhotoImage method with PNG
        png_path = os.path.join(base_dir, "icon.png")
        if os.path.exists(png_path):
            return _set_photoimage_icon(window, png_path, store_reference)
        
        # Try the original icon_path as final fallback
        if icon_path != png_path and os.path.exists(icon_path):
            return _set_photoimage_icon(window, icon_path, store_reference)
        
        logger.debug("No suitable icon found for macOS")
        return False
        
    except Exception as e:
        logger.debug(f"Error setting macOS icon: {e}")
        return False


def _set_linux_icon(window: Union[tk.Tk, tk.Toplevel], icon_path: str, store_reference: bool) -> bool:
    """Set icon on Linux using PhotoImage method."""
    try:
        return _set_photoimage_icon(window, icon_path, store_reference)
    except Exception as e:
        logger.debug(f"Error setting Linux icon: {e}")
        return False


def _set_photoimage_icon(window: Union[tk.Tk, tk.Toplevel], icon_path: str, store_reference: bool) -> bool:
    """Set icon using PhotoImage method (cross-platform fallback)."""
    try:
        import tkinter as tk
        import platform
        
        # Try PIL first for better quality and cross-platform compatibility
        try:
            from PIL import Image, ImageTk
            
            # Load and process icon
            icon_image = Image.open(icon_path)
            if icon_image.mode not in ['RGBA', 'RGB']:
                icon_image = icon_image.convert('RGBA')
            
            # Create appropriately sized icon based on platform
            if platform.system() == "Darwin":
                # macOS prefers 64x64 for window icons
                icon_resized = icon_image.resize((64, 64), Image.Resampling.LANCZOS)
            else:
                # Windows and Linux work well with 32x32
                icon_resized = icon_image.resize((32, 32), Image.Resampling.LANCZOS)
            
            icon_photo = ImageTk.PhotoImage(icon_resized)
            
            # Set the icon
            window.wm_iconphoto(True, icon_photo)
            
            # Store reference to prevent garbage collection
            if store_reference:
                window._vaitp_icon = icon_photo
            
            logger.debug(f"Icon set using PIL PhotoImage method ({icon_resized.size})")
            return True
            
        except ImportError:
            logger.debug("PIL not available, trying tkinter PhotoImage")
        except Exception as e:
            logger.debug(f"PIL PhotoImage failed: {e}")
        
        # Fallback to tkinter PhotoImage (works without PIL for PNG)
        if icon_path.endswith('.png'):
            try:
                icon_photo = tk.PhotoImage(file=icon_path)
                window.wm_iconphoto(True, icon_photo)
                
                if store_reference:
                    window._vaitp_icon = icon_photo
                
                logger.debug("Icon set using tkinter PhotoImage method")
                return True
            except tk.TclError as e:
                logger.debug(f"Tkinter PhotoImage failed: {e}")
                # Try to find a smaller PNG or create one
                return _try_alternative_png_icon(window, store_reference)
        
        logger.debug("No suitable PhotoImage method worked")
        return False
                
    except Exception as e:
        logger.debug(f"Error setting PhotoImage icon: {e}")
        return False


def _try_alternative_png_icon(window: Union[tk.Tk, tk.Toplevel], store_reference: bool) -> bool:
    """Try to use alternative PNG icons when the main one fails."""
    try:
        import tkinter as tk
        
        # Try the GUI assets icon
        base_dir = os.path.dirname(os.path.dirname(__file__))
        alternative_paths = [
            os.path.join(base_dir, "gui", "assets", "icons", "app_icon.png"),
            os.path.join(base_dir, "gui", "assets", "icons", "test_icon.png")
        ]
        
        for alt_path in alternative_paths:
            if os.path.exists(alt_path):
                try:
                    icon_photo = tk.PhotoImage(file=alt_path)
                    window.wm_iconphoto(True, icon_photo)
                    
                    if store_reference:
                        window._vaitp_icon = icon_photo
                    
                    logger.debug(f"Icon set using alternative PNG: {alt_path}")
                    return True
                except tk.TclError:
                    continue
        
        logger.debug("No suitable alternative PNG icons found")
        return False
        
    except Exception as e:
        logger.debug(f"Error trying alternative PNG icons: {e}")
        return False


def get_verdict_icon(verdict_id: str) -> str:
    """Get the Unicode icon for a verdict.
    
    Args:
        verdict_id: The verdict identifier
        
    Returns:
        str: Unicode icon character
    """
    icons = {
        # Main verdict types
        "SUCCESS": "✅",
        "FAILURE_NO_CHANGE": "❌",
        "INVALID_CODE": "⚠️",
        "WRONG_VULNERABILITY": "🔄",
        "PARTIAL_SUCCESS": "⚡",
        
        # Legacy/alternative names
        "correct": "✅",
        "incorrect": "❌", 
        "partial": "⚡",
        "unclear": "❓",
        "skip": "⏭️",
        "flag": "🚩"
    }
    return icons.get(verdict_id, "•")


def get_button_icon(button_type: str) -> str:
    """Get the Unicode icon for a button type.
    
    Args:
        button_type: The button type identifier
        
    Returns:
        str: Unicode icon character
    """
    icons = {
        # Navigation
        "next": "➡️",
        "back": "⬅️",
        "cancel": "❌",
        "start": "🚀",
        "resume": "▶️",
        "finish": "🏁",
        
        # File operations
        "browse": "📁",
        "delete": "🗑️",
        "save": "💾",
        "open": "📂",
        "export": "📤",
        "import": "📥",
        
        # Actions
        "ok": "✅",
        "close": "✅",
        "apply": "✅",
        "reset": "🔄",
        "test": "🧪",
        "undo": "↶️",
        "quit": "⏹️",
        "stop": "🛑",
        "pause": "⏸️",
        "play": "▶️",
        
        # Settings and configuration
        "settings": "⚙️",
        "config": "🔧",
        "preferences": "🎛️",
        "options": "⚙️",
        
        # Data and database
        "database": "🗄️",
        "table": "📊",
        "excel": "📊",
        "csv": "📋",
        "folders": "📁",
        
        # Status and feedback
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "help": "❓",
        
        # Font sizes
        "font_small": "🔍",
        "font_normal": "📄",
        "font_large": "🔍",
        "font_xlarge": "🔍",
        
        # Numbers
        "1": "1️⃣",
        "2": "2️⃣", 
        "3": "3️⃣",
        "4": "4️⃣",
        "5": "5️⃣",
        
        # Accessibility
        "accessibility": "♿",
        "keyboard": "⌨️",
        "audio": "🔊",
        "visual": "👁️",
        
        # Review specific
        "review": "📝",
        "compare": "🔍",
        "analyze": "🔬",
        "validate": "✔️"
    }
    return icons.get(button_type, "")


def add_icon_to_text(text: str, icon_type: str, position: str = "left") -> str:
    """Add an icon to button text.
    
    Args:
        text: Original button text
        icon_type: Type of icon to add (from get_button_icon)
        position: Position of icon ("left" or "right")
        
    Returns:
        str: Text with icon added
    """
    icon = get_button_icon(icon_type)
    if not icon:
        return text
    
    if position == "right":
        return f"{text} {icon}"
    else:
        return f"{icon} {text}"


def enhance_button_with_icon(button, icon_type: str, position: str = "left") -> None:
    """Enhance an existing button with an icon.
    
    Args:
        button: The CTkButton to enhance
        icon_type: Type of icon to add
        position: Position of icon ("left" or "right")
    """
    try:
        current_text = button.cget("text")
        # Remove existing icons if any (simple cleanup)
        import re
        clean_text = re.sub(r'^[^\w\s]+\s*', '', current_text)  # Remove leading icons
        clean_text = re.sub(r'\s*[^\w\s]+$', '', clean_text)    # Remove trailing icons
        
        new_text = add_icon_to_text(clean_text, icon_type, position)
        button.configure(text=new_text)
    except Exception as e:
        logger.debug(f"Error enhancing button with icon: {e}")


def get_themed_button_config(button_type: str) -> dict:
    """Get themed configuration for a button including icon and colors.
    
    Args:
        button_type: Type of button
        
    Returns:
        dict: Configuration dictionary with text, colors, etc.
    """
    configs = {
        "success": {
            "fg_color": "#2d8f47",
            "hover_color": "#1e6b35",
            "text_color": "white"
        },
        "error": {
            "fg_color": "#d32f2f", 
            "hover_color": "#b71c1c",
            "text_color": "white"
        },
        "warning": {
            "fg_color": "#f57c00",
            "hover_color": "#e65100", 
            "text_color": "white"
        },
        "info": {
            "fg_color": "#1976d2",
            "hover_color": "#0d47a1",
            "text_color": "white"
        },
        "primary": {
            "fg_color": "#6366f1",
            "hover_color": "#4f46e5",
            "text_color": "white"
        },
        "secondary": {
            "fg_color": "#6c757d",
            "hover_color": "#5a6268",
            "text_color": "white"
        },
        "danger": {
            "fg_color": "#dc3545",
            "hover_color": "#c82333",
            "text_color": "white"
        }
    }
    
    return configs.get(button_type, {})