#!/usr/bin/env python3
"""
Version validation script for VAITP-Auditor.

This script validates that version information is consistent across
all distribution methods and components.
"""

import sys
import os
from pathlib import Path
import re
import importlib.util

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent

def load_version_module():
    """Load the version module dynamically."""
    project_root = get_project_root()
    version_file = project_root / "vaitp_auditor" / "_version.py"
    
    spec = importlib.util.spec_from_file_location("_version", version_file)
    version_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(version_module)
    
    return version_module

def validate_setup_py():
    """Validate version in setup.py."""
    project_root = get_project_root()
    setup_file = project_root / "setup.py"
    
    if not setup_file.exists():
        return False, "setup.py not found"
    
    content = setup_file.read_text()
    
    # Check if it imports from _version
    if "from _version import __version__" not in content:
        return False, "setup.py does not import version from _version module"
    
    # Check if it uses the imported version
    if "version=__version__" not in content:
        return False, "setup.py does not use imported __version__"
    
    return True, "setup.py version is correctly configured"

def validate_package_init():
    """Validate version in package __init__.py."""
    project_root = get_project_root()
    init_file = project_root / "vaitp_auditor" / "__init__.py"
    
    if not init_file.exists():
        return False, "__init__.py not found"
    
    content = init_file.read_text()
    
    # Check if it imports from _version
    if "from ._version import __version__" not in content:
        return False, "__init__.py does not import version from _version module"
    
    return True, "Package __init__.py version is correctly configured"

def validate_gui_init():
    """Validate version in GUI __init__.py."""
    project_root = get_project_root()
    gui_init_file = project_root / "vaitp_auditor" / "gui" / "__init__.py"
    
    if not gui_init_file.exists():
        return False, "GUI __init__.py not found"
    
    content = gui_init_file.read_text()
    
    # Check if it imports from _version
    if "from .._version import __version__" not in content:
        return False, "GUI __init__.py does not import version from _version module"
    
    return True, "GUI __init__.py version is correctly configured"

def validate_version_format(version_str):
    """Validate version string format (semantic versioning)."""
    # Basic semantic versioning pattern: MAJOR.MINOR.PATCH
    pattern = r'^\d+\.\d+\.\d+$'
    
    if not re.match(pattern, version_str):
        return False, f"Version '{version_str}' does not follow semantic versioning (MAJOR.MINOR.PATCH)"
    
    return True, f"Version '{version_str}' follows semantic versioning"

def check_version_consistency():
    """Check that all version references are consistent."""
    try:
        version_module = load_version_module()
        version = version_module.__version__
        
        print(f"Current version: {version}")
        print(f"Full version: {version_module.get_full_version()}")
        print()
        
        # Validate version format
        format_valid, format_msg = validate_version_format(version)
        print(f"Version format: {'✓' if format_valid else '✗'} {format_msg}")
        
        # Validate setup.py
        setup_valid, setup_msg = validate_setup_py()
        print(f"setup.py: {'✓' if setup_valid else '✗'} {setup_msg}")
        
        # Validate package __init__.py
        init_valid, init_msg = validate_package_init()
        print(f"Package __init__.py: {'✓' if init_valid else '✗'} {init_msg}")
        
        # Validate GUI __init__.py
        gui_valid, gui_msg = validate_gui_init()
        print(f"GUI __init__.py: {'✓' if gui_valid else '✗'} {gui_msg}")
        
        all_valid = all([format_valid, setup_valid, init_valid, gui_valid])
        
        print()
        if all_valid:
            print("✓ All version checks passed!")
            return True
        else:
            print("✗ Some version checks failed!")
            return False
            
    except Exception as e:
        print(f"Error during validation: {e}")
        return False

def update_build_info(build_number=None, git_hash=None):
    """Update build information in version module."""
    project_root = get_project_root()
    version_file = project_root / "vaitp_auditor" / "_version.py"
    
    content = version_file.read_text()
    
    if build_number:
        content = re.sub(
            r'__build_number__ = .*',
            f'__build_number__ = "{build_number}"',
            content
        )
    
    if git_hash:
        content = re.sub(
            r'__git_hash__ = .*',
            f'__git_hash__ = "{git_hash}"',
            content
        )
    
    version_file.write_text(content)
    print(f"Updated build info: build_number={build_number}, git_hash={git_hash}")

def main():
    """Main validation entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate VAITP-Auditor version consistency")
    parser.add_argument("--build-number", help="Update build number")
    parser.add_argument("--git-hash", help="Update git hash")
    parser.add_argument("--update-build-info", action="store_true", 
                       help="Update build information")
    
    args = parser.parse_args()
    
    if args.update_build_info:
        update_build_info(args.build_number, args.git_hash)
        return
    
    success = check_version_consistency()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()