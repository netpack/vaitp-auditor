"""
Unit tests for the Setup Wizard GUI component.

Tests the SetupWizard class and related step classes for proper functionality,
navigation, validation, and data collection.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from datetime import datetime

# Mock CustomTkinter before importing GUI modules
sys.modules['customtkinter'] = MagicMock()

from vaitp_auditor.gui.setup_wizard import SetupWizard, NamingStep, DataSourceStep, ConfigurationStep, FinalizationStep, SetupStep, SessionResumptionStep
from vaitp_auditor.gui.models import GUIConfig


class TestSetupStep(unittest.TestCase):
    """Test cases for the abstract SetupStep class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_wizard = Mock()
        
        # Create a concrete implementation for testing
        class ConcreteStep(SetupStep):
            def create_widgets(self, parent):
                pass
            
            def validate(self):
                return True
            
            def get_data(self):
                return {"test": "data"}
        
        self.step = ConcreteStep(self.mock_wizard)
    
    def test_step_initialization(self):
        """Test SetupStep initialization."""
        self.assertEqual(self.step.wizard, self.mock_wizard)
        self.assertIsNone(self.step.frame)
        self.assertIsNotNone(self.step.logger)
    
    def test_abstract_methods_implemented(self):
        """Test that concrete step implements abstract methods."""
        # These should not raise NotImplementedError
        self.step.create_widgets(Mock())
        self.assertTrue(self.step.validate())
        self.assertEqual(self.step.get_data(), {"test": "data"})
    
    def test_optional_methods(self):
        """Test optional methods have default implementations."""
        # These should not raise exceptions
        self.step.on_show()
        self.step.on_hide()


class TestNamingStep(unittest.TestCase):
    """Test cases for the NamingStep class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_wizard = Mock()
        self.step = NamingStep(self.mock_wizard)
    
    def test_naming_step_initialization(self):
        """Test NamingStep initialization."""
        self.assertEqual(self.step.wizard, self.mock_wizard)
        self.assertIsNone(self.step.experiment_entry)
        self.assertIsNone(self.step.preview_label)
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_create_widgets(self, mock_ctk):
        """Test widget creation for naming step."""
        mock_parent = Mock()
        mock_ctk.CTkLabel.return_value = Mock()
        mock_ctk.CTkFrame.return_value = Mock()
        mock_ctk.CTkEntry.return_value = Mock()
        mock_ctk.CTkFont.return_value = Mock()
        
        self.step.create_widgets(mock_parent)
        
        # Verify widgets were created
        self.assertIsNotNone(self.step.experiment_entry)
        self.assertIsNotNone(self.step.preview_label)
        
        # Verify CTk components were called
        self.assertTrue(mock_ctk.CTkLabel.called)
        self.assertTrue(mock_ctk.CTkFrame.called)
        self.assertTrue(mock_ctk.CTkEntry.called)
    
    def test_generate_session_id_empty_name(self):
        """Test session ID generation with empty experiment name."""
        session_id = self.step._generate_session_id("")
        
        # Should use default name and include timestamp
        self.assertTrue(session_id.startswith("unnamed_experiment_"))
        self.assertRegex(session_id, r"unnamed_experiment_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}")
    
    def test_generate_session_id_valid_name(self):
        """Test session ID generation with valid experiment name."""
        test_name = "test_experiment"
        session_id = self.step._generate_session_id(test_name)
        
        # Should use provided name and include timestamp
        self.assertTrue(session_id.startswith("test_experiment_"))
        self.assertRegex(session_id, r"test_experiment_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}")
    
    def test_generate_session_id_invalid_characters(self):
        """Test session ID generation with invalid characters."""
        test_name = "test@experiment#123"
        session_id = self.step._generate_session_id(test_name)
        
        # Should clean invalid characters
        self.assertTrue(session_id.startswith("testexperiment123_"))
    
    def test_generate_session_id_only_invalid_characters(self):
        """Test session ID generation with only invalid characters."""
        test_name = "@#$%^&*()"
        session_id = self.step._generate_session_id(test_name)
        
        # Should fall back to default name
        self.assertTrue(session_id.startswith("unnamed_experiment_"))
    
    def test_validate_empty_name(self):
        """Test validation with empty experiment name."""
        # Mock the entry widget
        mock_entry = Mock()
        mock_entry.get.return_value = ""
        self.step.experiment_entry = mock_entry
        
        result = self.step.validate()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Please enter an experiment name.")
    
    def test_validate_whitespace_only_name(self):
        """Test validation with whitespace-only experiment name."""
        mock_entry = Mock()
        mock_entry.get.return_value = "   "
        self.step.experiment_entry = mock_entry
        
        result = self.step.validate()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Please enter an experiment name.")
    
    def test_validate_invalid_characters(self):
        """Test validation with invalid characters."""
        mock_entry = Mock()
        mock_entry.get.return_value = "test@experiment"
        self.step.experiment_entry = mock_entry
        
        result = self.step.validate()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with(
            "Experiment name can only contain letters, numbers, spaces, hyphens, and underscores."
        )
    
    def test_validate_too_long_name(self):
        """Test validation with name that's too long."""
        mock_entry = Mock()
        mock_entry.get.return_value = "a" * 51  # 51 characters
        self.step.experiment_entry = mock_entry
        
        result = self.step.validate()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Experiment name must be 50 characters or less.")
    
    def test_validate_valid_name(self):
        """Test validation with valid experiment name."""
        mock_entry = Mock()
        mock_entry.get.return_value = "valid_experiment_name"
        self.step.experiment_entry = mock_entry
        
        result = self.step.validate()
        
        self.assertTrue(result)
        self.mock_wizard.show_error.assert_not_called()
    
    def test_validate_valid_name_with_spaces_and_hyphens(self):
        """Test validation with valid name containing spaces and hyphens."""
        mock_entry = Mock()
        mock_entry.get.return_value = "valid experiment-name_123"
        self.step.experiment_entry = mock_entry
        
        result = self.step.validate()
        
        self.assertTrue(result)
        self.mock_wizard.show_error.assert_not_called()
    
    def test_get_data_no_entry(self):
        """Test get_data when entry widget is None."""
        self.step.experiment_entry = None
        
        result = self.step.get_data()
        
        self.assertEqual(result, {})
    
    def test_get_data_with_entry(self):
        """Test get_data with valid entry widget."""
        mock_entry = Mock()
        mock_entry.get.return_value = "test_experiment"
        self.step.experiment_entry = mock_entry
        
        result = self.step.get_data()
        
        self.assertIn("experiment_name", result)
        self.assertIn("session_id", result)
        self.assertEqual(result["experiment_name"], "test_experiment")
        self.assertTrue(result["session_id"].startswith("test_experiment_"))
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_update_preview(self, mock_ctk):
        """Test real-time preview update."""
        # Setup mock widgets
        mock_entry = Mock()
        mock_entry.get.return_value = "test_name"
        mock_label = Mock()
        
        self.step.experiment_entry = mock_entry
        self.step.preview_label = mock_label
        
        self.step._update_preview()
        
        # Verify label was updated
        mock_label.configure.assert_called_once()
        args, kwargs = mock_label.configure.call_args
        self.assertIn("text", kwargs)
        self.assertTrue(kwargs["text"].startswith("test_name_"))


