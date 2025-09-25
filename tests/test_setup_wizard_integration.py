"""
Integration tests for the Setup Wizard complete workflow.

Tests the complete Setup Wizard workflow from initialization through completion,
including all steps, validation, and session configuration creation.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import tempfile
import os
from pathlib import Path

# Mock CustomTkinter before importing GUI modules
sys.modules['customtkinter'] = MagicMock()

from vaitp_auditor.gui.setup_wizard import SetupWizard, NamingStep, DataSourceStep, ConfigurationStep, FinalizationStep
from vaitp_auditor.gui.models import GUIConfig
from vaitp_auditor.core.models import SessionConfig


class TestSetupWizardIntegration(unittest.TestCase):
    """Integration test cases for the complete Setup Wizard workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_parent = Mock()
        self.gui_config = GUIConfig()
        
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.generated_folder = os.path.join(self.temp_dir, "generated")
        self.expected_folder = os.path.join(self.temp_dir, "expected")
        os.makedirs(self.generated_folder)
        os.makedirs(self.expected_folder)
        
        # Create test files
        with open(os.path.join(self.generated_folder, "test1.py"), "w") as f:
            f.write("print('generated code')")
        with open(os.path.join(self.expected_folder, "test1.py"), "w") as f:
            f.write("print('expected code')")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_wizard_workflow_folders(self):
        """Test complete wizard workflow with folder data source."""
        # Create individual steps and test them
        mock_wizard = Mock()
        mock_wizard.steps = []
        mock_wizard.current_step = 0
        mock_wizard.show_error = Mock()
        
        # Test Step 1: Naming
        naming_step = NamingStep(mock_wizard)
        self._configure_naming_step(naming_step, "test_experiment")
        
        # Validate naming step
        self.assertTrue(naming_step.validate())
        naming_data = naming_step.get_data()
        self.assertEqual(naming_data['experiment_name'], "test_experiment")
        self.assertIn("test_experiment_", naming_data['session_id'])
        
        # Test Step 2: Data Source Selection
        data_source_step = DataSourceStep(mock_wizard)
        self._configure_data_source_step(data_source_step, "folders")
        
        # Validate data source step
        self.assertTrue(data_source_step.validate())
        data_source_data = data_source_step.get_data()
        self.assertEqual(data_source_data['data_source_type'], "folders")
        
        # Test Step 3: Configuration
        config_step = ConfigurationStep(mock_wizard)
        self._configure_folder_step(config_step, self.generated_folder, self.expected_folder)
        
        # Validate configuration step
        self.assertTrue(config_step.validate())
        config_data = config_step.get_data()
        self.assertEqual(config_data['generated_code_path'], self.generated_folder)
        self.assertEqual(config_data['expected_code_path'], self.expected_folder)
        
        # Test Step 4: Finalization
        finalization_step = FinalizationStep(mock_wizard)
        self._configure_finalization_step(finalization_step, 75, "excel")
        
        # Validate finalization step
        self.assertTrue(finalization_step.validate())
        finalization_data = finalization_step.get_data()
        self.assertEqual(finalization_data['sampling_percentage'], 75)
        self.assertEqual(finalization_data['output_format'], "excel")
        
        # Test complete configuration collection
        steps = [naming_step, data_source_step, config_step, finalization_step]
        complete_config = {}
        for step in steps:
            step_data = step.get_data()
            complete_config.update(step_data)
        
        # Verify complete configuration
        expected_keys = {
            'experiment_name', 'session_id', 'data_source_type',
            'generated_code_path', 'expected_code_path',
            'sampling_percentage', 'output_format'
        }
        self.assertTrue(expected_keys.issubset(complete_config.keys()))
        
        # Test session config creation
        session_config = SessionConfig(
            experiment_name=complete_config['experiment_name'],
            data_source_type=complete_config['data_source_type'],
            data_source_params={
                'generated_code_path': complete_config['generated_code_path'],
                'expected_code_path': complete_config['expected_code_path']
            },
            sample_percentage=float(complete_config['sampling_percentage']),
            output_format=complete_config['output_format']
        )
        
        # Verify session config is valid
        self.assertEqual(session_config.experiment_name, "test_experiment")
        self.assertEqual(session_config.data_source_type, "folders")
        self.assertEqual(session_config.sample_percentage, 75.0)
        self.assertEqual(session_config.output_format, "excel")
    
    def test_complete_wizard_workflow_sqlite(self):
        """Test complete wizard workflow with SQLite data source."""
        # Create individual steps and test them
        mock_wizard = Mock()
        mock_wizard.steps = []
        mock_wizard.current_step = 0
        mock_wizard.show_error = Mock()
        
        # Test Step 1: Naming
        naming_step = NamingStep(mock_wizard)
        self._configure_naming_step(naming_step, "sqlite_experiment")
        
        # Test Step 2: Data Source Selection
        data_source_step = DataSourceStep(mock_wizard)
        self._configure_data_source_step(data_source_step, "sqlite")
        
        # Test Step 3: Configuration
        config_step = ConfigurationStep(mock_wizard)
        # Mock the data source type method to return sqlite
        config_step._get_selected_data_source_type = Mock(return_value="sqlite")
        db_path = os.path.join(self.temp_dir, "test.db")
        self._configure_sqlite_step(config_step, db_path, "code_pairs", "id", "generated", "expected")
        
        # Test Step 4: Finalization
        finalization_step = FinalizationStep(mock_wizard)
        self._configure_finalization_step(finalization_step, 100, "csv")
        
        # Validate all steps
        steps = [naming_step, data_source_step, config_step, finalization_step]
        for step in steps:
            self.assertTrue(step.validate())
        
        # Test complete configuration collection
        complete_config = {}
        for step in steps:
            step_data = step.get_data()
            complete_config.update(step_data)
        
        # Verify SQLite-specific configuration
        self.assertEqual(complete_config['data_source_type'], "sqlite")
        self.assertEqual(complete_config['database_path'], db_path)
        self.assertEqual(complete_config['table_name'], "code_pairs")
        self.assertEqual(complete_config['identifier_column'], "id")
        self.assertEqual(complete_config['generated_code_column'], "generated")
        self.assertEqual(complete_config['expected_code_column'], "expected")
    
    def test_complete_wizard_workflow_excel(self):
        """Test complete wizard workflow with Excel data source."""
        # Create individual steps and test them
        mock_wizard = Mock()
        mock_wizard.steps = []
        mock_wizard.current_step = 0
        mock_wizard.show_error = Mock()
        
        # Test Step 1: Naming
        naming_step = NamingStep(mock_wizard)
        self._configure_naming_step(naming_step, "excel_experiment")
        
        # Test Step 2: Data Source Selection
        data_source_step = DataSourceStep(mock_wizard)
        self._configure_data_source_step(data_source_step, "excel")
        
        # Test Step 3: Configuration
        config_step = ConfigurationStep(mock_wizard)
        # Mock the data source type method to return excel
        config_step._get_selected_data_source_type = Mock(return_value="excel")
        excel_path = os.path.join(self.temp_dir, "test.xlsx")
        self._configure_excel_step(config_step, excel_path, "Sheet1", "ID", "Generated", "Expected")
        
        # Test Step 4: Finalization
        finalization_step = FinalizationStep(mock_wizard)
        self._configure_finalization_step(finalization_step, 50, "excel")
        
        # Validate all steps
        steps = [naming_step, data_source_step, config_step, finalization_step]
        for step in steps:
            self.assertTrue(step.validate())
        
        # Test complete configuration collection
        complete_config = {}
        for step in steps:
            step_data = step.get_data()
            complete_config.update(step_data)
        
        # Verify Excel-specific configuration
        self.assertEqual(complete_config['data_source_type'], "excel")
        self.assertEqual(complete_config['file_path'], excel_path)
        self.assertEqual(complete_config['sheet_name'], "Sheet1")
        self.assertEqual(complete_config['identifier_column'], "ID")
        self.assertEqual(complete_config['generated_code_column'], "Generated")
        self.assertEqual(complete_config['expected_code_column'], "Expected")
    
    def test_wizard_validation_failures(self):
        """Test wizard validation with various failure scenarios."""
        # Create individual steps and test validation failures
        mock_wizard = Mock()
        mock_wizard.steps = []
        mock_wizard.current_step = 0
        mock_wizard.show_error = Mock()
        
        # Test Step 1 validation failure (empty name)
        naming_step = NamingStep(mock_wizard)
        self._configure_naming_step(naming_step, "")
        self.assertFalse(naming_step.validate())
        
        # Test Step 1 validation failure (invalid characters)
        self._configure_naming_step(naming_step, "test@experiment")
        self.assertFalse(naming_step.validate())
        
        # Test Step 1 validation failure (too long)
        self._configure_naming_step(naming_step, "a" * 51)
        self.assertFalse(naming_step.validate())
        
        # Fix Step 1
        self._configure_naming_step(naming_step, "valid_experiment")
        self.assertTrue(naming_step.validate())
        
        # Test Step 3 validation failure (missing folder)
        config_step = ConfigurationStep(mock_wizard)
        self._configure_folder_step(config_step, "", "")
        self.assertFalse(config_step.validate())
        
        # Test Step 3 validation failure (non-existent folder)
        self._configure_folder_step(config_step, "/non/existent/path", "")
        self.assertFalse(config_step.validate())
        
        # Test Step 4 validation failure (invalid sampling)
        finalization_step = FinalizationStep(mock_wizard)
        self._configure_finalization_step(finalization_step, 0, "excel")
        self.assertFalse(finalization_step.validate())
        
        # Test Step 4 validation failure (invalid format)
        self._configure_finalization_step(finalization_step, 50, "invalid")
        self.assertFalse(finalization_step.validate())
    
    def test_wizard_step_data_collection(self):
        """Test that all wizard steps collect data correctly."""
        # Create individual steps and test data collection
        mock_wizard = Mock()
        mock_wizard.steps = []
        mock_wizard.current_step = 0
        mock_wizard.show_error = Mock()
        
        # Create and configure all steps
        naming_step = NamingStep(mock_wizard)
        data_source_step = DataSourceStep(mock_wizard)
        config_step = ConfigurationStep(mock_wizard)
        finalization_step = FinalizationStep(mock_wizard)
        
        self._configure_naming_step(naming_step, "callback_test")
        self._configure_data_source_step(data_source_step, "folders")
        self._configure_folder_step(config_step, self.generated_folder, self.expected_folder)
        self._configure_finalization_step(finalization_step, 100, "excel")
        
        # Collect data from all steps
        steps = [naming_step, data_source_step, config_step, finalization_step]
        complete_config = {}
        for step in steps:
            step_data = step.get_data()
            complete_config.update(step_data)
        
        # Verify complete configuration
        self.assertEqual(complete_config['experiment_name'], "callback_test")
        self.assertEqual(complete_config['data_source_type'], "folders")
        self.assertEqual(complete_config['sampling_percentage'], 100)
        self.assertEqual(complete_config['output_format'], "excel")
        self.assertEqual(complete_config['generated_code_path'], self.generated_folder)
        self.assertEqual(complete_config['expected_code_path'], self.expected_folder)
    
    def _setup_ctk_mocks(self, mock_ctk):
        """Set up CustomTkinter mocks."""
        # Create mock instances that behave like the real widgets
        mock_toplevel = Mock()
        mock_toplevel.winfo_children.return_value = []
        mock_toplevel.winfo_screenwidth.return_value = 1920
        mock_toplevel.winfo_screenheight.return_value = 1080
        mock_toplevel.winfo_x.return_value = 100
        mock_toplevel.winfo_y.return_value = 100
        mock_toplevel.winfo_width.return_value = 600
        mock_toplevel.winfo_height.return_value = 450
        
        mock_frame = Mock()
        mock_frame.winfo_children.return_value = []
        
        mock_widget = Mock()
        mock_widget.pack = Mock()
        mock_widget.configure = Mock()
        
        # Set up the CTk class mocks
        mock_ctk.CTkToplevel = Mock(return_value=mock_toplevel)
        mock_ctk.CTkFrame = Mock(return_value=mock_frame)
        mock_ctk.CTkLabel = Mock(return_value=mock_widget)
        mock_ctk.CTkEntry = Mock(return_value=mock_widget)
        mock_ctk.CTkButton = Mock(return_value=mock_widget)
        mock_ctk.CTkSegmentedButton = Mock(return_value=mock_widget)
        mock_ctk.CTkComboBox = Mock(return_value=mock_widget)
        mock_ctk.CTkSlider = Mock(return_value=mock_widget)
        mock_ctk.CTkRadioButton = Mock(return_value=mock_widget)
        mock_ctk.CTkTextbox = Mock(return_value=mock_widget)
        mock_ctk.CTkFont = Mock(return_value=Mock())
        
        # Mock variable classes
        mock_string_var = Mock()
        mock_string_var.get.return_value = ""
        mock_string_var.set = Mock()
        mock_ctk.StringVar = Mock(return_value=mock_string_var)
        
        mock_int_var = Mock()
        mock_int_var.get.return_value = 100
        mock_int_var.set = Mock()
        mock_ctk.IntVar = Mock(return_value=mock_int_var)
    
    def _configure_naming_step(self, step, experiment_name):
        """Configure naming step with test data."""
        mock_entry = Mock()
        mock_entry.get.return_value = experiment_name
        step.experiment_entry = mock_entry
    
    def _configure_data_source_step(self, step, data_source_type):
        """Configure data source step with test data."""
        mock_var = Mock()
        mock_var.get.return_value = data_source_type
        step.data_source_var = mock_var
    
    def _configure_folder_step(self, step, generated_path, expected_path):
        """Configure folder configuration step with test data."""
        mock_generated_var = Mock()
        mock_generated_var.get.return_value = generated_path
        step.generated_folder_var = mock_generated_var
        
        mock_expected_var = Mock()
        mock_expected_var.get.return_value = expected_path
        step.expected_folder_var = mock_expected_var
    
    def _configure_sqlite_step(self, step, db_path, table, id_col, gen_col, exp_col):
        """Configure SQLite configuration step with test data."""
        # Create a test SQLite database
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table} (
                    {id_col} TEXT PRIMARY KEY,
                    {gen_col} TEXT,
                    {exp_col} TEXT
                )
            ''')
            cursor.execute(f'''
                INSERT OR REPLACE INTO {table} ({id_col}, {gen_col}, {exp_col})
                VALUES ('test1', 'generated code', 'expected code')
            ''')
            conn.commit()
        
        mock_db_var = Mock()
        mock_db_var.get.return_value = db_path
        step.db_file_var = mock_db_var
        
        mock_table_var = Mock()
        mock_table_var.get.return_value = table
        step.table_var = mock_table_var
        
        mock_id_var = Mock()
        mock_id_var.get.return_value = id_col
        step.identifier_column_var = mock_id_var
        
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = gen_col
        step.generated_column_var = mock_gen_var
        
        mock_exp_var = Mock()
        mock_exp_var.get.return_value = exp_col
        step.expected_column_var = mock_exp_var
    
    def _configure_excel_step(self, step, file_path, sheet, id_col, gen_col, exp_col):
        """Configure Excel configuration step with test data."""
        # Create a test Excel file
        try:
            import pandas as pd
            df = pd.DataFrame({
                id_col: ['test1', 'test2'],
                gen_col: ['generated code 1', 'generated code 2'],
                exp_col: ['expected code 1', 'expected code 2']
            })
            df.to_excel(file_path, sheet_name=sheet, index=False)
        except ImportError:
            # If pandas is not available, create a CSV file instead
            import csv
            file_path = file_path.replace('.xlsx', '.csv')
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([id_col, gen_col, exp_col])
                writer.writerow(['test1', 'generated code 1', 'expected code 1'])
                writer.writerow(['test2', 'generated code 2', 'expected code 2'])
        
        mock_file_var = Mock()
        mock_file_var.get.return_value = file_path
        step.excel_file_var = mock_file_var
        
        mock_sheet_var = Mock()
        mock_sheet_var.get.return_value = sheet
        step.sheet_var = mock_sheet_var
        
        mock_id_var = Mock()
        mock_id_var.get.return_value = id_col
        step.excel_identifier_column_var = mock_id_var
        
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = gen_col
        step.excel_generated_column_var = mock_gen_var
        
        mock_exp_var = Mock()
        mock_exp_var.get.return_value = exp_col
        step.excel_expected_column_var = mock_exp_var
    
    def _configure_finalization_step(self, step, sampling_percentage, output_format):
        """Configure finalization step with test data."""
        mock_sampling_var = Mock()
        mock_sampling_var.get.return_value = sampling_percentage
        step.sampling_var = mock_sampling_var
        
        mock_format_var = Mock()
        mock_format_var.get.return_value = output_format
        step.output_format_var = mock_format_var


if __name__ == '__main__':
    unittest.main()