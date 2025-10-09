"""
Setup configuration for VAITP-Auditor package.
"""

from setuptools import setup, find_packages
import os
import sys

# Robust cross-platform version import for Windows compatibility
def get_version():
    """Get version using robust cross-platform method."""
    import importlib.util
    from pathlib import Path
    
    # Get the version file path
    setup_dir = Path(__file__).parent.absolute()
    version_file = setup_dir / "vaitp_auditor" / "_version.py"
    
    if not version_file.exists():
        # Fallback version if file doesn't exist
        return "0.1.0"
    
    try:
        # Load the version module directly using importlib
        spec = importlib.util.spec_from_file_location("_version", version_file)
        if spec is None or spec.loader is None:
            return "0.1.0"
        
        version_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(version_module)
        
        # Get version from the module
        return getattr(version_module, '__version__', "0.1.0")
        
    except Exception:
        # Fallback to hardcoded version if all else fails
        return "0.1.0"

__version__ = get_version()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vaitp-auditor",
    version=__version__,
    author="VAITP Research Team",
    description="Manual Code Verification Assistant for programmatically generated code snippets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "rich>=12.0.0",
        "openpyxl>=3.0.0",
        "pandas>=1.3.0",
    ],
    extras_require={
        "gui": [
            "customtkinter>=5.0.0",
            "pygments>=2.10.0",
            "pillow>=8.0.0",
            "psutil>=5.8.0",
            "setproctitle>=1.2.0",  # For better process naming on macOS/Linux
        ],
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=21.0.0",
            "mypy>=0.800",
            "flake8>=3.8.0",
            "pre-commit>=2.10.0",
        ],
        "all": [
            "customtkinter>=5.0.0",
            "pygments>=2.10.0",
            "pillow>=8.0.0",
            "psutil>=5.8.0",
            "setproctitle>=1.2.0",  # For better process naming on macOS/Linux
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=21.0.0",
            "mypy>=0.800",
            "flake8>=3.8.0",
            "pre-commit>=2.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "vaitp-auditor=vaitp_auditor.cli:main",
        ],
        "gui_scripts": [
            "vaitp-auditor-gui=vaitp_auditor.gui.gui_app:main",
        ],
    },
    package_data={
        "vaitp_auditor.gui": [
            "assets/icons/*.png",
            "assets/themes/*.json",
            "assets/fonts/*.ttf",
        ],
    },
    include_package_data=True,
)