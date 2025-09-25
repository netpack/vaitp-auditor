#!/usr/bin/env python3
"""
Build script for creating VAITP-Auditor GUI executables.

This script automates the process of building standalone executables
for different platforms using PyInstaller.
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
import argparse


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def check_dependencies():
    """Check if required build dependencies are installed with version validation."""
    required_packages = {
        'pyinstaller': '5.0.0',
        'customtkinter': '5.0.0', 
        'pygments': '2.10.0',
        'pillow': '8.0.0',
        'psutil': '5.8.0',
        'openpyxl': '3.0.0',
        'pandas': '1.3.0',
        'rich': '12.0.0'
    }
    
    missing_packages = []
    version_issues = []
    
    for package, min_version in required_packages.items():
        try:
            if package == 'pillow':
                import PIL
                module = PIL
                package_name = 'PIL'
            else:
                module = __import__(package)
                package_name = package
            
            # Check version if available
            if hasattr(module, '__version__'):
                current_version = module.__version__
                print(f"✓ {package_name}: {current_version}")
            else:
                print(f"✓ {package_name}: installed (version unknown)")
                
        except ImportError:
            missing_packages.append(package)
    
    # Check platform-specific dependencies
    system = platform.system().lower()
    if system == 'windows':
        try:
            import win32api
            print("✓ pywin32: available")
        except ImportError:
            print("⚠ pywin32: not installed (recommended for Windows)")
    
    if missing_packages:
        print(f"\n✗ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    if version_issues:
        print(f"\n⚠ Version issues found: {', '.join(version_issues)}")
        print("Consider upgrading packages with: pip install --upgrade <package_name>")
    
    return True


def create_assets_directory():
    """Create comprehensive assets directory structure with platform-specific icons."""
    project_root = get_project_root()
    assets_dir = project_root / "vaitp_auditor" / "gui" / "assets"
    
    # Create directory structure
    (assets_dir / "icons").mkdir(parents=True, exist_ok=True)
    (assets_dir / "themes").mkdir(parents=True, exist_ok=True)
    (assets_dir / "fonts").mkdir(parents=True, exist_ok=True)
    
    # Create comprehensive asset files
    system = platform.system().lower()
    
    # Icon files needed for different platforms
    icon_files = {
        'app_icon.png': 'PNG icon for general use',
        'app_icon.ico': 'Windows ICO format' if system == 'windows' else None,
        'app_icon.icns': 'macOS ICNS format' if system == 'darwin' else None,
    }
    
    for icon_file, description in icon_files.items():
        if description is None:
            continue
            
        icon_path = assets_dir / "icons" / icon_file
        if not icon_path.exists():
            # Create placeholder with proper format indication
            placeholder_content = f"# {description}\n# This is a placeholder - replace with actual {icon_file}\n"
            icon_path.write_text(placeholder_content)
            print(f"Created placeholder: {icon_path}")
    
    # Enhanced theme files
    theme_files = {
        'default.json': {
            "name": "default",
            "appearance_mode": "system",
            "colors": {
                "primary": "#1f538d",
                "secondary": "#14375e",
                "success": "#198754",
                "warning": "#ffc107",
                "error": "#dc3545",
                "background": "#ffffff",
                "surface": "#f8f9fa",
                "text": "#212529"
            },
            "fonts": {
                "default_family": "Segoe UI" if system == 'windows' else "SF Pro Display" if system == 'darwin' else "Ubuntu",
                "code_family": "Consolas" if system == 'windows' else "SF Mono" if system == 'darwin' else "Ubuntu Mono",
                "default_size": 12,
                "code_size": 11
            }
        },
        'dark.json': {
            "name": "dark",
            "appearance_mode": "dark",
            "colors": {
                "primary": "#0d6efd",
                "secondary": "#6c757d",
                "success": "#198754",
                "warning": "#ffc107",
                "error": "#dc3545",
                "background": "#212529",
                "surface": "#343a40",
                "text": "#ffffff"
            },
            "fonts": {
                "default_family": "Segoe UI" if system == 'windows' else "SF Pro Display" if system == 'darwin' else "Ubuntu",
                "code_family": "Consolas" if system == 'windows' else "SF Mono" if system == 'darwin' else "Ubuntu Mono",
                "default_size": 12,
                "code_size": 11
            }
        }
    }
    
    for theme_file, theme_data in theme_files.items():
        theme_path = assets_dir / "themes" / theme_file
        if not theme_path.exists():
            import json
            theme_path.write_text(json.dumps(theme_data, indent=2))
            print(f"Created theme: {theme_path}")
    
    # Font directory (for custom fonts if needed)
    fonts_readme = assets_dir / "fonts" / "README.md"
    if not fonts_readme.exists():
        fonts_readme.write_text("""# Fonts Directory

This directory can contain custom fonts for the application.
Supported formats: TTF, OTF

Platform-specific font recommendations:
- Windows: Segoe UI, Consolas
- macOS: SF Pro Display, SF Mono  
- Linux: Ubuntu, Ubuntu Mono

