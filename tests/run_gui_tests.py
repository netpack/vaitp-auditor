"""
GUI Test Runner for VAITP-Auditor

This script runs the complete GUI test suite including unit tests,
integration tests, end-to-end tests, and generates comprehensive reports.
"""

import os
import sys
import time
import argparse
import subprocess
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.gui_test_framework import create_gui_test_framework, run_gui_test_suite
from tests.test_gui_comprehensive_scenarios import ComprehensiveGUITestScenarios
from tests.test_gui_integration_e2e import IntegrationTestSuite


class GUITestRunner:
    """
    Comprehensive GUI test runner for VAITP-Auditor.
    
    Coordinates execution of all GUI tests including:
    - Unit tests for individual components
    - Integration tests for component interactions
    - End-to-end tests for complete workflows
    - Performance and cross-platform testing
    """
    
    def __init__(self, output_dir: str = None, verbose: bool = False):
        """
        Initialize the GUI test runner.
        
        Args:
            output_dir: Directory for test outputs
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        
        # Set up output directory
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "gui_test_results")
        
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize test components
        self.framework = create_gui_test_framework(output_dir)
        self.scenarios = ComprehensiveGUITestScenarios(self.framework)
        self.integration_suite = IntegrationTestSuite(output_dir)
        
        # Test results
        self.results = {
            'unit_tests': {},
            'scenario_tests': {},
            'integration_tests': {},
            'summary': {}
        }
        
        self._log("GUI Test Runner initialized")
        self._log(f"Output directory: {output_dir}")
    
    def run_all_tests(self, test_types: List[str] = None) -> Dict[str, Any]:
        """
        Run all GUI tests.
        
        Args:
            test_types: List of test types to run. If None, runs all tests.
                       Options: 'unit', 'scenarios', 'integration', 'performance'
        
        Returns:
            Comprehensive test results dictionary
        """
        if test_types is None:
            test_types = ['unit', 'scenarios', 'integration', 'performance']
        
        start_time = time.time()
        
        self._log("Starting comprehensive GUI test suite")
        self._log(f"Test types: {', '.join(test_types)}")
        
        # Run unit tests
        if 'unit' in test_types:
            self._log("Running unit tests...")
            self.results['unit_tests'] = self._run_unit_tests()
        
        # Run scenario tests
        if 'scenarios' in test_types:
            self._log("Running scenario tests...")
            self.results['scenario_tests'] = self._run_scenario_tests()
        
        # Run integration tests
        if 'integration' in test_types:
            self._log("Running integration tests...")
            self.results['integration_tests'] = self._run_integration_tests()
        
        # Run performance tests
        if 'performance' in test_types:
            self._log("Running performance tests...")
            self.results['performance_tests'] = self._run_performance_tests()
        
        # Generate summary
        total_duration = time.time() - start_time
        self.results['summary'] = self._generate_summary(total_duration)
        
        # Save comprehensive report
        self._save_comprehensive_report()
        
        self._log(f"Test suite completed in {total_duration:.2f}s")
        return self.results
    
    def _run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests using pytest."""
        unit_test_results = {
            'status': 'running',
            'tests': [],
            'summary': {}
        }
        
        try:
            # Find all GUI unit test files
            test_files = self._find_gui_unit_tests()
            
            if not test_files:
                self._log("No GUI unit test files found")
                unit_test_results['status'] = 'skipped'
                return unit_test_results
            
            # Run each test file
            for test_file in test_files:
                self._log(f"Running unit tests in {test_file}")
                
                try:
                    # Run pytest on the test file
                    result = subprocess.run([
                        sys.executable, '-m', 'pytest', 
                        test_file, 
                        '-v', 
                        '--tb=short',
                        f'--junitxml={self.output_dir}/unit_test_{Path(test_file).stem}.xml'
                    ], capture_output=True, text=True, timeout=300)
                    
                    test_result = {
                        'file': test_file,
                        'returncode': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'success': result.returncode == 0
                    }
                    
                    unit_test_results['tests'].append(test_result)
                    
                    if self.verbose:
                        self._log(f"Unit test output for {test_file}:")
                        self._log(result.stdout)
                        if result.stderr:
                            self._log(f"Errors: {result.stderr}")
                
                except subprocess.TimeoutExpired:
                    self._log(f"Unit test timeout for {test_file}")
                    unit_test_results['tests'].append({
                        'file': test_file,
                        'returncode': -1,
                        'error': 'timeout',
                        'success': False
                    })
                
                except Exception as e:
                    self._log(f"Error running unit tests for {test_file}: {e}")
                    unit_test_results['tests'].append({
                        'file': test_file,
                        'returncode': -1,
                        'error': str(e),
                        'success': False
                    })
            
            # Calculate summary
            total_tests = len(unit_test_results['tests'])
            passed_tests = len([t for t in unit_test_results['tests'] if t['success']])
            
            unit_test_results['summary'] = {
                'total': total_tests,
                'passed': passed_tests,
                'failed': total_tests - passed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0
            }
            
            unit_test_results['status'] = 'completed'
            
        except Exception as e:
            self._log(f"Error in unit test execution: {e}")
            unit_test_results['status'] = 'error'
            unit_test_results['error'] = str(e)
        
        return unit_test_results
    
    def _run_scenario_tests(self) -> Dict[str, Any]:
        """Run comprehensive scenario tests."""
        scenario_results = {
            'status': 'running',
            'scenarios': {},
            'summary': {}
        }
        
        try:
            # Get all scenarios
            all_scenarios = self.scenarios.create_all_scenarios()
            
            self._log(f"Running {len(all_scenarios)} scenario tests")
            
            # Run each scenario
            for scenario_name, scenario_function in all_scenarios.items():
                self._log(f"Running scenario: {scenario_name}")
                
                try:
                    result = self.framework.run_test_scenario(scenario_name, scenario_function)
                    
                    scenario_results['scenarios'][scenario_name] = {
                        'success': result.state.value == 'passed',
                        'duration': result.duration,
                        'error_message': result.error_message,
                        'performance_metrics': result.performance_metrics
                    }
                    
                except Exception as e:
                    self._log(f"Error in scenario {scenario_name}: {e}")
                    scenario_results['scenarios'][scenario_name] = {
                        'success': False,
                        'duration': 0,
                        'error_message': str(e),
                        'performance_metrics': {}
                    }
            
            # Calculate summary
            total_scenarios = len(scenario_results['scenarios'])
            passed_scenarios = len([s for s in scenario_results['scenarios'].values() if s['success']])
            
            scenario_results['summary'] = {
                'total': total_scenarios,
                'passed': passed_scenarios,
                'failed': total_scenarios - passed_scenarios,
                'success_rate': passed_scenarios / total_scenarios if total_scenarios > 0 else 0,
                'total_duration': sum(s['duration'] for s in scenario_results['scenarios'].values())
            }
            
            scenario_results['status'] = 'completed'
            
        except Exception as e:
            self._log(f"Error in scenario test execution: {e}")
            scenario_results['status'] = 'error'
            scenario_results['error'] = str(e)
        
        return scenario_results
    
    def _run_integration_tests(self) -> Dict[str, Any]:
        """Run integration and end-to-end tests."""
        integration_results = {
            'status': 'running',
            'tests': {},
            'summary': {}
        }
        
        try:
            # Run integration test suite
            self._log("Running integration test suite")
            report = self.integration_suite.run_all_tests()
            
            integration_results['tests'] = report
            integration_results['summary'] = report.get('summary', {})
            integration_results['status'] = 'completed'
            
        except Exception as e:
            self._log(f"Error in integration test execution: {e}")
            integration_results['status'] = 'error'
            integration_results['error'] = str(e)
        
        return integration_results
    
    def _run_performance_tests(self) -> Dict[str, Any]:
        """Run performance-specific tests."""
        performance_results = {
            'status': 'running',
            'tests': {},
            'summary': {}
        }
        
        try:
            # Run performance measurements
            performance_tester = self.integration_suite.performance_tester
            
            # Startup performance
            startup_metrics = performance_tester.measure_startup_performance(self.framework)
            startup_valid, startup_issues = performance_tester.validate_performance(startup_metrics)
            
            performance_results['tests']['startup'] = {
                'metrics': {
                    'memory_usage_mb': startup_metrics.memory_usage_mb,
                    'cpu_usage_percent': startup_metrics.cpu_usage_percent,
                    'startup_time_seconds': startup_metrics.startup_time_seconds
                },
                'valid': startup_valid,
                'issues': startup_issues
            }
            
            # Interaction performance
            interaction_metrics = performance_tester.measure_interaction_performance(self.framework)
            interaction_valid, interaction_issues = performance_tester.validate_performance(interaction_metrics)
            
            performance_results['tests']['interaction'] = {
                'metrics': {
                    'response_time_ms': interaction_metrics.response_time_ms,
                    'throughput_items_per_second': interaction_metrics.throughput_items_per_second
                },
                'valid': interaction_valid,
                'issues': interaction_issues
            }
            
            # Large data performance
            large_data_metrics = performance_tester.measure_large_data_performance(self.framework)
            large_data_valid, large_data_issues = performance_tester.validate_performance(large_data_metrics)
            
            performance_results['tests']['large_data'] = {
                'metrics': {
                    'memory_usage_mb': large_data_metrics.memory_usage_mb,
                    'response_time_ms': large_data_metrics.response_time_ms
                },
                'valid': large_data_valid,
                'issues': large_data_issues
            }
            
            # Calculate summary
            all_tests = performance_results['tests'].values()
            total_tests = len(all_tests)
            passed_tests = len([t for t in all_tests if t['valid']])
            
            performance_results['summary'] = {
                'total': total_tests,
                'passed': passed_tests,
                'failed': total_tests - passed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0
            }
            
            performance_results['status'] = 'completed'
            
        except Exception as e:
            self._log(f"Error in performance test execution: {e}")
            performance_results['status'] = 'error'
            performance_results['error'] = str(e)
        
        return performance_results
    
    def _find_gui_unit_tests(self) -> List[str]:
        """Find all GUI unit test files."""
        test_files = []
        test_dir = os.path.dirname(__file__)
        
        # Look for GUI-related test files
        gui_test_patterns = [
            'test_gui_*.py',
            'test_*_gui.py',
            'test_main_review_window.py',
            'test_setup_wizard.py',
            'test_accessibility.py'
        ]
        
        for pattern in gui_test_patterns:
            import glob
            matches = glob.glob(os.path.join(test_dir, pattern))
            test_files.extend(matches)
        
        # Remove duplicates and sort
        test_files = sorted(list(set(test_files)))
        
        return test_files
    
    def _generate_summary(self, total_duration: float) -> Dict[str, Any]:
        """Generate overall test summary."""
        summary = {
            'total_duration': total_duration,
            'timestamp': time.time(),
            'test_types': {},
            'overall': {}
        }
        
        # Summarize each test type
        total_tests = 0
        total_passed = 0
        
        for test_type, results in self.results.items():
            if test_type == 'summary':
                continue
            
            if 'summary' in results and results['summary']:
                type_summary = results['summary']
                summary['test_types'][test_type] = type_summary
                
                total_tests += type_summary.get('total', 0)
                total_passed += type_summary.get('passed', 0)
        
        # Overall summary
        summary['overall'] = {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_tests - total_passed,
            'overall_success_rate': total_passed / total_tests if total_tests > 0 else 0
        }
        
        return summary
    
    def _save_comprehensive_report(self):
        """Save comprehensive test report."""
        report_file = os.path.join(self.output_dir, 'comprehensive_gui_test_report.json')
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self._log(f"Comprehensive report saved to: {report_file}")
        
        # Also save a human-readable summary
        summary_file = os.path.join(self.output_dir, 'test_summary.txt')
        self._save_text_summary(summary_file)
    
    def _save_text_summary(self, filename: str):
        """Save human-readable test summary."""
        with open(filename, 'w') as f:
            f.write("VAITP-Auditor GUI Test Suite Results\n")
            f.write("=" * 50 + "\n\n")
            
            # Overall summary
            if 'summary' in self.results and 'overall' in self.results['summary']:
                overall = self.results['summary']['overall']
                f.write(f"Overall Results:\n")
                f.write(f"  Total Tests: {overall['total_tests']}\n")
                f.write(f"  Passed: {overall['total_passed']}\n")
                f.write(f"  Failed: {overall['total_failed']}\n")
                f.write(f"  Success Rate: {overall['overall_success_rate']:.1%}\n")
                f.write(f"  Duration: {self.results['summary']['total_duration']:.2f}s\n\n")
            
            # Test type summaries
            if 'summary' in self.results and 'test_types' in self.results['summary']:
                f.write("Results by Test Type:\n")
                for test_type, summary in self.results['summary']['test_types'].items():
                    f.write(f"  {test_type.title()}:\n")
                    f.write(f"    Total: {summary.get('total', 0)}\n")
                    f.write(f"    Passed: {summary.get('passed', 0)}\n")
                    f.write(f"    Success Rate: {summary.get('success_rate', 0):.1%}\n")
                    if 'total_duration' in summary:
                        f.write(f"    Duration: {summary['total_duration']:.2f}s\n")
                    f.write("\n")
            
            # Performance summary
            if 'performance_tests' in self.results and self.results['performance_tests'].get('status') == 'completed':
                f.write("Performance Test Results:\n")
                perf_tests = self.results['performance_tests']['tests']
                
                for test_name, test_data in perf_tests.items():
                    f.write(f"  {test_name.title()}:\n")
                    f.write(f"    Valid: {test_data['valid']}\n")
                    
                    metrics = test_data['metrics']
                    for metric, value in metrics.items():
                        f.write(f"    {metric}: {value}\n")
                    
                    if test_data['issues']:
                        f.write(f"    Issues: {'; '.join(test_data['issues'])}\n")
                    f.write("\n")
        
        self._log(f"Text summary saved to: {filename}")
    
    def _log(self, message: str):
        """Log a message."""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        if self.verbose:
            print(log_message)
        
        # Also save to log file
        log_file = os.path.join(self.output_dir, 'test_runner.log')
        with open(log_file, 'a') as f:
            f.write(log_message + '\n')


