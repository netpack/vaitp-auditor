# VAITP-Auditor Versioning Strategy

## Overview

VAITP-Auditor follows [Semantic Versioning](https://semver.org/) (SemVer) for consistent and predictable version numbering across all distribution methods.

## Version Format

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
```

- **MAJOR**: Incremented for incompatible API changes
- **MINOR**: Incremented for backwards-compatible functionality additions
- **PATCH**: Incremented for backwards-compatible bug fixes
- **PRERELEASE**: Optional identifier for pre-release versions (alpha, beta, rc)
- **BUILD**: Optional build metadata (build number, git hash)

## Examples

- `1.0.0` - First stable release
- `1.1.0` - Minor feature addition
- `1.1.1` - Bug fix release
- `2.0.0` - Major version with breaking changes
- `1.2.0-beta.1` - Beta pre-release
- `1.1.0+build.123.abc1234` - Release with build metadata

## Version Management

### Single Source of Truth

All version information is centralized in `vaitp_auditor/_version.py`:

```python
__version__ = "0.1.0"
__version_info__ = (0, 1, 0)
__release_date__ = "2025-09-25"
__release_name__ = "Initial Release"
```

### Distribution Consistency

All distribution methods use the same version:

- **setup.py**: Imports `__version__` from `_version.py`
- **Package __init__.py**: Imports version information from `_version.py`
- **GUI module**: Imports version from parent `_version.py`
- **Build scripts**: Read version from `_version.py`

### Version Validation

Use the validation script to ensure consistency:

```bash
python deployment/validate_version.py
```

This script checks:
- Version format follows semantic versioning
- All files import version from the single source
- No hardcoded version strings exist

## Release Process

### 1. Version Bumping

Update version in `vaitp_auditor/_version.py`:

```python
# For patch release (bug fixes)
__version__ = "0.1.1"

# For minor release (new features)
__version__ = "0.2.0"

# For major release (breaking changes)
__version__ = "1.0.0"
```

### 2. Pre-release Versions

For testing and beta releases:

```python
__version__ = "1.0.0-beta.1"  # First beta
__version__ = "1.0.0-beta.2"  # Second beta
__version__ = "1.0.0-rc.1"    # Release candidate
```

### 3. Build Information

Build scripts can add build metadata:

```bash
python deployment/validate_version.py --update-build-info --build-number 123 --git-hash abc1234
```

This updates the version module with build information that appears in `get_full_version()`.

### 4. Validation

Always validate before release:

```bash
python deployment/validate_version.py
```

## Version Access

### In Python Code

```python
import vaitp_auditor

# Get version string
version = vaitp_auditor.__version__
# or
version = vaitp_auditor.get_version()

# Get version tuple
version_info = vaitp_auditor.get_version_info()  # (0, 1, 0)

# Get full version with build info
full_version = vaitp_auditor.get_full_version()  # "0.1.0+build.123.abc1234"

# Get all release information
release_info = vaitp_auditor.get_release_info()
```

### From Command Line

```bash
# CLI version
vaitp-auditor --version

# GUI version (in about dialog)
vaitp-auditor-gui
```

### In Build Scripts

```python
from vaitp_auditor._version import __version__, get_full_version

print(f"Building version {__version__}")
print(f"Full version: {get_full_version()}")
```

## Release Numbering Scheme

### Current Development (0.x.x)

- `0.1.0` - Initial release with basic CLI and GUI functionality
- `0.1.x` - Bug fixes and minor improvements
- `0.2.0` - Additional data sources and features
- `0.x.0` - New features and enhancements

### Stable Release (1.x.x)

- `1.0.0` - First stable release with complete feature set
- `1.x.0` - New features maintaining backwards compatibility
- `1.x.x` - Bug fixes and security updates

### Major Updates (2.x.x+)

- `2.0.0` - Major architectural changes or breaking API changes
- Future major versions for significant rewrites or paradigm shifts

## Automation

### GitHub Actions Integration

Version tags trigger automated builds:

```yaml
on:
  push:
    tags:
      - 'v*'  # Triggers on version tags like v1.0.0
```

### Release Drafter

Automatically generates release notes based on:
- Version number from tag
- Commit messages and pull requests
- Categorized changes (features, fixes, breaking changes)

## Best Practices

### Version Updates

1. **Always update `_version.py` first**
2. **Run validation script before committing**
3. **Use descriptive release names for major versions**
4. **Update release date when bumping version**
5. **Test all distribution methods after version changes**

### Pre-release Testing

1. **Use beta versions for testing new features**
2. **Use release candidates for final testing**
3. **Never skip validation for any version change**
4. **Test installation from all distribution methods**

### Documentation

1. **Update CHANGELOG.md for every version**
2. **Document breaking changes clearly**
3. **Include migration guides for major versions**
4. **Keep version history in release notes**

## Troubleshooting

### Common Issues

**Version Mismatch Errors**
```bash
# Run validation to identify issues
python deployment/validate_version.py

# Check for hardcoded versions
grep -r "version.*=.*[\"'][0-9]" --exclude-dir=venv .
```

**Build Failures**
```bash
# Ensure version module is importable
python -c "from vaitp_auditor._version import __version__; print(__version__)"

# Check setup.py can import version
python setup.py --version
```

**Import Errors**
- Ensure `_version.py` is in the correct location
- Check that all imports use relative paths correctly
- Verify no circular imports exist

### Recovery Steps

1. **Reset to known good version**
2. **Run validation script**
3. **Fix any identified issues**
4. **Test all distribution methods**
5. **Commit changes with clear message**

## Future Enhancements

- Automated version bumping based on commit messages
- Integration with package managers for version checking
- Automated changelog generation from version history
- Version compatibility checking for dependencies