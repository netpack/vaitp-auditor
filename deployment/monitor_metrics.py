#!/usr/bin/env python3
"""
Metrics monitoring script for VAITP-Auditor.

This script collects and reports various metrics about releases,
downloads, issues, and project health.
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_github_repo_info() -> tuple[str, str]:
    """Get GitHub repository owner and name."""
    # This would typically be extracted from git config
    # For now, return placeholder values
    return "your-org", "vaitp-auditor"


def fetch_github_releases(owner: str, repo: str, limit: int = 10) -> List[Dict]:
    """Fetch recent GitHub releases."""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        params = {'per_page': limit}
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    except Exception as e:
        logger.error(f"Error fetching releases: {e}")
        return []


def fetch_github_issues(owner: str, repo: str, state: str = 'all', limit: int = 100) -> List[Dict]:
    """Fetch GitHub issues."""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        params = {
            'state': state,
            'per_page': limit,
            'sort': 'created',
            'direction': 'desc'
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    except Exception as e:
        logger.error(f"Error fetching issues: {e}")
        return []


def calculate_download_stats(releases: List[Dict]) -> Dict:
    """Calculate download statistics from releases."""
    stats = {
        'total_downloads': 0,
        'downloads_by_release': {},
        'downloads_by_platform': {'windows': 0, 'macos': 0, 'linux': 0, 'other': 0},
        'latest_release_downloads': 0,
        'average_downloads_per_release': 0
    }
    
    total_releases = 0
    
    for release in releases:
        if release.get('draft', False):
            continue  # Skip draft releases
        
        release_name = release['tag_name']
        release_downloads = 0
        
        for asset in release.get('assets', []):
            download_count = asset.get('download_count', 0)
            release_downloads += download_count
            stats['total_downloads'] += download_count
            
            # Categorize by platform
            asset_name = asset['name'].lower()
            if 'windows' in asset_name or asset_name.endswith('.exe'):
                stats['downloads_by_platform']['windows'] += download_count
            elif 'macos' in asset_name or 'mac' in asset_name or asset_name.endswith('.dmg'):
                stats['downloads_by_platform']['macos'] += download_count
            elif 'linux' in asset_name or asset_name.endswith('.appimage') or asset_name.endswith('.tar.gz'):
                stats['downloads_by_platform']['linux'] += download_count
            else:
                stats['downloads_by_platform']['other'] += download_count
        
        stats['downloads_by_release'][release_name] = release_downloads
        
        if total_releases == 0:  # Latest release
            stats['latest_release_downloads'] = release_downloads
        
        total_releases += 1
    
    if total_releases > 0:
        stats['average_downloads_per_release'] = stats['total_downloads'] / total_releases
    
    return stats


def calculate_issue_stats(issues: List[Dict]) -> Dict:
    """Calculate issue statistics."""
    stats = {
        'total_issues': len(issues),
        'open_issues': 0,
        'closed_issues': 0,
        'issues_by_label': {},
        'recent_issues': 0,  # Issues created in last 30 days
        'average_close_time_days': 0
    }
    
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    
    close_times = []
    
    for issue in issues:
        # Skip pull requests (they appear in issues API)
        if 'pull_request' in issue:
            continue
        
        if issue['state'] == 'open':
            stats['open_issues'] += 1
        else:
            stats['closed_issues'] += 1
            
            # Calculate close time
            if issue.get('closed_at'):
                created = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
                closed = datetime.fromisoformat(issue['closed_at'].replace('Z', '+00:00'))
                close_time = (closed - created).days
                close_times.append(close_time)
        
        # Check if recent
        created = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
        if created.replace(tzinfo=None) > thirty_days_ago:
            stats['recent_issues'] += 1
        
        # Count labels
        for label in issue.get('labels', []):
            label_name = label['name']
            stats['issues_by_label'][label_name] = stats['issues_by_label'].get(label_name, 0) + 1
    
    if close_times:
        stats['average_close_time_days'] = sum(close_times) / len(close_times)
    
    return stats


def calculate_release_stats(releases: List[Dict]) -> Dict:
    """Calculate release statistics."""
    stats = {
        'total_releases': 0,
        'stable_releases': 0,
        'pre_releases': 0,
        'latest_release': None,
        'release_frequency_days': 0,
        'releases_by_month': {}
    }
    
    release_dates = []
    
    for release in releases:
        if release.get('draft', False):
            continue  # Skip draft releases
        
        stats['total_releases'] += 1
        
        if release.get('prerelease', False):
            stats['pre_releases'] += 1
        else:
            stats['stable_releases'] += 1
        
        if stats['latest_release'] is None:
            stats['latest_release'] = {
                'tag': release['tag_name'],
                'date': release['created_at'],
                'assets': len(release.get('assets', []))
            }
        
        # Track release dates
        created = datetime.fromisoformat(release['created_at'].replace('Z', '+00:00'))
        release_dates.append(created)
        
        # Count by month
        month_key = created.strftime('%Y-%m')
        stats['releases_by_month'][month_key] = stats['releases_by_month'].get(month_key, 0) + 1
    
    # Calculate release frequency
    if len(release_dates) > 1:
        release_dates.sort()
        total_days = (release_dates[0] - release_dates[-1]).days
        stats['release_frequency_days'] = total_days / (len(release_dates) - 1)
    
    return stats


def generate_metrics_report(download_stats: Dict, issue_stats: Dict, release_stats: Dict) -> str:
    """Generate a comprehensive metrics report."""
    report_lines = [
        "# VAITP-Auditor Metrics Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Download Statistics",
        f"- **Total Downloads**: {download_stats['total_downloads']:,}",
        f"- **Latest Release Downloads**: {download_stats['latest_release_downloads']:,}",
        f"- **Average Downloads per Release**: {download_stats['average_downloads_per_release']:.1f}",
        "",
        "### Downloads by Platform",
        f"- **Windows**: {download_stats['downloads_by_platform']['windows']:,}",
        f"- **macOS**: {download_stats['downloads_by_platform']['macos']:,}",
        f"- **Linux**: {download_stats['downloads_by_platform']['linux']:,}",
        f"- **Other**: {download_stats['downloads_by_platform']['other']:,}",
        "",
        "### Top Releases by Downloads",
    ]
    
    # Add top releases
    sorted_releases = sorted(
        download_stats['downloads_by_release'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    for release, downloads in sorted_releases:
        report_lines.append(f"- **{release}**: {downloads:,} downloads")
    
    report_lines.extend([
        "",
        "## Issue Statistics",
        f"- **Total Issues**: {issue_stats['total_issues']}",
        f"- **Open Issues**: {issue_stats['open_issues']}",
        f"- **Closed Issues**: {issue_stats['closed_issues']}",
        f"- **Recent Issues (30 days)**: {issue_stats['recent_issues']}",
        f"- **Average Close Time**: {issue_stats['average_close_time_days']:.1f} days",
        "",
        "### Issues by Label",
    ])
    
    # Add top labels
    sorted_labels = sorted(
        issue_stats['issues_by_label'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    for label, count in sorted_labels:
        report_lines.append(f"- **{label}**: {count}")
    
    report_lines.extend([
        "",
        "## Release Statistics",
        f"- **Total Releases**: {release_stats['total_releases']}",
        f"- **Stable Releases**: {release_stats['stable_releases']}",
        f"- **Pre-releases**: {release_stats['pre_releases']}",
        f"- **Release Frequency**: {release_stats['release_frequency_days']:.1f} days",
        "",
    ])
    
    if release_stats['latest_release']:
        latest = release_stats['latest_release']
        report_lines.extend([
            "### Latest Release",
            f"- **Tag**: {latest['tag']}",
            f"- **Date**: {latest['date']}",
            f"- **Assets**: {latest['assets']}",
            "",
        ])
    
    # Add monthly release chart
    if release_stats['releases_by_month']:
        report_lines.extend([
            "### Releases by Month",
        ])
        
        sorted_months = sorted(release_stats['releases_by_month'].items())
        for month, count in sorted_months:
            report_lines.append(f"- **{month}**: {count}")
    
    return "\n".join(report_lines)


def save_metrics_data(data: Dict, output_file: Path) -> None:
    """Save metrics data to JSON file."""
    data['generated_at'] = datetime.now().isoformat()
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Metrics data saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor and report VAITP-Auditor metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --report                           # Generate metrics report
  %(prog)s --output metrics.json              # Save metrics data to file
  %(prog)s --report --output-dir reports/     # Generate report in specific directory
        """
    )
    
    parser.add_argument('--report', action='store_true',
                       help='Generate metrics report')
    parser.add_argument('--output', 
                       help='Output file for metrics data (JSON format)')
    parser.add_argument('--output-dir', default='.',
                       help='Output directory for reports')
    parser.add_argument('--owner', 
                       help='GitHub repository owner')
    parser.add_argument('--repo', 
                       help='GitHub repository name')
    parser.add_argument('--releases-limit', type=int, default=20,
                       help='Number of releases to analyze')
    parser.add_argument('--issues-limit', type=int, default=200,
                       help='Number of issues to analyze')
    
    args = parser.parse_args()
    
    try:
        # Get repository info
        if args.owner and args.repo:
            owner, repo = args.owner, args.repo
        else:
            owner, repo = get_github_repo_info()
        
        logger.info(f"Collecting metrics for {owner}/{repo}")
        
        # Fetch data
        logger.info("Fetching releases...")
        releases = fetch_github_releases(owner, repo, args.releases_limit)
        
        logger.info("Fetching issues...")
        issues = fetch_github_issues(owner, repo, 'all', args.issues_limit)
        
        # Calculate statistics
        logger.info("Calculating statistics...")
        download_stats = calculate_download_stats(releases)
        issue_stats = calculate_issue_stats(issues)
        release_stats = calculate_release_stats(releases)
        
        # Combine all metrics
        all_metrics = {
            'repository': f"{owner}/{repo}",
            'downloads': download_stats,
            'issues': issue_stats,
            'releases': release_stats
        }
        
        # Save data if requested
        if args.output:
            output_path = Path(args.output)
            save_metrics_data(all_metrics, output_path)
        
        # Generate report if requested
        if args.report:
            logger.info("Generating metrics report...")
            report = generate_metrics_report(download_stats, issue_stats, release_stats)
            
            output_dir = Path(args.output_dir)
            output_dir.mkdir(exist_ok=True)
            
            report_file = output_dir / f"metrics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            report_file.write_text(report)
            
            logger.info(f"Metrics report saved to {report_file}")
            
            # Also print summary to console
            print("\n" + "="*60)
            print("METRICS SUMMARY")
            print("="*60)
            print(f"Repository: {owner}/{repo}")
            print(f"Total Downloads: {download_stats['total_downloads']:,}")
            print(f"Total Issues: {issue_stats['total_issues']}")
            print(f"Open Issues: {issue_stats['open_issues']}")
            print(f"Total Releases: {release_stats['total_releases']}")
            if release_stats['latest_release']:
                print(f"Latest Release: {release_stats['latest_release']['tag']}")
            print("="*60)
        
        logger.info("Metrics collection completed successfully")
    
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()