"""
Unit tests for GUI-specific data models.

Tests all GUI data models including GUIConfig, ProgressInfo, and VerdictButtonConfig
with comprehensive validation and edge case coverage.
"""

import pytest
from dataclasses import FrozenInstanceError
from typing import Dict, Any

from vaitp_auditor.gui.models import (
    GUIConfig,
    ProgressInfo,
    VerdictButtonConfig,
    DEFAULT_VERDICT_BUTTONS,
    get_default_gui_config,
    get_default_verdict_buttons,
    validate_verdict_buttons
)


class TestGUIConfig:
    """Test cases for GUIConfig dataclass."""
    
    def test_default_initialization(self):
        """Test GUIConfig with default values."""
        config = GUIConfig()
        
        assert config.window_width == 1400
        assert config.window_height == 800
        assert config.wizard_width == 750
        assert config.wizard_height == 600
        assert config.syntax_theme == "default"
        assert config.font_family == "Consolas"
        assert config.font_size == 11
        assert config.auto_scroll is True
        assert config.show_line_numbers is True
        assert config.wrap_text is False
    
    def test_custom_initialization(self):
        """Test GUIConfig with custom values."""
        config = GUIConfig(
            window_width=1200,
            window_height=900,
            wizard_width=500,
            wizard_height=400,
            syntax_theme="dark",
            font_family="Monaco",
            font_size=12,
            auto_scroll=False,
            show_line_numbers=False,
            wrap_text=True
        )
        
        assert config.window_width == 1200
        assert config.window_height == 900
        assert config.wizard_width == 500
        assert config.wizard_height == 400
        assert config.syntax_theme == "dark"
        assert config.font_family == "Monaco"
        assert config.font_size == 12
        assert config.auto_scroll is False
        assert config.show_line_numbers is False
        assert config.wrap_text is True
    
    def test_window_width_validation(self):
        """Test window width validation."""
        # Valid values
        GUIConfig(window_width=800)
        GUIConfig(window_width=1920)
        GUIConfig(window_width=3840)
        
        # Invalid values
        with pytest.raises(ValueError, match="window_width must be between 800 and 3840"):
            GUIConfig(window_width=799)
        
        with pytest.raises(ValueError, match="window_width must be between 800 and 3840"):
            GUIConfig(window_width=3841)
    
    def test_window_height_validation(self):
        """Test window height validation."""
        # Valid values
        GUIConfig(window_height=600)
        GUIConfig(window_height=1080)
        GUIConfig(window_height=2160)
        
        # Invalid values
        with pytest.raises(ValueError, match="window_height must be between 600 and 2160"):
            GUIConfig(window_height=599)
        
        with pytest.raises(ValueError, match="window_height must be between 600 and 2160"):
            GUIConfig(window_height=2161)
    
    def test_wizard_dimensions_validation(self):
        """Test wizard dimensions validation."""
        # Valid values
        GUIConfig(wizard_width=400, wizard_height=300)
        GUIConfig(wizard_width=1200, wizard_height=800)
        
        # Invalid wizard width
        with pytest.raises(ValueError, match="wizard_width must be between 400 and 1200"):
            GUIConfig(wizard_width=399)
        
        with pytest.raises(ValueError, match="wizard_width must be between 400 and 1200"):
            GUIConfig(wizard_width=1201)
        
        # Invalid wizard height
        with pytest.raises(ValueError, match="wizard_height must be between 300 and 800"):
            GUIConfig(wizard_height=299)
        
        with pytest.raises(ValueError, match="wizard_height must be between 300 and 800"):
            GUIConfig(wizard_height=801)
    
    def test_syntax_theme_validation(self):
        """Test syntax theme validation."""
        # Valid themes
        for theme in ["default", "dark", "light", "system"]:
            GUIConfig(syntax_theme=theme)
        
        # Invalid theme
        with pytest.raises(ValueError, match="syntax_theme must be one of"):
            GUIConfig(syntax_theme="invalid_theme")
    
    def test_font_validation(self):
        """Test font validation."""
        # Valid font family
        GUIConfig(font_family="Arial")
        GUIConfig(font_family="Times New Roman")
        
        # Invalid font family
        with pytest.raises(ValueError, match="font_family must be a non-empty string"):
            GUIConfig(font_family="")
        
        with pytest.raises(ValueError, match="font_family must be a non-empty string"):
            GUIConfig(font_family=None)
        
        # Valid font sizes
        GUIConfig(font_size=8)
        GUIConfig(font_size=16)
        GUIConfig(font_size=24)
        
        # Invalid font sizes
        with pytest.raises(ValueError, match="font_size must be between 8 and 24"):
            GUIConfig(font_size=7)
        
        with pytest.raises(ValueError, match="font_size must be between 8 and 24"):
            GUIConfig(font_size=25)
    
    def test_boolean_validation(self):
        """Test boolean field validation."""
        # Valid boolean values
        GUIConfig(auto_scroll=True, show_line_numbers=False, wrap_text=True)
        
        # Invalid boolean values
        with pytest.raises(ValueError, match="auto_scroll must be a boolean"):
            GUIConfig(auto_scroll="true")
        
        with pytest.raises(ValueError, match="show_line_numbers must be a boolean"):
            GUIConfig(show_line_numbers=1)
        
        with pytest.raises(ValueError, match="wrap_text must be a boolean"):
            GUIConfig(wrap_text=0)
    
    def test_is_valid_dimensions(self):
        """Test is_valid_dimensions method."""
        config = GUIConfig()
        assert config.is_valid_dimensions() is True
        
        # Create invalid config by bypassing validation
        config.window_width = 500  # Too small
        assert config.is_valid_dimensions() is False
    
    def test_get_aspect_ratio(self):
        """Test aspect ratio calculation."""
        config = GUIConfig(window_width=1920, window_height=1080)
        assert abs(config.get_aspect_ratio() - 16/9) < 0.001
        
        config = GUIConfig(window_width=1600, window_height=1200)
        assert abs(config.get_aspect_ratio() - 4/3) < 0.001
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        config = GUIConfig(window_width=1200, font_size=14)
        data = config.to_dict()
        
        expected_keys = {
            'window_width', 'window_height', 'wizard_width', 'wizard_height',
            'syntax_theme', 'font_family', 'font_size', 'auto_scroll',
            'show_line_numbers', 'wrap_text'
        }
        assert set(data.keys()) == expected_keys
        assert data['window_width'] == 1200
        assert data['font_size'] == 14
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'window_width': 1200,
            'window_height': 900,
            'wizard_width': 500,
            'wizard_height': 400,
            'syntax_theme': 'dark',
            'font_family': 'Monaco',
            'font_size': 14,
            'auto_scroll': False,
            'show_line_numbers': True,
            'wrap_text': False
        }
        
        config = GUIConfig.from_dict(data)
        assert config.window_width == 1200
        assert config.window_height == 900
        assert config.syntax_theme == 'dark'
        assert config.font_family == 'Monaco'
        assert config.font_size == 14


