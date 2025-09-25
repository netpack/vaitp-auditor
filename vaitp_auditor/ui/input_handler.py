"""
Input handler for processing user keyboard input and commands.
"""

import sys
from typing import Tuple, Optional
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from .scroll_manager import ScrollManager
from .keyboard_input import KeyboardInput


class InputHandler:
    """
    Processes keyboard input and classification commands.
    
    Handles single-key commands for verdict classification and navigation.
    """

    def __init__(self, console: Console = None, scroll_manager: Optional[ScrollManager] = None):
        """
        Initialize the input handler.
        
        Args:
            console: Rich console instance. If None, creates a new one.
            scroll_manager: ScrollManager instance for handling navigation.
        """
        self.console = console or Console()
        self.scroll_manager = scroll_manager
        self.keyboard_input = KeyboardInput()
        self.valid_verdicts = {
            's': 'Success',
            'f': 'Failure - No Change', 
            'i': 'Invalid Code',
            'w': 'Wrong Vulnerability',
            'p': 'Partial Success',
            'u': 'Undo',
            'q': 'Quit'
        }

    def get_user_verdict(self) -> Tuple[str, str]:
        """
        Get user verdict and optional comment.
        
        Returns:
            Tuple[str, str]: (verdict, comment) from user input.
        """
        while True:
            # Display prompt
            self.console.print("\n[bold cyan]Enter your verdict:[/bold cyan]")
            self._display_verdict_options()
            
            try:
                # Get single character input
                user_input = self.console.input("\n[bold]Your choice: [/bold]").lower().strip()
                
                if not user_input:
                    self.console.print("[yellow]Please enter a valid option.[/yellow]")
                    continue
                
                # Take first character if multiple entered
                choice = user_input[0]
                
                if choice == 'h':
                    self.display_help()
                    continue
                
                if choice not in self.valid_verdicts:
                    self.console.print(f"[red]Invalid choice '{choice}'. Press 'h' for help.[/red]")
                    continue
                
                verdict = self.valid_verdicts[choice]
                
                # Handle quit immediately
                if verdict == 'Quit':
                    return verdict, ""
                
                # Confirm the selection
                if self.get_confirmation(f"Confirm verdict: {verdict}?"):
                    # Get optional comment
                    comment = self._get_comment()
                    return verdict, comment
                else:
                    self.console.print("[yellow]Selection cancelled. Please choose again.[/yellow]")
                    continue
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'q' to quit properly.[/yellow]")
                continue
            except EOFError:
                # Handle Ctrl+D
                return 'Quit', ""

    def get_user_verdict_with_scrolling(self, on_scroll_update) -> Tuple[str, str]:
        """
        Get user verdict with scrolling navigation support.
        
        Args:
            on_scroll_update: Callback function to call when scrolling occurs.
            
        Returns:
            Tuple[str, str]: (verdict, comment) from user input.
        """
        if not self.scroll_manager:
            # Fallback to regular input if no scroll manager
            return self.get_user_verdict()
        
        self.console.print("\n[bold cyan]Navigate with arrows/hjkl, Tab to switch panels. Enter verdict when ready:[/bold cyan]")
        self._display_verdict_options()
        
        with self.keyboard_input:
            while True:
                try:
                    # Get raw keyboard input
                    key = self.keyboard_input.get_key_blocking()
                    
                    if not key:
                        continue
                    
                    # Handle navigation keys
                    if self.scroll_manager.handle_scroll_input(key):
                        # Scrolling occurred, update display
                        if on_scroll_update:
                            on_scroll_update()
                        continue
                    
                    # Handle verdict keys
                    if key.lower() in self.valid_verdicts:
                        verdict = self.valid_verdicts[key.lower()]
                        
                        # Handle quit immediately
                        if verdict == 'Quit':
                            return verdict, ""
                        
                        # Confirm the selection
                        self.keyboard_input.disable_raw_mode()
                        try:
                            if self.get_confirmation(f"Confirm verdict: {verdict}?"):
                                # Get optional comment
                                comment = self._get_comment()
                                return verdict, comment
                            else:
                                self.console.print("[yellow]Selection cancelled. Continue navigating or choose again.[/yellow]")
                                self.keyboard_input.enable_raw_mode()
                                continue
                        except:
                            self.keyboard_input.enable_raw_mode()
                            continue
                    
                    # Handle help
                    elif key.lower() == 'h':
                        self.keyboard_input.disable_raw_mode()
                        try:
                            self.display_help()
                            self.console.print("\n[dim]Press any key to continue...[/dim]")
                            self.console.input()
                        finally:
                            self.keyboard_input.enable_raw_mode()
                    
                    # Handle Enter key (show current options)
                    elif key == '\n' or key == '\r':
                        self.console.print("\n[yellow]Choose a verdict option (s/f/i/w/p/q) or continue navigating.[/yellow]")
                    
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Use 'q' to quit properly.[/yellow]")
                    continue
                except EOFError:
                    return 'Quit', ""

    def get_confirmation(self, message: str) -> bool:
        """
        Get yes/no confirmation from user.
        
        Args:
            message: Confirmation message to display.
            
        Returns:
            bool: True if user confirms, False otherwise.
        """
        while True:
            try:
                response = self.console.input(f"[bold yellow]{message} (y/n): [/bold yellow]").lower().strip()
                
                if response in ['y', 'yes']:
                    return True
                elif response in ['n', 'no']:
                    return False
                else:
                    self.console.print("[red]Please enter 'y' for yes or 'n' for no.[/red]")
                    
            except (KeyboardInterrupt, EOFError):
                return False

    def display_help(self) -> None:
        """Display help information for available commands."""
        help_text = Text()
        help_text.append("Available Commands:\n\n", style="bold")
        
        for key, verdict in self.valid_verdicts.items():
            help_text.append(f"  {key.upper()}", style="bold green")
            help_text.append(f" - {verdict}\n", style="white")
        
        help_text.append("\n  H", style="bold blue")
        help_text.append(" - Show this help\n", style="white")
        
        help_text.append("\nAfter selecting a verdict, you'll be asked to:\n", style="dim")
        help_text.append("1. Confirm your selection\n", style="dim")
        help_text.append("2. Optionally add a comment\n", style="dim")
        
        panel = Panel(
            help_text,
            title="[bold blue]Help - Verdict Classification[/bold blue]",
            border_style="blue"
        )
        
        self.console.print(panel)

    def _display_verdict_options(self) -> None:
        """Display the available verdict options in a formatted way."""
        options_text = Text()
        
        for key, verdict in self.valid_verdicts.items():
            if key == 'q':
                options_text.append(f"[{key.upper()}]", style="bold red")
                options_text.append(f" {verdict}  ", style="red")
            elif key == 's':
                options_text.append(f"[{key.upper()}]", style="bold green")
                options_text.append(f" {verdict}  ", style="green")
            else:
                options_text.append(f"[{key.upper()}]", style="bold yellow")
                options_text.append(f" {verdict}  ", style="white")
        
        options_text.append("\n[H]", style="bold blue")
        options_text.append(" Help", style="blue")
        
        self.console.print(options_text)

    def _get_comment(self) -> str:
        """
        Get optional comment from user.
        
        Returns:
            str: User comment or empty string.
        """
        try:
            self.console.print("\n[dim]Optional: Add a comment about this review (press Enter to skip)[/dim]")
            comment = self.console.input("[bold]Comment: [/bold]").strip()
            return comment
        except (KeyboardInterrupt, EOFError):
            return ""

    def get_undo_confirmation(self) -> bool:
        """
        Get confirmation for undo operation.
        
        Returns:
            bool: True if user wants to undo, False otherwise.
        """
        return self.get_confirmation("Undo the last review?")

    def prompt_for_input(self, prompt: str, default: Optional[str] = None) -> str:
        """
        Generic input prompt with optional default value.
        
        Args:
            prompt: Prompt message to display.
            default: Default value if user presses Enter.
            
        Returns:
            str: User input or default value.
        """
        try:
            if default:
                full_prompt = f"[bold]{prompt} [{default}]: [/bold]"
            else:
                full_prompt = f"[bold]{prompt}: [/bold]"
            
            user_input = self.console.input(full_prompt).strip()
            
            if not user_input and default:
                return default
            
            return user_input
            
        except (KeyboardInterrupt, EOFError):
            return default or ""

    def show_error_message(self, message: str) -> None:
        """
        Display an error message to the user.
        
        Args:
            message: Error message to display.
        """
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def show_info_message(self, message: str) -> None:
        """
        Display an informational message to the user.
        
        Args:
            message: Info message to display.
        """
        self.console.print(f"[bold blue]Info:[/bold blue] {message}")

    def show_success_message(self, message: str) -> None:
        """
        Display a success message to the user.
        
        Args:
            message: Success message to display.
        """
        self.console.print(f"[bold green]Success:[/bold green] {message}")

    def validate_verdict(self, verdict: str) -> bool:
        """
        Validate if a verdict is one of the expected values.
        
        Args:
            verdict: Verdict string to validate.
            
        Returns:
            bool: True if verdict is valid, False otherwise.
        """
        return verdict in self.valid_verdicts.values()

    def get_verdict_key(self, verdict: str) -> Optional[str]:
        """
        Get the key for a given verdict.
        
        Args:
            verdict: Verdict string.
            
        Returns:
            Optional[str]: Key for the verdict, or None if not found.
        """
        for key, value in self.valid_verdicts.items():
            if value == verdict:
                return key
        return None