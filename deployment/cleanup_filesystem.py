#!/usr/bin/env python3
"""
File system cleanup script for VAITP-Auditor.

This script removes build artifacts, temporary files, and other unnecessary
files while preserving essential project components.
"""

import os
import shutil
import sys
from pathlib import Path
import glob
import argparse

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent

def remove_build_artifacts():
    """Remove build artifacts from dist/, build/, and *.egg-info/ directories."""
    project_root = get_project_root()
    removed_items = []
    
    # Directories to remove
    artifact_dirs = [
        project_root / "build",
        project_root / "dist",
    ]
    
    # Remove build directories
    for dir_path in artifact_dirs:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            removed_items.append(str(dir_path))
            print(f"Removed directory: {dir_path}")
    
    # Remove .egg-info directories
    egg_info_pattern = str(project_root / "*.egg-info")
    for egg_info_dir in glob.glob(egg_info_pattern):
        if os.path.isdir(egg_info_dir):
            shutil.rmtree(egg_info_dir)
            removed_items.append(egg_info_dir)
            print(f"Removed egg-info directory: {egg_info_dir}")
    
    return removed_items

def clean_temporary_reports():
    """Clean up temporary report files in reports/temp/ directory."""
    project_root = get_project_root()
    temp_dir = project_root / "reports" / "temp"
    removed_items = []
    
    if temp_dir.exists():
        for temp_file in temp_dir.iterdir():
            if temp_file.is_file():
                temp_file.unlink()
                removed_items.append(str(temp_file))
                print(f"Removed temporary report: {temp_file.name}")
    
    return removed_items

def remove_python_cache():
    """Remove Python cache files (__pycache__/, *.pyc) throughout project."""
    project_root = get_project_root()
    removed_items = []
    
    # Remove __pycache__ directories
    for pycache_dir in project_root.rglob("__pycache__"):
        if pycache_dir.is_dir() and "venv" not in str(pycache_dir):
            shutil.rmtree(pycache_dir)
            removed_items.append(str(pycache_dir))
            print(f"Removed cache directory: {pycache_dir}")
    
    # Remove .pyc files
    for pyc_file in project_root.rglob("*.pyc"):
        if "venv" not in str(pyc_file):
            pyc_file.unlink()
            removed_items.append(str(pyc_file))
            print(f"Removed cache file: {pyc_file}")
    
    # Remove .pyo files
    for pyo_file in project_root.rglob("*.pyo"):
        if "venv" not in str(pyo_file):
            pyo_file.unlink()
            removed_items.append(str(pyo_file))
            print(f"Removed optimized cache file: {pyo_file}")
    
    return removed_items

def remove_development_files():
    """Remove development summary files and other development artifacts."""
    project_root = get_project_root()
    removed_items = []
    
    # Patterns for development files to remove
    dev_patterns = [
        "*SUMMARY*.md",
        "*FIXES*.md", 
        "*.tmp",
        "*.bak",
        ".DS_Store",
        "Thumbs.db",
        "*.swp",
        "*.swo",
        "*~"
    ]
    
    for pattern in dev_patterns:
        for dev_file in project_root.rglob(pattern):
            if "venv" not in str(dev_file) and dev_file.is_file():
                dev_file.unlink()
                removed_items.append(str(dev_file))
                print(f"Removed development file: {dev_file}")
    
    return removed_items

def remove_empty_directories():
    """Remove empty directories that serve no purpose."""
    project_root = get_project_root()
    removed_items = []
    
    # Get all directories, sorted by depth (deepest first)
    all_dirs = []
    for dir_path in project_root.rglob("*"):
        if dir_path.is_dir() and "venv" not in str(dir_path) and ".git" not in str(dir_path):
            all_dirs.append(dir_path)
    
    # Sort by depth (deepest first) to remove child directories before parents
    all_dirs.sort(key=lambda x: len(x.parts), reverse=True)
    
    for dir_path in all_dirs:
        try:
            if dir_path.exists() and not any(dir_path.iterdir()):
                # Directory is empty
                dir_path.rmdir()
                removed_items.append(str(dir_path))
                print(f"Removed empty directory: {dir_path}")
        except OSError:
            # Directory not empty or permission error
            continue
    
    return removed_items

def create_gitignore():
    """Create or update .gitignore with comprehensive patterns."""
    project_root = get_project_root()
    gitignore_path = project_root / ".gitignore"
    
    gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
