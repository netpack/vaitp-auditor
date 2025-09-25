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
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")


def load_application_icons() -> Optional[List]:
    """Load application icons with minimal processing for best quality.
    
    Returns:
        List of PhotoImage objects or None if loading fails
    """
    try:
        from PIL import Image, ImageTk
        
        icon_path = get_icon_path()
        if not os.path.exists(icon_path):
            logger.debug(f"Icon file not found at: {icon_path}")
            return None
        
        # Check if we have a Tkinter root window
        try:
            import tkinter as tk
            root = tk._default_root
            if root is None:
                # Create a temporary root window for image creation
                temp_root = tk.Tk()
                temp_root.withdraw()  # Hide it
        except:
            pass
        
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


def create_ico_file() -> Optional[str]:
    """Create a high-quality ICO file from the PNG icon for better Windows compatibility.
    
    Returns:
        str: Path to the created ICO file or None if creation fails
    """
    try:
        from PIL import Image
        
        icon_path = get_icon_path()
        if not os.path.exists(icon_path):
            return None
        
        # Create ICO file path
        ico_path = icon_path.replace('.png', '.ico')
        
        # Check if ICO already exists and is newer than PNG
        if os.path.exists(ico_path):
            png_mtime = os.path.getmtime(icon_path)
            ico_mtime = os.path.getmtime(ico_path)
            if ico_mtime > png_mtime:
                return ico_path
        
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
        
        # Create multiple sizes for ICO file
        ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        ico_images = []
        
        for size in ico_sizes:
            # High-quality resize
            resized = icon_image.resize(size, Image.Resampling.LANCZOS)
            ico_images.append(resized)
        
        # Save as ICO with multiple sizes
        icon_image.save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in ico_images])
        
        logger.debug(f"Created high-quality ICO file: {ico_path}")
        return ico_path
        
    except Exception as e:
        logger.debug(f"Error creating ICO file: {e}")
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
        # Try to clear any existing icon
        window.wm_iconbitmap("")
    except:
        pass
    
    try:
        # Clear iconphoto as well
        window.wm_iconphoto(True, "")
    except:
        pass


def set_window_icon(window: Union[tk.Tk, tk.Toplevel], store_reference: bool = True) -> bool:
    """Set the icon for a Tkinter window with minimal processing for best quality.
    
    Args:
        window: The Tkinter window to set the icon for
        store_reference: Whether to store icon reference in window to prevent GC
        
    Returns:
        bool: True if icon was set successfully, False otherwise
    """
    try:
        # Load single high-quality icon
        icons = load_application_icons()
        if not icons or len(icons) == 0:
            logger.debug("No icons available to set")
            return False
        
        # Use just the single high-quality icon
        icon = icons[0]
        window.wm_iconphoto(True, icon)
        
        # Store reference to prevent garbage collection
        if store_reference:
            window._vaitp_icon = icon
        
        logger.debug("Window icon set using single high-quality 64x64 PNG")
        return True
            
    except Exception as e:
        logger.debug(f"Error setting window icon: {e}")
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