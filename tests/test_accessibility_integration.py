"""
Integration tests for accessibility features with GUI components.

This module tests the integration of accessibility features with the main
GUI application components including setup wizard, main review window,
and session controller.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    ctk = None

from vaitp_auditor.gui.accessibility import AccessibilityManager, AccessibilityConfig
from vaitp_auditor.gui.gui_app import GUIApplication


@unittest.skipUnless(CTK_AVAILABLE, "CustomTkinter not available")
class TestAccessibilityGUIIntegration(unittest.TestCase):
    """Test accessibility integration with main GUI components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_root = Mock(spec=ctk.CTk)
        self.mock_root.bind = Mock()
        self.mock_root.title = Mock(return_value="Test Window")
        self.mock_root.after = Mock()
        self.mock_root.winfo_children = Mock(return_value=[])
        self.mock_root.winfo_screenwidth = Mock(return_value=1920)
        self.mock_root.winfo_screenheight = Mock(return_value=1080)
        self.mock_root.update_idletasks = Mock()
        self.mock_root.geometry = Mock()
        self.mock_root.iconify = Mock()
        self.mock_root.protocol = Mock()
        self.mock_root.mainloop = Mock()
        self.mock_root.quit = Mock()
        self.mock_root.destroy = Mock()
    
    @patch('vaitp_auditor.gui.gui_app.ctk.CTk')
    @patch('vaitp_auditor.gui.gui_app.ctk.set_appearance_mode')
    @patch('vaitp_auditor.gui.gui_app.ctk.set_default_color_theme')
    def test_gui_application_accessibility_initialization(self, mock_theme, mock_appearance, mock_ctk):
        """Test that GUI application properly initializes accessibility features."""
        # Mock the CTk constructor to return our mock root
        mock_ctk.return_value = self.mock_root
        
        # Create GUI application
        app = GUIApplication()
        
        # Mock the setup wizard to avoid actual GUI creation
        with patch.object(app, 'launch_setup_wizard') as mock_launch_wizard:
            # Start the application (but don't actually run mainloop)
            self.mock_root.mainloop = Mock()  # Override to prevent actual GUI loop
            
            try:
                app.run()
            except Exception:
                pass  # Expected since we're mocking
            
            # Verify accessibility manager was created
            self.assertIsNotNone(app.accessibility_manager)
            self.assertIsInstance(app.accessibility_manager, AccessibilityManager)
            
            # Verify accessibility configuration
            config = app.accessibility_manager.config
            self.assertIsInstance(config, AccessibilityConfig)
            self.assertTrue(config.enable_keyboard_navigation)
            self.assertTrue(config.enable_screen_reader)
    
    def test_accessibility_manager_widget_registration(self):
        """Test that accessibility manager can register GUI widgets."""
        accessibility_manager = AccessibilityManager(self.mock_root)
        
        # Create mock GUI widgets
        mock_button = Mock(spec=ctk.CTkButton)
        mock_button.bind = Mock()
        mock_entry = Mock(spec=ctk.CTkEntry)
        mock_entry.bind = Mock()
        mock_textbox = Mock(spec=ctk.CTkTextbox)
        mock_textbox.bind = Mock()
        
        # Register widgets
        accessibility_manager.register_widget(
            mock_button,
            label="Test Button",
            description="A test button for accessibility testing"
        )
        
        accessibility_manager.register_widget(
            mock_entry,
            label="Test Entry",
            description="A test entry field"
        )
        
        accessibility_manager.register_widget(
            mock_textbox,
            label="Test Textbox",
            description="A test text area"
        )
        
        # Verify widgets were registered
        self.assertIn(mock_button, accessibility_manager.keyboard_nav.focus_order)
        self.assertIn(mock_entry, accessibility_manager.keyboard_nav.focus_order)
        self.assertIn(mock_textbox, accessibility_manager.keyboard_nav.focus_order)
        
        # Verify labels were set
        self.assertEqual(mock_button._accessible_label, "Test Button")
        self.assertEqual(mock_entry._accessible_label, "Test Entry")
        self.assertEqual(mock_textbox._accessible_label, "Test Textbox")
    
    def test_accessibility_keyboard_shortcuts_integration(self):
        """Test that accessibility keyboard shortcuts work with GUI application."""
        accessibility_manager = AccessibilityManager(self.mock_root)
        
        # Verify global shortcuts were bound
        bind_calls = [call[0][0] for call in self.mock_root.bind.call_args_list]
        
        # Check for essential accessibility shortcuts
        accessibility_shortcuts = [
            "<Control-plus>",    # Increase font size
            "<Control-minus>",   # Decrease font size
            "<Control-0>",       # Reset font size
            "<Control-Shift-H>", # Toggle high contrast
            "<Alt-a>",           # Accessibility settings
            "<F1>",              # Help
            "<Tab>",             # Tab navigation
            "<Shift-Tab>",       # Reverse tab navigation
        ]
        
        for shortcut in accessibility_shortcuts:
            self.assertIn(shortcut, bind_calls, f"Accessibility shortcut {shortcut} not bound")
    
    def test_accessibility_screen_reader_integration(self):
        """Test screen reader integration with GUI workflow."""
        accessibility_manager = AccessibilityManager(self.mock_root)
        
        # Test typical GUI workflow announcements
        workflow_steps = [
            ("Application started", "normal"),
            ("Setup wizard opened", "normal"),
            ("Data source selected", "normal"),
            ("Configuration completed", "normal"),
            ("Review session started", "normal"),
            ("Verdict selected: SUCCESS", "normal"),
            ("Progress: 5 of 10 (50%)", "low"),
            ("Review completed", "high"),
        ]
        
        for message, priority in workflow_steps:
            accessibility_manager.announce(message, priority=priority)
        
        # Enable screen reader for testing
        accessibility_manager.screen_reader.announcements_enabled = True
        
        # Make announcements again with screen reader enabled, including high priority
        for message, priority in workflow_steps:  # Test all announcements including high priority
            accessibility_manager.announce(message, priority=priority)
        
        # Verify announcements were made
        self.assertTrue(self.mock_root.title.called)
        self.assertTrue(self.mock_root.after.called)
        
        # Check that high priority announcements include ALERT prefix
        title_calls = [call[0][0] for call in self.mock_root.title.call_args_list if call[0]]
        alert_calls = [call for call in title_calls if "ALERT:" in call]
        self.assertTrue(len(alert_calls) > 0, "High priority announcements should include ALERT prefix")
    
    def test_accessibility_visual_enhancements_integration(self):
        """Test visual accessibility enhancements integration."""
        accessibility_manager = AccessibilityManager(self.mock_root)
        
        # Test font scaling
        initial_scale = accessibility_manager.font_scaling.current_scale
        self.assertEqual(initial_scale, 1.0)
        
        # Test font size increase
        accessibility_manager.font_scaling.increase_font_size(0.2)
        self.assertEqual(accessibility_manager.font_scaling.current_scale, 1.2)
        
        # Test font size decrease
        accessibility_manager.font_scaling.decrease_font_size(0.1)
        self.assertEqual(accessibility_manager.font_scaling.current_scale, 1.1)
        
        # Test reset
        accessibility_manager.font_scaling.reset_font_size()
        self.assertEqual(accessibility_manager.font_scaling.current_scale, 1.0)
        
        # Test high contrast mode
        self.assertFalse(accessibility_manager.high_contrast.high_contrast_enabled)
        
        with patch('vaitp_auditor.gui.accessibility.ctk.set_appearance_mode') as mock_set_appearance:
            accessibility_manager.high_contrast.enable_high_contrast()
            self.assertTrue(accessibility_manager.high_contrast.high_contrast_enabled)
            mock_set_appearance.assert_called_with("dark")
            
            accessibility_manager.high_contrast.disable_high_contrast()
            self.assertFalse(accessibility_manager.high_contrast.high_contrast_enabled)
            mock_set_appearance.assert_called_with("system")
    
    def test_accessibility_error_handling_integration(self):
        """Test accessibility integration with error handling."""
        from vaitp_auditor.gui.error_handler import GUIErrorHandler
        
        # Test that error dialogs are accessible
        with patch('vaitp_auditor.gui.error_handler.messagebox.showerror') as mock_error:
            GUIErrorHandler.show_error_dialog(
                self.mock_root,
                "Accessibility Test Error",
                "This is a test error for accessibility validation",
                "Detailed error information for screen readers"
            )
            
            # Verify error dialog was called with proper format
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            
            # Check that error message includes both summary and details
            self.assertEqual(call_args[0], "Accessibility Test Error")
            message = call_args[1]
            self.assertIn("This is a test error for accessibility validation", message)
            self.assertIn("Details:", message)
            self.assertIn("Detailed error information for screen readers", message)
    
    def test_accessibility_configuration_persistence(self):
        """Test that accessibility configuration changes persist correctly."""
        accessibility_manager = AccessibilityManager(self.mock_root)
        
        # Create new configuration
        new_config = AccessibilityConfig(
            enable_keyboard_navigation=True,
            enable_screen_reader=True,
            high_contrast_mode=True,
            font_scale_factor=1.5,
            focus_indicator_width=5
        )
        
        # Apply configuration
        with patch.object(accessibility_manager.high_contrast, 'enable_high_contrast') as mock_enable:
            with patch.object(accessibility_manager.font_scaling, 'set_font_scale') as mock_scale:
                accessibility_manager.update_config(new_config)
                
                # Verify configuration was applied
                self.assertEqual(accessibility_manager.config, new_config)
                mock_enable.assert_called_once()
                mock_scale.assert_called_with(1.5)
    
    def test_accessibility_cleanup_integration(self):
        """Test proper cleanup of accessibility resources."""
        accessibility_manager = AccessibilityManager(self.mock_root)
        
        # Set up some state
        accessibility_manager.high_contrast.high_contrast_enabled = True
        accessibility_manager.font_scaling.current_scale = 1.5
        
        # Add widgets
        mock_widget = Mock(spec=ctk.CTkButton)
        mock_widget.bind = Mock()
        accessibility_manager.register_widget(mock_widget)
        
        # Verify widget is registered
        self.assertIn(mock_widget, accessibility_manager.keyboard_nav.focus_order)
        
        # Test cleanup
        with patch.object(accessibility_manager.high_contrast, 'disable_high_contrast') as mock_disable:
            with patch.object(accessibility_manager.font_scaling, 'reset_font_size') as mock_reset:
                initial_focus_count = len(accessibility_manager.keyboard_nav.focus_order)
                accessibility_manager.cleanup()
                
                # Verify cleanup was performed
                mock_disable.assert_called_once()
                mock_reset.assert_called_once()
                
                # Verify we had widgets before cleanup
                self.assertTrue(initial_focus_count > 0)