class TestProgressInfo:
    """Test cases for ProgressInfo dataclass."""
    
    def test_valid_initialization(self):
        """Test ProgressInfo with valid values."""
        progress = ProgressInfo(
            current=5,
            total=10,
            current_file="test_file.py",
            experiment_name="test_experiment"
        )
        
        assert progress.current == 5
        assert progress.total == 10
        assert progress.current_file == "test_file.py"
        assert progress.experiment_name == "test_experiment"
    
    def test_current_validation(self):
        """Test current value validation."""
        # Valid values
        ProgressInfo(current=0, total=10, current_file="test.py", experiment_name="exp")
        ProgressInfo(current=5, total=10, current_file="test.py", experiment_name="exp")
        
        # Invalid values
        with pytest.raises(ValueError, match="current must be a non-negative integer"):
            ProgressInfo(current=-1, total=10, current_file="test.py", experiment_name="exp")
        
        with pytest.raises(ValueError, match="current must be a non-negative integer"):
            ProgressInfo(current="5", total=10, current_file="test.py", experiment_name="exp")
    
    def test_total_validation(self):
        """Test total value validation."""
        # Valid values
        ProgressInfo(current=0, total=0, current_file="test.py", experiment_name="exp")
        ProgressInfo(current=5, total=10, current_file="test.py", experiment_name="exp")
        
        # Invalid values
        with pytest.raises(ValueError, match="total must be a non-negative integer"):
            ProgressInfo(current=0, total=-1, current_file="test.py", experiment_name="exp")
        
        with pytest.raises(ValueError, match="total must be a non-negative integer"):
            ProgressInfo(current=0, total=10.5, current_file="test.py", experiment_name="exp")
    
    def test_current_greater_than_total(self):
        """Test validation when current > total."""
        with pytest.raises(ValueError, match="current cannot be greater than total"):
            ProgressInfo(current=15, total=10, current_file="test.py", experiment_name="exp")
    
    def test_current_file_validation(self):
        """Test current_file validation."""
        # Valid values
        ProgressInfo(current=0, total=10, current_file="", experiment_name="exp")
        ProgressInfo(current=0, total=10, current_file="test.py", experiment_name="exp")
        
        # Invalid values
        with pytest.raises(ValueError, match="current_file must be a string"):
            ProgressInfo(current=0, total=10, current_file=None, experiment_name="exp")
        
        with pytest.raises(ValueError, match="current_file must be a string"):
            ProgressInfo(current=0, total=10, current_file=123, experiment_name="exp")
    
    def test_experiment_name_validation(self):
        """Test experiment_name validation."""
        # Valid values
        ProgressInfo(current=0, total=10, current_file="test.py", experiment_name="exp")
        ProgressInfo(current=0, total=10, current_file="test.py", experiment_name="  exp  ")
        
        # Invalid values
        with pytest.raises(ValueError, match="experiment_name must be a non-empty string"):
            ProgressInfo(current=0, total=10, current_file="test.py", experiment_name="")
        
        with pytest.raises(ValueError, match="experiment_name must be a non-empty string"):
            ProgressInfo(current=0, total=10, current_file="test.py", experiment_name="   ")
        
        with pytest.raises(ValueError, match="experiment_name must be a non-empty string"):
            ProgressInfo(current=0, total=10, current_file="test.py", experiment_name=None)
    
    def test_percentage_property(self):
        """Test percentage calculation."""
        # Normal case
        progress = ProgressInfo(current=5, total=10, current_file="test.py", experiment_name="exp")
        assert progress.percentage == 50.0
        
        # Edge cases
        progress = ProgressInfo(current=0, total=10, current_file="test.py", experiment_name="exp")
        assert progress.percentage == 0.0
        
        progress = ProgressInfo(current=10, total=10, current_file="test.py", experiment_name="exp")
        assert progress.percentage == 100.0
        
        # Zero total
        progress = ProgressInfo(current=0, total=0, current_file="test.py", experiment_name="exp")
        assert progress.percentage == 100.0
    
    def test_remaining_property(self):
        """Test remaining calculation."""
        progress = ProgressInfo(current=3, total=10, current_file="test.py", experiment_name="exp")
        assert progress.remaining == 7
        
        progress = ProgressInfo(current=10, total=10, current_file="test.py", experiment_name="exp")
        assert progress.remaining == 0
    
    def test_is_complete(self):
        """Test completion check."""
        progress = ProgressInfo(current=5, total=10, current_file="test.py", experiment_name="exp")
        assert progress.is_complete() is False
        
        progress = ProgressInfo(current=10, total=10, current_file="test.py", experiment_name="exp")
        assert progress.is_complete() is True
        
        progress = ProgressInfo(current=0, total=0, current_file="test.py", experiment_name="exp")
        assert progress.is_complete() is True
    
    def test_get_progress_text(self):
        """Test progress text formatting."""
        progress = ProgressInfo(current=5, total=10, current_file="test.py", experiment_name="exp")
        assert progress.get_progress_text() == "5/10 (50.0%)"
        
        progress = ProgressInfo(current=1, total=3, current_file="test.py", experiment_name="exp")
        assert progress.get_progress_text() == "1/3 (33.3%)"
    
    def test_get_status_text(self):
        """Test status text formatting."""
        # Normal case
        progress = ProgressInfo(current=5, total=10, current_file="test.py", experiment_name="exp")
        assert progress.get_status_text() == "Reviewing: test.py"
        
        # Complete case
        progress = ProgressInfo(current=10, total=10, current_file="test.py", experiment_name="exp")
        assert progress.get_status_text() == "Review Complete - exp"
        
        # Long filename truncation
        long_filename = "very_long_filename_that_exceeds_thirty_characters.py"
        progress = ProgressInfo(current=5, total=10, current_file=long_filename, experiment_name="exp")
        status = progress.get_status_text()
        assert status.startswith("Reviewing: ...")
        assert len(status) <= 50  # Reasonable length limit


