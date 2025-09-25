# Code Signing Guide for VAITP-Auditor

This guide explains how to set up and use code signing for VAITP-Auditor executables on different platforms.

## Overview

Code signing is essential for:
- **Security**: Verifies the authenticity and integrity of executables
- **User Trust**: Prevents security warnings during installation/execution
- **Distribution**: Required for app stores and enterprise deployment
- **Compliance**: Meets security requirements for many organizations

## Platform-Specific Setup

### Windows Code Signing

#### Prerequisites
1. **Windows SDK**: Install Windows 10/11 SDK for `signtool.exe`
2. **Code Signing Certificate**: Obtain from a trusted Certificate Authority (CA)

#### Certificate Types
- **EV Code Signing Certificate** (Recommended)
  - Highest trust level
  - No SmartScreen warnings
  - Requires hardware token or cloud HSM
  - Cost: $300-500/year

- **Standard Code Signing Certificate**
  - Basic code signing
  - May show SmartScreen warnings initially
  - Software-based certificate
  - Cost: $100-300/year

#### Recommended Certificate Providers
- **DigiCert**: Industry leader, excellent support
- **Sectigo (formerly Comodo)**: Good value, reliable
- **GlobalSign**: Trusted CA with competitive pricing
- **SSL.com**: Affordable options with good support

#### Setup Steps

1. **Install Windows SDK**
   ```powershell
   # Download from Microsoft Developer site
   # Or install via Visual Studio Installer
   # Verify installation:
   signtool
   ```

2. **Obtain Certificate**
   - Purchase from CA (see providers above)
   - Complete identity verification process
   - Download certificate as .p12 or .pfx file

3. **Test Certificate**
   ```powershell
   # List certificates in file
   certutil -dump certificate.p12
   
   # Import to certificate store (optional)
   certutil -importpfx certificate.p12
   ```

#### Signing Process

```bash
# Using build script
python deployment/build_executable.py --sign --cert-path path/to/cert.p12 --cert-password "password"

# Manual signing
signtool sign /f certificate.p12 /p password /t http://timestamp.digicert.com /fd SHA256 /v executable.exe
```

#### Environment Variables (CI/CD)
```yaml
# GitHub Actions secrets
WINDOWS_CERT_BASE64: <base64-encoded certificate>
WINDOWS_CERT_PASSWORD: <certificate password>

# Usage in workflow
- name: Decode certificate
  run: |
    echo "${{ secrets.WINDOWS_CERT_BASE64 }}" | base64 -d > cert.p12
    
- name: Sign executable
  run: |
    python deployment/build_executable.py --sign --cert-path cert.p12 --cert-password "${{ secrets.WINDOWS_CERT_PASSWORD }}"
```

### macOS Code Signing

#### Prerequisites
1. **Xcode Command Line Tools**: For `codesign` utility
2. **Apple Developer Account**: Required for certificates
3. **Code Signing Certificate**: From Apple Developer Portal

#### Certificate Types
- **Developer ID Application** (Recommended for distribution)
  - For apps distributed outside Mac App Store
  - Bypasses Gatekeeper warnings
  - Cost: $99/year (Apple Developer Program)

- **Mac App Store Certificate**
  - For Mac App Store distribution only
  - Included with Apple Developer Program

#### Setup Steps

1. **Install Xcode Command Line Tools**
   ```bash
   xcode-select --install
   # Verify installation:
   codesign --version
   ```

2. **Create Certificate Signing Request (CSR)**
   - Open Keychain Access
   - Certificate Assistant → Request a Certificate from a Certificate Authority
   - Save CSR file

