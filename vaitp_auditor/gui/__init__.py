"""
VAITP-Auditor GUI Package

This package provides a modern desktop interface for the VAITP-Auditor tool
using CustomTkinter for an intuitive visual workflow.
"""

from .._version import __version__, get_version, get_version_info, get_full_version

__author__ = "VAITP-Auditor Team"

# Import GUI data models
from .models import (
    GUIConfig,
    ProgressInfo,
    VerdictButtonConfig,
    DEFAULT_VERDICT_BUTTONS,
    get_default_gui_config,
    get_default_verdict_buttons,
    validate_verdict_buttons
)

# Import GUI error handling
from .error_handler import (
    GUIErrorHandler,
    ErrorDialogBuilder,
    ProgressErrorHandler,
    show_file_error,
    show_database_error,
    show_validation_error,
    show_performance_warning,
    show_network_error,
    show_permission_error
)

# Import progress widgets
from .progress_widgets import (
    ProgressState,
    ProgressInfo as ProgressInfoWidget,
    ProgressCallback,
    LoadingIndicator,
    ProgressDialog,
    ProgressManager,
    DialogProgressCallback,
    show_loading_dialog,
    run_with_progress
)

# Import Setup Wizard components
from .setup_wizard import (
    SetupWizard,
    SetupStep,
    NamingStep
)

# Import Main Review Window components
from .main_review_window import (
    MainReviewWindow,
    HeaderFrame,
    CodePanelsFrame,
    ActionsFrame
)

__all__ = [
    'GUIConfig',
    'ProgressInfo', 
    'VerdictButtonConfig',
    'DEFAULT_VERDICT_BUTTONS',
    'get_default_gui_config',
    'get_default_verdict_buttons',
    'validate_verdict_buttons',
    'GUIErrorHandler',
    'ErrorDialogBuilder',
    'ProgressErrorHandler',
    'show_file_error',
    'show_database_error',
    'show_validation_error',
    'show_performance_warning',
    'show_network_error',
    'show_permission_error',
    'ProgressState',
    'ProgressInfoWidget',
    'ProgressCallback',
    'LoadingIndicator',
    'ProgressDialog',
    'ProgressManager',
    'DialogProgressCallback',
    'show_loading_dialog',
    'run_with_progress',
    'SetupWizard',
    'SetupStep',
    'NamingStep',
    'MainReviewWindow',
    'HeaderFrame',
    'CodePanelsFrame',
    'ActionsFrame'
]