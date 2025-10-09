@echo off
REM Windows batch launcher for VAITP-Auditor GUI
REM This launcher suppresses console windows and Python version display

REM Hide this batch window
if not "%1"=="HIDE" (
    start "" /B "%~f0" HIDE
    exit /B
)

REM Launch Python with GUI application, suppressing console output
pythonw -c "import sys; sys.path.insert(0, '.'); from vaitp_auditor.gui.windows_launcher import main; main()" >nul 2>&1

REM Alternative launch method if pythonw is not available
if errorlevel 1 (
    python -c "import sys; sys.path.insert(0, '.'); from vaitp_auditor.gui.windows_launcher import main; main()" >nul 2>&1
)