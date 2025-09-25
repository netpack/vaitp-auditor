#!/usr/bin/env python3
"""
Release validation script for VAITP-Auditor.

This script validates that a release has been created successfully
and that all artifacts are available and functional.
"""

import argparse
import hashlib
import json
import logging
import re
import requests
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_github_repo_info() -> Tuple[str, str]:
    """Get GitHub repository owner and name from git remote."""
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True,
            cwd=get_project_root()
        )
        
        if result.returncode != 0:
            raise ValueError("Could not get git remote URL")
        
        url = result.stdout.strip()
        
        # Parse GitHub URL
        if url.startswith('git@github.com:'):
            # SSH format: git@github.com:owner/repo.git
            repo_part = url.replace('git@github.com:', '').replace('.git', '')
        elif url.startswith('https://github.com/'):
            # HTTPS format: https://github.com/owner/repo.git
            repo_part = url.replace('https://github.com/', '').replace('.git', '')
        else:
            raise ValueError(f"Unsupported git remote URL format: {url}")
        
        owner, repo = repo_part.split('/', 1)
        return owner, repo
    
    except Exception as e:
        logger.error(f"Could not determine GitHub repository: {e}")
        # Fallback values
        return "your-org", "vaitp-auditor"


def get_github_release_info(version: str, owner: str, repo: str) -> Optional[Dict]:
    """Get release information from GitHub API."""
    try:
        # Ensure version has 'v' prefix for GitHub API
        tag_name = version if version.startswith('v') else f'v{version}'
        
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag_name}"
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            logger.error(f"Release {tag_name} not found")
            return None
        else:
            logger.error(f"GitHub API error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error fetching release info: {e}")
        return None


def validate_release_assets(release_info: Dict) -> Dict[str, bool]:
    """Validate that all expected release assets are present."""
    expected_assets = {
        'windows': r'VAITP-Auditor.*[Ww]indows.*\.(exe|zip)$',
        'macos': r'VAITP-Auditor.*[Mm]ac[Oo][Ss].*\.(dmg|zip|app\.zip)$',
        'linux': r'VAITP-Auditor.*[Ll]inux.*\.(AppImage|tar\.gz|zip)$'
    }
    
    assets = release_info.get('assets', [])
    asset_names = [asset['name'] for asset in assets]
    
    logger.info(f"Found {len(assets)} release assets:")
    for name in asset_names:
        logger.info(f"  - {name}")
    
    validation_results = {}
    
    for platform, pattern in expected_assets.items():
        found = any(re.search(pattern, name, re.IGNORECASE) for name in asset_names)
        validation_results[platform] = found
        
        if found:
            logger.info(f"✓ {platform.title()} asset found")
        else:
            logger.warning(f"✗ {platform.title()} asset missing (pattern: {pattern})")
    
    return validation_results


