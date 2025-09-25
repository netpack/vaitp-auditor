# VAITP-Auditor GUI Testing Framework

This directory contains a comprehensive testing framework for the VAITP-Auditor GUI components, providing extensive testing capabilities for all GUI workflows, performance monitoring, cross-platform compatibility, and visual regression testing.

## Overview

The GUI testing framework consists of several key components:

**Note**: The test suite has been optimized to remove redundant and demo files while maintaining comprehensive coverage of all GUI functionality.

### 1. Core Testing Framework (`gui_test_framework.py`)
- **Mock CustomTkinter Environment**: Complete mock implementation of CustomTkinter for isolated testing
- **Widget Simulation**: Simulate user interactions (clicks, key presses, text input)
- **State Capture**: Capture and validate widget and window states
- **Screenshot Testing**: Mock screenshot capture and visual regression testing
- **Performance Monitoring**: Track response times, memory usage, and throughput
- **Test Execution**: Run test scenarios with comprehensive monitoring

### 2. Comprehensive Test Scenarios (`test_gui_comprehensive_scenarios.py`)
- **Setup Wizard Scenarios**: Complete wizard workflows for all data source types
- **Main Review Window Scenarios**: Code review workflows, verdict handling, progress tracking
- **Integration Scenarios**: Wizard-to-review transitions, session persistence
- **Error Handling Scenarios**: File dialog errors, database connection issues, memory constraints
- **Performance Scenarios**: Large file handling, rapid user interactions
- **Accessibility Scenarios**: Keyboard navigation, screen reader compatibility, high contrast mode

### 3. Integration and End-to-End Testing (`test_gui_integration_e2e.py`)
- **Cross-Platform Testing**: Font rendering, file path handling, dialog compatibility across Windows, macOS, and Linux
- **Performance Testing**: Startup performance, interaction responsiveness, large data handling
- **End-to-End Testing**: Complete user journeys from application start to session completion
- **CLI/GUI Compatibility**: Ensure session configs and reports work in both modes

### 4. Test Runner (`run_gui_tests.py`)
- **Unified Test Execution**: Run all test types from a single command
- **Flexible Test Selection**: Choose specific test types (unit, scenarios, integration, performance)
- **Comprehensive Reporting**: Generate detailed reports in JSON and human-readable formats
- **Performance Validation**: Validate against configurable performance thresholds



## Quick Start

### Running All Tests
```bash
python tests/run_gui_tests.py
```

### Running Specific Test Types
```bash
# Run only unit tests and scenarios (quick mode)
python tests/run_gui_tests.py --quick

# Run specific test types
python tests/run_gui_tests.py --test-types unit scenarios

# Run with verbose output
python tests/run_gui_tests.py --verbose
```

### Running Individual Components
```bash
# Run comprehensive scenarios
python tests/test_gui_comprehensive_scenarios.py

# Run integration tests
python tests/test_gui_integration_e2e.py
```

## Test Categories

### Unit Tests
- Individual GUI component testing
- Widget behavior validation
- State management verification
- Input/output validation

### Scenario Tests
- **Setup Wizard**: Complete configuration workflows
- **Main Review**: Code review and verdict workflows
- **Navigation**: Window transitions and user flows
- **Error Handling**: Error recovery and user feedback
- **Accessibility**: Keyboard navigation and screen reader support

### Integration Tests
- **Cross-Platform**: Compatibility across operating systems
- **Performance**: Response times, memory usage, throughput
- **End-to-End**: Complete user journeys
- **CLI/GUI Compatibility**: Shared functionality validation

### Performance Tests
- **Startup Performance**: Application initialization time
- **Interaction Performance**: User interaction response times
- **Large Data Performance**: Handling of large code files
- **Memory Usage**: Memory consumption monitoring
- **Throughput**: Items processed per second

## Framework Features

### Mock Environment
- Complete CustomTkinter mock implementation
- Isolated testing without GUI dependencies
- Widget simulation and state tracking
- Event handling and callback testing

### Widget Simulation
```python
# Create test window
window = framework.create_test_window("Test Window")

# Simulate user interactions
framework.simulate_button_click(button)
framework.simulate_user_input(entry, "test input")
framework.simulate_key_press(widget, 's', modifiers=['Ctrl'])
```

### State Capture and Validation
```python
# Capture widget state
state = framework.capture_widget_state(widget, "widget_name")

# Validate against expected state
framework.assert_widget_state(widget, {
    'properties': {'state': 'normal', 'text': 'expected_text'}
})
```

### Screenshot Testing
```python
# Capture screenshot
screenshot = framework.capture_screenshot(window, "test_screenshot", "Description")

# Compare with baseline
is_similar, score = framework.compare_screenshots("current", "baseline")
```

