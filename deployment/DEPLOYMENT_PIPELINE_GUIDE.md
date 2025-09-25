# Deployment Pipeline Guide

This guide explains how to use the automated deployment pipeline for VAITP-Auditor GUI.

## Overview

The deployment pipeline automatically builds executables for Windows, macOS, and Linux, then creates GitHub releases with all necessary assets. The pipeline is triggered by pushing version tags.

## Pipeline Components

### 🔧 GitHub Actions Workflows

1. **Build and Release** (`.github/workflows/build-and-release.yml`)
   - Builds executables for all platforms
   - Validates executables
   - Creates GitHub releases
   - Triggered by version tags (`v*`)

2. **Release Drafter** (`.github/workflows/release-drafter.yml`)
   - Automatically updates release drafts
   - Categorizes changes based on PR labels
   - Triggered by pushes to main/develop branches

### 📦 Build Jobs

- **Windows**: Creates `.exe` executable and optional ZIP package
- **macOS**: Creates `.app` bundle and optional DMG installer
- **Linux**: Creates binary executable and optional AppImage

### 🔐 Code Signing (Optional)

The pipeline supports code signing for Windows and macOS executables when certificates are configured:

- **Windows**: Uses `WINDOWS_CERT_BASE64` and `WINDOWS_CERT_PASSWORD` secrets
- **macOS**: Uses `MACOS_CERT_BASE64`, `MACOS_CERT_PASSWORD`, and `MACOS_KEYCHAIN_PASSWORD` secrets

## Quick Start

### 1. Test the Pipeline

Before creating a production release, test the pipeline:

```bash
# Run pipeline validation tests
python deployment/test_deployment_pipeline.py

# Create a test tag to trigger the pipeline
./deployment/create_test_tag.sh
```

### 2. Create a Release

For a production release:

```bash
# Ensure version is updated
vim vaitp_auditor/_version.py

# Create and push release tag
git tag v1.0.0
git push origin v1.0.0
```

The pipeline will automatically:
1. Build executables for all platforms
2. Run validation tests
3. Create a GitHub release
4. Attach all build artifacts

## Release Types

### Stable Releases

Use semantic versioning: `v1.0.0`, `v1.2.3`, etc.

```bash
git tag v1.0.0
git push origin v1.0.0
```

### Pre-releases

Include pre-release identifiers: `v1.0.0-beta.1`, `v1.0.0-alpha.2`, etc.

```bash
git tag v1.0.0-beta.1
git push origin v1.0.0-beta.1
```

Pre-releases are automatically marked as such in GitHub.

## Testing the Pipeline

### Automated Testing

Run the comprehensive test suite:

```bash
# Test everything
python deployment/test_deployment_pipeline.py

# Test specific components
python deployment/test_deployment_pipeline.py --test workflow
python deployment/test_deployment_pipeline.py --test drafter
```

### Manual Testing

1. **Create Test Tag**:
   ```bash
   ./deployment/create_test_tag.sh
   ```

2. **Monitor Workflow**:
   - Go to GitHub Actions tab
   - Watch the build progress
   - Check for any failures

3. **Validate Artifacts**:
   - Download test artifacts
   - Verify executables work correctly
   - Check file sizes and signatures

## Configuration

### Required Files

- `.github/workflows/build-and-release.yml` - Main workflow
- `.github/workflows/release-drafter.yml` - Release draft automation
- `.github/release-drafter.yml` - Release Drafter configuration
- `deployment/build_executable.py` - Build script
- `deployment/validate_version.py` - Version validation
- `deployment/validate_deployment.py` - Deployment validation

### Optional Secrets

Configure these in GitHub repository settings for enhanced functionality:

#### Code Signing
- `WINDOWS_CERT_BASE64` - Base64-encoded Windows code signing certificate
- `WINDOWS_CERT_PASSWORD` - Password for Windows certificate
- `MACOS_CERT_BASE64` - Base64-encoded macOS Developer ID certificate
- `MACOS_CERT_PASSWORD` - Password for macOS certificate
- `MACOS_KEYCHAIN_PASSWORD` - Password for temporary keychain

#### Notifications (Optional)
- `SLACK_WEBHOOK` - Slack webhook for release notifications
- `DISCORD_WEBHOOK` - Discord webhook for release notifications

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Python version compatibility
   - Verify all dependencies are available
   - Review build logs for specific errors

2. **Code Signing Failures**
   - Verify certificate secrets are correctly configured
   - Check certificate expiration dates
   - Ensure certificates have proper permissions

3. **Release Creation Failures**
   - Verify `GITHUB_TOKEN` has sufficient permissions
   - Check tag format (must start with `v`)
   - Ensure Release Drafter configuration is valid

### Debug Steps

1. **Check Workflow Logs**:
   - Go to GitHub Actions tab
   - Click on failed workflow run
   - Review detailed logs for each job

2. **Test Locally**:
   ```bash
   # Test build script locally
   python deployment/build_executable.py
   
   # Validate version consistency
   python deployment/validate_version.py
   
   # Run deployment tests
   python deployment/test_deployment_pipeline.py
   ```

3. **Validate Configuration**:
   ```bash
   # Check workflow syntax
   yamllint .github/workflows/build-and-release.yml
   
   # Check Release Drafter config
   yamllint .github/release-drafter.yml
   ```

## Best Practices

### Before Releasing

1. ✅ Run all tests locally
2. ✅ Update version in `vaitp_auditor/_version.py`
3. ✅ Update `CHANGELOG.md` with release notes
4. ✅ Test the pipeline with a test tag
5. ✅ Review the deployment validation checklist

### Release Process

1. 🏷️ Create semantic version tag
2. 📤 Push tag to trigger pipeline
3. 👀 Monitor workflow execution
4. ✅ Validate generated release
5. 📢 Announce release if needed

### After Releasing

1. 📥 Test download and installation
2. 🐛 Monitor for user-reported issues
3. 📊 Review download metrics
4. 📝 Update documentation if needed

## Pipeline Metrics

The pipeline tracks several metrics:

- **Build Time**: Time to build all platform executables
- **Artifact Size**: Size of generated executables and packages
- **Success Rate**: Percentage of successful deployments
- **Download Count**: Number of downloads per release

## Support

For pipeline issues:

1. 📖 Check this guide and the validation checklist
2. 🔍 Review GitHub Actions logs
3. 🧪 Run local tests to isolate issues
4. 🐛 Create an issue with detailed error information

---

**Pipeline Version**: 1.0.0  
**Last Updated**: $(date +%Y-%m-%d)  
**Maintainer**: VAITP Research Team