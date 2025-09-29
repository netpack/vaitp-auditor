# VAITP-Auditor Setup Guide

## Quick Setup

### Prerequisites

- **Python 3.8 or higher**
- **Terminal/Command prompt access**
- **Git** (for development setup)

### Installation

1. **Install from source**:
   ```bash
   git clone <repository-url>
   cd vaitp-auditor
   pip install -e .[gui]
   ```

2. **Verify installation**:
   ```bash
   vaitp-auditor --help
   ```

3. **Start your first review**:
   ```bash
   vaitp-auditor
   ```

## Detailed Setup Instructions

### System Requirements

#### Minimum Requirements
- **OS**: Windows 10, macOS 10.14, or Linux (Ubuntu 18.04+)
- **Python**: 3.8+
- **RAM**: 4GB (8GB recommended for large datasets)
- **Storage**: 1GB free space (more for large code repositories)
- **Terminal**: Any terminal with color support

#### Recommended Requirements
- **OS**: Latest stable versions
- **Python**: 3.10+
- **RAM**: 8GB or more
- **Storage**: 5GB+ for extensive code reviews
- **Terminal**: Modern terminal with Unicode support

### Python Environment Setup

#### Option 1: System Python (Simple)

```bash
# Check Python version
python --version  # Should be 3.8+

# Install directly
pip install -e .[gui]
```

#### Option 2: Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv vaitp-auditor-env

# Activate virtual environment
# On Windows:
vaitp-auditor-env\Scripts\activate
# On macOS/Linux:
source vaitp-auditor-env/bin/activate

# Install package
pip install -e .[gui]
```

#### Option 3: Conda Environment

```bash
# Create conda environment
conda create -n vaitp-auditor python=3.10
conda activate vaitp-auditor

# Install package
pip install -e .[gui]
```

### Development Setup

#### For Contributors

```bash
# Clone repository
git clone <repository-url>
cd vaitp-auditor

# Create development environment
python -m venv dev-env
source dev-env/bin/activate  # On Windows: dev-env\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install

# Run tests to verify setup
pytest
```

#### Development Dependencies

The development setup includes additional tools:
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks

### Optional Dependencies

#### Performance Monitoring (Recommended)

```bash
pip install psutil
```

Benefits:
- Real-time memory usage monitoring
- Performance optimization triggers
- Resource usage statistics

#### Advanced Excel Features

```bash
pip install openpyxl[charts]
```

Benefits:
- Enhanced Excel report formatting
- Chart generation capabilities
- Advanced spreadsheet features

### Configuration

#### Default Configuration

The application works out-of-the-box with sensible defaults:
- **Session storage**: `~/.vaitp_auditor/sessions/`
- **Report output**: `./reports/`
- **Log files**: `~/.vaitp_auditor/logs/`

#### Custom Configuration (Optional)

Create configuration file at `~/.vaitp_auditor/config.yaml`:

```yaml
# Performance settings
performance:
  memory_limit_mb: 1000
  chunk_size: 100
  cache_size_mb: 100

# UI settings
ui:
  theme: "monokai"
  syntax_highlighting: true
  line_numbers: true

# Reporting settings
reporting:
  default_format: "excel"
  auto_backup: true
  compression: false

# Logging settings
logging:
  level: "INFO"
  file_logging: true
  console_logging: true
```

### Verification Steps

#### 1. Basic Functionality Test

```bash
# Test CLI access
vaitp-auditor --version

# Test help system
vaitp-auditor --help
```

#### 2. Create Test Data

```bash
# Create test directories
mkdir -p test_data/generated test_data/expected

# Create sample files
echo "def hello(): return 'world'" > test_data/generated/test1.py
echo "def hello(): return 'hello'" > test_data/expected/test1.py

echo "print('generated')" > test_data/generated/test2.py
echo "print('expected')" > test_data/expected/test2.py
```

#### 3. Run Test Review

```bash
# Start application
vaitp-auditor

# Follow prompts:
# - Experiment name: "setup_test"
# - Data source: "1" (Folders)
# - Generated folder: "test_data/generated"
# - Expected folder: "test_data/expected"
# - Sampling: "100"

# Review a few items, then quit with 'q'
# Check that report was generated in reports/ directory
```

#### 4. Run Test Suite (Development)

```bash
# Run basic tests
pytest tests/test_models.py -v

# Run performance tests
pytest tests/test_performance.py -v

# Run cross-platform tests
pytest tests/test_cross_platform.py -v
```

### Troubleshooting Setup Issues

#### Common Installation Problems

**Problem**: `pip install` fails with permission errors
```bash
# Solution 1: Use user installation
pip install --user -e .[gui]

# Solution 2: Use virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install -e .[gui]
```

**Problem**: Python version too old
```bash
# Check version
python --version

