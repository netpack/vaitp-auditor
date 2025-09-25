# VAITP-Auditor Maintainer Guide

This guide provides comprehensive instructions for maintainers on release management, version control, and deployment pipeline maintenance.

## Table of Contents

1. [Release Process](#release-process)
2. [Version Management](#version-management)
3. [GitHub Actions Workflow Maintenance](#github-actions-workflow-maintenance)
4. [Beta Release Management](#beta-release-management)
5. [Release Preparation Scripts](#release-preparation-scripts)
6. [Validation and Quality Assurance](#validation-and-quality-assurance)
7. [Documentation Generation](#documentation-generation)
8. [Monitoring and Metrics](#monitoring-and-metrics)
9. [Troubleshooting](#troubleshooting)

## Release Process

### Overview

The VAITP-Auditor follows semantic versioning and uses automated GitHub Actions workflows for building and releasing across all supported platforms.

### Release Types

1. **Stable Releases** (`v1.0.0`, `v1.2.3`)
   - Production-ready releases
   - Full testing and validation required
   - Automatic deployment to all channels

2. **Pre-releases** (`v1.0.0-beta.1`, `v1.0.0-alpha.2`)
   - Testing and feedback releases
   - Limited distribution
   - Marked as pre-release in GitHub

3. **Patch Releases** (`v1.0.1`, `v1.2.4`)
   - Bug fixes and minor improvements
   - Fast-track release process
   - Minimal testing required

### Standard Release Workflow

#### 1. Pre-Release Preparation

```bash
# 1. Ensure all planned features are complete
git checkout main
git pull origin main

# 2. Run comprehensive tests
python -m pytest tests/ -v --cov=vaitp_auditor --cov-report=html

# 3. Update version number
python deployment/prepare_release.py --version 1.0.0

# 4. Update CHANGELOG.md
python deployment/update_changelog.py --version 1.0.0

# 5. Validate release readiness
python deployment/validate_deployment.py --pre-release-check
```

#### 2. Release Creation

```bash
# 1. Commit version changes
git add .
git commit -m "Prepare release v1.0.0"
git push origin main

# 2. Create and push release tag
git tag v1.0.0
git push origin v1.0.0

# 3. Monitor GitHub Actions workflow
# Go to: https://github.com/your-org/vaitp-auditor/actions
```

#### 3. Post-Release Validation

```bash
# 1. Verify release was created successfully
python deployment/validate_release.py --version 1.0.0

# 2. Test download and installation
python deployment/test_release_artifacts.py --version 1.0.0

# 3. Update documentation if needed
python deployment/update_docs.py --post-release
```

### Emergency Patch Release

For critical bug fixes that need immediate release:

```bash
# 1. Create hotfix branch
git checkout -b hotfix/v1.0.1 v1.0.0

# 2. Apply fixes
# ... make necessary changes ...

# 3. Test fixes
python -m pytest tests/ -k "critical"

# 4. Prepare patch release
python deployment/prepare_release.py --version 1.0.1 --patch

# 5. Merge and release
git checkout main
git merge hotfix/v1.0.1
git tag v1.0.1
git push origin main v1.0.1
```

## Version Management

### Versioning Strategy

VAITP-Auditor follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** (`1.0.0` → `2.0.0`): Breaking changes, API changes
- **MINOR** (`1.0.0` → `1.1.0`): New features, backward compatible
- **PATCH** (`1.0.0` → `1.0.1`): Bug fixes, backward compatible

### Version File Locations

Version information is maintained in multiple files:

1. **Primary Source**: `vaitp_auditor/_version.py`
2. **Setup Configuration**: `setup.py`
3. **Documentation**: `docs/VERSIONING.md`
4. **Changelog**: `CHANGELOG.md`

### Version Update Process

Use the automated script to ensure consistency:

```bash
# Update version across all files
python deployment/prepare_release.py --version 1.2.0

# Verify version consistency
python deployment/validate_version.py
```

### Pre-release Versioning

For pre-releases, use these suffixes:

- **Alpha**: `v1.0.0-alpha.1` (early development)
- **Beta**: `v1.0.0-beta.1` (feature complete, testing)
- **Release Candidate**: `v1.0.0-rc.1` (final testing)

## GitHub Actions Workflow Maintenance

### Workflow Files

1. **Main Workflow**: `.github/workflows/build-and-release.yml`
   - Builds executables for all platforms
   - Runs validation tests
   - Creates GitHub releases

2. **Release Drafter**: `.github/workflows/release-drafter.yml`
   - Automatically updates release drafts
   - Categorizes changes based on PR labels

3. **Test Workflow**: `.github/workflows/test-build.yml`
   - Runs on pull requests
   - Tests build process without releasing

### Workflow Configuration

#### Required Secrets

Configure these in GitHub repository settings:

```yaml
# Code signing (optional but recommended)
WINDOWS_CERT_BASE64: <base64-encoded Windows certificate>
WINDOWS_CERT_PASSWORD: <Windows certificate password>
MACOS_CERT_BASE64: <base64-encoded macOS certificate>
MACOS_CERT_PASSWORD: <macOS certificate password>
MACOS_IDENTITY: "Developer ID Application: Your Name (TEAM_ID)"

# Notifications (optional)
SLACK_WEBHOOK: <Slack webhook URL>
DISCORD_WEBHOOK: <Discord webhook URL>
```

#### Workflow Monitoring

```bash
# Check workflow status
python deployment/check_workflow_status.py

# View recent workflow runs
gh run list --workflow=build-and-release.yml

# Download workflow artifacts for testing
gh run download <run-id>
```

### Updating Workflows

When modifying workflows:

1. **Test Changes**: Use test tags to validate changes
2. **Validate Syntax**: Use `yamllint` to check YAML syntax
3. **Document Changes**: Update this guide and workflow comments
4. **Monitor First Run**: Watch the first execution carefully

```bash
# Validate workflow syntax
yamllint .github/workflows/build-and-release.yml

# Test workflow changes
./deployment/create_test_tag.sh

# Monitor workflow execution
gh run watch
```

## Beta Release Management

### Beta Release Process

Beta releases allow testing new features with a limited audience:

```bash
# 1. Prepare beta release
python deployment/prepare_release.py --version 1.1.0-beta.1

# 2. Create beta tag
git tag v1.1.0-beta.1
git push origin v1.1.0-beta.1

# 3. Monitor beta feedback
python deployment/monitor_beta_feedback.py --version 1.1.0-beta.1
```

### Beta Testing Checklist

- [ ] All new features are functional
- [ ] No critical bugs in core functionality
- [ ] Documentation updated for new features
- [ ] Beta testers have been notified
- [ ] Feedback collection mechanism in place

### Promoting Beta to Stable

```bash
# 1. Collect and review beta feedback
python deployment/collect_beta_feedback.py --version 1.1.0-beta.1

# 2. Address critical issues
# ... fix any reported issues ...

# 3. Prepare stable release
python deployment/prepare_release.py --version 1.1.0 --from-beta 1.1.0-beta.1

# 4. Release stable version
git tag v1.1.0
git push origin v1.1.0
```

## Release Preparation Scripts

### Available Scripts

#### `deployment/prepare_release.py`

Automates version updates and release preparation:

```bash
# Basic usage
python deployment/prepare_release.py --version 1.0.0

# With changelog update
python deployment/prepare_release.py --version 1.0.0 --update-changelog

# Patch release
python deployment/prepare_release.py --version 1.0.1 --patch

# Beta release
python deployment/prepare_release.py --version 1.1.0-beta.1 --beta
```

#### `deployment/update_changelog.py`

Updates CHANGELOG.md with new release information:

```bash
# Interactive changelog update
python deployment/update_changelog.py --version 1.0.0

# Automatic update from git commits
python deployment/update_changelog.py --version 1.0.0 --auto

# Add specific changes
python deployment/update_changelog.py --version 1.0.0 --add "Fixed critical bug in data processing"
```

#### `deployment/validate_release.py`

Validates release artifacts and deployment:

```bash
# Validate specific release
python deployment/validate_release.py --version 1.0.0

# Validate latest release
python deployment/validate_release.py --latest

# Full validation including downloads
python deployment/validate_release.py --version 1.0.0 --full
```

### Creating New Scripts

When creating new release preparation scripts:

1. **Follow Naming Convention**: Use descriptive names with `deployment/` prefix
2. **Add Help Text**: Include comprehensive `--help` documentation
3. **Error Handling**: Implement robust error handling and rollback
4. **Logging**: Use consistent logging format
5. **Testing**: Include unit tests in `tests/` directory

Example script template:

```python
#!/usr/bin/env python3
"""
Script description here.
"""

import argparse
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Script description")
    parser.add_argument('--version', required=True, help='Version to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    args = parser.parse_args()
    
    try:
        # Script logic here
        logger.info(f"Processing version {args.version}")
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

## Validation and Quality Assurance

### Pre-Release Validation

Before any release, run the complete validation suite:

```bash
# 1. Code quality checks
python -m flake8 vaitp_auditor/
python -m black --check vaitp_auditor/
python -m isort --check-only vaitp_auditor/

# 2. Security scanning
python -m bandit -r vaitp_auditor/
python -m safety check

# 3. Dependency validation
python -m pip-audit

# 4. Test suite
python -m pytest tests/ -v --cov=vaitp_auditor --cov-report=html

# 5. Build validation
python deployment/build_executable.py --validate

# 6. Deployment validation
python deployment/validate_deployment.py
```

### Release Validation Checklist

Use this checklist for every release:

#### Code Quality
- [ ] All tests pass
- [ ] Code coverage above 80%
- [ ] No security vulnerabilities
- [ ] Dependencies are up to date
- [ ] Code style is consistent

#### Documentation
- [ ] README.md is current
- [ ] CHANGELOG.md is updated
- [ ] API documentation is current
- [ ] User guides are updated

#### Build and Deployment
- [ ] All platforms build successfully
- [ ] Executables launch and function correctly
- [ ] Code signing works (if configured)
- [ ] Release artifacts are complete

#### User Experience
- [ ] Setup wizard works correctly
- [ ] Core functionality is stable
- [ ] Performance meets targets
- [ ] UI is responsive and accessible

## Documentation Generation

### Automated Documentation

Generate documentation from code and CLI help:

```bash
# Generate CLI documentation
python deployment/generate_cli_docs.py

# Update API documentation
python deployment/generate_api_docs.py

# Generate user guide from docstrings
python deployment/generate_user_docs.py

# Update all documentation
python deployment/update_all_docs.py
```

### Documentation Maintenance

#### Regular Updates

1. **After Feature Addition**: Update relevant user guides
2. **After API Changes**: Regenerate API documentation
3. **Before Releases**: Ensure all documentation is current
4. **After User Feedback**: Address documentation gaps

#### Documentation Structure

```
docs/
├── USER_GUIDE.md           # End-user documentation
├── DEVELOPER_GUIDE.md      # Developer setup and contribution
├── GUI_USER_GUIDE.md       # GUI-specific user guide
├── GUI_DEVELOPER_GUIDE.md  # GUI development guide
├── SETUP_GUIDE.md          # Installation and setup
├── VERSIONING.md           # Version history and strategy
└── api/                    # Auto-generated API docs
    ├── core/
    ├── gui/
    └── data_sources/
```

## Monitoring and Metrics

### Release Metrics

Track these metrics for each release:

1. **Download Statistics**
   - Total downloads per platform
   - Download trends over time
   - Geographic distribution

2. **User Feedback**
   - GitHub issues and discussions
   - User surveys and feedback
   - Performance reports

3. **Technical Metrics**
   - Build success rates
   - Test coverage trends
   - Security scan results

### Monitoring Tools

```bash
# Check download statistics
python deployment/check_download_stats.py --version 1.0.0

# Monitor GitHub issues
python deployment/monitor_issues.py --since "2024-01-01"

# Generate metrics report
python deployment/generate_metrics_report.py --month 2024-01
```

### Performance Monitoring

Monitor application performance across releases:

```bash
# Benchmark current version
python deployment/benchmark_executable.py

# Compare with previous version
python deployment/compare_performance.py --baseline v1.0.0 --current v1.1.0

# Generate performance report
python deployment/performance_report.py --version 1.1.0
```

## Troubleshooting

### Common Release Issues

#### Build Failures

**Symptom**: GitHub Actions build jobs fail

**Diagnosis**:
```bash
# Check workflow logs
gh run view <run-id> --log

# Test build locally
python deployment/build_executable.py --debug

# Validate dependencies
python deployment/build_executable.py --check-deps
```

**Solutions**:
- Update dependencies in requirements files
- Fix import errors in code
- Update PyInstaller configuration
- Check platform-specific issues

#### Code Signing Issues

**Symptom**: Executables are not signed or signing fails

**Diagnosis**:
```bash
# Check certificate configuration
python deployment/check_certificates.py

# Validate certificate expiration
python deployment/validate_certificates.py
```

**Solutions**:
- Renew expired certificates
- Update GitHub secrets
- Fix certificate passwords
- Check certificate permissions

#### Release Creation Failures

**Symptom**: GitHub release is not created

**Diagnosis**:
```bash
# Check Release Drafter configuration
yamllint .github/release-drafter.yml

# Validate GitHub token permissions
gh auth status
```

**Solutions**:
- Fix Release Drafter configuration
- Update GitHub token permissions
- Check tag format and naming
- Verify workflow file syntax

### Emergency Procedures

#### Rolling Back a Release

If a release has critical issues:

```bash
# 1. Mark release as pre-release to hide it
gh release edit v1.0.0 --prerelease

# 2. Create hotfix
git checkout -b hotfix/v1.0.1 v1.0.0
# ... apply fixes ...

# 3. Release hotfix
python deployment/prepare_release.py --version 1.0.1 --hotfix
git tag v1.0.1
git push origin v1.0.1

# 4. Delete problematic release (if necessary)
gh release delete v1.0.0 --yes
```

#### Workflow Recovery

If GitHub Actions workflow is broken:

```bash
# 1. Disable workflow
gh workflow disable build-and-release.yml

# 2. Fix workflow file
# ... edit .github/workflows/build-and-release.yml ...

# 3. Test with test tag
./deployment/create_test_tag.sh

# 4. Re-enable workflow
gh workflow enable build-and-release.yml
```

### Getting Help

1. **Internal Resources**:
   - Check this maintainer guide
   - Review deployment documentation
   - Run diagnostic scripts

2. **External Resources**:
   - GitHub Actions documentation
   - PyInstaller documentation
   - Platform-specific signing guides

3. **Support Channels**:
   - Create internal issue for team discussion
   - Contact platform support for signing issues
   - Consult community forums for technical issues

---

**Guide Version**: 1.0.0  
**Last Updated**: 2024-01-15  
**Maintainer**: VAITP Research Team

For questions about this guide or the release process, please create an issue or contact the development team.