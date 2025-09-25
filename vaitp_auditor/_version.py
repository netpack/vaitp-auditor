"""
Version information for VAITP-Auditor.

This module provides a single source of truth for version information
across all distribution methods and components.
"""

# Version information
__version__ = "0.1.0"
__version_info__ = tuple(map(int, __version__.split('.')))

# Release information
__release_date__ = "2025-09-25"
__release_name__ = "Initial Release"

# Build information (will be updated by build scripts)
__build_number__ = None
__git_hash__ = None

def get_version():
    """Get the current version string."""
    return __version__

def get_version_info():
    """Get version as a tuple of integers."""
    return __version_info__

def get_full_version():
    """Get full version string including build info if available."""
    version = __version__
    
    if __build_number__:
        version += f"+build.{__build_number__}"
    
    if __git_hash__:
        version += f".{__git_hash__[:8]}"
    
    return version

def get_release_info():
    """Get release information as a dictionary."""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "release_date": __release_date__,
        "release_name": __release_name__,
        "build_number": __build_number__,
        "git_hash": __git_hash__,
        "full_version": get_full_version()
    }