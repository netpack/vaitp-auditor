"""
Main Review Window for VAITP-Auditor GUI.

This module provides the primary review interface with a three-row layout
for code comparison and verdict capture.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Dict, Any, Callable
from ..core.models import CodePair
from .models import GUIConfig, ProgressInfo, VerdictButtonConfig, get_default_verdict_buttons
from .accessibility import AccessibilityManager, AccessibilityConfig, create_accessibility_manager


class HeaderFrame(ctk.CTkFrame):
    """Header frame containing progress information and current file display."""
    
    def __init__(self, parent, accessibility_manager: Optional[AccessibilityManager] = None, **kwargs):
        """Initialize header frame with progress display components."""
        super().__init__(parent, **kwargs)
        
        # Store current progress state
        self._current_progress: Optional[ProgressInfo] = None
        self.accessibility_manager = accessibility_manager
        
        # Configure grid layout for header components
        self.grid_columnconfigure(0, weight=0)  # Current file (left)
        self.grid_columnconfigure(1, weight=1)  # Progress bar (center, expanding)
        self.grid_columnconfigure(2, weight=0)  # Progress text (right)
        
        # Current file label
        self.current_file_label = ctk.CTkLabel(
            self,
            text="No file loaded",
            font=ctk.CTkFont(size=12, weight="normal"),
            anchor="w"
        )
        self.current_file_label.grid(row=0, column=0, padx=(10, 20), pady=10, sticky="w")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=0, column=1, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0.0)
        
        # Progress text label
        self.progress_text_label = ctk.CTkLabel(
            self,
            text="0/0 (0.0%)",
            font=ctk.CTkFont(size=12, weight="normal"),
            anchor="e"
        )
        self.progress_text_label.grid(row=0, column=2, padx=(20, 10), pady=10, sticky="e")
        
        # Register widgets for accessibility
        if self.accessibility_manager:
            self.accessibility_manager.register_widget(
                self.current_file_label,
                label="Current file being reviewed",
                description="Shows the name of the file currently being reviewed"
            )
            self.accessibility_manager.register_widget(
                self.progress_bar,
                label="Review progress",
                description="Visual progress bar showing completion percentage"
            )
            self.accessibility_manager.register_widget(
                self.progress_text_label,
                label="Progress text",
                description="Text showing current progress as numbers and percentage"
            )
    
    def update_progress(self, progress_info: ProgressInfo) -> None:
        """Update progress display with new information.
        
        Args:
            progress_info: ProgressInfo object containing current progress state
        """
        # Validate input
        if not isinstance(progress_info, ProgressInfo):
            raise ValueError("progress_info must be a ProgressInfo instance")
        
        # Store current progress state
        self._current_progress = progress_info
        
        # Update current file display
        status_text = progress_info.get_status_text()
        self.current_file_label.configure(text=status_text)
        
        # Update progress bar (ensure value is between 0.0 and 1.0)
        progress_value = max(0.0, min(1.0, progress_info.percentage / 100.0))
        self.progress_bar.set(progress_value)
        
        # Update progress text
        progress_text = progress_info.get_progress_text()
        self.progress_text_label.configure(text=progress_text)
        
        # Announce progress update to screen readers
        if self.accessibility_manager:
            self.accessibility_manager.announce_progress(
                progress_info.current,
                progress_info.total,
                progress_info.current_file
            )
    
    def get_current_progress(self) -> Optional[ProgressInfo]:
        """Get the current progress information.
        
        Returns:
            Current ProgressInfo object or None if no progress has been set
        """
        return self._current_progress
    
    def reset_progress(self) -> None:
        """Reset progress display to initial state."""
        self._current_progress = None
        self.current_file_label.configure(text="No file loaded")
        self.progress_bar.set(0.0)
        self.progress_text_label.configure(text="0/0 (0.0%)")
    
    def set_loading_state(self, message: str = "Loading...") -> None:
        """Set header to loading state with optional message.
        
        Args:
            message: Loading message to display
        """
        self.current_file_label.configure(text=message)
        self.progress_bar.set(0.0)
        self.progress_text_label.configure(text="Preparing...")
    
    def set_completion_state(self, experiment_name: str) -> None:
        """Set header to completion state.
        
        Args:
            experiment_name: Name of the completed experiment
        """
        self.current_file_label.configure(text=f"Review Complete - {experiment_name}")
        self.progress_bar.set(1.0)
        self.progress_text_label.configure(text="100% Complete")
    
    def set_static_progress(self, text: str) -> None:
        """Set static progress text (temporary method for minimal implementation).
        
        Args:
            text: Static progress text to display
            
        Note:
            This method is deprecated and should be replaced with update_progress()
        """
        self.current_file_label.configure(text="Sample File")
        self.progress_bar.set(0.5)
        self.progress_text_label.configure(text=text)


class CodePanelsFrame(ctk.CTkFrame):
    """Frame containing side-by-side code display panels."""
    
    def __init__(self, parent, accessibility_manager: Optional[AccessibilityManager] = None, **kwargs):
        """Initialize code panels frame with three text display areas."""
        super().__init__(parent, **kwargs)
        self.accessibility_manager = accessibility_manager
        
        # Configure grid layout for three panels: Expected (top-left), Generated (top-right), Input (bottom)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Top text boxes expand
        self.grid_rowconfigure(3, weight=1)  # Bottom text box expands
        
        # Expected code label and panel
        self.expected_label = ctk.CTkLabel(
            self,
            text="Expected Code",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.expected_label.grid(row=0, column=0, padx=(10, 5), pady=(10, 5), sticky="w")
        
        self.expected_textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="none"
        )
        self.expected_textbox.grid(row=1, column=0, padx=(10, 5), pady=(0, 10), sticky="nsew")
        
        # Generated code label and panel
        self.generated_label = ctk.CTkLabel(
            self,
            text="Generated Code",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.generated_label.grid(row=0, column=1, padx=(5, 10), pady=(10, 5), sticky="w")
        
        self.generated_textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="none"
        )
        self.generated_textbox.grid(row=1, column=1, padx=(5, 10), pady=(0, 5), sticky="nsew")
        
        # Input code label and panel (spans both columns)
        self.input_label = ctk.CTkLabel(
            self,
            text="Input Code (Original)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.input_label.grid(row=2, column=0, columnspan=2, padx=10, pady=(5, 5), sticky="w")
        
        self.input_textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="none",
            height=150  # Smaller height for input panel
        )
        self.input_textbox.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="nsew")
        
        # Register widgets for accessibility
        if self.accessibility_manager:
            self.accessibility_manager.register_widget(
                self.expected_textbox,
                label="Expected code panel",
                description="Text area showing the expected code for comparison. Use arrow keys to scroll when focused.",
                tab_order=1
            )
            self.accessibility_manager.register_widget(
                self.generated_textbox,
                label="Generated code panel",
                description="Text area showing the generated code for review. Use arrow keys to scroll when focused.",
                tab_order=2
            )
            self.accessibility_manager.register_widget(
                self.input_textbox,
                label="Input code panel",
                description="Text area showing the original input code. Use arrow keys to scroll when focused.",
                tab_order=3
            )
            
            # Setup keyboard navigation for code panels
            self._setup_code_panel_navigation()
        
        # Set initial placeholder content
        self.set_placeholder_content()
    
    def _setup_code_panel_navigation(self) -> None:
        """Setup keyboard navigation for code panels."""
        try:
            # Bind arrow keys for scrolling when panels have focus
            def bind_textbox_navigation(textbox):
                # Vertical scrolling
                textbox.bind("<Up>", lambda e: self._scroll_code_panel(textbox, "up"))
                textbox.bind("<Down>", lambda e: self._scroll_code_panel(textbox, "down"))
                textbox.bind("<Page_Up>", lambda e: self._scroll_code_panel(textbox, "page_up"))
                textbox.bind("<Page_Down>", lambda e: self._scroll_code_panel(textbox, "page_down"))
                
                # Horizontal scrolling
                textbox.bind("<Left>", lambda e: self._scroll_code_panel(textbox, "left"))
                textbox.bind("<Right>", lambda e: self._scroll_code_panel(textbox, "right"))
                
                # Home/End navigation
                textbox.bind("<Home>", lambda e: self._scroll_code_panel(textbox, "home"))
                textbox.bind("<End>", lambda e: self._scroll_code_panel(textbox, "end"))
                textbox.bind("<Control-Home>", lambda e: self._scroll_code_panel(textbox, "top"))
                textbox.bind("<Control-End>", lambda e: self._scroll_code_panel(textbox, "bottom"))
            
            for textbox in [self.expected_textbox, self.generated_textbox, self.input_textbox]:
                bind_textbox_navigation(textbox)
                
        except Exception as e:
            if self.accessibility_manager:
                self.accessibility_manager.logger.error(f"Error setting up code panel navigation: {e}")
    
    def _scroll_code_panel(self, textbox: ctk.CTkTextbox, direction: str) -> str:
        """Handle keyboard scrolling in code panels.
        
        Args:
            textbox: The textbox to scroll
            direction: Direction to scroll
            
        Returns:
            "break" to prevent default behavior
        """
        try:
            if direction == "up":
                textbox.see("insert-1l")
            elif direction == "down":
                textbox.see("insert+1l")
            elif direction == "page_up":
                textbox.see("insert-10l")
            elif direction == "page_down":
                textbox.see("insert+10l")
            elif direction == "left":
                textbox.see("insert-1c")
            elif direction == "right":
                textbox.see("insert+1c")
            elif direction == "home":
                textbox.see("insert linestart")
            elif direction == "end":
                textbox.see("insert lineend")
            elif direction == "top":
                textbox.see("1.0")
            elif direction == "bottom":
                textbox.see("end")
            
            return "break"
            
        except Exception as e:
            if self.accessibility_manager:
                self.accessibility_manager.logger.error(f"Error scrolling code panel: {e}")
            return "continue"
    
    def set_placeholder_content(self) -> None:
        """Set placeholder content for initial display."""
        placeholder_text = "# No code loaded\n# Use the Setup Wizard to configure a session"
        
        self.expected_textbox.delete("1.0", "end")
        self.expected_textbox.insert("1.0", placeholder_text)
        
        self.generated_textbox.delete("1.0", "end")
        self.generated_textbox.insert("1.0", placeholder_text)
        
        self.input_textbox.delete("1.0", "end")
        self.input_textbox.insert("1.0", placeholder_text)
    
    def load_code_pair(self, code_pair: CodePair) -> None:
        """Load a code pair into the display panels."""
        # Clear existing content
        self.expected_textbox.delete("1.0", "end")
        self.generated_textbox.delete("1.0", "end")
        self.input_textbox.delete("1.0", "end")
        
        # Load expected code
        if code_pair.expected_code:
            self.expected_textbox.insert("1.0", code_pair.expected_code)
        else:
            self.expected_textbox.insert("1.0", "# No expected code available")
        
        # Load generated code
        if code_pair.generated_code:
            self.generated_textbox.insert("1.0", code_pair.generated_code)
        else:
            self.generated_textbox.insert("1.0", "# No generated code available")
        
        # Load input code
        if code_pair.input_code:
            self.input_textbox.insert("1.0", code_pair.input_code)
        else:
            self.input_textbox.insert("1.0", "# No input code available")
    
    def clear_content(self) -> None:
        """Clear all content from all panels."""
        self.expected_textbox.delete("1.0", "end")
        self.generated_textbox.delete("1.0", "end")
        self.input_textbox.delete("1.0", "end")
    
    def apply_syntax_highlighting(self, code_pair: CodePair) -> None:
        """Apply syntax highlighting to the code panels.
        
        Args:
            code_pair: Code pair containing the code to highlight
        """
        try:
            # Configure text tags for syntax highlighting
            self._configure_syntax_tags()
            
            # Apply basic Python syntax highlighting
            if code_pair.expected_code:
                self._highlight_python_syntax(self.expected_textbox, code_pair.expected_code)
            
            if code_pair.generated_code:
                self._highlight_python_syntax(self.generated_textbox, code_pair.generated_code)
            
            if code_pair.input_code:
                self._highlight_python_syntax(self.input_textbox, code_pair.input_code)
                
        except Exception as e:
            # Syntax highlighting is optional, don't fail if it doesn't work
            pass
    
    def apply_diff_highlighting(self, diff_lines, gui_config=None) -> None:
        """Apply diff highlighting to show differences between expected and generated code only.
        
        Args:
            diff_lines: List of DiffLine objects from CodeDiffer for expected vs generated
            gui_config: Optional GUIConfig to check if diff highlighting is enabled
        """
        try:
            # Check if diff highlighting is enabled
            if gui_config and not gui_config.enable_diff_highlighting:
                return
            
            # Configure text tags for diff highlighting
            self._configure_diff_tags()
            
            # Clear any existing diff highlighting
            self._clear_diff_highlighting()
            
            # Apply expected-generated diff highlighting only
            if diff_lines:
                self._apply_expected_generated_diff_highlighting(diff_lines)
            
        except Exception as e:
            # Diff highlighting is optional, don't fail if it doesn't work
            pass
    
    def _configure_syntax_tags(self) -> None:
        """Configure text tags for syntax highlighting."""
        # Python keywords
        for textbox in [self.expected_textbox, self.generated_textbox]:
            textbox.tag_config("keyword", foreground="#569CD6")  # Blue
            textbox.tag_config("string", foreground="#CE9178")   # Orange
            textbox.tag_config("comment", foreground="#6A9955")  # Green
            textbox.tag_config("number", foreground="#B5CEA8")   # Light green
    
    def _configure_diff_tags(self) -> None:
        """Configure text tags for diff highlighting with subtle colors."""
        # Subtle diff highlighting colors for expected-generated comparison only
        for textbox in [self.expected_textbox, self.generated_textbox]:
            textbox.tag_config("diff_added", background="#E8F5E8", foreground="#2D5A2D")    # Light green background
            textbox.tag_config("diff_removed", background="#F5E8E8", foreground="#5A2D2D")  # Light red background
            textbox.tag_config("diff_changed", background="#FFF8DC", foreground="#5A5A2D") # Light yellow background
    
    def _highlight_python_syntax(self, textbox, code: str) -> None:
        """Apply basic Python syntax highlighting to a textbox.
        
        Args:
            textbox: The textbox widget to highlight
            code: The code content to analyze
        """
        import re
        
        # Python keywords
        keywords = r'\b(def|class|if|elif|else|for|while|try|except|finally|with|import|from|as|return|yield|break|continue|pass|raise|assert|del|global|nonlocal|lambda|and|or|not|in|is|True|False|None)\b'
        
        # Find and highlight keywords
        for match in re.finditer(keywords, code):
            start_line = code[:match.start()].count('\n') + 1
            start_char = match.start() - code.rfind('\n', 0, match.start()) - 1
            end_line = code[:match.end()].count('\n') + 1
            end_char = match.end() - code.rfind('\n', 0, match.end()) - 1
            
            textbox.tag_add("keyword", f"{start_line}.{start_char}", f"{end_line}.{end_char}")
        
        # Highlight strings
        string_pattern = r'(["\'])(?:(?=(\\?))\2.)*?\1'
        for match in re.finditer(string_pattern, code):
            start_line = code[:match.start()].count('\n') + 1
            start_char = match.start() - code.rfind('\n', 0, match.start()) - 1
            end_line = code[:match.end()].count('\n') + 1
            end_char = match.end() - code.rfind('\n', 0, match.end()) - 1
            
            textbox.tag_add("string", f"{start_line}.{start_char}", f"{end_line}.{end_char}")
        
        # Highlight comments
        comment_pattern = r'#.*$'
        for match in re.finditer(comment_pattern, code, re.MULTILINE):
            start_line = code[:match.start()].count('\n') + 1
            start_char = match.start() - code.rfind('\n', 0, match.start()) - 1
            end_line = code[:match.end()].count('\n') + 1
            end_char = match.end() - code.rfind('\n', 0, match.end()) - 1
            
            textbox.tag_add("comment", f"{start_line}.{start_char}", f"{end_line}.{end_char}")
    

    
    def _clear_diff_highlighting(self) -> None:
        """Clear all existing diff highlighting from text boxes."""
        try:
            # Clear expected-generated diff tags only
            for textbox in [self.expected_textbox, self.generated_textbox]:
                textbox.tag_remove("diff_added", "1.0", "end")
                textbox.tag_remove("diff_removed", "1.0", "end")
                textbox.tag_remove("diff_changed", "1.0", "end")
        except Exception:
            pass
    
    def _apply_expected_generated_diff_highlighting(self, diff_lines) -> None:
        """Apply diff highlighting between expected and generated code only.
        
        Args:
            diff_lines: List of DiffLine objects from CodeDiffer (not used directly)
        """
        try:
            # Get the actual content from expected and generated textboxes
            expected_content = self.expected_textbox.get("1.0", "end-1c")
            generated_content = self.generated_textbox.get("1.0", "end-1c")
            expected_lines = expected_content.split('\n')
            generated_lines = generated_content.split('\n')
            
            # Use difflib to get a more accurate line-by-line comparison
            import difflib
            matcher = difflib.SequenceMatcher(None, expected_lines, generated_lines)
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    # Lines are identical, no highlighting needed
                    continue
                
                elif tag == 'delete':
                    # Lines removed from expected code
                    for i in range(i1, i2):
                        line_num = i + 1
                        if line_num <= len(expected_lines):
                            self.expected_textbox.tag_add("diff_removed", 
                                                        f"{line_num}.0", f"{line_num}.end")
                
                elif tag == 'insert':
                    # Lines added in generated code
                    for j in range(j1, j2):
                        line_num = j + 1
                        if line_num <= len(generated_lines):
                            self.generated_textbox.tag_add("diff_added", 
                                                         f"{line_num}.0", f"{line_num}.end")
                
                elif tag == 'replace':
                    # Lines modified - highlight both sides
                    for i in range(i1, i2):
                        line_num = i + 1
                        if line_num <= len(expected_lines):
                            self.expected_textbox.tag_add("diff_changed", 
                                                        f"{line_num}.0", f"{line_num}.end")
                    
                    for j in range(j1, j2):
                        line_num = j + 1
                        if line_num <= len(generated_lines):
                            self.generated_textbox.tag_add("diff_changed", 
                                                         f"{line_num}.0", f"{line_num}.end")
                        
        except Exception as e:
            # If diff highlighting fails, just continue without it
            pass


class ActionsFrame(ctk.CTkFrame):
    """Frame containing verdict buttons and control actions."""
    
    def __init__(self, parent, verdict_callback=None, undo_callback=None, quit_callback=None, 
                 accessibility_manager: Optional[AccessibilityManager] = None, **kwargs):
        """Initialize actions frame with verdict buttons and controls.
        
        Args:
            parent: Parent widget
            verdict_callback: Callback function for verdict selection (verdict_id, comment)
            undo_callback: Callback function for undo requests
            quit_callback: Callback function for quit requests
            accessibility_manager: Accessibility manager for enhanced features
        """
        super().__init__(parent, **kwargs)
        self.accessibility_manager = accessibility_manager
        
        # Store callbacks
        self.verdict_callback = verdict_callback
        self.undo_callback = undo_callback
        self.quit_callback = quit_callback
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)  # Verdict buttons area
        self.grid_columnconfigure(1, weight=0)  # Comment and controls area
        
        # Create verdict buttons frame
        self.verdict_frame = ctk.CTkFrame(self)
        self.verdict_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        
        # Create comment and controls frame
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ns")
        
        # Initialize verdict buttons
        self.verdict_buttons = {}
        self.verdict_configs = {}
        self.key_bindings = {}
        self._create_verdict_buttons()
        
        # Initialize comment field and control buttons
        self._create_controls()
        
        # Setup keyboard bindings
        self._setup_keyboard_bindings()
    
    def _create_verdict_buttons(self) -> None:
        """Create verdict buttons using VerdictButtonConfig-based implementation."""
        # Get default verdict button configurations
        button_configs = get_default_verdict_buttons()
        
        # Configure grid for buttons (2 rows, 3 columns)
        for i in range(3):
            self.verdict_frame.grid_columnconfigure(i, weight=1)
        
        # Create buttons in a 2x3 grid
        for idx, config in enumerate(button_configs):
            row = idx // 3
            col = idx % 3
            
            # Store configuration for reference
            self.verdict_configs[config.verdict_id] = config
            
            # Determine button colors based on theme
            button_colors = self._get_button_colors(config.color_theme)
            
            # Get icon for this verdict
            icon = self._get_verdict_icon(config.verdict_id)
            
            # Create button with enhanced styling and icon
            button = ctk.CTkButton(
                self.verdict_frame,
                text=f"{icon} {config.get_display_with_shortcut()}",
                command=lambda v=config.verdict_id: self._on_verdict_clicked(v),
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=button_colors["fg_color"],
                hover_color=button_colors["hover_color"],
                text_color=button_colors["text_color"]
            )
            button.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            
            # Add tooltip if available
            if config.tooltip:
                self._add_tooltip(button, config.tooltip)
            
            # Store button and key binding
            self.verdict_buttons[config.verdict_id] = button
            self.key_bindings[config.key_binding.lower()] = config.verdict_id
    
    def _get_verdict_icon(self, verdict_id: str) -> str:
        """Get icon for verdict button.
        
        Args:
            verdict_id: Verdict identifier
            
        Returns:
            Icon string for the verdict
        """
        from .icon_utils import get_verdict_icon
        return get_verdict_icon(verdict_id)
    
    def _get_button_colors(self, color_theme: str) -> Dict[str, str]:
        """Get button colors based on theme.
        
        Args:
            color_theme: Color theme name
            
        Returns:
            Dictionary with fg_color, hover_color, and text_color
        """
        color_schemes = {
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
            "default": {
                "fg_color": None,  # Use CustomTkinter default
                "hover_color": None,
                "text_color": None
            }
        }
        
        return color_schemes.get(color_theme, color_schemes["default"])
    
    def _get_theme_color(self, color_theme: str) -> str:
        """Get the primary color for a theme.
        
        Args:
            color_theme: Color theme name
            
        Returns:
            Primary color for the theme
        """
        colors = self._get_button_colors(color_theme)
        return colors["fg_color"] or "#1f538d"  # Default CustomTkinter blue
    
    def _get_theme_hover_color(self, color_theme: str) -> str:
        """Get the hover color for a theme.
        
        Args:
            color_theme: Color theme name
            
        Returns:
            Hover color for the theme
        """
        colors = self._get_button_colors(color_theme)
        return colors["hover_color"] or "#14375e"  # Default CustomTkinter hover blue
    
    def _add_tooltip(self, widget, tooltip_text: str) -> None:
        """Add tooltip to widget (placeholder implementation).
        
        Args:
            widget: Widget to add tooltip to
            tooltip_text: Tooltip text to display
            
        Note:
            This is a placeholder implementation. In a full implementation,
            you would use a proper tooltip library or custom tooltip widget.
        """
        # Store tooltip text as widget attribute for testing
        widget._tooltip_text = tooltip_text
    
    def _setup_keyboard_bindings(self) -> None:
        """Setup keyboard bindings for verdict buttons."""
        try:
            # Bind to parent window for global keyboard shortcuts
            parent = self.winfo_toplevel() if hasattr(self, 'winfo_toplevel') else self
            
            # Bind each key to its corresponding verdict
            for key, verdict_id in self.key_bindings.items():
                try:
                    parent.bind(f"<Key-{key}>", lambda event, v=verdict_id: self._on_key_pressed(v))
                except:
                    # Fallback for testing environment
                    pass
        except:
            # Complete fallback for testing environment
            pass
    
    def _on_key_pressed(self, verdict_id: str) -> None:
        """Handle keyboard shortcut for verdict selection.
        
        Args:
            verdict_id: ID of the verdict to select
        """
        # Check if keyboard shortcuts are enabled
        if not getattr(self, '_shortcuts_enabled', True):
            return  # Don't process shortcuts when comment field has focus
        
        # Only process if button is enabled
        if verdict_id in self.verdict_buttons:
            button = self.verdict_buttons[verdict_id]
            if button.cget("state") != "disabled":
                self._on_verdict_clicked(verdict_id)
    
    def _create_controls(self) -> None:
        """Create enhanced comment field and control buttons."""
        # Configure controls frame grid
        self.controls_frame.grid_rowconfigure(1, weight=1)  # Comment field expands
        
        # Comment label
        comment_label = ctk.CTkLabel(
            self.controls_frame,
            text="Comment:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        comment_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Enhanced comment entry field with proper clearing behavior
        self.comment_entry = ctk.CTkEntry(
            self.controls_frame,
            placeholder_text="Add an optional comment...",
            width=300
        )
        self.comment_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Bind Enter key to submit current verdict (if any button is focused)
        self.comment_entry.bind("<Return>", self._on_comment_enter)
        
        # Bind focus events to properly manage keyboard shortcuts
        self.comment_entry.bind("<FocusIn>", self._on_comment_focus_in)
        self.comment_entry.bind("<FocusOut>", self._on_comment_focus_out)
        
        # Track keyboard shortcut state
        self._shortcuts_enabled = True
        
        # Control buttons frame
        buttons_frame = ctk.CTkFrame(self.controls_frame)
        buttons_frame.grid(row=2, column=0, padx=10, pady=(10, 10), sticky="ew")
        
        # Enhanced Undo Last button with proper styling
        self.undo_button = ctk.CTkButton(
            buttons_frame,
            text="↶️ Undo Last (u)",
            command=self._on_undo_clicked,
            font=ctk.CTkFont(size=11),
            width=120,
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        self.undo_button.grid(row=0, column=0, padx=(0, 5), pady=5)
        
        # Enhanced Quit Session button with proper styling
        self.quit_button = ctk.CTkButton(
            buttons_frame,
            text="🛑 Quit Session (q)",
            command=self._on_quit_clicked,
            font=ctk.CTkFont(size=11),
            width=120,
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.quit_button.grid(row=0, column=1, padx=(5, 0), pady=5)
        
        # Setup additional keyboard bindings for control buttons
        self._setup_control_key_bindings()
    
    def _setup_control_key_bindings(self) -> None:
        """Setup keyboard bindings for control buttons."""
        try:
            parent = self.winfo_toplevel() if hasattr(self, 'winfo_toplevel') else self
            
            try:
                # Bind 'u' key for undo
                parent.bind("<Key-u>", lambda event: self._on_undo_key_pressed())
                # Bind 'q' key for quit
                parent.bind("<Key-q>", lambda event: self._on_quit_key_pressed())
            except:
                # Fallback for testing environment
                pass
        except:
            # Complete fallback for testing environment
            pass
    
    def _on_undo_key_pressed(self) -> None:
        """Handle undo key press with shortcut state checking."""
        # Check if keyboard shortcuts are enabled
        if not getattr(self, '_shortcuts_enabled', True):
            return  # Don't process shortcuts when comment field has focus
        
        self._on_undo_clicked()
    
    def _on_quit_key_pressed(self) -> None:
        """Handle quit key press with shortcut state checking."""
        # Check if keyboard shortcuts are enabled
        if not getattr(self, '_shortcuts_enabled', True):
            return  # Don't process shortcuts when comment field has focus
        
        self._on_quit_clicked()
    
    def _on_comment_focus_in(self, event) -> None:
        """Handle comment field gaining focus - disable keyboard shortcuts."""
        self._shortcuts_enabled = False
    
    def _on_comment_focus_out(self, event) -> None:
        """Handle comment field losing focus - enable keyboard shortcuts."""
        self._shortcuts_enabled = True
    
    def _on_comment_enter(self, event) -> None:
        """Handle Enter key press in comment field.
        
        Args:
            event: Key event
        """
        # This could be enhanced to submit the last selected verdict
        # For now, just move focus away from the comment field
        self.focus_set()
    
    def _on_verdict_clicked(self, verdict_id: str) -> None:
        """Handle verdict button click with enhanced functionality.
        
        Args:
            verdict_id: ID of the selected verdict
        """
        # Prevent double-clicks by disabling all verdict buttons immediately
        self.set_verdict_buttons_enabled(False)
        
        # Get comment text and validate
        comment, is_valid, error_msg = self.get_validated_comment()
        
        # If comment validation fails, show error and re-enable buttons
        if not is_valid:
            # Re-enable buttons immediately
            self.set_verdict_buttons_enabled(True)
            
            # Show error message (in a real implementation, this would use a proper dialog)
            print(f"Comment validation error: {error_msg}")
            return
        
        # Provide visual feedback - briefly change button state to show which was clicked
        if verdict_id in self.verdict_buttons:
            button = self.verdict_buttons[verdict_id]
            
            # Store original colors for restoration
            try:
                original_fg_color = button.cget("fg_color")
                original_hover_color = button.cget("hover_color")
                
                # Set active state colors (lighter feedback instead of dark)
                button.configure(
                    fg_color="#4a9eff",  # Light blue active color
                    hover_color="#4a9eff"
                )
                
                # Schedule restoration of original colors and re-enabling after processing
                def restore_button_state():
                    try:
                        # Ensure button still exists before configuring
                        if button.winfo_exists():
                            button.configure(
                                fg_color=original_fg_color,
                                hover_color=original_hover_color
                            )
                        # Re-enable verdict buttons after processing is complete
                        self.set_verdict_buttons_enabled(True)
                    except Exception:
                        # Fallback: just re-enable buttons even if color restoration fails
                        self.set_verdict_buttons_enabled(True)
                
                # Schedule restoration after 150ms for visual feedback
                self.after(150, restore_button_state)
                
            except Exception:
                # If color handling fails, just re-enable buttons
                self.after(150, lambda: self.set_verdict_buttons_enabled(True))
        else:
            # If button not found, still re-enable after delay
            self.after(150, lambda: self.set_verdict_buttons_enabled(True))
        
        # Clear comment field immediately after reading it
        self.clear_comment()
        
        # Call the verdict callback if provided
        if self.verdict_callback:
            try:
                self.verdict_callback(verdict_id, comment)
            except Exception as e:
                # If callback fails, ensure buttons are re-enabled
                self.set_verdict_buttons_enabled(True)
                raise e
        else:
            # Fallback for testing/standalone mode
            print(f"Verdict selected: {verdict_id}, Comment: '{comment}'")
    
    def _on_undo_clicked(self) -> None:
        """Handle undo button click with enhanced functionality and state validation."""
        # Check if undo button is currently enabled
        if self.undo_button.cget("state") == "disabled":
            return  # Ignore click if button is disabled
        
        # Disable undo button immediately to prevent double-clicks
        self.undo_button.configure(state="disabled")
        
        # Also disable verdict buttons during undo processing
        self.set_verdict_buttons_enabled(False)
        
        # Provide visual feedback with color change
        original_fg_color = self.undo_button.cget("fg_color")
        original_hover_color = self.undo_button.cget("hover_color")
        
        # Set processing state colors
        self.undo_button.configure(
            fg_color="#4a4a4a",  # Darker gray for processing
            hover_color="#4a4a4a"
        )
        
        def restore_button_state(success: bool = True):
            """Restore button state after undo processing."""
            try:
                # Restore original colors
                self.undo_button.configure(
                    fg_color=original_fg_color,
                    hover_color=original_hover_color
                )
                
                # Re-enable verdict buttons
                self.set_verdict_buttons_enabled(True)
                
                # Undo button state will be managed by the controller based on session state
                # Don't automatically re-enable it here
            except:
                # Fallback in case button is destroyed
                pass
        
        # Call the undo callback if provided
        if self.undo_callback:
            try:
                self.undo_callback()
                # Schedule restoration after brief delay for visual feedback
                self.after(200, lambda: restore_button_state(True))
            except Exception as e:
                # If callback fails, restore state and re-enable buttons
                self.after(200, lambda: restore_button_state(False))
                raise e
        else:
            # Fallback for testing/standalone mode
            print("Undo requested")
            self.after(200, lambda: restore_button_state(True))
    
    def _on_quit_clicked(self) -> None:
        """Handle quit button click with enhanced functionality and confirmation."""
        # Check if quit button is currently enabled
        if self.quit_button.cget("state") == "disabled":
            return  # Ignore click if button is disabled
        
        # Disable quit button immediately to prevent double-clicks
        self.quit_button.configure(state="disabled")
        
        # Provide visual feedback with color change
        original_fg_color = self.quit_button.cget("fg_color")
        original_hover_color = self.quit_button.cget("hover_color")
        
        # Set processing state colors
        self.quit_button.configure(
            fg_color="#8b0000",  # Darker red for processing
            hover_color="#8b0000"
        )
        
        def restore_button_state():
            """Restore button state if quit is cancelled."""
            try:
                self.quit_button.configure(
                    fg_color=original_fg_color,
                    hover_color=original_hover_color,
                    state="normal"
                )
            except:
                # Fallback in case button is destroyed
                pass
        
        # Call the quit callback if provided
        if self.quit_callback:
            try:
                # The callback will handle confirmation dialog and actual quit
                self.quit_callback()
                # If we reach here and window still exists, quit was cancelled
                self.after(200, restore_button_state)
            except Exception as e:
                # If callback fails, restore state
                self.after(200, restore_button_state)
                raise e
        else:
            # Fallback for testing/standalone mode
            print("Quit requested")
            self.after(200, restore_button_state)
    
    def get_comment(self) -> str:
        """Get current comment text."""
        return self.comment_entry.get()
    
    def clear_comment(self) -> None:
        """Clear the comment field with proper behavior."""
        try:
            # For CustomTkinter, try using the set method if available
            if hasattr(self.comment_entry, 'set'):
                self.comment_entry.set("")
            else:
                # Fallback to delete method
                self.comment_entry.delete(0, "end")
            
            # Don't set focus back to comment field to allow fast reviewing
            # Users can click on comment field if they want to add a comment
        except Exception as e:
            # Log error but don't fail the operation
            pass
    
    def validate_comment(self, comment: str) -> tuple[bool, str]:
        """Validate comment input.
        
        Args:
            comment: Comment text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation - comments are optional, so empty is valid
        if not comment:
            return True, ""
        
        # Check for reasonable length (prevent extremely long comments)
        if len(comment) > 1000:
            return False, "Comment is too long (maximum 1000 characters)"
        
        # Check for potentially problematic characters
        if '\x00' in comment:
            return False, "Comment contains invalid null characters"
        
        return True, ""
    
    def get_validated_comment(self) -> tuple[str, bool, str]:
        """Get and validate the current comment.
        
        Returns:
            Tuple of (comment, is_valid, error_message)
        """
        comment = self.get_comment().strip()
        is_valid, error_msg = self.validate_comment(comment)
        return comment, is_valid, error_msg
    
    def set_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable all verdict and control buttons."""
        for button in self.verdict_buttons.values():
            button.configure(state="normal" if enabled else "disabled")
        
        self.undo_button.configure(state="normal" if enabled else "disabled")
        self.quit_button.configure(state="normal" if enabled else "disabled")
    
    def set_verdict_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable only verdict buttons (keep control buttons enabled)."""
        for button in self.verdict_buttons.values():
            button.configure(state="normal" if enabled else "disabled")
    
    def set_undo_enabled(self, enabled: bool) -> None:
        """Enable or disable the undo button based on session state."""
        self.undo_button.configure(state="normal" if enabled else "disabled")
    
    def set_processing_state(self, processing: bool) -> None:
        """Set the UI to processing state to prevent user interaction during operations.
        
        Args:
            processing: True to disable interactions, False to re-enable
        """
        if processing:
            # Disable all interactive elements during processing
            self.set_verdict_buttons_enabled(False)
            self.undo_button.configure(state="disabled")
            self.quit_button.configure(state="disabled")
            self.comment_entry.configure(state="disabled")
        else:
            # Re-enable elements (verdict buttons will be managed by session state)
            # Only re-enable comment entry and quit button unconditionally
            self.comment_entry.configure(state="normal")
            self.quit_button.configure(state="normal")
            # Undo and verdict buttons will be managed by the controller based on session state
    
    def show_verdict_feedback(self, verdict_id: str, success: bool) -> None:
        """Show visual feedback for verdict submission result.
        
        Args:
            verdict_id: The verdict that was submitted
            success: Whether the submission was successful
        """
        if verdict_id not in self.verdict_buttons:
            return
        
        button = self.verdict_buttons[verdict_id]
        
        try:
            # Get original colors from the verdict config to ensure proper restoration
            verdict_config = self.verdict_configs.get(verdict_id)
            if verdict_config:
                # Use theme-based colors for restoration
                original_fg = self._get_theme_color(verdict_config.color_theme)
                original_hover = self._get_theme_hover_color(verdict_config.color_theme)
            else:
                # Fallback to current colors
                original_fg = button.cget("fg_color")
                original_hover = button.cget("hover_color")
            
            if success:
                # Green feedback for success
                feedback_color = "#28a745"
            else:
                # Red feedback for failure
                feedback_color = "#dc3545"
            
            # Apply feedback color
            button.configure(
                fg_color=feedback_color,
                hover_color=feedback_color
            )
            
            # Schedule restoration of original colors
            def restore_colors():
                try:
                    if button.winfo_exists():
                        button.configure(
                            fg_color=original_fg,
                            hover_color=original_hover
                        )
                except Exception:
                    pass
            
            self.after(400, restore_colors)  # Feedback duration for success/failure
            
        except Exception:
            # If feedback fails, silently continue - don't break the UI
            pass
    
    def get_verdict_config(self, verdict_id: str) -> Optional[VerdictButtonConfig]:
        """Get the configuration for a specific verdict button.
        
        Args:
            verdict_id: ID of the verdict button
            
        Returns:
            VerdictButtonConfig if found, None otherwise
        """
        return self.verdict_configs.get(verdict_id)
    
    def simulate_key_press(self, key: str) -> bool:
        """Simulate a key press for testing purposes.
        
        Args:
            key: Key to simulate
            
        Returns:
            True if key was handled, False otherwise
        """
        key_lower = key.lower()
        
        # Handle verdict keys
        if key_lower in self.key_bindings:
            verdict_id = self.key_bindings[key_lower]
            if verdict_id in self.verdict_buttons:
                button = self.verdict_buttons[verdict_id]
                if button.cget("state") != "disabled":
                    self._on_verdict_clicked(verdict_id)
                    return True
        
        # Handle control keys
        if key_lower == 'u' and self.undo_button.cget("state") != "disabled":
            self._on_undo_clicked()
            return True
        elif key_lower == 'q' and self.quit_button.cget("state") != "disabled":
            self._on_quit_clicked()
            return True
        
        return False