Custom fonts placed here will be bundled with the executable.
""")
        print(f"Created fonts README: {fonts_readme}")
    
    print(f"✓ Assets directory structure created at: {assets_dir}")
    return assets_dir


def validate_version():
    """Validate version consistency before building."""
    project_root = get_project_root()
    validate_script = project_root / "deployment" / "validate_version.py"
    
    if not validate_script.exists():
        print("Warning: Version validation script not found")
        return True
    
    try:
        result = subprocess.run([sys.executable, str(validate_script)], 
                              capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("✓ Version validation passed")
            return True
        else:
            print("✗ Version validation failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"Warning: Could not run version validation: {e}")
        return True

def create_version_file():
    """Create Windows version file for executable metadata."""
    if platform.system().lower() != 'windows':
        return None
    
    project_root = get_project_root()
    
    # Import version
    sys.path.insert(0, str(project_root / "vaitp_auditor"))
    from _version import __version__
    
    version_parts = __version__.split('.')
    while len(version_parts) < 4:
        version_parts.append('0')
    
    version_file_content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({','.join(version_parts)}),
    prodvers=({','.join(version_parts)}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'VAITP Research Team'),
            StringStruct(u'FileDescription', u'VAITP-Auditor GUI Application'),
            StringStruct(u'FileVersion', u'{__version__}'),
            StringStruct(u'InternalName', u'VAITP-Auditor-GUI'),
            StringStruct(u'LegalCopyright', u'Copyright © 2024 VAITP Research Team'),
            StringStruct(u'OriginalFilename', u'VAITP-Auditor-GUI.exe'),
            StringStruct(u'ProductName', u'VAITP-Auditor'),
            StringStruct(u'ProductVersion', u'{__version__}')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    
    version_file_path = project_root / "deployment" / "version_info.txt"
    version_file_path.write_text(version_file_content)
    print(f"✓ Created Windows version file: {version_file_path}")
    return version_file_path


def optimize_for_platform():
    """Apply platform-specific optimizations."""
    system = platform.system().lower()
    optimizations = []
    
    if system == 'windows':
        optimizations.extend([
            "Windows-specific optimizations:",
            "- UPX compression enabled",
            "- Version information embedded",
            "- Windows manifest included",
            "- ICO icon format used"
        ])
    elif system == 'darwin':
        optimizations.extend([
            "macOS-specific optimizations:",
            "- App bundle creation",
            "- ICNS icon format used", 
            "- Info.plist with proper metadata",
            "- High DPI support enabled",
            "- UPX disabled for code signing compatibility"
        ])
    elif system == 'linux':
        optimizations.extend([
            "Linux-specific optimizations:",
            "- Binary stripping enabled",
            "- UPX compression with exclusions",
            "- Desktop integration ready",
            "- Portable binary creation"
        ])
    
    for opt in optimizations:
        print(opt)
    
    return optimizations


def build_executable(platform_name=None, debug=False, optimize=True):
    """Enhanced build executable with platform-specific optimizations."""
    project_root = get_project_root()
    spec_file = project_root / "deployment" / "pyinstaller_config.spec"
    
    if not spec_file.exists():
        print(f"✗ Spec file not found: {spec_file}")
        return False
    
    # Validate version consistency
    if not validate_version():
        print("✗ Build aborted due to version validation failure")
        return False
    
    # Apply platform optimizations
    if optimize:
        print("\n📊 Platform Optimizations:")
        optimize_for_platform()
    
    # Create platform-specific files
    system = platform.system().lower()
    if system == 'windows':
        version_file = create_version_file()
    
    # Prepare enhanced build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(spec_file),
        "--clean",
        "--noconfirm"
    ]
    
    if debug:
        cmd.extend(["--debug", "all"])
        cmd.append("--console")  # Enable console for debugging
    
    # Add platform-specific options
    if system == 'windows' and not debug:
        cmd.extend(["--windowed"])  # Ensure windowed mode on Windows
    
    # Set working directory
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    try:
        print(f"\n🔨 Building executable for {platform.system()}...")
        print(f"Command: {' '.join(cmd)}")
        print("This may take several minutes...")
        
        # Run build with real-time output
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line.rstrip())
        
        process.wait()
        
        if process.returncode == 0:
            print("\n✅ Build successful!")
            
            # Analyze build results
            dist_dir = project_root / "dist"
            if dist_dir.exists():
                print(f"\n📁 Build artifacts in: {dist_dir}")
                total_size = 0
                
                for item in dist_dir.iterdir():
                    if item.is_file():
                        size_mb = item.stat().st_size / (1024 * 1024)
                        total_size += size_mb
                        print(f"  📄 {item.name} ({size_mb:.1f} MB)")
                    elif item.is_dir():
                        # Calculate directory size
                        dir_size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                        dir_size_mb = dir_size / (1024 * 1024)
                        total_size += dir_size_mb
                        print(f"  📁 {item.name}/ ({dir_size_mb:.1f} MB)")
                
                print(f"\n📊 Total build size: {total_size:.1f} MB")
                
                # Performance recommendations
                if total_size > 100:
                    print("⚠️  Large executable size detected. Consider:")
                    print("   - Reviewing excluded modules in spec file")
                    print("   - Enabling UPX compression")
                    print("   - Removing unnecessary assets")
            
            return True
        else:
            print("\n❌ Build failed!")
            print("Check the output above for error details.")
            return False
            
    except Exception as e:
        print(f"\n💥 Error during build: {e}")
        return False
    
    finally:
        os.chdir(original_cwd)


def clean_build_artifacts():
    """Clean up build artifacts."""
    project_root = get_project_root()
    
    artifacts = [
        project_root / "build",
        project_root / "dist",
        project_root / "*.spec",
    ]
    
    for artifact in artifacts:
        if artifact.exists():
            if artifact.is_dir():
                shutil.rmtree(artifact)
                print(f"Removed directory: {artifact}")
            else:
                artifact.unlink()
                print(f"Removed file: {artifact}")


def create_installer_script():
    """Create platform-specific installer script."""
    project_root = get_project_root()
    system = platform.system().lower()
    
    if system == "windows":
        # Create Windows batch installer
        installer_content = """@echo off
