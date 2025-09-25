"""
VAITP-Auditor: Manual Code Verification Assistant

A Python-based tool for efficient manual verification of programmatically 
generated code snippets through side-by-side comparison and classification.
"""

from ._version import __version__, get_version, get_version_info, get_full_version, get_release_info

__author__ = "VAITP Research Team"

from .core.models import CodePair, ReviewResult, DiffLine, SessionState, SessionConfig
from .session_manager import SessionManager
from .utils.logging_config import setup_logging, get_logger
from .utils.error_handling import VaitpError, handle_errors
from .utils.resource_manager import cleanup_resources, get_resource_manager

__all__ = [
    "CodePair",
    "ReviewResult", 
    "DiffLine",
    "SessionState",
    "SessionConfig",
    "SessionManager",
    "setup_logging",
    "get_logger",
    "VaitpError",
    "handle_errors",
    "cleanup_resources",
    "get_resource_manager"
]