class TestDataSourceStep(unittest.TestCase):
    """Test cases for the DataSourceStep class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_wizard = Mock()
        self.step = DataSourceStep(self.mock_wizard)
    
    def test_data_source_step_initialization(self):
        """Test DataSourceStep initialization."""
        self.assertEqual(self.step.wizard, self.mock_wizard)
        self.assertIsNone(self.step.data_source_var)
        self.assertIsNone(self.step.segmented_button)
        self.assertIsNotNone(self.step.available_types)
        
        # Verify available types are loaded from factory
        expected_types = {'folders': 'File System Folders', 'sqlite': 'SQLite Database', 'excel': 'Excel/CSV File'}
        self.assertEqual(self.step.available_types, expected_types)
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_create_widgets(self, mock_ctk):
        """Test widget creation for data source selection step."""
        mock_parent = Mock()
        mock_description_frame = Mock()
        mock_description_frame.winfo_children.return_value = []  # Empty list for cleanup
        
        mock_ctk.CTkLabel.return_value = Mock()
        mock_ctk.CTkFrame.return_value = mock_description_frame
        mock_ctk.CTkSegmentedButton.return_value = Mock()
        mock_ctk.StringVar.return_value = Mock()
        mock_ctk.CTkFont.return_value = Mock()
        
        self.step.create_widgets(mock_parent)
        
        # Verify widgets were created
        self.assertIsNotNone(self.step.data_source_var)
        self.assertIsNotNone(self.step.segmented_button)
        
        # Verify CTk components were called
        self.assertTrue(mock_ctk.CTkLabel.called)
        self.assertTrue(mock_ctk.CTkFrame.called)
        self.assertTrue(mock_ctk.CTkSegmentedButton.called)
        self.assertTrue(mock_ctk.StringVar.called)
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_segmented_button_configuration(self, mock_ctk):
        """Test segmented button is configured with correct values."""
        mock_parent = Mock()
        mock_string_var = Mock()
        mock_segmented_button = Mock()
        mock_description_frame = Mock()
        mock_description_frame.winfo_children.return_value = []  # Empty list for cleanup
        
        mock_ctk.StringVar.return_value = mock_string_var
        mock_ctk.CTkSegmentedButton.return_value = mock_segmented_button
        mock_ctk.CTkLabel.return_value = Mock()
        mock_ctk.CTkFrame.return_value = mock_description_frame
        mock_ctk.CTkFont.return_value = Mock()
        
        self.step.create_widgets(mock_parent)
        
        # Verify segmented button was created with correct parameters
        mock_ctk.CTkSegmentedButton.assert_called_once()
        call_args = mock_ctk.CTkSegmentedButton.call_args
        
        # Check that values parameter contains the data source keys
        self.assertIn('values', call_args.kwargs)
        values = call_args.kwargs['values']
        self.assertEqual(set(values), {'folders', 'sqlite', 'excel'})
        
        # Check that variable and command are set
        self.assertIn('variable', call_args.kwargs)
        self.assertIn('command', call_args.kwargs)
        
        # Verify initial selection is set to folders
        mock_segmented_button.set.assert_called_with("folders")
    
    def test_on_data_source_changed(self):
        """Test data source selection change handler."""
        self.step._update_description = Mock()
        
        self.step._on_data_source_changed("sqlite")
        
        # Verify description update was called
        self.step._update_description.assert_called_once()
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_update_description_folders(self, mock_ctk):
        """Test description update for folders data source."""
        # Setup mocks
        mock_frame = Mock()
        mock_frame.winfo_children.return_value = []
        mock_var = Mock()
        mock_var.get.return_value = "folders"
        
        self.step.description_frame = mock_frame
        self.step.data_source_var = mock_var
        
        mock_ctk.CTkLabel.return_value = Mock()
        mock_ctk.CTkFont.return_value = Mock()
        
        self.step._update_description()
        
        # Verify labels were created
        self.assertTrue(mock_ctk.CTkLabel.called)
        
        # Check that the description contains folder-specific text
        label_calls = mock_ctk.CTkLabel.call_args_list
        description_call = None
        for call in label_calls:
            if 'text' in call.kwargs and 'file system folders' in call.kwargs['text'].lower():
                description_call = call
                break
        
        self.assertIsNotNone(description_call, "Folder description not found in label calls")
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_update_description_sqlite(self, mock_ctk):
        """Test description update for SQLite data source."""
        # Setup mocks
        mock_frame = Mock()
        mock_frame.winfo_children.return_value = []
        mock_var = Mock()
        mock_var.get.return_value = "sqlite"
        
        self.step.description_frame = mock_frame
        self.step.data_source_var = mock_var
        
        mock_ctk.CTkLabel.return_value = Mock()
        mock_ctk.CTkFont.return_value = Mock()
        
        self.step._update_description()
        
        # Verify labels were created
        self.assertTrue(mock_ctk.CTkLabel.called)
        
        # Check that the description contains SQLite-specific text
        label_calls = mock_ctk.CTkLabel.call_args_list
        description_call = None
        for call in label_calls:
            if 'text' in call.kwargs and 'sqlite database' in call.kwargs['text'].lower():
                description_call = call
                break
        
        self.assertIsNotNone(description_call, "SQLite description not found in label calls")
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_update_description_excel(self, mock_ctk):
        """Test description update for Excel data source."""
        # Setup mocks
        mock_frame = Mock()
        mock_frame.winfo_children.return_value = []
        mock_var = Mock()
        mock_var.get.return_value = "excel"
        
        self.step.description_frame = mock_frame
        self.step.data_source_var = mock_var
        
        mock_ctk.CTkLabel.return_value = Mock()
        mock_ctk.CTkFont.return_value = Mock()
        
        self.step._update_description()
        
        # Verify labels were created
        self.assertTrue(mock_ctk.CTkLabel.called)
        
        # Check that the description contains Excel-specific text
        label_calls = mock_ctk.CTkLabel.call_args_list
        description_call = None
        for call in label_calls:
            if 'text' in call.kwargs and 'excel' in call.kwargs['text'].lower():
                description_call = call
                break
        
        self.assertIsNotNone(description_call, "Excel description not found in label calls")
    
    def test_validate_no_variable(self):
        """Test validation when data_source_var is None."""
        self.step.data_source_var = None
        
        result = self.step.validate()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Please select a data source type.")
    
    @patch('vaitp_auditor.data_sources.factory.DataSourceFactory.validate_source_type')
    def test_validate_invalid_type(self, mock_validate):
        """Test validation with invalid data source type."""
        mock_validate.return_value = False
        
        mock_var = Mock()
        mock_var.get.return_value = "invalid_type"
        self.step.data_source_var = mock_var
        
        result = self.step.validate()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Invalid data source type: invalid_type")
        mock_validate.assert_called_with("invalid_type")
    
    @patch('vaitp_auditor.data_sources.factory.DataSourceFactory.validate_source_type')
    def test_validate_valid_type(self, mock_validate):
        """Test validation with valid data source type."""
        mock_validate.return_value = True
        
        mock_var = Mock()
        mock_var.get.return_value = "folders"
        self.step.data_source_var = mock_var
        
        result = self.step.validate()
        
        self.assertTrue(result)
        self.mock_wizard.show_error.assert_not_called()
        mock_validate.assert_called_with("folders")
    
    def test_get_data_no_variable(self):
        """Test get_data when data_source_var is None."""
        self.step.data_source_var = None
        
        result = self.step.get_data()
        
        self.assertEqual(result, {})
    
    def test_get_data_with_variable(self):
        """Test get_data with valid data_source_var."""
        mock_var = Mock()
        mock_var.get.return_value = "sqlite"
        self.step.data_source_var = mock_var
        
        result = self.step.get_data()
        
        self.assertEqual(result, {"data_source_type": "sqlite"})
    
    def test_get_data_all_types(self):
        """Test get_data returns correct data for all supported types."""
        mock_var = Mock()
        self.step.data_source_var = mock_var
        
        for source_type in ['folders', 'sqlite', 'excel']:
            mock_var.get.return_value = source_type
            result = self.step.get_data()
            self.assertEqual(result, {"data_source_type": source_type})
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_description_frame_cleanup(self, mock_ctk):
        """Test that description frame is properly cleaned up when updating."""
        # Setup mocks
        mock_widget1 = Mock()
        mock_widget2 = Mock()
        mock_frame = Mock()
        mock_frame.winfo_children.return_value = [mock_widget1, mock_widget2]
        mock_var = Mock()
        mock_var.get.return_value = "folders"
        
        self.step.description_frame = mock_frame
        self.step.data_source_var = mock_var
        
        mock_ctk.CTkLabel.return_value = Mock()
        mock_ctk.CTkFont.return_value = Mock()
        
        self.step._update_description()
        
        # Verify old widgets were destroyed
        mock_widget1.destroy.assert_called_once()
        mock_widget2.destroy.assert_called_once()


class TestSetupWizardSteps(unittest.TestCase):
    """Test cases for SetupWizard step creation."""
    
    def test_create_steps_includes_data_source_step(self):
        """Test that _create_steps includes both NamingStep and DataSourceStep."""
        # Test the step creation logic by examining the step classes directly
        # This verifies that DataSourceStep is properly integrated
        
        # Create mock wizard
        mock_wizard = Mock()
        
        # Create instances of each step
        naming_step = NamingStep(mock_wizard)
        data_source_step = DataSourceStep(mock_wizard)
        
        # Verify they are the correct types
        self.assertIsInstance(naming_step, NamingStep)
        self.assertIsInstance(data_source_step, DataSourceStep)
        
        # Verify DataSourceStep has the required methods
        self.assertTrue(hasattr(data_source_step, 'create_widgets'))
        self.assertTrue(hasattr(data_source_step, 'validate'))
        self.assertTrue(hasattr(data_source_step, 'get_data'))
        
        # Verify DataSourceStep has the required attributes
        self.assertTrue(hasattr(data_source_step, 'available_types'))
        self.assertIsNotNone(data_source_step.available_types)


class TestSetupWizardMethods(unittest.TestCase):
    """Test cases for SetupWizard methods without GUI dependencies."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock wizard instance for testing methods
        self.wizard = Mock(spec=SetupWizard)
        self.wizard.current_step = 0
        self.wizard.steps = []
        self.wizard.session_config = None
        self.wizard.completion_callback = None
        self.wizard.logger = Mock()
        
        # Bind the actual methods to the mock
        self.wizard._on_back = SetupWizard._on_back.__get__(self.wizard)
        self.wizard._on_next = SetupWizard._on_next.__get__(self.wizard)
        self.wizard._on_finish = SetupWizard._on_finish.__get__(self.wizard)
        self.wizard._on_cancel = SetupWizard._on_cancel.__get__(self.wizard)
        self.wizard.set_completion_callback = SetupWizard.set_completion_callback.__get__(self.wizard)
        self.wizard.get_session_config = SetupWizard.get_session_config.__get__(self.wizard)
    
    def test_navigation_back(self):
        """Test back navigation."""
        self.wizard.current_step = 1
        self.wizard._show_current_step = Mock()
        
        self.wizard._on_back()
        
        self.assertEqual(self.wizard.current_step, 0)
        self.wizard._show_current_step.assert_called_once()
    
    def test_navigation_back_first_step(self):
        """Test back navigation on first step (should not change)."""
        self.wizard.current_step = 0
        self.wizard._show_current_step = Mock()
        
        self.wizard._on_back()
        
        self.assertEqual(self.wizard.current_step, 0)
        self.wizard._show_current_step.assert_not_called()
    
    def test_navigation_next_valid(self):
        """Test next navigation with valid step."""
        self.wizard.current_step = 0
        self.wizard._show_current_step = Mock()
        
        # Mock step validation to return True
        mock_step = Mock()
        mock_step.validate.return_value = True
        self.wizard.steps = [mock_step, Mock()]  # Two steps
        
        self.wizard._on_next()
        
        self.assertEqual(self.wizard.current_step, 1)
        self.wizard._show_current_step.assert_called_once()
    
    def test_navigation_next_invalid(self):
        """Test next navigation with invalid step."""
        self.wizard.current_step = 0
        self.wizard._show_current_step = Mock()
        
        # Mock step validation to return False
        mock_step = Mock()
        mock_step.validate.return_value = False
        self.wizard.steps = [mock_step]
        
        self.wizard._on_next()
        
        # Should not advance
        self.assertEqual(self.wizard.current_step, 0)
        self.wizard._show_current_step.assert_not_called()
    
    def test_navigation_next_last_step(self):
        """Test next navigation on last step (should finish)."""
        self.wizard.current_step = 0
        self.wizard._on_finish = Mock()
        
        # Mock step validation to return True
        mock_step = Mock()
        mock_step.validate.return_value = True
        self.wizard.steps = [mock_step]  # Only one step
        
        self.wizard._on_next()
        
        self.wizard._on_finish.assert_called_once()
    
    def test_finish_wizard(self):
        """Test wizard completion."""
        self.wizard.destroy = Mock()
        
        # Mock step data
        mock_step = Mock()
        mock_step.get_data.return_value = {"experiment_name": "test"}
        self.wizard.steps = [mock_step]
        
        # Mock completion callback
        mock_callback = Mock()
        self.wizard.completion_callback = mock_callback
        
        self.wizard._on_finish()
        
        # Verify session config was set
        self.assertIsNotNone(self.wizard.session_config)
        self.assertIn("experiment_name", self.wizard.session_config)
        self.assertIn("data_source_type", self.wizard.session_config)  # Hardcoded
        
        # Verify callback was called
        mock_callback.assert_called_once_with(self.wizard.session_config)
        
        # Verify window was destroyed
        self.wizard.destroy.assert_called_once()
    
    def test_cancel_wizard(self):
        """Test wizard cancellation."""
        self.wizard.destroy = Mock()
        
        self.wizard._on_cancel()
        
        self.wizard.destroy.assert_called_once()
    
    def test_set_completion_callback(self):
        """Test setting completion callback."""
        mock_callback = Mock()
        self.wizard.set_completion_callback(mock_callback)
        
        self.assertEqual(self.wizard.completion_callback, mock_callback)
    
    def test_get_session_config_none(self):
        """Test getting session config when None."""
        self.wizard.session_config = None
        
        result = self.wizard.get_session_config()
        
        self.assertIsNone(result)
    
    def test_get_session_config_with_data(self):
        """Test getting session config with data."""
        test_config = {"test": "data"}
        self.wizard.session_config = test_config
        
        result = self.wizard.get_session_config()
        
        self.assertEqual(result, test_config)


