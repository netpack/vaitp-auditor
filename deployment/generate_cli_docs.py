#!/usr/bin/env python3
"""
CLI documentation generation script for VAITP-Auditor.

This script automatically generates documentation from CLI help text
and command-line interface definitions.
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_cli_help(module_path: str, command: Optional[str] = None) -> str:
    """Get help text from a CLI module."""
    try:
        cmd = [sys.executable, '-m', module_path]
        if command:
            cmd.append(command)
        cmd.append('--help')
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=get_project_root(),
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            logger.error(f"Failed to get help for {module_path} {command or ''}: {result.stderr}")
            return ""
    
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout getting help for {module_path} {command or ''}")
        return ""
    except Exception as e:
        logger.error(f"Error getting help for {module_path} {command or ''}: {e}")
        return ""


def format_help_as_markdown(help_text: str, title: str) -> str:
    """Format CLI help text as markdown."""
    if not help_text.strip():
        return f"# {title}\n\n*Help text not available*\n"
    
    lines = help_text.split('\n')
    markdown_lines = [f"# {title}", ""]
    
    in_code_block = False
    current_section = None
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines at the start
        if not markdown_lines[-1] and not stripped:
            continue
        
        # Detect sections (usage, options, etc.)
        if stripped.lower().startswith(('usage:', 'positional arguments:', 'optional arguments:', 'options:')):
            if in_code_block:
                markdown_lines.append("```")
                in_code_block = False
            
            section_name = stripped.rstrip(':').title()
            markdown_lines.extend(["", f"## {section_name}", ""])
            current_section = section_name.lower()
            
            if current_section == 'usage':
                markdown_lines.append("```")
                in_code_block = True
            
            continue
        
        # Handle different sections
        if current_section == 'usage':
            if not in_code_block:
                markdown_lines.append("```")
                in_code_block = True
            markdown_lines.append(line)
        
        elif current_section in ['positional arguments', 'optional arguments', 'options']:
            if in_code_block:
                markdown_lines.append("```")
                in_code_block = False
            
            # Format argument descriptions
            if line.startswith('  ') and not line.startswith('    '):
                # This is an argument name
                arg_name = line.strip().split()[0]
                rest_of_line = line.strip()[len(arg_name):].strip()
                if rest_of_line:
                    markdown_lines.append(f"- **`{arg_name}`** {rest_of_line}")
                else:
                    markdown_lines.append(f"- **`{arg_name}`**")
            elif line.startswith('    '):
                # This is a description continuation
                markdown_lines.append(f"  {line.strip()}")
            elif stripped:
                markdown_lines.append(line)
        
        else:
            # Default handling
            if stripped:
                markdown_lines.append(line)
    
    # Close any open code block
    if in_code_block:
        markdown_lines.append("```")
    
    # Clean up empty lines
    cleaned_lines = []
    prev_empty = False
    for line in markdown_lines:
        if not line.strip():
            if not prev_empty:
                cleaned_lines.append("")
            prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False
    
    return "\n".join(cleaned_lines) + "\n"


def generate_main_cli_docs() -> str:
    """Generate documentation for the main CLI interface."""
    logger.info("Generating main CLI documentation...")
    
    # Get help for main CLI
    help_text = get_cli_help('vaitp_auditor.cli')
    
    if not help_text:
        # Try alternative import paths
        help_text = get_cli_help('vaitp_auditor')
    
    return format_help_as_markdown(help_text, "VAITP-Auditor CLI")


def generate_gui_cli_docs() -> str:
    """Generate documentation for the GUI CLI interface."""
    logger.info("Generating GUI CLI documentation...")
    
    # Get help for GUI CLI
    help_text = get_cli_help('vaitp_auditor.gui')
    
    return format_help_as_markdown(help_text, "VAITP-Auditor GUI")


def generate_subcommand_docs() -> Dict[str, str]:
    """Generate documentation for CLI subcommands."""
    logger.info("Generating subcommand documentation...")
    
    # Define known subcommands (this would be expanded based on actual CLI structure)
    subcommands = {
        'review': 'Interactive code review mode',
        'batch': 'Batch processing mode',
        'report': 'Generate reports',
        'config': 'Configuration management',
    }
    
    docs = {}
    
    for subcommand, description in subcommands.items():
        help_text = get_cli_help('vaitp_auditor.cli', subcommand)
        if help_text:
            docs[subcommand] = format_help_as_markdown(
                help_text, 
                f"VAITP-Auditor CLI - {subcommand.title()} Command"
            )
        else:
            docs[subcommand] = f"# VAITP-Auditor CLI - {subcommand.title()} Command\n\n{description}\n\n*Detailed help not available*\n"
    
    return docs


def create_cli_reference() -> str:
    """Create a comprehensive CLI reference document."""
    sections = [
        "# VAITP-Auditor CLI Reference",
        "",
        "This document provides comprehensive reference for all VAITP-Auditor command-line interfaces.",
        "",
        "## Table of Contents",
        "",
        "1. [Main CLI Interface](#main-cli-interface)",
        "2. [GUI Interface](#gui-interface)",
        "3. [Subcommands](#subcommands)",
        "4. [Examples](#examples)",
        "5. [Configuration](#configuration)",
        "",
        "---",
        ""
    ]
    
    return "\n".join(sections)


def generate_usage_examples() -> str:
    """Generate common usage examples."""
    examples = """
