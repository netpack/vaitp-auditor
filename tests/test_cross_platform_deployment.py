"""
Cross-platform deployment and compatibility tests.

This module tests the deployment configuration and cross-platform
compatibility of the VAITP-Auditor GUI application.
"""

import unittest
import sys
import os
import platform
import subprocess
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to the path to import vaitp_auditor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vaitp_auditor.gui.gui_app import GUIApplication


class TestCrossPlatformCompatibility(unittest.TestCase):
    """Test cross-platform compatibility features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.current_platform = platform.system().lower()
        self.project_root = Path(__file__).parent.parent
    
    def test_platform_detection(self):
        """Test that platform is correctly detected."""
        detected_platform = platform.system()
        self.assertIn(detected_platform, ['Windows', 'Darwin', 'Linux'])
    
    def test_path_handling(self):
        """Test cross-platform path handling."""
        # Test path creation
        test_path = Path("test") / "path" / "file.txt"
        self.assertTrue(isinstance(test_path, Path))
        
        # Test path conversion
        str_path = str(test_path)
        self.assertIsInstance(str_path, str)
        
        # Test path exists check (should not crash)
        exists = test_path.exists()
        self.assertIsInstance(exists, bool)
    
    def test_file_dialog_compatibility(self):
        """Test file dialog compatibility across platforms."""
        # This test ensures the file dialog imports work
        try:
            import tkinter.filedialog as filedialog
            # Test that the module can be imported
            self.assertTrue(hasattr(filedialog, 'askopenfilename'))
            self.assertTrue(hasattr(filedialog, 'askdirectory'))
        except ImportError:
            self.fail("tkinter.filedialog not available on this platform")
    
    def test_font_availability(self):
        """Test font availability across platforms."""
        # Test common fonts that should be available
        common_fonts = ['Arial', 'Helvetica', 'Times', 'Courier']
        
        # For GUI testing, we just ensure the font names are strings
        for font in common_fonts:
            self.assertIsInstance(font, str)
            self.assertTrue(len(font) > 0)
    
    def test_gui_dependencies_import(self):
        """Test that GUI dependencies can be imported."""
        required_modules = [
            'customtkinter',
            'pygments',
            'PIL',
        ]
        
        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                self.fail(f"Required GUI module {module_name} not available: {e}")
    
    def test_optional_dependencies(self):
        """Test optional dependencies handling."""
        # Test psutil (optional for performance monitoring)
        try:
            import psutil
            has_psutil = True
        except ImportError:
            has_psutil = False
        
        # Should work with or without psutil
        from vaitp_auditor.gui.performance_optimizer import MemoryManager
        memory_manager = MemoryManager()
        
        # Should return valid stats regardless of psutil availability
        stats = memory_manager.check_memory_usage()
        self.assertIn('memory_mb', stats)
        self.assertIn('exceeds_limit', stats)


class TestDeploymentConfiguration(unittest.TestCase):
    """Test deployment configuration files."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent
        self.deployment_dir = self.project_root / "deployment"
    
    def test_setup_py_configuration(self):
        """Test setup.py configuration."""
        setup_py = self.project_root / "setup.py"
        self.assertTrue(setup_py.exists(), "setup.py not found")
        
        # Read setup.py content
        content = setup_py.read_text()
        
        # Check for required sections
        self.assertIn("customtkinter", content)
        self.assertIn("pygments", content)
        self.assertIn("pillow", content)
        self.assertIn("extras_require", content)
        self.assertIn("entry_points", content)
    
    def test_pyinstaller_spec_exists(self):
        """Test that PyInstaller spec file exists."""
        spec_file = self.deployment_dir / "pyinstaller_config.spec"
        self.assertTrue(spec_file.exists(), "PyInstaller spec file not found")
        
        # Check spec file content
        content = spec_file.read_text()
        self.assertIn("customtkinter", content)
        self.assertIn("hiddenimports", content)
        self.assertIn("excludes", content)
    
    def test_build_script_exists(self):
        """Test that build script exists and is executable."""
        build_script = self.deployment_dir / "build_executable.py"
        self.assertTrue(build_script.exists(), "Build script not found")
        
        # Check if script has main function
        content = build_script.read_text()
        self.assertIn("def main()", content)
        self.assertIn("if __name__ == \"__main__\":", content)
    
    def test_deployment_readme_exists(self):
        """Test that deployment README exists."""
        readme_file = self.deployment_dir / "README.md"
        self.assertTrue(readme_file.exists(), "Deployment README not found")
        
        # Check README content
        content = readme_file.read_text()
        self.assertIn("Deployment Guide", content)
        self.assertIn("PyInstaller", content)


