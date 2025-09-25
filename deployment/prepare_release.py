#!/usr/bin/env python3
"""
Release preparation script for VAITP-Auditor.

This script automates version updates, changelog preparation, and release validation
to ensure consistent and reliable releases across all platforms.
"""

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def validate_version_format(version: str) -> bool:
    """Validate semantic version format."""
    # Semantic version pattern with optional pre-release
    pattern = r'^v?(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z]+)\.(\d+))?$'
    return bool(re.match(pattern, version))


def parse_version(version: str) -> Dict[str, Optional[str]]:
    """Parse version string into components."""
    # Remove 'v' prefix if present
    clean_version = version.lstrip('v')
    
    pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z]+)\.(\d+))?$'
    match = re.match(pattern, clean_version)
    
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    
    return {
        'major': match.group(1),
        'minor': match.group(2),
        'patch': match.group(3),
        'prerelease_type': match.group(4),
        'prerelease_number': match.group(5),
        'full': clean_version
    }


def get_current_version() -> str:
    """Get current version from _version.py."""
    version_file = get_project_root() / "vaitp_auditor" / "_version.py"
    
    if not version_file.exists():
        raise FileNotFoundError(f"Version file not found: {version_file}")
    
    content = version_file.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    
    if not match:
        raise ValueError("Could not find version in _version.py")
    
    return match.group(1)


def update_version_file(new_version: str, dry_run: bool = False) -> None:
    """Update the main version file."""
    version_file = get_project_root() / "vaitp_auditor" / "_version.py"
    
    if not version_file.exists():
        raise FileNotFoundError(f"Version file not found: {version_file}")
    
    content = version_file.read_text()
    new_content = re.sub(
        r'__version__\s*=\s*["\'][^"\']+["\']',
        f'__version__ = "{new_version}"',
        content
    )
    
    if dry_run:
        logger.info(f"Would update {version_file} with version {new_version}")
    else:
        version_file.write_text(new_content)
        logger.info(f"Updated {version_file} with version {new_version}")


def update_setup_py(new_version: str, dry_run: bool = False) -> None:
    """Update version in setup.py."""
    setup_file = get_project_root() / "setup.py"
    
    if not setup_file.exists():
        logger.warning(f"setup.py not found: {setup_file}")
        return
    
    content = setup_file.read_text()
    
    # Update version in setup() call
    new_content = re.sub(
        r'version\s*=\s*["\'][^"\']+["\']',
        f'version="{new_version}"',
        content
    )
    
    if dry_run:
        logger.info(f"Would update {setup_file} with version {new_version}")
    else:
        setup_file.write_text(new_content)
        logger.info(f"Updated {setup_file} with version {new_version}")


def update_pyinstaller_spec(new_version: str, dry_run: bool = False) -> None:
    """Update version in PyInstaller spec file."""
    spec_file = get_project_root() / "deployment" / "pyinstaller_config.spec"
    
    if not spec_file.exists():
        logger.warning(f"PyInstaller spec not found: {spec_file}")
        return
    
    content = spec_file.read_text()
    
    # Update version in version info
    new_content = re.sub(
        r"'FileVersion',\s*'[^']*'",
        f"'FileVersion', '{new_version}'",
        content
    )
    new_content = re.sub(
        r"'ProductVersion',\s*'[^']*'",
        f"'ProductVersion', '{new_version}'",
        new_content
    )
    
    if dry_run:
        logger.info(f"Would update {spec_file} with version {new_version}")
    else:
        spec_file.write_text(new_content)
        logger.info(f"Updated {spec_file} with version {new_version}")


def validate_version_consistency() -> bool:
    """Validate that version is consistent across all files."""
    files_to_check = [
        (get_project_root() / "vaitp_auditor" / "_version.py", r'__version__\s*=\s*["\']([^"\']+)["\']'),
        (get_project_root() / "setup.py", r'version\s*=\s*["\']([^"\']+)["\']'),
    ]
    
    versions = {}
    
    for file_path, pattern in files_to_check:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue
        
        content = file_path.read_text()
        match = re.search(pattern, content)
        
        if match:
            versions[str(file_path)] = match.group(1)
        else:
            logger.warning(f"Could not find version in {file_path}")
    
    if not versions:
        logger.error("No version information found in any file")
        return False
    
    # Check if all versions are the same
    unique_versions = set(versions.values())
    
    if len(unique_versions) == 1:
        logger.info(f"Version consistency validated: {list(unique_versions)[0]}")
        return True
    else:
        logger.error("Version inconsistency detected:")
        for file_path, version in versions.items():
            logger.error(f"  {file_path}: {version}")
        return False