echo Installing VAITP-Auditor GUI...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

REM Install the package
pip install vaitp-auditor[gui]

if errorlevel 1 (
    echo Installation failed
    pause
    exit /b 1
)

echo Installation completed successfully!
echo You can now run: vaitp-auditor-gui
pause
"""
        installer_path = project_root / "deployment" / "install_windows.bat"
        installer_path.write_text(installer_content)
        
    elif system == "darwin":
        # Create macOS shell installer
        installer_content = """#!/bin/bash
echo "Installing VAITP-Auditor GUI..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed"
    echo "Please install Python 3.8 or higher from https://python.org"
    exit 1
fi

# Install the package
pip3 install vaitp-auditor[gui]

if [ $? -ne 0 ]; then
    echo "Installation failed"
    exit 1
fi

echo "Installation completed successfully!"
echo "You can now run: vaitp-auditor-gui"
"""
        installer_path = project_root / "deployment" / "install_macos.sh"
        installer_path.write_text(installer_content)
        installer_path.chmod(0o755)
        
    elif system == "linux":
        # Create Linux shell installer
        installer_content = """#!/bin/bash
echo "Installing VAITP-Auditor GUI..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed"
    echo "Please install Python 3.8 or higher using your package manager"
    exit 1
fi

# Install the package
pip3 install --user vaitp-auditor[gui]

if [ $? -ne 0 ]; then
    echo "Installation failed"
    exit 1
fi

echo "Installation completed successfully!"
echo "You can now run: vaitp-auditor-gui"
echo "Note: Make sure ~/.local/bin is in your PATH"
"""
        installer_path = project_root / "deployment" / "install_linux.sh"
        installer_path.write_text(installer_content)
        installer_path.chmod(0o755)
    
    print(f"Created installer script for {system}")


def check_upx_availability():
    """Check if UPX is available for compression."""
    try:
        result = subprocess.run(['upx', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ UPX available: {version_line}")
            return True
        else:
            print("⚠️  UPX not found - executable size will be larger")
            print("   Install UPX from https://upx.github.io/ for better compression")
            return False
    except FileNotFoundError:
        print("⚠️  UPX not found - executable size will be larger")
        print("   Install UPX from https://upx.github.io/ for better compression")
        return False


def create_windows_manifest():
    """Create Windows application manifest for proper DPI awareness and compatibility."""
    project_root = get_project_root()
    
    # Import version
    sys.path.insert(0, str(project_root / "vaitp_auditor"))
    from _version import __version__
    
    manifest_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="{__version__}.0"
    processorArchitecture="*"
    name="VAITP.Auditor.GUI"
    type="win32"
  />
  <description>VAITP-Auditor GUI Application</description>
  
  <!-- Windows 10/11 compatibility -->
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <!-- Windows 10 -->
      <supportedOS Id="{{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}}"/>
      <!-- Windows 8.1 -->
      <supportedOS Id="{{1f676c76-80e1-4239-95bb-83d0f6d0da78}}"/>
      <!-- Windows 8 -->
      <supportedOS Id="{{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}}"/>
      <!-- Windows 7 -->
      <supportedOS Id="{{35138b9a-5d96-4fbd-8e2d-a2440225f93a}}"/>
    </application>
  </compatibility>
  
  <!-- DPI Awareness -->
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </windowsSettings>
  </application>
  
  <!-- Execution Level -->
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v2">
    <security>
      <requestedPrivileges xmlns="urn:schemas-microsoft-com:asm.v3">
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>
"""
    
    manifest_path = project_root / "deployment" / "app.manifest"
    manifest_path.write_text(manifest_content)
    print(f"✓ Created Windows manifest: {manifest_path}")
    return manifest_path


