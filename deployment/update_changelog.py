#!/usr/bin/env python3
"""
Changelog update script for VAITP-Auditor.

This script helps maintain the CHANGELOG.md file by automatically generating
entries from git commits or allowing manual entry of changes.
"""

import argparse
import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_git_commits_since_tag(tag: str) -> List[Dict[str, str]]:
    """Get git commits since the specified tag."""
    try:
        # Get commits since tag
        cmd = ['git', 'log', f'{tag}..HEAD', '--pretty=format:%H|%s|%an|%ad', '--date=short']
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=get_project_root())
        
        if result.returncode != 0:
            logger.error(f"Git command failed: {result.stderr}")
            return []
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        'hash': parts[0][:8],
                        'message': parts[1],
                        'author': parts[2],
                        'date': parts[3]
                    })
        
        return commits
    
    except subprocess.SubprocessError as e:
        logger.error(f"Error getting git commits: {e}")
        return []


def get_latest_tag() -> Optional[str]:
    """Get the latest git tag."""
    try:
        cmd = ['git', 'describe', '--tags', '--abbrev=0']
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=get_project_root())
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            logger.warning("No git tags found")
            return None
    
    except subprocess.SubprocessError as e:
        logger.error(f"Error getting latest tag: {e}")
        return None


def categorize_commit_message(message: str) -> str:
    """Categorize a commit message based on conventional commit patterns."""
    message_lower = message.lower()
    
    # Conventional commit patterns
    if re.match(r'^feat(\(.+\))?:', message_lower):
        return 'Added'
    elif re.match(r'^fix(\(.+\))?:', message_lower):
        return 'Fixed'
    elif re.match(r'^docs(\(.+\))?:', message_lower):
        return 'Changed'
    elif re.match(r'^style(\(.+\))?:', message_lower):
        return 'Changed'
    elif re.match(r'^refactor(\(.+\))?:', message_lower):
        return 'Changed'
    elif re.match(r'^perf(\(.+\))?:', message_lower):
        return 'Changed'
    elif re.match(r'^test(\(.+\))?:', message_lower):
        return 'Changed'
    elif re.match(r'^build(\(.+\))?:', message_lower):
        return 'Changed'
    elif re.match(r'^ci(\(.+\))?:', message_lower):
        return 'Changed'
    elif re.match(r'^chore(\(.+\))?:', message_lower):
        return 'Changed'
    elif re.match(r'^revert(\(.+\))?:', message_lower):
        return 'Fixed'
    
    # Keyword-based categorization
    if any(keyword in message_lower for keyword in ['add', 'new', 'implement', 'create']):
        return 'Added'
    elif any(keyword in message_lower for keyword in ['fix', 'resolve', 'correct', 'patch']):
        return 'Fixed'
    elif any(keyword in message_lower for keyword in ['remove', 'delete', 'drop']):
        return 'Removed'
    elif any(keyword in message_lower for keyword in ['update', 'change', 'modify', 'improve']):
        return 'Changed'
    elif any(keyword in message_lower for keyword in ['deprecate']):
        return 'Deprecated'
    elif any(keyword in message_lower for keyword in ['security', 'vulnerability']):
        return 'Security'
    else:
        return 'Changed'


