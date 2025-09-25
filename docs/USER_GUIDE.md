# VAITP-Auditor User Guide

## Overview

The VAITP-Auditor is a Python-based Manual Code Verification Assistant designed to facilitate efficient and accurate manual verification of programmatically generated code snippets. The tool enables human reviewers to compare "expected" (ground-truth vulnerable) code files against "generated" (LLM-produced) code files and classify the results.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Data Sources](#data-sources)
4. [Review Interface](#review-interface)
5. [Classification Options](#classification-options)
6. [Session Management](#session-management)
7. [Reports and Output](#reports-and-output)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)
10. [Performance Tips](#performance-tips)

## Installation

### Prerequisites

- Python 3.8 or higher
- Terminal/Command prompt access
- Sufficient disk space for code files and reports

### Install from Source

1. Clone or download the VAITP-Auditor repository
2. Navigate to the project directory
3. Install the package:

```bash
pip install -e .
```

### Verify Installation

```bash
vaitp-auditor --help
```

You should see the help message with available commands.

## Quick Start

### Basic Workflow

1. **Start the application**:
   ```bash
   vaitp-auditor
   ```

2. **Choose data source**: Select from Folders, SQLite database, or Excel file

3. **Configure experiment**: Provide experiment name and data source details

4. **Review code pairs**: Use the interactive interface to classify each code pair

5. **Complete session**: Review results are automatically saved to Excel/CSV reports

### Example: Folder-based Review

```bash
vaitp-auditor
```

Follow the prompts:
- Enter experiment name: `my_code_review_2024`
- Select data source: `1` (Folders)
- Generated code folder: `/path/to/generated/code`
- Expected code folder: `/path/to/expected/code` (optional)
- Sampling percentage: `100` (review all files)

## Data Sources

### 1. Folder-based (File System)

**Use case**: Code files stored in directories

**Setup**:
- Generated Code folder: Contains LLM-generated code files (required)
- Expected Code folder: Contains ground-truth code files (optional)

**File matching**: Files are matched by base name (ignoring extensions)
- `generated/test.py` matches with `expected/test.txt`
- `generated/subfolder/example.py` matches with `expected/subfolder/example.c`

**Supported file types**: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.h`, `.cs`, `.php`, `.rb`, `.go`, `.rs`, `.swift`, `.kt`, `.scala`, `.sql`, `.html`, `.css`, `.xml`, `.json`, `.yaml`, `.md`, `.txt`

### 2. SQLite Database

**Use case**: Code stored in database tables

**Setup**:
- Database file path
- Table selection
- Column mapping:
  - Generated Code column (required)
  - Expected Code column (optional)
  - Identifier column (required for traceability)

**Example schema**:
```sql
CREATE TABLE code_pairs (
    id INTEGER PRIMARY KEY,
    identifier TEXT,
    generated_code TEXT,
    expected_code TEXT
);
```

### 3. Excel/CSV Files

**Use case**: Code stored in spreadsheet format

**Setup**:
- Excel file path (.xlsx or .csv)
- Sheet selection (for Excel files)
- Column mapping:
  - Generated Code column (required)
  - Expected Code column (optional)
  - Identifier column (required for traceability)

**Example format**:
| ID | Generated Code | Expected Code |
|----|----------------|---------------|
| 1  | def func(): pass | def func(): return True |
| 2  | print("hello") | print("world") |

## Review Interface

### Two-Panel Display

The interface shows code side-by-side:
- **Left panel**: Expected Code (ground truth)
- **Right panel**: Generated Code (to be reviewed)

### Navigation

- **Arrow keys** or **hjkl**: Scroll within panels
- **Page Up/Down**: Page through content
- **Tab**: Switch between left and right panels
- **Active panel**: Highlighted with brighter border

### Progress Information

- Current review number and total count
- Percentage complete
- Source identifier for current code pair
- Active panel indicator

## Classification Options

### Verdict Categories

| Key | Verdict | Description |
|-----|---------|-------------|
| `s` | **Success** | Generated code correctly implements the expected functionality |
| `f` | **Failure - No Change** | Generated code fails to implement expected changes |
| `i` | **Invalid Code** | Generated code contains syntax errors or is malformed |
| `w` | **Wrong Vulnerability** | Generated code implements wrong type of vulnerability |
| `p` | **Partial Success** | Generated code partially implements expected functionality |
| `u` | **Undo** | Revert the last classification and return to previous code pair |
| `q` | **Quit** | Save progress and exit the session |

### Adding Comments

After selecting a verdict, you can optionally add a comment:
- Press Enter to skip comment
- Type your comment and press Enter to save

**Comment examples**:
- "Missing error handling in line 15"
- "Correct implementation but inefficient approach"
- "Syntax error on line 3: missing closing parenthesis"

## Session Management

### Automatic Saving

- Progress is saved after each review
- Session state includes completed reviews and remaining queue
- Safe to interrupt and resume sessions

### Session Resumption

When starting the application, you'll be prompted to resume existing sessions:

```
Found existing review sessions:
1. Code Review Experiment
   Session ID: experiment_20241201_143022_a1b2c3d4
   Progress: 15/100 reviews completed (15.0%)
   Created: 2024-12-01 14:30:22

2. Start a new session

Select an option (1-2):
```

### Session Files

- Stored in `~/.vaitp_auditor/sessions/`
- Automatically cleaned up after 30 days
- Can be manually deleted if corrupted

## Reports and Output

### Report Formats

- **Excel (.xlsx)**: Rich formatting, multiple sheets, recommended for analysis
- **CSV (.csv)**: Plain text, compatible with all tools

### Report Columns

| Column | Description |
|--------|-------------|
| review_id | Unique identifier for each review |
| source_identifier | Original identifier from data source |
| experiment_name | Name of the experiment session |
| review_timestamp_utc | When the review was completed (UTC) |
| reviewer_verdict | Classification result |
| reviewer_comment | Optional reviewer comment |
| time_to_review_seconds | Time spent on this review |
| expected_code | Full expected code content |
| generated_code | Full generated code content |
| code_diff | Unified diff between expected and generated |

### Report Location

Reports are saved in the `reports/` directory with naming pattern:
- `{experiment_name}_{timestamp}_{session_id}.xlsx`
- Example: `my_experiment_20241201_143022_a1b2c3d4.xlsx`

## Advanced Features

### Sampling

Review a subset of your data:
- Specify percentage (1-100%)
- Random sampling ensures representative coverage
- Useful for large datasets or pilot studies

### Undo Functionality

- Press `u` to undo the last classification
- Returns previous code pair to the review queue
- Removes last entry from the report
- Can be used multiple times in sequence

### Large File Handling

The system automatically optimizes for large files:
- **Lazy loading**: Large files loaded only when needed
- **Chunked processing**: Memory-efficient handling of large datasets
- **Syntax highlighting optimization**: Simplified rendering for very large files
- **Diff summarization**: Summary diffs for files over 100KB

### Performance Monitoring

Built-in performance monitoring tracks:
- Memory usage during operations
- Processing time for each component
- Cache hit rates for optimizations
- Automatic garbage collection when needed

## Troubleshooting

### Common Issues

#### "No code pairs found"
- **Cause**: Empty folders or no matching files
- **Solution**: Verify folder paths and ensure files exist
- **Check**: File extensions are supported

#### "Cannot read file" warnings
- **Cause**: Encoding issues or file permissions
- **Solution**: System automatically tries UTF-8 then latin-1 encoding
- **Note**: Warnings are logged but don't stop the process

#### "Session file corrupted"
- **Cause**: Interrupted save operation or disk issues
- **Solution**: Choose "Start a fresh session" from recovery options
- **Prevention**: Ensure sufficient disk space

#### Slow performance
- **Cause**: Very large files or low memory
- **Solution**: System automatically optimizes, but consider:
  - Using sampling for initial review
  - Closing other applications
  - Reviewing smaller batches

### Error Recovery

The system includes comprehensive error recovery:
- **Graceful degradation**: Continues with available data
- **Automatic fallbacks**: Alternative approaches when primary methods fail
- **Session recovery**: Multiple options for corrupted sessions
- **Memory management**: Automatic cleanup and optimization

### Getting Help

1. **Check logs**: Error details are logged for debugging
2. **Verify setup**: Ensure all paths and configurations are correct
3. **Test with small dataset**: Isolate issues with minimal data
4. **Check file permissions**: Ensure read access to source files and write access to output directory

## Performance Tips

### For Large Datasets

1. **Use sampling**: Start with 10-20% to test workflow
2. **Batch processing**: Review in smaller sessions
3. **Monitor memory**: System automatically manages but close other applications
4. **Regular breaks**: Save progress frequently (automatic)

### For Large Files

1. **System handles automatically**: Lazy loading and chunked processing
2. **Scrolling**: Use Page Up/Down for faster navigation
3. **Focus areas**: Use comments to note specific sections of interest

### For Better Efficiency

1. **Keyboard shortcuts**: Learn the single-key commands
2. **Comments**: Use brief, structured comments for consistency
3. **Session planning**: Plan review sessions around natural break points
4. **Progress tracking**: Monitor progress indicators to estimate completion time

### Memory Optimization

The system includes automatic optimizations:
- **Content caching**: Frequently accessed content is cached
- **Lazy loading**: Large files loaded only when displayed
- **Garbage collection**: Automatic memory cleanup
- **Chunked processing**: Large datasets processed in manageable chunks

## Best Practices

### Before Starting

1. **Plan your experiment**: Clear naming and objectives
2. **Test setup**: Run with small sample first
3. **Prepare workspace**: Quiet environment, good lighting
4. **Time allocation**: Plan for breaks in long sessions

### During Review

1. **Consistent criteria**: Establish clear classification rules
2. **Detailed comments**: Note specific issues and observations
3. **Regular breaks**: Maintain focus and accuracy
4. **Progress monitoring**: Check completion estimates

### After Completion

1. **Backup reports**: Copy to secure location
2. **Analysis planning**: Consider how to analyze results
3. **Documentation**: Record any methodology notes
4. **Cleanup**: Remove temporary files if needed

## Integration with Analysis Tools

### Excel Analysis

Reports can be opened directly in Excel for:
- Pivot tables and charts
- Statistical analysis
- Filtering and sorting
- Collaboration and sharing

### Python Analysis

```python
import pandas as pd

# Load report
df = pd.read_excel('my_experiment_20241201_143022_a1b2c3d4.xlsx')

# Basic statistics
print(df['reviewer_verdict'].value_counts())
print(f"Average review time: {df['time_to_review_seconds'].mean():.2f} seconds")

# Filter by verdict
successful = df[df['reviewer_verdict'] == 'Success']
print(f"Success rate: {len(successful) / len(df) * 100:.1f}%")
```

### Database Import

CSV reports can be imported into databases:
```sql
-- Example for PostgreSQL
COPY review_results FROM 'report.csv' WITH CSV HEADER;
```

This completes the user guide. The VAITP-Auditor is designed to be intuitive and efficient for manual code review workflows while providing the flexibility and robustness needed for research applications.