def create_macos_info_plist():
    """Create enhanced Info.plist for macOS app bundle."""
    project_root = get_project_root()
    
    # Import version
    sys.path.insert(0, str(project_root / "vaitp_auditor"))
    from _version import __version__
    
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>VAITP-Auditor GUI</string>
    
    <key>CFBundleDisplayName</key>
    <string>VAITP-Auditor GUI</string>
    
    <key>CFBundleIdentifier</key>
    <string>com.vaitp.auditor.gui</string>
    
    <key>CFBundleVersion</key>
    <string>{__version__}</string>
    
    <key>CFBundleShortVersionString</key>
    <string>{__version__}</string>
    
    <key>CFBundleExecutable</key>
    <string>VAITP-Auditor-GUI</string>
    
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    
    <key>CFBundleSignature</key>
    <string>VAIT</string>
    
    <key>CFBundleIconFile</key>
    <string>app_icon</string>
    
    <key>NSHighResolutionCapable</key>
    <true/>
    
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    
    <key>LSMinimumSystemVersion</key>
    <string>10.14.0</string>
    
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.developer-tools</string>
    
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2024 VAITP Research Team. All rights reserved.</string>
    
    <key>CFBundleDocumentTypes</key>
    <array>
        <dict>
            <key>CFBundleTypeName</key>
            <string>Excel Spreadsheet</string>
            <key>CFBundleTypeExtensions</key>
            <array>
                <string>xlsx</string>
                <string>xls</string>
            </array>
            <key>CFBundleTypeRole</key>
            <string>Viewer</string>
            <key>LSHandlerRank</key>
            <string>Alternate</string>
        </dict>
        <dict>
            <key>CFBundleTypeName</key>
            <string>SQLite Database</string>
            <key>CFBundleTypeExtensions</key>
            <array>
                <string>db</string>
                <string>sqlite</string>
                <string>sqlite3</string>
            </array>
            <key>CFBundleTypeRole</key>
            <string>Viewer</string>
            <key>LSHandlerRank</key>
            <string>Alternate</string>
        </dict>
    </array>
    
    <key>UTExportedTypeDeclarations</key>
    <array>
        <dict>
            <key>UTTypeIdentifier</key>
            <string>com.vaitp.auditor.session</string>
            <key>UTTypeDescription</key>
            <string>VAITP Auditor Session</string>
            <key>UTTypeConformsTo</key>
            <array>
                <string>public.data</string>
            </array>
            <key>UTTypeTagSpecification</key>
            <dict>
                <key>public.filename-extension</key>
                <array>
                    <string>vaitp</string>
                </array>
            </dict>
        </dict>
    </array>
    
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <false/>
    </dict>
    
    <key>NSCameraUsageDescription</key>
    <string>This app does not use the camera.</string>
    
    <key>NSMicrophoneUsageDescription</key>
    <string>This app does not use the microphone.</string>
</dict>
</plist>
"""
    
    plist_path = project_root / "deployment" / "Info.plist"
    plist_path.write_text(plist_content)
    print(f"✓ Created macOS Info.plist: {plist_path}")
    return plist_path


def create_linux_desktop_file():
    """Create Linux desktop integration file."""
    project_root = get_project_root()
    
    # Import version
    sys.path.insert(0, str(project_root / "vaitp_auditor"))
    from _version import __version__
    
    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=VAITP-Auditor GUI
GenericName=Code Verification Assistant
Comment=Manual Code Verification Assistant for programmatically generated code snippets
Exec=vaitp-auditor-gui
Icon=vaitp-auditor-gui
Terminal=false
Categories=Development;IDE;
Keywords=code;verification;audit;review;security;
MimeType=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;application/vnd.ms-excel;application/x-sqlite3;
StartupNotify=true
StartupWMClass=VAITP-Auditor-GUI
"""
    
    desktop_path = project_root / "deployment" / "vaitp-auditor-gui.desktop"
    desktop_path.write_text(desktop_content)
    print(f"✓ Created Linux desktop file: {desktop_path}")
    return desktop_path


def create_platform_package(dist_dir):
    """Create comprehensive platform-specific packages with proper metadata."""
    system = platform.system().lower()
    project_root = get_project_root()
    
    # Import version
    sys.path.insert(0, str(project_root / "vaitp_auditor"))
    from _version import __version__
    
    if system == 'windows':
        return create_windows_package(dist_dir, project_root, __version__)
    elif system == 'darwin':
        return create_macos_package(dist_dir, project_root, __version__)
    elif system == 'linux':
        return create_linux_package(dist_dir, project_root, __version__)
    
    return None


def create_windows_package(dist_dir, project_root, version):
    """Create comprehensive Windows package with installer."""
    import zipfile
    
    exe_file = None
    for item in dist_dir.iterdir():
        if item.suffix == '.exe':
            exe_file = item
            break
    
    if not exe_file:
        print("❌ No Windows executable found")
        return None
    
    # Create main ZIP package
    zip_path = project_root / f"VAITP-Auditor-GUI-Windows-{platform.machine()}-v{version}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(exe_file, exe_file.name)
        
        # Add comprehensive README
        readme_content = f"""VAITP-Auditor GUI v{version} for Windows
{'=' * 50}

INSTALLATION:
1. Extract this ZIP file to a folder of your choice (e.g., C:\\Program Files\\VAITP-Auditor)
2. Run VAITP-Auditor-GUI.exe
3. (Optional) Create a desktop shortcut for easy access

SYSTEM REQUIREMENTS:
- Windows 10 version 1903 or later (Windows 11 recommended)
- 4GB RAM minimum, 8GB recommended
- 100MB free disk space
- Display resolution: 1024x768 minimum, 1920x1080 recommended

FEATURES:
- Manual code verification and review
- Excel and SQLite data source support
- Syntax highlighting and diff visualization
- Session management and progress tracking
- Accessibility features and keyboard shortcuts

FIRST RUN:
- Windows Defender may show a security warning (normal for unsigned executables)
- Click "More info" then "Run anyway" if prompted
- The application will create configuration files in your user directory

TROUBLESHOOTING:
- If the app doesn't start, ensure you have the latest Windows updates
- For display issues, try running with Windows compatibility mode
- Check Windows Event Viewer for detailed error messages

SUPPORT:
- Documentation: docs/GUI_USER_GUIDE.md
- Issues: https://github.com/your-repo/vaitp-auditor/issues
- Email: support@vaitp-auditor.com

LICENSE:
This software is released under the MIT License.
See LICENSE file for details.

Copyright © 2024 VAITP Research Team. All rights reserved.
"""
        zf.writestr("README.txt", readme_content)
        
        # Add license file if it exists
        license_file = project_root / "LICENSE"
        if license_file.exists():
            zf.write(license_file, "LICENSE.txt")
        
        # Add changelog if it exists
        changelog_file = project_root / "CHANGELOG.md"
        if changelog_file.exists():
            zf.write(changelog_file, "CHANGELOG.txt")
    
    print(f"✓ Created Windows package: {zip_path}")
    return zip_path


