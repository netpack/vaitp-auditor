# Contributing to VAITP-Auditor

Thank you for your interest in contributing to VAITP-Auditor! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/vaitp-auditor.git
   cd vaitp-auditor
   ```
3. **Set up development environment**:
   ```bash
   python scripts/setup_dev.py
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```
5. **Make your changes** and add tests
6. **Run tests**:
   ```bash
   pytest
   ```
7. **Commit and push**:
   ```bash
   git commit -m "Add amazing feature"
   git push origin feature/amazing-feature
   ```
8. **Create a Pull Request** on GitHub

## 📋 Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep line length under 88 characters (Black formatter)

### Testing

- Write tests for new functionality
- Maintain test coverage above 80%
- Test on multiple platforms when possible
- Include both unit and integration tests

### Documentation

- Update documentation for new features
- Include examples in docstrings
- Update README.md if needed
- Add changelog entries

## 🏗️ Project Structure

```
vaitp-auditor/
├── vaitp_auditor/          # Main package
│   ├── cli/                # Command-line interface
│   ├── gui/                # GUI application
│   ├── core/               # Core functionality
│   └── utils/              # Utility functions
├── tests/                  # Test suite
├── docs/                   # Documentation
├── deployment/             # Deployment scripts
├── scripts/                # Development scripts
└── .github/                # GitHub workflows
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vaitp_auditor

# Run specific test file
pytest tests/test_gui_app.py

# Run GUI tests (requires display)
pytest tests/test_gui_*.py
```

### Test Categories

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **GUI Tests**: Test user interface functionality
- **Performance Tests**: Test performance characteristics

## 🚀 Deployment

### Building Executables

```bash
# Build for current platform
python deployment/build_executable.py

# Build with debug info
python deployment/build_executable.py --debug

# Clean build
python deployment/build_executable.py --clean
```

### Creating Releases

```bash
# Bump version and create release
python scripts/create_release.py patch  # or minor, major
```

## 📝 Pull Request Process

1. **Ensure tests pass** on your local machine
2. **Update documentation** as needed
3. **Add changelog entry** if applicable
4. **Create descriptive PR title** and description
5. **Link related issues** using keywords (fixes #123)
6. **Request review** from maintainers

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Changelog entry added (if needed)
- [ ] No merge conflicts
- [ ] PR description is clear and complete

## 🐛 Bug Reports

When reporting bugs, please include:

- **Platform and version** (Windows 10, macOS 12, Ubuntu 20.04, etc.)
- **Python version** and installation method
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Error messages** and stack traces
- **Screenshots** if applicable

## 💡 Feature Requests

For feature requests, please:

- **Check existing issues** to avoid duplicates
- **Describe the problem** you're trying to solve
- **Propose a solution** or approach
- **Consider implementation complexity**
- **Discuss with maintainers** before starting work

## 🏷️ Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements or additions to docs
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested

## 🔧 Development Environment

### Prerequisites

- Python 3.8 or higher
- Git
- Platform-specific GUI libraries (installed automatically)

### Optional Tools

- **Docker**: For containerized development
- **VS Code**: Recommended editor with Python extension
- **PyCharm**: Alternative IDE with good Python support

### Environment Variables

```bash
# Optional: Enable debug logging
export VAITP_DEBUG=1

# Optional: Custom config directory
export VAITP_CONFIG_DIR=/path/to/config
```

## 📞 Getting Help

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers for security issues

## 📄 License

By contributing to VAITP-Auditor, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors are recognized in:

- GitHub contributors list
- Release notes for significant contributions
- Special thanks in documentation

Thank you for contributing to VAITP-Auditor! 🎉
