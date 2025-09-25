"""
Diff renderer for color-coded code differences.
"""

from typing import List, Tuple
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.align import Align

from vaitp_auditor.core.models import DiffLine


class DiffRenderer:
    """
    Renders code differences with color highlighting.
    
    Interprets DiffLine tags and applies appropriate color coding:
    - Green for added lines
    - Red for removed lines  
    - Yellow for modified lines
    - White for equal lines
    """

    def __init__(self, console: Console = None):
        """
        Initialize the diff renderer.
        
        Args:
            console: Rich console instance. If None, creates a new one.
        """
        self.console = console or Console()

    def render_diff_lines(self, diff_lines: List[DiffLine]) -> Text:
        """
        Render a list of diff lines with appropriate color coding.
        
        Args:
            diff_lines: List of DiffLine objects to render.
            
        Returns:
            Rich Text object with colored diff content.
        """
        text = Text()
        
        for diff_line in diff_lines:
            line_text = diff_line.line_content
            
            # Add line number if available
            if diff_line.line_number is not None:
                line_prefix = f"{diff_line.line_number:4d}: "
            else:
                line_prefix = "     "
            
            # Apply color based on tag
            if diff_line.tag == 'add':
                text.append(line_prefix, style="dim")
                text.append(f"+ {line_text}", style="bold green on dark_green")
            elif diff_line.tag == 'remove':
                text.append(line_prefix, style="dim")
                text.append(f"- {line_text}", style="bold red on dark_red")
            elif diff_line.tag == 'modify':
                text.append(line_prefix, style="dim")
                text.append(f"~ {line_text}", style="bold yellow on #3a3a00")
            else:  # equal
                text.append(line_prefix, style="dim")
                text.append(f"  {line_text}", style="white")
            
            text.append("\n")
        
        return text

    def render_side_by_side_diff(
        self, 
        expected_lines: List[DiffLine], 
        generated_lines: List[DiffLine]
    ) -> Columns:
        """
        Render side-by-side diff comparison.
        
        Args:
            expected_lines: Diff lines for expected code.
            generated_lines: Diff lines for generated code.
            
        Returns:
            Rich Columns object with side-by-side panels.
        """
        expected_text = self.render_diff_lines(expected_lines)
        generated_text = self.render_diff_lines(generated_lines)
        
        expected_panel = Panel(
            expected_text,
            title="[bold green]Expected Code (with diff)[/bold green]",
            border_style="green",
            padding=(0, 1)
        )
        
        generated_panel = Panel(
            generated_text,
            title="[bold yellow]Generated Code (with diff)[/bold yellow]",
            border_style="yellow",
            padding=(0, 1)
        )
        
        return Columns([expected_panel, generated_panel], equal=True)

    def render_unified_diff(self, diff_lines: List[DiffLine]) -> Panel:
        """
        Render unified diff format.
        
        Args:
            diff_lines: List of DiffLine objects representing unified diff.
            
        Returns:
            Rich Panel with unified diff content.
        """
        text = self.render_diff_lines(diff_lines)
        
        return Panel(
            text,
            title="[bold blue]Unified Diff[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        )

    def create_diff_summary(self, diff_lines: List[DiffLine]) -> Text:
        """
        Create a summary of the differences.
        
        Args:
            diff_lines: List of DiffLine objects to analyze.
            
        Returns:
            Rich Text object with diff summary.
        """
        add_count = sum(1 for line in diff_lines if line.tag == 'add')
        remove_count = sum(1 for line in diff_lines if line.tag == 'remove')
        modify_count = sum(1 for line in diff_lines if line.tag == 'modify')
        equal_count = sum(1 for line in diff_lines if line.tag == 'equal')
        
        summary = Text()
        summary.append("Diff Summary: ", style="bold")
        
        if add_count > 0:
            summary.append(f"+{add_count} ", style="bold green")
        if remove_count > 0:
            summary.append(f"-{remove_count} ", style="bold red")
        if modify_count > 0:
            summary.append(f"~{modify_count} ", style="bold yellow")
        if equal_count > 0:
            summary.append(f"={equal_count} ", style="dim")
        
        if add_count == 0 and remove_count == 0 and modify_count == 0:
            summary.append("(No differences)", style="dim italic")
        
        return summary

    def render_diff_with_context(
        self, 
        diff_lines: List[DiffLine], 
        context_lines: int = 3
    ) -> Text:
        """
        Render diff with limited context around changes.
        
        Args:
            diff_lines: List of DiffLine objects.
            context_lines: Number of context lines to show around changes.
            
        Returns:
            Rich Text object with contextual diff.
        """
        if not diff_lines:
            return Text("No differences found", style="dim italic")
        
        # Find lines with changes
        change_indices = []
        for i, line in enumerate(diff_lines):
            if line.tag != 'equal':
                change_indices.append(i)
        
        if not change_indices:
            return Text("No differences found", style="dim italic")
        
        # Determine which lines to include with context
        lines_to_include = set()
        for idx in change_indices:
            start = max(0, idx - context_lines)
            end = min(len(diff_lines), idx + context_lines + 1)
            lines_to_include.update(range(start, end))
        
        # Render selected lines
        text = Text()
        prev_line = -1
        
        for i in sorted(lines_to_include):
            # Add separator if there's a gap
            if i > prev_line + 1:
                text.append("...\n", style="dim")
            
            line = diff_lines[i]
            line_text = line.line_content
            
            # Add line number if available
            if line.line_number is not None:
                line_prefix = f"{line.line_number:4d}: "
            else:
                line_prefix = f"{i+1:4d}: "
            
            # Apply color based on tag
            if line.tag == 'add':
                text.append(line_prefix, style="dim")
                text.append(f"+ {line_text}", style="bold green on dark_green")
            elif line.tag == 'remove':
                text.append(line_prefix, style="dim")
                text.append(f"- {line_text}", style="bold red on dark_red")
            elif line.tag == 'modify':
                text.append(line_prefix, style="dim")
                text.append(f"~ {line_text}", style="bold yellow on #3a3a00")
            else:  # equal
                text.append(line_prefix, style="dim")
                text.append(f"  {line_text}", style="white")
            
            text.append("\n")
            prev_line = i
        
        return text

    def get_color_legend(self) -> Panel:
        """
        Get a legend explaining the color coding.
        
        Returns:
            Rich Panel with color legend.
        """
        legend = Text()
        legend.append("Legend: ", style="bold")
        legend.append("+ Added", style="bold green on dark_green")
        legend.append(" | ", style="dim")
        legend.append("- Removed", style="bold red on dark_red")
        legend.append(" | ", style="dim")
        legend.append("~ Modified", style="bold yellow on #3a3a00")
        legend.append(" | ", style="dim")
        legend.append("  Unchanged", style="white")
        
        return Panel(
            Align.center(legend),
            border_style="dim"
        )