def create_changelog_entry(version: str, changes: List[str], dry_run: bool = False) -> None:
    """Create or update changelog entry for the version."""
    changelog_file = get_project_root() / "CHANGELOG.md"
    
    if not changelog_file.exists():
        logger.warning("CHANGELOG.md not found, creating new one")
        if not dry_run:
            changelog_file.write_text("# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n")
    
    # Parse version to determine if it's a pre-release
    version_info = parse_version(version)
    is_prerelease = version_info['prerelease_type'] is not None
    
    # Create changelog entry
    date_str = datetime.now().strftime("%Y-%m-%d")
    entry_header = f"## [{version}] - {date_str}"
    
    if is_prerelease:
        entry_header += f" (Pre-release)"
    
    entry_lines = [entry_header, ""]
    
    if changes:
        # Categorize changes
        added = [c for c in changes if c.lower().startswith(('add', 'new', 'implement'))]
        changed = [c for c in changes if c.lower().startswith(('change', 'update', 'modify', 'improve'))]
        fixed = [c for c in changes if c.lower().startswith(('fix', 'resolve', 'correct'))]
        removed = [c for c in changes if c.lower().startswith(('remove', 'delete', 'drop'))]
        other = [c for c in changes if c not in added + changed + fixed + removed]
        
        if added:
            entry_lines.extend(["### Added", ""] + [f"- {change}" for change in added] + [""])
        if changed:
            entry_lines.extend(["### Changed", ""] + [f"- {change}" for change in changed] + [""])
        if fixed:
            entry_lines.extend(["### Fixed", ""] + [f"- {change}" for change in fixed] + [""])
        if removed:
            entry_lines.extend(["### Removed", ""] + [f"- {change}" for change in removed] + [""])
        if other:
            entry_lines.extend(["### Other", ""] + [f"- {change}" for change in other] + [""])
    else:
        entry_lines.extend([
            "### Added",
            "- Initial release",
            ""
        ])
    
    entry_text = "\n".join(entry_lines)
    
    if dry_run:
        logger.info(f"Would add changelog entry:\n{entry_text}")
    else:
        # Read existing changelog
        content = changelog_file.read_text()
        
        # Find insertion point (after header, before first version entry)
        lines = content.split('\n')
        insert_index = len(lines)
        
        for i, line in enumerate(lines):
            if line.startswith('## [') and i > 0:
                insert_index = i
                break
        
        # Insert new entry
        lines.insert(insert_index, entry_text)
        
        # Write updated changelog
        changelog_file.write_text('\n'.join(lines))
        logger.info(f"Updated CHANGELOG.md with entry for version {version}")


def run_validation_checks() -> bool:
    """Run pre-release validation checks."""
    logger.info("Running pre-release validation checks...")
    
    checks_passed = True
    
    # Check version consistency
    if not validate_version_consistency():
        checks_passed = False
    
    # Check that required files exist
    required_files = [
        "vaitp_auditor/_version.py",
        "setup.py",
        "README.md",
        "CHANGELOG.md",
        "deployment/build_executable.py",
        "deployment/pyinstaller_config.spec",
    ]
    
    project_root = get_project_root()
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            logger.error(f"Required file missing: {file_path}")
            checks_passed = False
        else:
            logger.info(f"✓ Found required file: {file_path}")
    
    # Check that we're on main branch (if git is available)
    try:
        import subprocess
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, cwd=project_root)
        if result.returncode == 0:
            current_branch = result.stdout.strip()
            if current_branch not in ['main', 'master']:
                logger.warning(f"Not on main branch (current: {current_branch})")
                # Don't fail for this, just warn
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.info("Git not available, skipping branch check")
    
    return checks_passed


def main():
    parser = argparse.ArgumentParser(
        description="Prepare VAITP-Auditor release",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --version 1.0.0                    # Prepare stable release
  %(prog)s --version 1.1.0-beta.1 --beta      # Prepare beta release
  %(prog)s --version 1.0.1 --patch            # Prepare patch release
  %(prog)s --version 1.0.0 --dry-run          # Show what would be done
        """
    )
    
    parser.add_argument('--version', required=True, 
                       help='Version to prepare (e.g., 1.0.0, 1.1.0-beta.1)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--beta', action='store_true',
                       help='Prepare beta release')
    parser.add_argument('--patch', action='store_true',
                       help='Prepare patch release (minimal validation)')
    parser.add_argument('--hotfix', action='store_true',
                       help='Prepare hotfix release (emergency patch)')
    parser.add_argument('--update-changelog', action='store_true',
                       help='Update CHANGELOG.md with new entry')
    parser.add_argument('--changes', nargs='*',
                       help='List of changes for changelog')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip pre-release validation checks')
    
    args = parser.parse_args()
    
    try:
        # Validate version format
        if not validate_version_format(args.version):
            logger.error(f"Invalid version format: {args.version}")
            logger.error("Expected format: X.Y.Z or X.Y.Z-type.N (e.g., 1.0.0, 1.1.0-beta.1)")
            sys.exit(1)
        
        # Parse version
        version_info = parse_version(args.version)
        clean_version = version_info['full']
        
        logger.info(f"Preparing release for version {clean_version}")
        
        # Get current version for comparison
        try:
            current_version = get_current_version()
            logger.info(f"Current version: {current_version}")
        except Exception as e:
            logger.warning(f"Could not get current version: {e}")
            current_version = None
        
        # Run validation checks (unless skipped or hotfix)
        if not args.skip_validation and not args.hotfix:
            if not run_validation_checks():
                logger.error("Validation checks failed")
                if not args.patch:  # Allow patches to proceed with warnings
                    sys.exit(1)
        
        # Update version files
        logger.info("Updating version files...")
        update_version_file(clean_version, args.dry_run)
        update_setup_py(clean_version, args.dry_run)
        update_pyinstaller_spec(clean_version, args.dry_run)
        
        # Update changelog if requested
        if args.update_changelog:
            changes = args.changes or []
            create_changelog_entry(clean_version, changes, args.dry_run)
        
        # Final validation
        if not args.dry_run and not args.skip_validation:
            logger.info("Validating version consistency...")
            if not validate_version_consistency():
                logger.error("Version consistency validation failed after updates")
                sys.exit(1)
        
        # Success message
        if args.dry_run:
            logger.info(f"Dry run completed. Would prepare release {clean_version}")
        else:
            logger.info(f"Successfully prepared release {clean_version}")
            logger.info("Next steps:")
            logger.info("1. Review and commit changes")
            logger.info(f"2. Create and push tag: git tag v{clean_version} && git push origin v{clean_version}")
            logger.info("3. Monitor GitHub Actions workflow")
        
    except Exception as e:
        logger.error(f"Release preparation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()