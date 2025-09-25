"""
Accessibility Settings Dialog for VAITP-Auditor GUI

This module provides a comprehensive settings dialog for configuring
accessibility features including keyboard navigation, screen reader support,
high contrast mode, and font scaling.
"""

import logging
from typing import Optional, Callable

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from .accessibility import AccessibilityManager, AccessibilityConfig


class AccessibilitySettingsDialog(ctk.CTkToplevel):
    """
    Dialog for configuring accessibility settings.
    
    Provides a user-friendly interface for adjusting accessibility features
    including keyboard navigation, screen reader support, visual enhancements,
    and font scaling options.
    """
    
    def __init__(self, parent: ctk.CTk, accessibility_manager: AccessibilityManager):
        """Initialize the accessibility settings dialog.
        
        Args:
            parent: Parent window
            accessibility_manager: Accessibility manager to configure
        """
        super().__init__(parent)
        
        self.parent = parent
        self.accessibility_manager = accessibility_manager
        self.logger = logging.getLogger(__name__)
        
        # Store original config for cancel functionality
        self.original_config = AccessibilityConfig(
            enable_keyboard_navigation=accessibility_manager.config.enable_keyboard_navigation,
            tab_navigation=accessibility_manager.config.tab_navigation,
            arrow_key_navigation=accessibility_manager.config.arrow_key_navigation,
            enable_screen_reader=accessibility_manager.config.enable_screen_reader,
            announce_changes=accessibility_manager.config.announce_changes,
            verbose_descriptions=accessibility_manager.config.verbose_descriptions,
            high_contrast_mode=accessibility_manager.config.high_contrast_mode,
            font_scale_factor=accessibility_manager.config.font_scale_factor,
            focus_indicator_width=accessibility_manager.config.focus_indicator_width,
            enable_audio_feedback=accessibility_manager.config.enable_audio_feedback,
            button_click_sound=accessibility_manager.config.button_click_sound
        )
        
        # UI components
        self.keyboard_nav_var: Optional[ctk.BooleanVar] = None
        self.tab_nav_var: Optional[ctk.BooleanVar] = None
        self.arrow_nav_var: Optional[ctk.BooleanVar] = None
        self.screen_reader_var: Optional[ctk.BooleanVar] = None
        self.announce_changes_var: Optional[ctk.BooleanVar] = None
        self.verbose_descriptions_var: Optional[ctk.BooleanVar] = None
        self.high_contrast_var: Optional[ctk.BooleanVar] = None
        self.font_scale_var: Optional[ctk.DoubleVar] = None
        self.focus_width_var: Optional[ctk.IntVar] = None
        self.audio_feedback_var: Optional[ctk.BooleanVar] = None
        self.button_sound_var: Optional[ctk.BooleanVar] = None
        
        self._setup_dialog()
        self._create_widgets()
        self._load_current_settings()
        
        # Register with accessibility manager
        if self.accessibility_manager:
            self.accessibility_manager.register_widget(
                self,
                label="Accessibility Settings Dialog",
                description="Dialog for configuring accessibility features"
            )
    
    def _setup_dialog(self) -> None:
        """Set up the dialog window properties."""
        self.title("Accessibility Settings")
        self.geometry("600x700")
        self.resizable(False, False)
        
        # Center the dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 300
        y = (self.winfo_screenheight() // 2) - 350
        self.geometry(f"600x700+{x}+{y}")
        
        # Make dialog modal
        self.transient(self.parent)
        self.grab_set()
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Keyboard shortcuts
        self.bind("<Escape>", lambda e: self._on_cancel())
        self.bind("<Return>", lambda e: self._on_apply())
        self.bind("<Control-s>", lambda e: self._on_apply())
    
    def _create_widgets(self) -> None:
        """Create the dialog widgets."""
        # Main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Accessibility Settings",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Keyboard Navigation Section
        self._create_keyboard_section(main_frame)
        
        # Screen Reader Section
        self._create_screen_reader_section(main_frame)
        
        # Visual Accessibility Section
        self._create_visual_section(main_frame)
        
        # Audio Feedback Section
        self._create_audio_section(main_frame)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Action buttons
        self._create_action_buttons(buttons_frame)
    
    def _create_keyboard_section(self, parent: ctk.CTkFrame) -> None:
        """Create keyboard navigation settings section."""
        # Section frame
        keyboard_frame = ctk.CTkFrame(parent)
        keyboard_frame.pack(fill="x", pady=(0, 15))
        
        # Section title
        keyboard_title = ctk.CTkLabel(
            keyboard_frame,
            text="Keyboard Navigation",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        keyboard_title.pack(pady=(15, 10), anchor="w")
        
        # Enable keyboard navigation
        self.keyboard_nav_var = ctk.BooleanVar()
        keyboard_nav_check = ctk.CTkCheckBox(
            keyboard_frame,
            text="Enable keyboard navigation throughout the application",
            variable=self.keyboard_nav_var,
            command=self._on_keyboard_nav_changed
        )
        keyboard_nav_check.pack(pady=5, padx=20, anchor="w")
        
        # Tab navigation
        self.tab_nav_var = ctk.BooleanVar()
        tab_nav_check = ctk.CTkCheckBox(
            keyboard_frame,
            text="Enable Tab/Shift+Tab navigation between controls",
            variable=self.tab_nav_var
        )
        tab_nav_check.pack(pady=5, padx=40, anchor="w")
        
        # Arrow key navigation
        self.arrow_nav_var = ctk.BooleanVar()
        arrow_nav_check = ctk.CTkCheckBox(
            keyboard_frame,
            text="Enable arrow key navigation within control groups",
            variable=self.arrow_nav_var
        )
        arrow_nav_check.pack(pady=5, padx=40, anchor="w")
        
        # Focus indicator width
        focus_frame = ctk.CTkFrame(keyboard_frame)
        focus_frame.pack(fill="x", pady=10, padx=20)
        
        focus_label = ctk.CTkLabel(
            focus_frame,
            text="Focus indicator width (pixels):",
            font=ctk.CTkFont(size=12)
        )
        focus_label.pack(side="left", padx=(10, 5), pady=10)
        
        self.focus_width_var = ctk.IntVar()
        focus_slider = ctk.CTkSlider(
            focus_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            variable=self.focus_width_var
        )
        focus_slider.pack(side="left", fill="x", expand=True, padx=5, pady=10)
        
        focus_value_label = ctk.CTkLabel(
            focus_frame,
            textvariable=self.focus_width_var,
            font=ctk.CTkFont(size=12)
        )
        focus_value_label.pack(side="right", padx=(5, 10), pady=10)
    
    def _create_screen_reader_section(self, parent: ctk.CTkFrame) -> None:
        """Create screen reader settings section."""
        # Section frame
        screen_reader_frame = ctk.CTkFrame(parent)
        screen_reader_frame.pack(fill="x", pady=(0, 15))
        
        # Section title
        screen_reader_title = ctk.CTkLabel(
            screen_reader_frame,
            text="Screen Reader Support",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        screen_reader_title.pack(pady=(15, 10), anchor="w")
        
        # Enable screen reader
        self.screen_reader_var = ctk.BooleanVar()
        screen_reader_check = ctk.CTkCheckBox(
            screen_reader_frame,
            text="Enable screen reader announcements",
            variable=self.screen_reader_var,
            command=self._on_screen_reader_changed
        )
        screen_reader_check.pack(pady=5, padx=20, anchor="w")
        
        # Announce changes
        self.announce_changes_var = ctk.BooleanVar()
        announce_check = ctk.CTkCheckBox(
            screen_reader_frame,
            text="Announce UI changes and progress updates",
            variable=self.announce_changes_var
        )
        announce_check.pack(pady=5, padx=40, anchor="w")
        
        # Verbose descriptions
        self.verbose_descriptions_var = ctk.BooleanVar()
        verbose_check = ctk.CTkCheckBox(
            screen_reader_frame,
            text="Use verbose descriptions for complex elements",
            variable=self.verbose_descriptions_var
        )
        verbose_check.pack(pady=(5, 15), padx=40, anchor="w")
    
    def _create_visual_section(self, parent: ctk.CTkFrame) -> None:
        """Create visual accessibility settings section."""
        # Section frame
        visual_frame = ctk.CTkFrame(parent)
        visual_frame.pack(fill="x", pady=(0, 15))
        
        # Section title
        visual_title = ctk.CTkLabel(
            visual_frame,
            text="Visual Accessibility",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        visual_title.pack(pady=(15, 10), anchor="w")
        
        # High contrast mode
        self.high_contrast_var = ctk.BooleanVar()
        high_contrast_check = ctk.CTkCheckBox(
            visual_frame,
            text="Enable high contrast mode for better visibility",
            variable=self.high_contrast_var,
            command=self._on_high_contrast_changed
        )
        high_contrast_check.pack(pady=5, padx=20, anchor="w")
        
        # Font scaling
        font_frame = ctk.CTkFrame(visual_frame)
        font_frame.pack(fill="x", pady=10, padx=20)
        
        font_label = ctk.CTkLabel(
            font_frame,
            text="Font scale factor:",
            font=ctk.CTkFont(size=12)
        )
        font_label.pack(side="left", padx=(10, 5), pady=10)
        
        self.font_scale_var = ctk.DoubleVar()
        font_slider = ctk.CTkSlider(
            font_frame,
            from_=0.5,
            to=3.0,
            number_of_steps=25,
            variable=self.font_scale_var,
            command=self._on_font_scale_changed
        )
        font_slider.pack(side="left", fill="x", expand=True, padx=5, pady=10)
        
        font_value_label = ctk.CTkLabel(
            font_frame,
            text="1.0x",
            font=ctk.CTkFont(size=12)
        )
        font_value_label.pack(side="right", padx=(5, 10), pady=10)
        
        # Update font value label when slider changes
        def update_font_label(*args):
            font_value_label.configure(text=f"{self.font_scale_var.get():.1f}x")
        
        self.font_scale_var.trace("w", update_font_label)
        
        # Quick font size buttons
        font_buttons_frame = ctk.CTkFrame(visual_frame)
        font_buttons_frame.pack(fill="x", pady=(0, 15), padx=20)
        
        font_buttons_label = ctk.CTkLabel(
            font_buttons_frame,
            text="Quick font size:",
            font=ctk.CTkFont(size=12)
        )
        font_buttons_label.pack(side="left", padx=(10, 10), pady=10)
        
        small_button = ctk.CTkButton(
            font_buttons_frame,
            text="🔍 Small (0.8x)",
            command=lambda: self.font_scale_var.set(0.8),
            width=80
        )
        small_button.pack(side="left", padx=2, pady=10)
        
        normal_button = ctk.CTkButton(
            font_buttons_frame,
            text="📄 Normal (1.0x)",
            command=lambda: self.font_scale_var.set(1.0),
            width=80
        )
        normal_button.pack(side="left", padx=2, pady=10)
        
        large_button = ctk.CTkButton(
            font_buttons_frame,
            text="🔍 Large (1.5x)",
            command=lambda: self.font_scale_var.set(1.5),
            width=80
        )
        large_button.pack(side="left", padx=2, pady=10)
        
        xlarge_button = ctk.CTkButton(
            font_buttons_frame,
            text="🔍 X-Large (2.0x)",
            command=lambda: self.font_scale_var.set(2.0),
            width=80
        )
        xlarge_button.pack(side="left", padx=2, pady=10)
    
    def _create_audio_section(self, parent: ctk.CTkFrame) -> None:
        """Create audio feedback settings section."""
        # Section frame
        audio_frame = ctk.CTkFrame(parent)
        audio_frame.pack(fill="x", pady=(0, 15))
        
        # Section title
        audio_title = ctk.CTkLabel(
            audio_frame,
            text="Audio Feedback",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        audio_title.pack(pady=(15, 10), anchor="w")
        
        # Enable audio feedback
        self.audio_feedback_var = ctk.BooleanVar()
        audio_feedback_check = ctk.CTkCheckBox(
            audio_frame,
            text="Enable audio feedback for user interactions",
            variable=self.audio_feedback_var,
            command=self._on_audio_feedback_changed
        )
        audio_feedback_check.pack(pady=5, padx=20, anchor="w")
        
        # Button click sounds
        self.button_sound_var = ctk.BooleanVar()
        button_sound_check = ctk.CTkCheckBox(
            audio_frame,
            text="Play sound when buttons are clicked",
            variable=self.button_sound_var
        )
        button_sound_check.pack(pady=(5, 15), padx=40, anchor="w")
    
    def _create_action_buttons(self, parent: ctk.CTkFrame) -> None:
        """Create action buttons for the dialog."""
        # Button container
        button_container = ctk.CTkFrame(parent)
        button_container.pack(fill="x", padx=10, pady=10)
        
        # Apply button
        apply_button = ctk.CTkButton(
            button_container,
            text="✅ Apply (Ctrl+S)",
            command=self._on_apply,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2d8f47",
            hover_color="#1e6b35"
        )
        apply_button.pack(side="right", padx=(5, 0))
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            button_container,
            text="❌ Cancel (Escape)",
            command=self._on_cancel,
            font=ctk.CTkFont(size=12),
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        cancel_button.pack(side="right", padx=(5, 5))
        
        # Reset to defaults button
        reset_button = ctk.CTkButton(
            button_container,
            text="🔄 Reset to Defaults",
            command=self._on_reset_defaults,
            font=ctk.CTkFont(size=12),
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        reset_button.pack(side="left")
        
        # Test settings button
        test_button = ctk.CTkButton(
            button_container,
            text="🧪 Test Settings",
            command=self._on_test_settings,
            font=ctk.CTkFont(size=12),
            fg_color="#17a2b8",
            hover_color="#138496"
        )
        test_button.pack(side="left", padx=(5, 0))
    
    def _load_current_settings(self) -> None:
        """Load current accessibility settings into the dialog."""
        config = self.accessibility_manager.config
        
        self.keyboard_nav_var.set(config.enable_keyboard_navigation)
        self.tab_nav_var.set(config.tab_navigation)
        self.arrow_nav_var.set(config.arrow_key_navigation)
        self.screen_reader_var.set(config.enable_screen_reader)
        self.announce_changes_var.set(config.announce_changes)
        self.verbose_descriptions_var.set(config.verbose_descriptions)
        self.high_contrast_var.set(config.high_contrast_mode)
        self.font_scale_var.set(config.font_scale_factor)
        self.focus_width_var.set(config.focus_indicator_width)
        self.audio_feedback_var.set(config.enable_audio_feedback)
        self.button_sound_var.set(config.button_click_sound)
    
    def _on_keyboard_nav_changed(self) -> None:
        """Handle keyboard navigation toggle."""
        enabled = self.keyboard_nav_var.get()
        
        # Enable/disable dependent options
        if not enabled:
            self.tab_nav_var.set(False)
            self.arrow_nav_var.set(False)
    
    def _on_screen_reader_changed(self) -> None:
        """Handle screen reader toggle."""
        enabled = self.screen_reader_var.get()
        
        # Enable/disable dependent options
        if not enabled:
            self.announce_changes_var.set(False)
            self.verbose_descriptions_var.set(False)
    
    def _on_audio_feedback_changed(self) -> None:
        """Handle audio feedback toggle."""
        enabled = self.audio_feedback_var.get()
        
        # Enable/disable dependent options
        if not enabled:
            self.button_sound_var.set(False)
    
    def _on_high_contrast_changed(self) -> None:
        """Handle high contrast mode toggle with immediate preview."""
        enabled = self.high_contrast_var.get()
        
        if enabled:
            self.accessibility_manager.high_contrast.enable_high_contrast()
        else:
            self.accessibility_manager.high_contrast.disable_high_contrast()
    
    def _on_font_scale_changed(self, value: float) -> None:
        """Handle font scale change with immediate preview."""
        try:
            self.accessibility_manager.font_scaling.set_font_scale(value)
        except ValueError as e:
            self.logger.warning(f"Invalid font scale value: {e}")
    
    def _on_apply(self) -> None:
        """Apply the accessibility settings."""
        try:
            # Create new configuration
            new_config = AccessibilityConfig(
                enable_keyboard_navigation=self.keyboard_nav_var.get(),
                tab_navigation=self.tab_nav_var.get(),
                arrow_key_navigation=self.arrow_nav_var.get(),
                enable_screen_reader=self.screen_reader_var.get(),
                announce_changes=self.announce_changes_var.get(),
                verbose_descriptions=self.verbose_descriptions_var.get(),
                high_contrast_mode=self.high_contrast_var.get(),
                font_scale_factor=self.font_scale_var.get(),
                focus_indicator_width=self.focus_width_var.get(),
                enable_audio_feedback=self.audio_feedback_var.get(),
                button_click_sound=self.button_sound_var.get()
            )
            
            # Validate configuration
            new_config.validate()
            
            # Apply configuration
            self.accessibility_manager.update_config(new_config)
            
            # Announce success
            self.accessibility_manager.announce(
                "Accessibility settings applied successfully",
                priority="normal"
            )
            
            self.logger.info("Accessibility settings applied successfully")
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"Error applying accessibility settings: {e}")
            
            # Show error dialog
            from .error_handler import GUIErrorHandler
            GUIErrorHandler.show_error_dialog(
                self,
                "Settings Error",
                f"Failed to apply accessibility settings: {e}"
            )
    
    def _on_cancel(self) -> None:
        """Cancel changes and restore original settings."""
        try:
            # Restore original configuration
            self.accessibility_manager.update_config(self.original_config)
            
            self.logger.info("Accessibility settings changes cancelled")
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"Error cancelling accessibility settings: {e}")
            self.destroy()
    
    def _on_reset_defaults(self) -> None:
        """Reset all settings to default values."""
        try:
            # Create default configuration
            default_config = AccessibilityConfig()
            
            # Load defaults into dialog
            self.keyboard_nav_var.set(default_config.enable_keyboard_navigation)
            self.tab_nav_var.set(default_config.tab_navigation)
            self.arrow_nav_var.set(default_config.arrow_key_navigation)
            self.screen_reader_var.set(default_config.enable_screen_reader)
            self.announce_changes_var.set(default_config.announce_changes)
            self.verbose_descriptions_var.set(default_config.verbose_descriptions)
            self.high_contrast_var.set(default_config.high_contrast_mode)
            self.font_scale_var.set(default_config.font_scale_factor)
            self.focus_width_var.set(default_config.focus_indicator_width)
            self.audio_feedback_var.set(default_config.enable_audio_feedback)
            self.button_sound_var.set(default_config.button_click_sound)
            
            # Apply defaults immediately for preview
            self.accessibility_manager.update_config(default_config)
            
            self.logger.info("Accessibility settings reset to defaults")
            
        except Exception as e:
            self.logger.error(f"Error resetting accessibility settings: {e}")
    
    def _on_test_settings(self) -> None:
        """Test current accessibility settings."""
        try:
            # Create test dialog
            test_dialog = AccessibilityTestDialog(self, self.accessibility_manager)
            test_dialog.show()
            
        except Exception as e:
            self.logger.error(f"Error showing accessibility test dialog: {e}")
    
    def show(self) -> None:
        """Show the accessibility settings dialog."""
        self.deiconify()
        self.lift()
        self.focus_set()


class AccessibilityTestDialog(ctk.CTkToplevel):
    """
    Dialog for testing accessibility features.
    
    Provides a simple interface to test keyboard navigation,
    screen reader announcements, and visual enhancements.
    """
    
    def __init__(self, parent: ctk.CTkToplevel, accessibility_manager: AccessibilityManager):
        """Initialize the accessibility test dialog.
        
        Args:
            parent: Parent dialog
            accessibility_manager: Accessibility manager to test
        """
        super().__init__(parent)
        
        self.parent = parent
        self.accessibility_manager = accessibility_manager
        self.logger = logging.getLogger(__name__)
        
        self._setup_dialog()
        self._create_test_widgets()
    
    def _setup_dialog(self) -> None:
        """Set up the test dialog window properties."""
        self.title("Accessibility Test")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # Center the dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 250
        y = (self.winfo_screenheight() // 2) - 200
        self.geometry(f"500x400+{x}+{y}")
        
        # Make dialog modal
        self.transient(self.parent)
        self.grab_set()
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda e: self.destroy())
    
    def _create_test_widgets(self) -> None:
        """Create test widgets for accessibility features."""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Accessibility Feature Test",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        # Instructions
        instructions = ctk.CTkLabel(
            main_frame,
            text="Use Tab/Shift+Tab to navigate between controls.\n"
                 "Press Enter or Space to activate buttons.\n"
                 "Use arrow keys to navigate within groups.",
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        instructions.pack(pady=(0, 20))
        
        # Test buttons
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=10)
        
        test_button1 = ctk.CTkButton(
            buttons_frame,
            text="1️⃣ Test Button 1",
            command=lambda: self._test_announcement("Button 1 clicked")
        )
        test_button1.pack(side="left", padx=5, pady=10)
        
        test_button2 = ctk.CTkButton(
            buttons_frame,
            text="2️⃣ Test Button 2",
            command=lambda: self._test_announcement("Button 2 clicked")
        )
        test_button2.pack(side="left", padx=5, pady=10)
        
        test_button3 = ctk.CTkButton(
            buttons_frame,
            text="3️⃣ Test Button 3",
            command=lambda: self._test_announcement("Button 3 clicked")
        )
        test_button3.pack(side="left", padx=5, pady=10)
        
        # Test entry
        entry_frame = ctk.CTkFrame(main_frame)
        entry_frame.pack(fill="x", pady=10)
        
        entry_label = ctk.CTkLabel(
            entry_frame,
            text="Test Entry Field:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        entry_label.pack(side="left", padx=(10, 5), pady=10)
        
        test_entry = ctk.CTkEntry(
            entry_frame,
            placeholder_text="Type here to test keyboard input..."
        )
        test_entry.pack(side="right", fill="x", expand=True, padx=(5, 10), pady=10)
        
        # Test checkbox
        test_checkbox = ctk.CTkCheckBox(
            main_frame,
            text="Test checkbox (toggles high contrast)",
            command=self._test_high_contrast_toggle
        )
        test_checkbox.pack(pady=10)
        
        # Close button
        close_button = ctk.CTkButton(
            main_frame,
            text="✅ Close Test (Escape)",
            command=self.destroy,
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        close_button.pack(pady=20)
        
        # Register widgets for accessibility
        if self.accessibility_manager:
            for widget in [test_button1, test_button2, test_button3, test_entry, test_checkbox, close_button]:
                self.accessibility_manager.register_widget(widget)
    
    def _test_announcement(self, message: str) -> None:
        """Test screen reader announcement.
        
        Args:
            message: Message to announce
        """
        if self.accessibility_manager:
            self.accessibility_manager.announce(message, priority="normal")
    
    def _test_high_contrast_toggle(self) -> None:
        """Test high contrast mode toggle."""
        if self.accessibility_manager:
            self.accessibility_manager.high_contrast.toggle_high_contrast()
            
            mode = "enabled" if self.accessibility_manager.high_contrast.high_contrast_enabled else "disabled"
            self.accessibility_manager.announce(f"High contrast mode {mode}", priority="normal")
    
    def show(self) -> None:
        """Show the accessibility test dialog."""
        self.deiconify()
        self.lift()
        self.focus_set()