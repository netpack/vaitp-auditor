"""
Review UI controller for managing code pair display and user interaction.
"""

import time
from datetime import datetime, timezone
from typing import Tuple, Optional
from rich.console import Console

from ..core.models import CodePair, ReviewResult
from ..core.differ import CodeDiffer
from .display_manager import DisplayManager
from .input_handler import InputHandler
from .diff_renderer import DiffRenderer
from .scroll_manager import ScrollManager


class ReviewUIController:
    """
    Stateless component that displays individual code pairs and handles user input.
    
    The controller coordinates display, input handling, and diff rendering
    to provide a complete review interface for a single code pair.
    """

    def __init__(self, console: Console = None, enable_scrolling: bool = True, undo_callback=None):
        """
        Initialize the review UI controller.
        
        Args:
            console: Rich console instance. If None, creates a new one.
            enable_scrolling: Whether to enable scrolling functionality.
            undo_callback: Callback function for handling undo operations.
        """
        self.console = console or Console()
        self.scroll_manager = ScrollManager() if enable_scrolling else None
        self.display_manager = DisplayManager(self.scroll_manager)
        self.input_handler = InputHandler(self.console, self.scroll_manager)
        self.diff_renderer = DiffRenderer(self.console)
        self.code_differ = CodeDiffer()
        self.enable_scrolling = enable_scrolling
        self.undo_callback = undo_callback
        
        # Counter for generating review IDs
        self._review_id_counter = 1

    def display_code_pair(
        self, 
        code_pair: CodePair, 
        progress_info: dict,
        experiment_name: str
    ) -> ReviewResult:
        """
        Display a code pair and collect user review.
        
        Args:
            code_pair: The code pair to display and review.
            progress_info: Dictionary with 'current', 'total', 'percentage' keys.
            experiment_name: Name of the current experiment.
            
        Returns:
            ReviewResult: The completed review result.
        """
        start_time = time.time()
        
        try:
            # Display the code pair
            self._render_code_pair_display(code_pair, progress_info)
            
            # Get user verdict and comment
            if self.enable_scrolling and self.scroll_manager:
                verdict, comment = self.handle_user_input_with_scrolling(code_pair, progress_info)
            else:
                verdict, comment = self.handle_user_input()
            
            # Handle undo command
            if verdict == 'Undo':
                if self.undo_callback and self.undo_callback():
                    # Undo was successful, return a special result to indicate undo
                    return ReviewResult(
                        review_id=0,  # Use 0 as special ID to indicate undo
                        source_identifier="UNDO",
                        experiment_name=experiment_name,
                        review_timestamp_utc=datetime.now(timezone.utc),
                        reviewer_verdict="Undo",
                        reviewer_comment="",
                        time_to_review_seconds=0,
                        expected_code=None,
                        generated_code="",
                        code_diff=""
                    )
                else:
                    # Undo failed, show message and continue with current pair
                    self.show_message("No review to undo or undo failed.", "warning")
                    # Recursively call to get a new verdict
                    return self.display_code_pair(code_pair, progress_info, experiment_name)
            
            # Calculate review time
            review_time = time.time() - start_time
            
            # Create and return ReviewResult
            review_result = ReviewResult(
                review_id=self._get_next_review_id(),
                source_identifier=code_pair.identifier,
                experiment_name=experiment_name,
                review_timestamp_utc=datetime.now(timezone.utc),
                reviewer_verdict=verdict,
                reviewer_comment=comment,
                time_to_review_seconds=review_time,
                expected_code=code_pair.expected_code,
                generated_code=code_pair.generated_code,
                code_diff=self._get_diff_text(code_pair.expected_code, code_pair.generated_code)
            )
            
            return review_result
            
        except Exception as e:
            # Handle UI rendering failures with graceful degradation
            self.input_handler.show_error_message(f"UI rendering error: {str(e)}")
            
            # Fallback to basic text display
            self._render_fallback_display(code_pair, progress_info)
            
            # Still get user input
            verdict, comment = self.handle_user_input()
            
            review_time = time.time() - start_time
            
            return ReviewResult(
                review_id=self._get_next_review_id(),
                source_identifier=code_pair.identifier,
                experiment_name=experiment_name,
                review_timestamp_utc=datetime.now(timezone.utc),
                reviewer_verdict=verdict,
                reviewer_comment=comment,
                time_to_review_seconds=review_time,
                expected_code=code_pair.expected_code,
                generated_code=code_pair.generated_code,
                code_diff=self._get_diff_text(code_pair.expected_code, code_pair.generated_code)
            )

    def handle_user_input(self) -> Tuple[str, str]:
        """
        Handle user input for verdict and comment.
        
        Returns:
            Tuple[str, str]: (verdict, comment) from user input.
        """
        return self.input_handler.get_user_verdict()

    def handle_user_input_with_scrolling(self, code_pair: CodePair, progress_info: dict) -> Tuple[str, str]:
        """
        Handle user input with scrolling navigation support.
        
        Args:
            code_pair: The current code pair being reviewed.
            progress_info: Progress information dictionary.
            
        Returns:
            Tuple[str, str]: (verdict, comment) from user input.
        """
        def update_display():
            """Callback to update display when scrolling occurs."""
            self._render_scrollable_code_pair_display(code_pair, progress_info)
        
        return self.input_handler.get_user_verdict_with_scrolling(update_display)

    def render_diff(self, expected: Optional[str], generated: str) -> None:
        """
        Render code differences with appropriate highlighting.
        
        Args:
            expected: The expected code content (can be None).
            generated: The generated code content.
        """
        try:
            # Compute diff lines
            diff_lines = self.code_differ.compute_diff(expected, generated)
            
            # Display diff summary
            summary = self.diff_renderer.create_diff_summary(diff_lines)
            self.console.print(summary)
            
            # Display color legend
            legend = self.diff_renderer.get_color_legend()
            self.console.print(legend)
            
            # Display contextual diff
            contextual_diff = self.diff_renderer.render_diff_with_context(diff_lines, context_lines=3)
            self.console.print(contextual_diff)
            
        except Exception as e:
            self.input_handler.show_error_message(f"Diff rendering error: {str(e)}")
            # Fallback to basic text diff
            self._render_fallback_diff(expected, generated)

    def show_diff_view(self, code_pair: CodePair) -> None:
        """
        Show a detailed diff view for the code pair.
        
        Args:
            code_pair: The code pair to show diff for.
        """
        self.console.clear()
        self.console.print(f"\n[bold blue]Detailed Diff View - {code_pair.identifier}[/bold blue]\n")
        
        self.render_diff(code_pair.expected_code, code_pair.generated_code)
        
        # Wait for user to continue
        self.input_handler.prompt_for_input("\nPress Enter to return to review", "")

    def _render_code_pair_display(self, code_pair: CodePair, progress_info: dict) -> None:
        """
        Render the main code pair display.
        
        Args:
            code_pair: The code pair to display.
            progress_info: Progress information dictionary.
        """
        if self.enable_scrolling and self.scroll_manager:
            self._render_scrollable_code_pair_display(code_pair, progress_info)
        else:
            self.display_manager.render_code_panels(
                expected=code_pair.expected_code,
                generated=code_pair.generated_code,
                progress_info=progress_info,
                source_identifier=code_pair.identifier
            )

    def _render_scrollable_code_pair_display(self, code_pair: CodePair, progress_info: dict) -> None:
        """
        Render the scrollable code pair display.
        
        Args:
            code_pair: The code pair to display.
            progress_info: Progress information dictionary.
        """
        self.display_manager.render_scrollable_code_panels(
            expected=code_pair.expected_code,
            generated=code_pair.generated_code,
            progress_info=progress_info,
            source_identifier=code_pair.identifier
        )

    def _render_fallback_display(self, code_pair: CodePair, progress_info: dict) -> None:
        """
        Render a fallback display when rich rendering fails.
        
        Args:
            code_pair: The code pair to display.
            progress_info: Progress information dictionary.
        """
        self.console.clear()
        
        # Basic text display
        progress_text = f"Review {progress_info.get('current', 0)}/{progress_info.get('total', 0)} ({progress_info.get('percentage', 0):.1f}%)"
        self.console.print(f"\n=== VAITP Code Review - {progress_text} ===")
        self.console.print(f"Identifier: {code_pair.identifier}\n")
        
        self.console.print("=== EXPECTED CODE ===")
        if code_pair.expected_code:
            self.console.print(code_pair.expected_code)
        else:
            self.console.print("(No expected code available)")
        
        self.console.print("\n=== GENERATED CODE ===")
        self.console.print(code_pair.generated_code)
        self.console.print("\n" + "="*50)

    def _render_fallback_diff(self, expected: Optional[str], generated: str) -> None:
        """
        Render a basic text diff when rich rendering fails.
        
        Args:
            expected: Expected code content.
            generated: Generated code content.
        """
        diff_text = self.code_differ.get_diff_text(expected, generated)
        if diff_text:
            self.console.print("\n=== DIFF ===")
            self.console.print(diff_text)
        else:
            self.console.print("\n=== NO DIFFERENCES FOUND ===")

    def _get_diff_text(self, expected: Optional[str], generated: str) -> str:
        """
        Get diff text for storage in review result.
        
        Args:
            expected: Expected code content.
            generated: Generated code content.
            
        Returns:
            Diff text string.
        """
        try:
            return self.code_differ.get_diff_text(expected, generated)
        except Exception:
            return "Error computing diff"

    def _get_next_review_id(self) -> int:
        """
        Get the next review ID.
        
        Returns:
            Next review ID integer.
        """
        review_id = self._review_id_counter
        self._review_id_counter += 1
        return review_id

    def set_review_id_counter(self, start_id: int) -> None:
        """
        Set the starting review ID counter.
        
        Args:
            start_id: Starting ID for review counter.
        """
        self._review_id_counter = start_id

    def show_help(self) -> None:
        """Show help information to the user."""
        self.input_handler.display_help()

    def confirm_action(self, message: str) -> bool:
        """
        Get confirmation for an action.
        
        Args:
            message: Confirmation message.
            
        Returns:
            True if confirmed, False otherwise.
        """
        return self.input_handler.get_confirmation(message)

    def show_message(self, message: str, message_type: str = "info") -> None:
        """
        Show a message to the user.
        
        Args:
            message: Message to display.
            message_type: Type of message ('info', 'error', 'success', 'warning').
        """
        if message_type == "error":
            self.input_handler.show_error_message(message)
        elif message_type == "success":
            self.input_handler.show_success_message(message)
        elif message_type == "warning":
            self.display_manager.show_warning(message)
        else:
            self.input_handler.show_info_message(message)