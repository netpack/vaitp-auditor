# GitHub Actions Workflows

This directory contains the GitHub Actions workflows for the VAITP-Auditor project.

## Workflows

### build-and-release.yml

The main CI/CD workflow that handles testing, building, and releasing the application.

**Triggers:**
- Version tags (e.g., `v1.0.0`, `v1.0.0-beta.1`)
- Test branches (`test/**`, `ci/**`)
- Pull requests to `main` and `develop`

**Jobs:**

1. **test**: Runs the test suite across multiple platforms and Python versions
   - Matrix: Ubuntu, Windows, macOS × Python 3.9, 3.10, 3.11
   - Includes code coverage reporting

2. **build**: Creates standalone executables for each platform
   - Requires tests to pass first
   - Uses PyInstaller with the configuration in `deployment/pyinstaller_config.spec`
   - Uploads build artifacts for later use

3. **validate-executables**: Tests that the built executables work correctly
   - Downloads and tests each platform's executable
   - Performs basic functionality checks

4. **release-draft**: Creates or updates a GitHub release draft
   - Only runs for version tags
   - Uses Release Drafter for automated changelog generation

**Usage:**

To trigger a release build:
```bash
git tag v1.0.0
git push origin v1.0.0
```

To test the workflow without releasing:
```bash
git checkout -b test/workflow-validation
git push origin test/workflow-validation
```

### validate-workflow.yml

A validation workflow that checks the syntax and structure of the GitHub Actions workflows.

**Triggers:**
- Changes to workflow files
- Pull requests affecting workflow files

**Purpose:**
- Validates YAML syntax
- Checks that required files exist
- Validates Python script syntax

## Configuration Files

### release-drafter.yml

Configuration for the Release Drafter action that automatically generates release notes.

**Features:**
- Categorizes changes by type (Features, Bug Fixes, Maintenance, etc.)
- Automatically determines version numbers based on labels
- Generates installation instructions
- Creates professional release notes

**Labels:**
- `feature`, `enhancement` → Minor version bump
- `fix`, `bugfix`, `bug` → Patch version bump
- `major`, `breaking` → Major version bump

## Secrets Required

The workflows require the following GitHub secrets:

- `GITHUB_TOKEN` (automatically provided by GitHub)

For code signing (future enhancement):
- `WINDOWS_CERT` - Windows code signing certificate
- `MACOS_CERT` - macOS code signing certificate

## Platform-Specific Notes

### Windows
- Builds `.exe` executable
- Includes Windows-specific dependencies
- Future: Code signing with Authenticode

### macOS
- Builds `.app` bundle
- Includes macOS-specific metadata
- Future: Code signing and notarization

### Linux
- Builds standalone binary
- Compatible with major Linux distributions
- Future: AppImage packaging

## Troubleshooting

### Build Failures

1. **Dependency Issues**: Check that all required packages are listed in `setup.py`
2. **PyInstaller Errors**: Review the spec file configuration
3. **Platform-Specific Issues**: Check the build logs for platform-specific errors

### Test Failures

1. **GUI Tests on Linux**: Ensure `xvfb` is properly configured
2. **Import Errors**: Verify all modules are properly installed
3. **Coverage Issues**: Check that test coverage meets requirements

### Release Issues

1. **Tag Format**: Ensure tags follow the format `v*` (e.g., `v1.0.0`)
2. **Permissions**: Verify repository permissions for creating releases
3. **Artifact Upload**: Check that build artifacts are properly generated

## Development

To test workflow changes locally:

1. Use [act](https://github.com/nektos/act) to run workflows locally
2. Create test branches with `test/` prefix
3. Use the validation workflow to check syntax

Example with act:
```bash
# Install act
brew install act

# Run the test job locally
act -j test

# Run specific workflow
act -W .github/workflows/build-and-release.yml
```