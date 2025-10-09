#!/bin/bash
"""
VAITP-Auditor macOS Launcher Script

This script launches VAITP-Auditor with proper icon handling on macOS.
"""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Launching VAITP-Auditor on macOS with icon fix..."
    
    # Set environment variables for proper app identity
    export CFBundleName="VAITP-Auditor"
    export CFBundleDisplayName="VAITP-Auditor"
    export CFBundleIdentifier="com.vaitp.auditor"
    
    # Launch using the Python launcher
    python vaitp_auditor_launcher.py
else
    echo "🐧 Launching VAITP-Auditor on non-macOS system..."
    
    # For non-macOS systems, launch normally
    python -m vaitp_auditor.gui.gui_app
fi