class MainReviewContent(ctk.CTkFrame):
    """Main review content frame that can be embedded in any parent window."""
    
    def __init__(self, parent, gui_config: Optional[GUIConfig] = None, 
                 verdict_callback: Optional[Callable] = None,
                 undo_callback: Optional[Callable] = None,
                 quit_callback: Optional[Callable] = None,
                 save_callback: Optional[Callable] = None,
                 open_callback: Optional[Callable] = None,
                 restart_callback: Optional[Callable] = None,
                 accessibility_manager: Optional[AccessibilityManager] = None,
                 **kwargs):
        """Initialize main review content frame with three-row layout.
        
        Args:
            parent: Parent widget
            gui_config: GUI configuration settings
            verdict_callback: Callback for verdict selection (verdict_id, comment)
            undo_callback: Callback for undo requests
            quit_callback: Callback for quit requests
            save_callback: Callback for save requests
            open_callback: Callback for open requests
            restart_callback: Callback for restart requests
            accessibility_manager: Accessibility manager for enhanced features
        """
        super().__init__(parent, **kwargs)
        
        # Store configuration and callbacks
        self.gui_config = gui_config or GUIConfig()
        self.verdict_callback = verdict_callback
        self.undo_callback = undo_callback
        self.quit_callback = quit_callback
        self.save_callback = save_callback
        self.open_callback = open_callback
        self.restart_callback = restart_callback
        self.accessibility_manager = accessibility_manager
        
        # Pack to fill parent
        self.pack(fill="both", expand=True)
        
        # Setup layout
        self.setup_layout()
        
        # Set initial state
        self.set_placeholder_state()
    
    def setup_layout(self) -> None:
        """Setup the three-row grid layout structure."""
        # Configure main frame grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header (fixed height)
        self.grid_rowconfigure(1, weight=1)  # Main content (expanding)
        self.grid_rowconfigure(2, weight=0)  # Actions (fixed height)
        
        # Create header frame
        self.header_frame = HeaderFrame(self, accessibility_manager=self.accessibility_manager, height=60)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        
        # Create code panels frame
        self.code_panels_frame = CodePanelsFrame(self, accessibility_manager=self.accessibility_manager)
        self.code_panels_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Create actions frame with callbacks
        self.actions_frame = ActionsFrame(
            self, 
            verdict_callback=self.verdict_callback,
            undo_callback=self.undo_callback,
            quit_callback=self.quit_callback,
            accessibility_manager=self.accessibility_manager,
            height=120
        )
        self.actions_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))
    
    def set_placeholder_state(self) -> None:
        """Set initial placeholder state for the frame."""
        # Reset progress to initial state
        self.header_frame.reset_progress()
        
        # Code panels already have placeholder content from initialization
        
        # Disable buttons initially
        self.actions_frame.set_buttons_enabled(False)
    
    def load_code_pair(self, code_pair: CodePair) -> None:
        """Load a code pair for review."""
        self.code_panels_frame.load_code_pair(code_pair)
        self.actions_frame.set_buttons_enabled(True)
    
    def update_progress(self, progress_info: ProgressInfo) -> None:
        """Update progress display.
        
        Args:
            progress_info: ProgressInfo object containing current progress state
        """
        # Validate input
        if not isinstance(progress_info, ProgressInfo):
            raise ValueError("progress_info must be a ProgressInfo instance")
        
        # Update header frame
        self.header_frame.update_progress(progress_info)
    
    def get_current_progress(self) -> Optional[ProgressInfo]:
        """Get current progress information from header frame.
        
        Returns:
            Current ProgressInfo object or None if no progress has been set
        """
        return self.header_frame.get_current_progress()
    
    def set_loading_state(self, message: str = "Loading session...") -> None:
        """Set frame to loading state.
        
        Args:
            message: Loading message to display
        """
        self.header_frame.set_loading_state(message)
        
        # Disable actions during loading
        self.actions_frame.set_buttons_enabled(False)
    
    def clear_loading_state(self) -> None:
        """Clear loading state and return to normal operation."""
        self.header_frame.clear_loading_state()
        
        # Re-enable actions after loading
        self.actions_frame.set_buttons_enabled(True)
    
    def get_comment_text(self) -> str:
        """Get current comment text from actions frame.
        
        Returns:
            Current comment text
        """
        return self.actions_frame.get_comment()
    
    def clear_comment_text(self) -> None:
        """Clear comment text in actions frame."""
        self.actions_frame.clear_comment()
    
    def set_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable verdict buttons.
        
        Args:
            enabled: Whether to enable buttons
        """
        self.actions_frame.set_buttons_enabled(enabled)
    
    def focus_comment_area(self) -> None:
        """Focus the comment text area."""
        self.actions_frame.comment_entry.focus_set()
    
    def get_accessibility_manager(self) -> Optional[AccessibilityManager]:
        """Get the accessibility manager instance.
        
        Returns:
            AccessibilityManager instance or None
        """
        return self.accessibility_manager
    
    def set_completion_state(self, experiment_name: str) -> None:
        """Set frame to completion state.
        
        Args:
            experiment_name: Name of the completed experiment
        """
        self.header_frame.set_completion_state(experiment_name)
        
        # Disable verdict buttons but keep control buttons enabled
        for button in self.actions_frame.verdict_buttons.values():
            button.configure(state="disabled")
    
    def clear_content(self) -> None:
        """Clear all content and reset to placeholder state."""
        self.code_panels_frame.clear_content()
        self.actions_frame.clear_comment()
        self.set_placeholder_state()
    
    def get_comment(self) -> str:
        """Get current comment text."""
        return self.actions_frame.get_comment()
    
    def clear_comment(self) -> None:
        """Clear comment field."""
        self.actions_frame.clear_comment()
    
    def set_verdict_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable only verdict buttons."""
        self.actions_frame.set_verdict_buttons_enabled(enabled)
    
    def set_undo_enabled(self, enabled: bool) -> None:
        """Enable or disable the undo button based on session state."""
        self.actions_frame.set_undo_enabled(enabled)
    
    def set_processing_state(self, processing: bool) -> None:
        """Set the UI to processing state to prevent user interaction during operations."""
        self.actions_frame.set_processing_state(processing)
    
    def show_verdict_feedback(self, verdict_id: str, success: bool) -> None:
        """Show visual feedback for verdict submission result."""
        self.actions_frame.show_verdict_feedback(verdict_id, success)