class TestVerdictButtonConfig:
    """Test cases for VerdictButtonConfig dataclass."""
    
    def test_valid_initialization(self):
        """Test VerdictButtonConfig with valid values."""
        config = VerdictButtonConfig(
            verdict_id="SUCCESS",
            display_text="Success",
            key_binding="s",
            icon_path="/path/to/icon.png",
            color_theme="success",
            tooltip="Success tooltip"
        )
        
        assert config.verdict_id == "SUCCESS"
        assert config.display_text == "Success"
        assert config.key_binding == "s"
        assert config.icon_path == "/path/to/icon.png"
        assert config.color_theme == "success"
        assert config.tooltip == "Success tooltip"
    
    def test_minimal_initialization(self):
        """Test VerdictButtonConfig with minimal required fields."""
        config = VerdictButtonConfig(
            verdict_id="SUCCESS",
            display_text="Success",
            key_binding="s"
        )
        
        assert config.verdict_id == "SUCCESS"
        assert config.display_text == "Success"
        assert config.key_binding == "s"
        assert config.icon_path is None
        assert config.color_theme == "default"
        assert config.tooltip is None
    
    def test_verdict_id_validation(self):
        """Test verdict_id validation."""
        # Valid verdict IDs
        valid_ids = ["SUCCESS", "FAILURE", "INVALID_CODE", "PARTIAL_SUCCESS", "A", "TEST_123"]
        for verdict_id in valid_ids:
            VerdictButtonConfig(verdict_id=verdict_id, display_text="Test", key_binding="t")
        
        # Invalid verdict IDs
        invalid_cases = [
            ("", "verdict_id must be a non-empty string"),
            ("   ", "verdict_id must be a non-empty string"),
            (None, "verdict_id must be a non-empty string"),
            ("success", "verdict_id must be uppercase with underscores"),
            ("Success", "verdict_id must be uppercase with underscores"),
            ("SUCCESS-CASE", "verdict_id must be uppercase with underscores"),
            ("123SUCCESS", "verdict_id must be uppercase with underscores"),
            ("SUCCESS CASE", "verdict_id must be uppercase with underscores")
        ]
        
        for invalid_id, expected_error in invalid_cases:
            with pytest.raises(ValueError, match=expected_error):
                VerdictButtonConfig(verdict_id=invalid_id, display_text="Test", key_binding="t")
    
    def test_display_text_validation(self):
        """Test display_text validation."""
        # Valid display text
        VerdictButtonConfig(verdict_id="SUCCESS", display_text="Success", key_binding="s")
        VerdictButtonConfig(verdict_id="SUCCESS", display_text="A" * 50, key_binding="s")
        
        # Invalid display text
        with pytest.raises(ValueError, match="display_text must be a non-empty string"):
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="", key_binding="s")
        
        with pytest.raises(ValueError, match="display_text must be a non-empty string"):
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="   ", key_binding="s")
        
        with pytest.raises(ValueError, match="display_text must be a non-empty string"):
            VerdictButtonConfig(verdict_id="SUCCESS", display_text=None, key_binding="s")
        
        with pytest.raises(ValueError, match="display_text must be 50 characters or less"):
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="A" * 51, key_binding="s")
    
    def test_key_binding_validation(self):
        """Test key_binding validation."""
        # Valid key bindings
        valid_keys = ["a", "Z", "1", "9", "F1", "F12", "Escape", "Enter", "Space", "Tab"]
        for key in valid_keys:
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="Test", key_binding=key)
        
        # Invalid key bindings
        invalid_cases = [
            ("", "key_binding must be a non-empty string"),
            ("   ", "key_binding must be a non-empty string"),
            (None, "key_binding must be a non-empty string"),
            ("ab", "key_binding must be a single character"),
            ("F13", "key_binding must be a single character"),
            ("Ctrl+a", "key_binding must be a single character"),
            ("!", "key_binding must be a single character")
        ]
        
        for invalid_key, expected_error in invalid_cases:
            with pytest.raises(ValueError, match=expected_error):
                VerdictButtonConfig(verdict_id="SUCCESS", display_text="Test", key_binding=invalid_key)
    
    def test_color_theme_validation(self):
        """Test color_theme validation."""
        # Valid themes
        valid_themes = ["default", "success", "warning", "error", "info", "primary"]
        for theme in valid_themes:
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="Test", key_binding="t", color_theme=theme)
        
        # Invalid theme
        with pytest.raises(ValueError, match="color_theme must be one of"):
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="Test", key_binding="t", color_theme="invalid")
    
    def test_optional_fields_validation(self):
        """Test validation of optional fields."""
        # Valid icon_path
        VerdictButtonConfig(verdict_id="SUCCESS", display_text="Test", key_binding="t", icon_path="/path/icon.png")
        VerdictButtonConfig(verdict_id="SUCCESS", display_text="Test", key_binding="t", icon_path=None)
        
        # Invalid icon_path
        with pytest.raises(ValueError, match="icon_path must be a non-empty string if provided"):
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="Test", key_binding="t", icon_path="")
        
        with pytest.raises(ValueError, match="icon_path must be a non-empty string if provided"):
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="Test", key_binding="t", icon_path="   ")
        
        # Valid tooltip
        VerdictButtonConfig(verdict_id="SUCCESS", display_text="Test", key_binding="t", tooltip="Valid tooltip")
        VerdictButtonConfig(verdict_id="SUCCESS", display_text="Test", key_binding="t", tooltip="")
        VerdictButtonConfig(verdict_id="SUCCESS", display_text="Test", key_binding="t", tooltip=None)
        
        # Invalid tooltip
        with pytest.raises(ValueError, match="tooltip must be a string if provided"):
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="Test", key_binding="t", tooltip=123)
        
        with pytest.raises(ValueError, match="tooltip must be 200 characters or less"):
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="Test", key_binding="t", tooltip="A" * 201)
    
    def test_get_display_with_shortcut(self):
        """Test display text with shortcut formatting."""
        config = VerdictButtonConfig(verdict_id="SUCCESS", display_text="Success", key_binding="s")
        assert config.get_display_with_shortcut() == "Success (s)"
        
        config = VerdictButtonConfig(verdict_id="HELP", display_text="Help", key_binding="F1")
        assert config.get_display_with_shortcut() == "Help (F1)"
    
    def test_is_function_key(self):
        """Test function key detection."""
        config = VerdictButtonConfig(verdict_id="SUCCESS", display_text="Success", key_binding="s")
        assert config.is_function_key() is False
        
        config = VerdictButtonConfig(verdict_id="HELP", display_text="Help", key_binding="F1")
        assert config.is_function_key() is True
        
        config = VerdictButtonConfig(verdict_id="HELP", display_text="Help", key_binding="F12")
        assert config.is_function_key() is True
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        config = VerdictButtonConfig(
            verdict_id="SUCCESS",
            display_text="Success",
            key_binding="s",
            icon_path="/icon.png",
            color_theme="success",
            tooltip="Success tooltip"
        )
        
        data = config.to_dict()
        expected_keys = {'verdict_id', 'display_text', 'key_binding', 'icon_path', 'color_theme', 'tooltip'}
        assert set(data.keys()) == expected_keys
        assert data['verdict_id'] == "SUCCESS"
        assert data['display_text'] == "Success"
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'verdict_id': 'SUCCESS',
            'display_text': 'Success',
            'key_binding': 's',
            'icon_path': '/icon.png',
            'color_theme': 'success',
            'tooltip': 'Success tooltip'
        }
        
        config = VerdictButtonConfig.from_dict(data)
        assert config.verdict_id == 'SUCCESS'
        assert config.display_text == 'Success'
        assert config.key_binding == 's'
        assert config.icon_path == '/icon.png'
        assert config.color_theme == 'success'
        assert config.tooltip == 'Success tooltip'


