"""
GUI-specific data models for the VAITP-Auditor GUI interface.

This module contains dataclasses and configuration models specifically designed
for the GUI components, separate from the core business logic models.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import re


@dataclass
class GUIConfig:
    """Configuration specific to GUI behavior and appearance."""
    
    # Window dimensions
    window_width: int = 1400
    window_height: int = 800
    wizard_width: int = 750
    wizard_height: int = 600
    
    # Theme and appearance
    syntax_theme: str = "default"
    font_family: str = "Consolas"
    font_size: int = 11
    
    # UI behavior
    auto_scroll: bool = True
    show_line_numbers: bool = True
    wrap_text: bool = False
    enable_diff_highlighting: bool = True
    
    def __post_init__(self):
        """Validate configuration values after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate all configuration values and raise ValueError if invalid."""
        # Validate window dimensions
        if self.window_width < 800 or self.window_width > 3840:
            raise ValueError("window_width must be between 800 and 3840 pixels")
        
        if self.window_height < 600 or self.window_height > 2160:
            raise ValueError("window_height must be between 600 and 2160 pixels")
        
        if self.wizard_width < 400 or self.wizard_width > 1200:
            raise ValueError("wizard_width must be between 400 and 1200 pixels")
        
        if self.wizard_height < 300 or self.wizard_height > 800:
            raise ValueError("wizard_height must be between 300 and 800 pixels")
        
        # Validate theme
        valid_themes = {"default", "dark", "light", "system"}
        if self.syntax_theme not in valid_themes:
            raise ValueError(f"syntax_theme must be one of {valid_themes}")
        
        # Validate font
        if not self.font_family or not isinstance(self.font_family, str):
            raise ValueError("font_family must be a non-empty string")
        
        if self.font_size < 8 or self.font_size > 24:
            raise ValueError("font_size must be between 8 and 24")
        
        # Validate boolean flags
        if not isinstance(self.auto_scroll, bool):
            raise ValueError("auto_scroll must be a boolean")
        
        if not isinstance(self.show_line_numbers, bool):
            raise ValueError("show_line_numbers must be a boolean")
        
        if not isinstance(self.wrap_text, bool):
            raise ValueError("wrap_text must be a boolean")
        
        if not isinstance(self.enable_diff_highlighting, bool):
            raise ValueError("enable_diff_highlighting must be a boolean")
    
    def is_valid_dimensions(self) -> bool:
        """Check if the current dimensions are valid for the display."""
        try:
            self.validate()
            return True
        except ValueError:
            return False
    
    def get_aspect_ratio(self) -> float:
        """Get the aspect ratio of the main window."""
        return self.window_width / self.window_height
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            'window_width': self.window_width,
            'window_height': self.window_height,
            'wizard_width': self.wizard_width,
            'wizard_height': self.wizard_height,
            'syntax_theme': self.syntax_theme,
            'font_family': self.font_family,
            'font_size': self.font_size,
            'auto_scroll': self.auto_scroll,
            'show_line_numbers': self.show_line_numbers,
            'wrap_text': self.wrap_text,
            'enable_diff_highlighting': self.enable_diff_highlighting
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GUIConfig':
        """Create GUIConfig from dictionary."""
        return cls(**data)


@dataclass
class ProgressInfo:
    """Progress information for GUI display."""
    
    current: int
    total: int
    current_file: str
    experiment_name: str
    
    def __post_init__(self):
        """Validate progress information after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate progress information and raise ValueError if invalid."""
        if not isinstance(self.current, int) or self.current < 0:
            raise ValueError("current must be a non-negative integer")
        
        if not isinstance(self.total, int) or self.total < 0:
            raise ValueError("total must be a non-negative integer")
        
        if self.current > self.total:
            raise ValueError("current cannot be greater than total")
        
        if not isinstance(self.current_file, str):
            raise ValueError("current_file must be a string")
        
        if not isinstance(self.experiment_name, str) or not self.experiment_name.strip():
            raise ValueError("experiment_name must be a non-empty string")
    
    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100.0
    
    @property
    def remaining(self) -> int:
        """Get number of remaining items."""
        return self.total - self.current
    
    def is_complete(self) -> bool:
        """Check if progress is complete."""
        return self.current >= self.total
    
    def get_progress_text(self) -> str:
        """Get formatted progress text for display."""
        return f"{self.current}/{self.total} ({self.percentage:.1f}%)"
    
    def get_status_text(self) -> str:
        """Get formatted status text including current file."""
        if self.is_complete():
            return f"Review Complete - {self.experiment_name}"
        
        file_display = self.current_file if len(self.current_file) <= 30 else f"...{self.current_file[-27:]}"
        return f"Reviewing: {file_display}"


@dataclass
class VerdictButtonConfig:
    """Configuration for verdict buttons in the GUI."""
    
    verdict_id: str
    display_text: str
    key_binding: str
    icon_path: Optional[str] = None
    color_theme: str = "default"
    tooltip: Optional[str] = None
    
    def __post_init__(self):
        """Validate verdict button configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate verdict button configuration and raise ValueError if invalid."""
        # Validate verdict_id
        if not isinstance(self.verdict_id, str) or not self.verdict_id.strip():
            raise ValueError("verdict_id must be a non-empty string")
        
        # Verdict ID should be uppercase and use underscores
        if not re.match(r'^[A-Z][A-Z0-9_]*$', self.verdict_id):
            raise ValueError("verdict_id must be uppercase with underscores (e.g., 'SUCCESS', 'INVALID_CODE')")
        
        # Validate display_text
        if not isinstance(self.display_text, str) or not self.display_text.strip():
            raise ValueError("display_text must be a non-empty string")
        
        if len(self.display_text) > 50:
            raise ValueError("display_text must be 50 characters or less")
        
        # Validate key_binding
        if not isinstance(self.key_binding, str) or not self.key_binding.strip():
            raise ValueError("key_binding must be a non-empty string")
        
        # Key binding should be a single character or special key
        valid_key_pattern = r'^([a-zA-Z0-9]|F[1-9]|F1[0-2]|Escape|Enter|Space|Tab)$'
        if not re.match(valid_key_pattern, self.key_binding):
            raise ValueError("key_binding must be a single character, function key, or special key")
        
        # Validate color_theme
        valid_themes = {"default", "success", "warning", "error", "info", "primary"}
        if self.color_theme not in valid_themes:
            raise ValueError(f"color_theme must be one of {valid_themes}")
        
        # Validate optional fields
        if self.icon_path is not None:
            if not isinstance(self.icon_path, str) or not self.icon_path.strip():
                raise ValueError("icon_path must be a non-empty string if provided")
        
        if self.tooltip is not None:
            if not isinstance(self.tooltip, str):
                raise ValueError("tooltip must be a string if provided")
            if len(self.tooltip) > 200:
                raise ValueError("tooltip must be 200 characters or less")
    
    def get_display_with_shortcut(self) -> str:
        """Get display text with keyboard shortcut indicator."""
        return f"{self.display_text} ({self.key_binding})"
    
    def is_function_key(self) -> bool:
        """Check if the key binding is a function key."""
        return self.key_binding.startswith('F') and self.key_binding[1:].isdigit()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            'verdict_id': self.verdict_id,
            'display_text': self.display_text,
            'key_binding': self.key_binding,
            'icon_path': self.icon_path,
            'color_theme': self.color_theme,
            'tooltip': self.tooltip
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VerdictButtonConfig':
        """Create VerdictButtonConfig from dictionary."""
        return cls(**data)


# Default verdict button configurations
DEFAULT_VERDICT_BUTTONS: List[VerdictButtonConfig] = [
    VerdictButtonConfig(
        verdict_id="SUCCESS",
        display_text="Success",
        key_binding="s",
        color_theme="success",
        tooltip="Code generation was successful and matches expected output"
    ),
    VerdictButtonConfig(
        verdict_id="FAILURE_NO_CHANGE",
        display_text="Failure - No Change",
        key_binding="f",
        color_theme="error",
        tooltip="Code generation failed to make any changes"
    ),
    VerdictButtonConfig(
        verdict_id="INVALID_CODE",
        display_text="Invalid Code",
        key_binding="i",
        color_theme="error",
        tooltip="Generated code contains syntax errors or is invalid"
    ),
    VerdictButtonConfig(
        verdict_id="WRONG_VULNERABILITY",
        display_text="Wrong Vulnerability",
        key_binding="w",
        color_theme="warning",
        tooltip="Code addresses a different vulnerability than intended"
    ),
    VerdictButtonConfig(
        verdict_id="PARTIAL_SUCCESS",
        display_text="Partial Success",
        key_binding="p",
        color_theme="info",
        tooltip="Code generation was partially successful but incomplete"
    )
]


def get_default_gui_config() -> GUIConfig:
    """Get default GUI configuration."""
    return GUIConfig()


def get_default_verdict_buttons() -> List[VerdictButtonConfig]:
    """Get default verdict button configurations."""
    return DEFAULT_VERDICT_BUTTONS.copy()


def validate_verdict_buttons(buttons: List[VerdictButtonConfig]) -> None:
    """Validate a list of verdict button configurations."""
    if not isinstance(buttons, list):
        raise ValueError("buttons must be a list")
    
    if len(buttons) == 0:
        raise ValueError("at least one verdict button must be configured")
    
    if len(buttons) > 10:
        raise ValueError("maximum of 10 verdict buttons allowed")
    
    # Check for duplicate verdict IDs
    verdict_ids = [button.verdict_id for button in buttons]
    if len(verdict_ids) != len(set(verdict_ids)):
        raise ValueError("verdict_id values must be unique")
    
    # Check for duplicate key bindings
    key_bindings = [button.key_binding.lower() for button in buttons]
    if len(key_bindings) != len(set(key_bindings)):
        raise ValueError("key_binding values must be unique")
    
    # Validate each button
    for button in buttons:
        button.validate()