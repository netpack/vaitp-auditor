"""
Accessibility Manager for VAITP-Auditor GUI

This module provides accessibility features including keyboard navigation,
screen reader support, high contrast mode, and configurable font scaling.
"""

import logging
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass
from enum import Enum

try:
    import customtkinter as ctk
    import tkinter as tk
    from tkinter import ttk
    CTK_AVAILABLE = True
except ImportError:
    ctk = None
    tk = None
    ttk = None
    CTK_AVAILABLE = False

# Type alias for widgets - use Union to handle both CTk and Tk widgets
if CTK_AVAILABLE:
    from typing import Union
    WidgetType = Union[ctk.CTkBaseClass, tk.Widget]
else:
    WidgetType = object


class AccessibilityMode(Enum):
    """Accessibility mode options."""
    NORMAL = "normal"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    SCREEN_READER = "screen_reader"


@dataclass
class AccessibilityConfig:
    """Configuration for accessibility features."""
    
    # Keyboard navigation
    enable_keyboard_navigation: bool = True
    tab_navigation: bool = True
    arrow_key_navigation: bool = True
    
    # Screen reader support
    enable_screen_reader: bool = False
    announce_changes: bool = True
    verbose_descriptions: bool = False
    
    # Visual accessibility
    high_contrast_mode: bool = False
    font_scale_factor: float = 1.0
    focus_indicator_width: int = 3
    
    # Audio feedback
    enable_audio_feedback: bool = False
    button_click_sound: bool = False
    
    def validate(self) -> None:
        """Validate accessibility configuration."""
        if not isinstance(self.enable_keyboard_navigation, bool):
            raise ValueError("enable_keyboard_navigation must be a boolean")
        
        if not isinstance(self.font_scale_factor, (int, float)):
            raise ValueError("font_scale_factor must be a number")
        
        if self.font_scale_factor < 0.5 or self.font_scale_factor > 3.0:
            raise ValueError("font_scale_factor must be between 0.5 and 3.0")
        
        if not isinstance(self.focus_indicator_width, int) or self.focus_indicator_width < 1:
            raise ValueError("focus_indicator_width must be a positive integer")