def download_and_validate_asset(asset_info: Dict, temp_dir: Path) -> bool:
    """Download and validate a release asset."""
    try:
        name = asset_info['name']
        download_url = asset_info['browser_download_url']
        size = asset_info['size']
        
        logger.info(f"Downloading {name} ({size} bytes)...")
        
        response = requests.get(download_url, timeout=300)
        response.raise_for_status()
        
        # Verify size
        if len(response.content) != size:
            logger.error(f"Size mismatch for {name}: expected {size}, got {len(response.content)}")
            return False
        
        # Save to temp directory
        asset_path = temp_dir / name
        asset_path.write_bytes(response.content)
        
        # Basic validation based on file type
        if name.endswith('.zip'):
            try:
                with zipfile.ZipFile(asset_path, 'r') as zf:
                    zf.testzip()
                logger.info(f"✓ {name} is a valid ZIP file")
            except zipfile.BadZipFile:
                logger.error(f"✗ {name} is not a valid ZIP file")
                return False
        
        elif name.endswith('.exe'):
            # Check if it's a valid PE file (basic check)
            with open(asset_path, 'rb') as f:
                header = f.read(2)
                if header != b'MZ':
                    logger.error(f"✗ {name} is not a valid Windows executable")
                    return False
            logger.info(f"✓ {name} appears to be a valid Windows executable")
        
        elif name.endswith('.dmg'):
            # Basic DMG validation (check magic bytes)
            with open(asset_path, 'rb') as f:
                f.seek(0)
                header = f.read(4)
                # DMG files can have various headers, this is a basic check
                if len(header) == 4:
                    logger.info(f"✓ {name} appears to be a DMG file")
                else:
                    logger.warning(f"? {name} DMG validation inconclusive")
        
        elif name.endswith('.AppImage'):
            # Check if it's an ELF file
            with open(asset_path, 'rb') as f:
                header = f.read(4)
                if header != b'\x7fELF':
                    logger.error(f"✗ {name} is not a valid ELF file")
                    return False
            logger.info(f"✓ {name} appears to be a valid AppImage")
        
        # Calculate checksum
        sha256_hash = hashlib.sha256()
        with open(asset_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        checksum = sha256_hash.hexdigest()
        logger.info(f"✓ {name} SHA256: {checksum}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error validating asset {asset_info['name']}: {e}")
        return False


def validate_release_metadata(release_info: Dict, expected_version: str) -> bool:
    """Validate release metadata."""
    validation_passed = True
    
    # Check version tag
    tag_name = release_info.get('tag_name', '')
    expected_tag = expected_version if expected_version.startswith('v') else f'v{expected_version}'
    
    if tag_name != expected_tag:
        logger.error(f"Tag name mismatch: expected {expected_tag}, got {tag_name}")
        validation_passed = False
    else:
        logger.info(f"✓ Tag name correct: {tag_name}")
    
    # Check if it's a draft
    if release_info.get('draft', False):
        logger.warning("⚠ Release is still a draft")
    else:
        logger.info("✓ Release is published")
    
    # Check if it's a prerelease
    is_prerelease = release_info.get('prerelease', False)
    expected_prerelease = '-' in expected_version
    
    if is_prerelease != expected_prerelease:
        logger.warning(f"⚠ Prerelease flag mismatch: expected {expected_prerelease}, got {is_prerelease}")
    else:
        logger.info(f"✓ Prerelease flag correct: {is_prerelease}")
    
    # Check release notes
    body = release_info.get('body', '').strip()
    if not body:
        logger.warning("⚠ Release has no description/notes")
    else:
        logger.info(f"✓ Release notes present ({len(body)} characters)")
    
    # Check creation date
    created_at = release_info.get('created_at', '')
    if created_at:
        logger.info(f"✓ Release created at: {created_at}")
    
    return validation_passed


def validate_version_consistency(version: str) -> bool:
    """Validate that version is consistent across project files."""
    project_root = get_project_root()
    
    # Files to check for version consistency
    version_files = [
        (project_root / "vaitp_auditor" / "_version.py", r'__version__\s*=\s*["\']([^"\']+)["\']'),
        (project_root / "setup.py", r'version\s*=\s*["\']([^"\']+)["\']'),
    ]
    
    clean_version = version.lstrip('v')
    validation_passed = True
    
    for file_path, pattern in version_files:
        if not file_path.exists():
            logger.warning(f"Version file not found: {file_path}")
            continue
        
        try:
            content = file_path.read_text()
            match = re.search(pattern, content)
            
            if match:
                found_version = match.group(1)
                if found_version == clean_version:
                    logger.info(f"✓ Version consistent in {file_path.name}: {found_version}")
                else:
                    logger.error(f"✗ Version mismatch in {file_path.name}: expected {clean_version}, found {found_version}")
                    validation_passed = False
            else:
                logger.warning(f"⚠ Could not find version in {file_path.name}")
        
        except Exception as e:
            logger.error(f"Error checking version in {file_path.name}: {e}")
            validation_passed = False
    
    return validation_passed


def main():
    parser = argparse.ArgumentParser(
        description="Validate VAITP-Auditor release",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --version 1.0.0                    # Validate specific release
  %(prog)s --latest                           # Validate latest release
  %(prog)s --version 1.0.0 --download         # Download and validate assets
  %(prog)s --version 1.0.0 --full             # Full validation including downloads
        """
    )
    
    parser.add_argument('--version', 
                       help='Version to validate (e.g., 1.0.0 or v1.0.0)')
    parser.add_argument('--latest', action='store_true',
                       help='Validate the latest release')
    parser.add_argument('--download', action='store_true',
                       help='Download and validate release assets')
    parser.add_argument('--full', action='store_true',
                       help='Perform full validation including asset downloads')
    parser.add_argument('--owner', 
                       help='GitHub repository owner (auto-detected if not specified)')
    parser.add_argument('--repo', 
                       help='GitHub repository name (auto-detected if not specified)')
    
    args = parser.parse_args()
    
    try:
        # Determine repository info
        if args.owner and args.repo:
            owner, repo = args.owner, args.repo
        else:
            owner, repo = get_github_repo_info()
        
        logger.info(f"Validating release for {owner}/{repo}")
        
        # Determine version to validate
        if args.latest:
            # Get latest release
            url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                latest_release = response.json()
                version = latest_release['tag_name']
                logger.info(f"Latest release: {version}")
            else:
                logger.error(f"Could not fetch latest release: {response.status_code}")
                sys.exit(1)
        
        elif args.version:
            version = args.version
        
        else:
            logger.error("Either --version or --latest must be specified")
            sys.exit(1)
        
        # Get release information
        logger.info(f"Fetching release information for {version}...")
        release_info = get_github_release_info(version, owner, repo)
        
        if not release_info:
            logger.error(f"Release {version} not found or not accessible")
            sys.exit(1)
        
        validation_passed = True
        
        # Validate release metadata
        logger.info("Validating release metadata...")
        if not validate_release_metadata(release_info, version):
            validation_passed = False
        
        # Validate version consistency
        logger.info("Validating version consistency...")
        if not validate_version_consistency(version):
            validation_passed = False
        
        # Validate release assets
        logger.info("Validating release assets...")
        asset_validation = validate_release_assets(release_info)
        
        if not all(asset_validation.values()):
            validation_passed = False
        
        # Download and validate assets if requested
        if args.download or args.full:
            logger.info("Downloading and validating assets...")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                for asset in release_info.get('assets', []):
                    if not download_and_validate_asset(asset, temp_path):
                        validation_passed = False
        
        # Summary
        if validation_passed:
            logger.info(f"✅ Release {version} validation PASSED")
            
            # Print summary
            print(f"\nRelease Validation Summary for {version}:")
            print(f"  Repository: {owner}/{repo}")
            print(f"  Tag: {release_info['tag_name']}")
            print(f"  Published: {not release_info.get('draft', False)}")
            print(f"  Prerelease: {release_info.get('prerelease', False)}")
            print(f"  Assets: {len(release_info.get('assets', []))}")
            print(f"  Created: {release_info.get('created_at', 'Unknown')}")
            
            if release_info.get('html_url'):
                print(f"  URL: {release_info['html_url']}")
        
        else:
            logger.error(f"❌ Release {version} validation FAILED")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Release validation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()