class MainReviewWindow(ctk.CTk):
    """Main review window for code comparison and verdict capture."""
    
    def __init__(self, gui_config: Optional[GUIConfig] = None, 
                 verdict_callback: Optional[Callable] = None,
                 undo_callback: Optional[Callable] = None,
                 quit_callback: Optional[Callable] = None,
                 save_callback: Optional[Callable] = None,
                 open_callback: Optional[Callable] = None,
                 restart_callback: Optional[Callable] = None):
        """Initialize main review window with three-row layout.
        
        Args:
            gui_config: GUI configuration settings
            verdict_callback: Callback for verdict selection (verdict_id, comment)
            undo_callback: Callback for undo requests
            quit_callback: Callback for quit requests
            save_callback: Callback for save requests
            open_callback: Callback for open requests
            restart_callback: Callback for restart requests
        """
        super().__init__()
        
        # Store configuration and callbacks
        self.gui_config = gui_config or GUIConfig()
        self.verdict_callback = verdict_callback
        self.undo_callback = undo_callback
        self.quit_callback = quit_callback
        self.save_callback = save_callback
        self.open_callback = open_callback
        self.restart_callback = restart_callback
        
        # Configure window
        self.title("VAITP-Auditor - Main Review")
        self.geometry(f"{self.gui_config.window_width}x{self.gui_config.window_height}")
        self.minsize(800, 600)
        
        # Setup menu bar
        self.setup_menu()
        
        # Setup layout
        self.setup_layout()
        
        # Set initial state
        self.set_placeholder_state()
    
    def setup_menu(self) -> None:
        """Setup the menu bar."""
        # Create menu bar
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Create File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Review Process", command=self.save_review_process, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Open Review Process...", command=self.open_review_process, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Restart Review Process", command=self.restart_review_process, accelerator="Ctrl+R")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_application, accelerator="Ctrl+Q")
        
        # Create Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about_dialog)
        
        # Bind keyboard shortcuts
        self.bind_all("<Control-s>", lambda e: self.save_review_process())
        self.bind_all("<Control-o>", lambda e: self.open_review_process())
        self.bind_all("<Control-r>", lambda e: self.restart_review_process())
        self.bind_all("<Control-q>", lambda e: self.quit_application())
    
    def show_about_dialog(self) -> None:
        """Show the About dialog."""
        try:
            from .about_dialog import show_about_dialog
            show_about_dialog(self)
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
    
    def save_review_process(self) -> None:
        """Save the current review process."""
        if self.save_callback:
            self.save_callback()
        else:
            import tkinter.messagebox as messagebox
            messagebox.showwarning(
                "Save Review Process",
                "Save functionality is not available.\n"
                "No save callback has been configured."
            )
    
    def open_review_process(self) -> None:
        """Open another review process."""
        if self.open_callback:
            self.open_callback()
        else:
            import tkinter.messagebox as messagebox
            messagebox.showwarning(
                "Open Review Process",
                "Open functionality is not available.\n"
                "No open callback has been configured."
            )
    
    def restart_review_process(self) -> None:
        """Restart the current review process."""
        if self.restart_callback:
            self.restart_callback()
        else:
            import tkinter.messagebox as messagebox
            messagebox.showwarning(
                "Restart Review Process",
                "Restart functionality is not available.\n"
                "No restart callback has been configured."
            )
    
    def quit_application(self) -> None:
        """Quit the application."""
        if self.quit_callback:
            self.quit_callback()
        else:
            self.destroy()
    
    def setup_layout(self) -> None:
        """Setup the three-row grid layout structure."""
        # Configure main window grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header (fixed height)
        self.grid_rowconfigure(1, weight=1)  # Main content (expanding)
        self.grid_rowconfigure(2, weight=0)  # Actions (fixed height)
        
        # Create header frame
        self.header_frame = HeaderFrame(self, height=60)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        
        # Create code panels frame
        self.code_panels_frame = CodePanelsFrame(self)
        self.code_panels_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Create actions frame with callbacks
        self.actions_frame = ActionsFrame(
            self, 
            verdict_callback=self.verdict_callback,
            undo_callback=self.undo_callback,
            quit_callback=self.quit_callback,
            height=120
        )
        self.actions_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))
    
    def set_placeholder_state(self) -> None:
        """Set initial placeholder state for the window."""
        # Reset progress to initial state
        self.header_frame.reset_progress()
        
        # Code panels already have placeholder content from initialization
        
        # Disable buttons initially
        self.actions_frame.set_buttons_enabled(False)
    
    def load_code_pair(self, code_pair: CodePair) -> None:
        """Load a code pair for review."""
        self.code_panels_frame.load_code_pair(code_pair)
        self.actions_frame.set_buttons_enabled(True)
    
    def update_progress(self, progress_info: ProgressInfo) -> None:
        """Update progress display.
        
        Args:
            progress_info: ProgressInfo object containing current progress state
        """
        # Validate input
        if not isinstance(progress_info, ProgressInfo):
            raise ValueError("progress_info must be a ProgressInfo instance")
        
        # Update header frame
        self.header_frame.update_progress(progress_info)
        
        # Update window title with experiment name
        self.title(f"VAITP-Auditor - Reviewing: {progress_info.experiment_name}")
    
    def get_current_progress(self) -> Optional[ProgressInfo]:
        """Get current progress information from header frame.
        
        Returns:
            Current ProgressInfo object or None if no progress has been set
        """
        return self.header_frame.get_current_progress()
    
    def set_loading_state(self, message: str = "Loading session...") -> None:
        """Set window to loading state.
        
        Args:
            message: Loading message to display
        """
        self.header_frame.set_loading_state(message)
        self.title("VAITP-Auditor - Loading...")
        
        # Disable actions during loading
        self.actions_frame.set_buttons_enabled(False)
    
    def set_completion_state(self, experiment_name: str) -> None:
        """Set window to completion state.
        
        Args:
            experiment_name: Name of the completed experiment
        """
        self.header_frame.set_completion_state(experiment_name)
        self.title(f"VAITP-Auditor - Complete: {experiment_name}")
        
        # Disable verdict buttons but keep control buttons enabled
        for button in self.actions_frame.verdict_buttons.values():
            button.configure(state="disabled")
    
    def clear_content(self) -> None:
        """Clear all content and reset to placeholder state."""
        self.code_panels_frame.clear_content()
        self.actions_frame.clear_comment()
        self.set_placeholder_state()
    
    def get_comment(self) -> str:
        """Get current comment text."""
        return self.actions_frame.get_comment()
    
    def clear_comment(self) -> None:
        """Clear comment field."""
        self.actions_frame.clear_comment()
    
    def set_verdict_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable only verdict buttons."""
        self.actions_frame.set_verdict_buttons_enabled(enabled)
    
    def set_undo_enabled(self, enabled: bool) -> None:
        """Enable or disable the undo button based on session state."""
        self.actions_frame.set_undo_enabled(enabled)
    
    def set_processing_state(self, processing: bool) -> None:
        """Set the UI to processing state to prevent user interaction during operations."""
        self.actions_frame.set_processing_state(processing)
    
    def show_verdict_feedback(self, verdict_id: str, success: bool) -> None:
        """Show visual feedback for verdict submission result."""
        self.actions_frame.show_verdict_feedback(verdict_id, success)
    
    def validate_comment(self) -> tuple[bool, str]:
        """Validate the current comment.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        comment, is_valid, error_msg = self.actions_frame.get_validated_comment()
        return is_valid, error_msg
    
    def simulate_key_press(self, key: str) -> bool:
        """Simulate a key press for testing purposes.
        
        Args:
            key: Key to simulate
            
        Returns:
            True if key was handled, False otherwise
        """
        return self.actions_frame.simulate_key_press(key)
    
    def get_verdict_config(self, verdict_id: str) -> Optional[VerdictButtonConfig]:
        """Get the configuration for a specific verdict button.
        
        Args:
            verdict_id: ID of the verdict button
            
        Returns:
            VerdictButtonConfig if found, None otherwise
        """
        return self.actions_frame.get_verdict_config(verdict_id)


def main():
    """Test function for the main review window."""
    # Set appearance mode and color theme
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    
    # Create and run the window
    app = MainReviewWindow()
    app.mainloop()


if __name__ == "__main__":
    main()