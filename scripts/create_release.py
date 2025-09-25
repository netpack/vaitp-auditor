#!/usr/bin/env python3
"""
Script to create a new release of VAITP-Auditor.
This script automates the release process including version bumping and tagging.
"""

import sys
import subprocess
import re
from pathlib import Path


def get_current_version():
    """Get the current version from _version.py."""
    version_file = Path("vaitp_auditor/_version.py")
    if not version_file.exists():
        print("Error: _version.py not found")
        sys.exit(1)
    
    content = version_file.read_text()
    match = re.search(r'__version__ = ["']([^"']+)["']', content)
    if not match:
        print("Error: Could not find version in _version.py")
        sys.exit(1)
    
    return match.group(1)


def bump_version(current_version, bump_type):
    """Bump version number based on type (major, minor, patch)."""
    parts = current_version.split('.')
    if len(parts) != 3:
        print(f"Error: Invalid version format: {current_version}")
        sys.exit(1)
    
    major, minor, patch = map(int, parts)
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        print(f"Error: Invalid bump type: {bump_type}")
        sys.exit(1)
    
    return f"{major}.{minor}.{patch}"


def update_version_file(new_version):
    """Update the version in _version.py."""
    version_file = Path("vaitp_auditor/_version.py")
    content = version_file.read_text()
    
    updated_content = re.sub(
        r'__version__ = ["'][^"']+["']',
        f'__version__ = "{new_version}"',
        content
    )
    
    version_file.write_text(updated_content)
    print(f"✓ Updated version to {new_version}")


def create_git_tag(version):
    """Create and push git tag."""
    tag_name = f"v{version}"
    
    # Create tag
    subprocess.run(["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"], check=True)
    print(f"✓ Created tag {tag_name}")
    
    # Push tag
    subprocess.run(["git", "push", "origin", tag_name], check=True)
    print(f"✓ Pushed tag {tag_name}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python create_release.py <major|minor|patch>")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    if bump_type not in ['major', 'minor', 'patch']:
        print("Error: Bump type must be major, minor, or patch")
        sys.exit(1)
    
    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    # Calculate new version
    new_version = bump_version(current_version, bump_type)
    print(f"New version: {new_version}")
    
    # Confirm with user
    response = input(f"Create release {new_version}? (y/N): ")
    if response.lower() != 'y':
        print("Release cancelled")
        sys.exit(0)
    
    # Update version file
    update_version_file(new_version)
    
    # Commit version change
    subprocess.run(["git", "add", "vaitp_auditor/_version.py"], check=True)
    subprocess.run(["git", "commit", "-m", f"Bump version to {new_version}"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("✓ Committed version change")
    
    # Create and push tag
    create_git_tag(new_version)
    
    print(f"🚀 Release {new_version} created successfully!")
    print("GitHub Actions will automatically build and publish the release.")


if __name__ == "__main__":
    main()