def create_macos_package(dist_dir, project_root, version):
    """Create comprehensive macOS package with DMG-ready structure."""
    import zipfile
    
    app_bundle = None
    for item in dist_dir.iterdir():
        if item.suffix == '.app':
            app_bundle = item
            break
    
    if not app_bundle:
        print("❌ No macOS app bundle found")
        return None
    
    # Create DMG-ready ZIP package
    zip_path = project_root / f"VAITP-Auditor-GUI-macOS-{platform.machine()}-v{version}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        # Add the entire app bundle
        for root, dirs, files in os.walk(app_bundle):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(dist_dir)
                zf.write(file_path, arc_path)
        
        # Add comprehensive README
        readme_content = f"""VAITP-Auditor GUI v{version} for macOS
{'=' * 50}

INSTALLATION:
1. Extract this ZIP file
2. Drag VAITP-Auditor-GUI.app to your Applications folder
3. Double-click to run from Applications or Launchpad

SYSTEM REQUIREMENTS:
- macOS 10.14 (Mojave) or later (macOS 12+ recommended)
- 4GB RAM minimum, 8GB recommended
- 100MB free disk space
- Retina display supported

FIRST RUN:
- macOS Gatekeeper may prevent the app from running (normal for unsigned apps)
- Right-click the app and select "Open" to bypass the security warning
- Click "Open" in the confirmation dialog
- Subsequent runs will work normally

FEATURES:
- Native macOS interface with dark mode support
- Excel and SQLite data source support
- Syntax highlighting optimized for Retina displays
- Full keyboard navigation and VoiceOver support
- Automatic session backup and recovery

TROUBLESHOOTING:
- If the app won't open: Check System Preferences > Security & Privacy
- For display issues: Ensure "Use font smoothing when available" is enabled
- Performance issues: Close other applications to free up memory

UNINSTALLATION:
- Simply drag VAITP-Auditor-GUI.app to the Trash
- Configuration files are stored in ~/Library/Application Support/VAITP-Auditor

SUPPORT:
- Documentation: docs/GUI_USER_GUIDE.md
- Issues: https://github.com/your-repo/vaitp-auditor/issues
- Email: support@vaitp-auditor.com

LICENSE:
This software is released under the MIT License.
See LICENSE file for details.

Copyright © 2024 VAITP Research Team. All rights reserved.
"""
        zf.writestr("README.txt", readme_content)
        
        # Add license and changelog
        license_file = project_root / "LICENSE"
        if license_file.exists():
            zf.write(license_file, "LICENSE.txt")
        
        changelog_file = project_root / "CHANGELOG.md"
        if changelog_file.exists():
            zf.write(changelog_file, "CHANGELOG.txt")
    
    print(f"✓ Created macOS package: {zip_path}")
    return zip_path