def clean_commit_message(message: str) -> str:
    """Clean up commit message for changelog entry."""
    # Remove conventional commit prefix
    message = re.sub(r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?:\s*', '', message)
    
    # Capitalize first letter
    if message:
        message = message[0].upper() + message[1:]
    
    # Remove trailing periods
    message = message.rstrip('.')
    
    return message


def generate_changelog_from_commits(commits: List[Dict[str, str]]) -> Dict[str, List[str]]:
    """Generate changelog entries from git commits."""
    categories = {
        'Added': [],
        'Changed': [],
        'Deprecated': [],
        'Removed': [],
        'Fixed': [],
        'Security': []
    }
    
    for commit in commits:
        message = commit['message']
        
        # Skip merge commits and version bumps
        if (message.startswith('Merge ') or 
            message.startswith('Version ') or 
            message.startswith('Bump version') or
            'version' in message.lower() and any(word in message.lower() for word in ['bump', 'update', 'prepare'])):
            continue
        
        category = categorize_commit_message(message)
        clean_message = clean_commit_message(message)
        
        if clean_message and clean_message not in categories[category]:
            categories[category].append(clean_message)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def read_changelog() -> str:
    """Read the current CHANGELOG.md file."""
    changelog_file = get_project_root() / "CHANGELOG.md"
    
    if not changelog_file.exists():
        return """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""
    
    return changelog_file.read_text()


def write_changelog(content: str) -> None:
    """Write content to CHANGELOG.md."""
    changelog_file = get_project_root() / "CHANGELOG.md"
    changelog_file.write_text(content)
    logger.info(f"Updated {changelog_file}")


def create_changelog_entry(version: str, categories: Dict[str, List[str]], 
                          unreleased: bool = False) -> str:
    """Create a changelog entry for the given version and changes."""
    date_str = "Unreleased" if unreleased else datetime.now().strftime("%Y-%m-%d")
    
    lines = [f"## [{version}] - {date_str}", ""]
    
    # Add categories in standard order
    category_order = ['Added', 'Changed', 'Deprecated', 'Removed', 'Fixed', 'Security']
    
    for category in category_order:
        if category in categories and categories[category]:
            lines.append(f"### {category}")
            lines.append("")
            for change in categories[category]:
                lines.append(f"- {change}")
            lines.append("")
    
    return "\n".join(lines)


def insert_changelog_entry(changelog_content: str, entry: str) -> str:
    """Insert a new changelog entry at the appropriate position."""
    lines = changelog_content.split('\n')
    
    # Find the insertion point (after the header, before the first version entry)
    insert_index = len(lines)
    
    for i, line in enumerate(lines):
        if line.startswith('## [') and i > 0:
            insert_index = i
            break
    
    # Insert the new entry
    entry_lines = entry.split('\n')
    for j, entry_line in enumerate(entry_lines):
        lines.insert(insert_index + j, entry_line)
    
    return '\n'.join(lines)


def interactive_changelog_update(version: str) -> Dict[str, List[str]]:
    """Interactively collect changelog entries from user."""
    categories = {
        'Added': [],
        'Changed': [],
        'Deprecated': [],
        'Removed': [],
        'Fixed': [],
        'Security': []
    }
    
    print(f"\nCreating changelog entry for version {version}")
    print("Enter changes for each category (press Enter with empty line to finish each category):")
    
    for category in categories.keys():
        print(f"\n{category}:")
        while True:
            change = input("  - ").strip()
            if not change:
                break
            categories[category].append(change)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def main():
    parser = argparse.ArgumentParser(
        description="Update CHANGELOG.md for VAITP-Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --version 1.0.0                    # Interactive changelog update
  %(prog)s --version 1.0.0 --auto             # Auto-generate from git commits
  %(prog)s --version 1.0.0 --since v0.9.0     # Generate from commits since v0.9.0
  %(prog)s --add "Fixed critical bug"          # Add single change to unreleased
  %(prog)s --unreleased --auto                 # Update unreleased section from commits
        """
    )
    
    parser.add_argument('--version', 
                       help='Version to create changelog entry for')
    parser.add_argument('--auto', action='store_true',
                       help='Automatically generate changelog from git commits')
    parser.add_argument('--since', 
                       help='Generate changes since this tag (default: latest tag)')
    parser.add_argument('--add', action='append', default=[],
                       help='Add specific change (can be used multiple times)')
    parser.add_argument('--unreleased', action='store_true',
                       help='Update unreleased section instead of creating versioned entry')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be added without updating file')
    
    args = parser.parse_args()
    
    try:
        # Determine version
        if args.unreleased:
            version = "Unreleased"
        elif args.version:
            version = args.version.lstrip('v')
        else:
            logger.error("Either --version or --unreleased must be specified")
            sys.exit(1)
        
        # Collect changes
        categories = {}
        
        if args.auto:
            # Auto-generate from git commits
            since_tag = args.since or get_latest_tag()
            
            if since_tag:
                logger.info(f"Generating changelog from commits since {since_tag}")
                commits = get_git_commits_since_tag(since_tag)
                
                if commits:
                    categories = generate_changelog_from_commits(commits)
                    logger.info(f"Found {len(commits)} commits")
                else:
                    logger.warning("No commits found")
            else:
                logger.warning("No previous tag found, cannot auto-generate")
        
        elif args.add:
            # Add specific changes
            categories = {'Changed': args.add}
        
        else:
            # Interactive mode
            categories = interactive_changelog_update(version)
        
        if not categories or not any(categories.values()):
            logger.warning("No changes to add to changelog")
            return
        
        # Create changelog entry
        entry = create_changelog_entry(version, categories, args.unreleased)
        
        if args.dry_run:
            print("\nChangelog entry that would be added:")
            print("=" * 50)
            print(entry)
            print("=" * 50)
        else:
            # Update changelog file
            changelog_content = read_changelog()
            updated_content = insert_changelog_entry(changelog_content, entry)
            write_changelog(updated_content)
            
            logger.info(f"Successfully updated changelog for {version}")
            
            # Show summary
            total_changes = sum(len(changes) for changes in categories.values())
            logger.info(f"Added {total_changes} changes across {len(categories)} categories")
    
    except Exception as e:
        logger.error(f"Changelog update failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()