class TestDefaultConfigurations:
    """Test cases for default configurations and utility functions."""
    
    def test_get_default_gui_config(self):
        """Test default GUI configuration."""
        config = get_default_gui_config()
        assert isinstance(config, GUIConfig)
        assert config.window_width == 1400
        assert config.window_height == 800
    
    def test_get_default_verdict_buttons(self):
        """Test default verdict buttons."""
        buttons = get_default_verdict_buttons()
        assert isinstance(buttons, list)
        assert len(buttons) == 6
        
        # Check that all buttons are valid
        for button in buttons:
            assert isinstance(button, VerdictButtonConfig)
            button.validate()
        
        # Check specific expected buttons
        verdict_ids = [button.verdict_id for button in buttons]
        expected_ids = ["SUCCESS", "FAILURE_NO_CHANGE", "INVALID_CODE", "WRONG_VULNERABILITY", "PARTIAL_SUCCESS", "CUSTOM"]
        assert verdict_ids == expected_ids
    
    def test_default_verdict_buttons_constant(self):
        """Test DEFAULT_VERDICT_BUTTONS constant."""
        assert isinstance(DEFAULT_VERDICT_BUTTONS, list)
        assert len(DEFAULT_VERDICT_BUTTONS) == 6
        
        # Verify all buttons are valid
        for button in DEFAULT_VERDICT_BUTTONS:
            assert isinstance(button, VerdictButtonConfig)
            button.validate()
    
    def test_validate_verdict_buttons_valid(self):
        """Test validate_verdict_buttons with valid input."""
        buttons = get_default_verdict_buttons()
        validate_verdict_buttons(buttons)  # Should not raise
        
        # Single button
        single_button = [VerdictButtonConfig(verdict_id="SUCCESS", display_text="Success", key_binding="s")]
        validate_verdict_buttons(single_button)  # Should not raise
    
    def test_validate_verdict_buttons_invalid_type(self):
        """Test validate_verdict_buttons with invalid input type."""
        with pytest.raises(ValueError, match="buttons must be a list"):
            validate_verdict_buttons("not a list")
        
        with pytest.raises(ValueError, match="buttons must be a list"):
            validate_verdict_buttons(None)
    
    def test_validate_verdict_buttons_empty(self):
        """Test validate_verdict_buttons with empty list."""
        with pytest.raises(ValueError, match="at least one verdict button must be configured"):
            validate_verdict_buttons([])
    
    def test_validate_verdict_buttons_too_many(self):
        """Test validate_verdict_buttons with too many buttons."""
        buttons = []
        for i in range(11):
            buttons.append(VerdictButtonConfig(
                verdict_id=f"BUTTON_{i}",
                display_text=f"Button {i}",
                key_binding=str(i) if i < 10 else "a"
            ))
        
        with pytest.raises(ValueError, match="maximum of 10 verdict buttons allowed"):
            validate_verdict_buttons(buttons)
    
    def test_validate_verdict_buttons_duplicate_ids(self):
        """Test validate_verdict_buttons with duplicate verdict IDs."""
        buttons = [
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="Success 1", key_binding="s"),
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="Success 2", key_binding="t")
        ]
        
        with pytest.raises(ValueError, match="verdict_id values must be unique"):
            validate_verdict_buttons(buttons)
    
    def test_validate_verdict_buttons_duplicate_keys(self):
        """Test validate_verdict_buttons with duplicate key bindings."""
        buttons = [
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="Success", key_binding="s"),
            VerdictButtonConfig(verdict_id="FAILURE", display_text="Failure", key_binding="s")
        ]
        
        with pytest.raises(ValueError, match="key_binding values must be unique"):
            validate_verdict_buttons(buttons)
    
    def test_validate_verdict_buttons_case_insensitive_keys(self):
        """Test validate_verdict_buttons with case-insensitive key binding duplicates."""
        buttons = [
            VerdictButtonConfig(verdict_id="SUCCESS", display_text="Success", key_binding="s"),
            VerdictButtonConfig(verdict_id="FAILURE", display_text="Failure", key_binding="S")
        ]
        
        with pytest.raises(ValueError, match="key_binding values must be unique"):
            validate_verdict_buttons(buttons)
    
    def test_validate_verdict_buttons_invalid_button(self):
        """Test validate_verdict_buttons with invalid button configuration."""
        # The invalid button will fail during creation due to validation in __post_init__
        with pytest.raises(ValueError, match="verdict_id must be uppercase with underscores"):
            buttons = [
                VerdictButtonConfig(verdict_id="SUCCESS", display_text="Success", key_binding="s"),
                VerdictButtonConfig(verdict_id="invalid_id", display_text="Invalid", key_binding="i")  # lowercase verdict_id
            ]


if __name__ == "__main__":
    pytest.main([__file__])