class TestConfigurationStep(unittest.TestCase):
    """Test cases for the ConfigurationStep class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_wizard = Mock()
        
        # Mock the wizard steps to include a DataSourceStep
        mock_data_source_step = Mock(spec=DataSourceStep)
        mock_data_source_step.get_data.return_value = {"data_source_type": "folders"}
        self.mock_wizard.steps = [Mock(), mock_data_source_step]  # Step 0 and Step 1
        
        self.step = ConfigurationStep(self.mock_wizard)
    
    def test_configuration_step_initialization(self):
        """Test ConfigurationStep initialization."""
        self.assertEqual(self.step.wizard, self.mock_wizard)
        self.assertIsNone(self.step.current_config_frame)
        
        # Folder configuration attributes
        self.assertIsNone(self.step.generated_folder_var)
        self.assertIsNone(self.step.expected_folder_var)
        self.assertIsNone(self.step.generated_folder_entry)
        self.assertIsNone(self.step.expected_folder_entry)
        
        # Database configuration attributes
        self.assertIsNone(self.step.db_file_var)
        self.assertIsNone(self.step.table_var)
        
        # Excel configuration attributes
        self.assertIsNone(self.step.excel_file_var)
        self.assertIsNone(self.step.sheet_var)
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_create_widgets(self, mock_ctk):
        """Test widget creation for configuration step."""
        mock_parent = Mock()
        mock_config_frame = Mock()
        mock_config_frame.winfo_children.return_value = []
        
        mock_ctk.CTkLabel.return_value = Mock()
        mock_ctk.CTkFrame.return_value = mock_config_frame
        mock_ctk.CTkFont.return_value = Mock()
        
        self.step.create_widgets(mock_parent)
        
        # Verify widgets were created
        self.assertIsNotNone(self.step.current_config_frame)
        
        # Verify CTk components were called
        self.assertTrue(mock_ctk.CTkLabel.called)
        self.assertTrue(mock_ctk.CTkFrame.called)
    
    def test_get_selected_data_source_type_folders(self):
        """Test getting selected data source type - folders."""
        result = self.step._get_selected_data_source_type()
        self.assertEqual(result, "folders")
    
    def test_get_selected_data_source_type_sqlite(self):
        """Test getting selected data source type - sqlite."""
        # Update mock to return sqlite
        self.mock_wizard.steps[1].get_data.return_value = {"data_source_type": "sqlite"}
        
        result = self.step._get_selected_data_source_type()
        self.assertEqual(result, "sqlite")
    
    def test_get_selected_data_source_type_excel(self):
        """Test getting selected data source type - excel."""
        # Update mock to return excel
        self.mock_wizard.steps[1].get_data.return_value = {"data_source_type": "excel"}
        
        result = self.step._get_selected_data_source_type()
        self.assertEqual(result, "excel")
    
    def test_get_selected_data_source_type_no_step(self):
        """Test getting selected data source type when no DataSourceStep found."""
        # Mock wizard with no DataSourceStep
        self.mock_wizard.steps = [Mock(), Mock()]  # Neither is DataSourceStep
        
        result = self.step._get_selected_data_source_type()
        self.assertEqual(result, "folders")  # Default fallback
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_create_folder_configuration(self, mock_ctk):
        """Test creation of folder configuration interface."""
        mock_frame = Mock()
        mock_frame.winfo_children.return_value = []
        self.step.current_config_frame = mock_frame
        
        # Mock CTk components
        mock_ctk.CTkLabel.return_value = Mock()
        mock_ctk.CTkFrame.return_value = Mock()
        mock_ctk.CTkEntry.return_value = Mock()
        mock_ctk.CTkButton.return_value = Mock()
        mock_ctk.StringVar.return_value = Mock()
        mock_ctk.CTkFont.return_value = Mock()
        
        self.step._create_folder_configuration()
        
        # Verify folder variables were created
        self.assertIsNotNone(self.step.generated_folder_var)
        self.assertIsNotNone(self.step.expected_folder_var)
        self.assertIsNotNone(self.step.generated_folder_entry)
        self.assertIsNotNone(self.step.expected_folder_entry)
        
        # Verify CTk components were called
        self.assertTrue(mock_ctk.CTkLabel.called)
        self.assertTrue(mock_ctk.CTkFrame.called)
        self.assertTrue(mock_ctk.CTkEntry.called)
        self.assertTrue(mock_ctk.CTkButton.called)
        self.assertTrue(mock_ctk.StringVar.called)
    
    @patch('tkinter.filedialog.askdirectory')
    def test_browse_generated_folder_success(self, mock_askdirectory):
        """Test successful browsing for generated folder."""
        mock_askdirectory.return_value = "/path/to/generated"
        
        # Setup mock variables
        mock_var = Mock()
        self.step.generated_folder_var = mock_var
        
        self.step._browse_generated_folder()
        
        # Verify folder dialog was called
        mock_askdirectory.assert_called_once()
        call_args = mock_askdirectory.call_args
        self.assertEqual(call_args.kwargs['title'], "Select Generated Code Folder")
        
        # Verify variable was set
        mock_var.set.assert_called_once_with("/path/to/generated")
    
    @patch('tkinter.filedialog.askdirectory')
    def test_browse_generated_folder_cancel(self, mock_askdirectory):
        """Test cancelling generated folder browse."""
        mock_askdirectory.return_value = ""  # User cancelled
        
        # Setup mock variables
        mock_var = Mock()
        self.step.generated_folder_var = mock_var
        
        self.step._browse_generated_folder()
        
        # Verify variable was not set
        mock_var.set.assert_not_called()
    
    @patch('tkinter.filedialog.askdirectory')
    def test_browse_generated_folder_error(self, mock_askdirectory):
        """Test error handling in generated folder browse."""
        mock_askdirectory.side_effect = Exception("File dialog error")
        
        # Setup mock variables
        mock_var = Mock()
        self.step.generated_folder_var = mock_var
        
        self.step._browse_generated_folder()
        
        # Verify error was shown
        self.mock_wizard.show_error.assert_called_once()
        error_message = self.mock_wizard.show_error.call_args[0][0]
        self.assertIn("Error selecting folder", error_message)
    
    @patch('tkinter.filedialog.askdirectory')
    def test_browse_expected_folder_success(self, mock_askdirectory):
        """Test successful browsing for expected folder."""
        mock_askdirectory.return_value = "/path/to/expected"
        
        # Setup mock variables
        mock_var = Mock()
        self.step.expected_folder_var = mock_var
        
        self.step._browse_expected_folder()
        
        # Verify folder dialog was called
        mock_askdirectory.assert_called_once()
        call_args = mock_askdirectory.call_args
        self.assertEqual(call_args.kwargs['title'], "Select Expected Code Folder")
        
        # Verify variable was set
        mock_var.set.assert_called_once_with("/path/to/expected")
    
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_validate_folder_configuration_success(self, mock_isdir, mock_exists):
        """Test successful folder configuration validation."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isdir.return_value = True
        
        # Setup mock variables
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = "/path/to/generated"
        mock_exp_var = Mock()
        mock_exp_var.get.return_value = "/path/to/expected"
        
        self.step.generated_folder_var = mock_gen_var
        self.step.expected_folder_var = mock_exp_var
        
        result = self.step._validate_folder_configuration()
        
        self.assertTrue(result)
        self.mock_wizard.show_error.assert_not_called()
    
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_validate_folder_configuration_no_generated(self, mock_isdir, mock_exists):
        """Test folder configuration validation with no generated folder."""
        # Setup mock variables
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = ""  # Empty path
        
        self.step.generated_folder_var = mock_gen_var
        
        result = self.step._validate_folder_configuration()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Please select a Generated Code folder.")
    
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_validate_folder_configuration_generated_not_exists(self, mock_isdir, mock_exists):
        """Test folder configuration validation with non-existent generated folder."""
        # Setup mocks
        mock_exists.return_value = False
        
        # Setup mock variables
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = "/nonexistent/path"
        
        self.step.generated_folder_var = mock_gen_var
        
        result = self.step._validate_folder_configuration()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called()
        error_message = self.mock_wizard.show_error.call_args[0][0]
        self.assertIn("does not exist", error_message)
    
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_validate_folder_configuration_generated_not_dir(self, mock_isdir, mock_exists):
        """Test folder configuration validation with generated path that's not a directory."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isdir.return_value = False
        
        # Setup mock variables
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = "/path/to/file.txt"
        
        self.step.generated_folder_var = mock_gen_var
        
        result = self.step._validate_folder_configuration()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called()
        error_message = self.mock_wizard.show_error.call_args[0][0]
        self.assertIn("not a directory", error_message)
    
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_validate_folder_configuration_expected_optional(self, mock_isdir, mock_exists):
        """Test folder configuration validation with optional expected folder."""
        # Setup mocks - generated exists, expected doesn't
        def mock_exists_side_effect(path):
            return path == "/path/to/generated"
        
        def mock_isdir_side_effect(path):
            return path == "/path/to/generated"
        
        mock_exists.side_effect = mock_exists_side_effect
        mock_isdir.side_effect = mock_isdir_side_effect
        
        # Setup mock variables
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = "/path/to/generated"
        mock_exp_var = Mock()
        mock_exp_var.get.return_value = ""  # Empty - optional
        
        self.step.generated_folder_var = mock_gen_var
        self.step.expected_folder_var = mock_exp_var
        
        result = self.step._validate_folder_configuration()
        
        self.assertTrue(result)  # Should pass even without expected folder
        self.mock_wizard.show_error.assert_not_called()
    
    def test_get_folder_data_both_folders(self):
        """Test getting folder data with both folders set."""
        # Setup mock variables
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = "/path/to/generated"
        mock_exp_var = Mock()
        mock_exp_var.get.return_value = "/path/to/expected"
        
        self.step.generated_folder_var = mock_gen_var
        self.step.expected_folder_var = mock_exp_var
        
        result = self.step._get_folder_data()
        
        expected = {
            "generated_code_path": "/path/to/generated",
            "expected_code_path": "/path/to/expected"
        }
        self.assertEqual(result, expected)
    
    def test_get_folder_data_generated_only(self):
        """Test getting folder data with only generated folder set."""
        # Setup mock variables
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = "/path/to/generated"
        mock_exp_var = Mock()
        mock_exp_var.get.return_value = ""  # Empty
        
        self.step.generated_folder_var = mock_gen_var
        self.step.expected_folder_var = mock_exp_var
        
        result = self.step._get_folder_data()
        
        expected = {
            "generated_code_path": "/path/to/generated"
        }
        self.assertEqual(result, expected)
    
    def test_validate_folders_data_source(self):
        """Test validation when data source type is folders."""
        # Mock the data source type
        self.step._get_selected_data_source_type = Mock(return_value="folders")
        self.step._validate_folder_configuration = Mock(return_value=True)
        
        result = self.step.validate()
        
        self.assertTrue(result)
        self.step._validate_folder_configuration.assert_called_once()
    
    def test_get_data_folders_data_source(self):
        """Test get_data when data source type is folders."""
        # Mock the data source type and folder data
        self.step._get_selected_data_source_type = Mock(return_value="folders")
        self.step._get_folder_data = Mock(return_value={"generated_code_path": "/test"})
        
        result = self.step.get_data()
        
        self.assertEqual(result, {"generated_code_path": "/test"})
        self.step._get_folder_data.assert_called_once()
    
    def test_validate_unknown_data_source(self):
        """Test validation with unknown data source type."""
        # Mock unknown data source type
        self.step._get_selected_data_source_type = Mock(return_value="unknown")
        
        result = self.step.validate()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Unknown data source type: unknown")
    
    def test_get_data_unknown_data_source(self):
        """Test get_data with unknown data source type."""
        # Mock unknown data source type
        self.step._get_selected_data_source_type = Mock(return_value="unknown")
        
        result = self.step.get_data()
        
        self.assertEqual(result, {})


class TestConfigurationStepDatabase(unittest.TestCase):
    """Test cases for ConfigurationStep database configuration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_wizard = Mock()
        
        # Mock the wizard steps to include a DataSourceStep returning sqlite
        mock_data_source_step = Mock(spec=DataSourceStep)
        mock_data_source_step.get_data.return_value = {"data_source_type": "sqlite"}
        self.mock_wizard.steps = [Mock(), mock_data_source_step]
        
        self.step = ConfigurationStep(self.mock_wizard)
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_create_database_configuration(self, mock_ctk):
        """Test creation of database configuration interface."""
        mock_frame = Mock()
        mock_frame.winfo_children.return_value = []
        self.step.current_config_frame = mock_frame
        
        # Mock CTk components
        mock_ctk.CTkLabel.return_value = Mock()
        mock_ctk.CTkFrame.return_value = Mock()
        mock_ctk.CTkEntry.return_value = Mock()
        mock_ctk.CTkButton.return_value = Mock()
        mock_ctk.CTkComboBox.return_value = Mock()
        mock_ctk.StringVar.return_value = Mock()
        mock_ctk.CTkFont.return_value = Mock()
        
        self.step._create_database_configuration()
        
        # Verify database variables were created
        self.assertIsNotNone(self.step.db_file_var)
        self.assertIsNotNone(self.step.table_var)
        self.assertIsNotNone(self.step.identifier_column_var)
        self.assertIsNotNone(self.step.generated_column_var)
        self.assertIsNotNone(self.step.expected_column_var)
        
        # Verify CTk components were called
        self.assertTrue(mock_ctk.CTkComboBox.called)
    
    def test_validate_database_configuration_success(self):
        """Test successful database configuration validation."""
        # Setup mock variables
        mock_db_var = Mock()
        mock_db_var.get.return_value = "/path/to/db.sqlite"
        mock_table_var = Mock()
        mock_table_var.get.return_value = "test_table"
        mock_id_var = Mock()
        mock_id_var.get.return_value = "id_column"
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = "generated_column"
        
        self.step.db_file_var = mock_db_var
        self.step.table_var = mock_table_var
        self.step.identifier_column_var = mock_id_var
        self.step.generated_column_var = mock_gen_var
        
        result = self.step._validate_database_configuration()
        
        self.assertTrue(result)
        self.mock_wizard.show_error.assert_not_called()
    
    def test_validate_database_configuration_no_file(self):
        """Test database configuration validation with no file selected."""
        # Setup mock variables
        mock_db_var = Mock()
        mock_db_var.get.return_value = ""  # Empty path
        
        self.step.db_file_var = mock_db_var
        
        result = self.step._validate_database_configuration()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Please select a database file.")
    
    def test_get_database_data(self):
        """Test getting database configuration data."""
        # Setup mock variables
        mock_db_var = Mock()
        mock_db_var.get.return_value = "/path/to/db.sqlite"
        mock_table_var = Mock()
        mock_table_var.get.return_value = "test_table"
        mock_id_var = Mock()
        mock_id_var.get.return_value = "id_column"
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = "generated_column"
        mock_exp_var = Mock()
        mock_exp_var.get.return_value = "expected_column"
        
        self.step.db_file_var = mock_db_var
        self.step.table_var = mock_table_var
        self.step.identifier_column_var = mock_id_var
        self.step.generated_column_var = mock_gen_var
        self.step.expected_column_var = mock_exp_var
        
        result = self.step._get_database_data()
        
        expected = {
            "database_path": "/path/to/db.sqlite",
            "table_name": "test_table",
            "identifier_column": "id_column",
            "generated_code_column": "generated_column",
            "expected_code_column": "expected_column"
        }
        self.assertEqual(result, expected)
    
    def test_get_database_data_no_expected_column(self):
        """Test getting database data with no expected column (None skip)."""
        # Setup mock variables
        mock_db_var = Mock()
        mock_db_var.get.return_value = "/path/to/db.sqlite"
        mock_table_var = Mock()
        mock_table_var.get.return_value = "test_table"
        mock_id_var = Mock()
        mock_id_var.get.return_value = "id_column"
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = "generated_column"
        mock_exp_var = Mock()
        mock_exp_var.get.return_value = "None (skip)"  # Skip option
        
        self.step.db_file_var = mock_db_var
        self.step.table_var = mock_table_var
        self.step.identifier_column_var = mock_id_var
        self.step.generated_column_var = mock_gen_var
        self.step.expected_column_var = mock_exp_var
        
        result = self.step._get_database_data()
        
        expected = {
            "database_path": "/path/to/db.sqlite",
            "table_name": "test_table",
            "identifier_column": "id_column",
            "generated_code_column": "generated_column",
            "expected_code_column": None  # Should be None, not "None (skip)"
        }
        self.assertEqual(result, expected)
    
    @patch('tkinter.filedialog.askopenfilename')
    def test_browse_database_file_success(self, mock_askopenfilename):
        """Test successful browsing for database file."""
        mock_askopenfilename.return_value = "/path/to/database.db"
        
        # Setup mock variables
        mock_var = Mock()
        self.step.db_file_var = mock_var
        self.step._load_database_info = Mock()
        
        self.step._browse_database_file()
        
        # Verify file dialog was called
        mock_askopenfilename.assert_called_once()
        call_args = mock_askopenfilename.call_args
        self.assertEqual(call_args.kwargs['title'], "Select SQLite Database File")
        
        # Verify variable was set
        mock_var.set.assert_called_once_with("/path/to/database.db")
        
        # Verify database info loading was called
        self.step._load_database_info.assert_called_once_with("/path/to/database.db")
    
    @patch('tkinter.filedialog.askopenfilename')
    def test_browse_database_file_cancel(self, mock_askopenfilename):
        """Test cancelling database file browse."""
        mock_askopenfilename.return_value = ""  # User cancelled
        
        # Setup mock variables
        mock_var = Mock()
        self.step.db_file_var = mock_var
        self.step._load_database_info = Mock()
        
        self.step._browse_database_file()
        
        # Verify variable was not set
        mock_var.set.assert_not_called()
        
        # Verify database info loading was not called
        self.step._load_database_info.assert_not_called()
    
    @patch('sqlite3.connect')
    def test_load_database_info_success(self, mock_connect):
        """Test successful database info loading."""
        # Setup mock database connection
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("table1",), ("table2",)]
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_connect.return_value = mock_conn
        
        # Setup mock UI components
        self.step.loading_label = Mock()
        self.step.loading_label.pack = Mock()
        self.step.loading_label.pack_forget = Mock()
        self.step.current_config_frame = Mock()
        self.step.current_config_frame.update = Mock()
        self.step.table_dropdown = Mock()
        self.step._reset_column_dropdowns = Mock()
        
        self.step._load_database_info("/path/to/test.db")
        
        # Verify database connection was made
        mock_connect.assert_called_once_with("/path/to/test.db")
        
        # Verify table dropdown was updated
        self.step.table_dropdown.configure.assert_called()
        configure_calls = self.step.table_dropdown.configure.call_args_list
        
        # Find the call that sets values
        values_call = None
        for call in configure_calls:
            if 'values' in call.kwargs:
                values_call = call
                break
        
        self.assertIsNotNone(values_call)
        self.assertEqual(values_call.kwargs['values'], ["table1", "table2"])
        self.assertEqual(values_call.kwargs['state'], "normal")
    
    @patch('sqlite3.connect')
    def test_load_database_info_no_tables(self, mock_connect):
        """Test database info loading with no tables."""
        # Setup mock database connection with no tables
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []  # No tables
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_connect.return_value = mock_conn
        
        # Setup mock UI components
        self.step.loading_label = Mock()
        self.step.loading_label.pack = Mock()
        self.step.loading_label.pack_forget = Mock()
        self.step.current_config_frame = Mock()
        self.step.current_config_frame.update = Mock()
        self.step.table_dropdown = Mock()
        
        self.step._load_database_info("/path/to/test.db")
        
        # Verify error was shown
        self.mock_wizard.show_error.assert_called_with("No tables found in the selected database.")
        
        # Verify table dropdown was disabled
        self.step.table_dropdown.configure.assert_called()
        configure_calls = self.step.table_dropdown.configure.call_args_list
        
        # Find the call that sets disabled state
        disabled_call = None
        for call in configure_calls:
            if 'state' in call.kwargs and call.kwargs['state'] == "disabled":
                disabled_call = call
                break
        
        self.assertIsNotNone(disabled_call)
    
    @patch('sqlite3.connect')
    def test_on_table_selected_success(self, mock_connect):
        """Test successful table selection and column loading."""
        # Setup mock database connection
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (0, "id", "INTEGER", 0, None, 1),  # PRAGMA table_info format
            (1, "generated_code", "TEXT", 0, None, 0),
            (2, "expected_code", "TEXT", 0, None, 0)
        ]
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_connect.return_value = mock_conn
        
        # Setup mock UI components
        self.step.loading_label = Mock()
        self.step.loading_label.pack = Mock()
        self.step.loading_label.pack_forget = Mock()
        self.step.current_config_frame = Mock()
        self.step.current_config_frame.update = Mock()
        self.step.db_file_var = Mock()
        self.step.db_file_var.get.return_value = "/path/to/test.db"
        
        # Setup column dropdowns
        self.step.identifier_column_dropdown = Mock()
        self.step.generated_column_dropdown = Mock()
        self.step.expected_column_dropdown = Mock()
        
        self.step._on_table_selected("test_table")
        
        # Verify column dropdowns were updated
        expected_columns = ["id", "generated_code", "expected_code"]
        
        self.step.identifier_column_dropdown.configure.assert_called()
        id_configure_call = self.step.identifier_column_dropdown.configure.call_args
        self.assertEqual(id_configure_call.kwargs['values'], expected_columns)
        self.assertEqual(id_configure_call.kwargs['state'], "normal")
        
        self.step.generated_column_dropdown.configure.assert_called()
        gen_configure_call = self.step.generated_column_dropdown.configure.call_args
        self.assertEqual(gen_configure_call.kwargs['values'], expected_columns)
        self.assertEqual(gen_configure_call.kwargs['state'], "normal")
        
        self.step.expected_column_dropdown.configure.assert_called()
        exp_configure_call = self.step.expected_column_dropdown.configure.call_args
        self.assertEqual(exp_configure_call.kwargs['values'], ["None (skip)"] + expected_columns)
        self.assertEqual(exp_configure_call.kwargs['state'], "normal")


