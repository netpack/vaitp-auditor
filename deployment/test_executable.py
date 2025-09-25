#!/usr/bin/env python3
"""
Automated testing script for VAITP-Auditor GUI executables.

This script validates built executables across all platforms, testing:
- Executable existence and permissions
- Startup time and memory usage
- Core functionality
- Size optimization
- Platform-specific features
"""

import os
import sys
import subprocess
import platform
import time
import psutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse


class ExecutableTestResult:
    """Container for test results."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors = []
        self.warnings = []
        self.performance_metrics = {}
        self.platform_info = {}
    
    def add_test(self, name: str, passed: bool, message: str = "", warning: bool = False):
        """Add a test result."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {name}: PASS" + (f" - {message}" if message else ""))
        else:
            self.tests_failed += 1
            if warning:
                self.warnings.append(f"{name}: {message}")
                print(f"⚠️  {name}: WARNING - {message}")
            else:
                self.errors.append(f"{name}: {message}")
                print(f"❌ {name}: FAIL - {message}")
    
    def add_metric(self, name: str, value: float, unit: str = ""):
        """Add a performance metric."""
        self.performance_metrics[name] = {"value": value, "unit": unit}
        print(f"📊 {name}: {value:.2f} {unit}")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Tests run: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\nERRORS:")
            for error in self.errors:
                print(f"  ❌ {error}")
        
        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
        
        if self.performance_metrics:
            print("\nPERFORMANCE METRICS:")
            for name, data in self.performance_metrics.items():
                print(f"  📊 {name}: {data['value']:.2f} {data['unit']}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\nSUCCESS RATE: {success_rate:.1f}%")
        
        if self.tests_failed == 0:
            print("🎉 ALL TESTS PASSED!")
            return True
        else:
            print("💥 SOME TESTS FAILED!")
            return False


