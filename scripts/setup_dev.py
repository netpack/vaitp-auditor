#!/usr/bin/env python3
"""
Development environment setup script for VAITP-Auditor.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and handle errors."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result.returncode == 0


def setup_virtual_environment():
    """Set up Python virtual environment."""
    print("🐍 Setting up Python virtual environment...")
    
    if not run_command(f"{sys.executable} -m venv venv"):
        print("❌ Failed to create virtual environment")
        return False
    
    # Determine activation script path
    if os.name == 'nt':  # Windows
        activate_script = "venv\Scripts\activate"
        pip_path = "venv\Scripts\pip"
    else:  # Unix-like
        activate_script = "venv/bin/activate"
        pip_path = "venv/bin/pip"
    
    print(f"✓ Virtual environment created")
    print(f"To activate: source {activate_script}")
    
    return True


def install_dependencies():
    """Install development dependencies."""
    print("📦 Installing dependencies...")
    
    # Determine pip path
    if os.name == 'nt':  # Windows
        pip_path = "venv\Scripts\pip"
    else:  # Unix-like
        pip_path = "venv/bin/pip"
    
    # Install in development mode with all extras
    if not run_command(f"{pip_path} install -e .[all]"):
        print("❌ Failed to install dependencies")
        return False
    
    print("✓ Dependencies installed")
    return True


def setup_pre_commit():
    """Set up pre-commit hooks."""
    print("🔧 Setting up pre-commit hooks...")
    
    # Determine python path
    if os.name == 'nt':  # Windows
        python_path = "venv\Scripts\python"
    else:  # Unix-like
        python_path = "venv/bin/python"
    
    if not run_command(f"{python_path} -m pre_commit install"):
        print("⚠️  Failed to install pre-commit hooks (optional)")
        return False
    
    print("✓ Pre-commit hooks installed")
    return True


def run_tests():
    """Run the test suite to verify setup."""
    print("🧪 Running tests to verify setup...")
    
    # Determine python path
    if os.name == 'nt':  # Windows
        python_path = "venv\Scripts\python"
    else:  # Unix-like
        python_path = "venv/bin/python"
    
    if not run_command(f"{python_path} -m pytest tests/ -v", check=False):
        print("⚠️  Some tests failed - this might be expected in a new setup")
        return False
    
    print("✓ Tests completed")
    return True


def main():
    """Main setup function."""
    print("🚀 Setting up VAITP-Auditor development environment...")
    print()
    
    # Check if we're in the right directory
    if not Path("setup.py").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Setup steps
    steps = [
        ("Virtual Environment", setup_virtual_environment),
        ("Dependencies", install_dependencies),
        ("Pre-commit Hooks", setup_pre_commit),
        ("Test Suite", run_tests),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{'='*50}")
        print(f"Setting up: {step_name}")
        print('='*50)
        
        if not step_func():
            print(f"\n⚠️  {step_name} setup had issues, but continuing...")
    
    print("\n" + "="*50)
    print("🎉 Development environment setup complete!")
    print("="*50)
    print()
    print("Next steps:")
    print("1. Activate the virtual environment:")
    if os.name == 'nt':  # Windows
        print("   venv\Scripts\activate")
    else:  # Unix-like
        print("   source venv/bin/activate")
    print("2. Run the application:")
    print("   python -m vaitp_auditor.gui")
    print("3. Start developing!")
    print()
    print("Useful commands:")
    print("- Run tests: pytest")
    print("- Format code: black .")
    print("- Type checking: mypy vaitp_auditor/")
    print("- Build executable: python deployment/build_executable.py")


if __name__ == "__main__":
    main()
