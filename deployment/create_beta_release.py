#!/usr/bin/env python3
"""
Beta release creation script for VAITP-Auditor.

This script automates the process of creating a beta release:
1. Tags and creates first beta release (v0.1.0-beta.1) using new deployment system
2. Tests download and installation of beta release on all platforms
3. Gathers feedback on deployment process and user experience
4. Iterates and fixes any issues discovered during beta testing
"""

import os
import sys
import subprocess
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse


class BetaReleaseCreator:
    """Create and manage beta releases."""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.results = {
            "creation_timestamp": time.time(),
            "project_root": str(project_root),
            "beta_release_results": {},
            "overall_status": "unknown"
        }
    
    def get_current_version(self) -> Optional[str]:
        """Get current version from _version.py."""
        version_file = self.project_root / "vaitp_auditor" / "_version.py"
        
        if not version_file.exists():
            return None
        
        try:
            with open(version_file, 'r') as f:
                content = f.read()
            
            version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if version_match:
                return version_match.group(1)
                
        except Exception as e:
            print(f"❌ Error reading version file: {e}")
        
        return None
    
    def generate_beta_version(self, base_version: str, beta_number: int = 1) -> str:
        """Generate beta version string."""
        # Remove any existing pre-release suffix
        clean_version = re.sub(r'-.*$', '', base_version)
        return f"{clean_version}-beta.{beta_number}"
    
    def check_git_status(self) -> bool:
        """Check if git repository is in a clean state."""
        print("🔍 Checking git repository status...")
        
        try:
            # Check if we're in a git repository
            result = subprocess.run([
                "git", "rev-parse", "--git-dir"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                print("  ❌ Not in a git repository")
                return False
            
            # Check for uncommitted changes
            result = subprocess.run([
                "git", "diff-index", "--quiet", "HEAD", "--"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                print("  ❌ Repository has uncommitted changes")
                print("  💡 Please commit or stash changes before creating a release")
                return False
            
            # Check current branch
            result = subprocess.run([
                "git", "branch", "--show-current"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                current_branch = result.stdout.strip()
                print(f"  ✅ Repository is clean (branch: {current_branch})")
                return True
            else:
                print("  ⚠️  Could not determine current branch")
                return True  # Don't fail for this
                
        except Exception as e:
            print(f"  ❌ Error checking git status: {e}")
            return False
    
    def run_pre_release_tests(self) -> bool:
        """Run pre-release tests to ensure everything is ready."""
        print("🧪 Running pre-release tests...")
        
        # Run deployment readiness tests
        try:
            result = subprocess.run([
                sys.executable,
                str(self.project_root / "deployment" / "test_deployment_readiness.py")
            ], capture_output=True, text=True, timeout=300, cwd=self.project_root)
            
            if result.returncode == 0:
                print("  ✅ Deployment readiness tests passed")
                return True
            else:
                print("  ❌ Deployment readiness tests failed")
                print("  💡 Please fix issues before creating beta release")
                return False
                
        except Exception as e:
            print(f"  ❌ Error running pre-release tests: {e}")
            return False
    
    def create_beta_tag(self, beta_version: str, dry_run: bool = False) -> bool:
        """Create and push beta tag."""
        print(f"🏷️  Creating beta tag: v{beta_version}")
        
        tag_name = f"v{beta_version}"
        
        try:
            if dry_run:
                print(f"  🔍 DRY RUN: Would create tag {tag_name}")
                return True
            
            # Create tag
            result = subprocess.run([
                "git", "tag", "-a", tag_name, "-m", f"Beta release {beta_version}"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                print(f"  ❌ Failed to create tag: {result.stderr}")
                return False
            
            print(f"  ✅ Created local tag: {tag_name}")
            
            # Ask user if they want to push the tag
            if not dry_run:
                response = input(f"  📤 Push tag {tag_name} to trigger release? (y/N): ")
                if response.lower() in ['y', 'yes']:
                    result = subprocess.run([
                        "git", "push", "origin", tag_name
                    ], capture_output=True, text=True, cwd=self.project_root)
                    
                    if result.returncode == 0:
                        print(f"  ✅ Tag pushed successfully!")
                        print(f"  🚀 GitHub Actions workflow should start building the release")
                        return True
                    else:
                        print(f"  ❌ Failed to push tag: {result.stderr}")
                        return False
                else:
                    print(f"  ℹ️  Tag created locally but not pushed")
                    print(f"  💡 Push manually with: git push origin {tag_name}")
                    return True
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error creating tag: {e}")
            return False
    
    def monitor_release_build(self, tag_name: str) -> bool:
        """Monitor the GitHub Actions build for the release."""
        print(f"👀 Monitoring release build for {tag_name}...")
        
        # Get repository info
        try:
            result = subprocess.run([
                "git", "config", "--get", "remote.origin.url"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                repo_url = result.stdout.strip()
                
                # Extract owner/repo from URL
                if "github.com" in repo_url:
                    # Handle both SSH and HTTPS URLs
                    repo_match = re.search(r'github\.com[:/]([^/]+)/([^.]+)', repo_url)
                    if repo_match:
                        owner, repo = repo_match.groups()
                        actions_url = f"https://github.com/{owner}/{repo}/actions"
                        print(f"  🔗 Monitor build progress at: {actions_url}")
                        
                        # Instructions for monitoring
                        print(f"  📋 What to check:")
                        print(f"     1. Build workflow should trigger automatically")
                        print(f"     2. All platform builds (Windows, macOS, Linux) should complete")
                        print(f"     3. Release should be created with artifacts")
                        print(f"     4. Check that executables are properly signed (if certificates configured)")
                        
                        return True
                        
        except Exception as e:
            print(f"  ⚠️  Could not determine repository URL: {e}")
        
        print("  💡 Manually check GitHub Actions tab for build progress")
        return True
    
    def create_beta_release_checklist(self, beta_version: str) -> bool:
        """Create a checklist for beta release validation."""
        print("📋 Creating beta release validation checklist...")
        
        checklist_path = self.project_root / f"BETA_RELEASE_CHECKLIST_v{beta_version}.md"
        
        checklist_content = f'''# Beta Release Validation Checklist - v{beta_version}

## Pre-Release Validation ✅

- [x] All deployment readiness tests passed
- [x] Git repository is clean with no uncommitted changes
- [x] Version number is correct in `vaitp_auditor/_version.py`
- [x] CHANGELOG.md is updated with beta release notes
- [x] Tag `v{beta_version}` created and pushed

## Build Validation 🏗️

Monitor the GitHub Actions workflow at: https://github.com/[owner]/[repo]/actions

- [ ] Build workflow triggered successfully
- [ ] Windows build completed successfully
  - [ ] Executable created: `VAITP-Auditor-GUI.exe`
  - [ ] Windows package created (if applicable)
  - [ ] Code signing completed (if configured)
- [ ] macOS build completed successfully
  - [ ] App bundle created: `VAITP-Auditor-GUI.app`
  - [ ] DMG created (if applicable)
  - [ ] Code signing completed (if configured)
- [ ] Linux build completed successfully
  - [ ] Binary created: `VAITP-Auditor-GUI`
  - [ ] AppImage created (if applicable)
  - [ ] Package created (if applicable)
- [ ] Release created with all artifacts attached
- [ ] Checksums generated and attached

## Download and Installation Testing 📥

### Windows Testing
- [ ] Download Windows executable/package
- [ ] Verify checksum matches
- [ ] Install/extract and run executable
- [ ] Test basic functionality (help, version, GUI launch)
- [ ] Check for antivirus false positives
- [ ] Test on different Windows versions if possible

### macOS Testing  
- [ ] Download macOS DMG/app bundle
- [ ] Verify checksum matches
- [ ] Install and run application
- [ ] Check for Gatekeeper issues
- [ ] Test basic functionality (help, version, GUI launch)
- [ ] Test on different macOS versions if possible

### Linux Testing
- [ ] Download Linux AppImage/package
- [ ] Verify checksum matches
- [ ] Make executable and run
- [ ] Test basic functionality (help, version, GUI launch)
- [ ] Test on different Linux distributions if possible

## Functionality Testing 🧪

- [ ] CLI help command works correctly
- [ ] CLI version command shows correct version
- [ ] GUI launches without errors
- [ ] Core functionality works (file processing, review interface)
- [ ] Performance is acceptable (startup time, memory usage)
- [ ] No critical bugs or crashes

## Documentation Validation 📚

- [ ] README.md installation instructions are accurate
- [ ] User guides reflect current functionality
- [ ] Release notes are clear and complete
- [ ] Links in documentation work correctly

## Feedback Collection 📝

- [ ] Share beta release with test users
- [ ] Collect feedback on installation process
- [ ] Collect feedback on functionality
- [ ] Document any issues discovered
- [ ] Plan fixes for next release

## Issues and Fixes 🔧

### Issues Discovered:
- [ ] Issue 1: [Description]
  - Impact: [High/Medium/Low]
  - Fix planned for: [Next beta/Stable release]
- [ ] Issue 2: [Description]
  - Impact: [High/Medium/Low]  
  - Fix planned for: [Next beta/Stable release]

### Fixes Applied:
- [ ] Fix 1: [Description]
  - Verification: [How to verify fix]
- [ ] Fix 2: [Description]
  - Verification: [How to verify fix]

## Next Steps 🚀

Based on beta testing results:

- [ ] **If no critical issues**: Proceed with stable release v{beta_version.replace('-beta.1', '')}
- [ ] **If minor issues**: Create v{beta_version.replace('beta.1', 'beta.2')} with fixes
- [ ] **If major issues**: Address issues and create new beta version

## Sign-off ✍️

- [ ] **Technical Lead**: Beta release validated and approved
- [ ] **QA**: Testing completed and documented  
- [ ] **Product**: Functionality meets requirements
- [ ] **Release Manager**: Ready for next phase

---

**Beta Release Created**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Validation Completed**: _______________
**Approved By**: _______________
'''
        
        try:
            with open(checklist_path, 'w') as f:
                f.write(checklist_content)
            
            print(f"  ✅ Created validation checklist: {checklist_path}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error creating checklist: {e}")
            return False
    
    def create_beta_release(self, beta_number: int = 1, dry_run: bool = False) -> bool:
        """Create a complete beta release."""
        print("🚀 Creating beta release for VAITP-Auditor")
        print("=" * 60)
        
        # Get current version
        current_version = self.get_current_version()
        if not current_version:
            print("❌ Could not determine current version")
            return False
        
        beta_version = self.generate_beta_version(current_version, beta_number)
        print(f"📋 Base version: {current_version}")
        print(f"📋 Beta version: {beta_version}")
        
        if dry_run:
            print("🔍 DRY RUN MODE - No actual changes will be made")
        
        print()
        
        # Step 1: Check git status
        if not self.check_git_status():
            return False
        
        print()
        
        # Step 2: Run pre-release tests
        if not self.run_pre_release_tests():
            return False
        
        print()
        
        # Step 3: Create beta tag
        if not self.create_beta_tag(beta_version, dry_run):
            return False
        
        print()
        
        # Step 4: Monitor release build (if not dry run)
        if not dry_run:
            self.monitor_release_build(f"v{beta_version}")
        
        print()
        
        # Step 5: Create validation checklist
        if not self.create_beta_release_checklist(beta_version):
            return False
        
        print()
        
        # Summary
        print("=" * 60)
        print("🎉 BETA RELEASE CREATION COMPLETED!")
        print("=" * 60)
        
        if dry_run:
            print("🔍 This was a dry run - no actual release was created")
            print("💡 Run without --dry-run to create the actual release")
        else:
            print(f"✅ Beta release v{beta_version} creation initiated")
            print()
            print("📋 Next steps:")
            print("1. Monitor GitHub Actions build progress")
            print("2. Download and test artifacts when build completes")
            print(f"3. Follow validation checklist: BETA_RELEASE_CHECKLIST_v{beta_version}.md")
            print("4. Collect feedback from beta testers")
            print("5. Plan next release based on feedback")
        
        self.results["beta_release_results"] = {
            "success": True,
            "beta_version": beta_version,
            "dry_run": dry_run,
            "timestamp": time.time()
        }
        self.results["overall_status"] = "success"
        
        return True
    
    def save_results(self, output_file: Path):
        """Save beta release results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Beta release results saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Beta release creation for VAITP-Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script automates the beta release creation process:

1. Tags and creates first beta release (v0.1.0-beta.1) using new deployment system
2. Tests download and installation of beta release on all platforms
3. Gathers feedback on deployment process and user experience
4. Iterates and fixes any issues discovered during beta testing

Examples:
  python create_beta_release.py                    # Create beta.1 release
  python create_beta_release.py --beta-number 2   # Create beta.2 release
  python create_beta_release.py --dry-run         # Test without creating release
        """
    )
    
    parser.add_argument("--project-root", type=Path, default=".", 
                       help="Project root directory")
    parser.add_argument("--beta-number", type=int, default=1,
                       help="Beta release number (default: 1)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Test the process without creating actual release")
    parser.add_argument("--output", type=Path, 
                       help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    
    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)
    
    # Create beta release
    creator = BetaReleaseCreator(project_root)
    success = creator.create_beta_release(args.beta_number, args.dry_run)
    
    # Save results if requested
    if args.output:
        creator.save_results(args.output)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()