class TestConfigurationStepExcel(unittest.TestCase):
    """Test cases for ConfigurationStep Excel/CSV configuration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_wizard = Mock()
        
        # Mock the wizard steps to include a DataSourceStep returning excel
        mock_data_source_step = Mock(spec=DataSourceStep)
        mock_data_source_step.get_data.return_value = {"data_source_type": "excel"}
        self.mock_wizard.steps = [Mock(), mock_data_source_step]
        
        self.step = ConfigurationStep(self.mock_wizard)
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_create_excel_configuration(self, mock_ctk):
        """Test creation of Excel/CSV configuration interface."""
        mock_frame = Mock()
        mock_frame.winfo_children.return_value = []
        self.step.current_config_frame = mock_frame
        
        # Mock CTk components
        mock_ctk.CTkLabel.return_value = Mock()
        mock_ctk.CTkFrame.return_value = Mock()
        mock_ctk.CTkEntry.return_value = Mock()
        mock_ctk.CTkButton.return_value = Mock()
        mock_ctk.CTkComboBox.return_value = Mock()
        mock_ctk.StringVar.return_value = Mock()
        mock_ctk.CTkFont.return_value = Mock()
        
        self.step._create_excel_configuration()
        
        # Verify Excel variables were created
        self.assertIsNotNone(self.step.excel_file_var)
        self.assertIsNotNone(self.step.sheet_var)
        self.assertIsNotNone(self.step.excel_identifier_column_var)
        self.assertIsNotNone(self.step.excel_generated_column_var)
        self.assertIsNotNone(self.step.excel_expected_column_var)
        
        # Verify CTk components were called
        self.assertTrue(mock_ctk.CTkComboBox.called)
    
    def test_validate_excel_configuration_success(self):
        """Test successful Excel configuration validation."""
        # Setup mock variables
        mock_file_var = Mock()
        mock_file_var.get.return_value = "/path/to/file.csv"
        mock_id_var = Mock()
        mock_id_var.get.return_value = "id_column"
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = "generated_column"
        
        self.step.excel_file_var = mock_file_var
        self.step.excel_identifier_column_var = mock_id_var
        self.step.excel_generated_column_var = mock_gen_var
        
        result = self.step._validate_excel_configuration()
        
        self.assertTrue(result)
        self.mock_wizard.show_error.assert_not_called()
    
    def test_validate_excel_configuration_no_file(self):
        """Test Excel configuration validation with no file selected."""
        # Setup mock variables
        mock_file_var = Mock()
        mock_file_var.get.return_value = ""  # Empty path
        
        self.step.excel_file_var = mock_file_var
        
        result = self.step._validate_excel_configuration()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Please select an Excel or CSV file.")
    
    def test_get_excel_data_csv(self):
        """Test getting Excel data for CSV file."""
        # Setup mock variables
        mock_file_var = Mock()
        mock_file_var.get.return_value = "/path/to/file.csv"
        mock_id_var = Mock()
        mock_id_var.get.return_value = "id_column"
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = "generated_column"
        mock_exp_var = Mock()
        mock_exp_var.get.return_value = "expected_column"
        
        self.step.excel_file_var = mock_file_var
        self.step.excel_identifier_column_var = mock_id_var
        self.step.excel_generated_column_var = mock_gen_var
        self.step.excel_expected_column_var = mock_exp_var
        
        result = self.step._get_excel_data()
        
        expected = {
            "file_path": "/path/to/file.csv",
            "identifier_column": "id_column",
            "generated_code_column": "generated_column",
            "expected_code_column": "expected_column"
        }
        self.assertEqual(result, expected)
    
    def test_get_excel_data_xlsx_with_sheet(self):
        """Test getting Excel data for XLSX file with sheet."""
        # Setup mock variables
        mock_file_var = Mock()
        mock_file_var.get.return_value = "/path/to/file.xlsx"
        mock_sheet_var = Mock()
        mock_sheet_var.get.return_value = "Sheet1"
        mock_id_var = Mock()
        mock_id_var.get.return_value = "id_column"
        mock_gen_var = Mock()
        mock_gen_var.get.return_value = "generated_column"
        mock_exp_var = Mock()
        mock_exp_var.get.return_value = "None (skip)"  # Skip expected
        
        self.step.excel_file_var = mock_file_var
        self.step.sheet_var = mock_sheet_var
        self.step.excel_identifier_column_var = mock_id_var
        self.step.excel_generated_column_var = mock_gen_var
        self.step.excel_expected_column_var = mock_exp_var
        
        result = self.step._get_excel_data()
        
        expected = {
            "file_path": "/path/to/file.xlsx",
            "sheet_name": "Sheet1",
            "identifier_column": "id_column",
            "generated_code_column": "generated_column",
            "expected_code_column": None  # Should be None, not "None (skip)"
        }
        self.assertEqual(result, expected)
    
    @patch('tkinter.filedialog.askopenfilename')
    def test_browse_excel_file_success(self, mock_askopenfilename):
        """Test successful browsing for Excel/CSV file."""
        mock_askopenfilename.return_value = "/path/to/file.xlsx"
        
        # Setup mock variables
        mock_var = Mock()
        self.step.excel_file_var = mock_var
        self.step._load_excel_info = Mock()
        
        self.step._browse_excel_file()
        
        # Verify file dialog was called
        mock_askopenfilename.assert_called_once()
        call_args = mock_askopenfilename.call_args
        self.assertEqual(call_args.kwargs['title'], "Select Excel or CSV File")
        
        # Verify variable was set
        mock_var.set.assert_called_once_with("/path/to/file.xlsx")
        
        # Verify Excel info loading was called
        self.step._load_excel_info.assert_called_once_with("/path/to/file.xlsx")
    
    @patch('tkinter.filedialog.askopenfilename')
    def test_browse_excel_file_cancel(self, mock_askopenfilename):
        """Test cancelling Excel file browse."""
        mock_askopenfilename.return_value = ""  # User cancelled
        
        # Setup mock variables
        mock_var = Mock()
        self.step.excel_file_var = mock_var
        self.step._load_excel_info = Mock()
        
        self.step._browse_excel_file()
        
        # Verify variable was not set
        mock_var.set.assert_not_called()
        
        # Verify Excel info loading was not called
        self.step._load_excel_info.assert_not_called()
    
    @patch('pandas.read_csv')
    def test_load_excel_info_csv_success(self, mock_read_csv):
        """Test successful CSV file info loading."""
        # Setup mock pandas DataFrame
        mock_df = Mock()
        mock_df.columns = ["id", "generated_code", "expected_code"]
        mock_read_csv.return_value = mock_df
        
        # Setup mock UI components
        self.step.loading_label = Mock()
        self.step.loading_label.pack = Mock()
        self.step.loading_label.pack_forget = Mock()
        self.step.current_config_frame = Mock()
        self.step.current_config_frame.update = Mock()
        self.step.sheet_dropdown = Mock()
        self.step._update_excel_column_dropdowns = Mock()
        
        self.step._load_excel_info("/path/to/file.csv")
        
        # Verify CSV was read
        mock_read_csv.assert_called_once_with("/path/to/file.csv", nrows=0)
        
        # Verify sheet dropdown was disabled for CSV
        self.step.sheet_dropdown.configure.assert_called()
        configure_calls = self.step.sheet_dropdown.configure.call_args_list
        
        # Find the call that sets CSV state
        csv_call = None
        for call in configure_calls:
            if 'values' in call.kwargs and "N/A (CSV file)" in call.kwargs['values']:
                csv_call = call
                break
        
        self.assertIsNotNone(csv_call)
        self.assertEqual(csv_call.kwargs['state'], "disabled")
        
        # Verify column dropdowns were updated
        self.step._update_excel_column_dropdowns.assert_called_once_with(["id", "generated_code", "expected_code"])
    
    @patch('pandas.ExcelFile')
    def test_load_excel_info_xlsx_success(self, mock_excel_file_class):
        """Test successful Excel file info loading."""
        # Setup mock Excel file
        mock_excel_file = Mock()
        mock_excel_file.sheet_names = ["Sheet1", "Sheet2"]
        mock_excel_file_class.return_value = mock_excel_file
        
        # Setup mock UI components
        self.step.loading_label = Mock()
        self.step.loading_label.pack = Mock()
        self.step.loading_label.pack_forget = Mock()
        self.step.current_config_frame = Mock()
        self.step.current_config_frame.update = Mock()
        self.step.sheet_dropdown = Mock()
        self.step._load_excel_sheet_columns = Mock()
        
        self.step._load_excel_info("/path/to/file.xlsx")
        
        # Verify Excel file was opened
        mock_excel_file_class.assert_called_once_with("/path/to/file.xlsx")
        
        # Verify sheet dropdown was updated
        self.step.sheet_dropdown.configure.assert_called()
        configure_calls = self.step.sheet_dropdown.configure.call_args_list
        
        # Find the call that sets sheet values
        sheet_call = None
        for call in configure_calls:
            if 'values' in call.kwargs and call.kwargs['values'] == ["Sheet1", "Sheet2"]:
                sheet_call = call
                break
        
        self.assertIsNotNone(sheet_call)
        self.assertEqual(sheet_call.kwargs['state'], "normal")
    
    @patch('pandas.read_excel')
    def test_load_excel_sheet_columns_success(self, mock_read_excel):
        """Test successful Excel sheet column loading."""
        # Setup mock pandas DataFrame
        mock_df = Mock()
        mock_df.columns = ["id", "generated_code", "expected_code"]
        mock_read_excel.return_value = mock_df
        
        # Setup mock UI components
        self.step.loading_label = Mock()
        self.step.loading_label.pack = Mock()
        self.step.loading_label.pack_forget = Mock()
        self.step.current_config_frame = Mock()
        self.step.current_config_frame.update = Mock()
        self.step._update_excel_column_dropdowns = Mock()
        
        self.step._load_excel_sheet_columns("/path/to/file.xlsx", "Sheet1")
        
        # Verify Excel sheet was read
        mock_read_excel.assert_called_once_with("/path/to/file.xlsx", sheet_name="Sheet1", nrows=0)
        
        # Verify column dropdowns were updated
        self.step._update_excel_column_dropdowns.assert_called_once_with(["id", "generated_code", "expected_code"])
    
    def test_update_excel_column_dropdowns_success(self):
        """Test successful Excel column dropdown updates."""
        # Setup mock dropdowns
        self.step.excel_identifier_column_dropdown = Mock()
        self.step.excel_generated_column_dropdown = Mock()
        self.step.excel_expected_column_dropdown = Mock()
        
        columns = ["id", "generated_code", "expected_code"]
        self.step._update_excel_column_dropdowns(columns)
        
        # Verify identifier column dropdown
        self.step.excel_identifier_column_dropdown.configure.assert_called_once_with(
            values=columns, state="normal"
        )
        self.step.excel_identifier_column_dropdown.set.assert_called_once_with("Select column...")
        
        # Verify generated column dropdown
        self.step.excel_generated_column_dropdown.configure.assert_called_once_with(
            values=columns, state="normal"
        )
        self.step.excel_generated_column_dropdown.set.assert_called_once_with("Select column...")
        
        # Verify expected column dropdown (with None option)
        expected_values = ["None (skip)"] + columns
        self.step.excel_expected_column_dropdown.configure.assert_called_once_with(
            values=expected_values, state="normal"
        )
        self.step.excel_expected_column_dropdown.set.assert_called_once_with("None (skip)")
    
    def test_update_excel_column_dropdowns_no_columns(self):
        """Test Excel column dropdown updates with no columns."""
        # Setup mock dropdowns
        self.step.excel_identifier_column_dropdown = Mock()
        self.step.excel_generated_column_dropdown = Mock()
        self.step.excel_expected_column_dropdown = Mock()
        
        self.step._update_excel_column_dropdowns([])
        
        # Verify error was shown
        self.mock_wizard.show_error.assert_called_with("No columns found in the selected file/sheet.")
    
    def test_validate_excel_configuration_xlsx_no_sheet(self):
        """Test Excel configuration validation for XLSX file with no sheet selected."""
        # Setup mock variables
        mock_file_var = Mock()
        mock_file_var.get.return_value = "/path/to/file.xlsx"
        mock_sheet_var = Mock()
        mock_sheet_var.get.return_value = "Select a sheet..."  # Not selected
        
        self.step.excel_file_var = mock_file_var
        self.step.sheet_var = mock_sheet_var
        
        result = self.step._validate_excel_configuration()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Please select a sheet.")


class TestFinalizationStep(unittest.TestCase):
    """Test cases for the FinalizationStep class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_wizard = Mock()
        self.mock_wizard.steps = []
        self.mock_wizard.current_step = 3  # Finalization is step 4 (index 3)
        self.step = FinalizationStep(self.mock_wizard)
    
    def test_finalization_step_initialization(self):
        """Test FinalizationStep initialization."""
        self.assertEqual(self.step.wizard, self.mock_wizard)
        self.assertIsNone(self.step.sampling_var)
        self.assertIsNone(self.step.sampling_slider)
        self.assertIsNone(self.step.sampling_label)
        self.assertIsNone(self.step.output_format_var)
        self.assertIsNone(self.step.summary_text)
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_create_widgets(self, mock_ctk):
        """Test widget creation for finalization step."""
        mock_parent = Mock()
        mock_ctk.CTkLabel.return_value = Mock()
        mock_ctk.CTkFrame.return_value = Mock()
        mock_ctk.CTkSlider.return_value = Mock()
        mock_ctk.CTkRadioButton.return_value = Mock()
        mock_ctk.CTkTextbox.return_value = Mock()
        mock_ctk.CTkFont.return_value = Mock()
        mock_ctk.IntVar.return_value = Mock()
        mock_ctk.StringVar.return_value = Mock()
        
        self.step.create_widgets(mock_parent)
        
        # Verify widgets were created
        self.assertIsNotNone(self.step.sampling_var)
        self.assertIsNotNone(self.step.sampling_slider)
        self.assertIsNotNone(self.step.sampling_label)
        self.assertIsNotNone(self.step.output_format_var)
        self.assertIsNotNone(self.step.summary_text)
        
        # Verify CTk components were called
        self.assertTrue(mock_ctk.CTkLabel.called)
        self.assertTrue(mock_ctk.CTkFrame.called)
        self.assertTrue(mock_ctk.CTkSlider.called)
        self.assertTrue(mock_ctk.CTkRadioButton.called)
        self.assertTrue(mock_ctk.CTkTextbox.called)
    
    def test_update_sampling_label_100_percent(self):
        """Test sampling label update for 100%."""
        mock_label = Mock()
        self.step.sampling_label = mock_label
        
        self.step._update_sampling_label(100.0)
        
        mock_label.configure.assert_called_with(text="100% (Use all available data)")
    
    def test_update_sampling_label_90_percent(self):
        """Test sampling label update for 90%."""
        mock_label = Mock()
        self.step.sampling_label = mock_label
        
        self.step._update_sampling_label(90.0)
        
        mock_label.configure.assert_called_with(text="90% (Nearly all data)")
    
    def test_update_sampling_label_50_percent(self):
        """Test sampling label update for 50%."""
        mock_label = Mock()
        self.step.sampling_label = mock_label
        
        self.step._update_sampling_label(50.0)
        
        mock_label.configure.assert_called_with(text="50% (Majority of data)")
    
    def test_update_sampling_label_25_percent(self):
        """Test sampling label update for 25%."""
        mock_label = Mock()
        self.step.sampling_label = mock_label
        
        self.step._update_sampling_label(25.0)
        
        mock_label.configure.assert_called_with(text="25% (Quarter of data)")
    
    def test_update_sampling_label_10_percent(self):
        """Test sampling label update for 10%."""
        mock_label = Mock()
        self.step.sampling_label = mock_label
        
        self.step._update_sampling_label(10.0)
        
        mock_label.configure.assert_called_with(text="10% (Small sample)")
    
    def test_update_sampling_label_5_percent(self):
        """Test sampling label update for 5%."""
        mock_label = Mock()
        self.step.sampling_label = mock_label
        
        self.step._update_sampling_label(5.0)
        
        mock_label.configure.assert_called_with(text="5% (Very small sample)")
    
    def test_validate_no_sampling_var(self):
        """Test validation when sampling_var is None."""
        self.step.sampling_var = None
        
        result = self.step.validate()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Sampling configuration is not initialized.")
    
    def test_validate_invalid_sampling_percentage_too_low(self):
        """Test validation with sampling percentage too low."""
        mock_sampling_var = Mock()
        mock_sampling_var.get.return_value = 0
        self.step.sampling_var = mock_sampling_var
        
        result = self.step.validate()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Sampling percentage must be between 1% and 100%.")
    
    def test_validate_invalid_sampling_percentage_too_high(self):
        """Test validation with sampling percentage too high."""
        mock_sampling_var = Mock()
        mock_sampling_var.get.return_value = 101
        self.step.sampling_var = mock_sampling_var
        
        result = self.step.validate()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Sampling percentage must be between 1% and 100%.")
    
    def test_validate_no_output_format_var(self):
        """Test validation when output_format_var is None."""
        mock_sampling_var = Mock()
        mock_sampling_var.get.return_value = 50
        self.step.sampling_var = mock_sampling_var
        self.step.output_format_var = None
        
        result = self.step.validate()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Output format is not selected.")
    
    def test_validate_invalid_output_format(self):
        """Test validation with invalid output format."""
        mock_sampling_var = Mock()
        mock_sampling_var.get.return_value = 50
        self.step.sampling_var = mock_sampling_var
        
        mock_output_format_var = Mock()
        mock_output_format_var.get.return_value = "invalid"
        self.step.output_format_var = mock_output_format_var
        
        result = self.step.validate()
        
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Invalid output format selected.")
    
    def test_validate_valid_configuration_excel(self):
        """Test validation with valid configuration (Excel format)."""
        mock_sampling_var = Mock()
        mock_sampling_var.get.return_value = 75
        self.step.sampling_var = mock_sampling_var
        
        mock_output_format_var = Mock()
        mock_output_format_var.get.return_value = "excel"
        self.step.output_format_var = mock_output_format_var
        
        result = self.step.validate()
        
        self.assertTrue(result)
        self.mock_wizard.show_error.assert_not_called()
    
    def test_validate_valid_configuration_csv(self):
        """Test validation with valid configuration (CSV format)."""
        mock_sampling_var = Mock()
        mock_sampling_var.get.return_value = 100
        self.step.sampling_var = mock_sampling_var
        
        mock_output_format_var = Mock()
        mock_output_format_var.get.return_value = "csv"
        self.step.output_format_var = mock_output_format_var
        
        result = self.step.validate()
        
        self.assertTrue(result)
        self.mock_wizard.show_error.assert_not_called()
    
    def test_get_data_no_vars(self):
        """Test get_data when variables are None."""
        self.step.sampling_var = None
        self.step.output_format_var = None
        
        result = self.step.get_data()
        
        self.assertEqual(result, {})
    
    def test_get_data_valid_configuration(self):
        """Test get_data with valid configuration."""
        mock_sampling_var = Mock()
        mock_sampling_var.get.return_value = 80
        self.step.sampling_var = mock_sampling_var
        
        mock_output_format_var = Mock()
        mock_output_format_var.get.return_value = "excel"
        self.step.output_format_var = mock_output_format_var
        
        result = self.step.get_data()
        
        expected = {
            "sampling_percentage": 80,
            "output_format": "excel"
        }
        self.assertEqual(result, expected)
    
    def test_get_data_source_type_from_previous_steps(self):
        """Test getting data source type from previous steps."""
        # Create mock DataSourceStep
        mock_data_source_step = Mock(spec=DataSourceStep)
        mock_data_source_step.get_data.return_value = {"data_source_type": "sqlite"}
        
        self.mock_wizard.steps = [Mock(), mock_data_source_step, Mock()]
        
        result = self.step._get_data_source_type()
        
        self.assertEqual(result, "sqlite")
    
    def test_get_data_source_type_no_data_source_step(self):
        """Test getting data source type when no DataSourceStep exists."""
        self.mock_wizard.steps = [Mock(), Mock(), Mock()]
        
        result = self.step._get_data_source_type()
        
        self.assertEqual(result, "folders")  # Default fallback
    
    def test_on_show_updates_summary(self):
        """Test that on_show updates the summary display."""
        mock_summary_text = Mock()
        self.step.summary_text = mock_summary_text
        
        # Mock the wizard steps for summary generation
        mock_naming_step = Mock(spec=NamingStep)
        mock_naming_step.get_data.return_value = {
            "experiment_name": "test_experiment",
            "session_id": "test_experiment_2025-09-24_10-00-00"
        }
        
        mock_data_source_step = Mock(spec=DataSourceStep)
        mock_data_source_step.get_data.return_value = {"data_source_type": "folders"}
        
        mock_config_step = Mock(spec=ConfigurationStep)
        mock_config_step.get_data.return_value = {
            "generated_code_path": "/path/to/generated",
            "expected_code_path": "/path/to/expected"
        }
        
        self.mock_wizard.steps = [mock_naming_step, mock_data_source_step, mock_config_step, self.step]
        
        # Mock the current step variables
        mock_sampling_var = Mock()
        mock_sampling_var.get.return_value = 75
        self.step.sampling_var = mock_sampling_var
        
        mock_output_format_var = Mock()
        mock_output_format_var.get.return_value = "excel"
        self.step.output_format_var = mock_output_format_var
        
        self.step.on_show()
        
        # Verify summary was updated
        mock_summary_text.delete.assert_called_with("1.0", "end")
        mock_summary_text.insert.assert_called()
        
        # Check that the inserted text contains expected information
        call_args = mock_summary_text.insert.call_args[0]
        inserted_text = call_args[1]
        
        self.assertIn("test_experiment", inserted_text)
        self.assertIn("Folders", inserted_text)
        self.assertIn("75%", inserted_text)
        self.assertIn("EXCEL", inserted_text)