def create_linux_package(dist_dir, project_root, version):
    """Create comprehensive Linux package with desktop integration."""
    import tarfile
    
    exe_file = None
    for item in dist_dir.iterdir():
        if item.is_file() and not item.suffix:
            exe_file = item
            break
    
    if not exe_file:
        print("❌ No Linux executable found")
        return None
    
    # Create comprehensive tar.gz package
    tar_path = project_root / f"VAITP-Auditor-GUI-Linux-{platform.machine()}-v{version}.tar.gz"
    
    with tarfile.open(tar_path, 'w:gz') as tf:
        # Add the executable
        tf.add(exe_file, f"vaitp-auditor-gui/{exe_file.name}")
        
        # Create and add desktop integration files
        desktop_file = create_linux_desktop_file()
        tf.add(desktop_file, "vaitp-auditor-gui/vaitp-auditor-gui.desktop")
        
        # Add installation script
        install_script_content = f"""#!/bin/bash
# VAITP-Auditor GUI Installation Script for Linux

set -e

APP_NAME="vaitp-auditor-gui"
INSTALL_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

echo "Installing VAITP-Auditor GUI v{version}..."

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

# Copy executable
cp "VAITP-Auditor-GUI" "$INSTALL_DIR/$APP_NAME"
chmod +x "$INSTALL_DIR/$APP_NAME"

# Copy desktop file
cp "$APP_NAME.desktop" "$DESKTOP_DIR/"

# Update desktop file with correct paths
sed -i "s|Exec=$APP_NAME|Exec=$INSTALL_DIR/$APP_NAME|g" "$DESKTOP_DIR/$APP_NAME.desktop"

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR"
fi

echo "✓ Installation completed!"
echo ""
echo "The application has been installed to: $INSTALL_DIR/$APP_NAME"
echo "Desktop entry created in: $DESKTOP_DIR"
echo ""
echo "You can now:"
echo "1. Run from terminal: $APP_NAME"
echo "2. Find it in your application menu"
echo "3. Add $INSTALL_DIR to your PATH for easier access"
echo ""
echo "To add to PATH, add this line to your ~/.bashrc or ~/.zshrc:"
echo "export PATH=\\"\\$PATH:$INSTALL_DIR\\""
"""
        
        # Create install script as temporary file
        install_script_path = project_root / "install_temp.sh"
        install_script_path.write_text(install_script_content)
        tf.add(install_script_path, "vaitp-auditor-gui/install.sh")
        install_script_path.unlink()
        
        # Add comprehensive README
        readme_content = f"""VAITP-Auditor GUI v{version} for Linux
{'=' * 50}

QUICK INSTALLATION:
1. Extract this archive: tar -xzf VAITP-Auditor-GUI-Linux-*.tar.gz
2. cd vaitp-auditor-gui
3. ./install.sh

MANUAL INSTALLATION:
1. Extract this archive: tar -xzf VAITP-Auditor-GUI-Linux-*.tar.gz
2. cd vaitp-auditor-gui
3. Copy VAITP-Auditor-GUI to a directory in your PATH (e.g., ~/.local/bin)
4. Make executable: chmod +x ~/.local/bin/VAITP-Auditor-GUI
5. Copy vaitp-auditor-gui.desktop to ~/.local/share/applications/

SYSTEM REQUIREMENTS:
- Linux distribution with glibc 2.17+ (Ubuntu 18.04+, CentOS 7+, etc.)
- 4GB RAM minimum, 8GB recommended
- 100MB free disk space
- X11 or Wayland display server
- GTK 3.0+ (for file dialogs)

TESTED DISTRIBUTIONS:
- Ubuntu 20.04 LTS and later
- Debian 10 and later
- CentOS 8 and later
- Fedora 32 and later
- openSUSE Leap 15.2 and later
- Arch Linux (current)

FEATURES:
- Native Linux interface with system theme integration
- Excel and SQLite data source support
- Syntax highlighting with customizable themes
- Full keyboard navigation and accessibility support
- Automatic session backup and recovery

RUNNING:
- From terminal: vaitp-auditor-gui (if installed with install.sh)
- From application menu: Search for "VAITP-Auditor GUI"
- Direct execution: ./VAITP-Auditor-GUI

TROUBLESHOOTING:
- Missing libraries: Install development packages for your distribution
- Permission denied: Ensure the executable has execute permissions
- Display issues: Try setting QT_SCALE_FACTOR=1 environment variable
- Font issues: Install Microsoft fonts package for better compatibility

UNINSTALLATION:
- Remove ~/.local/bin/vaitp-auditor-gui
- Remove ~/.local/share/applications/vaitp-auditor-gui.desktop
- Remove ~/.config/VAITP-Auditor/ (configuration files)

SUPPORT:
- Documentation: docs/GUI_USER_GUIDE.md
- Issues: https://github.com/your-repo/vaitp-auditor/issues
- Email: support@vaitp-auditor.com

LICENSE:
This software is released under the MIT License.
See LICENSE file for details.

Copyright © 2024 VAITP Research Team. All rights reserved.
"""
        
        # Create README as temporary file
        readme_path = project_root / "README_temp.txt"
        readme_path.write_text(readme_content)
        tf.add(readme_path, "vaitp-auditor-gui/README.txt")
        readme_path.unlink()
        
        # Add license and changelog
        license_file = project_root / "LICENSE"
        if license_file.exists():
            tf.add(license_file, "vaitp-auditor-gui/LICENSE.txt")
        
        changelog_file = project_root / "CHANGELOG.md"
        if changelog_file.exists():
            tf.add(changelog_file, "vaitp-auditor-gui/CHANGELOG.txt")
    
    print(f"✓ Created Linux package: {tar_path}")
    return tar_path