class KeyboardNavigationManager:
    """Manages keyboard navigation throughout the GUI."""
    
    def __init__(self, root_widget: WidgetType):
        """Initialize keyboard navigation manager.
        
        Args:
            root_widget: Root window widget
        """
        self.root = root_widget
        self.logger = logging.getLogger(__name__)
        self.focus_order: List[WidgetType] = []
        self.current_focus_index: int = -1
        self.key_bindings: Dict[str, Callable] = {}
        
        # Setup global keyboard bindings
        self._setup_global_bindings()
    
    def _setup_global_bindings(self) -> None:
        """Setup global keyboard bindings."""
        try:
            # Tab navigation
            self.root.bind("<Tab>", self._handle_tab_forward)
            self.root.bind("<Shift-Tab>", self._handle_tab_backward)
            
            # Arrow key navigation
            self.root.bind("<Up>", self._handle_arrow_up)
            self.root.bind("<Down>", self._handle_arrow_down)
            self.root.bind("<Left>", self._handle_arrow_left)
            self.root.bind("<Right>", self._handle_arrow_right)
            
            # Enter/Space for activation
            self.root.bind("<Return>", self._handle_activate)
            self.root.bind("<space>", self._handle_activate)
            
            # Escape for cancel/close
            self.root.bind("<Escape>", self._handle_escape)
            
            # F1 for help
            self.root.bind("<F1>", self._handle_help)
            
        except Exception as e:
            self.logger.error(f"Error setting up global keyboard bindings: {e}")
    
    def register_widget(self, widget: WidgetType, tab_order: Optional[int] = None) -> None:
        """Register a widget for keyboard navigation.
        
        Args:
            widget: Widget to register
            tab_order: Optional tab order position
        """
        try:
            if tab_order is not None:
                self.focus_order.insert(tab_order, widget)
            else:
                self.focus_order.append(widget)
            
            # Add focus event handlers
            widget.bind("<FocusIn>", lambda e: self._on_widget_focus_in(widget))
            widget.bind("<FocusOut>", lambda e: self._on_widget_focus_out(widget))
            
        except Exception as e:
            self.logger.error(f"Error registering widget for navigation: {e}")
    
    def unregister_widget(self, widget: WidgetType) -> None:
        """Unregister a widget from keyboard navigation.
        
        Args:
            widget: Widget to unregister
        """
        try:
            if widget in self.focus_order:
                self.focus_order.remove(widget)
        except Exception as e:
            self.logger.error(f"Error unregistering widget: {e}")
    
    def _handle_tab_forward(self, event) -> str:
        """Handle Tab key for forward navigation."""
        try:
            self._move_focus(1)
            return "break"  # Prevent default tab behavior
        except Exception as e:
            self.logger.error(f"Error handling tab forward: {e}")
            return "continue"
    
    def _handle_tab_backward(self, event) -> str:
        """Handle Shift+Tab for backward navigation."""
        try:
            self._move_focus(-1)
            return "break"
        except Exception as e:
            self.logger.error(f"Error handling tab backward: {e}")
            return "continue"
    
    def _handle_arrow_up(self, event) -> str:
        """Handle Up arrow key."""
        try:
            # Move focus up in grid layouts
            self._move_focus_in_direction("up")
            return "break"
        except Exception as e:
            self.logger.error(f"Error handling arrow up: {e}")
            return "continue"
    
    def _handle_arrow_down(self, event) -> str:
        """Handle Down arrow key."""
        try:
            # Move focus down in grid layouts
            self._move_focus_in_direction("down")
            return "break"
        except Exception as e:
            self.logger.error(f"Error handling arrow down: {e}")
            return "continue"
    
    def _handle_arrow_left(self, event) -> str:
        """Handle Left arrow key."""
        try:
            # Move focus left in grid layouts
            self._move_focus_in_direction("left")
            return "break"
        except Exception as e:
            self.logger.error(f"Error handling arrow left: {e}")
            return "continue"
    
    def _handle_arrow_right(self, event) -> str:
        """Handle Right arrow key."""
        try:
            # Move focus right in grid layouts
            self._move_focus_in_direction("right")
            return "break"
        except Exception as e:
            self.logger.error(f"Error handling arrow right: {e}")
            return "continue"
    
    def _handle_activate(self, event) -> str:
        """Handle Enter/Space for widget activation."""
        try:
            focused_widget = self.root.focus_get()
            if focused_widget and hasattr(focused_widget, 'invoke'):
                focused_widget.invoke()
                return "break"
        except Exception as e:
            self.logger.error(f"Error handling activation: {e}")
        return "continue"
    
    def _handle_escape(self, event) -> str:
        """Handle Escape key for cancel/close operations."""
        try:
            # Find the topmost window and try to close it
            current_widget = self.root.focus_get()
            if current_widget:
                toplevel = current_widget.winfo_toplevel()
                if hasattr(toplevel, 'destroy') and toplevel != self.root:
                    toplevel.destroy()
                    return "break"
        except Exception as e:
            self.logger.error(f"Error handling escape: {e}")
        return "continue"
    
    def _handle_help(self, event) -> str:
        """Handle F1 key for help."""
        try:
            # Show context-sensitive help
            self._show_help()
            return "break"
        except Exception as e:
            self.logger.error(f"Error handling help: {e}")
        return "continue"
    
    def _move_focus(self, direction: int) -> None:
        """Move focus in the tab order.
        
        Args:
            direction: 1 for forward, -1 for backward
        """
        if not self.focus_order:
            return
        
        # Find current focus index
        current_widget = self.root.focus_get()
        try:
            self.current_focus_index = self.focus_order.index(current_widget)
        except ValueError:
            self.current_focus_index = -1
        
        # Calculate next index
        next_index = (self.current_focus_index + direction) % len(self.focus_order)
        
        # Set focus to next widget
        next_widget = self.focus_order[next_index]
        if next_widget.winfo_exists() and str(next_widget.cget("state")) != "disabled":
            next_widget.focus_set()
            self.current_focus_index = next_index
    
    def _move_focus_in_direction(self, direction: str) -> None:
        """Move focus in a specific direction for grid layouts.
        
        Args:
            direction: "up", "down", "left", or "right"
        """
        # For now, use tab order navigation
        # In a full implementation, this would analyze grid positions
        if direction in ["up", "left"]:
            self._move_focus(-1)
        else:
            self._move_focus(1)
    
    def _on_widget_focus_in(self, widget: WidgetType) -> None:
        """Handle widget gaining focus."""
        try:
            # Update current focus index
            if widget in self.focus_order:
                self.current_focus_index = self.focus_order.index(widget)
            
            # Add visual focus indicator
            self._add_focus_indicator(widget)
            
        except Exception as e:
            self.logger.error(f"Error handling focus in: {e}")
    
    def _on_widget_focus_out(self, widget: WidgetType) -> None:
        """Handle widget losing focus."""
        try:
            # Remove visual focus indicator
            self._remove_focus_indicator(widget)
            
        except Exception as e:
            self.logger.error(f"Error handling focus out: {e}")
    
    def _add_focus_indicator(self, widget: WidgetType) -> None:
        """Add visual focus indicator to widget."""
        try:
            # Store original border configuration
            if not hasattr(widget, '_original_border_width'):
                try:
                    widget._original_border_width = widget.cget("border_width")
                    widget._original_border_color = widget.cget("border_color")
                except:
                    # Fallback for widgets without border properties
                    widget._original_border_width = 0
                    widget._original_border_color = "#000000"
            
            # Apply focus indicator
            try:
                widget.configure(
                    border_width=3,
                    border_color="#0078d4"  # Accessible blue color
                )
            except:
                # For widgets that don't support border, try relief
                try:
                    widget.configure(relief="solid", highlightthickness=3, highlightcolor="#0078d4")
                except:
                    pass
            
        except Exception as e:
            self.logger.debug(f"Could not add focus indicator to {type(widget).__name__}: {e}")
    
    def _remove_focus_indicator(self, widget: WidgetType) -> None:
        """Remove visual focus indicator from widget."""
        try:
            # Restore original border configuration
            if hasattr(widget, '_original_border_width'):
                try:
                    widget.configure(
                        border_width=widget._original_border_width,
                        border_color=widget._original_border_color
                    )
                except:
                    # Restore relief-based focus indicator
                    try:
                        widget.configure(relief="flat", highlightthickness=0)
                    except:
                        pass
            
        except Exception as e:
            self.logger.debug(f"Could not remove focus indicator from {type(widget).__name__}: {e}")
    
    def _show_help(self) -> None:
        """Show context-sensitive help."""
        try:
            # Get current focused widget
            focused_widget = self.root.focus_get()
            
            # Create help dialog
            help_dialog = ctk.CTkToplevel(self.root)
            help_dialog.title("Keyboard Navigation Help")
            help_dialog.geometry("500x400")
            help_dialog.transient(self.root)
            help_dialog.grab_set()
            
            # Center the dialog
            help_dialog.update_idletasks()
            x = (help_dialog.winfo_screenwidth() // 2) - 250
            y = (help_dialog.winfo_screenheight() // 2) - 200
            help_dialog.geometry(f"500x400+{x}+{y}")
            
            # Help content
            help_text = """Keyboard Navigation Help

General Navigation:
• Tab / Shift+Tab: Move between controls
• Arrow Keys: Navigate within groups
• Enter / Space: Activate buttons and controls
• Escape: Cancel or close dialogs
• F1: Show this help

Accessibility Features:
• Ctrl + Plus/Equal: Increase font size
• Ctrl + Minus: Decrease font size
• Ctrl + 0: Reset font size to normal
• Ctrl + Shift + H: Toggle high contrast mode
• Alt + A: Open accessibility settings

Verdict Buttons:
• S: Success
• F: Failure - No Change
• I: Invalid Code
• W: Wrong Vulnerability
• P: Partial Success
• C: Custom

Session Controls:
• U: Undo Last
• Q: Quit Session
• Ctrl + S: Save session progress
• Ctrl + R: Resume session

Code Panels:
• Use Tab to focus panels
• Arrow keys to scroll when focused
• Page Up/Down for faster scrolling
• Ctrl + F: Find in code (if supported)
• Home/End: Go to beginning/end of line
• Ctrl + Home/End: Go to beginning/end of file

Window Management:
• F11: Toggle fullscreen mode
• Ctrl + W: Close current window
• Alt + F4: Exit application
"""
            
            text_widget = ctk.CTkTextbox(help_dialog)
            text_widget.pack(fill="both", expand=True, padx=20, pady=20)
            text_widget.insert("1.0", help_text)
            text_widget.configure(state="disabled")
            
            # Close button
            close_button = ctk.CTkButton(
                help_dialog,
                text="Close (Escape)",
                command=help_dialog.destroy
            )
            close_button.pack(pady=(0, 20))
            
            # Bind escape to close
            help_dialog.bind("<Escape>", lambda e: help_dialog.destroy())
            
            # Focus the close button
            close_button.focus_set()
            
        except Exception as e:
            self.logger.error(f"Error showing help: {e}")


class ScreenReaderManager:
    """Manages screen reader compatibility and announcements."""
    
    def __init__(self, root_widget: WidgetType):
        """Initialize screen reader manager.
        
        Args:
            root_widget: Root window widget
        """
        self.root = root_widget
        self.logger = logging.getLogger(__name__)
        self.announcements_enabled = True
        
    def announce(self, message: str, priority: str = "normal") -> None:
        """Announce a message to screen readers.
        
        Args:
            message: Message to announce
            priority: Priority level ("low", "normal", "high")
        """
        if not self.announcements_enabled:
            return
        
        try:
            # Update window title with announcement (basic screen reader support)
            original_title = self.root.title()
            
            if priority == "high":
                announcement = f"ALERT: {message}"
            else:
                announcement = message
            
            # Temporarily update title for screen readers
            self.root.title(f"{original_title} - {announcement}")
            
            # Restore original title after brief delay
            self.root.after(2000, lambda: self.root.title(original_title))
            
            self.logger.debug(f"Screen reader announcement: {message}")
            
        except Exception as e:
            self.logger.error(f"Error making screen reader announcement: {e}")
    
    def set_widget_label(self, widget: WidgetType, label: str) -> None:
        """Set accessible label for a widget.
        
        Args:
            widget: Widget to label
            label: Accessible label text
        """
        try:
            # Store label as widget attribute
            widget._accessible_label = label
            
            # Try to set tooltip as fallback
            if hasattr(widget, 'configure'):
                try:
                    widget.configure(tooltip=label)
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"Error setting widget label: {e}")
    
    def set_widget_description(self, widget: WidgetType, description: str) -> None:
        """Set accessible description for a widget.
        
        Args:
            widget: Widget to describe
            description: Accessible description text
        """
        try:
            # Store description as widget attribute
            widget._accessible_description = description
            
        except Exception as e:
            self.logger.error(f"Error setting widget description: {e}")
    
    def announce_progress(self, current: int, total: int, item_name: str = "") -> None:
        """Announce progress updates.
        
        Args:
            current: Current progress value
            total: Total progress value
            item_name: Optional name of current item
        """
        try:
            percentage = (current / total * 100) if total > 0 else 0
            
            if item_name:
                message = f"Progress: {current} of {total} ({percentage:.0f}%) - {item_name}"
            else:
                message = f"Progress: {current} of {total} ({percentage:.0f}%)"
            
            self.announce(message, priority="low")
            
        except Exception as e:
            self.logger.error(f"Error announcing progress: {e}")
    
    def announce_verdict_selection(self, verdict: str) -> None:
        """Announce verdict selection.
        
        Args:
            verdict: Selected verdict
        """
        try:
            message = f"Verdict selected: {verdict}"
            self.announce(message, priority="normal")
            
        except Exception as e:
            self.logger.error(f"Error announcing verdict selection: {e}")


class HighContrastManager:
    """Manages high contrast mode for better visibility."""
    
    def __init__(self, root_widget: WidgetType):
        """Initialize high contrast manager.
        
        Args:
            root_widget: Root window widget
        """
        self.root = root_widget
        self.logger = logging.getLogger(__name__)
        self.high_contrast_enabled = False
        self.original_colors: Dict[WidgetType, Dict[str, Any]] = {}
        
        # High contrast color scheme
        self.high_contrast_colors = {
            "bg_color": "#000000",
            "fg_color": "#FFFFFF",
            "text_color": "#FFFFFF",
            "button_color": "#FFFFFF",
            "button_hover_color": "#CCCCCC",
            "button_text_color": "#000000",
            "entry_color": "#FFFFFF",
            "entry_text_color": "#000000",
            "focus_color": "#FFFF00",  # Yellow for focus
            "success_color": "#00FF00",  # Bright green
            "error_color": "#FF0000",   # Bright red
            "warning_color": "#FFFF00"  # Bright yellow
        }
    
    def enable_high_contrast(self) -> None:
        """Enable high contrast mode."""
        try:
            if self.high_contrast_enabled:
                return
            
            self.high_contrast_enabled = True
            
            # Apply high contrast theme to CustomTkinter
            ctk.set_appearance_mode("dark")
            
            # Store and apply high contrast colors to all widgets
            self._apply_high_contrast_recursively(self.root)
            
            self.logger.info("High contrast mode enabled")
            
        except Exception as e:
            self.logger.error(f"Error enabling high contrast mode: {e}")
    
    def disable_high_contrast(self) -> None:
        """Disable high contrast mode."""
        try:
            if not self.high_contrast_enabled:
                return
            
            self.high_contrast_enabled = False
            
            # Restore original colors
            self._restore_original_colors()
            
            # Reset CustomTkinter theme
            ctk.set_appearance_mode("system")
            
            self.logger.info("High contrast mode disabled")
            
        except Exception as e:
            self.logger.error(f"Error disabling high contrast mode: {e}")
    
    def toggle_high_contrast(self) -> None:
        """Toggle high contrast mode."""
        if self.high_contrast_enabled:
            self.disable_high_contrast()
        else:
            self.enable_high_contrast()
    
    def _apply_high_contrast_recursively(self, widget: WidgetType) -> None:
        """Apply high contrast colors to widget and its children.
        
        Args:
            widget: Widget to apply high contrast to
        """
        try:
            # Store original colors
            if widget not in self.original_colors:
                self.original_colors[widget] = {}
                
                # Store configurable color properties
                color_properties = ["fg_color", "bg_color", "text_color", "button_color", 
                                  "button_hover_color", "hover_color"]
                
                for prop in color_properties:
                    try:
                        original_value = widget.cget(prop)
                        self.original_colors[widget][prop] = original_value
                    except:
                        pass
            
            # Apply high contrast colors based on widget type
            self._apply_widget_high_contrast(widget)
            
            # Recursively apply to children
            try:
                for child in widget.winfo_children():
                    if hasattr(child, 'configure'):  # Any configurable widget
                        self._apply_high_contrast_recursively(child)
            except:
                pass
            
        except Exception as e:
            self.logger.debug(f"Error applying high contrast to {type(widget).__name__}: {e}")
    
    def _apply_widget_high_contrast(self, widget: WidgetType) -> None:
        """Apply high contrast colors to a specific widget.
        
        Args:
            widget: Widget to apply colors to
        """
        try:
            widget_type = type(widget).__name__
            
            # Apply colors based on widget type
            if "Button" in widget_type:
                try:
                    widget.configure(
                        fg_color=self.high_contrast_colors["button_color"],
                        hover_color=self.high_contrast_colors["button_hover_color"],
                        text_color=self.high_contrast_colors["button_text_color"]
                    )
                except Exception as e:
                    self.logger.debug(f"Could not configure button colors: {e}")
                    
            elif "Entry" in widget_type or "Textbox" in widget_type:
                try:
                    widget.configure(
                        fg_color=self.high_contrast_colors["entry_color"],
                        text_color=self.high_contrast_colors["entry_text_color"]
                    )
                except Exception as e:
                    self.logger.debug(f"Could not configure entry colors: {e}")
                    
            elif "Label" in widget_type:
                try:
                    widget.configure(
                        text_color=self.high_contrast_colors["text_color"]
                    )
                except Exception as e:
                    self.logger.debug(f"Could not configure label colors: {e}")
                    
            elif "Frame" in widget_type:
                try:
                    widget.configure(
                        fg_color=self.high_contrast_colors["bg_color"]
                    )
                except Exception as e:
                    self.logger.debug(f"Could not configure frame colors: {e}")
            
            # Always try to configure basic colors as fallback
            try:
                widget.configure(bg=self.high_contrast_colors["bg_color"])
            except:
                pass
            
            try:
                widget.configure(fg=self.high_contrast_colors["text_color"])
            except:
                pass
            
        except Exception as e:
            self.logger.debug(f"Error applying high contrast to {type(widget).__name__}: {e}")
    
    def _restore_original_colors(self) -> None:
        """Restore original colors to all widgets."""
        try:
            for widget, colors in self.original_colors.items():
                if widget.winfo_exists():
                    for prop, value in colors.items():
                        try:
                            widget.configure(**{prop: value})
                        except:
                            pass
            
            # Clear stored colors
            self.original_colors.clear()
            
        except Exception as e:
            self.logger.error(f"Error restoring original colors: {e}")


class FontScalingManager:
    """Manages configurable font scaling for better readability."""
    
    def __init__(self, root_widget: WidgetType):
        """Initialize font scaling manager.
        
        Args:
            root_widget: Root window widget
        """
        self.root = root_widget
        self.logger = logging.getLogger(__name__)
        self.current_scale = 1.0
        self.original_fonts: Dict[WidgetType, Any] = {}
    
    def set_font_scale(self, scale_factor: float) -> None:
        """Set font scale factor for all text.
        
        Args:
            scale_factor: Scale factor (0.5 to 3.0)
        """
        if scale_factor < 0.5 or scale_factor > 3.0:
            raise ValueError("Scale factor must be between 0.5 and 3.0")
        
        try:
            self.current_scale = scale_factor
            
            # Apply scaling to all widgets
            self._apply_font_scaling_recursively(self.root)
            
            self.logger.info(f"Font scaling set to {scale_factor}")
            
        except Exception as e:
            self.logger.error(f"Error setting font scale: {e}")
            raise
    
    def increase_font_size(self, increment: float = 0.1) -> None:
        """Increase font size by increment.
        
        Args:
            increment: Amount to increase scale by
        """
        new_scale = min(3.0, round(self.current_scale + increment, 1))
        self.set_font_scale(new_scale)
    
    def decrease_font_size(self, decrement: float = 0.1) -> None:
        """Decrease font size by decrement.
        
        Args:
            decrement: Amount to decrease scale by
        """
        new_scale = max(0.5, round(self.current_scale - decrement, 1))
        self.set_font_scale(new_scale)
    
    def reset_font_size(self) -> None:
        """Reset font size to normal (1.0)."""
        self.set_font_scale(1.0)
    
    def _apply_font_scaling_recursively(self, widget: WidgetType) -> None:
        """Apply font scaling to widget and its children.
        
        Args:
            widget: Widget to apply scaling to
        """
        try:
            # Store original font if not already stored
            if widget not in self.original_fonts:
                try:
                    original_font = widget.cget("font")
                    if original_font:
                        self.original_fonts[widget] = original_font
                except:
                    pass
            
            # Apply scaled font
            self._apply_widget_font_scaling(widget)
            
            # Recursively apply to children
            try:
                for child in widget.winfo_children():
                    if hasattr(child, 'configure'):  # Any configurable widget
                        self._apply_font_scaling_recursively(child)
            except:
                pass
            
        except Exception as e:
            self.logger.debug(f"Error applying font scaling to {type(widget).__name__}: {e}")
    
    def _apply_widget_font_scaling(self, widget: WidgetType) -> None:
        """Apply font scaling to a specific widget.
        
        Args:
            widget: Widget to apply scaling to
        """
        try:
            # Get original or current font
            original_font = self.original_fonts.get(widget)
            if not original_font:
                try:
                    original_font = widget.cget("font")
                except:
                    return
            
            if not original_font:
                return
            
            # Calculate new font size
            if CTK_AVAILABLE and hasattr(ctk, 'CTkFont') and isinstance(original_font, ctk.CTkFont):
                original_size = original_font.cget("size")
                new_size = int(original_size * self.current_scale)
                
                # Create scaled font
                scaled_font = ctk.CTkFont(
                    family=original_font.cget("family"),
                    size=new_size,
                    weight=original_font.cget("weight"),
                    slant=original_font.cget("slant")
                )
                
                widget.configure(font=scaled_font)
            elif isinstance(original_font, tuple):
                # Handle tuple font specification (family, size, style)
                family, size, *style = original_font
                new_size = int(size * self.current_scale)
                new_font = (family, new_size, *style)
                widget.configure(font=new_font)
            elif hasattr(original_font, 'configure'):
                # Handle tkinter Font objects
                try:
                    original_size = original_font['size']
                    new_size = int(original_size * self.current_scale)
                    original_font.configure(size=new_size)
                except:
                    pass
            
        except Exception as e:
            self.logger.debug(f"Error applying font scaling to {type(widget).__name__}: {e}")


class AccessibilityManager:
    """Main accessibility manager that coordinates all accessibility features."""
    
    def __init__(self, root_widget: WidgetType, config: Optional[AccessibilityConfig] = None):
        """Initialize accessibility manager.
        
        Args:
            root_widget: Root window widget
            config: Accessibility configuration
        """
        self.root = root_widget
        self.config = config or AccessibilityConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize sub-managers
        self.keyboard_nav = KeyboardNavigationManager(root_widget)
        self.screen_reader = ScreenReaderManager(root_widget)
        self.high_contrast = HighContrastManager(root_widget)
        self.font_scaling = FontScalingManager(root_widget)
        
        # Apply initial configuration
        self._apply_configuration()
        
        # Setup global accessibility shortcuts
        self._setup_accessibility_shortcuts()
    
    def _apply_configuration(self) -> None:
        """Apply accessibility configuration."""
        try:
            # Apply high contrast mode
            if self.config.high_contrast_mode:
                self.high_contrast.enable_high_contrast()
            
            # Apply font scaling
            if self.config.font_scale_factor != 1.0:
                self.font_scaling.set_font_scale(self.config.font_scale_factor)
            
            # Configure screen reader
            self.screen_reader.announcements_enabled = self.config.enable_screen_reader
            
        except Exception as e:
            self.logger.error(f"Error applying accessibility configuration: {e}")
    
    def _setup_accessibility_shortcuts(self) -> None:
        """Setup global accessibility keyboard shortcuts."""
        try:
            # Font scaling shortcuts
            self.root.bind("<Control-plus>", lambda e: self.font_scaling.increase_font_size())
            self.root.bind("<Control-equal>", lambda e: self.font_scaling.increase_font_size())  # For keyboards without numpad
            self.root.bind("<Control-KP_Add>", lambda e: self.font_scaling.increase_font_size())  # Numpad plus
            self.root.bind("<Control-minus>", lambda e: self.font_scaling.decrease_font_size())
            self.root.bind("<Control-KP_Subtract>", lambda e: self.font_scaling.decrease_font_size())  # Numpad minus
            self.root.bind("<Control-0>", lambda e: self.font_scaling.reset_font_size())
            
            # High contrast toggle
            self.root.bind("<Control-Shift-H>", lambda e: self.high_contrast.toggle_high_contrast())
            
            # Accessibility settings dialog
            self.root.bind("<Alt-a>", lambda e: self._show_accessibility_settings())
            self.root.bind("<Alt-A>", lambda e: self._show_accessibility_settings())
            
            # Screen reader announcements toggle
            self.root.bind("<Control-Shift-S>", lambda e: self._toggle_screen_reader())
            
            # Focus management
            self.root.bind("<Control-Shift-F>", lambda e: self._show_focus_order())
            
            # Quick accessibility mode toggles
            self.root.bind("<F2>", lambda e: self._toggle_accessibility_mode("high_contrast"))
            self.root.bind("<F3>", lambda e: self._toggle_accessibility_mode("large_text"))
            self.root.bind("<F4>", lambda e: self._toggle_accessibility_mode("screen_reader"))
            
        except Exception as e:
            self.logger.error(f"Error setting up accessibility shortcuts: {e}")
    
    def _show_accessibility_settings(self) -> None:
        """Show accessibility settings dialog."""
        try:
            # Create accessibility settings dialog
            settings_dialog = ctk.CTkToplevel(self.root)
            settings_dialog.title("Accessibility Settings")
            settings_dialog.geometry("600x500")
            settings_dialog.transient(self.root)
            settings_dialog.grab_set()
            
            # Center the dialog
            settings_dialog.update_idletasks()
            x = (settings_dialog.winfo_screenwidth() // 2) - 300
            y = (settings_dialog.winfo_screenheight() // 2) - 250
            settings_dialog.geometry(f"600x500+{x}+{y}")
            
            # Create settings interface
            self._create_accessibility_settings_ui(settings_dialog)
            
        except Exception as e:
            self.logger.error(f"Error showing accessibility settings: {e}")
    
    def _create_accessibility_settings_ui(self, parent: ctk.CTkToplevel) -> None:
        """Create accessibility settings user interface.
        
        Args:
            parent: Parent window for settings
        """
        try:
            # Main frame with scrollable content
            main_frame = ctk.CTkScrollableFrame(parent)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Title
            title_label = ctk.CTkLabel(
                main_frame,
                text="Accessibility Settings",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title_label.pack(pady=(0, 20))
            
            # Keyboard Navigation Section
            nav_frame = ctk.CTkFrame(main_frame)
            nav_frame.pack(fill="x", pady=(0, 15))
            
            nav_title = ctk.CTkLabel(
                nav_frame,
                text="Keyboard Navigation",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            nav_title.pack(pady=(10, 5))
            
            # Keyboard navigation checkboxes
            self.nav_enabled_var = ctk.BooleanVar(value=self.config.enable_keyboard_navigation)
            nav_checkbox = ctk.CTkCheckBox(
                nav_frame,
                text="Enable keyboard navigation",
                variable=self.nav_enabled_var,
                command=self._update_keyboard_navigation
            )
            nav_checkbox.pack(anchor="w", padx=20, pady=5)
            
            self.tab_nav_var = ctk.BooleanVar(value=self.config.tab_navigation)
            tab_checkbox = ctk.CTkCheckBox(
                nav_frame,
                text="Tab navigation between controls",
                variable=self.tab_nav_var
            )
            tab_checkbox.pack(anchor="w", padx=20, pady=5)
            
            self.arrow_nav_var = ctk.BooleanVar(value=self.config.arrow_key_navigation)
            arrow_checkbox = ctk.CTkCheckBox(
                nav_frame,
                text="Arrow key navigation within groups",
                variable=self.arrow_nav_var
            )
            arrow_checkbox.pack(anchor="w", padx=20, pady=(5, 15))
            
            # Visual Accessibility Section
            visual_frame = ctk.CTkFrame(main_frame)
            visual_frame.pack(fill="x", pady=(0, 15))
            
            visual_title = ctk.CTkLabel(
                visual_frame,
                text="Visual Accessibility",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            visual_title.pack(pady=(10, 5))
            
            # High contrast mode
            self.high_contrast_var = ctk.BooleanVar(value=self.config.high_contrast_mode)
            contrast_checkbox = ctk.CTkCheckBox(
                visual_frame,
                text="High contrast mode",
                variable=self.high_contrast_var,
                command=self._toggle_high_contrast_setting
            )
            contrast_checkbox.pack(anchor="w", padx=20, pady=5)
            
            # Font scaling
            font_label = ctk.CTkLabel(
                visual_frame,
                text=f"Font Scale: {self.config.font_scale_factor:.1f}x",
                font=ctk.CTkFont(size=12)
            )
            font_label.pack(anchor="w", padx=20, pady=(10, 5))
            
            self.font_scale_var = ctk.DoubleVar(value=self.config.font_scale_factor)
            font_slider = ctk.CTkSlider(
                visual_frame,
                from_=0.5,
                to=3.0,
                number_of_steps=25,
                variable=self.font_scale_var,
                command=self._update_font_scale
            )
            font_slider.pack(fill="x", padx=20, pady=(0, 15))
            
            # Screen Reader Section
            reader_frame = ctk.CTkFrame(main_frame)
            reader_frame.pack(fill="x", pady=(0, 15))
            
            reader_title = ctk.CTkLabel(
                reader_frame,
                text="Screen Reader Support",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            reader_title.pack(pady=(10, 5))
            
            # Screen reader checkboxes
            self.screen_reader_var = ctk.BooleanVar(value=self.config.enable_screen_reader)
            reader_checkbox = ctk.CTkCheckBox(
                reader_frame,
                text="Enable screen reader announcements",
                variable=self.screen_reader_var,
                command=self._toggle_screen_reader_setting
            )
            reader_checkbox.pack(anchor="w", padx=20, pady=5)
            
            self.announce_changes_var = ctk.BooleanVar(value=self.config.announce_changes)
            announce_checkbox = ctk.CTkCheckBox(
                reader_frame,
                text="Announce UI changes",
                variable=self.announce_changes_var
            )
            announce_checkbox.pack(anchor="w", padx=20, pady=5)
            
            self.verbose_desc_var = ctk.BooleanVar(value=self.config.verbose_descriptions)
            verbose_checkbox = ctk.CTkCheckBox(
                reader_frame,
                text="Verbose descriptions",
                variable=self.verbose_desc_var
            )
            verbose_checkbox.pack(anchor="w", padx=20, pady=(5, 15))
            
            # Buttons frame
            button_frame = ctk.CTkFrame(parent)
            button_frame.pack(fill="x", padx=20, pady=(0, 20))
            
            # Apply and Close buttons
            apply_button = ctk.CTkButton(
                button_frame,
                text="Apply Settings",
                command=lambda: self._apply_accessibility_settings(parent)
            )
            apply_button.pack(side="left", padx=(10, 5), pady=10)
            
            reset_button = ctk.CTkButton(
                button_frame,
                text="Reset to Defaults",
                command=self._reset_accessibility_settings
            )
            reset_button.pack(side="left", padx=5, pady=10)
            
            close_button = ctk.CTkButton(
                button_frame,
                text="Close",
                command=parent.destroy
            )
            close_button.pack(side="right", padx=(5, 10), pady=10)
            
            # Register widgets for accessibility
            self.register_widget(nav_checkbox, label="Enable keyboard navigation", tab_order=0)
            self.register_widget(contrast_checkbox, label="High contrast mode toggle")
            self.register_widget(font_slider, label="Font scale adjustment")
            self.register_widget(reader_checkbox, label="Screen reader support")
            self.register_widget(apply_button, label="Apply accessibility settings")
            self.register_widget(close_button, label="Close settings dialog")
            
        except Exception as e:
            self.logger.error(f"Error creating accessibility settings UI: {e}")
    
    def _update_keyboard_navigation(self) -> None:
        """Update keyboard navigation setting."""
        self.config.enable_keyboard_navigation = self.nav_enabled_var.get()
    
    def _toggle_high_contrast_setting(self) -> None:
        """Toggle high contrast mode from settings."""
        if self.high_contrast_var.get():
            self.high_contrast.enable_high_contrast()
        else:
            self.high_contrast.disable_high_contrast()
        self.config.high_contrast_mode = self.high_contrast_var.get()
    
    def _update_font_scale(self, value: float) -> None:
        """Update font scale from slider.
        
        Args:
            value: New font scale value
        """
        self.font_scaling.set_font_scale(value)
        self.config.font_scale_factor = value
    
    def _toggle_screen_reader_setting(self) -> None:
        """Toggle screen reader from settings."""
        self.screen_reader.announcements_enabled = self.screen_reader_var.get()
        self.config.enable_screen_reader = self.screen_reader_var.get()
    
    def _apply_accessibility_settings(self, dialog: ctk.CTkToplevel) -> None:
        """Apply accessibility settings and close dialog.
        
        Args:
            dialog: Settings dialog to close
        """
        try:
            # Update configuration from UI
            self.config.enable_keyboard_navigation = self.nav_enabled_var.get()
            self.config.tab_navigation = self.tab_nav_var.get()
            self.config.arrow_key_navigation = self.arrow_nav_var.get()
            self.config.high_contrast_mode = self.high_contrast_var.get()
            self.config.font_scale_factor = self.font_scale_var.get()
            self.config.enable_screen_reader = self.screen_reader_var.get()
            self.config.announce_changes = self.announce_changes_var.get()
            self.config.verbose_descriptions = self.verbose_desc_var.get()
            
            # Apply configuration
            self._apply_configuration()
            
            # Announce success
            self.announce("Accessibility settings applied successfully")
            
            # Close dialog
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Error applying accessibility settings: {e}")
    
    def _reset_accessibility_settings(self) -> None:
        """Reset accessibility settings to defaults."""
        try:
            # Reset to default configuration
            default_config = AccessibilityConfig()
            
            # Update UI variables
            self.nav_enabled_var.set(default_config.enable_keyboard_navigation)
            self.tab_nav_var.set(default_config.tab_navigation)
            self.arrow_nav_var.set(default_config.arrow_key_navigation)
            self.high_contrast_var.set(default_config.high_contrast_mode)
            self.font_scale_var.set(default_config.font_scale_factor)
            self.screen_reader_var.set(default_config.enable_screen_reader)
            self.announce_changes_var.set(default_config.announce_changes)
            self.verbose_desc_var.set(default_config.verbose_descriptions)
            
            # Apply defaults
            self.config = default_config
            self._apply_configuration()
            
            self.announce("Accessibility settings reset to defaults")
            
        except Exception as e:
            self.logger.error(f"Error resetting accessibility settings: {e}")
    
    def _toggle_screen_reader(self) -> None:
        """Toggle screen reader announcements."""
        self.screen_reader.announcements_enabled = not self.screen_reader.announcements_enabled
        self.config.enable_screen_reader = self.screen_reader.announcements_enabled
        
        status = "enabled" if self.screen_reader.announcements_enabled else "disabled"
        self.announce(f"Screen reader announcements {status}", priority="high")
    
    def _show_focus_order(self) -> None:
        """Show current focus order for debugging."""
        try:
            focus_info = []
            for i, widget in enumerate(self.keyboard_nav.focus_order):
                widget_type = type(widget).__name__
                label = getattr(widget, '_accessible_label', 'No label')
                focus_info.append(f"{i+1}. {widget_type}: {label}")
            
            focus_text = "Current Focus Order:\n\n" + "\n".join(focus_info)
            
            # Create focus order dialog
            focus_dialog = ctk.CTkToplevel(self.root)
            focus_dialog.title("Focus Order")
            focus_dialog.geometry("400x300")
            focus_dialog.transient(self.root)
            
            text_widget = ctk.CTkTextbox(focus_dialog)
            text_widget.pack(fill="both", expand=True, padx=20, pady=20)
            text_widget.insert("1.0", focus_text)
            text_widget.configure(state="disabled")
            
        except Exception as e:
            self.logger.error(f"Error showing focus order: {e}")
    
    def _toggle_accessibility_mode(self, mode: str) -> None:
        """Toggle specific accessibility mode.
        
        Args:
            mode: Mode to toggle ("high_contrast", "large_text", "screen_reader")
        """
        try:
            if mode == "high_contrast":
                self.high_contrast.toggle_high_contrast()
                self.config.high_contrast_mode = self.high_contrast.high_contrast_enabled
                status = "enabled" if self.high_contrast.high_contrast_enabled else "disabled"
                self.announce(f"High contrast mode {status}", priority="high")
                
            elif mode == "large_text":
                if self.config.font_scale_factor == 1.0:
                    self.font_scaling.set_font_scale(1.5)
                    self.config.font_scale_factor = 1.5
                    self.announce("Large text mode enabled", priority="high")
                else:
                    self.font_scaling.reset_font_size()
                    self.config.font_scale_factor = 1.0
                    self.announce("Large text mode disabled", priority="high")
                    
            elif mode == "screen_reader":
                self._toggle_screen_reader()
                
        except Exception as e:
            self.logger.error(f"Error toggling accessibility mode {mode}: {e}")
    
    def register_widget(self, widget: WidgetType, 
                       label: Optional[str] = None,
                       description: Optional[str] = None,
                       tab_order: Optional[int] = None) -> None:
        """Register a widget for accessibility features.
        
        Args:
            widget: Widget to register
            label: Accessible label
            description: Accessible description
            tab_order: Tab order position
        """
        try:
            # Register for keyboard navigation
            if self.config.enable_keyboard_navigation:
                self.keyboard_nav.register_widget(widget, tab_order)
            
            # Set screen reader labels
            if label:
                self.screen_reader.set_widget_label(widget, label)
            
            if description:
                self.screen_reader.set_widget_description(widget, description)
            
        except Exception as e:
            self.logger.error(f"Error registering widget for accessibility: {e}")
    
    def unregister_widget(self, widget: WidgetType) -> None:
        """Unregister a widget from accessibility features.
        
        Args:
            widget: Widget to unregister
        """
        try:
            self.keyboard_nav.unregister_widget(widget)
            
        except Exception as e:
            self.logger.error(f"Error unregistering widget: {e}")
    
    def announce(self, message: str, priority: str = "normal") -> None:
        """Make an announcement to screen readers.
        
        Args:
            message: Message to announce
            priority: Priority level
        """
        self.screen_reader.announce(message, priority)
    
    def announce_progress(self, current: int, total: int, item_name: str = "") -> None:
        """Announce progress updates.
        
        Args:
            current: Current progress
            total: Total progress
            item_name: Current item name
        """
        self.screen_reader.announce_progress(current, total, item_name)
    
    def announce_verdict_selection(self, verdict: str) -> None:
        """Announce verdict selection.
        
        Args:
            verdict: Selected verdict
        """
        self.screen_reader.announce_verdict_selection(verdict)
    
    def update_config(self, config: AccessibilityConfig) -> None:
        """Update accessibility configuration.
        
        Args:
            config: New accessibility configuration
        """
        try:
            self.config = config
            self._apply_configuration()
            
        except Exception as e:
            self.logger.error(f"Error updating accessibility configuration: {e}")
    
    def get_config(self) -> AccessibilityConfig:
        """Get current accessibility configuration.
        
        Returns:
            Current accessibility configuration
        """
        return self.config
    
    def cleanup(self) -> None:
        """Clean up accessibility resources."""
        try:
            # Restore original appearance if high contrast was enabled
            if self.high_contrast.high_contrast_enabled:
                self.high_contrast.disable_high_contrast()
            
            # Reset font scaling
            if self.font_scaling.current_scale != 1.0:
                self.font_scaling.reset_font_size()
            
        except Exception as e:
            self.logger.error(f"Error cleaning up accessibility manager: {e}")


def create_accessibility_manager(root_widget: WidgetType, 
                               config: Optional[AccessibilityConfig] = None) -> AccessibilityManager:
    """Create and configure an accessibility manager.
    
    Args:
        root_widget: Root window widget
        config: Optional accessibility configuration
        
    Returns:
        Configured accessibility manager
    """
    if not CTK_AVAILABLE:
        raise ImportError("CustomTkinter is required for accessibility features")
    
    return AccessibilityManager(root_widget, config)