### Performance Monitoring
```python
# Measure performance
metrics = performance_tester.measure_startup_performance(framework)
valid, issues = performance_tester.validate_performance(metrics)
```

## Configuration

### Performance Thresholds
The framework includes configurable performance thresholds:
- **Startup Time**: < 5.0 seconds
- **Memory Usage**: < 200 MB
- **Response Time**: < 100 ms
- **Throughput**: > 10 items/second
- **CPU Usage**: < 50%

### Visual Regression
- **Similarity Threshold**: 95% (configurable)
- **Screenshot Format**: JSON metadata (mock implementation)
- **Baseline Management**: Automatic baseline creation and comparison

## Test Output

### Directory Structure
```
test_output_dir/
├── screenshots/           # Test screenshots
├── baselines/            # Baseline screenshots for comparison
├── logs/                 # Test execution logs
├── test_report.json      # Detailed test results
├── integration_test_report.json  # Integration test results
├── comprehensive_gui_test_report.json  # Complete test suite results
└── test_summary.txt      # Human-readable summary
```

### Report Contents
- **Test Results**: Pass/fail status, duration, error messages
- **Performance Metrics**: Memory usage, response times, throughput
- **Platform Information**: OS, architecture, Python version
- **Screenshots**: Visual regression test results
- **Recommendations**: Suggestions for addressing issues

## Extending the Framework

### Adding New Test Scenarios
```python
def test_new_feature():
    """Test a new GUI feature."""
    window = framework.create_test_window("New Feature Test")
    
    # Create and test widgets
    widget = framework.mock_ctk.CTkWidget(window)
    framework.simulate_user_input(widget, "test_value")
    
    # Validate results
    assert widget.get() == "test_value"

# Add to scenarios
scenarios['new_feature_test'] = test_new_feature
```

### Custom Performance Metrics
```python
def measure_custom_performance(framework):
    """Measure custom performance metrics."""
    start_time = time.time()
    
    # Perform operations
    # ...
    
    duration = time.time() - start_time
    return PerformanceMetrics(
        memory_usage_mb=get_memory_usage(),
        cpu_usage_percent=get_cpu_usage(),
        response_time_ms=duration * 1000,
        throughput_items_per_second=items / duration,
        startup_time_seconds=0.0
    )
```

### Platform-Specific Tests
```python
def test_platform_specific_feature():
    """Test platform-specific functionality."""
    platform = CrossPlatformTester().current_platform
    
    if platform == PlatformInfo.WINDOWS:
        # Windows-specific tests
        pass
    elif platform == PlatformInfo.MACOS:
        # macOS-specific tests
        pass
    elif platform == PlatformInfo.LINUX:
        # Linux-specific tests
        pass
```

## Best Practices

### Test Organization
- Group related tests into scenarios
- Use descriptive test names
- Include comprehensive error handling
- Validate both success and failure cases

### Performance Testing
- Set realistic performance thresholds
- Test with various data sizes
- Monitor memory usage over time
- Include stress testing scenarios

### Cross-Platform Testing
- Test on multiple operating systems
- Validate platform-specific behaviors
- Handle platform differences gracefully
- Use appropriate file path separators

### Accessibility Testing
- Test keyboard navigation thoroughly
- Validate screen reader compatibility
- Check high contrast mode support
- Ensure proper focus management

## Troubleshooting

### Common Issues
1. **Mock Environment Setup**: Ensure CustomTkinter is properly mocked
2. **Widget Simulation**: Check that widgets support the simulated operations
3. **State Capture**: Verify widget properties are accessible
4. **Performance Thresholds**: Adjust thresholds based on system capabilities

### Debug Mode
Enable verbose logging for detailed test execution information:
```bash
python tests/run_gui_tests.py --verbose
```

### Test Isolation
Each test runs in an isolated mock environment to prevent interference between tests.

## Requirements

### Dependencies
- Python 3.7+
- unittest (standard library)
- psutil (for performance monitoring)
- subprocess (for CLI integration testing)

### Optional Dependencies
- pytest (for enhanced unit testing)
- coverage (for test coverage analysis)

## Contributing

When adding new GUI components or features:

1. **Add Unit Tests**: Test individual component behavior
2. **Create Scenarios**: Add comprehensive workflow tests
3. **Update Integration Tests**: Ensure new features work with existing components
4. **Performance Testing**: Validate performance impact
5. **Cross-Platform Testing**: Test on multiple platforms
6. **Documentation**: Update test documentation

## Conclusion

The VAITP-Auditor GUI testing framework provides comprehensive testing capabilities for all GUI components and workflows. It ensures reliability, performance, and cross-platform compatibility while supporting continuous integration and automated testing practices.

For questions or issues, refer to the test output logs and reports for detailed information about test execution and results.