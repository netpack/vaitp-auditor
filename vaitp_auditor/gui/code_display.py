"""
Code display components with syntax highlighting and diff visualization.

This module provides enhanced code panels with syntax highlighting using Pygments
and diff highlighting for visual code comparison, with performance optimizations.
"""

import customtkinter as ctk
from typing import List, Tuple, Optional, Dict, Any
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import get_formatter_by_name
from pygments.util import ClassNotFound
from pygments.token import Token
import re
import time

from ..core.models import DiffLine
from .performance_optimizer import (
    get_performance_optimizer, LazyCodeLoader, 
    performance_optimized
)


class SyntaxHighlighter:
    """Handles syntax highlighting using Pygments with performance optimizations."""
    
    def __init__(self):
        """Initialize the syntax highlighter."""
        self._lexer_cache = {}
        self._token_style_cache = {}
        self.performance_optimizer = get_performance_optimizer()
        
        # Define color mappings for different token types
        self._token_colors = {
            Token.Keyword: "#569cd6",           # Blue for keywords
            Token.String: "#ce9178",            # Orange for strings
            Token.Comment: "#6a9955",           # Green for comments
            Token.Number: "#b5cea8",            # Light green for numbers
            Token.Operator: "#d4d4d4",          # Light gray for operators
            Token.Name.Function: "#dcdcaa",     # Yellow for functions
            Token.Name.Class: "#4ec9b0",        # Cyan for classes
            Token.Name.Builtin: "#569cd6",      # Blue for builtins
            Token.Name.Exception: "#4ec9b0",    # Cyan for exceptions
            Token.Literal: "#d69d85",           # Light orange for literals
            Token.Error: "#f44747",             # Red for errors
        }
    
    @performance_optimized("syntax_highlighting")
    def highlight_code(self, code: str, language: str = "python") -> List[Tuple[str, str]]:
        """
        Highlight code and return list of (text, color) tuples with caching.
        
        Args:
            code: Code content to highlight
            language: Programming language (default: python)
            
        Returns:
            List of (text_content, color) tuples for text insertion
        """
        if not code.strip():
            return [("", "#d4d4d4")]  # Default text color
        
        # Check cache first
        cached_result = self.performance_optimizer.optimize_syntax_highlighting(code, language)
        if cached_result is not None:
            return cached_result
        
        try:
            # Get or create lexer
            lexer = self._get_lexer(language, code)
            
            # Tokenize the code
            tokens = list(lexer.get_tokens(code))
            
            # Convert tokens to (text, color) tuples
            highlighted_parts = []
            for token_type, text in tokens:
                color = self._get_token_color(token_type)
                highlighted_parts.append((text, color))
            
            # Cache the result for future use
            self.performance_optimizer.cache_syntax_highlighting(code, language, highlighted_parts)
            
            return highlighted_parts
            
        except Exception as e:
            # Fallback to plain text on any error
            fallback_result = [(code, "#d4d4d4")]
            # Cache the fallback too to avoid repeated failures
            self.performance_optimizer.cache_syntax_highlighting(code, language, fallback_result)
            return fallback_result
    
    def _get_lexer(self, language: str, code: str):
        """Get lexer for the specified language with caching."""
        cache_key = language.lower()
        
        if cache_key in self._lexer_cache:
            return self._lexer_cache[cache_key]
        
        try:
            # Try to get lexer by name first
            lexer = get_lexer_by_name(language.lower())
        except ClassNotFound:
            try:
                # Fallback to guessing lexer from code content
                lexer = guess_lexer(code)
            except ClassNotFound:
                # Final fallback to Python lexer
                lexer = get_lexer_by_name('python')
        
        # Cache the lexer
        self._lexer_cache[cache_key] = lexer
        return lexer
    
    def _get_token_color(self, token_type) -> str:
        """Get color for a token type."""
        # Check cache first
        if token_type in self._token_style_cache:
            return self._token_style_cache[token_type]
        
        # Find the most specific color match
        color = "#d4d4d4"  # Default color
        
        # Check for exact match first
        if token_type in self._token_colors:
            color = self._token_colors[token_type]
        else:
            # Check for parent token matches
            for parent_token, parent_color in self._token_colors.items():
                if token_type in parent_token:
                    color = parent_color
                    break
        
        # Cache the result
        self._token_style_cache[token_type] = color
        return color


