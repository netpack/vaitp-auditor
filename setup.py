"""
Setup configuration for VAITP-Auditor package.
"""

from setuptools import setup, find_packages
import os
import sys

# Add the package directory to the path to import version
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vaitp_auditor'))
from _version import __version__

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