# Install newer Python (varies by OS)
# Ubuntu/Debian:
sudo apt update && sudo apt install python3.10

# macOS with Homebrew:
brew install python@3.10

# Windows: Download from python.org
```

**Problem**: Missing system dependencies
```bash
# Ubuntu/Debian:
sudo apt install python3-dev python3-pip

# CentOS/RHEL:
sudo yum install python3-devel python3-pip

# macOS:
xcode-select --install
```

#### Runtime Issues

**Problem**: "Command not found: vaitp-auditor"
```bash
# Solution 1: Check PATH
echo $PATH
# Ensure pip install location is in PATH

# Solution 2: Run directly
python -m vaitp_auditor

# Solution 3: Reinstall in virtual environment
```

**Problem**: Import errors
```bash
# Check installation
pip list | grep vaitp

# Reinstall if needed
pip uninstall vaitp-auditor
pip install -e .[gui]
```

**Problem**: Permission denied for session directory
```bash
# Check permissions
ls -la ~/.vaitp_auditor/

# Fix permissions if needed
chmod 755 ~/.vaitp_auditor/
chmod 755 ~/.vaitp_auditor/sessions/
```

#### Performance Issues

**Problem**: Slow startup or operation
```bash
# Install performance dependencies
pip install psutil

# Check system resources
# Ensure sufficient RAM and disk space

# Try with smaller dataset first
```

**Problem**: Memory errors with large files
```bash
# Reduce chunk size in config
# Use sampling for initial testing
# Close other applications
```

### Platform-Specific Notes

#### Windows

- **Terminal**: Use Windows Terminal or PowerShell for best experience
- **Paths**: Use forward slashes or raw strings for paths
- **Encoding**: System should handle UTF-8 automatically
- **Performance**: May be slower than Unix systems for large datasets

#### macOS

- **Terminal**: Built-in Terminal.app works well
- **Python**: Use Homebrew Python for best compatibility
- **Permissions**: May need to grant terminal access to folders
- **Performance**: Generally excellent performance

#### Linux

- **Terminal**: Any modern terminal works
- **Python**: Use system package manager for Python
- **Permissions**: Standard Unix permissions apply
- **Performance**: Typically best performance

### Docker Setup (Advanced)

#### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . .

# Install application
RUN pip install -e .[gui]

# Create data directories
RUN mkdir -p /data/input /data/output

# Set entrypoint
ENTRYPOINT ["vaitp-auditor"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  vaitp-auditor:
    build: .
    volumes:
      - ./data:/data
      - ./reports:/app/reports
    stdin_open: true
    tty: true
```

#### Usage

```bash
# Build image
docker build -t vaitp-auditor .

# Run interactively
docker run -it -v $(pwd)/data:/data vaitp-auditor

# Or with docker-compose
docker-compose run vaitp-auditor
```

### Cloud Setup (Advanced)

#### AWS EC2

```bash
# Launch EC2 instance (Ubuntu 20.04 LTS)
# Connect via SSH

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and Git
sudo apt install python3.10 python3.10-venv git -y

# Clone and setup
git clone <repository-url>
cd vaitp-auditor
python3.10 -m venv venv
source venv/bin/activate
pip install -e .[gui]

# Transfer data files (use scp, rsync, or S3)
# Run reviews in screen/tmux for long sessions
```

#### Google Cloud Platform

```bash
# Create Compute Engine instance
# SSH into instance

# Similar setup to AWS
# Use gsutil for data transfer
# Consider using Cloud Storage for large datasets
```

### Next Steps

After successful setup:

1. **Read the User Guide**: `docs/USER_GUIDE.md`
2. **Try a small test**: Use sample data to familiarize yourself
3. **Plan your experiment**: Define clear objectives and methodology
4. **Prepare your data**: Organize code files or databases
5. **Start reviewing**: Begin with a small sample to test workflow

### Getting Help

If you encounter issues:

1. **Check logs**: Look in `~/.vaitp_auditor/logs/`
2. **Run diagnostics**: Use `vaitp-auditor --debug`
3. **Test with minimal data**: Isolate the problem
4. **Check documentation**: Review relevant guide sections
5. **Report issues**: Create detailed bug reports with logs

### Maintenance

#### Regular Updates

```bash
# Update from repository
git pull origin main
pip install -e .[gui]

# Update dependencies
pip install --upgrade -r requirements.txt
```

#### Cleanup

```bash
# Clean old session files (automatic after 30 days)
# Manual cleanup if needed:
rm -rf ~/.vaitp_auditor/sessions/*.pkl

# Clean old logs
find ~/.vaitp_auditor/logs/ -name "*.log" -mtime +30 -delete

# Clean temporary files
rm -rf reports/temp/
```

This setup guide should get you up and running with the VAITP-Auditor system. The application is designed to be easy to install and configure while providing the flexibility needed for various research and development workflows.