class DiffHighlighter:
    """Handles diff highlighting for code comparison."""
    
    def __init__(self):
        """Initialize the diff highlighter."""
        # Define diff colors (using light backgrounds for readability)
        self.diff_colors = {
            'add': '#2d4a2d',      # Dark green background
            'remove': '#4a2d2d',   # Dark red background
            'modify': '#4a4a2d',   # Dark yellow background
            'equal': None          # No special highlighting
        }
    
    def configure_diff_tags(self, textbox: ctk.CTkTextbox) -> None:
        """Configure text tags for diff highlighting in a textbox."""
        # Configure tags for different diff types
        textbox.tag_config("diff_add", background=self.diff_colors['add'])
        textbox.tag_config("diff_remove", background=self.diff_colors['remove'])
        textbox.tag_config("diff_modify", background=self.diff_colors['modify'])
    
    def apply_diff_tags(self, textbox: ctk.CTkTextbox, diff_lines: List[DiffLine]) -> None:
        """
        Apply diff highlighting tags to textbox content.
        
        Args:
            textbox: CTkTextbox widget to apply tags to
            diff_lines: List of DiffLine objects with diff information
        """
        # Clear existing diff tags
        textbox.tag_remove("diff_add", "1.0", "end")
        textbox.tag_remove("diff_remove", "1.0", "end")
        textbox.tag_remove("diff_modify", "1.0", "end")
        
        # Apply tags based on diff lines
        current_line = 1
        
        for diff_line in diff_lines:
            if diff_line.tag in ['add', 'remove', 'modify']:
                # Calculate line positions
                line_start = f"{current_line}.0"
                line_end = f"{current_line}.end"
                
                # Apply appropriate tag
                tag_name = f"diff_{diff_line.tag}"
                textbox.tag_add(tag_name, line_start, line_end)
            
            current_line += 1
    
    def create_diff_view(self, expected_code: Optional[str], generated_code: str) -> Tuple[List[DiffLine], List[DiffLine]]:
        """
        Create diff views for both expected and generated code panels.
        
        This method integrates with the existing CodeDiffer to compute differences
        and then separates them into appropriate views for each panel.
        
        Args:
            expected_code: Expected code content (can be None)
            generated_code: Generated code content
            
        Returns:
            Tuple of (expected_diff_lines, generated_diff_lines)
        """
        from ..core.differ import CodeDiffer
        
        # Use existing CodeDiffer to compute differences
        differ = CodeDiffer()
        diff_lines = differ.compute_diff(expected_code, generated_code)
        
        # Separate diff lines for each panel
        expected_diff_lines = []
        generated_diff_lines = []
        
        expected_line_num = 1
        generated_line_num = 1
        
        for diff_line in diff_lines:
            if diff_line.tag == 'equal':
                # Line appears in both panels
                expected_diff_lines.append(DiffLine(
                    tag='equal',
                    line_content=diff_line.line_content,
                    line_number=expected_line_num
                ))
                generated_diff_lines.append(DiffLine(
                    tag='equal',
                    line_content=diff_line.line_content,
                    line_number=generated_line_num
                ))
                expected_line_num += 1
                generated_line_num += 1
                
            elif diff_line.tag == 'remove':
                # Line only appears in expected panel (removed in generated)
                expected_diff_lines.append(DiffLine(
                    tag='remove',
                    line_content=diff_line.line_content,
                    line_number=expected_line_num
                ))
                expected_line_num += 1
                
            elif diff_line.tag == 'add':
                # Line only appears in generated panel (added in generated)
                generated_diff_lines.append(DiffLine(
                    tag='add',
                    line_content=diff_line.line_content,
                    line_number=generated_line_num
                ))
                generated_line_num += 1
        
        return expected_diff_lines, generated_diff_lines
    
    def apply_diff_to_panels(self, expected_panel: 'CodePanel', generated_panel: 'CodePanel',
                           expected_code: Optional[str], generated_code: str) -> None:
        """
        Apply diff highlighting to both code panels.
        
        This is a convenience method that computes diffs and applies highlighting
        to both panels in one operation.
        
        Args:
            expected_panel: CodePanel for expected code
            generated_panel: CodePanel for generated code
            expected_code: Expected code content
            generated_code: Generated code content
        """
        try:
            # Create diff views
            expected_diff_lines, generated_diff_lines = self.create_diff_view(
                expected_code, generated_code
            )
            
            # Apply diff highlighting to both panels
            expected_panel.apply_diff_highlighting(expected_diff_lines)
            generated_panel.apply_diff_highlighting(generated_diff_lines)
            
        except Exception:
            # If diff highlighting fails, continue without it
            pass