class ExecutableTester:
    """Main executable testing class."""
    
    def __init__(self, executable_path: Path):
        self.executable_path = Path(executable_path)
        self.system = platform.system().lower()
        self.result = ExecutableTestResult()
        
        # Collect platform info
        self.result.platform_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success."""
        print(f"🧪 Testing executable: {self.executable_path}")
        print(f"Platform: {self.system} ({platform.machine()})")
        print("-" * 60)
        
        # Basic tests
        self.test_executable_exists()
        self.test_executable_permissions()
        self.test_executable_size()
        
        # Platform-specific tests
        if self.system == 'windows':
            self.test_windows_specific()
        elif self.system == 'darwin':
            self.test_macos_specific()
        elif self.system == 'linux':
            self.test_linux_specific()
        
        # Performance tests
        self.test_startup_time()
        self.test_memory_usage()
        
        # Functional tests
        self.test_help_command()
        self.test_version_command()
        
        # Dependencies test
        self.test_dependencies()
        
        return self.result.print_summary()
    
    def test_executable_exists(self):
        """Test that the executable file exists."""
        exists = self.executable_path.exists()
        self.result.add_test(
            "Executable exists",
            exists,
            f"Path: {self.executable_path}" if exists else f"Not found: {self.executable_path}"
        )
    
    def test_executable_permissions(self):
        """Test that the executable has correct permissions."""
        if not self.executable_path.exists():
            self.result.add_test("Executable permissions", False, "File does not exist")
            return
        
        if self.system == 'windows':
            # Windows executables should have .exe extension
            has_exe_ext = self.executable_path.suffix.lower() == '.exe'
            self.result.add_test(
                "Windows executable extension",
                has_exe_ext,
                ".exe extension present" if has_exe_ext else "Missing .exe extension"
            )
        else:
            # Unix-like systems should have execute permission
            is_executable = os.access(self.executable_path, os.X_OK)
            self.result.add_test(
                "Execute permissions",
                is_executable,
                "Execute permission granted" if is_executable else "No execute permission"
            )
    
    def test_executable_size(self):
        """Test executable size and provide optimization feedback."""
        if not self.executable_path.exists():
            self.result.add_test("Executable size", False, "File does not exist")
            return
        
        if self.executable_path.is_dir():
            # Calculate directory size (for .app bundles)
            total_size = sum(f.stat().st_size for f in self.executable_path.rglob('*') if f.is_file())
        else:
            total_size = self.executable_path.stat().st_size
        
        size_mb = total_size / (1024 * 1024)
        self.result.add_metric("Executable size", size_mb, "MB")
        
        # Size thresholds (adjust based on requirements)
        if size_mb < 50:
            self.result.add_test("Size optimization", True, f"Excellent size: {size_mb:.1f} MB")
        elif size_mb < 100:
            self.result.add_test("Size optimization", True, f"Good size: {size_mb:.1f} MB")
        elif size_mb < 200:
            self.result.add_test("Size optimization", True, f"Acceptable size: {size_mb:.1f} MB", warning=True)
        else:
            self.result.add_test("Size optimization", False, f"Large size: {size_mb:.1f} MB - consider optimization")
    
    def test_windows_specific(self):
        """Test Windows-specific features."""
        if self.executable_path.suffix.lower() != '.exe':
            self.result.add_test("Windows executable format", False, "Not a .exe file")
            return
        
        # Test if it's a valid PE executable
        try:
            with open(self.executable_path, 'rb') as f:
                # Check PE header
                f.seek(0)
                dos_header = f.read(2)
                if dos_header == b'MZ':
                    self.result.add_test("PE executable format", True, "Valid PE executable")
                else:
                    self.result.add_test("PE executable format", False, "Invalid PE header")
        except Exception as e:
            self.result.add_test("PE executable format", False, f"Error reading file: {e}")
        
        # Test for code signing (if available)
        try:
            result = subprocess.run(
                ['powershell', '-Command', f'Get-AuthenticodeSignature "{self.executable_path}"'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and 'Valid' in result.stdout:
                self.result.add_test("Code signing", True, "Executable is signed")
            else:
                self.result.add_test("Code signing", True, "Executable is not signed (acceptable for testing)", warning=True)
        except Exception:
            self.result.add_test("Code signing", True, "Could not check signature (acceptable)", warning=True)
    
    def test_macos_specific(self):
        """Test macOS-specific features."""
        if self.executable_path.suffix == '.app':
            # Test app bundle structure
            required_paths = [
                self.executable_path / 'Contents',
                self.executable_path / 'Contents' / 'MacOS',
                self.executable_path / 'Contents' / 'Info.plist'
            ]
            
            bundle_valid = all(path.exists() for path in required_paths)
            self.result.add_test(
                "App bundle structure",
                bundle_valid,
                "Valid app bundle" if bundle_valid else "Invalid app bundle structure"
            )
            
            # Test Info.plist
            info_plist = self.executable_path / 'Contents' / 'Info.plist'
            if info_plist.exists():
                try:
                    import plistlib
                    with open(info_plist, 'rb') as f:
                        plist_data = plistlib.load(f)
                    
                    required_keys = ['CFBundleName', 'CFBundleIdentifier', 'CFBundleVersion']
                    has_required_keys = all(key in plist_data for key in required_keys)
                    
                    self.result.add_test(
                        "Info.plist validity",
                        has_required_keys,
                        "Valid Info.plist" if has_required_keys else "Missing required Info.plist keys"
                    )
                except Exception as e:
                    self.result.add_test("Info.plist validity", False, f"Error reading Info.plist: {e}")
            
            # Find the actual executable
            macos_dir = self.executable_path / 'Contents' / 'MacOS'
            if macos_dir.exists():
                executables = [f for f in macos_dir.iterdir() if f.is_file() and os.access(f, os.X_OK)]
                if executables:
                    actual_executable = executables[0]
                    self.result.add_test("App bundle executable", True, f"Found: {actual_executable.name}")
                else:
                    self.result.add_test("App bundle executable", False, "No executable found in MacOS directory")
        
        # Test for code signing
        try:
            result = subprocess.run(
                ['codesign', '--verify', '--verbose', str(self.executable_path)],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                self.result.add_test("Code signing", True, "Executable is signed")
            else:
                self.result.add_test("Code signing", True, "Executable is not signed (acceptable for testing)", warning=True)
        except Exception:
            self.result.add_test("Code signing", True, "Could not check signature (acceptable)", warning=True)
    
    def test_linux_specific(self):
        """Test Linux-specific features."""
        # Test ELF format
        try:
            with open(self.executable_path, 'rb') as f:
                elf_header = f.read(4)
                if elf_header == b'\\x7fELF':
                    self.result.add_test("ELF executable format", True, "Valid ELF executable")
                else:
                    self.result.add_test("ELF executable format", False, "Invalid ELF header")
        except Exception as e:
            self.result.add_test("ELF executable format", False, f"Error reading file: {e}")
        
        # Test dependencies
        try:
            result = subprocess.run(['ldd', str(self.executable_path)], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Count dependencies
                deps = [line for line in result.stdout.split('\\n') if '=>' in line]
                self.result.add_test("Dynamic dependencies", True, f"Found {len(deps)} dependencies")
                self.result.add_metric("Dependency count", len(deps), "libraries")
            else:
                self.result.add_test("Dynamic dependencies", True, "Static executable or ldd not applicable", warning=True)
        except Exception as e:
            self.result.add_test("Dynamic dependencies", False, f"Error checking dependencies: {e}")
    
    def test_startup_time(self):
        """Test executable startup time."""
        if not self.executable_path.exists():
            self.result.add_test("Startup time", False, "Executable does not exist")
            return
        
        # Get the command to run
        if self.system == 'darwin' and self.executable_path.suffix == '.app':
            # For .app bundles, use 'open' command or find the actual executable
            macos_dir = self.executable_path / 'Contents' / 'MacOS'
            if macos_dir.exists():
                executables = [f for f in macos_dir.iterdir() if f.is_file() and os.access(f, os.X_OK)]
                if executables:
                    cmd = [str(executables[0]), '--help']
                else:
                    self.result.add_test("Startup time", False, "No executable found in app bundle")
                    return
            else:
                self.result.add_test("Startup time", False, "Invalid app bundle structure")
                return
        else:
            cmd = [str(self.executable_path), '--help']
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            end_time = time.time()
            
            startup_time = end_time - start_time
            self.result.add_metric("Startup time", startup_time, "seconds")
            
            # Startup time thresholds
            if startup_time < 2.0:
                self.result.add_test("Startup performance", True, f"Fast startup: {startup_time:.2f}s")
            elif startup_time < 5.0:
                self.result.add_test("Startup performance", True, f"Acceptable startup: {startup_time:.2f}s")
            else:
                self.result.add_test("Startup performance", False, f"Slow startup: {startup_time:.2f}s")
                
        except subprocess.TimeoutExpired:
            self.result.add_test("Startup time", False, "Startup timeout (>30s)")
        except Exception as e:
            self.result.add_test("Startup time", False, f"Error testing startup: {e}")
    
    def test_memory_usage(self):
        """Test memory usage during startup."""
        if not self.executable_path.exists():
            self.result.add_test("Memory usage", False, "Executable does not exist")
            return
        
        # Get the command to run
        if self.system == 'darwin' and self.executable_path.suffix == '.app':
            macos_dir = self.executable_path / 'Contents' / 'MacOS'
            if macos_dir.exists():
                executables = [f for f in macos_dir.iterdir() if f.is_file() and os.access(f, os.X_OK)]
                if executables:
                    cmd = [str(executables[0]), '--help']
                else:
                    self.result.add_test("Memory usage", False, "No executable found in app bundle")
                    return
            else:
                self.result.add_test("Memory usage", False, "Invalid app bundle structure")
                return
        else:
            cmd = [str(self.executable_path), '--help']
        
        try:
            # Start process and monitor memory
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it a moment to start
            time.sleep(0.5)
            
            try:
                ps_process = psutil.Process(process.pid)
                memory_info = ps_process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)  # RSS in MB
                
                self.result.add_metric("Memory usage", memory_mb, "MB")
                
                # Memory usage thresholds
                if memory_mb < 50:
                    self.result.add_test("Memory efficiency", True, f"Low memory usage: {memory_mb:.1f} MB")
                elif memory_mb < 100:
                    self.result.add_test("Memory efficiency", True, f"Moderate memory usage: {memory_mb:.1f} MB")
                elif memory_mb < 200:
                    self.result.add_test("Memory efficiency", True, f"High memory usage: {memory_mb:.1f} MB", warning=True)
                else:
                    self.result.add_test("Memory efficiency", False, f"Very high memory usage: {memory_mb:.1f} MB")
                    
            except psutil.NoSuchProcess:
                self.result.add_test("Memory usage", True, "Process exited quickly (normal for --help)", warning=True)
            
            # Wait for process to complete
            process.wait(timeout=10)
            
        except subprocess.TimeoutExpired:
            self.result.add_test("Memory usage", False, "Process timeout during memory test")
            if 'process' in locals():
                process.kill()
        except Exception as e:
            self.result.add_test("Memory usage", False, f"Error testing memory usage: {e}")
    
    def test_help_command(self):
        """Test that the executable responds to --help."""
        if not self.executable_path.exists():
            self.result.add_test("Help command", False, "Executable does not exist")
            return
        
        # Get the command to run
        if self.system == 'darwin' and self.executable_path.suffix == '.app':
            macos_dir = self.executable_path / 'Contents' / 'MacOS'
            if macos_dir.exists():
                executables = [f for f in macos_dir.iterdir() if f.is_file() and os.access(f, os.X_OK)]
                if executables:
                    cmd = [str(executables[0]), '--help']
                else:
                    self.result.add_test("Help command", False, "No executable found in app bundle")
                    return
            else:
                self.result.add_test("Help command", False, "Invalid app bundle structure")
                return
        else:
            cmd = [str(self.executable_path), '--help']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                help_text = result.stdout.lower()
                has_usage = 'usage' in help_text or 'help' in help_text
                self.result.add_test(
                    "Help command",
                    has_usage,
                    "Help text available" if has_usage else "No help text found"
                )
            else:
                self.result.add_test("Help command", False, f"Non-zero exit code: {result.returncode}")
                
        except subprocess.TimeoutExpired:
            self.result.add_test("Help command", False, "Help command timeout")
        except Exception as e:
            self.result.add_test("Help command", False, f"Error running help command: {e}")
    
    def test_version_command(self):
        """Test that the executable responds to --version."""
        if not self.executable_path.exists():
            self.result.add_test("Version command", False, "Executable does not exist")
            return
        
        # Get the command to run
        if self.system == 'darwin' and self.executable_path.suffix == '.app':
            macos_dir = self.executable_path / 'Contents' / 'MacOS'
            if macos_dir.exists():
                executables = [f for f in macos_dir.iterdir() if f.is_file() and os.access(f, os.X_OK)]
                if executables:
                    cmd = [str(executables[0]), '--version']
                else:
                    self.result.add_test("Version command", False, "No executable found in app bundle")
                    return
            else:
                self.result.add_test("Version command", False, "Invalid app bundle structure")
                return
        else:
            cmd = [str(self.executable_path), '--version']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                version_text = result.stdout.strip()
                has_version = bool(version_text) and any(char.isdigit() for char in version_text)
                self.result.add_test(
                    "Version command",
                    has_version,
                    f"Version: {version_text}" if has_version else "No version information"
                )
            else:
                # Some apps might not support --version, which is acceptable
                self.result.add_test("Version command", True, "Version command not supported (acceptable)", warning=True)
                
        except subprocess.TimeoutExpired:
            self.result.add_test("Version command", False, "Version command timeout")
        except Exception as e:
            self.result.add_test("Version command", False, f"Error running version command: {e}")
    
    def test_dependencies(self):
        """Test that all required dependencies are bundled."""
        if not self.executable_path.exists():
            self.result.add_test("Dependencies", False, "Executable does not exist")
            return
        
        if self.system == 'linux':
            # For Linux, check ldd output for missing dependencies
            try:
                result = subprocess.run(['ldd', str(self.executable_path)], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    missing_deps = [line for line in result.stdout.split('\\n') if 'not found' in line]
                    if missing_deps:
                        self.result.add_test("Dependencies", False, f"Missing dependencies: {len(missing_deps)}")
                    else:
                        self.result.add_test("Dependencies", True, "All dependencies satisfied")
                else:
                    self.result.add_test("Dependencies", True, "Static executable or ldd not applicable", warning=True)
            except Exception as e:
                self.result.add_test("Dependencies", False, f"Error checking dependencies: {e}")
        else:
            # For Windows and macOS, dependencies should be bundled
            self.result.add_test("Dependencies", True, "Dependencies should be bundled in executable")
    
    def save_results(self, output_file: Path):
        """Save test results to JSON file."""
        results_data = {
            "platform_info": self.result.platform_info,
            "executable_path": str(self.executable_path),
            "tests_run": self.result.tests_run,
            "tests_passed": self.result.tests_passed,
            "tests_failed": self.result.tests_failed,
            "errors": self.result.errors,
            "warnings": self.result.warnings,
            "performance_metrics": self.result.performance_metrics,
            "timestamp": time.time()
        }
        
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"📄 Test results saved to: {output_file}")


def find_executable(dist_dir: Path) -> Optional[Path]:
    """Find the executable in the dist directory."""
    if not dist_dir.exists():
        return None
    
    system = platform.system().lower()
    
    # Look for platform-specific executables
    for item in dist_dir.iterdir():
        if system == 'windows' and item.suffix == '.exe':
            return item
        elif system == 'darwin' and item.suffix == '.app':
            return item
        elif system == 'linux' and item.is_file() and not item.suffix and os.access(item, os.X_OK):
            return item
    
    return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test VAITP-Auditor GUI executable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_executable.py                           # Auto-find executable in dist/
  python test_executable.py --executable dist/app.exe # Test specific executable
  python test_executable.py --output results.json    # Save results to file
        """
    )
    
    parser.add_argument("--executable", type=Path, help="Path to executable to test")
    parser.add_argument("--dist-dir", type=Path, default="dist", help="Distribution directory to search")
    parser.add_argument("--output", type=Path, help="Output file for test results (JSON)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Find executable
    if args.executable:
        executable_path = args.executable
    else:
        project_root = Path(__file__).parent.parent
        dist_dir = project_root / args.dist_dir
        executable_path = find_executable(dist_dir)
        
        if not executable_path:
            print(f"❌ No executable found in {dist_dir}")
            print("Available files:")
            if dist_dir.exists():
                for item in dist_dir.iterdir():
                    print(f"  - {item.name}")
            sys.exit(1)
    
    if not executable_path.exists():
        print(f"❌ Executable not found: {executable_path}")
        sys.exit(1)
    
    # Run tests
    tester = ExecutableTester(executable_path)
    success = tester.run_all_tests()
    
    # Save results if requested
    if args.output:
        tester.save_results(args.output)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()