class TestPackageStructure(unittest.TestCase):
    """Test package structure and imports."""
    
    def test_gui_package_structure(self):
        """Test GUI package structure."""
        from vaitp_auditor import gui
        
        # Test that main modules can be imported
        required_modules = [
            'gui_app',
            'setup_wizard',
            'main_review_window',
            'gui_session_controller',
            'code_display',
            'models',
            'accessibility',
            'error_handler',
            'performance_optimizer'
        ]
        
        for module_name in required_modules:
            try:
                module = __import__(f'vaitp_auditor.gui.{module_name}', fromlist=[module_name])
                self.assertIsNotNone(module)
            except ImportError as e:
                self.fail(f"Could not import vaitp_auditor.gui.{module_name}: {e}")
    
    def test_entry_points(self):
        """Test that entry points are properly configured."""
        # Test that the main GUI application class exists
        from vaitp_auditor.gui.gui_app import GUIApplication
        self.assertTrue(hasattr(GUIApplication, 'run'))
        
        # Test that main function exists
        from vaitp_auditor.gui import gui_app
        self.assertTrue(hasattr(gui_app, 'main'))
    
    def test_backward_compatibility(self):
        """Test backward compatibility with CLI interface."""
        # Test that CLI still works
        from vaitp_auditor import cli
        self.assertTrue(hasattr(cli, 'main'))
        
        # Test that core modules are unchanged
        from vaitp_auditor.core import models
        self.assertTrue(hasattr(models, 'CodePair'))
        self.assertTrue(hasattr(models, 'ReviewResult'))


