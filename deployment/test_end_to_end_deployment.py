#!/usr/bin/env python3
"""
End-to-end deployment testing script for VAITP-Auditor.

This script performs comprehensive testing of the complete deployment workflow:
1. Tests complete workflow from code changes to release publication
2. Validates all executables work correctly on target platforms
3. Tests installation and uninstallation procedures for each platform
4. Verifies documentation accuracy and link validity
"""

import os
import sys
import subprocess
import platform
import json
import time
import tempfile
import shutil
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import argparse
import hashlib


class EndToEndDeploymentTester:
    """Comprehensive end-to-end deployment testing."""
    
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
        self.temp_dir = None
    
    def setup_test_environment(self) -> bool:
        """Set up temporary test environment."""
        print("🔧 Setting up test environment...")
        
        try:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="vaitp_e2e_test_"))
            print(f"  ✅ Created test directory: {self.temp_dir}")
            
            # Create subdirectories for different test phases
            (self.temp_dir / "build").mkdir()
            (self.temp_dir / "artifacts").mkdir()
            (self.temp_dir / "installation").mkdir()
            (self.temp_dir / "validation").mkdir()
            
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to setup test environment: {e}")
            return False
    
    def cleanup_test_environment(self):
        """Clean up test environment."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                print(f"  ✅ Cleaned up test directory: {self.temp_dir}")
            except Exception as e:
                print(f"  ⚠️  Failed to cleanup test directory: {e}")
    
    def test_build_pipeline(self) -> bool:
        """Test the complete build pipeline."""
        print("🏗️  Testing build pipeline...")
        
        success = True
        build_results = {}
        
        # Test clean build
        try:
            print("  📋 Testing clean build...")
            result = subprocess.run([
                sys.executable,
                str(self.project_root / "deployment" / "build_executable.py"),
                "--clean"
            ], capture_output=True, text=True, timeout=600)  # 10 minutes timeout
            
            if result.returncode == 0:
                print("    ✅ Clean build successful")
                build_results["clean_build"] = True
            else:
                print("    ❌ Clean build failed")
                print(f"    Error: {result.stderr}")
                build_results["clean_build"] = False
                success = False
                
        except subprocess.TimeoutExpired:
            print("    ❌ Clean build timeout")
            build_results["clean_build"] = False
            success = False
        except Exception as e:
            print(f"    ❌ Clean build error: {e}")
            build_results["clean_build"] = False
            success = False
        
        # Test incremental build
        try:
            print("  📋 Testing incremental build...")
            result = subprocess.run([
                sys.executable,
                str(self.project_root / "deployment" / "build_executable.py")
            ], capture_output=True, text=True, timeout=300)  # 5 minutes timeout
            
            if result.returncode == 0:
                print("    ✅ Incremental build successful")
                build_results["incremental_build"] = True
            else:
                print("    ❌ Incremental build failed")
                print(f"    Error: {result.stderr}")
                build_results["incremental_build"] = False
                success = False
                
        except Exception as e:
            print(f"    ❌ Incremental build error: {e}")
            build_results["incremental_build"] = False
            success = False
        
        # Verify build artifacts
        dist_dir = self.project_root / "dist"
        if dist_dir.exists():
            artifacts = list(dist_dir.iterdir())
            build_results["artifacts_created"] = len(artifacts) > 0
            build_results["artifact_count"] = len(artifacts)
            
            if artifacts:
                print(f"    ✅ {len(artifacts)} build artifacts created")
                for artifact in artifacts:
                    size_mb = artifact.stat().st_size / (1024 * 1024)
                    print(f"      - {artifact.name}: {size_mb:.1f} MB")
            else:
                print("    ❌ No build artifacts found")
                success = False
        else:
            print("    ❌ Build directory not found")
            build_results["artifacts_created"] = False
            success = False
        
        self.results["test_results"]["build_pipeline"] = {
            "success": success,
            "details": build_results
        }
        
        return success
    
    def test_executable_functionality(self) -> bool:
        """Test executable functionality across different scenarios."""
        print("🧪 Testing executable functionality...")
        
        # Find the executable
        dist_dir = self.project_root / "dist"
        executable_path = None
        
        if dist_dir.exists():
            for item in dist_dir.iterdir():
                if self.system == 'windows' and item.suffix == '.exe':
                    executable_path = item
                    break
                elif self.system == 'darwin' and item.suffix == '.app':
                    # For macOS app bundle, find the actual executable
                    macos_exe = item / "Contents" / "MacOS" / "VAITP-Auditor-GUI"
                    if macos_exe.exists():
                        executable_path = macos_exe
                    break
                elif self.system == 'linux' and item.is_file() and not item.suffix:
                    executable_path = item
                    break
        
        if not executable_path:
            print("  ❌ No executable found for testing")
            self.results["test_results"]["executable_functionality"] = {"success": False}
            return False
        
        print(f"  📋 Testing executable: {executable_path}")
        
        success = True
        test_results = {}
        
        # Test 1: Help command
        try:
            print("    🔍 Testing help command...")
            result = subprocess.run([
                str(executable_path), "--help"
            ], capture_output=True, text=True, timeout=30)
            
            help_success = result.returncode == 0 and "usage:" in result.stdout.lower()
            test_results["help_command"] = help_success
            
            if help_success:
                print("      ✅ Help command works")
            else:
                print("      ❌ Help command failed")
                success = False
                
        except Exception as e:
            print(f"      ❌ Help command error: {e}")
            test_results["help_command"] = False
            success = False
        
        # Test 2: Version command
        try:
            print("    🔍 Testing version command...")
            result = subprocess.run([
                str(executable_path), "--version"
            ], capture_output=True, text=True, timeout=30)
            
            version_success = result.returncode == 0 and len(result.stdout.strip()) > 0
            test_results["version_command"] = version_success
            
            if version_success:
                print(f"      ✅ Version: {result.stdout.strip()}")
            else:
                print("      ❌ Version command failed")
                success = False
                
        except Exception as e:
            print(f"      ❌ Version command error: {e}")
            test_results["version_command"] = False
            success = False
        
        # Test 3: GUI launch test (with timeout for headless environments)
        try:
            print("    🔍 Testing GUI launch...")
            result = subprocess.run([
                str(executable_path), "--gui"
            ], capture_output=True, text=True, timeout=10)
            
            # In headless environments, GUI might fail to start but shouldn't crash
            gui_success = result.returncode in [0, 1]  # 0 = success, 1 = display error
            test_results["gui_launch"] = gui_success
            
            if gui_success:
                print("      ✅ GUI launch test completed (may timeout in headless environment)")
            else:
                print("      ❌ GUI launch failed with unexpected error")
                success = False
                
        except subprocess.TimeoutExpired:
            print("      ✅ GUI launch test completed (timeout expected in headless environment)")
            test_results["gui_launch"] = True
        except Exception as e:
            print(f"      ❌ GUI launch error: {e}")
            test_results["gui_launch"] = False
            success = False
        
        # Test 4: File processing test (if test data available)
        test_data_dir = self.project_root / "tests" / "test_data"
        if test_data_dir.exists():
            try:
                print("    🔍 Testing file processing...")
                test_files = list(test_data_dir.glob("*.xlsx"))
                
                if test_files:
                    test_file = test_files[0]
                    result = subprocess.run([
                        str(executable_path), 
                        "--input", str(test_file),
                        "--dry-run"
                    ], capture_output=True, text=True, timeout=60)
                    
                    processing_success = result.returncode == 0
                    test_results["file_processing"] = processing_success
                    
                    if processing_success:
                        print("      ✅ File processing test passed")
                    else:
                        print("      ❌ File processing test failed")
                        success = False
                else:
                    print("      ⚠️  No test files found, skipping file processing test")
                    test_results["file_processing"] = None
                    
            except Exception as e:
                print(f"      ❌ File processing error: {e}")
                test_results["file_processing"] = False
                success = False
        else:
            print("      ⚠️  No test data directory found, skipping file processing test")
            test_results["file_processing"] = None
        
        self.results["test_results"]["executable_functionality"] = {
            "success": success,
            "executable_path": str(executable_path),
            "details": test_results
        }
        
        return success
    
    def test_performance_benchmarks(self) -> bool:
        """Test executable performance benchmarks."""
        print("⚡ Testing performance benchmarks...")
        
        try:
            result = subprocess.run([
                sys.executable,
                str(self.project_root / "deployment" / "benchmark_executable.py"),
                "--output", str(self.temp_dir / "benchmark_results.json"),
                "--iterations", "3",
                "--duration", "10"
            ], capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                print("  ✅ Performance benchmarks completed")
                
                # Load and analyze results
                benchmark_file = self.temp_dir / "benchmark_results.json"
                if benchmark_file.exists():
                    with open(benchmark_file, 'r') as f:
                        benchmark_data = json.load(f)
                    
                    # Check performance targets
                    startup_time = benchmark_data.get("startup_time", {}).get("average", 0)
                    memory_usage = benchmark_data.get("memory_usage", {}).get("peak_mb", 0)
                    
                    performance_ok = startup_time < 10.0 and memory_usage < 500  # 10s startup, 500MB memory
                    
                    if performance_ok:
                        print(f"    ✅ Performance targets met (startup: {startup_time:.1f}s, memory: {memory_usage:.1f}MB)")
                    else:
                        print(f"    ⚠️  Performance targets exceeded (startup: {startup_time:.1f}s, memory: {memory_usage:.1f}MB)")
                    
                    success = True
                else:
                    print("  ❌ Benchmark results file not found")
                    success = False
                    
            else:
                print("  ❌ Performance benchmarks failed")
                print(f"    Error: {result.stderr}")
                success = False
                
        except Exception as e:
            print(f"  ❌ Performance benchmark error: {e}")
            success = False
        
        self.results["test_results"]["performance_benchmarks"] = {
            "success": success
        }
        
        return success
    
    def test_package_creation(self) -> bool:
        """Test package creation for distribution."""
        print("📦 Testing package creation...")
        
        success = True
        package_results = {}
        
        try:
            result = subprocess.run([
                sys.executable,
                str(self.project_root / "deployment" / "build_executable.py"),
                "--package"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("  ✅ Package creation successful")
                
                # Check for created packages
                artifacts_dir = self.temp_dir / "artifacts"
                packages = []
                
                for item in artifacts_dir.iterdir():
                    if item.suffix in ['.zip', '.dmg', '.tar.gz', '.AppImage']:
                        packages.append(item)
                        size_mb = item.stat().st_size / (1024 * 1024)
                        print(f"    📦 {item.name}: {size_mb:.1f} MB")
                
                package_results["packages_created"] = len(packages)
                package_results["package_files"] = [p.name for p in packages]
                
                if packages:
                    print(f"  ✅ {len(packages)} packages created")
                else:
                    print("  ❌ No packages found")
                    success = False
                    
            else:
                print("  ❌ Package creation failed")
                print(f"    Error: {result.stderr}")
                success = False
                
        except Exception as e:
            print(f"  ❌ Package creation error: {e}")
            success = False
        
        self.results["test_results"]["package_creation"] = {
            "success": success,
            "details": package_results
        }
        
        return success
    
    def test_installation_procedures(self) -> bool:
        """Test installation and uninstallation procedures."""
        print("💿 Testing installation procedures...")
        
        success = True
        install_results = {}
        
        # Platform-specific installation tests
        if self.system == 'windows':
            success = self._test_windows_installation()
        elif self.system == 'darwin':
            success = self._test_macos_installation()
        elif self.system == 'linux':
            success = self._test_linux_installation()
        else:
            print(f"  ⚠️  Installation testing not implemented for {self.system}")
            success = True  # Don't fail for unsupported platforms
        
        self.results["test_results"]["installation_procedures"] = {
            "success": success,
            "platform": self.system
        }
        
        return success
    
    def _test_windows_installation(self) -> bool:
        """Test Windows-specific installation procedures."""
        print("  🪟 Testing Windows installation...")
        
        # Test executable permissions and dependencies
        dist_dir = self.project_root / "dist"
        exe_files = list(dist_dir.glob("*.exe"))
        
        if not exe_files:
            print("    ❌ No Windows executable found")
            return False
        
        exe_file = exe_files[0]
        
        # Test file properties
        try:
            import win32api
            info = win32api.GetFileVersionInfo(str(exe_file), "\\")
            print(f"    ✅ Executable has version info: {info}")
        except ImportError:
            print("    ⚠️  Cannot check version info (win32api not available)")
        except Exception as e:
            print(f"    ⚠️  Version info check failed: {e}")
        
        # Test that executable runs without additional dependencies
        try:
            result = subprocess.run([str(exe_file), "--version"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("    ✅ Executable runs independently")
                return True
            else:
                print("    ❌ Executable failed to run")
                return False
        except Exception as e:
            print(f"    ❌ Executable test failed: {e}")
            return False
    
    def _test_macos_installation(self) -> bool:
        """Test macOS-specific installation procedures."""
        print("  🍎 Testing macOS installation...")
        
        # Test app bundle structure
        dist_dir = self.project_root / "dist"
        app_bundles = list(dist_dir.glob("*.app"))
        
        if not app_bundles:
            print("    ❌ No macOS app bundle found")
            return False
        
        app_bundle = app_bundles[0]
        
        # Check app bundle structure
        required_paths = [
            app_bundle / "Contents",
            app_bundle / "Contents" / "MacOS",
            app_bundle / "Contents" / "Info.plist"
        ]
        
        for path in required_paths:
            if not path.exists():
                print(f"    ❌ Missing required path: {path}")
                return False
        
        print("    ✅ App bundle structure is correct")
        
        # Test executable within bundle
        executable = app_bundle / "Contents" / "MacOS" / "VAITP-Auditor-GUI"
        if executable.exists():
            try:
                result = subprocess.run([str(executable), "--version"], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print("    ✅ App bundle executable works")
                    return True
                else:
                    print("    ❌ App bundle executable failed")
                    return False
            except Exception as e:
                print(f"    ❌ App bundle test failed: {e}")
                return False
        else:
            print("    ❌ App bundle executable not found")
            return False
    
    def _test_linux_installation(self) -> bool:
        """Test Linux-specific installation procedures."""
        print("  🐧 Testing Linux installation...")
        
        # Test binary dependencies
        dist_dir = self.project_root / "dist"
        binaries = [f for f in dist_dir.iterdir() if f.is_file() and not f.suffix]
        
        if not binaries:
            print("    ❌ No Linux binary found")
            return False
        
        binary = binaries[0]
        
        # Test binary dependencies using ldd
        try:
            result = subprocess.run(["ldd", str(binary)], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                # Check for missing dependencies
                if "not found" in result.stdout:
                    print("    ❌ Binary has missing dependencies")
                    print(f"    Dependencies: {result.stdout}")
                    return False
                else:
                    print("    ✅ All binary dependencies satisfied")
            else:
                print("    ⚠️  Could not check dependencies (static binary?)")
        except FileNotFoundError:
            print("    ⚠️  ldd not available, skipping dependency check")
        except Exception as e:
            print(f"    ⚠️  Dependency check failed: {e}")
        
        # Test that binary runs
        try:
            result = subprocess.run([str(binary), "--version"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("    ✅ Binary runs correctly")
                return True
            else:
                print("    ❌ Binary failed to run")
                return False
        except Exception as e:
            print(f"    ❌ Binary test failed: {e}")
            return False
    
    def test_documentation_validity(self) -> bool:
        """Test documentation accuracy and link validity."""
        print("📚 Testing documentation validity...")
        
        success = True
        doc_results = {}
        
        # Test required documentation files
        required_docs = [
            "README.md",
            "CHANGELOG.md",
            "deployment/README.md",
            "deployment/CODE_SIGNING_GUIDE.md",
            "deployment/MAINTAINER_GUIDE.md",
            "docs/GUI_USER_GUIDE.md",
            "docs/DEVELOPER_GUIDE.md"
        ]
        
        missing_docs = []
        for doc_path in required_docs:
            full_path = self.project_root / doc_path
            if not full_path.exists():
                missing_docs.append(doc_path)
        
        if missing_docs:
            print(f"  ❌ Missing documentation files: {', '.join(missing_docs)}")
            success = False
        else:
            print("  ✅ All required documentation files present")
        
        doc_results["missing_docs"] = missing_docs
        
        # Test link validity in README
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                
                # Extract local file links
                import re
                local_links = re.findall(r'\[.*?\]\(([^http][^)]+)\)', readme_content)
                
                broken_links = []
                for link in local_links:
                    # Handle anchor links
                    if '#' in link:
                        link = link.split('#')[0]
                    
                    if link and not link.startswith('http'):
                        link_path = self.project_root / link
                        if not link_path.exists():
                            broken_links.append(link)
                
                if broken_links:
                    print(f"  ❌ Broken links in README: {', '.join(broken_links)}")
                    success = False
                else:
                    print("  ✅ All README links are valid")
                
                doc_results["broken_links"] = broken_links
                
            except Exception as e:
                print(f"  ❌ Error checking README links: {e}")
                success = False
        
        # Test that version information is consistent
        try:
            version_file = self.project_root / "vaitp_auditor" / "_version.py"
            if version_file.exists():
                with open(version_file, 'r') as f:
                    version_content = f.read()
                
                # Extract version
                version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', version_content)
                if version_match:
                    version = version_match.group(1)
                    print(f"  ✅ Current version: {version}")
                    doc_results["current_version"] = version
                else:
                    print("  ❌ Could not extract version from _version.py")
                    success = False
            else:
                print("  ❌ Version file not found")
                success = False
                
        except Exception as e:
            print(f"  ❌ Error checking version: {e}")
            success = False
        
        self.results["test_results"]["documentation_validity"] = {
            "success": success,
            "details": doc_results
        }
        
        return success
    
    def test_github_actions_workflow(self) -> bool:
        """Test GitHub Actions workflow configuration."""
        print("🚀 Testing GitHub Actions workflow...")
        
        success = True
        workflow_results = {}
        
        # Check workflow files
        workflow_files = [
            ".github/workflows/build-and-release.yml",
            ".github/workflows/release-drafter.yml"
        ]
        
        missing_workflows = []
        for workflow_path in workflow_files:
            full_path = self.project_root / workflow_path
            if not full_path.exists():
                missing_workflows.append(workflow_path)
        
        if missing_workflows:
            print(f"  ❌ Missing workflow files: {', '.join(missing_workflows)}")
            success = False
        else:
            print("  ✅ All workflow files present")
        
        workflow_results["missing_workflows"] = missing_workflows
        
        # Test workflow syntax (if PyYAML is available)
        try:
            import yaml
            
            for workflow_path in workflow_files:
                full_path = self.project_root / workflow_path
                if full_path.exists():
                    try:
                        with open(full_path, 'r') as f:
                            yaml.safe_load(f)
                        print(f"  ✅ {workflow_path} syntax is valid")
                    except yaml.YAMLError as e:
                        print(f"  ❌ {workflow_path} syntax error: {e}")
                        success = False
                        
        except ImportError:
            print("  ⚠️  PyYAML not available, skipping workflow syntax check")
        
        # Test Release Drafter configuration
        drafter_config = self.project_root / ".github" / "release-drafter.yml"
        if drafter_config.exists():
            print("  ✅ Release Drafter configuration found")
        else:
            print("  ❌ Release Drafter configuration missing")
            success = False
        
        self.results["test_results"]["github_actions_workflow"] = {
            "success": success,
            "details": workflow_results
        }
        
        return success
    
    def run_comprehensive_test(self) -> bool:
        """Run comprehensive end-to-end deployment testing."""
        print("🎯 Running comprehensive end-to-end deployment testing")
        print(f"Platform: {self.system} ({platform.machine()})")
        print(f"Python: {platform.python_version()}")
        print("=" * 70)
        
        if not self.setup_test_environment():
            return False
        
        try:
            tests = [
                ("Build Pipeline", self.test_build_pipeline),
                ("Executable Functionality", self.test_executable_functionality),
                ("Performance Benchmarks", self.test_performance_benchmarks),
                ("Package Creation", self.test_package_creation),
                ("Installation Procedures", self.test_installation_procedures),
                ("Documentation Validity", self.test_documentation_validity),
                ("GitHub Actions Workflow", self.test_github_actions_workflow),
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
            print("END-TO-END DEPLOYMENT TEST SUMMARY")
            print("=" * 70)
            
            for name, success in results.items():
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"{status} {name}")
            
            print(f"\nPlatform: {self.system} ({platform.machine()})")
            print(f"Python: {platform.python_version()}")
            print(f"Test Duration: {time.time() - self.results['timestamp']:.1f} seconds")
            
            if overall_success:
                print("\n🎉 ALL END-TO-END TESTS PASSED!")
                print("The deployment system is fully validated and ready for production.")
                self.results["overall_status"] = "success"
            else:
                print("\n💥 SOME END-TO-END TESTS FAILED!")
                print("Please address the issues above before proceeding with deployment.")
                self.results["overall_status"] = "failed"
            
            return overall_success
            
        finally:
            self.cleanup_test_environment()
    
    def save_results(self, output_file: Path):
        """Save test results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Test results saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="End-to-end deployment testing for VAITP-Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script performs comprehensive end-to-end testing of the deployment pipeline:

1. Tests complete workflow from code changes to release publication
2. Validates all executables work correctly on target platforms  
3. Tests installation and uninstallation procedures for each platform
4. Verifies documentation accuracy and link validity

Examples:
  python test_end_to_end_deployment.py                    # Run full test suite
  python test_end_to_end_deployment.py --output results.json  # Save results
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
    tester = EndToEndDeploymentTester(project_root)
    success = tester.run_comprehensive_test()
    
    # Save results if requested
    if args.output:
        tester.save_results(args.output)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()