#!/bin/bash
# macOS launcher script for VAITP-Auditor GUI
# This script launches the GUI without showing Python version windows

# Suppress all output and launch in background to prevent console windows
exec > /dev/null 2>&1

# Function to launch with pythonw (preferred - no console)
launch_with_pythonw() {
    if command -v pythonw3 &> /dev/null; then
        nohup pythonw3 -c "import sys; sys.path.insert(0, '.'); from vaitp_auditor.gui.gui_app import main; main()" >/dev/null 2>&1 &
        disown
        return 0
    elif command -v pythonw &> /dev/null; then
        nohup pythonw -c "import sys; sys.path.insert(0, '.'); from vaitp_auditor.gui.gui_app import main; main()" >/dev/null 2>&1 &
        disown
        return 0
    else
        return 1
    fi
}

# Function to launch with regular python (fallback)
launch_with_python() {
    if command -v python3 &> /dev/null; then
        nohup python3 -c "import sys; sys.path.insert(0, '.'); from vaitp_auditor.gui.gui_app import main; main()" >/dev/null 2>&1 &
        disown
        return 0
    elif command -v python &> /dev/null; then
        nohup python -c "import sys; sys.path.insert(0, '.'); from vaitp_auditor.gui.gui_app import main; main()" >/dev/null 2>&1 &
        disown
        return 0
    else
        return 1
    fi
}

# Try pythonw first (suppresses console), then fallback to python
if ! launch_with_pythonw; then
    if ! launch_with_python; then
        # Only show error if we can't launch at all
        exec > /dev/tty 2>&1
        echo "Error: No suitable Python executable found"
        exit 1
    fi
fi

# Exit immediately to close this shell process
exit 0