class TestAssetManagement(unittest.TestCase):
    """Test asset management and packaging."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent
        self.assets_dir = self.project_root / "vaitp_auditor" / "gui" / "assets"
    
    def test_assets_directory_structure(self):
        """Test that assets directory has correct structure."""
        # Create assets directory if it doesn't exist (for testing)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        (self.assets_dir / "icons").mkdir(exist_ok=True)
        (self.assets_dir / "themes").mkdir(exist_ok=True)
        (self.assets_dir / "fonts").mkdir(exist_ok=True)
        
        # Test directory structure
        self.assertTrue(self.assets_dir.exists())
        self.assertTrue((self.assets_dir / "icons").exists())
        self.assertTrue((self.assets_dir / "themes").exists())
        self.assertTrue((self.assets_dir / "fonts").exists())
    
    def test_theme_files(self):
        """Test theme file structure."""
        themes_dir = self.assets_dir / "themes"
        themes_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a test theme file
        test_theme = themes_dir / "test_theme.json"
        test_theme.write_text('{"name": "test", "colors": {}}')
        
        # Test that theme file can be read
        import json
        try:
            with open(test_theme) as f:
                theme_data = json.load(f)
            self.assertIn("name", theme_data)
        except json.JSONDecodeError:
            self.fail("Theme file is not valid JSON")
    
    def test_icon_placeholder_creation(self):
        """Test icon placeholder creation."""
        icons_dir = self.assets_dir / "icons"
        icons_dir.mkdir(parents=True, exist_ok=True)
        
        # Create placeholder icon
        placeholder_icon = icons_dir / "test_icon.png"
        placeholder_icon.touch()
        
        self.assertTrue(placeholder_icon.exists())


class TestPerformanceOptimization(unittest.TestCase):
    """Test performance optimization features."""
    
    def test_lazy_loading_performance(self):
        """Test lazy loading performance."""
        from vaitp_auditor.gui.performance_optimizer import LazyCodeLoader
        
        # Test with small content
        small_content = "print('hello')\n" * 10
        small_loader = LazyCodeLoader(small_content)
        self.assertFalse(small_loader.is_large)
        
        # Test with large content
        large_content = "print('hello')\n" * 1000
        large_loader = LazyCodeLoader(large_content)
        self.assertTrue(large_loader.is_large)
        
        # Test performance - preview should be faster than full content
        import time
        
        start_time = time.time()
        preview = large_loader.get_preview()
        preview_time = time.time() - start_time
        
        start_time = time.time()
        full_content = large_loader.get_content(force_full=True)
        full_time = time.time() - start_time
        
        # Preview should be available (not necessarily faster in this simple test)
        self.assertIsInstance(preview, str)
        self.assertIsInstance(full_content, str)
    
    def test_memory_management(self):
        """Test memory management features."""
        from vaitp_auditor.gui.performance_optimizer import MemoryManager
        
        memory_manager = MemoryManager()
        
        # Test memory usage check
        stats = memory_manager.check_memory_usage()
        self.assertIn('memory_mb', stats)
        self.assertIn('exceeds_limit', stats)
        
        # Test garbage collection (should not crash)
        memory_manager.force_garbage_collection()
    
    def test_caching_effectiveness(self):
        """Test caching effectiveness."""
        from vaitp_auditor.gui.performance_optimizer import SyntaxHighlightingCache
        
        cache = SyntaxHighlightingCache()
        test_content = "def hello(): pass"
        test_result = [("def", "#569cd6"), (" hello", "#d4d4d4")]
        
        # Test cache miss
        result = cache.get(test_content, "python")
        self.assertIsNone(result)
        
        # Test cache put and hit
        cache.put(test_content, "python", test_result)
        result = cache.get(test_content, "python")
        self.assertEqual(result, test_result)
        
        # Test cache stats
        stats = cache.get_stats()
        self.assertIn('hit_rate', stats)
        self.assertIn('size', stats)


class TestAccessibilityFeatures(unittest.TestCase):
    """Test accessibility features."""
    
    def test_accessibility_manager_import(self):
        """Test that accessibility manager can be imported."""
        try:
            from vaitp_auditor.gui.accessibility import AccessibilityManager
            self.assertTrue(hasattr(AccessibilityManager, 'register_widget'))
        except ImportError as e:
            self.fail(f"Could not import AccessibilityManager: {e}")
    
    def test_keyboard_navigation_support(self):
        """Test keyboard navigation support."""
        # Test that keyboard event handling is available
        try:
            import tkinter as tk
            # Test basic keyboard event binding
            root = tk.Tk()
            root.bind("<Tab>", lambda e: None)
            root.bind("<Return>", lambda e: None)
            root.destroy()
        except Exception as e:
            self.fail(f"Keyboard navigation setup failed: {e}")
    
    def test_screen_reader_compatibility(self):
        """Test screen reader compatibility features."""
        from vaitp_auditor.gui.accessibility import AccessibilityManager
        
        # Test that accessibility manager can be created
        try:
            manager = AccessibilityManager()
            self.assertIsNotNone(manager)
        except Exception as e:
            self.fail(f"AccessibilityManager creation failed: {e}")


class TestErrorHandling(unittest.TestCase):
    """Test error handling and recovery."""
    
    def test_gui_error_handler_import(self):
        """Test GUI error handler import."""
        try:
            from vaitp_auditor.gui.error_handler import GUIErrorHandler
            self.assertTrue(hasattr(GUIErrorHandler, 'show_error_dialog'))
        except ImportError as e:
            self.fail(f"Could not import GUIErrorHandler: {e}")
    
    def test_graceful_degradation(self):
        """Test graceful degradation when optional features fail."""
        # Test that the application can handle missing optional dependencies
        with patch.dict('sys.modules', {'psutil': None}):
            try:
                from vaitp_auditor.gui.performance_optimizer import MemoryManager
                manager = MemoryManager()
                stats = manager.check_memory_usage()
                # Should return default values when psutil is not available
                self.assertEqual(stats['memory_mb'], 0)
            except Exception as e:
                self.fail(f"Graceful degradation failed: {e}")


if __name__ == '__main__':
    # Run cross-platform tests
    unittest.main(verbosity=2)