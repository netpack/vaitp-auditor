# Deployment Pipeline Validation Checklist

Use this checklist to validate the deployment pipeline before creating production releases.

## Pre-Release Validation

### 🔧 Configuration Validation

- [ ] GitHub Actions workflow files are present and valid
  - [ ] `.github/workflows/build-and-release.yml`
  - [ ] `.github/workflows/release-drafter.yml`
- [ ] Release Drafter configuration is present and valid
  - [ ] `.github/release-drafter.yml`
- [ ] Build scripts are present and executable
  - [ ] `deployment/build_executable.py`
  - [ ] `deployment/validate_version.py`
  - [ ] `deployment/validate_deployment.py`

### 🧪 Test Pipeline Execution

- [ ] Create test tag using `deployment/create_test_tag.sh`
- [ ] Verify workflow triggers correctly on test tag
- [ ] Check that all build jobs complete successfully
  - [ ] Windows build job
  - [ ] macOS build job  
  - [ ] Linux build job
- [ ] Verify executable validation passes on all platforms
- [ ] Check that test deployment job completes successfully
- [ ] Verify artifacts are uploaded correctly

### 📦 Artifact Validation

- [ ] Windows artifacts are created
  - [ ] `VAITP-Auditor-GUI.exe`
  - [ ] `VAITP-Auditor-GUI-Windows-x64-v*.zip` (if package job runs)
- [ ] macOS artifacts are created
  - [ ] `VAITP-Auditor-GUI.app`
  - [ ] `VAITP-Auditor-GUI-macOS-v*.dmg` (if DMG creation succeeds)
- [ ] Linux artifacts are created
  - [ ] `VAITP-Auditor-GUI`
  - [ ] `VAITP-Auditor-GUI-Linux-x86_64-v*.AppImage` (if AppImage creation succeeds)
  - [ ] `VAITP-Auditor-GUI-Linux-x86_64-v*.tar.gz` (if package job runs)

### 🔐 Security Validation

- [ ] Code signing works (if certificates are configured)
  - [ ] Windows executable is signed (if `WINDOWS_CERT_BASE64` secret is set)
  - [ ] macOS app bundle is signed (if `MACOS_CERT_BASE64` secret is set)
- [ ] Checksums are generated correctly
- [ ] No sensitive information is exposed in logs

## Production Release Process

### 📋 Pre-Release Steps

- [ ] All tests pass on main branch
- [ ] Version number is updated in `vaitp_auditor/_version.py`
- [ ] CHANGELOG.md is updated with release notes
- [ ] Documentation is up to date
- [ ] All planned features for the release are complete

### 🏷️ Release Tag Creation

- [ ] Create release tag with format `v*.*.*` (e.g., `v1.0.0`)
- [ ] For pre-releases, use format `v*.*.*-beta.*` or `v*.*.*-alpha.*`
- [ ] Push tag to trigger release workflow

### 🚀 Release Validation

- [ ] Release workflow completes successfully
- [ ] All platform artifacts are attached to the release
- [ ] Release notes are generated correctly
- [ ] Download links work correctly
- [ ] Checksums match downloaded files

### 📱 Post-Release Testing

- [ ] Download and test Windows executable
  - [ ] Launches without errors
  - [ ] Core functionality works
  - [ ] No antivirus false positives
- [ ] Download and test macOS app
  - [ ] Launches without Gatekeeper issues
  - [ ] App bundle is properly structured
  - [ ] Core functionality works
- [ ] Download and test Linux AppImage
  - [ ] Executable permissions are correct
  - [ ] Launches without errors
  - [ ] Core functionality works

### 📢 Communication

- [ ] Update project README if needed
- [ ] Announce release in appropriate channels
- [ ] Update documentation links if needed
- [ ] Monitor for user feedback and issues

## Troubleshooting

### Common Issues

1. **Build failures**
   - Check dependency versions
   - Verify Python version compatibility
   - Check for missing build tools

2. **Code signing failures**
   - Verify certificate secrets are correctly configured
   - Check certificate expiration dates
   - Ensure certificates have proper permissions

3. **Artifact upload failures**
   - Check GitHub Actions permissions
   - Verify artifact paths are correct
   - Check for file size limits

4. **Release creation failures**
   - Verify GITHUB_TOKEN permissions
   - Check Release Drafter configuration
   - Ensure tag format is correct

### Getting Help

- Check GitHub Actions logs for detailed error messages
- Review workflow configuration files
- Test locally using build scripts
- Consult deployment documentation in `deployment/README.md`

---

**Last Updated**: $(date +%Y-%m-%d)
**Pipeline Version**: 1.0.0
