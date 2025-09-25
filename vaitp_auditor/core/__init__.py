"""
Core components for VAITP-Auditor including data models and business logic.
"""

from .models import CodePair, ReviewResult, DiffLine, SessionState, SessionConfig
from .differ import CodeDiffer

__all__ = [
    "CodePair",
    "ReviewResult", 
    "DiffLine",
    "SessionState",
    "SessionConfig",
    "CodeDiffer"
]