## Examples

### Basic Usage

```bash
# Launch GUI interface
python -m vaitp_auditor.gui

# Start CLI review session
python -m vaitp_auditor.cli review --source /path/to/code

# Generate report
python -m vaitp_auditor.cli report --input session.json --output report.xlsx
```

### Advanced Usage

```bash
# Batch processing with custom configuration
python -m vaitp_auditor.cli batch \\
    --source /path/to/code \\
    --config custom_config.json \\
    --output batch_results.xlsx

# Review with specific file patterns
python -m vaitp_auditor.cli review \\
    --source /path/to/code \\
    --include "*.py" \\
    --exclude "test_*.py"

# Generate report with custom template
python -m vaitp_auditor.cli report \\
    --input session.json \\
    --template custom_template.xlsx \\
    --output detailed_report.xlsx
```

### Configuration Examples

```bash
# Show current configuration
python -m vaitp_auditor.cli config show

# Set configuration value
python -m vaitp_auditor.cli config set theme dark

# Reset configuration to defaults
python -m vaitp_auditor.cli config reset
```
"""
    return examples


def main():
    parser = argparse.ArgumentParser(
        description="Generate CLI documentation for VAITP-Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--output-dir', default='docs',
                       help='Output directory for generated documentation')
    parser.add_argument('--format', choices=['markdown', 'rst'], default='markdown',
                       help='Output format')
    parser.add_argument('--single-file', action='store_true',
                       help='Generate single comprehensive file instead of separate files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be generated without writing files')
    
    args = parser.parse_args()
    
    try:
        project_root = get_project_root()
        output_dir = project_root / args.output_dir
        
        if not args.dry_run:
            output_dir.mkdir(exist_ok=True)
        
        if args.single_file:
            # Generate single comprehensive file
            logger.info("Generating comprehensive CLI reference...")
            
            content_parts = [
                create_cli_reference(),
                generate_main_cli_docs(),
                generate_gui_cli_docs(),
                "## Subcommands",
                ""
            ]
            
            # Add subcommand documentation
            subcommand_docs = generate_subcommand_docs()
            for subcommand, doc_content in subcommand_docs.items():
                content_parts.extend([
                    f"### {subcommand.title()} Command",
                    "",
                    doc_content.split('\n', 2)[2],  # Skip title and first empty line
                    ""
                ])
            
            # Add examples
            content_parts.append(generate_usage_examples())
            
            full_content = "\n".join(content_parts)
            
            if args.dry_run:
                print("Would generate CLI_REFERENCE.md:")
                print("=" * 50)
                print(full_content[:1000] + "..." if len(full_content) > 1000 else full_content)
                print("=" * 50)
            else:
                output_file = output_dir / "CLI_REFERENCE.md"
                output_file.write_text(full_content)
                logger.info(f"Generated {output_file}")
        
        else:
            # Generate separate files
            docs_to_generate = {
                'CLI_MAIN.md': generate_main_cli_docs(),
                'CLI_GUI.md': generate_gui_cli_docs(),
            }
            
            # Add subcommand docs
            subcommand_docs = generate_subcommand_docs()
            for subcommand, content in subcommand_docs.items():
                docs_to_generate[f'CLI_{subcommand.upper()}.md'] = content
            
            # Add examples
            docs_to_generate['CLI_EXAMPLES.md'] = f"# CLI Usage Examples\n{generate_usage_examples()}"
            
            if args.dry_run:
                print("Would generate the following files:")
                for filename in docs_to_generate.keys():
                    print(f"  - {args.output_dir}/{filename}")
            else:
                for filename, content in docs_to_generate.items():
                    output_file = output_dir / filename
                    output_file.write_text(content)
                    logger.info(f"Generated {output_file}")
        
        logger.info("CLI documentation generation completed successfully")
    
    except Exception as e:
        logger.error(f"CLI documentation generation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()