class CodePanel(ctk.CTkTextbox):
    """Enhanced code panel with syntax highlighting, diff support, and advanced scrolling."""
    
    def __init__(self, parent: ctk.CTkFrame, title: str, **kwargs):
        """
        Initialize code panel with syntax highlighting and scrolling capabilities.
        
        Args:
            parent: Parent frame
            title: Panel title (e.g., "Expected Code", "Generated Code")
            **kwargs: Additional CTkTextbox arguments
        """
        # Set default font and wrap settings for code display
        default_kwargs = {
            'font': ctk.CTkFont(family="Consolas", size=11),
            'wrap': "none",
            'state': "normal"
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
        
        self.title = title
        self._syntax_highlighter = SyntaxHighlighter()
        self._diff_highlighter = DiffHighlighter()
        
        # Configure diff tags
        self._diff_highlighter.configure_diff_tags(self)
        
        # Store current content info
        self._current_language = "python"
        self._has_syntax_highlighting = False
        
        # Setup scrolling and navigation
        self._setup_scrolling_and_navigation()
    
    @performance_optimized("code_content_display")
    def set_code_content(self, content: str, language: str = "python", apply_syntax: bool = True) -> None:
        """
        Set code content with optional syntax highlighting and performance optimization.
        
        Args:
            content: Code content to display
            language: Programming language for syntax highlighting
            apply_syntax: Whether to apply syntax highlighting
        """
        # Clear existing content
        self.delete("1.0", "end")
        
        if not content.strip():
            self.insert("1.0", "# No code available")
            return
        
        self._current_language = language
        
        # Use performance optimizer to determine optimal display strategy
        performance_optimizer = get_performance_optimizer()
        optimized_content, is_cached = performance_optimizer.optimize_code_display(content, language)
        
        # Check if we should use lazy loading
        if performance_optimizer.should_use_lazy_loading(content):
            lazy_loader = LazyCodeLoader(content)
            display_content = lazy_loader.get_content()
            
            # Add indicator for large files
            if lazy_loader.is_large:
                display_content += f"\n\n# Large file preview - {lazy_loader.line_count} total lines"
        else:
            display_content = optimized_content
        
        if apply_syntax:
            try:
                self._apply_syntax_highlighting(display_content, language)
                self._has_syntax_highlighting = True
            except Exception:
                # Fallback to plain text
                self._apply_plain_text(display_content)
                self._has_syntax_highlighting = False
        else:
            self._apply_plain_text(display_content)
            self._has_syntax_highlighting = False
    
    def _apply_syntax_highlighting(self, content: str, language: str) -> None:
        """Apply syntax highlighting to content."""
        # Get highlighted parts from syntax highlighter
        highlighted_parts = self._syntax_highlighter.highlight_code(content, language)
        
        # Insert content with colors
        for text, color in highlighted_parts:
            if text:  # Only insert non-empty text
                # Create a unique tag for this color
                tag_name = f"color_{color.replace('#', '')}"
                
                # Configure the tag if not already configured
                try:
                    self.tag_config(tag_name, foreground=color)
                except Exception:
                    # If tag configuration fails, just insert plain text
                    pass
                
                # Insert text with the color tag
                start_pos = self.index("end-1c")
                self.insert("end", text)
                end_pos = self.index("end-1c")
                
                try:
                    self.tag_add(tag_name, start_pos, end_pos)
                except Exception:
                    # If tagging fails, continue without highlighting
                    pass
    
    def _apply_plain_text(self, content: str) -> None:
        """Apply content as plain text without highlighting."""
        self.insert("1.0", content)
    
    def apply_diff_highlighting(self, diff_lines: List[DiffLine]) -> None:
        """
        Apply diff highlighting to the current content.
        
        Args:
            diff_lines: List of DiffLine objects with diff information
        """
        try:
            self._diff_highlighter.apply_diff_tags(self, diff_lines)
        except Exception:
            # If diff highlighting fails, continue without it
            pass
    
    def clear_content(self) -> None:
        """Clear all content from the panel."""
        self.delete("1.0", "end")
        self._has_syntax_highlighting = False
    
    def get_current_language(self) -> str:
        """Get the current programming language."""
        return self._current_language
    
    def has_syntax_highlighting(self) -> bool:
        """Check if syntax highlighting is currently applied."""
        return self._has_syntax_highlighting
    
    def _setup_scrolling_and_navigation(self) -> None:
        """Setup advanced scrolling and keyboard navigation."""
        # Bind keyboard events for navigation
        self.bind("<Control-Home>", self._go_to_start)
        self.bind("<Control-End>", self._go_to_end)
        self.bind("<Control-Up>", self._scroll_up_fast)
        self.bind("<Control-Down>", self._scroll_down_fast)
        self.bind("<Control-Left>", self._scroll_left_fast)
        self.bind("<Control-Right>", self._scroll_right_fast)
        self.bind("<Page_Up>", self._page_up)
        self.bind("<Page_Down>", self._page_down)
        
        # Bind mouse wheel events for smooth scrolling
        self.bind("<MouseWheel>", self._on_mouse_wheel)
        self.bind("<Button-4>", self._on_mouse_wheel)  # Linux
        self.bind("<Button-5>", self._on_mouse_wheel)  # Linux
        
        # Bind horizontal scrolling
        self.bind("<Shift-MouseWheel>", self._on_horizontal_mouse_wheel)
        
        # Store scroll position for synchronization
        self._scroll_position = {"x": 0.0, "y": 0.0}
    
    def _go_to_start(self, event=None) -> str:
        """Navigate to the start of the document."""
        try:
            self.see("1.0")
            self.mark_set("insert", "1.0")
            self._update_scroll_position()
        except Exception:
            pass
        return "break"
    
    def _go_to_end(self, event=None) -> str:
        """Navigate to the end of the document."""
        try:
            self.see("end")
            self.mark_set("insert", "end")
            self._update_scroll_position()
        except Exception:
            pass
        return "break"
    
    def _scroll_up_fast(self, event=None) -> str:
        """Scroll up quickly (5 lines)."""
        try:
            current_line = int(self.index("insert").split('.')[0])
            target_line = max(1, current_line - 5)
            self.see(f"{target_line}.0")
            self.mark_set("insert", f"{target_line}.0")
            self._update_scroll_position()
        except Exception:
            pass
        return "break"
    
    def _scroll_down_fast(self, event=None) -> str:
        """Scroll down quickly (5 lines)."""
        try:
            current_line = int(self.index("insert").split('.')[0])
            target_line = current_line + 5
            self.see(f"{target_line}.0")
            self.mark_set("insert", f"{target_line}.0")
            self._update_scroll_position()
        except Exception:
            pass
        return "break"
    
    def _scroll_left_fast(self, event=None) -> str:
        """Scroll left quickly."""
        try:
            current_pos = self.index("insert")
            line, col = current_pos.split('.')
            new_col = max(0, int(col) - 10)
            new_pos = f"{line}.{new_col}"
            self.see(new_pos)
            self.mark_set("insert", new_pos)
            self._update_scroll_position()
        except Exception:
            pass
        return "break"
    
    def _scroll_right_fast(self, event=None) -> str:
        """Scroll right quickly."""
        try:
            current_pos = self.index("insert")
            line, col = current_pos.split('.')
            new_col = int(col) + 10
            new_pos = f"{line}.{new_col}"
            self.see(new_pos)
            self.mark_set("insert", new_pos)
            self._update_scroll_position()
        except Exception:
            pass
        return "break"
    
    def _page_up(self, event=None) -> str:
        """Scroll up one page."""
        try:
            # Get visible area height
            visible_lines = int(self.winfo_height() / 20)  # Approximate line height
            current_line = int(self.index("insert").split('.')[0])
            target_line = max(1, current_line - visible_lines)
            self.see(f"{target_line}.0")
            self.mark_set("insert", f"{target_line}.0")
            self._update_scroll_position()
        except Exception:
            pass
        return "break"
    
    def _page_down(self, event=None) -> str:
        """Scroll down one page."""
        try:
            # Get visible area height
            visible_lines = int(self.winfo_height() / 20)  # Approximate line height
            current_line = int(self.index("insert").split('.')[0])
            target_line = current_line + visible_lines
            self.see(f"{target_line}.0")
            self.mark_set("insert", f"{target_line}.0")
            self._update_scroll_position()
        except Exception:
            pass
        return "break"
    
    def _on_mouse_wheel(self, event) -> str:
        """Handle mouse wheel scrolling with smooth behavior."""
        try:
            # Determine scroll direction and amount
            if event.delta:
                # Windows and macOS
                delta = -1 * (event.delta / 120)
            else:
                # Linux
                if event.num == 4:
                    delta = -1
                else:
                    delta = 1
            
            # Smooth scrolling - scroll by lines
            scroll_amount = int(delta * 3)  # 3 lines per wheel step
            
            if scroll_amount != 0:
                current_line = int(self.index("@0,0").split('.')[0])
                target_line = max(1, current_line + scroll_amount)
                self.see(f"{target_line}.0")
                self._update_scroll_position()
        except Exception:
            pass
        return "break"
    
    def _on_horizontal_mouse_wheel(self, event) -> str:
        """Handle horizontal mouse wheel scrolling."""
        try:
            # Determine scroll direction
            if event.delta:
                delta = -1 * (event.delta / 120)
            else:
                if event.num == 4:
                    delta = -1
                else:
                    delta = 1
            
            # Horizontal scrolling
            scroll_amount = int(delta * 5)  # 5 characters per wheel step
            
            if scroll_amount != 0:
                current_pos = self.index("@0,0")
                line, col = current_pos.split('.')
                new_col = max(0, int(col) + scroll_amount)
                self.see(f"{line}.{new_col}")
                self._update_scroll_position()
        except Exception:
            pass
        return "break"
    
    def _update_scroll_position(self) -> None:
        """Update stored scroll position for synchronization."""
        try:
            # Get current scroll position
            self._scroll_position["x"] = self.xview()[0]
            self._scroll_position["y"] = self.yview()[0]
        except Exception:
            pass
    
    def get_scroll_position(self) -> Dict[str, float]:
        """Get current scroll position."""
        self._update_scroll_position()
        return self._scroll_position.copy()
    
    def set_scroll_position(self, x: float, y: float) -> None:
        """Set scroll position."""
        try:
            self.xview_moveto(x)
            self.yview_moveto(y)
            self._scroll_position["x"] = x
            self._scroll_position["y"] = y
        except Exception:
            pass
    
    def scroll_to_line(self, line_number: int) -> None:
        """Scroll to a specific line number."""
        try:
            self.see(f"{line_number}.0")
            self.mark_set("insert", f"{line_number}.0")
            self._update_scroll_position()
        except Exception:
            pass
    
    def get_visible_range(self) -> Tuple[int, int]:
        """Get the range of visible lines."""
        try:
            # Get first and last visible positions
            first_visible = self.index("@0,0")
            last_visible = self.index(f"@0,{self.winfo_height()}")
            
            first_line = int(first_visible.split('.')[0])
            last_line = int(last_visible.split('.')[0])
            
            return first_line, last_line
        except Exception:
            return 1, 1


class EnhancedCodePanelsFrame(ctk.CTkFrame):
    """Enhanced code panels frame with syntax highlighting, diff support, and synchronized scrolling."""
    
    def __init__(self, parent, **kwargs):
        """Initialize enhanced code panels frame."""
        super().__init__(parent, **kwargs)
        
        # Configure grid layout for two equal columns
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Text boxes expand
        
        # Expected code label and panel
        self.expected_label = ctk.CTkLabel(
            self,
            text="Expected Code",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.expected_label.grid(row=0, column=0, padx=(10, 5), pady=(10, 5), sticky="w")
        
        self.expected_panel = CodePanel(self, "Expected Code")
        self.expected_panel.grid(row=1, column=0, padx=(10, 5), pady=(0, 10), sticky="nsew")
        
        # Generated code label and panel
        self.generated_label = ctk.CTkLabel(
            self,
            text="Generated Code",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.generated_label.grid(row=0, column=1, padx=(5, 10), pady=(10, 5), sticky="w")
        
        self.generated_panel = CodePanel(self, "Generated Code")
        self.generated_panel.grid(row=1, column=1, padx=(5, 10), pady=(0, 10), sticky="nsew")
        
        # Setup synchronized scrolling
        self._synchronized_scrolling = True
        self._setup_synchronized_scrolling()
        
        # Set initial placeholder content
        self.set_placeholder_content()
    
    def set_placeholder_content(self) -> None:
        """Set placeholder content for initial display."""
        placeholder_text = "# No code loaded\n# Use the Setup Wizard to configure a session"
        
        self.expected_panel.set_code_content(placeholder_text, apply_syntax=False)
        self.generated_panel.set_code_content(placeholder_text, apply_syntax=False)
    
    def load_code_pair(self, code_pair, language: str = "python", apply_syntax: bool = True, 
                      apply_diff: bool = True) -> None:
        """
        Load a code pair into the display panels with syntax highlighting and diff highlighting.
        
        Args:
            code_pair: CodePair object with expected and generated code
            language: Programming language for syntax highlighting
            apply_syntax: Whether to apply syntax highlighting
            apply_diff: Whether to apply diff highlighting
        """
        # Load expected code
        expected_content = code_pair.expected_code or "# No expected code available"
        self.expected_panel.set_code_content(expected_content, language, apply_syntax)
        
        # Load generated code
        generated_content = code_pair.generated_code or "# No generated code available"
        self.generated_panel.set_code_content(generated_content, language, apply_syntax)
        
        # Apply diff highlighting if requested
        if apply_diff:
            self.apply_diff_highlighting_from_code_pair(code_pair)
    
    def apply_diff_highlighting(self, expected_diff_lines: List[DiffLine], 
                              generated_diff_lines: List[DiffLine]) -> None:
        """
        Apply diff highlighting to both panels.
        
        Args:
            expected_diff_lines: Diff lines for expected code panel
            generated_diff_lines: Diff lines for generated code panel
        """
        try:
            self.expected_panel.apply_diff_highlighting(expected_diff_lines)
            self.generated_panel.apply_diff_highlighting(generated_diff_lines)
        except Exception:
            # If diff highlighting fails, continue without it
            pass
    
    def apply_diff_highlighting_from_code_pair(self, code_pair) -> None:
        """
        Apply diff highlighting using a CodePair object.
        
        This method uses the integrated DiffHighlighter to compute and apply
        diff highlighting based on the code pair's expected and generated code.
        
        Args:
            code_pair: CodePair object with expected and generated code
        """
        try:
            # Create a diff highlighter instance
            diff_highlighter = DiffHighlighter()
            
            # Apply diff highlighting to both panels
            diff_highlighter.apply_diff_to_panels(
                self.expected_panel,
                self.generated_panel,
                code_pair.expected_code,
                code_pair.generated_code
            )
        except Exception:
            # If diff highlighting fails, continue without it
            pass
    
    def clear_content(self) -> None:
        """Clear all content from both panels."""
        self.expected_panel.clear_content()
        self.generated_panel.clear_content()
    
    def set_language(self, language: str) -> None:
        """Set the programming language for both panels."""
        # This would trigger re-highlighting if content is already loaded
        # For now, it's stored for future use
        pass
    
    def _setup_synchronized_scrolling(self) -> None:
        """Setup synchronized scrolling between panels."""
        # Bind scroll events to synchronize panels
        self.expected_panel.bind("<MouseWheel>", self._on_expected_scroll)
        self.expected_panel.bind("<Button-4>", self._on_expected_scroll)  # Linux
        self.expected_panel.bind("<Button-5>", self._on_expected_scroll)  # Linux
        
        self.generated_panel.bind("<MouseWheel>", self._on_generated_scroll)
        self.generated_panel.bind("<Button-4>", self._on_generated_scroll)  # Linux
        self.generated_panel.bind("<Button-5>", self._on_generated_scroll)  # Linux
        
        # Bind keyboard navigation events
        self.expected_panel.bind("<Key>", self._on_expected_key)
        self.generated_panel.bind("<Key>", self._on_generated_key)
    
    def _on_expected_scroll(self, event) -> str:
        """Handle scroll event on expected panel."""
        if self._synchronized_scrolling:
            # Let the expected panel handle the scroll first
            result = self.expected_panel._on_mouse_wheel(event)
            
            # Synchronize the generated panel
            try:
                pos = self.expected_panel.get_scroll_position()
                self.generated_panel.set_scroll_position(pos["x"], pos["y"])
            except Exception:
                pass
            
            return result
        return None
    
    def _on_generated_scroll(self, event) -> str:
        """Handle scroll event on generated panel."""
        if self._synchronized_scrolling:
            # Let the generated panel handle the scroll first
            result = self.generated_panel._on_mouse_wheel(event)
            
            # Synchronize the expected panel
            try:
                pos = self.generated_panel.get_scroll_position()
                self.expected_panel.set_scroll_position(pos["x"], pos["y"])
            except Exception:
                pass
            
            return result
        return None
    
    def _on_expected_key(self, event) -> None:
        """Handle key event on expected panel for navigation synchronization."""
        if self._synchronized_scrolling and event.keysym in ['Up', 'Down', 'Page_Up', 'Page_Down', 'Home', 'End']:
            # Delay synchronization to allow the key event to be processed
            self.after(10, self._sync_from_expected)
    
    def _on_generated_key(self, event) -> None:
        """Handle key event on generated panel for navigation synchronization."""
        if self._synchronized_scrolling and event.keysym in ['Up', 'Down', 'Page_Up', 'Page_Down', 'Home', 'End']:
            # Delay synchronization to allow the key event to be processed
            self.after(10, self._sync_from_generated)
    
    def _sync_from_expected(self) -> None:
        """Synchronize generated panel with expected panel position."""
        try:
            pos = self.expected_panel.get_scroll_position()
            self.generated_panel.set_scroll_position(pos["x"], pos["y"])
        except Exception:
            pass
    
    def _sync_from_generated(self) -> None:
        """Synchronize expected panel with generated panel position."""
        try:
            pos = self.generated_panel.get_scroll_position()
            self.expected_panel.set_scroll_position(pos["x"], pos["y"])
        except Exception:
            pass
    
    def set_synchronized_scrolling(self, enabled: bool) -> None:
        """Enable or disable synchronized scrolling between panels."""
        self._synchronized_scrolling = enabled
    
    def is_synchronized_scrolling_enabled(self) -> bool:
        """Check if synchronized scrolling is enabled."""
        return self._synchronized_scrolling
    
    def scroll_to_line(self, line_number: int) -> None:
        """Scroll both panels to a specific line number."""
        self.expected_panel.scroll_to_line(line_number)
        self.generated_panel.scroll_to_line(line_number)
    
    def get_visible_range(self) -> Tuple[int, int]:
        """Get the visible line range from the expected panel."""
        return self.expected_panel.get_visible_range()