def main():
    """Main entry point for GUI test runner."""
    parser = argparse.ArgumentParser(description='VAITP-Auditor GUI Test Runner')
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        help='Output directory for test results'
    )
    
    parser.add_argument(
        '--test-types', '-t',
        nargs='+',
        choices=['unit', 'scenarios', 'integration', 'performance'],
        default=['unit', 'scenarios', 'integration', 'performance'],
        help='Types of tests to run'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run only essential tests (unit and scenarios)'
    )
    
    args = parser.parse_args()
    
    # Adjust test types for quick mode
    if args.quick:
        args.test_types = ['unit', 'scenarios']
    
    # Create test runner
    runner = GUITestRunner(
        output_dir=args.output_dir,
        verbose=args.verbose
    )
    
    # Run tests
    print("VAITP-Auditor GUI Test Suite")
    print("=" * 40)
    print(f"Test types: {', '.join(args.test_types)}")
    print(f"Output directory: {runner.output_dir}")
    print()
    
    try:
        results = runner.run_all_tests(args.test_types)
        
        # Print summary
        if 'summary' in results and 'overall' in results['summary']:
            overall = results['summary']['overall']
            print(f"\nTest Results Summary:")
            print(f"Total Tests: {overall['total_tests']}")
            print(f"Passed: {overall['total_passed']}")
            print(f"Failed: {overall['total_failed']}")
            print(f"Success Rate: {overall['overall_success_rate']:.1%}")
            print(f"Duration: {results['summary']['total_duration']:.2f}s")
        
        # Exit with appropriate code
        if results['summary']['overall']['overall_success_rate'] == 1.0:
            print("\nAll tests passed! ✅")
            sys.exit(0)
        else:
            print(f"\nSome tests failed. Check {runner.output_dir} for details. ❌")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        print(f"\nError running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()