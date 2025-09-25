# VAITP-Auditor Deployment Guide

This directory contains configuration files and scripts for deploying the VAITP-Auditor application across different platforms using automated GitHub Actions workflows.

## Overview

The deployment system supports multiple distribution methods with automated builds:

1. **Python Package Installation** - Install via pip for Python users
2. **Standalone Executables** - Self-contained executables for end users (Windows, macOS, Linux)
3. **Platform-Specific Packages** - Native installers and packages (DMG, AppImage, ZIP archives)
4. **Automated Releases** - GitHub Actions workflow with Release Drafter integration

## Quick Start

### For Python Users

```bash
# Install from PyPI (when available)
pip install vaitp-auditor[gui]

# Or install from source
git clone https://github.com/your-org/vaitp-auditor.git
cd vaitp-auditor
pip install -e .[gui]

# Launch the application
python -m vaitp_auditor.gui
```

### For End Users (Standalone Executables)

1. Go to the [Releases page](https://github.com/your-org/vaitp-auditor/releases)
2. Download the appropriate executable for your platform:
   - **Windows**: `VAITP-Auditor-GUI-Windows-x64-v*.zip`
   - **macOS**: `VAITP-Auditor-GUI-macOS-v*.dmg`
   - **Linux**: `VAITP-Auditor-GUI-Linux-x86_64-v*.AppImage`
3. Extract (if needed) and run the executable directly (no Python installation required)

### For Developers (Automated Deployment)

```bash
# Test the deployment pipeline
python deployment/test_deployment_pipeline.py

# Create a test release
./deployment/create_test_tag.sh

# Create a production release
git tag v1.0.0
git push origin v1.0.0
```

## Automated Deployment System

The VAITP-Auditor uses GitHub Actions for automated building and deployment across all supported platforms.

### GitHub Actions Workflow

The deployment pipeline is triggered by pushing version tags and includes:

1. **Multi-platform builds** (Windows, macOS, Linux)
2. **Code signing** (when certificates are configured)
3. **Automated testing** of built executables
4. **Release creation** with Release Drafter integration
5. **Asset packaging** and distribution

### Triggering a Release

```bash
# For stable releases
git tag v1.0.0
git push origin v1.0.0

# For pre-releases
git tag v1.0.0-beta.1
git push origin v1.0.0-beta.1

# For testing (creates artifacts but no release)
./deployment/create_test_tag.sh
```

### Pipeline Components

- **Build Jobs**: Create executables for each platform
- **Validation Jobs**: Test executables and verify functionality
- **Release Job**: Create GitHub release with all artifacts
- **Release Drafter**: Automatically generate release notes

## Manual Building (Development)

### Prerequisites

- Python 3.8 or higher
- PyInstaller (`pip install pyinstaller`)
- All GUI dependencies installed
- Platform-specific build tools (see Platform-Specific Instructions)

### Build Process

1. **Check Dependencies**:

   ```bash
   python deployment/build_executable.py --check-deps
   ```

2. **Build Executable**:

   ```bash
   python deployment/build_executable.py
   ```

3. **Clean Build (if needed)**:

   ```bash
   python deployment/build_executable.py --clean
   ```

4. **Debug Build**:
   ```bash
   python deployment/build_executable.py --debug
   ```

5. **Build with Code Signing** (if certificates configured):
   ```bash
   # Windows
   python deployment/build_executable.py --sign --cert-path cert.p12 --cert-password "password"
   
   # macOS
   python deployment/build_executable.py --sign --identity "Developer ID Application: Your Name"
   ```

## Platform-Specific Deployment

### Windows Deployment

#### System Requirements
- **OS**: Windows 10 (1903) or later, Windows 11
- **Architecture**: x64 (64-bit)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 100MB free space for installation

#### Build Requirements
- **Python**: 3.8-3.11 (3.10 recommended)
- **Windows SDK**: For code signing (optional)
- **Visual C++ Redistributable**: Bundled automatically

#### Build Process
```cmd
# Local build
python deployment\build_executable.py

# With code signing
python deployment\build_executable.py --sign --cert-path cert.p12 --cert-password "password"

# Create ZIP package
python deployment\build_executable.py --package
```

#### Output Files
- `dist\VAITP-Auditor-GUI.exe` - Standalone executable
- `VAITP-Auditor-GUI-Windows-x64-v*.zip` - Distribution package

#### Deployment Considerations
- **Code Signing**: Highly recommended to avoid SmartScreen warnings
- **Antivirus**: Test with major antivirus solutions
- **Dependencies**: All dependencies are bundled, no additional installation required
- **File Associations**: Can be configured for .vaitp files

#### Limitations
- **Architecture**: x64 only (no 32-bit or ARM support)
- **Windows Version**: Requires Windows 10 1903+ due to GUI framework requirements
- **File Size**: Executable is ~80-120MB due to bundled dependencies

### macOS Deployment

#### System Requirements
- **OS**: macOS 10.15 (Catalina) or later
- **Architecture**: Intel x64 and Apple Silicon (Universal Binary)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 150MB free space for installation

#### Build Requirements
- **Python**: 3.8-3.11 (3.10 recommended)
- **Xcode Command Line Tools**: For code signing
- **Apple Developer Account**: For distribution certificates

#### Build Process
```bash
# Local build
python deployment/build_executable.py

# With code signing
python deployment/build_executable.py --sign --identity "Developer ID Application: Your Name"

# Create DMG installer
python deployment/build_executable.py --create-dmg
```

#### Output Files
- `dist/VAITP-Auditor-GUI.app` - Application bundle
- `VAITP-Auditor-GUI-macOS-v*.dmg` - DMG installer

#### Deployment Considerations
- **Code Signing**: Required for Gatekeeper compatibility
- **Notarization**: Recommended for macOS 10.15+
- **App Bundle**: Proper Info.plist and icon sets included
- **Retina Support**: High-DPI displays fully supported

#### Limitations
- **macOS Version**: Requires 10.15+ due to security requirements
- **Gatekeeper**: Unsigned apps will show security warnings
- **File Size**: App bundle is ~100-150MB
- **Quarantine**: Downloaded apps may need manual approval

### Linux Deployment

#### System Requirements
- **Distributions**: Ubuntu 18.04+, Debian 10+, CentOS 8+, Fedora 32+
- **Architecture**: x86_64 (64-bit)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 120MB free space for installation

#### Build Requirements
- **Python**: 3.8-3.11 (3.10 recommended)
- **System Libraries**: GTK3, X11 development libraries
- **Build Tools**: GCC, make, pkg-config

#### Build Process
```bash
# Install build dependencies (Ubuntu/Debian)
sudo apt-get install python3-dev libgtk-3-dev libx11-dev

# Local build
python deployment/build_executable.py

# Create AppImage
python deployment/build_executable.py --create-appimage

# Create tarball
python deployment/build_executable.py --package
```

#### Output Files
- `dist/VAITP-Auditor-GUI` - Standalone binary
- `VAITP-Auditor-GUI-Linux-x86_64-v*.AppImage` - Portable AppImage
- `VAITP-Auditor-GUI-Linux-x86_64-v*.tar.gz` - Archive package

#### Deployment Considerations
- **Dependencies**: Most system libraries are bundled
- **Desktop Integration**: .desktop file included for menu integration
- **Permissions**: Executable permissions set automatically
- **Font Rendering**: Uses system fonts for consistency

#### Limitations
- **Distribution Compatibility**: Tested on major distributions only
- **Wayland**: X11 required (Wayland support through XWayland)
- **File Size**: Binary is ~90-130MB
- **System Libraries**: Some system libraries must be present (glibc, GTK3)

### Cross-Platform Considerations

#### File Formats
- **Configuration**: JSON format, cross-platform compatible
- **Data Files**: Excel (.xlsx), SQLite, filesystem sources supported
- **Reports**: Excel output with cross-platform compatibility

#### User Interface
- **Themes**: Adapts to system appearance (light/dark mode)
- **Fonts**: Uses system fonts for native appearance
- **Keyboard Shortcuts**: Platform-appropriate shortcuts
- **File Dialogs**: Native file dialogs on each platform

#### Performance
- **Startup Time**: 3-8 seconds depending on platform and system
- **Memory Usage**: 150-400MB depending on dataset size
- **File I/O**: Optimized for SSD storage, works on HDD
- **Multi-threading**: Background processing for large datasets

#### Compatibility Matrix

| Feature | Windows | macOS | Linux |
|---------|---------|-------|-------|
| GUI Framework | ✅ CustomTkinter | ✅ CustomTkinter | ✅ CustomTkinter |
| Code Signing | ✅ Authenticode | ✅ Developer ID | ❌ GPG only |
| Auto-Updates | 🚧 Planned | 🚧 Planned | 🚧 Planned |
| File Associations | ✅ Registry | ✅ Info.plist | ✅ .desktop |
| System Integration | ✅ Full | ✅ Full | ✅ Partial |
| Package Managers | ❌ Manual only | 🚧 Homebrew planned | 🚧 Snap/Flatpak planned |

## Configuration Files

### `pyinstaller_config.spec`

PyInstaller specification file that defines:

- **Entry Point**: Main GUI application script
- **Dependencies**: Hidden imports and required modules
- **Assets**: Icons, themes, and fonts
- **Platform Settings**: OS-specific configurations
- **Optimization**: Excluded modules to reduce size

Key sections:

```python
# Hidden imports for GUI dependencies
hiddenimports = [
    'customtkinter',
    'pygments',
    'PIL',
    'psutil',
    # ... VAITP-Auditor modules
]

# Exclude unnecessary modules
excludes = [
    'matplotlib',
    'numpy',
    'scipy',
    # ... other large packages
]
```

### `build_executable.py`

Automated build script that:

- Checks dependencies
- Creates asset directories
- Runs PyInstaller with proper configuration
- Handles cross-platform differences
- Generates installer scripts

Usage examples:

```bash
# Basic build
python deployment/build_executable.py

# Clean build with debug info
python deployment/build_executable.py --clean --debug

# Create installer scripts only
python deployment/build_executable.py --installer
```

## Asset Management

### Directory Structure

```
vaitp_auditor/gui/assets/
├── icons/
│   ├── app_icon.png      # Application icon (PNG)
│   ├── app_icon.ico      # Windows icon
│   ├── app_icon.icns     # macOS icon
│   ├── success.png       # Verdict button icons
│   ├── failure.png
│   └── warning.png
├── themes/
│   ├── default.json      # Default theme
│   ├── dark.json         # Dark theme
│   └── high_contrast.json # Accessibility theme
└── fonts/
    └── consolas.ttf      # Code display font
```

### Creating Icons

#### Windows (.ico)

```bash
# Convert PNG to ICO using ImageMagick
convert app_icon.png -define icon:auto-resize=256,128,64,48,32,16 app_icon.ico
```

#### macOS (.icns)

```bash
# Create iconset directory
mkdir app_icon.iconset

# Create different sizes
sips -z 16 16     app_icon.png --out app_icon.iconset/icon_16x16.png
sips -z 32 32     app_icon.png --out app_icon.iconset/icon_16x16@2x.png
sips -z 32 32     app_icon.png --out app_icon.iconset/icon_32x32.png
sips -z 64 64     app_icon.png --out app_icon.iconset/icon_32x32@2x.png
sips -z 128 128   app_icon.png --out app_icon.iconset/icon_128x128.png
sips -z 256 256   app_icon.png --out app_icon.iconset/icon_128x128@2x.png
sips -z 256 256   app_icon.png --out app_icon.iconset/icon_256x256.png
sips -z 512 512   app_icon.png --out app_icon.iconset/icon_256x256@2x.png
sips -z 512 512   app_icon.png --out app_icon.iconset/icon_512x512.png
sips -z 1024 1024 app_icon.png --out app_icon.iconset/icon_512x512@2x.png

# Create ICNS file
iconutil -c icns app_icon.iconset
```

## Distribution

### Package Distribution

#### PyPI (Python Package Index)

1. **Prepare Package**:

   ```bash
   python setup.py sdist bdist_wheel
   ```

2. **Upload to PyPI**:
   ```bash
   pip install twine
   twine upload dist/*
   ```

#### Conda (Anaconda/Miniconda)

1. **Create Conda Recipe**:

   ```yaml
   # meta.yaml
   package:
     name: vaitp-auditor
     version: "0.1.0"

   source:
     path: ..

   requirements:
     build:
       - python
       - setuptools
     run:
       - python >=3.8
       - customtkinter >=5.0.0
       - pygments >=2.10.0
       - pillow >=8.0.0
   ```

2. **Build Conda Package**:
   ```bash
   conda build .
   ```

### Executable Distribution

#### GitHub Releases

1. **Create Release Assets**:

   ```bash
   # Build for each platform
   python deployment/build_executable.py

   # Create archives
   # Windows
   zip -r VAITP-Auditor-GUI-windows.zip dist/VAITP-Auditor-GUI.exe

   # macOS
   zip -r VAITP-Auditor-GUI-macos.zip dist/VAITP-Auditor-GUI.app

   # Linux
   tar -czf VAITP-Auditor-GUI-linux.tar.gz -C dist VAITP-Auditor-GUI
   ```

2. **Upload to GitHub Releases**:
   - Create a new release on GitHub
   - Upload the platform-specific archives
   - Include installation instructions

#### Direct Download

Host executables on a web server with download links:

```html
<h3>Download VAITP-Auditor GUI</h3>
<ul>
  <li><a href="VAITP-Auditor-GUI-windows.zip">Windows (64-bit)</a></li>
  <li><a href="VAITP-Auditor-GUI-macos.zip">macOS (Intel/Apple Silicon)</a></li>
  <li><a href="VAITP-Auditor-GUI-linux.tar.gz">Linux (64-bit)</a></li>
</ul>
```

## Testing Deployment

### Automated Testing

Create test scripts for each platform:

```bash
# test_deployment.py
import subprocess
import sys
import tempfile
import os

def test_executable():
    """Test that the executable runs without errors."""
    # Test basic startup
    result = subprocess.run([
        "./dist/VAITP-Auditor-GUI",
        "--help"
    ], capture_output=True, text=True, timeout=30)

    assert result.returncode == 0
    print("Executable test passed")

def test_package_installation():
    """Test package installation in clean environment."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create virtual environment
        subprocess.run([
            sys.executable, "-m", "venv",
            os.path.join(temp_dir, "test_env")
        ])

        # Install package
        pip_path = os.path.join(temp_dir, "test_env", "bin", "pip")
        subprocess.run([
            pip_path, "install", "vaitp-auditor[gui]"
        ])

        # Test import
        python_path = os.path.join(temp_dir, "test_env", "bin", "python")
        result = subprocess.run([
            python_path, "-c",
            "import vaitp_auditor.gui; print('Import successful')"
        ], capture_output=True, text=True)

        assert result.returncode == 0
        print("Package installation test passed")
```

### Manual Testing Checklist

#### Functionality Tests

- [ ] Application launches without errors
- [ ] Setup wizard completes successfully
- [ ] Main review window displays correctly
- [ ] Code highlighting works properly
- [ ] Verdict buttons respond correctly
- [ ] Session can be saved and resumed
- [ ] Application exits cleanly

#### Platform-Specific Tests

**Windows:**

- [ ] Executable runs on Windows 10/11
- [ ] File dialogs work correctly
- [ ] Application appears in taskbar
- [ ] Uninstallation removes all files

**macOS:**

- [ ] App bundle opens correctly
- [ ] Gatekeeper allows execution (signed)
- [ ] Retina display support works
- [ ] Application appears in Applications folder

**Linux:**

- [ ] Executable runs on Ubuntu/Debian
- [ ] Desktop integration works
- [ ] File permissions are correct
- [ ] Dependencies are bundled

#### Performance Tests

- [ ] Application starts within 5 seconds
- [ ] Memory usage stays under 500MB
- [ ] Large files load within acceptable time
- [ ] UI remains responsive during operations

## Troubleshooting

### Deployment Pipeline Issues

#### GitHub Actions Workflow Failures

**Build Job Failures**:
- Check Python version compatibility (3.8-3.11 supported)
- Verify all dependencies are available in requirements
- Review build logs for specific error messages
- Test build locally using the same Python version

**Code Signing Failures**:
- Verify certificate secrets are correctly configured in GitHub
- Check certificate expiration dates
- Ensure certificate passwords are correct
- Test signing locally before pushing to CI

**Release Creation Failures**:
- Verify `GITHUB_TOKEN` has sufficient permissions
- Check tag format (must start with `v`)
- Ensure Release Drafter configuration is valid
- Check for conflicting release names

#### Local Build Issues

**Missing Dependencies**:

```bash
# Error: ModuleNotFoundError: No module named 'customtkinter'
# Solution:
pip install -e .[gui]  # Install all GUI dependencies
# Or manually:
pip install customtkinter pygments pillow psutil openpyxl pandas rich
```

**Asset Files Not Found**:

```bash
# Error: FileNotFoundError: assets/icons/app_icon.png
# Solution:
python deployment/build_executable.py --check-deps
# This creates placeholder asset files
```

**PyInstaller Import Errors**:

```bash
# Error: ImportError when running executable
# Solutions:
# 1. Add missing modules to hiddenimports in pyinstaller_config.spec
# 2. Test in clean environment:
python -m venv test_env
source test_env/bin/activate  # or test_env\Scripts\activate on Windows
pip install -e .[gui]
python deployment/build_executable.py
```

**Large Executable Size**:

```bash
# Issue: Executable larger than expected (>100MB)
# Solutions:
# 1. Review excludes in pyinstaller_config.spec
# 2. Remove unnecessary assets
# 3. Check UPX compression is working
python deployment/build_executable.py --debug  # Shows size breakdown
```

### Platform-Specific Issues

#### Windows

**Code Signing Issues**:
- Install Windows SDK for `signtool.exe`
- Use different timestamp servers if one fails:
  - `http://timestamp.digicert.com`
  - `http://timestamp.sectigo.com`
  - `http://timestamp.globalsign.com`

**Antivirus False Positives**:
- Submit executable to antivirus vendors for whitelisting
- Use EV Code Signing certificate for better reputation
- Test with multiple antivirus solutions

#### macOS

**Gatekeeper Issues**:
- Ensure using "Developer ID Application" certificate
- Consider notarization for macOS 10.15+
- Test on different macOS versions

**App Bundle Structure**:
```bash
# Verify app bundle structure
ls -la dist/VAITP-Auditor-GUI.app/Contents/
# Should contain: Info.plist, MacOS/, Resources/
```

#### Linux

**Missing System Libraries**:
```bash
# Check for missing libraries
ldd dist/VAITP-Auditor-GUI
# Install missing libraries or use static linking
```

**Desktop Integration**:
```bash
# Create desktop file for proper integration
cat > ~/.local/share/applications/vaitp-auditor.desktop << EOF
[Desktop Entry]
Name=VAITP Auditor GUI
Exec=/path/to/VAITP-Auditor-GUI
Icon=/path/to/icon.png
Type=Application
Categories=Development;
EOF
```

### Runtime Issues

#### Application Startup Problems

**GUI Not Displaying**:
```bash
# Linux: Check display environment
echo $DISPLAY
export DISPLAY=:0  # if needed

# Check GUI dependencies
python -c "import tkinter; tkinter.Tk()"  # Should not error

# Run with debug output
./VAITP-Auditor-GUI --debug
```

**Slow Startup**:
- Check available system memory (minimum 4GB recommended)
- Verify SSD storage for better I/O performance
- Close other resource-intensive applications

**Configuration Issues**:
```bash
# Reset configuration to defaults
rm -rf ~/.config/vaitp-auditor/  # Linux/macOS
# or
rmdir /s %APPDATA%\vaitp-auditor\  # Windows
```

#### Performance Issues

**High Memory Usage**:
- Monitor memory usage with built-in performance tools
- Reduce dataset size for large files
- Enable memory optimization in settings

**UI Responsiveness**:
- Check CPU usage during operations
- Verify adequate system resources
- Update graphics drivers

### Getting Help

1. **Check Documentation**:
   - [DEPLOYMENT_PIPELINE_GUIDE.md](DEPLOYMENT_PIPELINE_GUIDE.md)
   - [CODE_SIGNING_GUIDE.md](CODE_SIGNING_GUIDE.md)
   - [DEPLOYMENT_VALIDATION_CHECKLIST.md](DEPLOYMENT_VALIDATION_CHECKLIST.md)

2. **Run Diagnostic Tools**:
   ```bash
   # Test deployment pipeline
   python deployment/test_deployment_pipeline.py
   
   # Validate version consistency
   python deployment/validate_version.py
   
   # Check deployment readiness
   python deployment/validate_deployment.py
   ```

3. **Create Issue Report**:
   - Include platform and Python version
   - Attach build logs and error messages
   - Describe steps to reproduce the issue
   - Include system specifications

## Code Signing Setup

Code signing is essential for user trust and security. The deployment system supports automated code signing for Windows and macOS.

### Certificate Requirements

#### Windows Code Signing
- **Certificate Type**: Standard or EV Code Signing Certificate
- **Recommended Providers**: DigiCert, Sectigo, GlobalSign, SSL.com
- **Cost**: $100-500/year depending on certificate type
- **Format**: .p12 or .pfx file

#### macOS Code Signing
- **Certificate Type**: Developer ID Application certificate
- **Provider**: Apple Developer Program ($99/year)
- **Requirements**: Apple Developer account and Xcode Command Line Tools

### Setting Up Code Signing

#### For GitHub Actions (Automated)

1. **Obtain Certificates** (see [CODE_SIGNING_GUIDE.md](CODE_SIGNING_GUIDE.md) for detailed instructions)

2. **Configure GitHub Secrets**:
   ```bash
   # Windows secrets
   WINDOWS_CERT_BASE64=<base64-encoded-certificate>
   WINDOWS_CERT_PASSWORD=<certificate-password>
   
   # macOS secrets
   MACOS_CERT_BASE64=<base64-encoded-certificate>
   MACOS_CERT_PASSWORD=<certificate-password>
   MACOS_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
   ```

3. **Enable Signing in Workflow**: The GitHub Actions workflow automatically detects and uses certificates when secrets are configured.

#### For Local Development

1. **Windows**:
   ```bash
   # Install Windows SDK for signtool
   # Place certificate file in secure location
   python deployment/build_executable.py --sign --cert-path path/to/cert.p12 --cert-password "password"
   ```

2. **macOS**:
   ```bash
   # Install certificate in Keychain
   # Find identity name
   security find-identity -v -p codesigning
   
   # Build with signing
   python deployment/build_executable.py --sign --identity "Developer ID Application: Your Name"
   ```

### Certificate Management Best Practices

1. **Security**:
   - Never commit certificates to version control
   - Use encrypted secrets in CI/CD systems
   - Rotate certificates before expiration
   - Maintain secure backups

2. **Validation**:
   - Test signing process before production use
   - Verify signatures after building
   - Monitor certificate expiration dates

For detailed code signing instructions, see [CODE_SIGNING_GUIDE.md](CODE_SIGNING_GUIDE.md).

### Security Scanning

Run security scans on executables before distribution:

```bash
# Virus scanning
clamscan dist/VAITP-Auditor-GUI.exe

# Dependency vulnerability scanning
pip-audit

# Static analysis
bandit -r vaitp_auditor/
```

## Maintenance

### Version Updates

1. **Update Version Numbers**:

   - `setup.py`
   - `pyinstaller_config.spec`
   - Documentation files

2. **Test New Version**:

   - Run full test suite
   - Build and test executables
   - Verify backward compatibility

3. **Release Process**:
   - Tag release in version control
   - Build distribution packages
   - Update documentation
   - Announce release

### Monitoring

Track deployment metrics:

- Download counts
- Error reports
- Performance metrics
- User feedback

---

_This deployment guide ensures reliable distribution of the VAITP-Auditor GUI across all supported platforms._