class TestSessionResumptionStep(unittest.TestCase):
    """Test cases for the SessionResumptionStep class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_wizard = Mock()
        
        # Mock the SessionManager
        with patch('vaitp_auditor.gui.setup_wizard.SessionManager') as mock_session_manager_class:
            self.mock_session_manager = Mock()
            mock_session_manager_class.return_value = self.mock_session_manager
            self.step = SessionResumptionStep(self.mock_wizard)
    
    def test_step_initialization(self):
        """Test SessionResumptionStep initialization."""
        self.assertEqual(self.step.wizard, self.mock_wizard)
        self.assertIsNotNone(self.step.session_manager)
        self.assertEqual(self.step.available_sessions, [])
        self.assertIsNone(self.step.selected_session_id)
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_create_widgets_no_sessions(self, mock_ctk):
        """Test widget creation when no sessions are available."""
        # Mock no available sessions
        self.mock_session_manager.list_available_sessions.return_value = []
        
        # Mock StringVar
        mock_string_var = Mock()
        mock_string_var.get.return_value = "new"
        mock_ctk.StringVar.return_value = mock_string_var
        
        mock_parent = Mock()
        self.step.create_widgets(mock_parent)
        
        # Verify that new session widgets are created
        self.assertEqual(self.step.available_sessions, [])
        self.assertIsNotNone(self.step.action_var)
        self.assertEqual(self.step.action_var.get(), "new")
    
    @patch('vaitp_auditor.gui.setup_wizard.ctk')
    def test_create_widgets_with_sessions(self, mock_ctk):
        """Test widget creation when sessions are available."""
        # Mock available sessions
        mock_sessions = ['session1', 'session2']
        self.mock_session_manager.list_available_sessions.return_value = mock_sessions
        
        # Mock session info
        mock_session_info = {
            'experiment_name': 'Test Experiment',
            'completed_reviews': 5,
            'total_reviews': 10,
            'progress_percentage': 50.0,
            'created_timestamp': datetime.now(),
            'saved_timestamp': datetime.now()
        }
        self.mock_session_manager.get_session_info.return_value = mock_session_info
        
        # Mock StringVar
        mock_string_var = Mock()
        mock_string_var.get.return_value = "resume"
        mock_ctk.StringVar.return_value = mock_string_var
        
        mock_parent = Mock()
        self.step.create_widgets(mock_parent)
        
        # Verify that resumption widgets are created
        self.assertEqual(self.step.available_sessions, mock_sessions)
        self.assertIsNotNone(self.step.action_var)
        self.assertEqual(self.step.action_var.get(), "resume")
    
    def test_validate_new_session(self):
        """Test validation for new session action."""
        self.step.action_var = Mock()
        self.step.action_var.get.return_value = "new"
        
        result = self.step.validate()
        self.assertTrue(result)
    
    def test_validate_resume_session_valid(self):
        """Test validation for resume session action with valid selection."""
        self.step.action_var = Mock()
        self.step.action_var.get.return_value = "resume"
        self.step.selected_session_id = "session1"
        self.step.available_sessions = ["session1", "session2"]
        
        result = self.step.validate()
        self.assertTrue(result)
    
    def test_validate_resume_session_no_selection(self):
        """Test validation for resume session action with no selection."""
        self.step.action_var = Mock()
        self.step.action_var.get.return_value = "resume"
        self.step.selected_session_id = None
        
        result = self.step.validate()
        self.assertFalse(result)
        self.mock_wizard.show_error.assert_called_with("Please select a session to resume.")
    
    def test_get_data_new_session(self):
        """Test get_data for new session action."""
        self.step.action_var = Mock()
        self.step.action_var.get.return_value = "new"
        
        data = self.step.get_data()
        expected = {"action": "new"}
        self.assertEqual(data, expected)
    
    def test_get_data_resume_session(self):
        """Test get_data for resume session action."""
        self.step.action_var = Mock()
        self.step.action_var.get.return_value = "resume"
        self.step.selected_session_id = "session1"
        
        data = self.step.get_data()
        expected = {"action": "resume", "session_id": "session1"}
        self.assertEqual(data, expected)
    
    def test_select_session(self):
        """Test session selection functionality."""
        session_id = "test_session"
        
        # Mock session buttons
        mock_button1 = Mock()
        mock_button2 = Mock()
        self.step.session_buttons = [
            (mock_button1, "session1"),
            (mock_button2, session_id)
        ]
        
        self.step._select_session(session_id)
        
        # Verify selection
        self.assertEqual(self.step.selected_session_id, session_id)
        mock_button1.deselect.assert_called_once()
        mock_button2.select.assert_called_once()


if __name__ == '__main__':
    unittest.main()