@unittest.skipUnless(CTK_AVAILABLE, "CustomTkinter not available")
class TestAccessibilityRequirementsCompliance(unittest.TestCase):
    """Test compliance with specific accessibility requirements."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_root = Mock(spec=ctk.CTk)
        self.mock_root.bind = Mock()
        self.mock_root.title = Mock(return_value="Test Window")
        self.mock_root.after = Mock()
        self.mock_root.winfo_children = Mock(return_value=[])
    
    def test_requirement_8_8_complete_implementation(self):
        """Test complete implementation of requirement 8.8."""
        # Requirement 8.8: WHEN accessibility features are needed THEN the system 
        # SHALL support keyboard navigation and screen reader compatibility
        
        accessibility_manager = AccessibilityManager(self.mock_root)
        
        # Test keyboard navigation support
        self.assertTrue(accessibility_manager.config.enable_keyboard_navigation)
        self.assertIsNotNone(accessibility_manager.keyboard_nav)
        
        # Test that keyboard navigation can be used
        mock_widget = Mock(spec=ctk.CTkButton)
        mock_widget.bind = Mock()
        mock_widget.winfo_exists = Mock(return_value=True)
        mock_widget.cget = Mock(return_value="normal")
        mock_widget.focus_set = Mock()
        
        accessibility_manager.register_widget(mock_widget)
        self.assertIn(mock_widget, accessibility_manager.keyboard_nav.focus_order)
        
        # Test screen reader compatibility
        self.assertIsNotNone(accessibility_manager.screen_reader)
        
        # Enable screen reader announcements for testing
        accessibility_manager.screen_reader.announcements_enabled = True
        
        # Test announcement functionality
        accessibility_manager.announce("Test announcement")
        self.mock_root.title.assert_called()
        
        # Test widget labeling for screen readers
        accessibility_manager.screen_reader.set_widget_label(mock_widget, "Test Button")
        self.assertEqual(mock_widget._accessible_label, "Test Button")
    
    def test_requirement_8_9_complete_implementation(self):
        """Test complete implementation of requirement 8.9."""
        # Requirement 8.9: ALL user-facing error messages SHALL be presented in 
        # standardized modal dialog boxes with clear error summary and optional details section
        
        from vaitp_auditor.gui.error_handler import GUIErrorHandler
        
        # Test error dialog with details
        with patch('vaitp_auditor.gui.error_handler.messagebox.showerror') as mock_error:
            GUIErrorHandler.show_error_dialog(
                self.mock_root,
                "Test Error Title",
                "Clear error summary message",
                "Optional detailed error information"
            )
            
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            
            # Verify standardized format
            self.assertEqual(call_args[0], "Test Error Title")  # Title
            message = call_args[1]
            self.assertIn("Clear error summary message", message)  # Summary
            self.assertIn("Details:", message)  # Details section header
            self.assertIn("Optional detailed error information", message)  # Details content
        
        # Test error dialog without details
        with patch('vaitp_auditor.gui.error_handler.messagebox.showerror') as mock_error:
            GUIErrorHandler.show_error_dialog(
                self.mock_root,
                "Simple Error",
                "Simple error message"
            )
            
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            
            # Verify format without details
            self.assertEqual(call_args[0], "Simple Error")
            self.assertEqual(call_args[1], "Simple error message")
        
        # Test confirmation dialog
        with patch('vaitp_auditor.gui.error_handler.messagebox.askyesno') as mock_confirm:
            mock_confirm.return_value = True
            
            result = GUIErrorHandler.show_confirmation_dialog(
                self.mock_root,
                "Confirm Action",
                "Are you sure?"
            )
            
            mock_confirm.assert_called_once()
            self.assertTrue(result)
        
        # Test info dialog
        with patch('vaitp_auditor.gui.error_handler.messagebox.showinfo') as mock_info:
            GUIErrorHandler.show_info_dialog(
                self.mock_root,
                "Information",
                "Informational message"
            )
            
            mock_info.assert_called_once()


if __name__ == '__main__':
    unittest.main()