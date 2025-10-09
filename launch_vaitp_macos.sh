#!/bin/bash
# Ultimate macOS launcher for VAITP-Auditor GUI
# Uses osascript to launch without any terminal involvement

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use osascript to launch Python without terminal
osascript -e "
tell application \"System Events\"
    do shell script \"cd '$SCRIPT_DIR' && pythonw3 -c 'import sys; sys.path.insert(0, \\\".\\\"); from vaitp_auditor.gui.gui_app import main; main()' > /dev/null 2>&1 &\"
end tell
" > /dev/null 2>&1

# Alternative method if pythonw3 is not available
if [ $? -ne 0 ]; then
    osascript -e "
    tell application \"System Events\"
        do shell script \"cd '$SCRIPT_DIR' && python3 -c 'import sys; sys.path.insert(0, \\\".\\\"); from vaitp_auditor.gui.gui_app import main; main()' > /dev/null 2>&1 &\"
    end tell
    " > /dev/null 2>&1
fi