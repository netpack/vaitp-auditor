# VAITP-Auditor GUI User Guide

## Overview

The VAITP-Auditor GUI provides a modern desktop interface for manual code review and vulnerability assessment. This graphical interface replaces the terminal-based workflow with an intuitive visual experience while maintaining all the powerful features of the original tool.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Setup Wizard](#setup-wizard)
3. [Main Review Window](#main-review-window)
4. [Keyboard Shortcuts](#keyboard-shortcuts)
5. [Data Sources](#data-sources)
6. [Review Workflow](#review-workflow)
7. [Accessibility Features](#accessibility-features)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Display**: 1280x720 minimum resolution, 1920x1080 recommended

### Installation

1. **Install Python Dependencies**:
   ```bash
   pip install vaitp-auditor[gui]
   ```

2. **Launch the GUI**:
   ```bash
   vaitp-auditor-gui
   ```
   
   Or use the default mode:
   ```bash
   vaitp-auditor
   ```

### First Launch

When you first launch the VAITP-Auditor GUI, you'll see the Setup Wizard that guides you through configuring your first review session.

## Setup Wizard

The Setup Wizard is a 4-step process that helps you configure your review session:

### Step 1: Name Your Review Session

![Setup Wizard Step 1](screenshots/setup_step1.png)

- **Experiment Name**: Enter a descriptive name for your review session
- **Session ID Preview**: See how your session ID will be formatted with timestamp
- **Example**: "VulnAssessment_2024-03-15_14-30-00"

**Tips**:
- Use descriptive names that help you identify the session later
- Avoid special characters that might cause file system issues
- The timestamp is automatically added to ensure uniqueness

### Step 2: Select Data Source

![Setup Wizard Step 2](screenshots/setup_step2.png)

Choose from three data source types:

1. **Folders**: Compare files from two directory structures
2. **SQLite Database**: Load code pairs from a database
3. **Excel/CSV Files**: Import code pairs from spreadsheet files

**Choosing the Right Data Source**:
- **Folders**: Best for comparing generated code against reference implementations
- **SQLite**: Ideal for large datasets with structured metadata
- **Excel/CSV**: Perfect for smaller datasets or when working with spreadsheet-based workflows

### Step 3: Configure Data Source

The configuration options change based on your Step 2 selection:

#### Folder Configuration

![Folder Configuration](screenshots/setup_folders.png)

- **Generated Code Folder**: Required. Contains the AI-generated code to review
- **Expected Code Folder**: Optional. Contains reference implementations for comparison
- **Browse Buttons**: Click to open native folder selection dialogs
- **Path Validation**: Paths are validated in real-time

#### SQLite Configuration

![SQLite Configuration](screenshots/setup_sqlite.png)

- **Database File**: Select your SQLite database file
- **Table Selection**: Choose the table containing your code pairs
- **Column Mapping**: Map database columns to:
  - Identifier Column (unique ID for each code pair)
  - Generated Code Column
  - Expected Code Column (optional)

#### Excel/CSV Configuration

![Excel Configuration](screenshots/setup_excel.png)

- **File Selection**: Choose your Excel (.xlsx) or CSV file
- **Sheet Selection**: For Excel files, select the appropriate worksheet
- **Column Mapping**: Map spreadsheet columns to code pair fields
- **Preview**: See a preview of your data before proceeding

### Step 4: Finalize Settings

![Setup Wizard Step 4](screenshots/setup_finalize.png)

- **Sampling Percentage**: Choose what percentage of your dataset to review (1-100%)
- **Output Format**: Select Excel (.xlsx) or CSV for your review results
- **Configuration Summary**: Review all your settings before starting
- **Start Review**: Launch the main review interface

**Sampling Guidelines**:
- **100%**: Review all code pairs (recommended for small datasets)
- **50%**: Good balance for medium datasets
- **10-25%**: Suitable for large datasets or initial assessments

## Main Review Window

The Main Review Window is where you perform the actual code review:

![Main Review Window](screenshots/main_window.png)

### Window Layout

The interface is organized into three main sections:

#### 1. Header Section
- **Current File**: Shows the identifier of the code pair being reviewed
- **Progress Bar**: Visual progress indicator
- **Progress Text**: Numerical progress (e.g., "15/100 (15.0%)")

#### 2. Code Comparison Section
- **Expected Code Panel** (left): Reference implementation or expected output
- **Generated Code Panel** (right): AI-generated code to review
- **Syntax Highlighting**: Automatic Python syntax highlighting
- **Diff Highlighting**: Visual differences between expected and generated code
  - 🟢 **Green**: Lines added in generated code
  - 🔴 **Red**: Lines removed from expected code
  - 🟡 **Yellow**: Lines modified between versions

#### 3. Actions Section
- **Verdict Buttons**: Six classification options for code quality
- **Comment Field**: Optional text field for additional notes
- **Control Buttons**: Undo and Quit functionality

### Verdict Options

Choose the most appropriate classification for each code pair:

| Verdict | Description | When to Use |
|---------|-------------|-------------|
| **Success** | Code works correctly and addresses the vulnerability | Generated code properly fixes the issue |
| **Failure - No Change** | Code doesn't address the vulnerability | No meaningful changes were made |
| **Invalid Code** | Code has syntax errors or won't run | Compilation/runtime errors present |
| **Wrong Vulnerability** | Code addresses a different vulnerability | Misunderstood the target vulnerability |
| **Partial Success** | Code partially addresses the issue | Some progress but incomplete solution |
| **Custom** | Other classification | Use comment field to explain |

### Code Panel Features

#### Syntax Highlighting
- **Automatic Detection**: Python syntax is highlighted automatically
- **Color Coding**: Keywords, strings, comments, and functions are color-coded
- **Fallback**: Plain text display if highlighting fails

#### Diff Visualization
- **Side-by-Side Comparison**: Expected vs. Generated code
- **Line-by-Line Highlighting**: Visual indicators for changes
- **Synchronized Scrolling**: Both panels scroll together for easy comparison

#### Navigation
- **Mouse Scrolling**: Use mouse wheel for vertical scrolling
- **Keyboard Navigation**: Arrow keys, Page Up/Down, Home/End
- **Zoom**: Ctrl+Plus/Minus to adjust font size (if supported)

## Keyboard Shortcuts

### Verdict Selection
- **1**: Success
- **2**: Failure - No Change  
- **3**: Invalid Code
- **4**: Wrong Vulnerability
- **5**: Partial Success
- **6**: Custom

### Navigation
- **Tab**: Move between interface elements
- **Enter**: Submit verdict (when comment field is focused)
- **Escape**: Clear comment field

### Session Control
- **U**: Undo last verdict
- **Q**: Quit session (with confirmation)

### Code Panel Navigation
- **↑/↓**: Scroll up/down
- **Page Up/Down**: Scroll by page
- **Home/End**: Go to beginning/end of line
- **Ctrl+Home/End**: Go to beginning/end of document

## Data Sources

### Folder Structure Requirements

When using folder-based data sources, organize your files as follows:

```
project/
├── generated/          # Generated code folder
│   ├── file1.py
│   ├── file2.py
│   └── subdirectory/
│       └── file3.py
└── expected/           # Expected code folder (optional)
    ├── file1.py
    ├── file2.py
    └── subdirectory/
        └── file3.py
```

**Important Notes**:
- File names must match between generated and expected folders
- Subdirectory structure should be identical
- Only Python files (.py) are currently supported for syntax highlighting

### Database Schema

For SQLite data sources, your table should have this structure:

```sql
CREATE TABLE code_pairs (
    id TEXT PRIMARY KEY,
    generated_code TEXT NOT NULL,
    expected_code TEXT,
    metadata TEXT
);
```

**Column Requirements**:
- **ID Column**: Unique identifier for each code pair
- **Generated Code**: The AI-generated code to review (required)
- **Expected Code**: Reference implementation (optional)
- **Additional Columns**: Any extra metadata columns are preserved

### Excel/CSV Format

Spreadsheet files should have these columns:

| Column A | Column B | Column C | Column D |
|----------|----------|----------|----------|
| ID | Generated Code | Expected Code | Notes |
| pair_001 | def hello():... | def hello():... | Test case 1 |
| pair_002 | class MyClass:... | class MyClass:... | Test case 2 |

**Format Guidelines**:
- **Header Row**: First row should contain column names
- **Text Encoding**: Use UTF-8 encoding for special characters
- **Line Breaks**: Use proper line breaks (\n) in code cells
- **File Size**: Keep files under 100MB for optimal performance

## Review Workflow

### Starting a Review Session

1. **Launch Application**: Start VAITP-Auditor GUI
2. **Complete Setup Wizard**: Configure your data source and settings
3. **Begin Review**: Click "Start Review" to open the Main Review Window

### Reviewing Code Pairs

For each code pair:

1. **Examine the Code**: 
   - Read the expected code (if available) in the left panel
   - Review the generated code in the right panel
   - Look for differences highlighted in color

2. **Assess Quality**:
   - Does the generated code compile/run?
   - Does it address the intended vulnerability?
   - Are there any security issues introduced?
   - Is the code style and structure appropriate?

3. **Select Verdict**:
   - Click the appropriate verdict button
   - Add comments if needed for clarification
   - The system automatically moves to the next code pair

4. **Use Undo if Needed**:
   - Click "Undo Last" to revert the previous decision
   - Useful for correcting mistakes or reconsidering verdicts

### Session Management

#### Saving Progress
- **Automatic Saving**: Progress is saved after each verdict
- **Resume Capability**: Interrupted sessions can be resumed
- **Export Results**: Final results are saved in your chosen format

#### Completing a Session
- **Review All Pairs**: Continue until all code pairs are reviewed
- **Final Report**: System generates a comprehensive report
- **Session Summary**: View statistics and completion details

## Accessibility Features

The VAITP-Auditor GUI includes comprehensive accessibility support:

### Keyboard Navigation
- **Full Keyboard Access**: All functions accessible via keyboard
- **Tab Order**: Logical tab sequence through interface elements
- **Focus Indicators**: Clear visual focus indicators

### Screen Reader Support
- **ARIA Labels**: Proper labeling for all interactive elements
- **Descriptive Text**: Detailed descriptions for complex UI components
- **Progress Announcements**: Screen readers announce progress updates

### Visual Accessibility
- **High Contrast Mode**: Enhanced contrast for better visibility
- **Font Scaling**: Adjustable font sizes for better readability
- **Color Blind Support**: Diff highlighting uses patterns in addition to colors

### Customization Options
- **Theme Selection**: Choose from multiple visual themes
- **Font Preferences**: Customize font family and size
- **Layout Options**: Adjust panel sizes and arrangements

## Troubleshooting

### Common Issues

#### Setup Wizard Problems

**Issue**: "Cannot browse for folders"
- **Solution**: Ensure you have proper file system permissions
- **Alternative**: Type folder paths manually in the text fields

**Issue**: "Database connection failed"
- **Solution**: 
  - Verify the SQLite file is not corrupted
  - Check file permissions
  - Ensure the file is not locked by another application

**Issue**: "Excel file cannot be parsed"
- **Solution**:
  - Verify the file is a valid Excel (.xlsx) or CSV format
  - Check for special characters in column headers
  - Ensure the file is not password-protected

#### Main Review Window Issues

**Issue**: "Code panels are blank"
- **Solution**:
  - Check that your data source contains valid code content
  - Verify file encoding (should be UTF-8)
  - Try refreshing by using Undo then proceeding again

**Issue**: "Syntax highlighting not working"
- **Solution**:
  - This is normal for non-Python files
  - Code will display in plain text
  - Functionality is not affected

**Issue**: "Application is slow or unresponsive"
- **Solution**:
  - Close other applications to free memory
  - Use sampling to review smaller subsets
  - Check available disk space for temporary files

#### Performance Issues

**Issue**: "Large files take too long to load"
- **Solution**: The system automatically uses lazy loading for large files
- **Expected Behavior**: Large files show a preview with line count indicator

**Issue**: "Memory usage is high"
- **Solution**: The system includes automatic memory management
- **Manual Cleanup**: Restart the application if memory issues persist

### Error Messages

#### "Session configuration invalid"
- **Cause**: Missing required configuration parameters
- **Solution**: Return to Setup Wizard and verify all required fields

#### "Cannot save results"
- **Cause**: Insufficient disk space or permission issues
- **Solution**: 
  - Check available disk space
  - Verify write permissions to output directory
  - Choose a different output location

#### "Data source connection lost"
- **Cause**: File moved, deleted, or network issues (for remote files)
- **Solution**:
  - Verify source files still exist
  - Check network connectivity for remote sources
  - Restart the session with updated file paths

### Getting Help

#### Log Files
- **Location**: `~/.vaitp-auditor/logs/`
- **Contents**: Detailed error messages and performance metrics
- **Usage**: Include relevant log excerpts when reporting issues

#### Performance Monitoring
- **Built-in Metrics**: The application tracks performance automatically
- **Memory Usage**: Monitor via system task manager
- **Response Times**: Logged for optimization purposes

#### Support Resources
- **Documentation**: Complete API and developer documentation
- **Issue Tracker**: Report bugs and feature requests
- **Community**: User forums and discussion groups

### Advanced Configuration

#### Configuration Files
- **Location**: `~/.vaitp-auditor/config/`
- **GUI Settings**: Customize appearance and behavior
- **Performance Tuning**: Adjust memory limits and cache sizes

#### Custom Themes
- **Theme Files**: JSON-based theme configuration
- **Color Schemes**: Customize syntax highlighting colors
- **Layout Options**: Adjust panel proportions and spacing

## Best Practices

### Efficient Reviewing
1. **Consistent Criteria**: Establish clear criteria for each verdict type
2. **Use Comments**: Add comments for borderline cases or complex issues
3. **Take Breaks**: Regular breaks improve accuracy and reduce fatigue
4. **Review Patterns**: Look for common patterns in generated code quality

### Data Management
1. **Backup Results**: Regularly backup your review results
2. **Version Control**: Track changes to your datasets
3. **Documentation**: Document your review criteria and methodology
4. **Quality Assurance**: Periodically review your own verdicts for consistency

### Performance Optimization
1. **Sampling Strategy**: Use appropriate sampling percentages for your dataset size
2. **System Resources**: Ensure adequate RAM and disk space
3. **File Organization**: Keep source files organized and accessible
4. **Regular Cleanup**: Remove old session files and temporary data

---

*This user guide covers the essential features and workflows of the VAITP-Auditor GUI. For technical details and API documentation, see the Developer Guide.*