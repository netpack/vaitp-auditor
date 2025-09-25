#!/usr/bin/env python3
"""
Comprehensive deployment validation script for VAITP-Auditor.

This script validates the entire deployment pipeline including:
- Build system functionality
- Executable quality and performance
- Platform-specific requirements
- Distribution package integrity
- Documentation completeness
"""

import os
import sys
import subprocess
import platform
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse


class DeploymentValidator:
    """Comprehensive deployment validation."""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.system = platform.system().lower()
        self.results = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
            },
            "validation_results": {},
            "timestamp": time.time(),
            "overall_status": "unknown"
        }
    
    def validate_build_system(self) -> bool:
        """Validate the build system components."""
        print("🔧 Validating build system...")
        
        success = True
        
        # Check required files
        required_files = [
            "deployment/build_executable.py",
            "deployment/pyinstaller_config.spec",
            "deployment/test_executable.py",
            "deployment/benchmark_executable.py",
            "deployment/CODE_SIGNING_GUIDE.md",
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
                success = False
        
        if missing_files:
            print(f"  ❌ Missing files: {', '.join(missing_files)}")
        else:
            print("  ✅ All required build files present")
        
        # Check build script functionality
        try:
            result = subprocess.run([
                sys.executable, 
                str(self.project_root / "deployment" / "build_executable.py"),
                "--check-deps"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("  ✅ Build dependencies check passed")
            else:
                print("  ❌ Build dependencies check failed")
                success = False
                
        except Exception as e:
            print(f"  ❌ Error checking build dependencies: {e}")
            success = False
        
        self.results["validation_results"]["build_system"] = {
            "success": success,
            "missing_files": missing_files
        }
        
        return success
    
    def validate_executable_build(self) -> bool:
        """Validate that executables can be built."""
        print("🏗️  Validating executable build...")
        
        # Clean any existing build
        try:
            result = subprocess.run([
                sys.executable,
                str(self.project_root / "deployment" / "build_executable.py"),
                "--clean"
            ], capture_output=True, text=True, timeout=300)  # 5 minutes timeout
            
            if result.returncode == 0:
                print("  ✅ Executable build successful")
                build_success = True
            else:
                print("  ❌ Executable build failed")
                print(f"    Error: {result.stderr}")
                build_success = False
                
        except subprocess.TimeoutExpired:
            print("  ❌ Executable build timeout")
            build_success = False
        except Exception as e:
            print(f"  ❌ Error during build: {e}")
            build_success = False
        
        # Check if executable was created
        dist_dir = self.project_root / "dist"
        executable_found = False
        
        if dist_dir.exists():
            for item in dist_dir.iterdir():
                if self.system == 'windows' and item.suffix == '.exe':
                    executable_found = True
                    break
                elif self.system == 'darwin' and item.suffix == '.app':
                    executable_found = True
                    break
                elif self.system == 'linux' and item.is_file() and not item.suffix:
                    executable_found = True
                    break
        
        if executable_found:
            print("  ✅ Executable file created")
        else:
            print("  ❌ No executable file found")
            build_success = False
        
        self.results["validation_results"]["executable_build"] = {
            "success": build_success,
            "executable_found": executable_found
        }
        
        return build_success
    
    def validate_executable_quality(self) -> bool:
        """Validate executable quality using test scripts."""
        print("🧪 Validating executable quality...")
        
        # Find the executable
        dist_dir = self.project_root / "dist"
        executable_path = None
        
        if dist_dir.exists():
            for item in dist_dir.iterdir():
                if self.system == 'windows' and item.suffix == '.exe':
                    executable_path = item
                    break
                elif self.system == 'darwin' and item.suffix == '.app':
                    executable_path = item
                    break
                elif self.system == 'linux' and item.is_file() and not item.suffix:
                    executable_path = item
                    break
        
        if not executable_path:
            print("  ❌ No executable found for testing")
            self.results["validation_results"]["executable_quality"] = {"success": False}
            return False
        
        # Run executable tests
        try:
            result = subprocess.run([
                sys.executable,
                str(self.project_root / "deployment" / "test_executable.py"),
                "--executable", str(executable_path),
                "--output", str(self.project_root / "validation_test_results.json")
            ], capture_output=True, text=True, timeout=120)
            
            test_success = result.returncode == 0
            
            if test_success:
                print("  ✅ Executable tests passed")
            else:
                print("  ❌ Executable tests failed")
                print(f"    Error: {result.stderr}")
            
        except Exception as e:
            print(f"  ❌ Error running executable tests: {e}")
            test_success = False
        
        # Run performance benchmarks
        try:
            result = subprocess.run([
                sys.executable,
                str(self.project_root / "deployment" / "benchmark_executable.py"),
                "--executable", str(executable_path),
                "--output", str(self.project_root / "validation_benchmark.json"),
                "--iterations", "3",
                "--duration", "5"
            ], capture_output=True, text=True, timeout=120)
            
            benchmark_success = result.returncode == 0
            
            if benchmark_success:
                print("  ✅ Performance benchmarks completed")
            else:
                print("  ❌ Performance benchmarks failed")
                print(f"    Error: {result.stderr}")
            
        except Exception as e:
            print(f"  ❌ Error running benchmarks: {e}")
            benchmark_success = False
        
        overall_success = test_success and benchmark_success
        
        self.results["validation_results"]["executable_quality"] = {
            "success": overall_success,
            "test_success": test_success,
            "benchmark_success": benchmark_success,
            "executable_path": str(executable_path)
        }
        
        return overall_success
    
    def validate_code_signing_setup(self) -> bool:
        """Validate code signing setup and documentation."""
        print("🔐 Validating code signing setup...")
        
        # Check code signing tools
        try:
            result = subprocess.run([
                sys.executable,
                str(self.project_root / "deployment" / "build_executable.py"),
                "--check-signing"
            ], capture_output=True, text=True, timeout=30)
            
            tools_available = result.returncode == 0
            
        except Exception as e:
            print(f"  ❌ Error checking signing tools: {e}")
            tools_available = False
        
        # Check documentation
        signing_guide = self.project_root / "deployment" / "CODE_SIGNING_GUIDE.md"
        docs_available = signing_guide.exists()
        
        if tools_available:
            print("  ✅ Code signing tools available")
        else:
            print("  ⚠️  Code signing tools not available (acceptable for development)")
        
        if docs_available:
            print("  ✅ Code signing documentation present")
        else:
            print("  ❌ Code signing documentation missing")
        
        # Overall success if docs are present (tools are optional)
        success = docs_available
        
        self.results["validation_results"]["code_signing"] = {
            "success": success,
            "tools_available": tools_available,
            "docs_available": docs_available
        }
        
        return success
    
    def validate_github_actions(self) -> bool:
        """Validate GitHub Actions workflow configuration."""
        print("🚀 Validating GitHub Actions workflow...")
        
        workflow_file = self.project_root / ".github" / "workflows" / "test-build.yml"
        
        if not workflow_file.exists():
            print("  ❌ GitHub Actions workflow file missing")
            self.results["validation_results"]["github_actions"] = {"success": False}
            return False
        
        # Basic validation of workflow file
        try:
            import yaml
            with open(workflow_file, 'r') as f:
                workflow_data = yaml.safe_load(f)
            
            # Check for required jobs
            required_jobs = ["test-build-windows", "test-build-macos", "test-build-linux"]
            has_required_jobs = all(job in workflow_data.get("jobs", {}) for job in required_jobs)
            
            if has_required_jobs:
                print("  ✅ GitHub Actions workflow properly configured")
                success = True
            else:
                print("  ❌ GitHub Actions workflow missing required jobs")
                success = False
                
        except ImportError:
            print("  ⚠️  Cannot validate workflow (PyYAML not available)")
            success = True  # Don't fail validation for missing optional dependency
        except Exception as e:
            print(f"  ❌ Error validating workflow: {e}")
            success = False
        
        self.results["validation_results"]["github_actions"] = {
            "success": success,
            "workflow_exists": workflow_file.exists()
        }
        
        return success
    
    def validate_documentation(self) -> bool:
        """Validate deployment documentation."""
        print("📚 Validating documentation...")
        
        required_docs = [
            "deployment/README.md",
            "deployment/CODE_SIGNING_GUIDE.md",
            "README.md",
            "CHANGELOG.md"
        ]
        
        missing_docs = []
        for doc_path in required_docs:
            full_path = self.project_root / doc_path
            if not full_path.exists():
                missing_docs.append(doc_path)
        
        if missing_docs:
            print(f"  ❌ Missing documentation: {', '.join(missing_docs)}")
            success = False
        else:
            print("  ✅ All required documentation present")
            success = True
        
        self.results["validation_results"]["documentation"] = {
            "success": success,
            "missing_docs": missing_docs
        }
        
        return success
    
    def validate_package_creation(self) -> bool:
        """Validate package creation functionality."""
        print("📦 Validating package creation...")
        
        try:
            result = subprocess.run([
                sys.executable,
                str(self.project_root / "deployment" / "build_executable.py"),
                "--package"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("  ✅ Package creation successful")
                
                # Check if package was created
                package_found = False
                for item in self.project_root.iterdir():
                    if item.name.startswith("VAITP-Auditor-GUI-"):
                        package_found = True
                        print(f"    Created: {item.name}")
                        break
                
                success = package_found
                if not package_found:
                    print("  ❌ No package file found")
                    
            else:
                print("  ❌ Package creation failed")
                print(f"    Error: {result.stderr}")
                success = False
                
        except Exception as e:
            print(f"  ❌ Error creating package: {e}")
            success = False
        
        self.results["validation_results"]["package_creation"] = {
            "success": success
        }
        
        return success
    
    def run_full_validation(self) -> bool:
        """Run complete deployment validation."""
        print("🎯 Running comprehensive deployment validation")
        print(f"Platform: {self.system} ({platform.machine()})")
        print("=" * 60)
        
        validations = [
            ("Build System", self.validate_build_system),
            ("Executable Build", self.validate_executable_build),
            ("Executable Quality", self.validate_executable_quality),
            ("Code Signing Setup", self.validate_code_signing_setup),
            ("GitHub Actions", self.validate_github_actions),
            ("Documentation", self.validate_documentation),
            ("Package Creation", self.validate_package_creation),
        ]
        
        results = {}
        overall_success = True
        
        for name, validator in validations:
            print(f"\n{name}:")
            try:
                success = validator()
                results[name] = success
                if not success:
                    overall_success = False
            except Exception as e:
                print(f"  ❌ Validation error: {e}")
                results[name] = False
                overall_success = False
        
        # Print summary
        print("\n" + "=" * 60)
        print("DEPLOYMENT VALIDATION SUMMARY")
        print("=" * 60)
        
        for name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {name}")
        
        if overall_success:
            print("\n🎉 ALL VALIDATIONS PASSED!")
            print("The deployment system is ready for production use.")
            self.results["overall_status"] = "success"
        else:
            print("\n💥 SOME VALIDATIONS FAILED!")
            print("Please address the issues above before deploying.")
            self.results["overall_status"] = "failed"
        
        return overall_success
    
    def save_results(self, output_file: Path):
        """Save validation results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Validation results saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive deployment validation for VAITP-Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script validates the entire deployment pipeline including build system,
executable quality, code signing setup, GitHub Actions, and documentation.

Examples:
  python validate_deployment.py                    # Run full validation
  python validate_deployment.py --output results.json  # Save results
        """
    )
    
    parser.add_argument("--project-root", type=Path, default=".", 
                       help="Project root directory")
    parser.add_argument("--output", type=Path, 
                       help="Output file for validation results (JSON)")
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    
    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)
    
    # Run validation
    validator = DeploymentValidator(project_root)
    success = validator.run_full_validation()
    
    # Save results if requested
    if args.output:
        validator.save_results(args.output)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()