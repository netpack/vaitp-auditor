"""
Setup Wizard for VAITP-Auditor GUI

This module provides a multi-step setup wizard for configuring review sessions
in the VAITP-Auditor GUI application.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
from datetime import datetime

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from .models import GUIConfig
from ..data_sources.factory import DataSourceFactory
from ..session_manager import SessionManager


class SetupStep(ABC):
    """Abstract base class for setup wizard steps."""
    
    def __init__(self, wizard: 'SetupWizard'):
        """Initialize the setup step.
        
        Args:
            wizard: Reference to the parent SetupWizard instance
        """
        self.wizard = wizard
        self.frame: Optional[ctk.CTkFrame] = None
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def create_widgets(self, parent: ctk.CTkFrame) -> None:
        """Create the widgets for this step.
        
        Args:
            parent: Parent frame to contain the step widgets
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate the current step's input.
        
        Returns:
            bool: True if validation passes, False otherwise
        """
        pass
    
    @abstractmethod
    def get_data(self) -> Dict[str, Any]:
        """Get the data from this step.
        
        Returns:
            Dict[str, Any]: Step data for session configuration
        """
        pass
    
    def on_show(self) -> None:
        """Called when this step is shown. Override for custom behavior."""
        pass
    
    def on_hide(self) -> None:
        """Called when this step is hidden. Override for custom behavior."""
        pass


class NamingStep(SetupStep):
    """Step 1: Experiment naming with real-time session ID preview."""
    
    def __init__(self, wizard: 'SetupWizard'):
        """Initialize the naming step."""
        super().__init__(wizard)
        self.experiment_entry: Optional[ctk.CTkEntry] = None
        self.preview_label: Optional[ctk.CTkLabel] = None
    
    def create_widgets(self, parent: ctk.CTkFrame) -> None:
        """Create widgets for experiment naming step."""
        self.frame = parent
        
        # Title
        title_label = ctk.CTkLabel(
            parent,
            text="Step 1: Name Your Review Session",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Description
        desc_label = ctk.CTkLabel(
            parent,
            text="Enter a name for your experiment. This will be used to identify\nyour review session and generate output files.",
            font=ctk.CTkFont(size=12)
        )
        desc_label.pack(pady=(0, 20))
        
        # Experiment name entry
        name_frame = ctk.CTkFrame(parent)
        name_frame.pack(pady=10, padx=40, fill="x")
        
        name_label = ctk.CTkLabel(
            name_frame,
            text="Experiment Name:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        name_label.pack(pady=(15, 5))
        
        self.experiment_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="Enter experiment name (e.g., 'vulnerability_test_1')",
            font=ctk.CTkFont(size=12),
            width=400
        )
        self.experiment_entry.pack(pady=(0, 10))
        
        # Initialize cache
        self._experiment_name_cache = ""
        
        # Bind the entry to update preview in real-time and cache the value
        self.experiment_entry.bind("<KeyRelease>", self._update_preview)
        self.experiment_entry.bind("<FocusOut>", self._cache_experiment_name)
        
        # Session ID preview
        preview_frame = ctk.CTkFrame(parent)
        preview_frame.pack(pady=10, padx=40, fill="x")
        
        preview_title = ctk.CTkLabel(
            preview_frame,
            text="Session ID Preview:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        preview_title.pack(pady=(15, 5))
        
        self.preview_label = ctk.CTkLabel(
            preview_frame,
            text=self._generate_session_id(""),
            font=ctk.CTkFont(size=12, family="monospace"),
            text_color="gray"
        )
        self.preview_label.pack(pady=(0, 15))
    
    def _update_preview(self, event=None) -> None:
        """Update the session ID preview based on current input."""
        if self.experiment_entry and self.preview_label:
            experiment_name = self.experiment_entry.get().strip()
            session_id = self._generate_session_id(experiment_name)
            self.preview_label.configure(text=session_id)
            # Cache the value
            self._experiment_name_cache = experiment_name
    
    def _cache_experiment_name(self, event=None) -> None:
        """Cache the experiment name to avoid widget access issues."""
        try:
            if self.experiment_entry:
                experiment_name = self.experiment_entry.get().strip()
                self._experiment_name_cache = experiment_name
                # Also update the wizard's main cache
                if hasattr(self, 'wizard') and self.wizard:
                    session_id = self._generate_session_id(experiment_name)
                    self.wizard.update_cached_data({
                        'experiment_name': experiment_name,
                        'session_id': session_id
                    })
        except Exception as e:
            self.logger.debug(f"Error caching experiment name: {e}")
    
    def _generate_session_id(self, experiment_name: str) -> str:
        """Generate session ID with timestamp format.
        
        Args:
            experiment_name: The experiment name entered by user
            
        Returns:
            str: Formatted session ID
        """
        if not experiment_name:
            experiment_name = "unnamed_experiment"
        
        # Clean the experiment name (remove invalid characters)
        clean_name = "".join(c for c in experiment_name if c.isalnum() or c in "_-")
        if not clean_name:
            clean_name = "unnamed_experiment"
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        return f"{clean_name}_{timestamp}"
    
    def validate(self) -> bool:
        """Validate the experiment name input."""
        if not self.experiment_entry:
            return False
        
        experiment_name = self.experiment_entry.get().strip()
        
        if not experiment_name:
            self.wizard.show_error("Please enter an experiment name.")
            return False
        
        # Check for valid characters
        if not all(c.isalnum() or c in "_- " for c in experiment_name):
            self.wizard.show_error(
                "Experiment name can only contain letters, numbers, spaces, hyphens, and underscores."
            )
            return False
        
        if len(experiment_name) > 50:
            self.wizard.show_error("Experiment name must be 50 characters or less.")
            return False
        
        return True
    
    def get_data(self) -> Dict[str, Any]:
        """Get the experiment name data."""
        try:
            if not self.experiment_entry:
                return {}
            
            # Use after_idle to ensure widget is accessible
            experiment_name = ""
            try:
                experiment_name = self.experiment_entry.get().strip()
            except Exception as widget_error:
                self.logger.debug(f"Widget access error, using fallback: {widget_error}")
                # Fallback: try to get the value through the variable if available
                if hasattr(self, '_experiment_name_cache'):
                    experiment_name = self._experiment_name_cache
            
            session_id = self._generate_session_id(experiment_name)
            
            return {
                "experiment_name": experiment_name,
                "session_id": session_id
            }
        except Exception as e:
            self.logger.error(f"Error getting naming step data: {e}")
            return {}


class DataSourceStep(SetupStep):
    """Step 2: Data source selection with segmented button interface."""
    
    def __init__(self, wizard: 'SetupWizard'):
        """Initialize the data source selection step."""
        super().__init__(wizard)
        self.data_source_var: Optional[ctk.StringVar] = None
        self.segmented_button: Optional[ctk.CTkSegmentedButton] = None
        self.available_types = DataSourceFactory.get_available_types()
    
    def create_widgets(self, parent: ctk.CTkFrame) -> None:
        """Create widgets for data source selection step."""
        self.frame = parent
        
        # Title
        title_label = ctk.CTkLabel(
            parent,
            text="Step 2: Select Data Source",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Description
        desc_label = ctk.CTkLabel(
            parent,
            text="Choose the type of data source that contains your code pairs\nfor review. Each option provides different configuration methods.",
            font=ctk.CTkFont(size=12)
        )
        desc_label.pack(pady=(0, 20))
        
        # Data source selection frame
        selection_frame = ctk.CTkFrame(parent)
        selection_frame.pack(pady=10, padx=40, fill="x")
        
        selection_label = ctk.CTkLabel(
            selection_frame,
            text="Data Source Type:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        selection_label.pack(pady=(15, 10))
        
        # Create segmented button with available data source types
        self.data_source_var = ctk.StringVar(value="folders")  # Default to folders
        
        # Initialize cache
        self._data_source_cache = "folders"
        
        # Get the keys for the segmented button (folders, sqlite, excel)
        source_keys = list(self.available_types.keys())
        
        self.segmented_button = ctk.CTkSegmentedButton(
            selection_frame,
            values=source_keys,
            variable=self.data_source_var,
            command=self._on_data_source_changed
        )
        self.segmented_button.pack(pady=(0, 10))
        
        # Set initial selection
        self.segmented_button.set("folders")
        
        # Description frame for selected data source
        self.description_frame = ctk.CTkFrame(parent)
        self.description_frame.pack(pady=10, padx=40, fill="x")
        
        # Update description for initial selection
        self._update_description()
    
    def _on_data_source_changed(self, value: str) -> None:
        """Handle data source selection change.
        
        Args:
            value: Selected data source type
        """
        self.logger.debug(f"Data source changed to: {value}")
        self._data_source_cache = value  # Cache the value
        # Also update the wizard's main cache
        if hasattr(self, 'wizard') and self.wizard:
            self.wizard.update_cached_data({'data_source_type': value})
        self._update_description()
    
    def _update_description(self) -> None:
        """Update the description based on selected data source."""
        if not self.description_frame or not self.data_source_var:
            return
        
        # Clear existing description
        for widget in self.description_frame.winfo_children():
            widget.destroy()
        
        selected_type = self.data_source_var.get()
        
        # Description title
        desc_title = ctk.CTkLabel(
            self.description_frame,
            text=f"Selected: {self.available_types.get(selected_type, selected_type)}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        desc_title.pack(pady=(15, 5))
        
        # Type-specific descriptions
        descriptions = {
            "folders": (
                "Use file system folders containing your code files.\n"
                "Files are matched by base name (ignoring extensions).\n"
                "Ideal for comparing files with different extensions."
            ),
            "sqlite": (
                "Use an SQLite database containing code pairs.\n"
                "Requires a database with tables containing code columns.\n"
                "Provides structured data access and querying capabilities."
            ),
            "excel": (
                "Use Excel (.xlsx, .xls) or CSV files containing code pairs.\n"
                "Each row represents a code pair with separate columns.\n"
                "Easy to prepare and review data in spreadsheet format."
            )
        }
        
        description_text = descriptions.get(selected_type, "Unknown data source type.")
        
        desc_label = ctk.CTkLabel(
            self.description_frame,
            text=description_text,
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        desc_label.pack(pady=(0, 15), padx=10)
    
    def validate(self) -> bool:
        """Validate the data source selection."""
        if not self.data_source_var:
            self.wizard.show_error("Please select a data source type.")
            return False
        
        selected_type = self.data_source_var.get()
        
        if not DataSourceFactory.validate_source_type(selected_type):
            self.wizard.show_error(f"Invalid data source type: {selected_type}")
            return False
        
        return True
    
    def get_data(self) -> Dict[str, Any]:
        """Get the selected data source type."""
        try:
            selected_type = ""
            if self.data_source_var:
                try:
                    selected_type = self.data_source_var.get()
                except Exception as widget_error:
                    self.logger.debug(f"Widget access error, using cache: {widget_error}")
                    selected_type = getattr(self, '_data_source_cache', 'folders')
            else:
                selected_type = getattr(self, '_data_source_cache', 'folders')
            
            return {
                "data_source_type": selected_type
            }
        except Exception as e:
            self.logger.error(f"Error getting data source step data: {e}")
            return {"data_source_type": "folders"}  # Safe fallback


class ConfigurationStep(SetupStep):
    """Step 3: Dynamic data source configuration based on selection from Step 2."""
    
    def __init__(self, wizard: 'SetupWizard'):
        """Initialize the configuration step."""
        super().__init__(wizard)
        self.current_config_frame: Optional[ctk.CTkFrame] = None
        
        # Folder configuration widgets
        self.generated_folder_var: Optional[ctk.StringVar] = None
        self.expected_folder_var: Optional[ctk.StringVar] = None
        self.input_folder_var: Optional[ctk.StringVar] = None
        self.generated_folder_entry: Optional[ctk.CTkEntry] = None
        self.expected_folder_entry: Optional[ctk.CTkEntry] = None
        self.input_folder_entry: Optional[ctk.CTkEntry] = None
        
        # Database configuration widgets
        self.db_file_var: Optional[ctk.StringVar] = None
        self.db_file_entry: Optional[ctk.CTkEntry] = None
        self.table_var: Optional[ctk.StringVar] = None
        self.table_dropdown: Optional[ctk.CTkComboBox] = None
        self.identifier_column_var: Optional[ctk.StringVar] = None
        self.identifier_column_dropdown: Optional[ctk.CTkComboBox] = None
        self.generated_column_var: Optional[ctk.StringVar] = None
        self.generated_column_dropdown: Optional[ctk.CTkComboBox] = None
        self.expected_column_var: Optional[ctk.StringVar] = None
        self.expected_column_dropdown: Optional[ctk.CTkComboBox] = None
        
        # Excel configuration widgets
        self.excel_file_var: Optional[ctk.StringVar] = None
        self.excel_file_entry: Optional[ctk.CTkEntry] = None
        self.sheet_var: Optional[ctk.StringVar] = None
        self.sheet_dropdown: Optional[ctk.CTkComboBox] = None
        self.excel_identifier_column_var: Optional[ctk.StringVar] = None
        self.excel_identifier_column_dropdown: Optional[ctk.CTkComboBox] = None
        self.excel_generated_column_var: Optional[ctk.StringVar] = None
        self.excel_generated_column_dropdown: Optional[ctk.CTkComboBox] = None
        self.excel_expected_column_var: Optional[ctk.StringVar] = None
        self.excel_expected_column_dropdown: Optional[ctk.CTkComboBox] = None
        self.excel_input_column_var: Optional[ctk.StringVar] = None
        self.excel_input_column_dropdown: Optional[ctk.CTkComboBox] = None
        
        # Loading indicator
        self.loading_label: Optional[ctk.CTkLabel] = None
    
    def create_widgets(self, parent: ctk.CTkFrame) -> None:
        """Create widgets for configuration step."""
        self.frame = parent
        
        # Title
        title_label = ctk.CTkLabel(
            parent,
            text="Step 3: Configure Data Source",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Description
        desc_label = ctk.CTkLabel(
            parent,
            text="Configure the selected data source with specific paths and settings.",
            font=ctk.CTkFont(size=12)
        )
        desc_label.pack(pady=(0, 20))
        
        # Configuration content frame (will be populated based on data source type)
        self.current_config_frame = ctk.CTkFrame(parent)
        self.current_config_frame.pack(pady=10, padx=40, fill="both", expand=True)
        
        # Update content based on selected data source
        self._update_configuration_content()
    
    def _update_configuration_content(self) -> None:
        """Update configuration content based on selected data source type."""
        if not self.current_config_frame:
            return
        
        # Clear existing content
        for widget in self.current_config_frame.winfo_children():
            widget.destroy()
        
        # Get data source type from previous step
        data_source_type = self._get_selected_data_source_type()
        
        if data_source_type == "folders":
            self._create_folder_configuration()
        elif data_source_type == "sqlite":
            self._create_database_configuration()
        elif data_source_type == "excel":
            self._create_excel_configuration()
        else:
            # Fallback for unknown type
            error_label = ctk.CTkLabel(
                self.current_config_frame,
                text=f"Unknown data source type: {data_source_type}",
                font=ctk.CTkFont(size=12),
                text_color="red"
            )
            error_label.pack(pady=20)
    
    def _get_selected_data_source_type(self) -> str:
        """Get the selected data source type from the previous step."""
        # Find the DataSourceStep and get its selection
        for step in self.wizard.steps:
            if isinstance(step, DataSourceStep):
                step_data = step.get_data()
                return step_data.get("data_source_type", "folders")
        return "folders"  # Default fallback
    
    def _create_folder_configuration(self) -> None:
        """Create folder configuration interface."""
        # Title
        config_title = ctk.CTkLabel(
            self.current_config_frame,
            text="Configure Folder Paths",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        config_title.pack(pady=(10, 8))
        
        # Generated Code Folder (mandatory)
        gen_frame = ctk.CTkFrame(self.current_config_frame)
        gen_frame.pack(pady=8, padx=15, fill="x")
        
        gen_label = ctk.CTkLabel(
            gen_frame,
            text="Generated Code Folder (Required):",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        gen_label.pack(pady=(12, 4), anchor="w")
        
        gen_path_frame = ctk.CTkFrame(gen_frame)
        gen_path_frame.pack(pady=(0, 12), padx=8, fill="x")
        
        self.generated_folder_var = ctk.StringVar()
        self.generated_folder_entry = ctk.CTkEntry(
            gen_path_frame,
            textvariable=self.generated_folder_var,
            placeholder_text="Select folder containing generated code files...",
            state="readonly",
            font=ctk.CTkFont(size=11)
        )
        self.generated_folder_entry.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=8)
        
        gen_browse_button = ctk.CTkButton(
            gen_path_frame,
            text="📁 Browse...",
            command=self._browse_generated_folder,
            width=80
        )
        gen_browse_button.pack(side="right", padx=(4, 8), pady=8)
        
        # Expected Code Folder (optional)
        exp_frame = ctk.CTkFrame(self.current_config_frame)
        exp_frame.pack(pady=8, padx=15, fill="x")
        
        exp_label = ctk.CTkLabel(
            exp_frame,
            text="Expected Code Folder (Optional):",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        exp_label.pack(pady=(12, 4), anchor="w")
        
        exp_path_frame = ctk.CTkFrame(exp_frame)
        exp_path_frame.pack(pady=(0, 12), padx=8, fill="x")
        
        self.expected_folder_var = ctk.StringVar()
        self.expected_folder_entry = ctk.CTkEntry(
            exp_path_frame,
            textvariable=self.expected_folder_var,
            placeholder_text="Select folder containing expected code files (optional)...",
            state="readonly",
            font=ctk.CTkFont(size=11)
        )
        self.expected_folder_entry.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=8)
        
        exp_browse_button = ctk.CTkButton(
            exp_path_frame,
            text="📁 Browse...",
            command=self._browse_expected_folder,
            width=80
        )
        exp_browse_button.pack(side="right", padx=(4, 8), pady=8)
        
        # Input Code Folder (optional)
        input_frame = ctk.CTkFrame(self.current_config_frame)
        input_frame.pack(pady=8, padx=15, fill="x")
        
        input_label = ctk.CTkLabel(
            input_frame,
            text="Input Code Folder (Optional):",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        input_label.pack(pady=(12, 4), anchor="w")
        
        input_path_frame = ctk.CTkFrame(input_frame)
        input_path_frame.pack(pady=(0, 12), padx=8, fill="x")
        
        self.input_folder_var = ctk.StringVar()
        self.input_folder_entry = ctk.CTkEntry(
            input_path_frame,
            textvariable=self.input_folder_var,
            placeholder_text="Select folder containing input code files (optional)...",
            state="readonly",
            font=ctk.CTkFont(size=11)
        )
        self.input_folder_entry.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=8)
        
        input_browse_button = ctk.CTkButton(
            input_path_frame,
            text="📁 Browse...",
            command=self._browse_input_folder,
            width=80
        )
        input_browse_button.pack(side="right", padx=(4, 8), pady=8)
        
        # Help text
        help_label = ctk.CTkLabel(
            self.current_config_frame,
            text="Files are matched by base name (ignoring extensions).\n"
                 "Generated code folder is required. Expected and input code folders are optional.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        help_label.pack(pady=(8, 12))
    
    def _browse_generated_folder(self) -> None:
        """Browse for generated code folder."""
        try:
            from tkinter import filedialog
            
            folder_path = filedialog.askdirectory(
                title="Select Generated Code Folder",
                initialdir=self.generated_folder_var.get() if self.generated_folder_var.get() else None
            )
            
            if folder_path:
                self.generated_folder_var.set(folder_path)
                self.logger.info(f"Selected generated code folder: {folder_path}")
                # Cache the value immediately
                if hasattr(self, 'wizard') and self.wizard:
                    self.wizard.update_cached_data({'generated_code_path': folder_path})
        
        except Exception as e:
            self.logger.error(f"Error browsing for generated folder: {e}")
            self.wizard.show_error(f"Error selecting folder: {str(e)}")
    
    def _browse_expected_folder(self) -> None:
        """Browse for expected code folder."""
        try:
            from tkinter import filedialog
            
            folder_path = filedialog.askdirectory(
                title="Select Expected Code Folder",
                initialdir=self.expected_folder_var.get() if self.expected_folder_var.get() else None
            )
            
            if folder_path:
                self.expected_folder_var.set(folder_path)
                self.logger.info(f"Selected expected code folder: {folder_path}")
                # Cache the value immediately
                if hasattr(self, 'wizard') and self.wizard:
                    self.wizard.update_cached_data({'expected_code_path': folder_path})
        
        except Exception as e:
            self.logger.error(f"Error browsing for expected folder: {e}")
            self.wizard.show_error(f"Error selecting folder: {str(e)}")
    
    def _browse_input_folder(self) -> None:
        """Browse for input code folder."""
        try:
            from tkinter import filedialog
            
            folder_path = filedialog.askdirectory(
                title="Select Input Code Folder",
                initialdir=self.input_folder_var.get() if self.input_folder_var.get() else None
            )
            
            if folder_path:
                self.input_folder_var.set(folder_path)
                self.logger.info(f"Selected input code folder: {folder_path}")
                # Cache the value immediately
                if hasattr(self, 'wizard') and self.wizard:
                    self.wizard.update_cached_data({'input_code_path': folder_path})
        
        except Exception as e:
            self.logger.error(f"Error browsing for input folder: {e}")
            self.wizard.show_error(f"Error selecting folder: {str(e)}")
    
    def _create_database_configuration(self) -> None:
        """Create SQLite database configuration interface."""
        # Title
        config_title = ctk.CTkLabel(
            self.current_config_frame,
            text="Configure SQLite Database",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        config_title.pack(pady=(10, 8))
        
        # Database File Selection
        db_frame = ctk.CTkFrame(self.current_config_frame)
        db_frame.pack(pady=8, padx=15, fill="x")
        
        db_label = ctk.CTkLabel(
            db_frame,
            text="Database File:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        db_label.pack(pady=(15, 5), anchor="w")
        
        db_path_frame = ctk.CTkFrame(db_frame)
        db_path_frame.pack(pady=(0, 15), padx=10, fill="x")
        
        self.db_file_var = ctk.StringVar()
        self.db_file_entry = ctk.CTkEntry(
            db_path_frame,
            textvariable=self.db_file_var,
            placeholder_text="Select SQLite database file...",
            state="readonly",
            font=ctk.CTkFont(size=11)
        )
        self.db_file_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        
        db_browse_button = ctk.CTkButton(
            db_path_frame,
            text="📁 Browse...",
            command=self._browse_database_file,
            width=80
        )
        db_browse_button.pack(side="right", padx=(5, 10), pady=10)
        
        # Table and Column Selection (initially disabled)
        selection_frame = ctk.CTkFrame(self.current_config_frame)
        selection_frame.pack(pady=10, padx=20, fill="x")
        
        # Table selection
        table_label = ctk.CTkLabel(
            selection_frame,
            text="Table:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        table_label.pack(pady=(15, 5), anchor="w")
        
        self.table_var = ctk.StringVar()
        self.table_dropdown = ctk.CTkComboBox(
            selection_frame,
            variable=self.table_var,
            values=["Select database file first..."],
            state="disabled",
            command=self._on_table_selected
        )
        self.table_dropdown.pack(pady=(0, 10), padx=10, fill="x")
        
        # Column selections
        columns_frame = ctk.CTkFrame(selection_frame)
        columns_frame.pack(pady=(0, 15), padx=10, fill="x")
        
        # Identifier column (optional - auto-detected)
        id_label = ctk.CTkLabel(
            columns_frame,
            text="Identifier Column (Optional - Auto-detected):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        id_label.pack(pady=(10, 2), anchor="w")
        
        self.identifier_column_var = ctk.StringVar()
        self.identifier_column_dropdown = ctk.CTkComboBox(
            columns_frame,
            variable=self.identifier_column_var,
            values=["Select table first..."],
            state="disabled"
        )
        self.identifier_column_dropdown.pack(pady=(0, 5), fill="x")
        
        # Generated code column
        gen_col_label = ctk.CTkLabel(
            columns_frame,
            text="Generated Code Column:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        gen_col_label.pack(pady=(5, 2), anchor="w")
        
        self.generated_column_var = ctk.StringVar()
        self.generated_column_dropdown = ctk.CTkComboBox(
            columns_frame,
            variable=self.generated_column_var,
            values=["Select table first..."],
            state="disabled"
        )
        self.generated_column_dropdown.pack(pady=(0, 5), fill="x")
        
        # Expected code column (optional)
        exp_col_label = ctk.CTkLabel(
            columns_frame,
            text="Expected Code Column (Optional):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        exp_col_label.pack(pady=(5, 2), anchor="w")
        
        self.expected_column_var = ctk.StringVar()
        self.expected_column_dropdown = ctk.CTkComboBox(
            columns_frame,
            variable=self.expected_column_var,
            values=["Select table first..."],
            state="disabled"
        )
        self.expected_column_dropdown.pack(pady=(0, 5), fill="x")
        
        # Input code column (optional)
        input_col_label = ctk.CTkLabel(
            columns_frame,
            text="Input Code Column (Optional):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        input_col_label.pack(pady=(5, 2), anchor="w")
        
        self.input_column_var = ctk.StringVar()
        self.input_column_dropdown = ctk.CTkComboBox(
            columns_frame,
            variable=self.input_column_var,
            values=["Select table first..."],
            state="disabled"
        )
        self.input_column_dropdown.pack(pady=(0, 10), fill="x")
        
        # Loading indicator (initially hidden)
        self.loading_label = ctk.CTkLabel(
            self.current_config_frame,
            text="Loading database information...",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        # Don't pack initially - will be shown during loading
    
    def _browse_database_file(self) -> None:
        """Browse for SQLite database file."""
        try:
            from tkinter import filedialog
            
            file_path = filedialog.askopenfilename(
                title="Select SQLite Database File",
                filetypes=[
                    ("SQLite Database", "*.db *.sqlite *.sqlite3"),
                    ("All Files", "*.*")
                ],
                initialdir=None
            )
            
            if file_path:
                self.db_file_var.set(file_path)
                self.logger.info(f"Selected database file: {file_path}")
                
                # Load database information
                self._load_database_info(file_path)
        
        except Exception as e:
            self.logger.error(f"Error browsing for database file: {e}")
            self.wizard.show_error(f"Error selecting database file: {str(e)}")
    
    def _load_database_info(self, db_path: str) -> None:
        """Load database tables and enable table selection with progress feedback."""
        from .progress_widgets import show_loading_dialog, ProgressInfo, ProgressState
        from .error_handler import GUIErrorHandler
        import threading
        import sqlite3
        import os
        
        # Check memory constraints before loading
        if not GUIErrorHandler.check_memory_constraints(self.wizard, "loading database"):
            return
        
        # Show progress dialog
        progress_dialog = show_loading_dialog(
            self.wizard,
            title="Loading Database",
            message="Connecting to database and loading table information...",
            can_cancel=True
        )
        
        def load_database_worker():
            """Worker function to load database in background thread."""
            try:
                # Check file size for performance warning
                file_size_mb = os.path.getsize(db_path) / (1024 * 1024)
                if file_size_mb > 50:  # 50MB threshold
                    from .error_handler import show_performance_warning
                    if not show_performance_warning(self.wizard, "database loading", file_size_mb):
                        return
                
                # Update progress
                progress_info = ProgressInfo(
                    current=1,
                    total=3,
                    message="Connecting to database...",
                    percentage=33.0,
                    state=ProgressState.RUNNING
                )
                progress_dialog.update_progress(progress_info)
                
                # Check for cancellation
                if progress_dialog.is_cancelled:
                    return
                
                # Connect to database
                with sqlite3.connect(db_path, timeout=10.0) as conn:
                    # Update progress
                    progress_info.current = 2
                    progress_info.message = "Loading table information..."
                    progress_info.percentage = 66.0
                    progress_dialog.update_progress(progress_info)
                    
                    # Check for cancellation
                    if progress_dialog.is_cancelled:
                        return
                    
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                    tables = [row[0] for row in cursor.fetchall()]
                
                # Update progress
                progress_info.current = 3
                progress_info.message = f"Loaded {len(tables)} tables successfully"
                progress_info.percentage = 100.0
                progress_info.state = ProgressState.COMPLETED
                progress_dialog.update_progress(progress_info)
                
                # Update UI on main thread
                def update_ui():
                    try:
                        if tables:
                            # Update table dropdown
                            self.table_dropdown.configure(values=tables, state="normal")
                            self.table_dropdown.set("Select a table...")
                            
                            # Reset column dropdowns
                            self._reset_column_dropdowns()
                            
                            self.logger.info(f"Loaded {len(tables)} tables from database")
                        else:
                            GUIErrorHandler.show_error_dialog(
                                self.wizard,
                                "No Tables Found",
                                "No tables found in the selected database.",
                                "The database may be empty or corrupted."
                            )
                            self.table_dropdown.configure(values=["No tables found"], state="disabled")
                    except Exception as e:
                        self.logger.error(f"Error updating UI after database load: {e}")
                
                self.wizard.after(100, update_ui)
                
            except sqlite3.OperationalError as e:
                self.logger.error(f"Database operational error: {e}")
                
                def show_db_error():
                    from .error_handler import show_database_error
                    if show_database_error(self.wizard, db_path, e):
                        # User wants to try again
                        self.wizard.after(100, lambda: self._browse_database_file())
                    else:
                        self.table_dropdown.configure(values=["Database error"], state="disabled")
                
                self.wizard.after(100, show_db_error)
                
            except Exception as e:
                self.logger.error(f"Error loading database info: {e}")
                
                def show_error():
                    GUIErrorHandler.show_error_dialog(
                        self.wizard,
                        "Database Loading Error",
                        f"Error loading database information: {str(e)}",
                        "Please check that the file is a valid SQLite database and try again."
                    )
                    self.table_dropdown.configure(values=["Error loading tables"], state="disabled")
                
                self.wizard.after(100, show_error)
            
            finally:
                # Close progress dialog
                self.wizard.after(100, progress_dialog.destroy)
        
        # Start loading in background thread
        loading_thread = threading.Thread(target=load_database_worker, daemon=True)
        loading_thread.start()
    
    def _on_table_selected(self, table_name: str) -> None:
        """Handle table selection and load column information with progress feedback."""
        if not table_name or table_name in ["Select a table...", "No tables found", "Error loading tables"]:
            return
        
        from .progress_widgets import LoadingIndicator
        import threading
        import sqlite3
        
        # Create loading indicator
        loading_indicator = LoadingIndicator(self.current_config_frame, f"Loading columns for table '{table_name}'...")
        loading_indicator.pack(pady=10)
        loading_indicator.start()
        
        def load_columns_worker():
            """Worker function to load columns in background thread."""
            try:
                db_path = self.db_file_var.get()
                
                # Get column information
                with sqlite3.connect(db_path, timeout=5.0) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor.fetchall()]  # Column name is at index 1
                
                # Update UI on main thread
                def update_columns_ui():
                    try:
                        if columns:
                            # Update column dropdowns with auto-detection
                            self._update_sqlite_columns_with_autodetection(columns)
                            
                            self.logger.info(f"Loaded {len(columns)} columns from table '{table_name}'")
                        else:
                            from .error_handler import GUIErrorHandler
                            GUIErrorHandler.show_error_dialog(
                                self.wizard,
                                "No Columns Found",
                                f"No columns found in table '{table_name}'.",
                                "The table may be empty or have an invalid structure."
                            )
                            self._reset_column_dropdowns()
                    except Exception as e:
                        self.logger.error(f"Error updating columns UI: {e}")
                    finally:
                        # Remove loading indicator
                        loading_indicator.stop()
                        loading_indicator.destroy()
                
                self.wizard.after(100, update_columns_ui)
                
            except Exception as e:
                self.logger.error(f"Error loading column info: {e}")
                
                def show_column_error():
                    from .error_handler import GUIErrorHandler
                    GUIErrorHandler.show_error_dialog(
                        self.wizard,
                        "Column Loading Error",
                        f"Error loading column information for table '{table_name}': {str(e)}",
                        "Please check the database connection and try again."
                    )
                    self._reset_column_dropdowns()
                    loading_indicator.stop()
                    loading_indicator.destroy()
                
                self.wizard.after(100, show_column_error)
        
        # Start loading in background thread
        loading_thread = threading.Thread(target=load_columns_worker, daemon=True)
        loading_thread.start()
    
    def _reset_column_dropdowns(self) -> None:
        """Reset column dropdowns to initial state."""
        try:
            self.identifier_column_dropdown.configure(values=["Select table first..."], state="disabled")
            self.identifier_column_dropdown.set("Select table first...")
            
            self.generated_column_dropdown.configure(values=["Select table first..."], state="disabled")
            self.generated_column_dropdown.set("Select table first...")
            
            self.expected_column_dropdown.configure(values=["Select table first..."], state="disabled")
            self.expected_column_dropdown.set("Select table first...")
            
            self.input_column_dropdown.configure(values=["Select table first..."], state="disabled")
            self.input_column_dropdown.set("Select table first...")
        except Exception as e:
            self.logger.error(f"Error resetting column dropdowns: {e}")
            self.loading_label.pack_forget()
    
    def _auto_detect_id_column(self, columns: list) -> Optional[str]:
        """Auto-detect the ID column from available columns.
        
        Args:
            columns: List of available column names
            
        Returns:
            str: The detected ID column name, or None if not found
        """
        # Common ID column patterns
        id_patterns = ['id', 'ID', 'Id', 'identifier', 'row_id', 'record_id', 'pk', 'primary_key']
        
        # First, look for exact matches
        for pattern in id_patterns:
            if pattern in columns:
                return pattern
        
        # Then, look for columns that contain ID patterns
        for column in columns:
            column_lower = column.lower()
            if any(pattern.lower() in column_lower for pattern in id_patterns):
                return column
        
        # If no ID column found, return the first column (common convention)
        return columns[0] if columns else None
    
    def _auto_detect_generated_code_column(self, columns: list) -> Optional[str]:
        """Auto-detect the generated code column from available columns.
        
        Args:
            columns: List of available column names
            
        Returns:
            str: The detected generated code column name, or None if not found
        """
        # Common generated code column patterns
        generated_patterns = [
            'generated_code', 'generated', 'output_code', 'result_code', 'code_generated',
            'ai_code', 'model_output', 'prediction', 'response', 'completion',
            'generated_text', 'output', 'result', 'answer'
        ]
        
        # First, look for exact matches
        for pattern in generated_patterns:
            if pattern in columns:
                return pattern
        
        # Then, look for columns that contain generated patterns
        for column in columns:
            column_lower = column.lower()
            if any(pattern in column_lower for pattern in generated_patterns):
                return column
        
        return None
    
    def _auto_detect_expected_code_column(self, columns: list) -> Optional[str]:
        """Auto-detect the expected code column from available columns.
        
        Args:
            columns: List of available column names
            
        Returns:
            str: The detected expected code column name, or None if not found
        """
        # Common expected code column patterns
        expected_patterns = [
            'expected_code', 'expected', 'reference_code', 'target_code', 'ground_truth',
            'correct_code', 'solution', 'answer', 'reference', 'target',
            'expected_output', 'gold_standard', 'truth', 'label'
        ]
        
        # First, look for exact matches
        for pattern in expected_patterns:
            if pattern in columns:
                return pattern
        
        # Then, look for columns that contain expected patterns
        for column in columns:
            column_lower = column.lower()
            if any(pattern in column_lower for pattern in expected_patterns):
                return column
        
        return None
    
    def _auto_detect_input_code_column(self, columns: list) -> Optional[str]:
        """Auto-detect the input code column from available columns.
        
        Args:
            columns: List of available column names
            
        Returns:
            str: The detected input code column name, or None if not found
        """
        # Common input code column patterns
        input_patterns = [
            'input_code', 'original_code', 'source_code', 'input', 'original',
            'source', 'prompt', 'query', 'request', 'initial_code',
            'base_code', 'starting_code', 'raw_code', 'user_input'
        ]
        
        # First, look for exact matches
        for pattern in input_patterns:
            if pattern in columns:
                return pattern
        
        # Then, look for columns that contain input patterns
        for column in columns:
            column_lower = column.lower()
            if any(pattern in column_lower for pattern in input_patterns):
                return column
        
        return None
    
    def _update_sqlite_columns_with_autodetection(self, columns: list) -> None:
        """Update SQLite column dropdowns with auto-detection for all column types.
        
        Args:
            columns: List of available column names
        """
        # Auto-detect all column types
        id_column = self._auto_detect_id_column(columns)
        generated_column = self._auto_detect_generated_code_column(columns)
        expected_column = self._auto_detect_expected_code_column(columns)
        input_column = self._auto_detect_input_code_column(columns)
        
        # Update identifier column dropdown
        self.identifier_column_dropdown.configure(values=["(Auto-detect)"] + columns, state="normal")
        if id_column:
            self.identifier_column_dropdown.set(id_column)
            self.logger.info(f"Auto-detected ID column: {id_column}")
        else:
            self.identifier_column_dropdown.set("(Auto-detect)")
        
        # Update generated code column dropdown
        self.generated_column_dropdown.configure(values=columns, state="normal")
        if generated_column:
            self.generated_column_dropdown.set(generated_column)
            self.logger.info(f"Auto-detected generated code column: {generated_column}")
        else:
            self.generated_column_dropdown.set("Select column...")
        
        # Update expected code column dropdown
        self.expected_column_dropdown.configure(values=["(None)"] + columns, state="normal")
        if expected_column:
            self.expected_column_dropdown.set(expected_column)
            self.logger.info(f"Auto-detected expected code column: {expected_column}")
        else:
            self.expected_column_dropdown.set("(None)")
        
        # Update input code column dropdown
        self.input_column_dropdown.configure(values=["(None)"] + columns, state="normal")
        if input_column:
            self.input_column_dropdown.set(input_column)
            self.logger.info(f"Auto-detected input code column: {input_column}")
        else:
            self.input_column_dropdown.set("(None)")
        
        # Show summary of auto-detections
        detections = []
        if id_column:
            detections.append(f"ID: {id_column}")
        if generated_column:
            detections.append(f"Generated: {generated_column}")
        if expected_column:
            detections.append(f"Expected: {expected_column}")
        if input_column:
            detections.append(f"Input: {input_column}")
        
        if detections:
            self.logger.info(f"Auto-detected columns - {', '.join(detections)}")
        else:
            self.logger.info("No columns auto-detected, manual selection required")
    
    def _reset_column_dropdowns(self) -> None:
        """Reset all column dropdowns to disabled state."""
        for dropdown in [self.identifier_column_dropdown, self.generated_column_dropdown, self.expected_column_dropdown, self.input_column_dropdown]:
            if dropdown:
                dropdown.configure(values=["Select table first..."], state="disabled")
                dropdown.set("Select table first...")
    
    def _create_excel_configuration(self) -> None:
        """Create Excel/CSV configuration interface."""
        # Title
        config_title = ctk.CTkLabel(
            self.current_config_frame,
            text="Configure Excel/CSV File",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        config_title.pack(pady=(10, 8))
        
        # File Selection
        file_frame = ctk.CTkFrame(self.current_config_frame)
        file_frame.pack(pady=8, padx=15, fill="x")
        
        file_label = ctk.CTkLabel(
            file_frame,
            text="Excel/CSV File:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        file_label.pack(pady=(12, 4), anchor="w")
        
        file_path_frame = ctk.CTkFrame(file_frame)
        file_path_frame.pack(pady=(0, 12), padx=8, fill="x")
        
        self.excel_file_var = ctk.StringVar()
        self.excel_file_entry = ctk.CTkEntry(
            file_path_frame,
            textvariable=self.excel_file_var,
            placeholder_text="Select Excel (.xlsx, .xls) or CSV file...",
            state="readonly",
            font=ctk.CTkFont(size=11)
        )
        self.excel_file_entry.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=8)
        
        file_browse_button = ctk.CTkButton(
            file_path_frame,
            text="📁 Browse...",
            command=self._browse_excel_file,
            width=80
        )
        file_browse_button.pack(side="right", padx=(4, 8), pady=8)
        
        # Sheet and Column Selection (initially disabled)
        selection_frame = ctk.CTkFrame(self.current_config_frame)
        selection_frame.pack(pady=8, padx=15, fill="x")
        
        # Sheet selection (for Excel files only)
        sheet_label = ctk.CTkLabel(
            selection_frame,
            text="Sheet (Excel only):",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        sheet_label.pack(pady=(12, 4), anchor="w")
        
        self.sheet_var = ctk.StringVar()
        self.sheet_dropdown = ctk.CTkComboBox(
            selection_frame,
            variable=self.sheet_var,
            values=["Select Excel file first..."],
            state="disabled"
        )
        self.sheet_dropdown.pack(pady=(0, 8), padx=8, fill="x")
        
        # Column selections
        columns_frame = ctk.CTkFrame(selection_frame)
        columns_frame.pack(pady=(0, 12), padx=8, fill="x")
        
        # Identifier column
        id_label = ctk.CTkLabel(
            columns_frame,
            text="Identifier Column:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        id_label.pack(pady=(8, 2), anchor="w")
        
        self.excel_identifier_column_var = ctk.StringVar()
        self.excel_identifier_column_dropdown = ctk.CTkComboBox(
            columns_frame,
            variable=self.excel_identifier_column_var,
            values=["Select file first..."],
            state="disabled"
        )
        self.excel_identifier_column_dropdown.pack(pady=(0, 4), fill="x")
        
        # Generated code column
        gen_col_label = ctk.CTkLabel(
            columns_frame,
            text="Generated Code Column:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        gen_col_label.pack(pady=(4, 2), anchor="w")
        
        self.excel_generated_column_var = ctk.StringVar()
        self.excel_generated_column_dropdown = ctk.CTkComboBox(
            columns_frame,
            variable=self.excel_generated_column_var,
            values=["Select file first..."],
            state="disabled"
        )
        self.excel_generated_column_dropdown.pack(pady=(0, 4), fill="x")
        
        # Expected code column (optional)
        exp_col_label = ctk.CTkLabel(
            columns_frame,
            text="Expected Code Column (Optional):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        exp_col_label.pack(pady=(4, 2), anchor="w")
        
        self.excel_expected_column_var = ctk.StringVar()
        self.excel_expected_column_dropdown = ctk.CTkComboBox(
            columns_frame,
            variable=self.excel_expected_column_var,
            values=["Select file first..."],
            state="disabled"
        )
        self.excel_expected_column_dropdown.pack(pady=(0, 4), fill="x")
        
        # Input code column (optional)
        input_col_label = ctk.CTkLabel(
            columns_frame,
            text="Input Code Column (Optional):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        input_col_label.pack(pady=(4, 2), anchor="w")
        
        self.excel_input_column_var = ctk.StringVar()
        self.excel_input_column_dropdown = ctk.CTkComboBox(
            columns_frame,
            variable=self.excel_input_column_var,
            values=["Select file first..."],
            state="disabled"
        )
        self.excel_input_column_dropdown.pack(pady=(0, 8), fill="x")
        
        # Loading indicator (initially hidden)
        if not self.loading_label:
            self.loading_label = ctk.CTkLabel(
                self.current_config_frame,
                text="Loading file information...",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
    
    def _browse_excel_file(self) -> None:
        """Browse for Excel/CSV file."""
        try:
            from tkinter import filedialog
            
            file_path = filedialog.askopenfilename(
                title="Select Excel or CSV File",
                filetypes=[
                    ("Excel Files", "*.xlsx *.xls"),
                    ("CSV Files", "*.csv"),
                    ("All Supported", "*.xlsx *.xls *.csv"),
                    ("All Files", "*.*")
                ],
                initialdir=None
            )
            
            if file_path:
                self.excel_file_var.set(file_path)
                self.logger.info(f"Selected Excel/CSV file: {file_path}")
                
                # Load file information
                self._load_excel_info(file_path)
        
        except Exception as e:
            self.logger.error(f"Error browsing for Excel/CSV file: {e}")
            self.wizard.show_error(f"Error selecting file: {str(e)}")
    
    def _load_excel_info(self, file_path: str) -> None:
        """Load Excel/CSV file information and enable selections."""
        try:
            # Show loading indicator
            self.loading_label.pack(pady=10)
            self.current_config_frame.update()
            
            import pandas as pd
            import os
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv':
                # CSV file - no sheets, load columns directly
                df = pd.read_csv(file_path, nrows=0)  # Just get column names
                columns = list(df.columns)
                
                # Disable sheet selection for CSV
                self.sheet_dropdown.configure(values=["N/A (CSV file)"], state="disabled")
                self.sheet_dropdown.set("N/A (CSV file)")
                
                # Enable column selection
                self._update_excel_column_dropdowns(columns)
                
            elif file_ext in ['.xlsx', '.xls']:
                # Excel file - get sheets first
                excel_file = pd.ExcelFile(file_path)
                sheets = excel_file.sheet_names
                
                if sheets:
                    # Enable sheet selection
                    self.sheet_dropdown.configure(values=sheets, state="normal")
                    if len(sheets) == 1:
                        # Auto-select if only one sheet
                        self.sheet_dropdown.set(sheets[0])
                        self.logger.info(f"Auto-selecting single sheet: {sheets[0]}")
                        self._load_excel_sheet_columns(file_path, sheets[0])
                    else:
                        self.sheet_dropdown.set("Select a sheet...")
                        # Set up callback for sheet selection
                        def on_sheet_selected(sheet_name):
                            if sheet_name and sheet_name not in ["Select a sheet...", "Select Excel file first..."]:
                                self._load_excel_sheet_columns(file_path, sheet_name)
                        self.sheet_dropdown.configure(command=on_sheet_selected)
                else:
                    self.wizard.show_error("No sheets found in the Excel file.")
            else:
                self.wizard.show_error(f"Unsupported file format: {file_ext}")
        
        except Exception as e:
            self.logger.error(f"Error loading Excel/CSV info: {e}")
            self.wizard.show_error(f"Error loading file information: {str(e)}")
        
        finally:
            # Hide loading indicator
            self.loading_label.pack_forget()
    
    def _load_excel_sheet_columns(self, file_path: str, sheet_name: str) -> None:
        """Load columns from selected Excel sheet."""
        if not sheet_name or sheet_name in ["Select a sheet...", "N/A (CSV file)"]:
            self.logger.debug(f"Skipping column loading for sheet: {sheet_name}")
            return
        
        try:
            self.logger.info(f"Loading columns from sheet '{sheet_name}' in file: {file_path}")
            
            # Show loading indicator
            if self.loading_label:
                self.loading_label.pack(pady=10)
                self.current_config_frame.update()
            
            import pandas as pd
            
            # Load just the column names
            df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=0)
            columns = list(df.columns)
            
            self.logger.info(f"Found {len(columns)} columns: {columns}")
            
            # Enable column selection
            self._update_excel_column_dropdowns(columns)
            
            self.logger.info(f"Successfully loaded {len(columns)} columns from sheet '{sheet_name}'")
        
        except Exception as e:
            self.logger.error(f"Error loading sheet columns: {e}")
            self.wizard.show_error(f"Error loading sheet information: {str(e)}")
        
        finally:
            # Hide loading indicator
            if self.loading_label:
                self.loading_label.pack_forget()
    
    def _update_excel_column_dropdowns(self, columns: list) -> None:
        """Update Excel column dropdowns with available columns."""
        if columns:
            self.logger.info(f"Updating Excel column dropdowns with {len(columns)} columns")
            
            # Update column dropdowns
            if self.excel_identifier_column_dropdown:
                self.excel_identifier_column_dropdown.configure(values=columns, state="normal")
                self.excel_identifier_column_dropdown.set("Select column...")
                self.logger.debug("Updated identifier column dropdown")
            
            if self.excel_generated_column_dropdown:
                self.excel_generated_column_dropdown.configure(values=columns, state="normal")
                self.excel_generated_column_dropdown.set("Select column...")
                self.logger.debug("Updated generated code column dropdown")
            
            # Add "None (skip)" option for optional expected column
            expected_values = ["None (skip)"] + columns
            if self.excel_expected_column_dropdown:
                self.excel_expected_column_dropdown.configure(values=expected_values, state="normal")
                self.excel_expected_column_dropdown.set("None (skip)")
                self.logger.debug("Updated expected code column dropdown")
            
            # Add "None (skip)" option for optional input column
            input_values = ["None (skip)"] + columns
            if self.excel_input_column_dropdown:
                self.excel_input_column_dropdown.configure(values=input_values, state="normal")
                self.excel_input_column_dropdown.set("None (skip)")
                self.logger.debug("Updated input code column dropdown")
            
            # Try to auto-suggest common column mappings
            self._auto_suggest_column_mappings(columns)
            
            self.logger.info("Excel column dropdowns updated successfully")
        else:
            self.logger.error("No columns provided to update dropdowns")
            self.wizard.show_error("No columns found in the selected file/sheet.")
    
    def _auto_suggest_column_mappings(self, columns: list) -> None:
        """Auto-suggest column mappings based on common column names."""
        try:
            # Use the same detection methods as SQLite for consistency
            id_column = self._auto_detect_id_column(columns)
            generated_column = self._auto_detect_generated_code_column(columns)
            expected_column = self._auto_detect_expected_code_column(columns)
            input_column = self._auto_detect_input_code_column(columns)
            
            # Auto-suggest identifier column
            if id_column and self.excel_identifier_column_dropdown:
                self.excel_identifier_column_dropdown.set(id_column)
                self.logger.info(f"Auto-suggested identifier column: {id_column}")
            
            # Auto-suggest generated code column
            if generated_column and self.excel_generated_column_dropdown:
                self.excel_generated_column_dropdown.set(generated_column)
                self.logger.info(f"Auto-suggested generated code column: {generated_column}")
            
            # Auto-suggest expected code column
            if expected_column and self.excel_expected_column_dropdown:
                self.excel_expected_column_dropdown.set(expected_column)
                self.logger.info(f"Auto-suggested expected code column: {expected_column}")
            
            # Auto-suggest input code column
            if input_column and self.excel_input_column_dropdown:
                self.excel_input_column_dropdown.set(input_column)
                self.logger.info(f"Auto-suggested input code column: {input_column}")
            
            # Show summary of auto-detections
            detections = []
            if id_column:
                detections.append(f"ID: {id_column}")
            if generated_column:
                detections.append(f"Generated: {generated_column}")
            if expected_column:
                detections.append(f"Expected: {expected_column}")
            
            if detections:
                self.logger.info(f"Auto-detected Excel columns - {', '.join(detections)}")
                    
        except Exception as e:
            self.logger.debug(f"Error in auto-suggestion: {e}")
            # Don't show error to user as this is just a convenience feature
    
    def validate(self) -> bool:
        """Validate the configuration based on selected data source type."""
        data_source_type = self._get_selected_data_source_type()
        
        if data_source_type == "folders":
            return self._validate_folder_configuration()
        elif data_source_type == "sqlite":
            return self._validate_database_configuration()
        elif data_source_type == "excel":
            return self._validate_excel_configuration()
        else:
            self.wizard.show_error(f"Unknown data source type: {data_source_type}")
            return False
    
    def _validate_folder_configuration(self) -> bool:
        """Validate folder configuration."""
        if not self.generated_folder_var or not self.generated_folder_var.get().strip():
            self.wizard.show_error("Please select a Generated Code folder.")
            return False
        
        import os
        
        generated_path = self.generated_folder_var.get().strip()
        if not os.path.exists(generated_path):
            self.wizard.show_error(f"Generated Code folder does not exist: {generated_path}")
            return False
        
        if not os.path.isdir(generated_path):
            self.wizard.show_error(f"Generated Code path is not a directory: {generated_path}")
            return False
        
        # Expected folder is optional, but validate if provided
        if self.expected_folder_var and self.expected_folder_var.get().strip():
            expected_path = self.expected_folder_var.get().strip()
            if not os.path.exists(expected_path):
                self.wizard.show_error(f"Expected Code folder does not exist: {expected_path}")
                return False
            
            if not os.path.isdir(expected_path):
                self.wizard.show_error(f"Expected Code path is not a directory: {expected_path}")
                return False
        
        return True
    
    def _validate_database_configuration(self) -> bool:
        """Validate database configuration."""
        if not self.db_file_var or not self.db_file_var.get().strip():
            self.wizard.show_error("Please select a database file.")
            return False
        
        if not self.table_var or not self.table_var.get() or self.table_var.get() in ["Select a table...", "No tables found", "Error loading tables"]:
            self.wizard.show_error("Please select a table.")
            return False
        
        # Identifier column is optional (can be auto-detected)
        # No validation needed for identifier column
        
        if not self.generated_column_var or not self.generated_column_var.get() or self.generated_column_var.get() in ["Select column...", "Select table first..."]:
            self.wizard.show_error("Please select a generated code column.")
            return False
        
        return True
    
    def _validate_excel_configuration(self) -> bool:
        """Validate Excel/CSV configuration."""
        if not self.excel_file_var or not self.excel_file_var.get().strip():
            self.wizard.show_error("Please select an Excel or CSV file.")
            return False
        
        # For Excel files, check sheet selection
        import os
        file_ext = os.path.splitext(self.excel_file_var.get())[1].lower()
        if file_ext in ['.xlsx', '.xls']:
            if not self.sheet_var or not self.sheet_var.get() or self.sheet_var.get() in ["Select a sheet...", "Select Excel file first..."]:
                self.wizard.show_error("Please select a sheet.")
                return False
        
        if not self.excel_identifier_column_var or not self.excel_identifier_column_var.get() or self.excel_identifier_column_var.get() in ["Select column...", "Select file first..."]:
            self.wizard.show_error("Please select an identifier column.")
            return False
        
        if not self.excel_generated_column_var or not self.excel_generated_column_var.get() or self.excel_generated_column_var.get() in ["Select column...", "Select file first..."]:
            self.wizard.show_error("Please select a generated code column.")
            return False
        
        return True
    
    def get_data(self) -> Dict[str, Any]:
        """Get configuration data based on selected data source type."""
        try:
            data_source_type = self._get_selected_data_source_type()
            
            if data_source_type == "folders":
                return self._get_folder_data()
            elif data_source_type == "sqlite":
                return self._get_database_data()
            elif data_source_type == "excel":
                return self._get_excel_data()
            else:
                return {}
        except Exception as e:
            self.logger.error(f"Error getting configuration step data: {e}")
            return {}
    
    def _get_folder_data(self) -> Dict[str, Any]:
        """Get folder configuration data."""
        try:
            data = {
                "generated_code_path": self.generated_folder_var.get().strip() if self.generated_folder_var else ""
            }
            
            if self.expected_folder_var and self.expected_folder_var.get().strip():
                data["expected_code_path"] = self.expected_folder_var.get().strip()
            
            if self.input_folder_var and self.input_folder_var.get().strip():
                data["input_code_path"] = self.input_folder_var.get().strip()
            
            return data
        except Exception as e:
            self.logger.error(f"Error getting folder data: {e}")
            return {}
    
    def _get_database_data(self) -> Dict[str, Any]:
        """Get database configuration data."""
        try:
            expected_column = self.expected_column_var.get() if self.expected_column_var else None
            if expected_column in ["(None)", "None (skip)", ""]:
                expected_column = None
            
            input_column = self.input_column_var.get() if self.input_column_var else None
            if input_column in ["(None)", "None (skip)", ""]:
                input_column = None
            
            identifier_column = self.identifier_column_var.get() if self.identifier_column_var else None
            if identifier_column in ["(Auto-detect)", ""]:
                identifier_column = None  # Will be auto-detected by data source
            
            return {
                "database_path": self.db_file_var.get().strip() if self.db_file_var else "",
                "table_name": self.table_var.get() if self.table_var else "",
                "identifier_column": identifier_column,
                "generated_code_column": self.generated_column_var.get() if self.generated_column_var else "",
                "expected_code_column": expected_column,
                "input_code_column": input_column
            }
        except Exception as e:
            self.logger.error(f"Error getting database data: {e}")
            return {}
    
    def _get_excel_data(self) -> Dict[str, Any]:
        """Get Excel/CSV configuration data."""
        try:
            expected_column = self.excel_expected_column_var.get() if self.excel_expected_column_var else None
            if expected_column == "None (skip)":
                expected_column = None
            
            input_column = self.excel_input_column_var.get() if self.excel_input_column_var else None
            if input_column == "None (skip)":
                input_column = None
            
            data = {
                "file_path": self.excel_file_var.get().strip() if self.excel_file_var else "",
                "identifier_column": self.excel_identifier_column_var.get() if self.excel_identifier_column_var else "",
                "generated_code_column": self.excel_generated_column_var.get() if self.excel_generated_column_var else "",
                "expected_code_column": expected_column,
                "input_code_column": input_column
            }
            
            # Add sheet name for Excel files
            import os
            if self.excel_file_var and self.excel_file_var.get():
                file_ext = os.path.splitext(self.excel_file_var.get())[1].lower()
                if file_ext in ['.xlsx', '.xls'] and self.sheet_var:
                    sheet_name = self.sheet_var.get()
                    if sheet_name and sheet_name not in ["Select a sheet...", "Select Excel file first..."]:
                        data["sheet_name"] = sheet_name
            
            return data
        except Exception as e:
            self.logger.error(f"Error getting Excel data: {e}")
            return {}


class SessionResumptionStep(SetupStep):
    """Step 0: Check for existing sessions and offer resumption."""
    
    def __init__(self, wizard: 'SetupWizard'):
        """Initialize the session resumption step."""
        super().__init__(wizard)
        self.session_manager = SessionManager()
        self.available_sessions = []
        self.selected_session_id = None
        self.action_var: Optional[ctk.StringVar] = None
        self.session_listbox: Optional[ctk.CTkScrollableFrame] = None
        self.session_buttons = []
        self.delete_buttons = []
        
    def create_widgets(self, parent: ctk.CTkFrame) -> None:
        """Create widgets for session resumption step."""
        self.frame = parent
        
        # Check for available sessions
        self.available_sessions = self.session_manager.list_available_sessions()
        
        if not self.available_sessions:
            # No existing sessions - show new session message
            self._create_new_session_widgets(parent)
        else:
            # Existing sessions found - show resumption options
            self._create_resumption_widgets(parent)
    
    def _create_new_session_widgets(self, parent: ctk.CTkFrame) -> None:
        """Create widgets when no existing sessions are found."""
        # Title
        title_label = ctk.CTkLabel(
            parent,
            text="Welcome to VAITP-Auditor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(30, 20))
        
        # Description
        desc_label = ctk.CTkLabel(
            parent,
            text="No previous review sessions found.\nLet's set up a new review session.",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        desc_label.pack(pady=(0, 30))
        
        # Icon or illustration (optional)
        info_frame = ctk.CTkFrame(parent)
        info_frame.pack(pady=20, padx=40, fill="x")
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="🚀 Ready to start your first review session!",
            font=ctk.CTkFont(size=16)
        )
        info_label.pack(pady=20)
        
        # Set action to new session
        self.action_var = ctk.StringVar(value="new")
    
    def _create_resumption_widgets(self, parent: ctk.CTkFrame) -> None:
        """Create widgets when existing sessions are found."""
        # Title
        title_label = ctk.CTkLabel(
            parent,
            text="Resume or Start New Session",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Description
        desc_label = ctk.CTkLabel(
            parent,
            text="Found existing review sessions. You can resume a previous session\nor start a new one.",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        desc_label.pack(pady=(0, 20))
        
        # Action selection
        self.action_var = ctk.StringVar(value="resume")
        
        action_frame = ctk.CTkFrame(parent)
        action_frame.pack(pady=10, padx=20, fill="x")
        
        # Resume existing session option
        resume_radio = ctk.CTkRadioButton(
            action_frame,
            text="Resume an existing session",
            variable=self.action_var,
            value="resume",
            command=self._on_action_changed,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        resume_radio.pack(pady=(15, 10), anchor="w")
        
        # Session list frame
        self.session_listbox = ctk.CTkScrollableFrame(action_frame, height=200)
        self.session_listbox.pack(pady=(0, 15), padx=10, fill="x")
        
        self._populate_session_list()
        
        # New session option
        new_radio = ctk.CTkRadioButton(
            action_frame,
            text="Start a new session",
            variable=self.action_var,
            value="new",
            command=self._on_action_changed,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        new_radio.pack(pady=(10, 15), anchor="w")
    
    def _populate_session_list(self) -> None:
        """Populate the session list with available sessions."""
        if not self.session_listbox:
            return
        
        # Clear existing widgets
        for widget in self.session_listbox.winfo_children():
            widget.destroy()
        
        self.session_buttons = []
        self.delete_buttons = []
        
        if not self.available_sessions:
            no_sessions_label = ctk.CTkLabel(
                self.session_listbox,
                text="No sessions available",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_sessions_label.pack(pady=10)
            return
        
        # Create session entries
        for session_id in self.available_sessions:
            session_info = self.session_manager.get_session_info(session_id)
            
            if not session_info:
                continue
            
            # Session frame
            session_frame = ctk.CTkFrame(self.session_listbox)
            session_frame.pack(pady=5, padx=5, fill="x")
            
            # Session selection button (left side)
            session_button = ctk.CTkRadioButton(
                session_frame,
                text="",  # We'll add text separately for better layout
                variable=ctk.StringVar(),  # Individual variable for each session
                value=session_id,
                command=lambda sid=session_id: self._select_session(sid)
            )
            session_button.pack(side="left", padx=(10, 5), pady=10)
            self.session_buttons.append((session_button, session_id))
            
            # Session info (center)
            info_frame = ctk.CTkFrame(session_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)
            
            # Experiment name
            name_label = ctk.CTkLabel(
                info_frame,
                text=session_info['experiment_name'],
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            name_label.pack(anchor="w")
            
            # Progress info
            progress_text = (
                f"Progress: {session_info['completed_reviews']}/{session_info['total_reviews']} "
                f"({session_info['progress_percentage']:.1f}%)"
            )
            progress_label = ctk.CTkLabel(
                info_frame,
                text=progress_text,
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w"
            )
            progress_label.pack(anchor="w")
            
            # Timestamps
            created_text = f"Created: {session_info['created_timestamp'].strftime('%Y-%m-%d %H:%M')}"
            if session_info.get('saved_timestamp'):
                saved_text = f"Last saved: {session_info['saved_timestamp'].strftime('%Y-%m-%d %H:%M')}"
                timestamp_text = f"{created_text} • {saved_text}"
            else:
                timestamp_text = created_text
            
            timestamp_label = ctk.CTkLabel(
                info_frame,
                text=timestamp_text,
                font=ctk.CTkFont(size=10),
                text_color="gray",
                anchor="w"
            )
            timestamp_label.pack(anchor="w")
            
            # Delete button (right side)
            delete_button = ctk.CTkButton(
                session_frame,
                text="🗑️ Delete",
                command=lambda sid=session_id: self._delete_session(sid),
                width=60,
                height=28,
                fg_color="red",
                hover_color="darkred"
            )
            delete_button.pack(side="right", padx=(5, 10), pady=10)
            self.delete_buttons.append((delete_button, session_id))
        
        # Select first session by default
        if self.available_sessions:
            self._select_session(self.available_sessions[0])
    
    def _select_session(self, session_id: str) -> None:
        """Select a session for resumption."""
        self.selected_session_id = session_id
        
        # Update radio button states
        for button, sid in self.session_buttons:
            if sid == session_id:
                button.select()
            else:
                button.deselect()
        
        self.logger.debug(f"Selected session: {session_id}")
    
    def _delete_session(self, session_id: str) -> None:
        """Delete a session after confirmation."""
        session_info = self.session_manager.get_session_info(session_id)
        if not session_info:
            return
        
        # Show confirmation dialog
        confirm_dialog = ctk.CTkToplevel(self.wizard)
        confirm_dialog.title("Delete Session")
        confirm_dialog.geometry("400x200")
        confirm_dialog.resizable(False, False)
        confirm_dialog.transient(self.wizard)
        confirm_dialog.grab_set()
        
        # Center on wizard
        confirm_dialog.update_idletasks()
        x = (self.wizard.winfo_x() + (self.wizard.winfo_width() // 2) - 200)
        y = (self.wizard.winfo_y() + (self.wizard.winfo_height() // 2) - 100)
        confirm_dialog.geometry(f"+{x}+{y}")
        
        # Confirmation message
        message = (
            f"Are you sure you want to delete this session?\n\n"
            f"Experiment: {session_info['experiment_name']}\n"
            f"Progress: {session_info['completed_reviews']}/{session_info['total_reviews']} reviews\n\n"
            f"This action cannot be undone."
        )
        
        label = ctk.CTkLabel(
            confirm_dialog,
            text=message,
            font=ctk.CTkFont(size=12),
            wraplength=350,
            justify="center"
        )
        label.pack(pady=20)
        
        # Buttons
        button_frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
        button_frame.pack(pady=10)
        
        def do_delete():
            try:
                # Delete session file
                from pathlib import Path
                session_file = Path.home() / '.vaitp_auditor' / 'sessions' / f"{session_id}.pkl"
                if session_file.exists():
                    session_file.unlink()
                
                # Update available sessions
                self.available_sessions = self.session_manager.list_available_sessions()
                
                # Refresh the session list
                self._populate_session_list()
                
                # If no sessions left, switch to new session mode
                if not self.available_sessions:
                    self.action_var.set("new")
                    self._on_action_changed()
                
                confirm_dialog.destroy()
                self.logger.info(f"Deleted session: {session_id}")
                
            except Exception as e:
                self.logger.error(f"Error deleting session: {e}")
                # Show error in the confirmation dialog
                label.configure(text=f"Error deleting session:\n{str(e)}")
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            command=confirm_dialog.destroy,
            width=80
        )
        cancel_button.pack(side="left", padx=(0, 10))
        
        delete_button = ctk.CTkButton(
            button_frame,
            text="🗑️ Delete",
            command=do_delete,
            width=80,
            fg_color="red",
            hover_color="darkred"
        )
        delete_button.pack(side="left")
    
    def _on_action_changed(self) -> None:
        """Handle action selection change."""
        action = self.action_var.get()
        
        if action == "new":
            # Hide session list if it exists
            if self.session_listbox:
                self.session_listbox.pack_forget()
            self.selected_session_id = None
        elif action == "resume":
            # Show session list if it exists
            if self.session_listbox:
                self.session_listbox.pack(pady=(0, 15), padx=10, fill="x")
            # Select first session if none selected
            if not self.selected_session_id and self.available_sessions:
                self._select_session(self.available_sessions[0])
        
        # Update cached data and navigation buttons
        self.wizard.update_cached_data({'action': action})
        self.wizard._update_navigation_buttons()
    
    def validate(self) -> bool:
        """Validate the session resumption step."""
        if not self.action_var:
            return False
        
        action = self.action_var.get()
        
        if action == "resume":
            if not self.selected_session_id:
                self.wizard.show_error("Please select a session to resume.")
                return False
            
            # Validate that the selected session still exists
            if self.selected_session_id not in self.available_sessions:
                self.wizard.show_error("Selected session is no longer available.")
                return False
        
        return True
    
    def get_data(self) -> Dict[str, Any]:
        """Get the session resumption data."""
        if not self.action_var:
            return {"action": "new"}
        
        action = self.action_var.get()
        
        if action == "resume" and self.selected_session_id:
            return {
                "action": "resume",
                "session_id": self.selected_session_id
            }
        else:
            return {"action": "new"}


class FinalizationStep(SetupStep):
    """Step 5: Sampling and output format configuration with summary display."""
    
    def __init__(self, wizard: 'SetupWizard'):
        """Initialize the finalization step."""
        super().__init__(wizard)
        self.sampling_var: Optional[ctk.IntVar] = None
        self.sampling_slider: Optional[ctk.CTkSlider] = None
        self.sampling_label: Optional[ctk.CTkLabel] = None
        self.output_format_var: Optional[ctk.StringVar] = None
        self.summary_text: Optional[ctk.CTkTextbox] = None
    
    def create_widgets(self, parent: ctk.CTkFrame) -> None:
        """Create widgets for finalization step."""
        self.frame = parent
        
        # Title
        title_label = ctk.CTkLabel(
            parent,
            text="Step 4: Finalize Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Description
        desc_label = ctk.CTkLabel(
            parent,
            text="Configure sampling settings and output format, then review your configuration.",
            font=ctk.CTkFont(size=12)
        )
        desc_label.pack(pady=(0, 20))
        
        # Sampling configuration frame
        sampling_frame = ctk.CTkFrame(parent)
        sampling_frame.pack(pady=10, padx=40, fill="x")
        
        sampling_title = ctk.CTkLabel(
            sampling_frame,
            text="Sampling Configuration:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        sampling_title.pack(pady=(15, 10))
        
        # Sampling percentage slider
        slider_frame = ctk.CTkFrame(sampling_frame)
        slider_frame.pack(pady=(0, 15), padx=20, fill="x")
        
        slider_label = ctk.CTkLabel(
            slider_frame,
            text="Sampling Percentage:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        slider_label.pack(pady=(10, 5), anchor="w")
        
        # Create slider with IntVar for percentage (1-100)
        self.sampling_var = ctk.IntVar(value=100)
        self.sampling_slider = ctk.CTkSlider(
            slider_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            variable=self.sampling_var,
            command=self._on_sampling_changed
        )
        self.sampling_slider.pack(pady=(0, 5), padx=10, fill="x")
        
        # Sampling percentage display
        self.sampling_label = ctk.CTkLabel(
            slider_frame,
            text="100% (Use all available data)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.sampling_label.pack(pady=(0, 10))
        
        # Output format configuration frame
        format_frame = ctk.CTkFrame(parent)
        format_frame.pack(pady=10, padx=40, fill="x")
        
        format_title = ctk.CTkLabel(
            format_frame,
            text="Output Format:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        format_title.pack(pady=(15, 10))
        
        # Output format selection
        self.output_format_var = ctk.StringVar(value="excel")
        
        format_selection_frame = ctk.CTkFrame(format_frame)
        format_selection_frame.pack(pady=(0, 15), padx=20, fill="x")
        
        excel_radio = ctk.CTkRadioButton(
            format_selection_frame,
            text="Excel (.xlsx) - Recommended for detailed analysis",
            variable=self.output_format_var,
            value="excel",
            font=ctk.CTkFont(size=12),
            command=self._update_summary_display
        )
        excel_radio.pack(pady=(10, 5), anchor="w")
        
        csv_radio = ctk.CTkRadioButton(
            format_selection_frame,
            text="CSV (.csv) - Compatible with most tools",
            variable=self.output_format_var,
            value="csv",
            font=ctk.CTkFont(size=12),
            command=self._update_summary_display
        )
        csv_radio.pack(pady=(0, 10), anchor="w")
        
        # Configuration summary frame
        summary_frame = ctk.CTkFrame(parent)
        summary_frame.pack(pady=10, padx=40, fill="both", expand=True)
        
        summary_title = ctk.CTkLabel(
            summary_frame,
            text="Configuration Summary:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        summary_title.pack(pady=(15, 10))
        
        # Summary text display
        self.summary_text = ctk.CTkTextbox(
            summary_frame,
            height=120,
            font=ctk.CTkFont(size=11, family="monospace"),
            wrap="word"
        )
        self.summary_text.pack(pady=(0, 15), padx=20, fill="both", expand=True)
        
        # Update summary display
        self._update_summary_display()
    
    def _on_sampling_changed(self, value: float) -> None:
        """Handle sampling percentage change - update both label and summary.
        
        Args:
            value: Current slider value
        """
        self._update_sampling_label(value)
        self._update_summary_display()
    
    def _update_sampling_label(self, value: float) -> None:
        """Update the sampling percentage label.
        
        Args:
            value: Current slider value
        """
        if not self.sampling_label:
            return
        
        percentage = int(value)
        
        if percentage == 100:
            text = "100% (Use all available data)"
        elif percentage >= 90:
            text = f"{percentage}% (Nearly all data)"
        elif percentage >= 50:
            text = f"{percentage}% (Majority of data)"
        elif percentage >= 25:
            text = f"{percentage}% (Quarter of data)"
        elif percentage >= 10:
            text = f"{percentage}% (Small sample)"
        else:
            text = f"{percentage}% (Very small sample)"
        
        self.sampling_label.configure(text=text)
    
    def _update_summary_display(self) -> None:
        """Update the configuration summary display."""
        if not self.summary_text:
            return
        
        try:
            # Collect configuration from all previous steps
            summary_lines = []
            summary_lines.append("=== Review Session Configuration ===\n")
            
            # Get data from previous steps with individual error handling
            for i, step in enumerate(self.wizard.steps):
                if i >= self.wizard.current_step:  # Don't include current or future steps
                    continue
                
                try:
                    step_data = step.get_data()
                    
                    if isinstance(step, NamingStep):
                        summary_lines.append(f"Experiment Name: {step_data.get('experiment_name', 'N/A')}")
                        summary_lines.append(f"Session ID: {step_data.get('session_id', 'N/A')}")
                        summary_lines.append("")
                    
                    elif isinstance(step, DataSourceStep):
                        data_source_type = step_data.get('data_source_type', 'N/A')
                        summary_lines.append(f"Data Source Type: {data_source_type.title()}")
                        summary_lines.append("")
                    
                    elif isinstance(step, ConfigurationStep):
                        data_source_type = self._get_data_source_type()
                        
                        if data_source_type == "folders":
                            summary_lines.append("Folder Configuration:")
                            summary_lines.append(f"  Generated Code: {step_data.get('generated_code_path', 'N/A')}")
                            expected_path = step_data.get('expected_code_path')
                            if expected_path:
                                summary_lines.append(f"  Expected Code: {expected_path}")
                            else:
                                summary_lines.append("  Expected Code: Not specified")
                        
                        elif data_source_type == "sqlite":
                            summary_lines.append("Database Configuration:")
                            summary_lines.append(f"  Database: {step_data.get('database_path', 'N/A')}")
                            summary_lines.append(f"  Table: {step_data.get('table_name', 'N/A')}")
                            summary_lines.append(f"  ID Column: {step_data.get('identifier_column', 'N/A')}")
                            summary_lines.append(f"  Generated Column: {step_data.get('generated_code_column', 'N/A')}")
                            expected_col = step_data.get('expected_code_column')
                            if expected_col:
                                summary_lines.append(f"  Expected Column: {expected_col}")
                            else:
                                summary_lines.append("  Expected Column: Not specified")
                        
                        elif data_source_type == "excel":
                            summary_lines.append("Excel/CSV Configuration:")
                            summary_lines.append(f"  File: {step_data.get('file_path', 'N/A')}")
                            sheet_name = step_data.get('sheet_name')
                            if sheet_name:
                                summary_lines.append(f"  Sheet: {sheet_name}")
                            summary_lines.append(f"  ID Column: {step_data.get('identifier_column', 'N/A')}")
                            summary_lines.append(f"  Generated Column: {step_data.get('generated_code_column', 'N/A')}")
                            expected_col = step_data.get('expected_code_column')
                            if expected_col:
                                summary_lines.append(f"  Expected Column: {expected_col}")
                            else:
                                summary_lines.append("  Expected Column: Not specified")
                        
                        summary_lines.append("")
                        
                except Exception as step_error:
                    self.logger.error(f"Error getting data from step {i}: {step_error}")
                    summary_lines.append(f"Step {i+1}: Error retrieving configuration")
                    summary_lines.append("")
            
            # Add current step configuration
            try:
                if self.sampling_var and self.output_format_var:
                    summary_lines.append("Finalization Settings:")
                    summary_lines.append(f"  Sampling: {self.sampling_var.get()}%")
                    summary_lines.append(f"  Output Format: {self.output_format_var.get().upper()}")
                    summary_lines.append("")
            except Exception as final_error:
                self.logger.error(f"Error getting finalization settings: {final_error}")
                summary_lines.append("Finalization Settings: Error retrieving settings")
                summary_lines.append("")
            
            summary_lines.append("Ready to start review session!")
            
            # Update text widget
            if self.summary_text:
                self.summary_text.delete("1.0", "end")
                self.summary_text.insert("1.0", "\n".join(summary_lines))
            
        except Exception as e:
            self.logger.error(f"Error updating summary display: {e}")
            if self.summary_text:
                try:
                    self.summary_text.delete("1.0", "end")
                    self.summary_text.insert("1.0", f"Error generating summary: {str(e)}")
                except Exception as text_error:
                    self.logger.error(f"Error updating summary text widget: {text_error}")
    
    def _get_data_source_type(self) -> str:
        """Get the data source type from previous steps."""
        for step in self.wizard.steps:
            if isinstance(step, DataSourceStep):
                step_data = step.get_data()
                return step_data.get("data_source_type", "folders")
        return "folders"
    
    def on_show(self) -> None:
        """Called when this step is shown - update summary."""
        self._update_summary_display()
    
    def validate(self) -> bool:
        """Validate the finalization configuration."""
        if not self.sampling_var:
            self.wizard.show_error("Sampling configuration is not initialized.")
            return False
        
        sampling_percentage = self.sampling_var.get()
        if sampling_percentage < 1 or sampling_percentage > 100:
            self.wizard.show_error("Sampling percentage must be between 1% and 100%.")
            return False
        
        if not self.output_format_var:
            self.wizard.show_error("Output format is not selected.")
            return False
        
        output_format = self.output_format_var.get()
        if output_format not in ["excel", "csv"]:
            self.wizard.show_error("Invalid output format selected.")
            return False
        
        return True
    
    def get_data(self) -> Dict[str, Any]:
        """Get the finalization configuration data."""
        try:
            if not self.sampling_var or not self.output_format_var:
                return {}
            
            return {
                "sampling_percentage": self.sampling_var.get(),
                "output_format": self.output_format_var.get()
            }
        except Exception as e:
            self.logger.error(f"Error getting finalization step data: {e}")
            return {}


class SetupWizard(ctk.CTkToplevel):
    """
    Multi-step setup wizard for configuring VAITP-Auditor review sessions.
    
    This wizard guides users through the process of setting up a new review session,
    including experiment naming, data source selection, and configuration.
    """
    
    def __init__(self, parent: ctk.CTk, gui_config: Optional[GUIConfig] = None, 
                 accessibility_manager: Optional['AccessibilityManager'] = None):
        """Initialize the Setup Wizard.
        
        Args:
            parent: Parent window
            gui_config: GUI configuration (uses default if None)
            accessibility_manager: Accessibility manager for enhanced features
        """
        super().__init__(parent)
        
        self.parent = parent
        self.gui_config = gui_config or GUIConfig()
        self.accessibility_manager = accessibility_manager
        self.logger = logging.getLogger(__name__)
        
        # Wizard state
        self.current_step = 0
        self.steps: list[SetupStep] = []
        self.session_config: Optional[Dict[str, Any]] = None
        self.completion_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.cancellation_callback: Optional[Callable[[], None]] = None
        
        # Data cache to avoid widget access issues during completion
        self.cached_data: Dict[str, Any] = {}
        
        # Initialize with default values
        self.cached_data.update({
            'experiment_name': '',
            'session_id': '',
            'data_source_type': 'folders',
            'sampling_percentage': 100,
            'output_format': 'excel'
        })
        
        # UI components
        self.main_frame: Optional[ctk.CTkFrame] = None
        self.scrollable_frame: Optional[ctk.CTkScrollableFrame] = None
        self.content_frame: Optional[ctk.CTkFrame] = None
        self.nav_frame: Optional[ctk.CTkFrame] = None
        self.back_button: Optional[ctk.CTkButton] = None
        self.next_button: Optional[ctk.CTkButton] = None
        self.cancel_button: Optional[ctk.CTkButton] = None
        
        self.logger.info("Setting up Setup Wizard window")
        self._setup_window()
        self.logger.info("Creating wizard steps")
        self._create_steps()
        self.logger.info("Creating wizard layout")
        self._create_layout()
        self.logger.info("Showing current step")
        self._show_current_step()
        self.logger.info("Setup Wizard initialization complete")
    
    def update_cached_data(self, data: Dict[str, Any]) -> None:
        """Safely update the cached data.
        
        Args:
            data: Dictionary of data to cache
        """
        try:
            self.cached_data.update(data)
            self.logger.debug(f"Updated cached data: {data}")
        except Exception as e:
            self.logger.error(f"Error updating cached data: {e}")
    
    def _setup_window(self) -> None:
        """Configure the wizard window properties."""
        # Set window properties
        self.title("VAITP-Auditor: Session Setup")
        self.geometry(f"{self.gui_config.wizard_width}x{self.gui_config.wizard_height}")
        self.resizable(True, True)
        self.minsize(650, 550)  # Set minimum size to prevent too small windows
        
        # Set application icon
        from .icon_utils import set_window_icon
        
        success = set_window_icon(self, store_reference=True)
        if success:
            self.logger.debug("Setup wizard icon set successfully")
        else:
            self.logger.debug("Could not set setup wizard icon")
        
        # Make window modal and always on top
        self.transient(self.parent)
        self.lift()  # Bring to front
        
        # Try to set topmost attribute (may not work on all platforms)
        try:
            self.attributes('-topmost', True)  # Keep on top
        except Exception as e:
            self.logger.debug(f"Could not set topmost attribute: {e}")
        
        # Ensure window is visible and focused
        self.deiconify()  # Make sure it's not minimized
        self.grab_set()  # Make window modal
        
        # Center on screen since parent might be hidden
        self.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calculate center position
        x = (screen_width // 2) - (self.gui_config.wizard_width // 2)
        y = (screen_height // 2) - (self.gui_config.wizard_height // 2)
        
        # Ensure window is visible on screen
        x = max(0, min(x, screen_width - self.gui_config.wizard_width))
        y = max(0, min(y, screen_height - self.gui_config.wizard_height))
        
        self.geometry(f"+{x}+{y}")
        
        self.logger.info(f"Setup Wizard positioned at {x},{y} with size {self.gui_config.wizard_width}x{self.gui_config.wizard_height}")
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Focus the window and make sure it's visible
        self.update()  # Process all pending events
        self.focus_set()
        self.focus_force()
        
        # Make a system beep to indicate the window appeared
        try:
            self.bell()
        except Exception as e:
            self.logger.debug(f"Could not make system beep: {e}")
        
        self.logger.info("Setup Wizard window setup complete and focused")
    
    def _create_steps(self) -> None:
        """Create and initialize all wizard steps."""
        # Step 0: Session resumption (check for existing sessions)
        self.steps.append(SessionResumptionStep(self))
        
        # Step 1: Experiment naming
        self.steps.append(NamingStep(self))
        
        # Step 2: Data source selection
        self.steps.append(DataSourceStep(self))
        
        # Step 3: Data source configuration
        self.steps.append(ConfigurationStep(self))
        
        # Step 4: Finalization (sampling and output format)
        self.steps.append(FinalizationStep(self))
    
    def _create_layout(self) -> None:
        """Create the main wizard layout."""
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable content area
        self.scrollable_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))
        
        # Content frame is the scrollable frame itself
        self.content_frame = self.scrollable_frame
        
        # Navigation frame (fixed height)
        self.nav_frame = ctk.CTkFrame(self.main_frame)
        self.nav_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # Navigation buttons
        self._create_navigation_buttons()
    
    def _create_navigation_buttons(self) -> None:
        """Create the navigation buttons (Back, Next, Cancel)."""
        if not self.nav_frame:
            return
        
        # Cancel button (left side)
        self.cancel_button = ctk.CTkButton(
            self.nav_frame,
            text="❌ Cancel",
            command=self._on_cancel,
            width=80
        )
        self.cancel_button.pack(side="left", padx=(10, 0), pady=10)
        
        # Back and Next buttons (right side)
        button_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=(0, 10), pady=10)
        
        self.back_button = ctk.CTkButton(
            button_frame,
            text="⬅️ Back",
            command=self._on_back,
            width=80
        )
        self.back_button.pack(side="left", padx=(0, 10))
        
        self.next_button = ctk.CTkButton(
            button_frame,
            text="➡️ Next",
            command=self._on_next,
            width=80
        )
        self.next_button.pack(side="left")
        
        # Update button states
        self._update_navigation_buttons()
    
    def _show_current_step(self) -> None:
        """Display the current step in the content frame."""
        if not self.content_frame or not self.steps:
            return
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Hide previous step
        if self.current_step > 0 and self.current_step - 1 < len(self.steps):
            self.steps[self.current_step - 1].on_hide()
        
        # Show current step
        if self.current_step < len(self.steps):
            current_step = self.steps[self.current_step]
            current_step.create_widgets(self.content_frame)
            current_step.on_show()
        
        # Update navigation buttons
        self._update_navigation_buttons()
    
    def _update_navigation_buttons(self) -> None:
        """Update the state of navigation buttons based on current step."""
        if not all([self.back_button, self.next_button]):
            return
        
        # Back button: disabled on first step
        if self.current_step == 0:
            self.back_button.configure(state="disabled")
        else:
            self.back_button.configure(state="normal")
        
        # Next button: changes based on current step and action
        is_last_step = self.current_step >= len(self.steps) - 1
        
        if self.current_step == 0:  # Session resumption step
            action = self.cached_data.get('action', 'new')
            if action == 'resume':
                self.next_button.configure(text="▶️ Resume Session")
            else:
                self.next_button.configure(text="➡️ Next")
        elif is_last_step:
            self.next_button.configure(text="🚀 Start Review")
        else:
            self.next_button.configure(text="➡️ Next")
    
    def _on_back(self) -> None:
        """Handle Back button click."""
        if self.current_step > 0:
            # Cache current step data before going back
            try:
                current_step = self.steps[self.current_step]
                step_data = current_step.get_data()
                self.update_cached_data(step_data)
                self.logger.debug(f"Cached data when going back from step {self.current_step + 1}: {step_data}")
            except Exception as e:
                self.logger.debug(f"Error caching data when going back: {e}")
            
            self.current_step -= 1
            self._show_current_step()
    
    def _on_next(self) -> None:
        """Handle Next button click."""
        # Validate current step
        if self.current_step < len(self.steps):
            current_step = self.steps[self.current_step]
            if not current_step.validate():
                return
            
            # Cache the data from this step to avoid widget access issues later
            try:
                step_data = current_step.get_data()
                self.update_cached_data(step_data)
                self.logger.debug(f"Cached data from step {self.current_step + 1}: {step_data}")
            except Exception as e:
                self.logger.error(f"Error caching data from step {self.current_step + 1}: {e}")
                self.show_error(f"Error saving step data: {str(e)}")
                return
        
        # Special handling for session resumption step
        if self.current_step == 0:  # SessionResumptionStep
            action = self.cached_data.get('action', 'new')
            if action == 'resume':
                # User chose to resume - skip to finish with session resumption
                self._on_resume_session()
                return
        
        # Check if this is the last step
        if self.current_step >= len(self.steps) - 1:
            self._on_finish()
        else:
            self.current_step += 1
            self._show_current_step()
    
    def _on_cancel(self) -> None:
        """Handle Cancel button click or window close."""
        self.logger.info("Setup wizard cancelled by user")
        
        # Call cancellation callback if set
        if self.cancellation_callback:
            self.cancellation_callback()
        
        self.destroy()
    
    def _on_resume_session(self) -> None:
        """Handle session resumption."""
        try:
            session_id = self.cached_data.get('session_id')
            if not session_id:
                self.show_error("No session selected for resumption.")
                return
            
            self.logger.info(f"Resuming session: {session_id}")
            
            # Create a session config for resumption
            session_config = {
                'action': 'resume',
                'session_id': session_id
            }
            
            self.session_config = session_config
            
            # Call completion callback if set
            if self.completion_callback:
                self.completion_callback(session_config)
            
            # Close the wizard
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"Error resuming session: {e}")
            self.show_error(f"Error resuming session: {str(e)}")
    
    def _on_finish(self) -> None:
        """Handle wizard completion."""
        try:
            # Use cached data instead of accessing widgets directly
            # This avoids the widget hierarchy issues with scrollable frames
            session_config = self.cached_data.copy()
            
            # Validate that we have the required data
            required_fields = ['experiment_name', 'data_source_type']
            missing_fields = [field for field in required_fields if field not in session_config]
            
            if missing_fields:
                self.logger.error(f"Missing required fields: {missing_fields}")
                self.show_error(f"Missing required configuration: {', '.join(missing_fields)}")
                return
            
            # Add any final validation based on data source type
            data_source_type = session_config.get('data_source_type', '')
            if data_source_type == 'folders' and 'generated_code_path' not in session_config:
                self.show_error("Generated code folder is required for folder data source.")
                return
            elif data_source_type == 'sqlite' and 'database_path' not in session_config:
                self.show_error("Database file is required for SQLite data source.")
                return
            elif data_source_type == 'excel' and 'file_path' not in session_config:
                self.show_error("Excel/CSV file is required for Excel data source.")
                return
            
            # Mark as new session
            session_config['action'] = 'new'
            
            self.session_config = session_config
            
            self.logger.info(f"Setup wizard completed with config: {session_config}")
            
            # Call completion callback if set
            if self.completion_callback:
                self.completion_callback(session_config)
            
            # Close the wizard
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"Error completing setup wizard: {e}")
            self.show_error(f"Error completing setup: {str(e)}")
    
    def show_error(self, message: str) -> None:
        """Show an error message to the user.
        
        Args:
            message: Error message to display
        """
        # Create a simple error dialog
        error_dialog = ctk.CTkToplevel(self)
        error_dialog.title("Error")
        error_dialog.geometry("400x150")
        error_dialog.resizable(False, False)
        error_dialog.transient(self)
        error_dialog.grab_set()
        
        # Center on wizard
        error_dialog.update_idletasks()
        x = (self.winfo_x() + (self.winfo_width() // 2) - 200)
        y = (self.winfo_y() + (self.winfo_height() // 2) - 75)
        error_dialog.geometry(f"+{x}+{y}")
        
        # Error message
        label = ctk.CTkLabel(
            error_dialog,
            text=message,
            font=ctk.CTkFont(size=12),
            wraplength=350
        )
        label.pack(pady=20)
        
        # OK button
        ok_button = ctk.CTkButton(
            error_dialog,
            text="✓ OK",
            command=error_dialog.destroy,
            width=80
        )
        ok_button.pack(pady=(0, 20))
    
    def set_completion_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set the callback function to call when wizard is completed.
        
        Args:
            callback: Function to call with session configuration
        """
        self.completion_callback = callback
    
    def set_cancellation_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback function to call when wizard is cancelled.
        
        Args:
            callback: Function to call when wizard is cancelled
        """
        self.cancellation_callback = callback
    
    def get_session_config(self) -> Optional[Dict[str, Any]]:
        """Get the session configuration from the completed wizard.
        
        Returns:
            Optional[Dict[str, Any]]: Session configuration or None if not completed
        """
        return self.session_config