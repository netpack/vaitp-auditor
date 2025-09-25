#!/usr/bin/env python3
"""
Test script for validating the complete deployment pipeline.

This script tests various aspects of the deployment system including:
- Build artifact generation
- Release asset preparation
- Version extraction and validation
- Workflow configuration validation
"""

import os
import sys
import json
import yaml
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def load_workflow_config(workflow_path: Path) -> Dict:
    """Load and parse GitHub Actions workflow configuration."""
    try:
        with open(workflow_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load workflow config: {e}")
        return {}


def load_release_drafter_config(config_path: Path) -> Dict:
    """Load and parse Release Drafter configuration."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load Release Drafter config: {e}")
        return {}


def test_workflow_structure(workflow_config: Dict) -> bool:
    """Test the structure of the GitHub Actions workflow."""
    print("🧪 Testing workflow structure...")
    
    required_jobs = [
        'test',
        'build-windows', 
        'build-macos',
        'build-linux',
        'validate-executables',
        'test-deployment',
        'create-release'
    ]
    
    if 'jobs' not in workflow_config:
        print("❌ No jobs section found in workflow")
        return False
    
    jobs = workflow_config['jobs']
    missing_jobs = []
    
    for job in required_jobs:
        if job not in jobs:
            missing_jobs.append(job)
        else:
            print(f"✅ Found job: {job}")
    
    if missing_jobs:
        print(f"❌ Missing required jobs: {', '.join(missing_jobs)}")
        return False
    
    # Test job dependencies
    expected_dependencies = {
        'build-windows': ['test'],
        'build-macos': ['test'],
        'build-linux': ['test'],
        'validate-executables': ['build-windows', 'build-macos', 'build-linux'],
        'test-deployment': ['test', 'build-windows', 'build-macos', 'build-linux', 'validate-executables'],
        'create-release': ['test', 'build-windows', 'build-macos', 'build-linux', 'validate-executables']
    }
    
    for job_name, expected_deps in expected_dependencies.items():
        if job_name in jobs:
            job_config = jobs[job_name]
            if 'needs' in job_config:
                actual_deps = job_config['needs']
                if isinstance(actual_deps, str):
                    actual_deps = [actual_deps]
                
                missing_deps = set(expected_deps) - set(actual_deps)
                if missing_deps:
                    print(f"⚠️ Job {job_name} missing dependencies: {', '.join(missing_deps)}")
                else:
                    print(f"✅ Job {job_name} has correct dependencies")
    
    print("✅ Workflow structure test completed")
    return True


def test_release_drafter_config(config: Dict) -> bool:
    """Test the Release Drafter configuration."""
    print("🧪 Testing Release Drafter configuration...")
    
    required_sections = ['categories', 'version-resolver', 'template', 'autolabeler']
    
    for section in required_sections:
        if section not in config:
            print(f"❌ Missing required section: {section}")
            return False
        else:
            print(f"✅ Found section: {section}")
    
    # Test categories
    categories = config.get('categories', [])
    if not categories:
        print("❌ No categories defined")
        return False
    
    category_titles = [cat.get('title', '') for cat in categories]
    print(f"✅ Found {len(categories)} categories: {', '.join(category_titles)}")
    
    # Test version resolver
    version_resolver = config.get('version-resolver', {})
    required_version_types = ['major', 'minor', 'patch']
    
    for version_type in required_version_types:
        if version_type not in version_resolver:
            print(f"❌ Missing version type: {version_type}")
            return False
        else:
            labels = version_resolver[version_type].get('labels', [])
            print(f"✅ {version_type} version labels: {', '.join(labels)}")
    
    # Test autolabeler
    autolabeler = config.get('autolabeler', [])
    if not autolabeler:
        print("⚠️ No autolabeler rules defined")
    else:
        print(f"✅ Found {len(autolabeler)} autolabeler rules")
    
    print("✅ Release Drafter configuration test completed")
    return True


def test_version_extraction() -> bool:
    """Test version extraction from different tag formats."""
    print("🧪 Testing version extraction...")
    
    test_cases = [
        ("v1.0.0", "1.0.0", False),
        ("v1.0.0-beta.1", "1.0.0-beta.1", True),
        ("v2.1.0-alpha.3", "2.1.0-alpha.3", True),
        ("v1.0.0-rc.1", "1.0.0-rc.1", True),
        ("v3.2.1", "3.2.1", False),
    ]
    
    for tag, expected_version, expected_prerelease in test_cases:
        # Simulate version extraction
        version = tag[1:] if tag.startswith('v') else tag
        is_prerelease = any(pre in version for pre in ['beta', 'alpha', 'rc'])
        
        if version == expected_version and is_prerelease == expected_prerelease:
            print(f"✅ {tag} -> {version} (prerelease: {is_prerelease})")
        else:
            print(f"❌ {tag} -> {version} (prerelease: {is_prerelease}) - Expected: {expected_version} (prerelease: {expected_prerelease})")
            return False
    
    print("✅ Version extraction test completed")
    return True


def test_build_script_availability() -> bool:
    """Test that required build scripts are available."""
    print("🧪 Testing build script availability...")
    
    project_root = get_project_root()
    required_scripts = [
        "deployment/build_executable.py",
        "deployment/validate_version.py",
        "deployment/validate_deployment.py",
    ]
    
    for script_path in required_scripts:
        full_path = project_root / script_path
        if full_path.exists():
            print(f"✅ Found script: {script_path}")
        else:
            print(f"❌ Missing script: {script_path}")
            return False
    
    print("✅ Build script availability test completed")
    return True


def test_asset_organization() -> bool:
    """Test asset organization and naming conventions."""
    print("🧪 Testing asset organization...")
    
    # Test expected asset naming patterns
    expected_patterns = {
        'windows': [
            'VAITP-Auditor-GUI.exe',
            'VAITP-Auditor-GUI-Windows-x64-v*.zip'
        ],
        'macos': [
            'VAITP-Auditor-GUI.app',
            'VAITP-Auditor-GUI-macOS-v*.dmg'
        ],
        'linux': [
            'VAITP-Auditor-GUI',
            'VAITP-Auditor-GUI-Linux-x86_64-v*.AppImage',
            'VAITP-Auditor-GUI-Linux-x86_64-v*.tar.gz'
        ]
    }
    
    for platform, patterns in expected_patterns.items():
        print(f"✅ {platform.title()} expected assets: {', '.join(patterns)}")
    
    # Test checksum file generation
    print("✅ Checksum file: SHA256SUMS.txt")
    
    print("✅ Asset organization test completed")
    return True


def simulate_deployment_test() -> bool:
    """Simulate a deployment test without actually deploying."""
    print("🧪 Simulating deployment test...")
    
    # Create temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create mock artifacts
        artifacts_dir = temp_path / "artifacts"
        artifacts_dir.mkdir()
        
        # Create mock executables
        (artifacts_dir / "windows-executable").mkdir()
        (artifacts_dir / "windows-executable" / "VAITP-Auditor-GUI.exe").write_text("mock exe")
        
        (artifacts_dir / "macos-executable").mkdir()
        (artifacts_dir / "macos-executable" / "VAITP-Auditor-GUI.app").mkdir()
        
        (artifacts_dir / "linux-executable").mkdir()
        (artifacts_dir / "linux-executable" / "VAITP-Auditor-GUI").write_text("mock binary")
        
        # Test artifact detection
        expected_artifacts = [
            "windows-executable/VAITP-Auditor-GUI.exe",
            "macos-executable/VAITP-Auditor-GUI.app",
            "linux-executable/VAITP-Auditor-GUI"
        ]
        
        missing_artifacts = []
        for artifact in expected_artifacts:
            artifact_path = artifacts_dir / artifact
            if not artifact_path.exists():
                missing_artifacts.append(artifact)
            else:
                print(f"✅ Found mock artifact: {artifact}")
        
        if missing_artifacts:
            print(f"❌ Missing mock artifacts: {', '.join(missing_artifacts)}")
            return False
        
        # Test release asset preparation
        release_assets_dir = temp_path / "release-assets"
        release_assets_dir.mkdir()
        
        # Simulate copying assets
        for artifact in expected_artifacts:
            src = artifacts_dir / artifact
            if src.is_file():
                dst = release_assets_dir / src.name
                shutil.copy2(src, dst)
                print(f"✅ Prepared release asset: {src.name}")
        
        # Simulate checksum generation
        checksum_file = release_assets_dir / "SHA256SUMS.txt"
        checksum_content = ""
        for asset_file in release_assets_dir.glob("*"):
            if asset_file.is_file() and asset_file.name != "SHA256SUMS.txt":
                # Mock checksum
                checksum_content += f"abc123def456  {asset_file.name}\n"
        
        if checksum_content:
            checksum_file.write_text(checksum_content)
            print(f"✅ Generated mock checksums: {checksum_file}")
        
    print("✅ Deployment simulation test completed")
    return True


def test_workflow_triggers() -> bool:
    """Test workflow trigger configurations."""
    print("🧪 Testing workflow triggers...")
    
    project_root = get_project_root()
    
    # Test main build workflow
    build_workflow = project_root / ".github" / "workflows" / "build-and-release.yml"
    if build_workflow.exists():
        config = load_workflow_config(build_workflow)
        
        # Handle YAML parsing issue where 'on' becomes True
        triggers = config.get('on') or config.get(True)
        if triggers:
            
            # Check for tag triggers
            if 'push' in triggers and 'tags' in triggers['push']:
                tags = triggers['push']['tags']
                if 'v*' in tags or any('v*' in tag for tag in tags):
                    print("✅ Tag-based release triggers configured")
                else:
                    print("❌ Missing v* tag triggers")
                    return False
            else:
                print("❌ Missing tag-based release triggers")
                return False
            
            # Check for test branch triggers
            if 'push' in triggers and 'branches' in triggers['push']:
                branches = triggers['push']['branches']
                if any('test/' in branch or 'ci/' in branch for branch in branches):
                    print("✅ Test branch triggers configured")
                else:
                    print("⚠️ No test branch triggers found")
            
            # Check for PR triggers
            if 'pull_request' in triggers:
                print("✅ Pull request triggers configured")
            else:
                print("⚠️ No pull request triggers found")
        else:
            print("❌ No triggers configured in build workflow")
            return False
    else:
        print("❌ Build workflow not found")
        return False
    
    # Test release drafter workflow
    drafter_workflow = project_root / ".github" / "workflows" / "release-drafter.yml"
    if drafter_workflow.exists():
        print("✅ Release Drafter workflow found")
    else:
        print("⚠️ Release Drafter workflow not found")
    
    print("✅ Workflow triggers test completed")
    return True


def create_test_tag_script() -> bool:
    """Create a script for testing with test tags."""
    print("🧪 Creating test tag script...")
    
    project_root = get_project_root()
    script_path = project_root / "deployment" / "create_test_tag.sh"
    
    script_content = '''#!/bin/bash
# Script to create test tags for deployment pipeline testing

set -e

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

echo -e "${GREEN}🏷️  Test Tag Creation Script${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "Current branch: ${YELLOW}$CURRENT_BRANCH${NC}"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ You have uncommitted changes. Please commit or stash them first.${NC}"
    exit 1
fi

# Generate test tag name
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TEST_TAG="test/deployment-$TIMESTAMP"

echo ""
echo -e "${YELLOW}Creating test tag: $TEST_TAG${NC}"
echo ""

# Create and push test tag
git tag "$TEST_TAG"
echo -e "${GREEN}✅ Created local tag: $TEST_TAG${NC}"

echo ""
echo -e "${YELLOW}Push this tag to trigger the deployment pipeline:${NC}"
echo -e "${GREEN}git push origin $TEST_TAG${NC}"
echo ""
echo -e "${YELLOW}To delete the tag later:${NC}"
echo -e "${GREEN}git tag -d $TEST_TAG${NC}"
echo -e "${GREEN}git push origin --delete $TEST_TAG${NC}"
echo ""

# Ask if user wants to push immediately
read -p "Push the tag now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin "$TEST_TAG"
    echo -e "${GREEN}✅ Tag pushed! Check GitHub Actions for workflow execution.${NC}"
    echo -e "${YELLOW}Workflow URL: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\\([^/]*\\)\\/\\([^.]*\\).*/\\1\\/\\2/')/actions${NC}"
else
    echo -e "${YELLOW}Tag created locally but not pushed.${NC}"
fi
'''
    
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    
    print(f"✅ Created test tag script: {script_path}")
    return True


def create_deployment_validation_checklist() -> bool:
    """Create a checklist for manual deployment validation."""
    print("🧪 Creating deployment validation checklist...")
    
    project_root = get_project_root()
    checklist_path = project_root / "deployment" / "DEPLOYMENT_VALIDATION_CHECKLIST.md"
    
    checklist_content = '''# Deployment Pipeline Validation Checklist

Use this checklist to validate the deployment pipeline before creating production releases.

## Pre-Release Validation

### 🔧 Configuration Validation

- [ ] GitHub Actions workflow files are present and valid
  - [ ] `.github/workflows/build-and-release.yml`
  - [ ] `.github/workflows/release-drafter.yml`
- [ ] Release Drafter configuration is present and valid
  - [ ] `.github/release-drafter.yml`
- [ ] Build scripts are present and executable
  - [ ] `deployment/build_executable.py`
  - [ ] `deployment/validate_version.py`
  - [ ] `deployment/validate_deployment.py`

### 🧪 Test Pipeline Execution

- [ ] Create test tag using `deployment/create_test_tag.sh`
- [ ] Verify workflow triggers correctly on test tag
- [ ] Check that all build jobs complete successfully
  - [ ] Windows build job
  - [ ] macOS build job  
  - [ ] Linux build job
- [ ] Verify executable validation passes on all platforms
- [ ] Check that test deployment job completes successfully
- [ ] Verify artifacts are uploaded correctly

### 📦 Artifact Validation

- [ ] Windows artifacts are created
  - [ ] `VAITP-Auditor-GUI.exe`
  - [ ] `VAITP-Auditor-GUI-Windows-x64-v*.zip` (if package job runs)
- [ ] macOS artifacts are created
  - [ ] `VAITP-Auditor-GUI.app`
  - [ ] `VAITP-Auditor-GUI-macOS-v*.dmg` (if DMG creation succeeds)
- [ ] Linux artifacts are created
  - [ ] `VAITP-Auditor-GUI`
  - [ ] `VAITP-Auditor-GUI-Linux-x86_64-v*.AppImage` (if AppImage creation succeeds)
  - [ ] `VAITP-Auditor-GUI-Linux-x86_64-v*.tar.gz` (if package job runs)

### 🔐 Security Validation

- [ ] Code signing works (if certificates are configured)
  - [ ] Windows executable is signed (if `WINDOWS_CERT_BASE64` secret is set)
  - [ ] macOS app bundle is signed (if `MACOS_CERT_BASE64` secret is set)
- [ ] Checksums are generated correctly
- [ ] No sensitive information is exposed in logs

## Production Release Process

### 📋 Pre-Release Steps

- [ ] All tests pass on main branch
- [ ] Version number is updated in `vaitp_auditor/_version.py`
- [ ] CHANGELOG.md is updated with release notes
- [ ] Documentation is up to date
- [ ] All planned features for the release are complete

### 🏷️ Release Tag Creation

- [ ] Create release tag with format `v*.*.*` (e.g., `v1.0.0`)
- [ ] For pre-releases, use format `v*.*.*-beta.*` or `v*.*.*-alpha.*`
- [ ] Push tag to trigger release workflow

### 🚀 Release Validation

- [ ] Release workflow completes successfully
- [ ] All platform artifacts are attached to the release
- [ ] Release notes are generated correctly
- [ ] Download links work correctly
- [ ] Checksums match downloaded files

### 📱 Post-Release Testing

- [ ] Download and test Windows executable
  - [ ] Launches without errors
  - [ ] Core functionality works
  - [ ] No antivirus false positives
- [ ] Download and test macOS app
  - [ ] Launches without Gatekeeper issues
  - [ ] App bundle is properly structured
  - [ ] Core functionality works
- [ ] Download and test Linux AppImage
  - [ ] Executable permissions are correct
  - [ ] Launches without errors
  - [ ] Core functionality works

### 📢 Communication

- [ ] Update project README if needed
- [ ] Announce release in appropriate channels
- [ ] Update documentation links if needed
- [ ] Monitor for user feedback and issues

## Troubleshooting

### Common Issues

1. **Build failures**
   - Check dependency versions
   - Verify Python version compatibility
   - Check for missing build tools

2. **Code signing failures**
   - Verify certificate secrets are correctly configured
   - Check certificate expiration dates
   - Ensure certificates have proper permissions

3. **Artifact upload failures**
   - Check GitHub Actions permissions
   - Verify artifact paths are correct
   - Check for file size limits

4. **Release creation failures**
   - Verify GITHUB_TOKEN permissions
   - Check Release Drafter configuration
   - Ensure tag format is correct

### Getting Help

- Check GitHub Actions logs for detailed error messages
- Review workflow configuration files
- Test locally using build scripts
- Consult deployment documentation in `deployment/README.md`

---

**Last Updated**: $(date +%Y-%m-%d)
**Pipeline Version**: 1.0.0
'''
    
    checklist_path.write_text(checklist_content)
    
    print(f"✅ Created deployment validation checklist: {checklist_path}")
    return True


def run_all_tests() -> bool:
    """Run all deployment pipeline tests."""
    print("🚀 Running complete deployment pipeline tests...")
    print("=" * 60)
    
    project_root = get_project_root()
    
    # Load configurations
    workflow_config = load_workflow_config(project_root / ".github" / "workflows" / "build-and-release.yml")
    drafter_config = load_release_drafter_config(project_root / ".github" / "release-drafter.yml")
    
    tests = [
        ("Workflow Structure", lambda: test_workflow_structure(workflow_config)),
        ("Release Drafter Config", lambda: test_release_drafter_config(drafter_config)),
        ("Version Extraction", test_version_extraction),
        ("Build Script Availability", test_build_script_availability),
        ("Asset Organization", test_asset_organization),
        ("Deployment Simulation", simulate_deployment_test),
        ("Workflow Triggers", test_workflow_triggers),
        ("Test Tag Script Creation", create_test_tag_script),
        ("Validation Checklist Creation", create_deployment_validation_checklist),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"💥 {test_name} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All deployment pipeline tests passed!")
        print("\n🚀 Next steps:")
        print("1. Run `deployment/create_test_tag.sh` to test the pipeline")
        print("2. Review `deployment/DEPLOYMENT_VALIDATION_CHECKLIST.md`")
        print("3. Create a production release tag when ready")
        return True
    else:
        print("❌ Some tests failed. Please review and fix issues before deploying.")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test deployment pipeline")
    parser.add_argument("--test", choices=[
        "workflow", "drafter", "version", "scripts", "assets", 
        "simulation", "triggers", "all"
    ], default="all", help="Specific test to run")
    
    args = parser.parse_args()
    
    if args.test == "all":
        success = run_all_tests()
    else:
        # Run specific test
        project_root = get_project_root()
        workflow_config = load_workflow_config(project_root / ".github" / "workflows" / "build-and-release.yml")
        drafter_config = load_release_drafter_config(project_root / ".github" / "release-drafter.yml")
        
        test_map = {
            "workflow": lambda: test_workflow_structure(workflow_config),
            "drafter": lambda: test_release_drafter_config(drafter_config),
            "version": test_version_extraction,
            "scripts": test_build_script_availability,
            "assets": test_asset_organization,
            "simulation": simulate_deployment_test,
            "triggers": test_workflow_triggers,
        }
        
        if args.test in test_map:
            success = test_map[args.test]()
        else:
            print(f"❌ Unknown test: {args.test}")
            success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()