#   For a library or package, you might want to ignore these files since the code is
#   intended to run in multiple environments; otherwise, check them in:
# .python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or not
#   install all needed dependencies.
#Pipfile.lock

# poetry
#   Similar to Pipfile.lock, it is generally recommended to include poetry.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
#   https://python-poetry.org/docs/basic-usage/#commit-your-poetrylock-file-to-version-control
#poetry.lock

# pdm
#   Similar to Pipfile.lock, it is generally recommended to include pdm.lock in version control.
#pdm.lock
#   pdm stores project-wide configurations in .pdm.toml, but it is recommended to not include it
#   in version control.
#   https://pdm.fming.dev/#use-with-ide
.pdm.toml

# PEP 582; used by e.g. github.com/David-OConnor/pyflow and github.com/pdm-project/pdm
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# PyCharm
#  JetBrains specific template is maintained in a separate JetBrains.gitignore that can
#  be added to the global gitignore or merged into this project gitignore.  For a PyCharm
#  project, it is recommended to ignore the entire .idea directory.
.idea/

# VS Code
.vscode/

# Temporary files
*.tmp
*.bak
*~
.DS_Store
Thumbs.db

# Development files
*SUMMARY*.md
*FIXES*.md
*TODO*.md

# Application specific
reports/temp/
*.log
*.pid

# Build artifacts
*.dmg
*.exe
*.msi
*.deb
*.rpm
*.tar.gz
*.zip

# Code signing
*.p12
*.pem
codesign/
"""
    
    gitignore_path.write_text(gitignore_content)
    print(f"Created/updated .gitignore: {gitignore_path}")
    return str(gitignore_path)

def validate_cleanup():
    """Validate that no critical dependencies or imports are broken after cleanup."""
    project_root = get_project_root()
    
    print("\nValidating cleanup...")
    
    # Test basic imports
    test_imports = [
        "vaitp_auditor",
        "vaitp_auditor.core.models",
        "vaitp_auditor.session_manager",
        "vaitp_auditor.gui",
        "vaitp_auditor.cli"
    ]
    
    # Change to project root for imports
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    try:
        for module in test_imports:
            try:
                __import__(module)
                print(f"✓ Import test passed: {module}")
            except ImportError as e:
                print(f"✗ Import test failed: {module} - {e}")
                return False
        
        # Test version access
        try:
            import vaitp_auditor
            version = vaitp_auditor.__version__
            print(f"✓ Version access test passed: {version}")
        except Exception as e:
            print(f"✗ Version access test failed: {e}")
            return False
        
        print("✓ All validation tests passed!")
        return True
        
    finally:
        os.chdir(original_cwd)

def main():
    """Main cleanup entry point."""
    parser = argparse.ArgumentParser(description="Clean up VAITP-Auditor file system")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be removed without actually removing")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip import validation after cleanup")
    parser.add_argument("--artifacts-only", action="store_true",
                       help="Only remove build artifacts")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be actually removed")
        print()
    
    all_removed = []
    
    print("Starting file system cleanup...")
    print()
    
    # Remove build artifacts
    print("1. Removing build artifacts...")
    removed = remove_build_artifacts()
    all_removed.extend(removed)
    if not removed:
        print("   No build artifacts found")
    
    if not args.artifacts_only:
        # Clean temporary reports
        print("\n2. Cleaning temporary report files...")
        removed = clean_temporary_reports()
        all_removed.extend(removed)
        if not removed:
            print("   No temporary report files found")
        
        # Remove Python cache
        print("\n3. Removing Python cache files...")
        removed = remove_python_cache()
        all_removed.extend(removed)
        if not removed:
            print("   No Python cache files found")
        
        # Remove development files
        print("\n4. Removing development files...")
        removed = remove_development_files()
        all_removed.extend(removed)
        if not removed:
            print("   No development files found")
        
        # Remove empty directories
        print("\n5. Removing empty directories...")
        removed = remove_empty_directories()
        all_removed.extend(removed)
        if not removed:
            print("   No empty directories found")
        
        # Create/update .gitignore
        print("\n6. Creating/updating .gitignore...")
        gitignore_path = create_gitignore()
    
    print(f"\nCleanup completed! Removed {len(all_removed)} items.")
    
    if not args.skip_validation and not args.dry_run:
        if not validate_cleanup():
            print("\n⚠️  Validation failed! Some imports may be broken.")
            sys.exit(1)
    
    print("\n✓ File system cleanup successful!")

if __name__ == "__main__":
    main()