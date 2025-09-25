"""
Display manager for terminal rendering with Rich library.
"""

from typing import Optional, List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.syntax import Syntax
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.layout import Layout
from rich.align import Align
from .scroll_manager import ScrollManager
from ..utils.performance import (
    get_content_cache, get_performance_monitor, 
    performance_monitor, LazyLoader
)


class DisplayManager:
    """
    Manages terminal rendering using the Rich library.
    
    Handles two-panel layout, syntax highlighting, and progress indicators.
    """

    def __init__(self, scroll_manager: Optional[ScrollManager] = None):
        """Initialize the display manager."""
        self.console = Console()
        self.layout = Layout()
        self.scroll_manager = scroll_manager or ScrollManager()
        self._cache = get_content_cache()
        self._monitor = get_performance_monitor()
        self._syntax_cache = {}  # Local cache for syntax objects
        self._setup_layout()

    def _setup_layout(self) -> None:
        """Set up the main layout structure."""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        # Split main area into two panels
        self.layout["main"].split_row(
            Layout(name="expected"),
            Layout(name="generated")
        )

    def render_code_panels(
        self, 
        expected: Optional[str], 
        generated: str, 
        progress_info: dict,
        source_identifier: str = ""
    ) -> None:
        """
        Render two-panel code display with headers and progress.
        
        Args:
            expected: Expected code content (can be None).
            generated: Generated code content.
            progress_info: Dictionary with 'current', 'total', 'percentage' keys.
            source_identifier: Identifier for the current code pair.
        """
        # Create progress display
        progress_text = f"Review {progress_info.get('current', 0)}/{progress_info.get('total', 0)} ({progress_info.get('percentage', 0):.1f}%)"
        if source_identifier:
            progress_text += f" - {source_identifier}"
        
        self.layout["header"].update(
            Panel(
                Align.center(Text(progress_text, style="bold blue")),
                title="VAITP Code Review",
                border_style="blue"
            )
        )

        # Create expected code panel with caching
        if expected is not None:
            expected_syntax = self._get_cached_syntax(expected, "expected")
            expected_panel = Panel(
                expected_syntax,
                title="[bold green]Expected Code[/bold green]",
                border_style="green"
            )
        else:
            expected_panel = Panel(
                Align.center(Text("No expected code available", style="dim italic")),
                title="[bold green]Expected Code[/bold green]",
                border_style="green"
            )

        # Create generated code panel with caching
        generated_syntax = self._get_cached_syntax(generated, "generated")
        generated_panel = Panel(
            generated_syntax,
            title="[bold yellow]Generated Code[/bold yellow]",
            border_style="yellow"
        )

        # Update layout
        self.layout["expected"].update(expected_panel)
        self.layout["generated"].update(generated_panel)

        # Create footer with instructions
        instructions = Text()
        instructions.append("Commands: ", style="bold")
        instructions.append("s", style="bold green")
        instructions.append("=Success, ", style="white")
        instructions.append("f", style="bold red")
        instructions.append("=Failure, ", style="white")
        instructions.append("i", style="bold magenta")
        instructions.append("=Invalid, ", style="white")
        instructions.append("w", style="bold cyan")
        instructions.append("=Wrong Vuln, ", style="white")
        instructions.append("p", style="bold blue")
        instructions.append("=Partial, ", style="white")
        instructions.append("u", style="bold magenta")
        instructions.append("=Undo, ", style="white")
        instructions.append("q", style="bold red")
        instructions.append("=Quit", style="white")

        self.layout["footer"].update(
            Panel(
                Align.center(instructions),
                border_style="dim"
            )
        )

        # Render the complete layout
        self.console.clear()
        self.console.print(self.layout)

    def render_scrollable_code_panels(
        self, 
        expected: Optional[str], 
        generated: str, 
        progress_info: dict,
        source_identifier: str = ""
    ) -> None:
        """
        Render two-panel code display with scrolling support.
        
        Args:
            expected: Expected code content (can be None).
            generated: Generated code content.
            progress_info: Dictionary with 'current', 'total', 'percentage' keys.
            source_identifier: Identifier for the current code pair.
        """
        # Get terminal dimensions
        terminal_width, terminal_height = self.get_terminal_size()
        
        # Calculate viewport dimensions (accounting for borders and headers)
        viewport_height = max(1, terminal_height - 6)  # Header + footer + borders
        viewport_width = max(1, (terminal_width - 4) // 2)  # Split in half, account for borders
        
        # Prepare content lines
        expected_lines = expected.split('\n') if expected else ["No expected code available"]
        generated_lines = generated.split('\n') if generated else [""]
        
        # Set content dimensions for scroll manager
        self.scroll_manager.set_content_dimensions("left", expected_lines, viewport_height, viewport_width)
        self.scroll_manager.set_content_dimensions("right", generated_lines, viewport_height, viewport_width)
        
        # Get visible content
        visible_expected, expected_start_line, expected_scroll_indicator = self.scroll_manager.get_visible_content("left", expected_lines)
        visible_generated, generated_start_line, generated_scroll_indicator = self.scroll_manager.get_visible_content("right", generated_lines)
        
        # Create progress display with scroll info
        progress_text = f"Review {progress_info.get('current', 0)}/{progress_info.get('total', 0)} ({progress_info.get('percentage', 0):.1f}%)"
        if source_identifier:
            progress_text += f" - {source_identifier}"
        
        # Add active panel indicator
        active_panel = self.scroll_manager.get_active_panel()
        progress_text += f" | Active: {'Expected' if active_panel == 'left' else 'Generated'}"
        
        self.layout["header"].update(
            Panel(
                Align.center(Text(progress_text, style="bold blue")),
                title="VAITP Code Review (Use arrows/Tab to navigate)",
                border_style="blue"
            )
        )

        # Create expected code panel with scroll indicators
        expected_title = "[bold green]Expected Code[/bold green]"
        if expected_scroll_indicator > 0:
            scroll_info = self.scroll_manager.get_scroll_info("left")
            expected_title += f" (Line {expected_start_line}+)"
            if scroll_info['can_scroll_up'] or scroll_info['can_scroll_down']:
                expected_title += " ↕"
            if scroll_info['can_scroll_left'] or scroll_info['can_scroll_right']:
                expected_title += " ↔"
        
        if active_panel == "left":
            expected_border_style = "bright_green"
        else:
            expected_border_style = "green"
        
        if expected and visible_expected:
            # Create syntax highlighting for visible content with caching
            visible_expected_text = '\n'.join(visible_expected)
            expected_syntax = self._get_cached_syntax(
                visible_expected_text, 
                f"expected_scroll_{expected_start_line}",
                start_line=expected_start_line,
                word_wrap=False
            )
            expected_panel = Panel(
                expected_syntax,
                title=expected_title,
                border_style=expected_border_style
            )
        else:
            expected_panel = Panel(
                Align.center(Text("No expected code available", style="dim italic")),
                title=expected_title,
                border_style=expected_border_style
            )

        # Create generated code panel with scroll indicators
        generated_title = "[bold yellow]Generated Code[/bold yellow]"
        if generated_scroll_indicator > 0:
            scroll_info = self.scroll_manager.get_scroll_info("right")
            generated_title += f" (Line {generated_start_line}+)"
            if scroll_info['can_scroll_up'] or scroll_info['can_scroll_down']:
                generated_title += " ↕"
            if scroll_info['can_scroll_left'] or scroll_info['can_scroll_right']:
                generated_title += " ↔"
        
        if active_panel == "right":
            generated_border_style = "bright_yellow"
        else:
            generated_border_style = "yellow"
        
        visible_generated_text = '\n'.join(visible_generated)
        generated_syntax = self._get_cached_syntax(
            visible_generated_text,
            f"generated_scroll_{generated_start_line}",
            start_line=generated_start_line,
            word_wrap=False
        )
        generated_panel = Panel(
            generated_syntax,
            title=generated_title,
            border_style=generated_border_style
        )

        # Update layout
        self.layout["expected"].update(expected_panel)
        self.layout["generated"].update(generated_panel)

        # Create footer with navigation instructions
        instructions = Text()
        instructions.append("Navigation: ", style="bold")
        instructions.append("↑↓←→", style="bold cyan")
        instructions.append("/", style="white")
        instructions.append("hjkl", style="bold cyan")
        instructions.append("=Scroll, ", style="white")
        instructions.append("PgUp/PgDn", style="bold cyan")
        instructions.append("=Page, ", style="white")
        instructions.append("Tab", style="bold cyan")
        instructions.append("=Switch Panel | ", style="white")
        
        instructions.append("Review: ", style="bold")
        instructions.append("s", style="bold green")
        instructions.append("=Success, ", style="white")
        instructions.append("f", style="bold red")
        instructions.append("=Failure, ", style="white")
        instructions.append("u", style="bold magenta")
        instructions.append("=Undo, ", style="white")
        instructions.append("q", style="bold red")
        instructions.append("=Quit", style="white")

        self.layout["footer"].update(
            Panel(
                Align.center(instructions),
                border_style="dim"
            )
        )

        # Render the complete layout
        self.console.clear()
        self.console.print(self.layout)

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        self.console.clear()

    def show_message(self, message: str, style: str = "white") -> None:
        """
        Display a message to the user.
        
        Args:
            message: Message to display.
            style: Rich style for the message.
        """
        self.console.print(message, style=style)

    def show_error(self, error_message: str) -> None:
        """
        Display an error message with appropriate styling.
        
        Args:
            error_message: Error message to display.
        """
        self.console.print(f"[bold red]Error:[/bold red] {error_message}")

    def show_success(self, success_message: str) -> None:
        """
        Display a success message with appropriate styling.
        
        Args:
            success_message: Success message to display.
        """
        self.console.print(f"[bold green]Success:[/bold green] {success_message}")

    def show_warning(self, warning_message: str) -> None:
        """
        Display a warning message with appropriate styling.
        
        Args:
            warning_message: Warning message to display.
        """
        self.console.print(f"[bold yellow]Warning:[/bold yellow] {warning_message}")

    def prompt_user(self, prompt_text: str) -> str:
        """
        Display a prompt and get user input.
        
        Args:
            prompt_text: Text to display as prompt.
            
        Returns:
            User input string.
        """
        return self.console.input(f"[bold cyan]{prompt_text}[/bold cyan] ")

    def get_terminal_size(self) -> tuple[int, int]:
        """
        Get current terminal dimensions.
        
        Returns:
            Tuple of (width, height).
        """
        return self.console.size
    
    def _get_cached_syntax(self, content: str, cache_key: str, 
                          start_line: int = 1, word_wrap: bool = True) -> Syntax:
        """
        Get syntax-highlighted content with caching.
        
        Args:
            content: Code content to highlight.
            cache_key: Unique key for caching.
            start_line: Starting line number.
            word_wrap: Whether to enable word wrapping.
            
        Returns:
            Syntax object for rendering.
        """
        # Generate full cache key including parameters
        full_cache_key = f"syntax_{cache_key}_{start_line}_{word_wrap}_{hash(content)}"
        
        # Check local cache first
        if full_cache_key in self._syntax_cache:
            return self._syntax_cache[full_cache_key]
        
        # Check if content is large and should be processed differently
        content_size = len(content.encode('utf-8'))
        is_large = content_size > 50000  # 50KB threshold for syntax highlighting
        
        if is_large:
            # For large content, use plain text or simplified highlighting
            syntax = self._create_large_content_syntax(content, start_line, word_wrap)
        else:
            # Create syntax highlighting
            syntax = Syntax(
                content,
                "python",
                theme="monokai",
                line_numbers=True,
                start_line=start_line,
                word_wrap=word_wrap
            )
        
        # Cache the result (limit cache size)
        if len(self._syntax_cache) < 50:  # Limit to 50 cached syntax objects
            self._syntax_cache[full_cache_key] = syntax
        
        return syntax
    
    def _create_large_content_syntax(self, content: str, start_line: int, word_wrap: bool) -> Syntax:
        """
        Create syntax highlighting for large content with optimizations.
        
        Args:
            content: Large code content.
            start_line: Starting line number.
            word_wrap: Whether to enable word wrapping.
            
        Returns:
            Optimized Syntax object.
        """
        lines = content.split('\n')
        
        # For very large files, show only a portion with indicators
        if len(lines) > 1000:
            # Show first 500 lines with an indicator
            truncated_lines = lines[:500]
            truncated_lines.append(f"... [TRUNCATED: {len(lines) - 500} more lines] ...")
            truncated_content = '\n'.join(truncated_lines)
            
            return Syntax(
                truncated_content,
                "python",
                theme="monokai",
                line_numbers=True,
                start_line=start_line,
                word_wrap=word_wrap
            )
        else:
            # Use regular syntax highlighting but with simpler theme for performance
            return Syntax(
                content,
                "python",
                theme="default",  # Simpler theme for better performance
                line_numbers=True,
                start_line=start_line,
                word_wrap=word_wrap
            )
    
    def clear_caches(self) -> None:
        """Clear all display caches to free memory."""
        self._syntax_cache.clear()
        self._cache.clear()
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics for monitoring."""
        return {
            'syntax_cache_size': len(self._syntax_cache),
            'content_cache_stats': self._cache.get_stats()
        }