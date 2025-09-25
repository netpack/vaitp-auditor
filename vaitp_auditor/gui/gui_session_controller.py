"""
GUI Session Controller for VAITP-Auditor GUI.

This module provides the controller that coordinates between GUI components
and the existing SessionManager, following the MVC pattern.
"""

import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from pathlib import Path

from ..core.models import CodePair, ReviewResult, SessionConfig
from ..session_manager import SessionManager
from ..data_sources.factory import DataSourceFactory
from ..reporting.report_manager import ReportManager
from ..core.differ import CodeDiffer
from .models import GUIConfig, ProgressInfo
from .error_handler import GUIErrorHandler


class GUISessionController:
    """
    Controller that coordinates between GUI components and backend SessionManager.
    
    This class follows the MVC pattern where it acts as the Controller,
    managing the flow between the GUI Views and the backend Models.
    Implements complete event handling for verdict submission, undo, and quit requests.
    """
    
    def __init__(self, gui_config: Optional[GUIConfig] = None):
        """
        Initialize the GUI Session Controller.
        
        Args:
            gui_config: GUI configuration (uses default if None)
        """
        self.logger = logging.getLogger(__name__)
        self.gui_config = gui_config or GUIConfig()
        
        # Backend components
        self._session_manager: Optional[SessionManager] = None
        self._data_source_factory = DataSourceFactory()
        self._report_manager: Optional[ReportManager] = None
        self._code_differ = CodeDiffer()
        
        # GUI components (will be set by the application)
        self._main_window = None
        self._setup_wizard = None
        
        # Session state
        self._current_session_config: Optional[Dict[str, Any]] = None
        self._is_session_active = False
        self._session_paused = False
        self._current_code_pair: Optional[CodePair] = None
        self._review_start_time: Optional[datetime] = None
        
        # Callbacks for window transitions
        self._wizard_completion_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._session_completion_callback: Optional[Callable[[], None]] = None
        
        # Error handler for GUI-specific error handling
        self._error_handler = GUIErrorHandler()
        
        self.logger.info("GUISessionController initialized with full MVC implementation")
    
    def _get_root_window(self):
        """Get the root window from the main window for dialog display."""
        if self._main_window and hasattr(self._main_window, 'winfo_toplevel'):
            return self._main_window.winfo_toplevel()
        return None
    
    def _get_verdict_display_text(self, verdict_id: str) -> str:
        """Convert verdict ID to display text for ReviewResult validation.
        
        Args:
            verdict_id: The verdict ID from the GUI button
            
        Returns:
            The display text that matches ReviewResult validation expectations
        """
        # Import here to avoid circular imports
        from .models import get_default_verdict_buttons
        
        # Get the verdict button configurations
        verdict_buttons = get_default_verdict_buttons()
        
        # Find the matching configuration and return display_text
        for config in verdict_buttons:
            if config.verdict_id == verdict_id:
                return config.display_text
        
        # Fallback: return the verdict_id if no match found
        self.logger.warning(f"No display text found for verdict_id: {verdict_id}")
        return verdict_id
    
    def set_main_window(self, main_window) -> None:
        """
        Set the main review window reference.
        
        Args:
            main_window: MainReviewWindow instance
        """
        self._main_window = main_window
        self.logger.debug("Main window reference set")
    
    def set_setup_wizard(self, setup_wizard) -> None:
        """
        Set the setup wizard reference.
        
        Args:
            setup_wizard: SetupWizard instance
        """
        self._setup_wizard = setup_wizard
        self.logger.debug("Setup wizard reference set")
    
    def set_wizard_completion_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set callback for when setup wizard is completed.
        
        Args:
            callback: Function to call with session configuration
        """
        self._wizard_completion_callback = callback
        self.logger.debug("Wizard completion callback set")
    
    def set_session_completion_callback(self, callback: Callable[[], None]) -> None:
        """
        Set callback for when session is completed.
        
        Args:
            callback: Function to call when session ends
        """
        self._session_completion_callback = callback
        self.logger.debug("Session completion callback set")
    
    def start_session_from_config(self, config: Dict[str, Any]) -> bool:
        """
        Start a new session or resume an existing session from setup wizard configuration.
        
        Args:
            config: Session configuration from setup wizard
            
        Returns:
            bool: True if session started successfully, False otherwise
        """
        try:
            action = config.get('action', 'new')
            
            if action == 'resume':
                return self._resume_existing_session(config)
            else:
                return self._start_new_session(config)
            
        except Exception as e:
            self.logger.error(f"Failed to start/resume session: {e}")
            self._handle_session_error(f"Failed to start/resume session: {str(e)}", e)
            return False
    
    def _start_new_session(self, config: Dict[str, Any]) -> bool:
        """
        Start a new session from configuration.
        
        Args:
            config: Session configuration from setup wizard
            
        Returns:
            bool: True if session started successfully, False otherwise
        """
        try:
            self.logger.info(f"Starting new session: {config.get('experiment_name', 'Unknown')}")
            
            # Store configuration
            self._current_session_config = config
            
            # Create SessionConfig object
            session_config = self._create_session_config_from_dict(config)
            
            # Create data source
            data_source = self._create_data_source_from_config(config)
            
            # Initialize report manager
            self._report_manager = ReportManager()
            
            # Create session manager with no UI controller (GUI will handle UI)
            self._session_manager = SessionManager(
                ui_controller=None,
                report_manager=self._report_manager
            )
            
            # Start the session
            session_id = self._session_manager.start_session(session_config, data_source)
            
            self._is_session_active = True
            self._session_paused = False
            self.logger.info(f"New session started successfully with ID: {session_id}")
            
            # Call wizard completion callback
            if self._wizard_completion_callback:
                self._wizard_completion_callback(config)
            
            # Start the review process
            self.process_review_queue_gui()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start new session: {e}")
            raise
    
    def _resume_existing_session(self, config: Dict[str, Any]) -> bool:
        """
        Resume an existing session from configuration.
        
        Args:
            config: Session configuration containing session_id to resume
            
        Returns:
            bool: True if session resumed successfully, False otherwise
        """
        try:
            session_id = config.get('session_id')
            if not session_id:
                raise ValueError("No session ID provided for resumption")
            
            self.logger.info(f"Resuming existing session: {session_id}")
            
            # Store configuration
            self._current_session_config = config
            
            # Initialize report manager
            self._report_manager = ReportManager()
            
            # Create session manager with no UI controller (GUI will handle UI)
            self._session_manager = SessionManager(
                ui_controller=None,
                report_manager=self._report_manager
            )
            
            # Resume the session
            success = self._session_manager.resume_session(session_id)
            if not success:
                raise ValueError(f"Failed to resume session {session_id}")
            
            # Get session info for data source recreation
            session_info = self._session_manager.get_session_info(session_id)
            if not session_info:
                raise ValueError(f"Could not get session info for {session_id}")
            
            # Recreate data source from session config
            data_source_config = session_info['data_source_config']
            data_source = self._recreate_data_source_from_session_config(data_source_config)
            
            # Set the data source in session manager
            self._session_manager._data_source = data_source
            
            # Initialize report manager for resumed session
            self._report_manager.initialize_report(session_id, 'excel')
            
            self._is_session_active = True
            self._session_paused = False
            
            self.logger.info(f"Session resumed successfully: {session_id}")
            
            # Update config with session info for display
            config.update({
                'experiment_name': session_info['experiment_name'],
                'session_id': session_id
            })
            
            # Call wizard completion callback
            if self._wizard_completion_callback:
                self._wizard_completion_callback(config)
            
            # Start the review process
            self.process_review_queue_gui()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to resume session: {e}")
            raise
    
    def _recreate_data_source_from_session_config(self, data_source_config: Dict[str, Any]):
        """
        Recreate data source from saved session configuration.
        
        Args:
            data_source_config: Data source configuration from saved session
            
        Returns:
            DataSource: Recreated and configured data source
        """
        data_source_type = data_source_config.get('data_source_type', 'folders')
        
        # Create data source using factory
        data_source = self._data_source_factory.create_data_source(data_source_type)
        
        # Configure the data source based on type
        if data_source_type == 'folders':
            from pathlib import Path
            data_source.generated_folder = Path(data_source_config.get('generated_code_path', ''))
            expected_path = data_source_config.get('expected_code_path')
            if expected_path:
                data_source.expected_folder = Path(expected_path)
            input_path = data_source_config.get('input_code_path')
            if input_path:
                data_source.input_folder = Path(input_path)
            
            # Discover file pairs and mark as configured
            data_source._discover_file_pairs()
            if data_source._file_pairs:
                data_source._configured = True
                self.logger.info(f"FileSystemSource recreated with {len(data_source._file_pairs)} file pairs")
            else:
                raise ValueError("No code files found in the specified folders")
        
        elif data_source_type == 'sqlite':
            data_source._db_path = data_source_config.get('database_path', '')
            data_source._table_name = data_source_config.get('table_name', '')
            data_source._identifier_column = data_source_config.get('identifier_column', '')
            data_source._generated_code_column = data_source_config.get('generated_code_column', '')
            expected_column = data_source_config.get('expected_code_column')
            if expected_column:
                data_source._expected_code_column = expected_column
            input_column = data_source_config.get('input_code_column')
            if input_column:
                data_source._input_code_column = input_column
            
            # Mark as configured for SQLite
            data_source._configured = True
            self.logger.info(f"SQLiteSource recreated for database: {data_source._db_path}")
        
        elif data_source_type == 'excel':
            data_source._file_path = data_source_config.get('file_path', '')
            sheet_name = data_source_config.get('sheet_name')
            if sheet_name:
                data_source._sheet_name = sheet_name
            data_source._identifier_column = data_source_config.get('identifier_column', '')
            data_source._generated_code_column = data_source_config.get('generated_code_column', '')
            expected_column = data_source_config.get('expected_code_column')
            if expected_column:
                data_source._expected_code_column = expected_column
            input_column = data_source_config.get('input_code_column')
            if input_column:
                data_source._input_code_column = input_column
            
            # Mark as configured for Excel
            data_source._configured = True
            self.logger.info(f"ExcelSource recreated for file: {data_source._file_path}")
        
        return data_source
    
    def _create_session_config_from_dict(self, config: Dict[str, Any]) -> SessionConfig:
        """
        Create SessionConfig from wizard configuration.
        
        Args:
            config: Configuration dictionary from wizard
            
        Returns:
            SessionConfig: Configured session object
        """
        # Extract data source parameters based on type
        data_source_type = config.get('data_source_type', 'folders')
        data_source_params = {}
        
        if data_source_type == 'folders':
            data_source_params = {
                'generated_code_path': config.get('generated_code_path', ''),
                'expected_code_path': config.get('expected_code_path'),
                'input_code_path': config.get('input_code_path')
            }
        elif data_source_type == 'sqlite':
            data_source_params = {
                'database_path': config.get('database_path', ''),
                'table_name': config.get('table_name', ''),
                'identifier_column': config.get('identifier_column', ''),
                'generated_code_column': config.get('generated_code_column', ''),
                'expected_code_column': config.get('expected_code_column')
            }
        elif data_source_type == 'excel':
            data_source_params = {
                'file_path': config.get('file_path', ''),
                'sheet_name': config.get('sheet_name'),
                'identifier_column': config.get('identifier_column', ''),
                'generated_code_column': config.get('generated_code_column', ''),
                'expected_code_column': config.get('expected_code_column'),
                'input_code_column': config.get('input_code_column')
            }
        
        return SessionConfig(
            experiment_name=config.get('experiment_name', 'gui_experiment'),
            data_source_type=data_source_type,
            data_source_params=data_source_params,
            sample_percentage=float(config.get('sampling_percentage', 100)),
            output_format=config.get('output_format', 'excel')
        )
    
    def _create_data_source_from_config(self, config: Dict[str, Any]):
        """
        Create data source from configuration.
        
        Args:
            config: Configuration dictionary from wizard
            
        Returns:
            DataSource: Configured data source
        """
        data_source_type = config.get('data_source_type', 'folders')
        
        # Create data source using factory
        data_source = self._data_source_factory.create_data_source(data_source_type)
        
        # Configure the data source based on type
        if data_source_type == 'folders':
            from pathlib import Path
            data_source.generated_folder = Path(config.get('generated_code_path', ''))
            expected_path = config.get('expected_code_path')
            if expected_path:
                data_source.expected_folder = Path(expected_path)
            input_path = config.get('input_code_path')
            if input_path:
                data_source.input_folder = Path(input_path)
            
            # Discover file pairs and mark as configured
            data_source._discover_file_pairs()
            if data_source._file_pairs:
                data_source._configured = True
                self.logger.info(f"FileSystemSource configured with {len(data_source._file_pairs)} file pairs")
            else:
                raise ValueError("No code files found in the specified folders")
        
        elif data_source_type == 'sqlite':
            data_source._db_path = config.get('database_path', '')
            data_source._table_name = config.get('table_name', '')
            data_source._identifier_column = config.get('identifier_column', '')
            data_source._generated_code_column = config.get('generated_code_column', '')
            expected_column = config.get('expected_code_column')
            if expected_column:
                data_source._expected_code_column = expected_column
            input_column = config.get('input_code_column')
            if input_column:
                data_source._input_code_column = input_column
            
            # Mark as configured for SQLite
            data_source._configured = True
            self.logger.info(f"SQLiteSource configured for database: {data_source._db_path}")
        
        elif data_source_type == 'excel':
            data_source._file_path = config.get('file_path', '')
            sheet_name = config.get('sheet_name')
            if sheet_name:
                data_source._sheet_name = sheet_name
            data_source._identifier_column = config.get('identifier_column', '')
            data_source._generated_code_column = config.get('generated_code_column', '')
            expected_column = config.get('expected_code_column')
            if expected_column:
                data_source._expected_code_column = expected_column
            input_column = config.get('input_code_column')
            if input_column:
                data_source._input_code_column = input_column
            
            # Mark as configured for Excel
            data_source._configured = True
            self.logger.info(f"ExcelSource configured for file: {data_source._file_path}")
        
        return data_source
    
    def process_review_queue_gui(self) -> None:
        """
        Process the review queue for GUI mode.
        
        This method coordinates the review process between the session manager
        and the GUI components, implementing complete MVC event handling.
        """
        if not self._is_session_active or not self._session_manager:
            self.logger.error("No active session to process")
            return
        
        if not self._main_window:
            self.logger.error("No main window available for review")
            return
        
        try:
            self.logger.info("Starting GUI review process")
            
            # Update view state
            self.update_view_state()
            
            # Load the first code pair
            self.load_next_code_pair()
            
        except Exception as e:
            self.logger.error(f"Error starting review process: {e}")
            self._handle_session_error(f"Error starting review: {str(e)}", e)
    
    def load_next_code_pair(self) -> None:
        """
        Load the next code pair for review with complete MVC implementation.
        """
        if not self._session_manager or not self._main_window:
            return
        
        try:
            # Check if there are more items in the queue
            if not self._session_manager._current_session.remaining_queue:
                self.logger.info("Review queue is empty - session complete")
                self._handle_session_completion()
                return
            
            # Get the next code pair (without removing it from queue yet)
            code_pair = self._session_manager._current_session.remaining_queue[0]
            self._current_code_pair = code_pair
            
            # Record review start time for timing metrics
            self._review_start_time = datetime.utcnow()
            
            # Update progress information
            progress_info = self._get_current_progress()
            
            # Load code pair in the main window with syntax highlighting and diff
            self._load_code_pair_with_enhancements(code_pair)
            self._main_window.update_progress(progress_info)
            
            # Update button states based on session state
            self._update_button_states()
            
            self.logger.debug(f"Loaded code pair: {code_pair.identifier}")
            
        except Exception as e:
            self.logger.error(f"Error loading next code pair: {e}")
            self._handle_session_error(f"Error loading code pair: {str(e)}", e)
    
    def submit_verdict(self, verdict_id: str, comment: str = "") -> None:
        """
        Submit a verdict for the current code pair with complete MVC implementation.
        
        Args:
            verdict_id: The verdict identifier (e.g., "SUCCESS", "FAILURE")
            comment: Optional comment from the user
        """
        if not self._session_manager or not self._main_window:
            self.logger.error("Cannot submit verdict - no active session or window")
            if self._main_window:
                self._main_window.show_verdict_feedback(verdict_id, False)
            return
        
        if self._session_paused:
            self.logger.warning("Cannot submit verdict - session is paused")
            if self._main_window:
                self._main_window.show_verdict_feedback(verdict_id, False)
            return
        
        # Set processing state to prevent double-clicks
        if self._main_window:
            self._main_window.set_processing_state(True)
        
        try:
            self.logger.info(f"Verdict submitted: {verdict_id}, Comment: '{comment}'")
            
            # Get the current code pair
            if not self._session_manager._current_session.remaining_queue:
                self.logger.warning("No code pair to submit verdict for")
                if self._main_window:
                    self._main_window.show_verdict_feedback(verdict_id, False)
                    self._main_window.set_processing_state(False)
                return
            
            code_pair = self._session_manager._current_session.remaining_queue.pop(0)
            
            # Calculate review time
            review_time = 0.0
            if self._review_start_time:
                review_time = (datetime.utcnow() - self._review_start_time).total_seconds()
            
            # Generate code diff for the review result
            code_diff = ""
            if code_pair.expected_code and code_pair.generated_code:
                try:
                    diff_lines = self._code_differ.compute_diff(
                        code_pair.expected_code, 
                        code_pair.generated_code
                    )
                    code_diff = "\n".join([line.line_content for line in diff_lines])
                except Exception as diff_error:
                    self.logger.warning(f"Failed to compute diff: {diff_error}")
                    code_diff = "Diff computation failed"
            
            # Convert verdict_id to proper display text for validation
            verdict_display_text = self._get_verdict_display_text(verdict_id)
            
            # Create complete ReviewResult
            review_result = ReviewResult(
                review_id=len(self._session_manager._current_session.completed_reviews) + 1,
                source_identifier=code_pair.identifier,
                experiment_name=self._session_manager._current_session.experiment_name,
                review_timestamp_utc=datetime.utcnow(),
                reviewer_verdict=verdict_display_text,
                reviewer_comment=comment,
                time_to_review_seconds=review_time,
                expected_code=code_pair.expected_code or "",
                generated_code=code_pair.generated_code,
                code_diff=code_diff
            )
            
            # Add to completed reviews
            self._session_manager._current_session.completed_reviews.append(code_pair.identifier)
            
            # Store the reviewed pair for potential undo
            self._session_manager._last_reviewed_pair = code_pair
            
            # Save to report
            if self._report_manager:
                self._report_manager.append_review_result(review_result)
            
            # Save session state to prevent data loss
            self._session_manager.save_session_state()
            
            # Show success feedback
            if self._main_window:
                self._main_window.show_verdict_feedback(verdict_id, True)
            
            # Reset current code pair (comment is cleared in GUI immediately after reading)
            self._current_code_pair = None
            self._review_start_time = None
            
            # Re-enable UI after successful processing
            if self._main_window:
                self._main_window.set_processing_state(False)
            
            # Load next code pair
            self.load_next_code_pair()
            
        except Exception as e:
            self.logger.error(f"Error submitting verdict: {e}")
            
            # Show failure feedback
            if self._main_window:
                self._main_window.show_verdict_feedback(verdict_id, False)
                self._main_window.set_processing_state(False)
            
            self._handle_session_error(f"Error submitting verdict: {str(e)}", e)
    
    def handle_undo_request(self) -> None:
        """
        Handle undo request with complete MVC implementation and proper state validation.
        """
        if not self._session_manager:
            self.logger.error("Cannot undo - no active session")
            return
        
        if self._session_paused:
            self.logger.warning("Cannot undo - session is paused")
            return
        
        # Set processing state to prevent interactions during undo
        if self._main_window:
            self._main_window.set_processing_state(True)
        
        try:
            self.logger.info("Undo requested")
            
            # Check if undo is possible (edge case: first review, empty session)
            if not self._session_manager.can_undo():
                self.logger.info("No reviews to undo - edge case handled")
                if self._main_window:
                    self._error_handler.show_info_dialog(
                        self._get_root_window(),
                        "Undo Not Available",
                        "There are no reviews to undo. This is the first review of the session."
                    )
                    self._main_window.set_processing_state(False)
                return
            
            # Additional validation: check if session has completed reviews
            if (not hasattr(self._session_manager._current_session, 'completed_reviews') or 
                len(self._session_manager._current_session.completed_reviews) == 0):
                self.logger.info("No completed reviews to undo - empty session edge case")
                if self._main_window:
                    self._error_handler.show_info_dialog(
                        self._get_root_window(),
                        "Undo Not Available", 
                        "There are no completed reviews to undo."
                    )
                    self._main_window.set_processing_state(False)
                return
            
            # Get undo info for user confirmation
            undo_info = self._session_manager.get_undo_info()
            if undo_info and self._main_window:
                # Show confirmation dialog with detailed information
                confirm = self._error_handler.show_confirmation_dialog(
                    self._get_root_window(),
                    "Confirm Undo",
                    f"Undo review #{undo_info['review_id']} for '{undo_info['source_identifier']}'?\n\n"
                    f"This will:\n"
                    f"• Remove the last review from the report\n"
                    f"• Return the code pair to the review queue\n"
                    f"• Update your progress counter\n\n"
                    f"This action cannot be undone."
                )
                
                if not confirm:
                    self.logger.info("Undo cancelled by user")
                    if self._main_window:
                        self._main_window.set_processing_state(False)
                    return
            
            # Perform undo with error handling
            success = self._session_manager.undo_last_review()
            
            if success:
                self.logger.info("Undo successful")
                
                # Clear current state
                self._current_code_pair = None
                self._review_start_time = None
                
                # Reload the current code pair (which is now the undone pair)
                self.load_next_code_pair()
                
                # Update button states
                self._update_button_states()
                
                # Show success message
                if self._main_window:
                    self._error_handler.show_info_dialog(
                        self._get_root_window(),
                        "Undo Successful",
                        "The last review has been undone successfully."
                    )
                
            else:
                self.logger.warning("Undo failed")
                if self._main_window:
                    self._error_handler.show_error_dialog(
                        self._get_root_window(),
                        "Undo Failed",
                        "The undo operation failed. This may be due to:\n"
                        "• Report file access issues\n"
                        "• Session state corruption\n"
                        "• File system permissions\n\n"
                        "Please try again or restart the session."
                    )
            
            # Re-enable UI after processing
            if self._main_window:
                self._main_window.set_processing_state(False)
                
        except Exception as e:
            self.logger.error(f"Error handling undo: {e}")
            
            # Ensure UI is re-enabled even on error
            if self._main_window:
                self._main_window.set_processing_state(False)
            
            self._handle_session_error(f"Error during undo: {str(e)}", e)
    
    def handle_quit_request(self) -> None:
        """
        Handle quit request with complete MVC implementation and session save confirmation.
        """
        try:
            self.logger.info("Quit requested")
            
            if not self._main_window:
                # No window to show confirmation, just quit
                self._perform_quit()
                return
            
            # Set processing state to prevent other interactions
            self._main_window.set_processing_state(True)
            
            # Show confirmation dialog with detailed session save information
            progress_info = self._get_current_progress()
            
            if self._is_session_active and progress_info.total > 0:
                # Active session with progress
                completed_reviews = progress_info.current - 1 if progress_info.current > 0 else 0
                remaining_reviews = progress_info.total - completed_reviews
                
                message = (
                    f"Are you sure you want to quit the review session?\n\n"
                    f"Session Details:\n"
                    f"• Experiment: {progress_info.experiment_name}\n"
                    f"• Completed: {completed_reviews}/{progress_info.total} reviews\n"
                    f"• Remaining: {remaining_reviews} reviews\n"
                    f"• Progress: {progress_info.percentage:.1f}%\n\n"
                    f"Session Save Information:\n"
                    f"• Your progress will be automatically saved\n"
                    f"• You can resume this session later\n"
                    f"• All completed reviews are preserved\n"
                    f"• Report file will be updated with current progress\n\n"
                    f"Click 'Yes' to save and quit, or 'No' to continue reviewing."
                )
                
                title = "Save and Quit Session"
            else:
                # No active session or no progress
                message = (
                    f"Are you sure you want to quit?\n\n"
                    f"No active review session detected.\n"
                    f"No session data will be lost."
                )
                title = "Quit Application"
            
            confirm = self._error_handler.show_confirmation_dialog(
                self._get_root_window(),
                title,
                message
            )
            
            if confirm:
                # User confirmed quit - perform save and quit
                self.logger.info("User confirmed quit - performing save and quit")
                
                # Show saving progress if there's an active session
                if self._is_session_active:
                    # Attempt to save session state
                    try:
                        if self._session_manager:
                            self._session_manager.save_session_state()
                        self.logger.info("Session state saved successfully before quit")
                        
                        # Show brief confirmation of save
                        self._error_handler.show_info_dialog(
                            self._get_root_window(),
                            "Session Saved",
                            f"Session '{progress_info.experiment_name}' has been saved successfully.\n"
                            f"You can resume from where you left off next time.",
                            auto_close_ms=2000  # Auto-close after 2 seconds
                        )
                        
                    except Exception as save_error:
                        self.logger.error(f"Failed to save session state: {save_error}")
                        
                        # Ask user if they still want to quit despite save failure
                        still_quit = self._error_handler.show_confirmation_dialog(
                            self._get_root_window(),
                            "Save Failed",
                            f"Failed to save session state:\n{str(save_error)}\n\n"
                            f"Do you still want to quit? Unsaved progress may be lost."
                        )
                        
                        if not still_quit:
                            self.logger.info("User cancelled quit due to save failure")
                            self._main_window.set_processing_state(False)
                            return
                
                # Perform the actual quit
                self._perform_quit()
                
            else:
                self.logger.info("Quit cancelled by user")
                # Re-enable UI since quit was cancelled
                self._main_window.set_processing_state(False)
            
        except Exception as e:
            self.logger.error(f"Error handling quit: {e}")
            
            # Ensure UI is re-enabled
            if self._main_window:
                self._main_window.set_processing_state(False)
            
            # Still try to quit gracefully in case of error
            try:
                emergency_quit = self._error_handler.show_confirmation_dialog(
                    self._get_root_window(),
                    "Error During Quit",
                    f"An error occurred while processing quit request:\n{str(e)}\n\n"
                    f"Force quit anyway? (Progress may not be saved)"
                )
                
                if emergency_quit:
                    self._perform_quit()
                    
            except:
                # Last resort - force quit
                self._perform_quit()
    
    def _get_current_progress(self) -> ProgressInfo:
        """
        Get current progress information for display.
        
        Returns:
            ProgressInfo: Current progress information
        """
        if not self._session_manager or not self._session_manager._current_session:
            return ProgressInfo(
                current=0,
                total=0,
                current_file="No session",
                experiment_name="Unknown"
            )
        
        session = self._session_manager._current_session
        completed = len(session.completed_reviews)
        total = session.get_total_reviews()
        
        # Get current file name
        current_file = "No file"
        if session.remaining_queue:
            current_file = session.remaining_queue[0].identifier
        elif completed > 0:
            current_file = "Session complete"
        
        # Calculate current position - if there are remaining items, show completed + 1
        # If no remaining items, show completed (which equals total)
        current_position = completed + 1 if session.remaining_queue else completed
        
        # Ensure current doesn't exceed total
        current_position = min(current_position, total)
        
        return ProgressInfo(
            current=current_position,
            total=total,
            current_file=current_file,
            experiment_name=session.experiment_name
        )
    
    def _handle_session_completion(self) -> None:
        """
        Handle session completion with complete MVC implementation.
        """
        try:
            self.logger.info("Session completed")
            
            # Update session state
            self._is_session_active = False
            self._current_code_pair = None
            self._review_start_time = None
            
            # Update main window state and get progress info
            progress_info = None
            if self._main_window:
                progress_info = self._get_current_progress()
                self._main_window.set_completion_state(progress_info.experiment_name)
            
            # Finalize session and create final report
            final_report_path = None
            if self._session_manager:
                final_report_path = self._session_manager.finalize_session()
                if final_report_path:
                    self.logger.info(f"Final report created: {final_report_path}")
                else:
                    self.logger.warning("Failed to create final report")
            
            # Update completion dialog to include report path
            if self._main_window and final_report_path:
                # Show updated completion dialog with report path
                self._error_handler.show_info_dialog(
                    self._get_root_window(),
                    "Review Complete",
                    f"Congratulations! You have completed the review session.\n\n"
                    f"Experiment: {progress_info.experiment_name}\n"
                    f"Total reviews: {progress_info.total}\n\n"
                    f"Final report saved to:\n{final_report_path}"
                )
            
            # Call completion callback
            if self._session_completion_callback:
                self._session_completion_callback()
            
        except Exception as e:
            self.logger.error(f"Error handling session completion: {e}")
    
    def _perform_quit(self) -> None:
        """
        Perform the actual quit operation with proper cleanup and exit the application.
        """
        try:
            self.logger.info("Performing quit operation")
            
            # Save session state if active
            if self._is_session_active and self._session_manager:
                self._session_manager.save_session_state()
                self.logger.info("Session state saved before quit")
            
            # Update session state
            self._session_paused = True
            
            # Exit the entire application by closing the root window
            if self._main_window:
                root_window = self._main_window.winfo_toplevel()
                if root_window:
                    # Schedule the window destruction to happen after current event processing
                    root_window.after(100, root_window.destroy)
            
        except Exception as e:
            self.logger.error(f"Error during quit operation: {e}")
            # Still try to exit the application
            try:
                if self._main_window:
                    root_window = self._main_window.winfo_toplevel()
                    if root_window:
                        root_window.after(100, root_window.destroy)
            except:
                pass
    
    def _load_code_pair_with_enhancements(self, code_pair: CodePair) -> None:
        """
        Load code pair with syntax highlighting and diff enhancements.
        
        Args:
            code_pair: Code pair to load
        """
        try:
            # Load basic code pair
            self._main_window.load_code_pair(code_pair)
            
            # Apply syntax highlighting and diff highlighting if code display supports it
            if hasattr(self._main_window, 'code_panels_frame'):
                code_panels = self._main_window.code_panels_frame
                
                # Apply syntax highlighting if available
                if hasattr(code_panels, 'apply_syntax_highlighting'):
                    try:
                        self.logger.debug("Applying syntax highlighting")
                        code_panels.apply_syntax_highlighting(code_pair)
                        self.logger.debug("Syntax highlighting applied successfully")
                    except Exception as highlight_error:
                        self.logger.warning(f"Syntax highlighting failed: {highlight_error}")
                
                # Apply diff highlighting between expected and generated code only
                if hasattr(code_panels, 'apply_diff_highlighting'):
                    try:
                        self.logger.debug("Computing expected-generated diff for highlighting")
                        
                        # Compute expected-generated diff only
                        expected_generated_diff = None
                        if code_pair.expected_code and code_pair.generated_code:
                            expected_generated_diff = self._code_differ.compute_diff(
                                code_pair.expected_code, 
                                code_pair.generated_code
                            )
                        
                        # Apply expected-generated diff highlighting only
                        code_panels.apply_diff_highlighting(expected_generated_diff, self.gui_config)
                        self.logger.debug("Expected-generated diff highlighting applied successfully")
                    except Exception as diff_error:
                        self.logger.warning(f"Diff highlighting failed: {diff_error}")
            
        except Exception as e:
            self.logger.warning(f"Enhanced code loading failed, using basic loading: {e}")
            # Fallback to basic loading
            self._main_window.load_code_pair(code_pair)
    
    def _update_button_states(self) -> None:
        """
        Update button states based on current session state.
        """
        try:
            if not self._main_window:
                return
            
            # Enable/disable undo button based on availability
            can_undo = self._session_manager and self._session_manager.can_undo()
            self._main_window.set_undo_enabled(can_undo and not self._session_paused)
            
            # Enable/disable verdict buttons based on session state
            has_code_pair = self._current_code_pair is not None
            self._main_window.set_verdict_buttons_enabled(has_code_pair and not self._session_paused)
            
        except Exception as e:
            self.logger.warning(f"Failed to update button states: {e}")
    
    def _handle_session_error(self, message: str, exception: Exception) -> None:
        """
        Handle session-related errors with GUI feedback.
        
        Args:
            message: Error message to display
            exception: The exception that occurred
        """
        self.logger.error(f"Session error: {message}")
        
        if self._main_window:
            self._error_handler.show_error_dialog(
                self._get_root_window(),
                "Session Error",
                message,
                str(exception)
            )
        else:
            # Fallback for when no GUI is available
            print(f"Error: {message}")
    
    def update_view_state(self) -> None:
        """
        Update view state to reflect current session state.
        """
        try:
            if not self._main_window:
                return
            
            if self._is_session_active and self._session_manager:
                # Update progress (window title is handled by GUI app)
                progress_info = self._get_current_progress()
                self._main_window.update_progress(progress_info)
                
            else:
                # Reset to default state
                self._main_window.set_placeholder_state()
            
            # Update button states
            self._update_button_states()
            
        except Exception as e:
            self.logger.warning(f"Failed to update view state: {e}")
    
    def pause_session(self) -> bool:
        """
        Pause the current session.
        
        Returns:
            bool: True if session was paused successfully
        """
        if not self._is_session_active:
            return False
        
        try:
            self.logger.info("Pausing session")
            self._session_paused = True
            
            # Save current state
            if self._session_manager:
                self._session_manager.save_session_state()
            
            # Update view state
            self.update_view_state()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausing session: {e}")
            return False
    
    def resume_session(self) -> bool:
        """
        Resume a paused session.
        
        Returns:
            bool: True if session was resumed successfully
        """
        if not self._is_session_active or not self._session_paused:
            return False
        
        try:
            self.logger.info("Resuming session")
            self._session_paused = False
            
            # Update view state
            self.update_view_state()
            
            # Reload current code pair if available
            if self._current_code_pair:
                self._load_code_pair_with_enhancements(self._current_code_pair)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resuming session: {e}")
            return False
    
    def is_session_paused(self) -> bool:
        """
        Check if the current session is paused.
        
        Returns:
            bool: True if session is paused
        """
        return self._session_paused
    
    def get_current_progress(self) -> Dict[str, Any]:
        """
        Get current progress as dictionary for external use.
        
        Returns:
            Dict[str, Any]: Progress information dictionary
        """
        progress_info = self._get_current_progress()
        return {
            'current': progress_info.current,
            'total': progress_info.total,
            'percentage': progress_info.percentage,
            'current_file': progress_info.current_file,
            'experiment_name': progress_info.experiment_name,
            'is_complete': progress_info.is_complete()
        }
    
    def is_session_active(self) -> bool:
        """
        Check if a session is currently active.
        
        Returns:
            bool: True if session is active, False otherwise
        """
        return self._is_session_active
    
    def get_session_config(self) -> Optional[Dict[str, Any]]:
        """
        Get the current session configuration.
        
        Returns:
            Optional[Dict[str, Any]]: Session configuration or None if no active session
        """
        return self._current_session_config
    
    def cleanup(self) -> None:
        """
        Clean up controller resources with complete session lifecycle management.
        """
        try:
            self.logger.info("Cleaning up GUI session controller")
            
            # Save session state if active
            if self._session_manager and self._is_session_active:
                try:
                    self._session_manager.save_session_state()
                    self.logger.info("Session state saved during cleanup")
                except Exception as save_error:
                    self.logger.warning(f"Failed to save session state during cleanup: {save_error}")
            
            # Clear session manager reference (SessionManager handles cleanup internally)
            self._session_manager = None
            self._report_manager = None
            self._main_window = None
            self._setup_wizard = None
            self._current_session_config = None
            self._current_code_pair = None
            self._review_start_time = None
            self._is_session_active = False
            self._session_paused = False
            
            # Clear callbacks
            self._wizard_completion_callback = None
            self._session_completion_callback = None
            
            self.logger.info("GUI session controller cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during controller cleanup: {e}")
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get current session statistics.
        
        Returns:
            Dict containing session statistics
        """
        if not self._session_manager or not self._is_session_active:
            return {
                'active': False,
                'paused': False,
                'completed_reviews': 0,
                'remaining_reviews': 0,
                'total_reviews': 0,
                'progress_percentage': 0.0,
                'experiment_name': 'No active session'
            }
        
        try:
            session = self._session_manager._current_session
            completed = len(session.completed_reviews)
            total = session.get_total_reviews()
            remaining = len(session.remaining_queue)
            
            return {
                'active': self._is_session_active,
                'paused': self._session_paused,
                'completed_reviews': completed,
                'remaining_reviews': remaining,
                'total_reviews': total,
                'progress_percentage': (completed / total * 100) if total > 0 else 0.0,
                'experiment_name': session.experiment_name,
                'session_id': session.session_id,
                'created_timestamp': session.created_timestamp.isoformat() if session.created_timestamp else None,
                'current_file': self._current_code_pair.identifier if self._current_code_pair else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting session statistics: {e}")
            return {
                'active': False,
                'error': str(e)
            }
    
    def resume_session_from_state(self, session_id: str, data_source) -> bool:
        """
        Resume a session from saved state with complete lifecycle management.
        
        Args:
            session_id: Session ID to resume
            data_source: Configured data source for the session
            
        Returns:
            bool: True if session was successfully resumed
        """
        try:
            self.logger.info(f"Attempting to resume session: {session_id}")
            
            # Initialize report manager
            self._report_manager = ReportManager()
            
            # Create session manager
            self._session_manager = SessionManager(
                ui_controller=None,
                report_manager=self._report_manager
            )
            
            # Attempt to resume the session
            success = self._session_manager.resume_session_with_fallback(session_id, data_source)
            
            if success:
                self._is_session_active = True
                self._session_paused = False
                
                # Update view state
                self.update_view_state()
                
                # Load current code pair if available
                if (self._session_manager._current_session and 
                    self._session_manager._current_session.remaining_queue):
                    self.load_next_code_pair()
                
                self.logger.info(f"Session {session_id} resumed successfully")
                return True
            else:
                self.logger.warning(f"Failed to resume session {session_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error resuming session {session_id}: {e}")
            self._handle_session_error(f"Failed to resume session: {str(e)}", e)
            return False
    
    def save_session_state(self) -> bool:
        """
        Save current session state with error handling.
        
        Returns:
            bool: True if state was saved successfully
        """
        if not self._session_manager or not self._is_session_active:
            return False
        
        try:
            self._session_manager.save_session_state()
            self.logger.debug("Session state saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save session state: {e}")
            return False
    
    def get_session_state_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current session state.
        
        Returns:
            Dict with session state information or None if no active session
        """
        if not self._session_manager or not self._is_session_active:
            return None
        
        try:
            session = self._session_manager._current_session
            
            return {
                'session_id': session.session_id,
                'experiment_name': session.experiment_name,
                'created_timestamp': session.created_timestamp.isoformat() if session.created_timestamp else None,
                'data_source_config': session.data_source_config,
                'completed_reviews': len(session.completed_reviews),
                'remaining_reviews': len(session.remaining_queue),
                'total_reviews': session.get_total_reviews(),
                'is_paused': self._session_paused,
                'current_code_pair': self._current_code_pair.identifier if self._current_code_pair else None,
                'can_undo': self._session_manager.can_undo() if self._session_manager else False
            }
            
        except Exception as e:
            self.logger.error(f"Error getting session state info: {e}")
            return None
    
    def force_session_completion(self) -> bool:
        """
        Force completion of the current session (for emergency situations).
        
        Returns:
            bool: True if session was completed successfully
        """
        if not self._is_session_active:
            return False
        
        try:
            self.logger.warning("Forcing session completion")
            
            # Save current state
            self.save_session_state()
            
            # Mark session as complete
            self._is_session_active = False
            self._session_paused = False
            
            # Update view
            if self._main_window:
                progress_info = self._get_current_progress()
                self._main_window.set_completion_state(progress_info.experiment_name)
            
            # Call completion callback
            if self._session_completion_callback:
                self._session_completion_callback()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error forcing session completion: {e}")
            return False
    
    def synchronize_session_state(self) -> bool:
        """
        Synchronize session state between GUI and backend.
        
        Returns:
            bool: True if synchronization was successful
        """
        if not self._session_manager or not self._is_session_active:
            return False
        
        try:
            # Save current session state
            if not self.save_session_state():
                return False
            
            # Update view state to match backend
            self.update_view_state()
            
            # Update button states
            self._update_button_states()
            
            # Reload current code pair if needed
            if (self._current_code_pair and 
                self._session_manager._current_session and
                self._session_manager._current_session.remaining_queue):
                
                current_in_queue = any(
                    pair.identifier == self._current_code_pair.identifier 
                    for pair in self._session_manager._current_session.remaining_queue
                )
                
                if not current_in_queue:
                    # Current code pair is no longer in queue, load next
                    self.load_next_code_pair()
            
            self.logger.debug("Session state synchronized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error synchronizing session state: {e}")
            return False
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage information.
        
        Returns:
            Dict with resource usage information
        """
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                'memory_rss_mb': memory_info.rss / 1024 / 1024,
                'memory_vms_mb': memory_info.vms / 1024 / 1024,
                'cpu_percent': process.cpu_percent(),
                'num_threads': process.num_threads(),
                'open_files': len(process.open_files()) if hasattr(process, 'open_files') else 0
            }
            
        except ImportError:
            # psutil not available, return basic info
            return {
                'memory_rss_mb': 0,
                'memory_vms_mb': 0,
                'cpu_percent': 0,
                'num_threads': 1,
                'open_files': 0,
                'note': 'psutil not available for detailed resource monitoring'
            }
        except Exception as e:
            self.logger.warning(f"Error getting resource usage: {e}")
            return {
                'error': str(e)
            }