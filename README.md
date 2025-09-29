# 🔍 VAITP-Auditor

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Cross-Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](#-system-requirements)

> **A powerful Python-based Manual Code Verification Assistant for efficient and accurate review of programmatically generated code snippets.**

Transform your code review workflow with both modern GUI and interactive terminal interfaces that make comparing generated code against expected results fast, intuitive, and comprehensive.

**Current Version**: 0.1.0 (Alpha) - Active development with regular updates

---


## 🚀 Installation

### Prerequisites

- **Python 3.8+** 🐍 (Python 3.10+ recommended)
- **Git** for cloning the repository

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/netpack/vaitp-auditor.git
cd vaitp-auditor

# Create and activate a Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with GUI support
pip install -e ".[gui]"

# Run the application
vaitp-auditor
```

### 🎯 First Run

**GUI Mode (Default)**
```bash
# Launch the modern desktop interface (default if GUI dependencies available)
vaitp-auditor
# Or explicitly request GUI mode
vaitp-auditor --gui
```

**Terminal Mode**
```bash
# Start terminal-based review session
vaitp-auditor --cli
```

Follow the interactive setup wizard:

1. **Enter experiment name**: `my_first_review`
2. **Select data source**: Choose from folders, SQLite, or Excel/CSV
3. **Configure paths**: Point to your generated and expected code
4. **Set sampling**: Choose percentage of data to review (1-100%)
5. **Start reviewing**: Use intuitive interface to classify code pairs

---

## 💡 How to Use

### 🗂️ Data Sources

**📁 Folder-based Review** (Most Common)

```bash
vaitp-auditor
# Select option 1: Folders
# Generated code: /path/to/generated/
# Expected code: /path/to/expected/
```

**🗄️ Database Review**

```bash
# SQLite database with code_pairs table
# Columns: id, generated_code, expected_code
```

**📊 Excel/CSV Review**

```bash
# Spreadsheet with columns:
# ID | Generated Code | Expected Code
```

### ⌨️ Review Interface

**Navigation (CLI Mode)**

- `↑↓←→` or `hjkl` - Scroll through code
- `Tab` - Switch between panels
- `Page Up/Down` - Navigate faster

**Classification** (Single keypress!)

- `s` - **Success** ✅ (Code works correctly)
- `f` - **Failure** ❌ (Code doesn't work)
- `i` - **Invalid** 🚫 (Syntax errors)
- `w` - **Wrong** ⚠️ (Wrong vulnerability type)
- `p` - **Partial** 🔶 (Partially correct)
- `u` - **Undo** ↩️ (Go back one step)
- `q` - **Quit** 🚪 (Save and exit)

**GUI Mode Features**

- Point-and-click interface with keyboard shortcuts
- Side-by-side code comparison with syntax highlighting
- Progress tracking and session management
- Accessibility features and customizable themes

### 📊 Example Session

```
┌─ Expected Code ─────────────────┐ ┌─ Generated Code ────────────────┐
│ def vulnerable_function():      │ │ def vulnerable_function():      │
│     user_input = input()        │ │     user_input = input()        │
│     eval(user_input)  # BAD!    │ │     # Fixed: validate input     │
│                                 │ │     if user_input.isalnum():    │
│                                 │ │         eval(user_input)        │
└─────────────────────────────────┘ └─────────────────────────────────┘

Review 1/100 (1.0%) - ID: test_001.py
Classification: [s]uccess [f]ailure [i]nvalid [w]rong [p]artial [u]ndo [q]uit
```

---

## ✨ Key Features

### 🖥️ **Modern Desktop GUI**

- **Setup Wizard**: Intuitive 5-step configuration process
- **Side-by-Side Code Comparison**: Syntax highlighting with diff visualization
- **Responsive Interface**: Smooth scrolling, keyboard shortcuts, and accessibility support
- **Performance Optimized**: Lazy loading for large files, intelligent caching
- **Accessibility Features**: Screen reader support, high contrast themes, keyboard navigation

### 🎨 **Rich Terminal Interface**

- Side-by-side code comparison with syntax highlighting
- Smooth scrolling and navigation
- Progress tracking and session management

### 🔄 **Multiple Data Sources**

- **File System**: Compare folders of code files
- **SQLite**: Review code stored in databases
- **Excel/CSV**: Process spreadsheet data

### 💾 **Smart Session Management**

- Auto-save progress after each review
- Resume interrupted sessions seamlessly
- 30-day automatic cleanup of old sessions

### 📈 **Comprehensive Reporting**

- Excel reports with rich formatting and metadata
- CSV exports for further analysis
- Detailed timing and diff information

### ⚡ **Performance Optimized**

- Lazy loading for large files (>100KB)
- Intelligent caching and memory management
- Chunked processing for massive datasets
- Real-time performance monitoring

---

## 📋 System Requirements

| Component   | Minimum     | Recommended |
| ----------- | ----------- | ----------- |
| **Python**  | 3.8         | 3.10+       |
| **RAM**     | 4GB         | 8GB+        |
| **Storage** | 1GB         | 5GB+        |

---

## 🧪 Testing & Validation

```bash
# Run the full test suite
pytest

# Performance benchmarks
pytest tests/test_performance.py -v

# Cross-platform compatibility
pytest tests/test_cross_platform.py -v

# Comprehensive validation
pytest tests/test_comprehensive_validation.py -v
```

**Test Coverage**: Comprehensive test suite covering all components with performance benchmarks and cross-platform validation.

---

## 🧹 Maintenance & Cleanup

### Session Management

VAITP-Auditor automatically manages session files, but you can manually clean up when needed:

```bash
# View session files
ls -la ~/.vaitp_auditor/sessions/

# Remove sessions older than 7 days (automatic cleanup is 30 days)
find ~/.vaitp_auditor/sessions/ -name "*.pkl" -mtime +7 -delete

# Remove all session files (⚠️ careful!)
rm ~/.vaitp_auditor/sessions/*.pkl
```

### Complete Reset

```bash
# Remove all application data (sessions, logs, config)
rm -rf ~/.vaitp_auditor/

# Reports are stored separately in ./reports/ and won't be affected
```

### File Locations

| Type         | Location                          | Description               |
| ------------ | --------------------------------- | ------------------------- |
| **Sessions** | `~/.vaitp_auditor/sessions/*.pkl` | Review progress and state |
| **Logs**     | `~/.vaitp_auditor/logs/*.log`     | Application logs          |
| **Reports**  | `./reports/*.xlsx`                | Generated review reports  |
| **Config**   | `~/.vaitp_auditor/config.yaml`    | Optional configuration    |

### Automatic Cleanup

- **Sessions**: Auto-deleted after 30 days
- **Logs**: Rotated automatically
- **Reports**: Never auto-deleted (your data!)

---

## 📚 Documentation

| Guide                                              | Description                                |
| -------------------------------------------------- | ------------------------------------------ |
| 🖥️ [GUI User Guide](docs/GUI_USER_GUIDE.md)        | Complete GUI interface documentation       |
| 👩‍💻 [GUI Developer Guide](docs/GUI_DEVELOPER_GUIDE.md) | GUI development and extension guide        |
| 📖 [CLI User Guide](docs/USER_GUIDE.md)           | Terminal interface documentation           |
| 🔧 [Setup Guide](docs/SETUP_GUIDE.md)             | Detailed installation and configuration    |
| 🏗️ [Developer Guide](docs/DEVELOPER_GUIDE.md)      | Architecture and contribution guidelines   |

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   UI Components │    │   Processing    │
│                 │    │                 │    │                 │
│ • File System   │───▶│ • Terminal UI   │───▶│ • Diff Engine   │
│ • SQLite DB     │    │ • Syntax Highl. │    │ • Classification│
│ • Excel/CSV     │    │ • Navigation    │    │ • Validation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Session Manager │    │ Report Generator│    │ Performance     │
│                 │    │                 │    │                 │
│ • Auto-save     │    │ • Excel Export  │    │ • Memory Mgmt   │
│ • Resume        │    │ • CSV Export    │    │ • Caching       │
│ • Recovery      │    │ • Metadata      │    │ • Optimization  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🎯 Performance Targets

| Metric             | Target              | Achieved      |
| ------------------ | ------------------- | ------------- |
| **Code Display**   | < 100ms             | ✅ ~50ms      |
| **Syntax Highlighting** | < 50ms        | ✅ ~20ms      |
| **Diff Computation** | < 100ms           | ✅ ~50ms      |
| **Memory Usage**   | < 1GB for 10K pairs | ✅ ~500MB     |
| **Session Start**  | < 5 seconds         | ✅ ~2 seconds |
| **Navigation Speed** | < 500ms for 50 items | ✅ ~200ms   |

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Quick Start

1. **Fork** the repository on GitHub
2. **Clone** your fork: `git clone https://github.com/yourusername/vaitp-auditor.git`
3. **Create** a feature branch: `git checkout -b feature/amazing-feature`
4. **Install** development dependencies: `pip install -e .[dev]`
5. **Make** your changes and add tests
6. **Run** tests: `pytest`
7. **Commit** your changes: `git commit -m 'Add amazing feature'`
8. **Push** to the branch: `git push origin feature/amazing-feature`
9. **Open** a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass before submitting
- Write clear, descriptive commit messages

### Code Quality

```bash
# Run tests
pytest

# Check code style
black --check .
flake8 .

# Type checking
mypy vaitp_auditor/
```

See our [Developer Guide](docs/DEVELOPER_GUIDE.md) for detailed contribution guidelines and architecture information.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### License Summary

- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ❌ Liability
- ❌ Warranty

The MIT License is a permissive license that allows you to use this software for any purpose, including commercial applications, as long as you include the original copyright notice.

---

## 🌟 Why VAITP-Auditor?

- **🚀 Fast**: Optimized for large-scale code review workflows
- **🎯 Accurate**: Structured classification with detailed reporting
- **💪 Robust**: Cross-platform with comprehensive error handling
- **🔧 Flexible**: Multiple data sources and export formats
- **📊 Insightful**: Rich metadata and performance analytics

**Ready to revolutionize your manual code review process?** Get started in under 2 minutes! 🚀

---

## 🚧 Development Status

VAITP-Auditor is currently in **active development** (v0.1.0 Alpha). The core functionality is stable and ready for use, with ongoing improvements to the GUI interface, performance optimizations, and deployment capabilities.

### Recent Updates
- ✅ Modern GUI interface with accessibility features
- ✅ Enhanced performance optimization and caching
- ✅ Comprehensive test suite with >80% coverage
- ✅ Simplified installation process

### Upcoming Features
- 🔄 Enhanced reporting and analytics
- 🎨 Additional GUI themes and customization
- 📊 Advanced performance metrics and monitoring

---

## 📞 Support & Community

- 📖 **Documentation**: Comprehensive guides in the [docs/](docs/) directory
- 🐛 **Issues**: Report bugs and request features via GitHub Issues
- 💬 **Discussions**: Join community discussions for questions and ideas
- 📧 **Contact**: Reach out to the VAITP Research Team for collaboration

---
