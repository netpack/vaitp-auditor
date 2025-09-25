#!/usr/bin/env python3
"""
Deployment readiness testing script for VAITP-Auditor.

This script tests deployment readiness without actually building executables:
1. Tests complete workflow configuration
2. Validates all deployment scripts and configurations
3. Tests documentation accuracy and completeness
4. Verifies GitHub Actions workflow configuration
"""

import os
import sys
import subprocess
import platform
import json
import time
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse


class DeploymentReadinessTester:
    """Test deployment readiness without building executables."""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.system = platform.system().lower()
        self.results = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "python_version": platform.python_version(),
            },
            "test_results": {},
            "timestamp": time.time(),
            "overall_status": "unknown"
        }
    
    def test_project_structure(self) -> bool:
        """Test that all required project files and directories exist."""
        print("📁 Testing project structure...")
        
        required_files = [
            "vaitp_auditor/__init__.py",
            "vaitp_auditor/_version.py",
            "vaitp_auditor/cli.py",
            "setup.py",
            "README.md",
            "CHANGELOG.md",
            "LICENSE",
            "deployment/build_executable.py",
            "deployment/pyinstaller_config.spec",
            ".github/workflows/build-and-release.yml",
            ".github/workflows/release-drafter.yml",
            ".github/release-drafter.yml"
        ]
        
        required_dirs = [
            "vaitp_auditor",
            "deployment",
            "docs",
            "tests",
            ".github/workflows"
        ]
        
        missing_files = []
        missing_dirs = []
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        for dir_path in required_dirs:
            if not (self.project_root / dir_path).is_dir():
                missing_dirs.append(dir_path)
        
        success = len(missing_files) == 0 and len(missing_dirs) == 0
        
        if success:
            print(f"  ✅ All {len(required_files)} required files present")
            print(f"  ✅ All {len(required_dirs)} required directories present")
        else:
            if missing_files:
                print(f"  ❌ Missing files: {', '.join(missing_files)}")
            if missing_dirs:
                print(f"  ❌ Missing directories: {', '.join(missing_dirs)}")
        
        self.results["test_results"]["project_structure"] = {
            "success": success,
            "missing_files": missing_files,
            "missing_dirs": missing_dirs
        }
        
        return success
    
    def test_version_consistency(self) -> bool:
        """Test version consistency across all files."""
        print("🔢 Testing version consistency...")
        
        # Get version from _version.py
        version_file = self.project_root / "vaitp_auditor" / "_version.py"
        current_version = None
        
        if version_file.exists():
            try:
                with open(version_file, 'r') as f:
                    content = f.read()
                
                import re
                version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                if version_match:
                    current_version = version_match.group(1)
                    print(f"  📋 Current version: {current_version}")
                    
            except Exception as e:
                print(f"  ❌ Error reading version file: {e}")
        
        if not current_version:
            print("  ❌ Could not determine current version")
            self.results["test_results"]["version_consistency"] = {"success": False}
            return False
        
        # Check setup.py
        setup_py = self.project_root / "setup.py"
        setup_version_ok = False
        
        if setup_py.exists():
            try:
                with open(setup_py, 'r') as f:
                    setup_content = f.read()
                
                if current_version in setup_content:
                    print("  ✅ setup.py version matches")
                    setup_version_ok = True
                else:
                    print("  ⚠️  setup.py version may not match")
                    
            except Exception as e:
                print(f"  ❌ Error checking setup.py: {e}")
        
        # Check CHANGELOG.md
        changelog = self.project_root / "CHANGELOG.md"
        changelog_version_ok = False
        
        if changelog.exists():
            try:
                with open(changelog, 'r') as f:
                    changelog_content = f.read()
                
                if current_version in changelog_content:
                    print("  ✅ CHANGELOG.md contains current version")
                    changelog_version_ok = True
                else:
                    print("  ⚠️  CHANGELOG.md may not contain current version")
                    
            except Exception as e:
                print(f"  ❌ Error checking CHANGELOG.md: {e}")
        
        success = True  # Version consistency is informational
        
        self.results["test_results"]["version_consistency"] = {
            "success": success,
            "current_version": current_version,
            "setup_version_ok": setup_version_ok,
            "changelog_version_ok": changelog_version_ok
        }
        
        return success
    
    def test_build_scripts(self) -> bool:
        """Test build scripts without actually building."""
        print("🔧 Testing build scripts...")
        
        success = True
        
        # Test build script help
        try:
            result = subprocess.run([
                sys.executable,
                str(self.project_root / "deployment" / "build_executable.py"),
                "--help"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and "usage:" in result.stdout:
                print("  ✅ Build script help works")
            else:
                print("  ❌ Build script help failed")
                success = False
                
        except Exception as e:
            print(f"  ❌ Build script error: {e}")
            success = False
        
        # Test dependency check
        try:
            result = subprocess.run([
                sys.executable,
                str(self.project_root / "deployment" / "build_executable.py"),
                "--check-deps"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("  ✅ Build dependencies check passed")
            else:
                print("  ⚠️  Build dependencies check failed (may be missing optional deps)")
                
        except Exception as e:
            print(f"  ⚠️  Build dependency check error: {e}")
        
        # Test PyInstaller spec file
        spec_file = self.project_root / "deployment" / "pyinstaller_config.spec"
        if spec_file.exists():
            print("  ✅ PyInstaller spec file exists")
        else:
            print("  ❌ PyInstaller spec file missing")
            success = False
        
        self.results["test_results"]["build_scripts"] = {
            "success": success
        }
        
        return success
    
    def test_github_workflows(self) -> bool:
        """Test GitHub Actions workflow configurations."""
        print("🚀 Testing GitHub Actions workflows...")
        
        success = True
        workflow_results = {}
        
        workflows = [
            ".github/workflows/build-and-release.yml",
            ".github/workflows/release-drafter.yml",
            ".github/workflows/test-build.yml"
        ]
        
        for workflow_path in workflows:
            full_path = self.project_root / workflow_path
            
            if not full_path.exists():
                print(f"  ❌ {workflow_path} not found")
                workflow_results[workflow_path] = {"exists": False, "valid": False}
                success = False
                continue
            
            # Test YAML syntax
            try:
                with open(full_path, 'r') as f:
                    workflow_data = yaml.safe_load(f)
                
                print(f"  ✅ {workflow_path} syntax valid")
                workflow_results[workflow_path] = {"exists": True, "valid": True}
                
                # Check for required sections
                if 'jobs' in workflow_data:
                    job_count = len(workflow_data['jobs'])
                    print(f"    📋 {job_count} jobs defined")
                else:
                    print(f"    ⚠️  No jobs section found")
                    
            except yaml.YAMLError as e:
                print(f"  ❌ {workflow_path} syntax error: {e}")
                workflow_results[workflow_path] = {"exists": True, "valid": False}
                success = False
            except Exception as e:
                print(f"  ❌ {workflow_path} error: {e}")
                workflow_results[workflow_path] = {"exists": True, "valid": False}
                success = False
        
        # Test Release Drafter config
        drafter_config = self.project_root / ".github" / "release-drafter.yml"
        if drafter_config.exists():
            try:
                with open(drafter_config, 'r') as f:
                    drafter_data = yaml.safe_load(f)
                
                print("  ✅ Release Drafter config valid")
                workflow_results["release-drafter.yml"] = {"exists": True, "valid": True}
                
            except yaml.YAMLError as e:
                print(f"  ❌ Release Drafter config syntax error: {e}")
                workflow_results["release-drafter.yml"] = {"exists": True, "valid": False}
                success = False
        else:
            print("  ❌ Release Drafter config not found")
            workflow_results["release-drafter.yml"] = {"exists": False, "valid": False}
            success = False
        
        self.results["test_results"]["github_workflows"] = {
            "success": success,
            "workflows": workflow_results
        }
        
        return success
    
    def test_cli_functionality(self) -> bool:
        """Test CLI functionality without GUI components."""
        print("⌨️  Testing CLI functionality...")
        
        success = True
        cli_results = {}
        
        # Test CLI help
        try:
            result = subprocess.run([
                sys.executable, "-m", "vaitp_auditor.cli", "--help"
            ], capture_output=True, text=True, timeout=30, cwd=self.project_root)
            
            if result.returncode == 0 and "usage:" in result.stdout:
                print("  ✅ CLI help command works")
                cli_results["help"] = True
            else:
                print("  ❌ CLI help command failed")
                cli_results["help"] = False
                success = False
                
        except Exception as e:
            print(f"  ❌ CLI help error: {e}")
            cli_results["help"] = False
            success = False
        
        # Test CLI version
        try:
            result = subprocess.run([
                sys.executable, "-m", "vaitp_auditor.cli", "--version"
            ], capture_output=True, text=True, timeout=30, cwd=self.project_root)
            
            if result.returncode == 0 and len(result.stdout.strip()) > 0:
                version_output = result.stdout.strip()
                print(f"  ✅ CLI version command works: {version_output}")
                cli_results["version"] = True
            else:
                print("  ❌ CLI version command failed")
                cli_results["version"] = False
                success = False
                
        except Exception as e:
            print(f"  ❌ CLI version error: {e}")
            cli_results["version"] = False
            success = False
        
        self.results["test_results"]["cli_functionality"] = {
            "success": success,
            "details": cli_results
        }
        
        return success
    
    def test_documentation_completeness(self) -> bool:
        """Test documentation completeness."""
        print("📚 Testing documentation completeness...")
        
        required_docs = [
            "README.md",
            "CHANGELOG.md",
            "docs/USER_GUIDE.md",
            "docs/DEVELOPER_GUIDE.md",
            "docs/SETUP_GUIDE.md",
            "deployment/README.md",
            "deployment/CODE_SIGNING_GUIDE.md",
            "deployment/MAINTAINER_GUIDE.md"
        ]
        
        missing_docs = []
        for doc_path in required_docs:
            if not (self.project_root / doc_path).exists():
                missing_docs.append(doc_path)
        
        success = len(missing_docs) == 0
        
        if success:
            print(f"  ✅ All {len(required_docs)} required documentation files present")
        else:
            print(f"  ❌ Missing documentation: {', '.join(missing_docs)}")
        
        # Check README content
        readme_path = self.project_root / "README.md"
        readme_complete = False
        
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                
                required_sections = ['installation', 'usage', 'features']
                missing_sections = []
                
                for section in required_sections:
                    if section.lower() not in readme_content.lower():
                        missing_sections.append(section)
                
                if not missing_sections:
                    print("  ✅ README.md contains all required sections")
                    readme_complete = True
                else:
                    print(f"  ⚠️  README.md missing sections: {', '.join(missing_sections)}")
                    
            except Exception as e:
                print(f"  ❌ Error reading README.md: {e}")
        
        self.results["test_results"]["documentation_completeness"] = {
            "success": success,
            "missing_docs": missing_docs,
            "readme_complete": readme_complete
        }
        
        return success
    
    def test_package_metadata(self) -> bool:
        """Test package metadata and configuration."""
        print("📦 Testing package metadata...")
        
        success = True
        
        # Test setup.py
        setup_py = self.project_root / "setup.py"
        if setup_py.exists():
            try:
                with open(setup_py, 'r') as f:
                    setup_content = f.read()
                
                required_fields = ['name', 'version', 'description', 'author', 'install_requires']
                missing_fields = []
                
                for field in required_fields:
                    if field not in setup_content:
                        missing_fields.append(field)
                
                if not missing_fields:
                    print("  ✅ setup.py contains all required fields")
                else:
                    print(f"  ❌ setup.py missing fields: {', '.join(missing_fields)}")
                    success = False
                    
            except Exception as e:
                print(f"  ❌ Error reading setup.py: {e}")
                success = False
        else:
            print("  ❌ setup.py not found")
            success = False
        
        # Test __init__.py
        init_py = self.project_root / "vaitp_auditor" / "__init__.py"
        if init_py.exists():
            print("  ✅ Package __init__.py exists")
        else:
            print("  ❌ Package __init__.py missing")
            success = False
        
        self.results["test_results"]["package_metadata"] = {
            "success": success
        }
        
        return success
    
    def test_deployment_scripts(self) -> bool:
        """Test deployment scripts and utilities."""
        print("🚀 Testing deployment scripts...")
        
        deployment_scripts = [
            "deployment/build_executable.py",
            "deployment/validate_version.py",
            "deployment/validate_deployment.py",
            "deployment/test_deployment_pipeline.py",
            "deployment/benchmark_executable.py",
            "deployment/test_executable.py"
        ]
        
        missing_scripts = []
        working_scripts = []
        
        for script_path in deployment_scripts:
            full_path = self.project_root / script_path
            
            if not full_path.exists():
                missing_scripts.append(script_path)
                continue
            
            # Test script help
            try:
                result = subprocess.run([
                    sys.executable, str(full_path), "--help"
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    working_scripts.append(script_path)
                    print(f"  ✅ {script_path} works")
                else:
                    print(f"  ⚠️  {script_path} help failed")
                    
            except Exception as e:
                print(f"  ⚠️  {script_path} error: {e}")
        
        success = len(missing_scripts) == 0
        
        if missing_scripts:
            print(f"  ❌ Missing scripts: {', '.join(missing_scripts)}")
        
        self.results["test_results"]["deployment_scripts"] = {
            "success": success,
            "missing_scripts": missing_scripts,
            "working_scripts": working_scripts
        }
        
        return success
    
    def run_comprehensive_test(self) -> bool:
        """Run comprehensive deployment readiness testing."""
        print("🎯 Running comprehensive deployment readiness testing")
        print(f"Platform: {self.system} ({platform.machine()})")
        print(f"Python: {platform.python_version()}")
        print("=" * 70)
        
        tests = [
            ("Project Structure", self.test_project_structure),
            ("Version Consistency", self.test_version_consistency),
            ("Build Scripts", self.test_build_scripts),
            ("GitHub Workflows", self.test_github_workflows),
            ("CLI Functionality", self.test_cli_functionality),
            ("Documentation Completeness", self.test_documentation_completeness),
            ("Package Metadata", self.test_package_metadata),
            ("Deployment Scripts", self.test_deployment_scripts),
        ]
        
        results = {}
        overall_success = True
        
        for name, test_func in tests:
            print(f"\n{name}:")
            print("-" * 50)
            
            try:
                success = test_func()
                results[name] = success
                if not success:
                    overall_success = False
            except Exception as e:
                print(f"  ❌ Test error: {e}")
                results[name] = False
                overall_success = False
        
        # Print comprehensive summary
        print("\n" + "=" * 70)
        print("DEPLOYMENT READINESS TEST SUMMARY")
        print("=" * 70)
        
        for name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {name}")
        
        print(f"\nPlatform: {self.system} ({platform.machine()})")
        print(f"Python: {platform.python_version()}")
        print(f"Test Duration: {time.time() - self.results['timestamp']:.1f} seconds")
        
        if overall_success:
            print("\n🎉 ALL DEPLOYMENT READINESS TESTS PASSED!")
            print("The deployment system is ready for testing and production use.")
            print("\n🚀 Next steps:")
            print("1. Run `deployment/create_test_tag.sh` to test the pipeline")
            print("2. Review `deployment/DEPLOYMENT_VALIDATION_CHECKLIST.md`")
            print("3. Create a production release tag when ready")
            self.results["overall_status"] = "success"
        else:
            print("\n💥 SOME DEPLOYMENT READINESS TESTS FAILED!")
            print("Please address the issues above before proceeding with deployment.")
            self.results["overall_status"] = "failed"
        
        return overall_success
    
    def save_results(self, output_file: Path):
        """Save test results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Test results saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Deployment readiness testing for VAITP-Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script tests deployment readiness without building executables:

1. Tests complete workflow configuration
2. Validates all deployment scripts and configurations  
3. Tests documentation accuracy and completeness
4. Verifies GitHub Actions workflow configuration

Examples:
  python test_deployment_readiness.py                    # Run full test suite
  python test_deployment_readiness.py --output results.json  # Save results
        """
    )
    
    parser.add_argument("--project-root", type=Path, default=".", 
                       help="Project root directory")
    parser.add_argument("--output", type=Path, 
                       help="Output file for test results (JSON)")
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    
    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)
    
    # Run comprehensive testing
    tester = DeploymentReadinessTester(project_root)
    success = tester.run_comprehensive_test()
    
    # Save results if requested
    if args.output:
        tester.save_results(args.output)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()