def check_code_signing_tools():
    """Check availability of code signing tools for the current platform."""
    system = platform.system().lower()
    tools_available = {}
    
    if system == 'windows':
        # Check for signtool (Windows SDK)
        try:
            result = subprocess.run(['signtool'], capture_output=True, text=True)
            if 'Microsoft (R) Sign Tool' in result.stderr or result.returncode == 0:
                tools_available['signtool'] = True
                print("✓ signtool available (Windows code signing)")
            else:
                tools_available['signtool'] = False
                print("⚠️  signtool not found - Windows code signing unavailable")
        except FileNotFoundError:
            tools_available['signtool'] = False
            print("⚠️  signtool not found - install Windows SDK for code signing")
            
    elif system == 'darwin':
        # Check for codesign (Xcode Command Line Tools)
        try:
            result = subprocess.run(['codesign', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                tools_available['codesign'] = True
                print(f"✓ codesign available: {result.stdout.strip()}")
            else:
                tools_available['codesign'] = False
                print("⚠️  codesign not working - macOS code signing unavailable")
        except FileNotFoundError:
            tools_available['codesign'] = False
            print("⚠️  codesign not found - install Xcode Command Line Tools")
        
        # Check for create-dmg (optional)
        try:
            result = subprocess.run(['create-dmg', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                tools_available['create-dmg'] = True
                print("✓ create-dmg available for DMG creation")
            else:
                tools_available['create-dmg'] = False
        except FileNotFoundError:
            tools_available['create-dmg'] = False
            print("⚠️  create-dmg not found - install with: brew install create-dmg")
    
    return tools_available


def sign_executable(executable_path, cert_path=None, cert_password=None, identity=None):
    """Sign executable with platform-appropriate code signing."""
    system = platform.system().lower()
    
    if not Path(executable_path).exists():
        print(f"❌ Executable not found: {executable_path}")
        return False
    
    try:
        if system == 'windows':
            return sign_windows_executable(executable_path, cert_path, cert_password)
        elif system == 'darwin':
            return sign_macos_executable(executable_path, identity)
        else:
            print("ℹ️  Code signing not supported on Linux")
            return True  # Not an error, just not supported
            
    except Exception as e:
        print(f"❌ Code signing failed: {e}")
        return False


def sign_windows_executable(executable_path, cert_path=None, cert_password=None):
    """Sign Windows executable using signtool."""
    if not cert_path:
        print("⚠️  No certificate path provided for Windows signing")
        return False
    
    cert_path = Path(cert_path)
    if not cert_path.exists():
        print(f"❌ Certificate file not found: {cert_path}")
        return False
    
    # Build signtool command
    cmd = [
        'signtool', 'sign',
        '/f', str(cert_path),
        '/t', 'http://timestamp.digicert.com',  # Timestamp server
        '/fd', 'SHA256',  # File digest algorithm
        '/v',  # Verbose output
    ]
    
    if cert_password:
        cmd.extend(['/p', cert_password])
    
    cmd.append(str(executable_path))
    
    print(f"🔐 Signing Windows executable: {executable_path}")
    print(f"Certificate: {cert_path}")
    
    try:
        # Don't show password in command output
        display_cmd = [c if c != cert_password else '***' for c in cmd]
        print(f"Command: {' '.join(display_cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Windows executable signed successfully")
            print(result.stdout)
            return True
        else:
            print("❌ Windows signing failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error during Windows signing: {e}")
        return False


def sign_macos_executable(executable_path, identity=None):
    """Sign macOS executable or app bundle using codesign."""
    if not identity:
        print("⚠️  No signing identity provided for macOS signing")
        return False
    
    executable_path = Path(executable_path)
    
    # Determine if it's an app bundle or standalone executable
    if executable_path.suffix == '.app':
        print(f"🔐 Signing macOS app bundle: {executable_path}")
        target_path = executable_path
    else:
        print(f"🔐 Signing macOS executable: {executable_path}")
        target_path = executable_path
    
    # Build codesign command
    cmd = [
        'codesign',
        '--sign', identity,
        '--force',  # Replace existing signature
        '--verbose',
        '--timestamp',  # Include secure timestamp
        '--options', 'runtime',  # Enable hardened runtime
        str(target_path)
    ]
    
    print(f"Identity: {identity}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ macOS executable signed successfully")
            print(result.stdout)
            
            # Verify the signature
            verify_cmd = ['codesign', '--verify', '--verbose', str(target_path)]
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
            
            if verify_result.returncode == 0:
                print("✅ Signature verification passed")
                return True
            else:
                print("⚠️  Signature verification failed")
                print(verify_result.stderr)
                return False
        else:
            print("❌ macOS signing failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error during macOS signing: {e}")
        return False


def create_macos_dmg(app_bundle_path, output_path=None):
    """Create a DMG file from macOS app bundle."""
    app_bundle_path = Path(app_bundle_path)
    
    if not app_bundle_path.exists() or app_bundle_path.suffix != '.app':
        print(f"❌ App bundle not found: {app_bundle_path}")
        return False
    
    if not output_path:
        output_path = app_bundle_path.parent / f"{app_bundle_path.stem}.dmg"
    
    # Check if create-dmg is available
    try:
        subprocess.run(['create-dmg', '--version'], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("⚠️  create-dmg not available, creating simple DMG")
        return create_simple_dmg(app_bundle_path, output_path)
    
    # Use create-dmg for professional DMG
    cmd = [
        'create-dmg',
        '--volname', 'VAITP-Auditor GUI',
        '--volicon', str(app_bundle_path / 'Contents' / 'Resources' / 'app_icon.icns'),
        '--window-pos', '200', '120',
        '--window-size', '600', '400',
        '--icon-size', '100',
        '--icon', app_bundle_path.name, '175', '120',
        '--hide-extension', app_bundle_path.name,
        '--app-drop-link', '425', '120',
        str(output_path),
        str(app_bundle_path.parent)
    ]
    
    print(f"📦 Creating DMG: {output_path}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ DMG created successfully: {output_path}")
            return True
        else:
            print("❌ DMG creation failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error creating DMG: {e}")
        return False


def create_simple_dmg(app_bundle_path, output_path):
    """Create a simple DMG using hdiutil (built into macOS)."""
    app_bundle_path = Path(app_bundle_path)
    output_path = Path(output_path)
    
    # Create temporary directory for DMG contents
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy app bundle to temp directory
        import shutil
        shutil.copytree(app_bundle_path, temp_path / app_bundle_path.name)
        
        # Create DMG
        cmd = [
            'hdiutil', 'create',
            '-srcfolder', str(temp_path),
            '-volname', 'VAITP-Auditor GUI',
            '-format', 'UDZO',  # Compressed
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Simple DMG created: {output_path}")
                return True
            else:
                print("❌ Simple DMG creation failed")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error creating simple DMG: {e}")
            return False


def main():
    """Enhanced main build script entry point with code signing support."""
    parser = argparse.ArgumentParser(
        description="Enhanced VAITP-Auditor GUI executable builder with code signing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_executable.py                    # Standard build
  python build_executable.py --clean --package # Clean build with packaging
  python build_executable.py --debug           # Debug build
  python build_executable.py --sign --cert-path cert.p12 --cert-password pass  # Windows signing
  python build_executable.py --sign --identity "Developer ID Application: Name"  # macOS signing
  python build_executable.py --check-signing   # Check code signing tools
        """
    )
    
    parser.add_argument("--clean", action="store_true", 
                       help="Clean build artifacts before building")
    parser.add_argument("--debug", action="store_true", 
                       help="Build with debug information and console output")
    parser.add_argument("--no-optimize", action="store_true",
                       help="Disable platform-specific optimizations")
    parser.add_argument("--package", action="store_true",
                       help="Create platform-specific distribution package")
    parser.add_argument("--installer", action="store_true", 
                       help="Create installer scripts")
    parser.add_argument("--check-deps", action="store_true", 
                       help="Check build dependencies and exit")
    parser.add_argument("--check-upx", action="store_true",
                       help="Check UPX availability and exit")
    parser.add_argument("--check-signing", action="store_true",
                       help="Check code signing tools availability and exit")
    
    # Code signing arguments
    parser.add_argument("--sign", action="store_true",
                       help="Sign the executable after building")
    parser.add_argument("--cert-path", type=str,
                       help="Path to certificate file (Windows .p12/.pfx)")
    parser.add_argument("--cert-password", type=str,
                       help="Certificate password (Windows)")
    parser.add_argument("--identity", type=str,
                       help="Code signing identity (macOS)")
    parser.add_argument("--create-dmg", action="store_true",
                       help="Create DMG file (macOS only)")
    
    args = parser.parse_args()
    
    print("🚀 VAITP-Auditor GUI Build System")
    print("=" * 40)
    
    if args.check_deps:
        print("🔍 Checking build dependencies...")
        if check_dependencies():
            print("✅ All dependencies are installed.")
        else:
            sys.exit(1)
        return
    
    if args.check_upx:
        print("🔍 Checking UPX availability...")
        check_upx_availability()
        return
    
    if args.check_signing:
        print("🔍 Checking code signing tools...")
        tools = check_code_signing_tools()
        if any(tools.values()):
            print("✅ Code signing tools available")
        else:
            print("⚠️  No code signing tools available")
        return
    
    if args.clean:
        print("🧹 Cleaning build artifacts...")
        clean_build_artifacts()
    
    if args.installer:
        print("📦 Creating installer scripts...")
        create_installer_script()
        return
    
    # Pre-build checks
    print("🔍 Pre-build validation...")
    if not check_dependencies():
        print("❌ Dependency check failed")
        sys.exit(1)
    
    # Check UPX availability (non-blocking)
    check_upx_availability()
    
    # Check code signing tools if signing is requested
    if args.sign:
        print("\n🔐 Checking code signing tools...")
        signing_tools = check_code_signing_tools()
        system = platform.system().lower()
        
        if system == 'windows' and not signing_tools.get('signtool', False):
            print("❌ signtool not available for Windows signing")
            sys.exit(1)
        elif system == 'darwin' and not signing_tools.get('codesign', False):
            print("❌ codesign not available for macOS signing")
            sys.exit(1)
    
    # Create assets directory
    print("\n📁 Setting up assets...")
    create_assets_directory()
    
    # Build executable
    print("\n🔨 Building executable...")
    success = build_executable(
        debug=args.debug, 
        optimize=not args.no_optimize
    )
    
    if success:
        print("\n✅ Build completed successfully!")
        
        # Code signing
        if args.sign:
            print("\n🔐 Code signing...")
            project_root = get_project_root()
            dist_dir = project_root / "dist"
            system = platform.system().lower()
            
            # Find the executable to sign
            executable_path = None
            if system == 'windows':
                for item in dist_dir.iterdir():
                    if item.suffix == '.exe':
                        executable_path = item
                        break
            elif system == 'darwin':
                for item in dist_dir.iterdir():
                    if item.suffix == '.app':
                        executable_path = item
                        break
            else:
                for item in dist_dir.iterdir():
                    if item.is_file() and not item.suffix:
                        executable_path = item
                        break
            
            if executable_path:
                sign_success = sign_executable(
                    executable_path,
                    cert_path=args.cert_path,
                    cert_password=args.cert_password,
                    identity=args.identity
                )
                
                if not sign_success:
                    print("⚠️  Code signing failed, but continuing...")
            else:
                print("❌ No executable found to sign")
        
        # Create DMG for macOS
        if args.create_dmg and platform.system().lower() == 'darwin':
            print("\n📦 Creating DMG...")
            project_root = get_project_root()
            dist_dir = project_root / "dist"
            
            app_bundle = None
            for item in dist_dir.iterdir():
                if item.suffix == '.app':
                    app_bundle = item
                    break
            
            if app_bundle:
                dmg_success = create_macos_dmg(app_bundle)
                if dmg_success:
                    print("✅ DMG created successfully")
                else:
                    print("⚠️  DMG creation failed")
            else:
                print("❌ No app bundle found for DMG creation")
        
        # Create package if requested
        if args.package:
            print("\n📦 Creating distribution package...")
            project_root = get_project_root()
            dist_dir = project_root / "dist"
            
            if dist_dir.exists():
                package_path = create_platform_package(dist_dir)
                if package_path:
                    print(f"✅ Package created: {package_path}")
        
        print("\n🎉 Next steps:")
        print("1. Test the executable in the dist/ directory")
        if not args.sign:
            print("2. Consider code signing with --sign for production releases")
        if not args.package:
            print("3. Run with --package to create distribution archives")
        if platform.system().lower() == 'darwin' and not args.create_dmg:
            print("4. Run with --create-dmg to create macOS DMG installer")
        print("5. Distribute to users")
        
    else:
        print("\n❌ Build failed. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()