3. **Generate Certificate in Apple Developer Portal**
   - Login to [developer.apple.com](https://developer.apple.com)
   - Certificates, Identifiers & Profiles
   - Create new "Developer ID Application" certificate
   - Upload CSR file
   - Download certificate

4. **Install Certificate**
   - Double-click downloaded certificate
   - Install in "login" keychain
   - Verify in Keychain Access

5. **Find Certificate Identity**
   ```bash
   # List available identities
   security find-identity -v -p codesigning
   
   # Example output:
   # 1) ABC123... "Developer ID Application: Your Name (TEAM_ID)"
   ```

#### Signing Process

```bash
# Using build script
python deployment/build_executable.py --sign --identity "Developer ID Application: Your Name (TEAM_ID)"

# Manual signing
codesign --sign "Developer ID Application: Your Name (TEAM_ID)" --force --verbose --timestamp --options runtime VAITP-Auditor-GUI.app

# Verify signature
codesign --verify --verbose VAITP-Auditor-GUI.app
```

#### Notarization (Recommended)

For macOS 10.15+ compatibility, notarize your app:

```bash
# Create app-specific password in Apple ID account
# Store in keychain
xcrun altool --store-password-in-keychain-item "NOTARIZATION_PASSWORD" -u "your-apple-id@example.com" -p "app-specific-password"

# Notarize app
xcrun altool --notarize-app --primary-bundle-id "com.vaitp.auditor.gui" --username "your-apple-id@example.com" --password "@keychain:NOTARIZATION_PASSWORD" --file VAITP-Auditor-GUI.app

# Check notarization status
xcrun altool --notarization-info <RequestUUID> --username "your-apple-id@example.com" --password "@keychain:NOTARIZATION_PASSWORD"

# Staple notarization to app
xcrun stapler staple VAITP-Auditor-GUI.app
```

#### Environment Variables (CI/CD)
```yaml
# GitHub Actions secrets
MACOS_CERT_BASE64: <base64-encoded certificate>
MACOS_CERT_PASSWORD: <certificate password>
MACOS_IDENTITY: "Developer ID Application: Your Name (TEAM_ID)"
APPLE_ID: <your-apple-id@example.com>
APPLE_PASSWORD: <app-specific-password>

# Usage in workflow
- name: Import certificate
  run: |
    echo "${{ secrets.MACOS_CERT_BASE64 }}" | base64 -d > cert.p12
    security create-keychain -p temp_password build.keychain
    security import cert.p12 -k build.keychain -P "${{ secrets.MACOS_CERT_PASSWORD }}" -T /usr/bin/codesign
    security list-keychains -s build.keychain
    security unlock-keychain -p temp_password build.keychain
    
- name: Sign app
  run: |
    python deployment/build_executable.py --sign --identity "${{ secrets.MACOS_IDENTITY }}"
```

### Linux (No Code Signing)

Linux doesn't have a standardized code signing system like Windows/macOS. However, you can:

1. **GPG Signatures**: Sign packages with GPG keys
2. **Package Repository Signing**: Sign repository metadata
3. **Checksums**: Provide SHA256 checksums for verification

```bash
# Create GPG signature
gpg --armor --detach-sign VAITP-Auditor-GUI-Linux-x86_64.tar.gz

# Verify signature
gpg --verify VAITP-Auditor-GUI-Linux-x86_64.tar.gz.asc VAITP-Auditor-GUI-Linux-x86_64.tar.gz

# Create checksums
sha256sum VAITP-Auditor-GUI-Linux-x86_64.tar.gz > VAITP-Auditor-GUI-Linux-x86_64.tar.gz.sha256
```

## GitHub Actions Integration

### Complete Workflow Example

```yaml
name: Build and Sign

on:
  push:
    tags: ['v*']

jobs:
  build-and-sign:
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    
    runs-on: ${{ matrix.os }}
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[gui]
        pip install pyinstaller
    
    # Windows signing
    - name: Setup Windows signing
      if: runner.os == 'Windows'
      run: |
        echo "${{ secrets.WINDOWS_CERT_BASE64 }}" | base64 -d > cert.p12
    
    - name: Build and sign Windows
      if: runner.os == 'Windows'
      run: |
        python deployment/build_executable.py --clean --sign --cert-path cert.p12 --cert-password "${{ secrets.WINDOWS_CERT_PASSWORD }}"
    
    # macOS signing
    - name: Setup macOS signing
      if: runner.os == 'macOS'
      run: |
        echo "${{ secrets.MACOS_CERT_BASE64 }}" | base64 -d > cert.p12
        security create-keychain -p temp_password build.keychain
        security import cert.p12 -k build.keychain -P "${{ secrets.MACOS_CERT_PASSWORD }}" -T /usr/bin/codesign
        security list-keychains -s build.keychain
        security unlock-keychain -p temp_password build.keychain
    
    - name: Build and sign macOS
      if: runner.os == 'macOS'
      run: |
        python deployment/build_executable.py --clean --sign --identity "${{ secrets.MACOS_IDENTITY }}" --create-dmg
    
    # Linux build (no signing)
    - name: Build Linux
      if: runner.os == 'Linux'
      run: |
        python deployment/build_executable.py --clean
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: ${{ runner.os }}-executable
        path: |
          dist/*
          *.zip
          *.dmg
          *.tar.gz
```

## Security Best Practices

### Certificate Management
1. **Secure Storage**: Never commit certificates to version control
2. **Environment Variables**: Use encrypted secrets in CI/CD
3. **Access Control**: Limit access to signing certificates
4. **Backup**: Maintain secure backups of certificates
5. **Rotation**: Renew certificates before expiration

### Build Security
1. **Clean Environment**: Use fresh build environments
2. **Dependency Verification**: Verify all dependencies
3. **Reproducible Builds**: Ensure builds are reproducible
4. **Audit Trail**: Log all signing operations

### Distribution Security
1. **Checksums**: Provide SHA256 checksums
2. **Secure Channels**: Use HTTPS for distribution
3. **Signature Verification**: Document verification process
4. **Update Mechanism**: Implement secure update system

## Troubleshooting

### Windows Issues

**"The specified timestamp server either could not be reached or returned an invalid response"**
- Try different timestamp servers:
  - `http://timestamp.digicert.com`
  - `http://timestamp.sectigo.com`
  - `http://timestamp.globalsign.com`

**"SignTool Error: No certificates were found that met all the given criteria"**
- Verify certificate is properly installed
- Check certificate password
- Ensure certificate hasn't expired

### macOS Issues

**"errSecInternalComponent"**
- Unlock keychain: `security unlock-keychain`
- Check certificate installation in Keychain Access

**"The identity used to sign the executable is no longer valid"**
- Certificate may have expired
- Check Apple Developer account status
- Regenerate certificate if needed

**Gatekeeper still shows warnings**
- Ensure using "Developer ID Application" certificate
- Consider notarization for macOS 10.15+

### General Issues

**Build fails after adding signing**
- Test signing separately from build process
- Verify all signing tools are installed
- Check certificate validity and permissions

## Cost Considerations

### Annual Costs
- **Windows EV Certificate**: $300-500
- **Windows Standard Certificate**: $100-300
- **Apple Developer Program**: $99
- **Total (both platforms)**: $400-600/year

### Free Alternatives
- **Self-signed certificates**: For internal use only
- **Test certificates**: For development/testing
- **Open source projects**: Some CAs offer free certificates

## Support and Resources

### Official Documentation
- [Microsoft Code Signing](https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)
- [Apple Code Signing Guide](https://developer.apple.com/library/archive/documentation/Security/Conceptual/CodeSigningGuide/)

### Tools and Utilities
- [SignTool (Windows)](https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool)
- [codesign (macOS)](https://developer.apple.com/library/archive/documentation/Security/Conceptual/CodeSigningGuide/Procedures/Procedures.html)

### Certificate Authorities
- [DigiCert](https://www.digicert.com/code-signing/)
- [Sectigo](https://sectigo.com/ssl-certificates-tls/code-signing)
- [GlobalSign](https://www.globalsign.com/en/code-signing-certificate)
- [SSL.com](https://www.ssl.com/certificates/code-signing/)

For questions or issues with code signing, please:
1. Check this guide first
2. Search existing GitHub issues
3. Create a new issue with detailed error messages
4. Contact the development team