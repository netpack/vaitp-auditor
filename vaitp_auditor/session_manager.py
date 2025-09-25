"""
Session manager for orchestrating the review workflow.
"""

import gc
import json
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from uuid import uuid4

from .core.models import CodePair, ReviewResult, SessionState, SessionConfig
from .data_sources.base import DataSource
from .ui.review_controller import ReviewUIController
from .reporting.report_manager import ReportManager
from .utils.logging_config import get_logger, log_exception
from .utils.error_handling import (
    SessionError, handle_errors, safe_execute, retry_on_error
)
from .utils.resource_manager import get_resource_manager
from .utils.performance import (
    get_performance_monitor, get_content_cache, get_chunked_processor,
    performance_monitor
)


class SessionManager:
    """
    Orchestrates the overall review workflow and manages session lifecycle.
    
    The SessionManager coordinates between data sources, UI components, and
    reporting to provide a complete review experience.
    """

    def __init__(self, ui_controller: Optional[ReviewUIController] = None, 
                 report_manager: Optional[ReportManager] = None):
        """
        Initialize the session manager.
        
        Args:
            ui_controller: UI controller for displaying code pairs (optional for testing).
            report_manager: Report manager for output generation (optional for testing).
        """
        self.logger = get_logger('session_manager')
        self.resource_manager = get_resource_manager()
        self.performance_monitor = get_performance_monitor()
        self.content_cache = get_content_cache()
        self.chunked_processor = get_chunked_processor()
        
        self._current_session: Optional[SessionState] = None
        self._data_source: Optional[DataSource] = None
        self._ui_controller = ui_controller or ReviewUIController(undo_callback=self.undo_last_review)
        self._report_manager = report_manager or ReportManager()
        self._session_dir = Path.home() / '.vaitp_auditor' / 'sessions'
        
        # Create session directory with error handling
        try:
            self._session_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Session directory ready: {self._session_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create session directory: {e}")
            raise SessionError(f"Cannot create session directory: {e}")
        
        self._next_review_id = 1
        self._last_reviewed_pair: Optional[CodePair] = None  # Store last reviewed pair for undo
        
        # Set up undo callback if UI controller was provided without it
        if hasattr(self._ui_controller, 'undo_callback') and self._ui_controller.undo_callback is None:
            self._ui_controller.undo_callback = self.undo_last_review
        
        # Register cleanup callback
        self.resource_manager.register_cleanup_callback(self._cleanup_session_resources)
        
        self.logger.info("SessionManager initialized successfully")

    @handle_errors(error_types=(ValueError, SessionError), context={'operation': 'start_session'})
    def start_session(self, config: SessionConfig, data_source: DataSource) -> str:
        """
        Start a new review session with the given configuration.
        
        Args:
            config: Session configuration including data source and experiment details.
            data_source: Configured data source for loading code pairs.
            
        Returns:
            str: The session ID of the created session.
            
        Raises:
            ValueError: If configuration is invalid or data source fails to load.
        """
        self.logger.info(f"Starting new session for experiment: {config.experiment_name}")
        
        # Generate unique session ID
        session_id = f"{config.experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid4())[:8]}"
        self.logger.debug(f"Generated session ID: {session_id}")
        
        # Load data from source with comprehensive error handling
        try:
            self.logger.info("Loading data from configured source")
            code_pairs = data_source.load_data(config.sample_percentage)
            
            if not code_pairs:
                error_msg = "No code pairs loaded from data source"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            self.logger.info(f"Successfully loaded {len(code_pairs)} code pairs")
            
        except Exception as e:
            error_msg = f"Failed to load data from source: {e}"
            self.logger.error(error_msg)
            log_exception(self.logger, e, {'operation': 'load_data', 'config': str(config)})
            raise ValueError(error_msg)
        
        # Create session state with data source type included in config
        data_source_config = config.data_source_params.copy()
        data_source_config['data_source_type'] = config.data_source_type
        
        try:
            self._current_session = SessionState(
                session_id=session_id,
                experiment_name=config.experiment_name,
                data_source_config=data_source_config,
                completed_reviews=[],
                remaining_queue=code_pairs,
                created_timestamp=datetime.utcnow()
            )
            
            self._data_source = data_source
            
            # Initialize report manager
            self.logger.debug("Initializing report manager")
            self._report_manager.initialize_report(session_id, config.output_format)
            
            # Save initial session state
            self.logger.debug("Saving initial session state")
            self.save_session_state()
            
            self.logger.info(f"Session {session_id} started successfully")
            return session_id
            
        except Exception as e:
            error_msg = f"Failed to initialize session: {e}"
            self.logger.error(error_msg)
            log_exception(self.logger, e, {'session_id': session_id, 'config': str(config)})
            raise SessionError(error_msg)

    def resume_session(self, session_id: str) -> bool:
        """
        Resume an existing session from saved state.
        
        Args:
            session_id: Unique identifier of the session to resume.
            
        Returns:
            bool: True if session was successfully resumed, False otherwise.
            
        Raises:
            FileNotFoundError: If session file doesn't exist.
            ValueError: If session file is corrupted or invalid.
        """
        session_file = self._session_dir / f"{session_id}.pkl"
        
        if not session_file.exists():
            raise FileNotFoundError(f"Session file not found: {session_file}")
        
        try:
            with open(session_file, 'rb') as f:
                session_data = pickle.load(f)
            
            # Validate loaded session data
            if not isinstance(session_data, dict):
                raise ValueError("Invalid session file format")
            
            required_keys = {'session_state', 'data_source_config', 'next_review_id'}
            if not all(key in session_data for key in required_keys):
                raise ValueError("Missing required session data")
            
            # Restore session state
            self._current_session = session_data['session_state']
            self._next_review_id = session_data['next_review_id']
            
            # Validate session state integrity
            if not self._current_session.validate_integrity():
                raise ValueError("Session state failed integrity validation")
            
            # Note: Data source will need to be reconfigured by caller
            # as it may contain non-serializable objects
            
            return True
            
        except (pickle.PickleError, EOFError, KeyError) as e:
            raise ValueError(f"Corrupted session file: {e}")

    def prompt_for_session_resumption(self) -> Optional[str]:
        """
        Prompt user for session resumption with validation.
        
        Returns:
            Optional[str]: Session ID to resume, or None if user chooses not to resume.
        """
        available_sessions = self.list_available_sessions()
        
        if not available_sessions:
            return None
        
        print("\nFound existing review sessions:")
        print("=" * 50)
        
        # Display available sessions with details
        valid_sessions = []
        for i, session_id in enumerate(available_sessions, 1):
            session_info = self.get_session_info(session_id)
            if session_info:
                print(f"{i}. {session_info['experiment_name']}")
                print(f"   Session ID: {session_id}")
                print(f"   Progress: {session_info['completed_reviews']}/{session_info['total_reviews']} "
                      f"({session_info['progress_percentage']:.1f}%)")
                print(f"   Created: {session_info['created_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                if session_info.get('saved_timestamp'):
                    print(f"   Last saved: {session_info['saved_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                print()
                valid_sessions.append(session_id)
            else:
                print(f"{i}. [CORRUPTED] {session_id}")
                print("   This session file appears to be corrupted and cannot be resumed.")
                print()
        
        if not valid_sessions:
            print("No valid sessions found to resume.")
            return None
        
        print(f"{len(valid_sessions) + 1}. Start a new session")
        print()
        
        # Get user choice with validation
        while True:
            try:
                choice = input(f"Select an option (1-{len(valid_sessions) + 1}): ").strip()
                
                if not choice:
                    continue
                
                choice_num = int(choice)
                
                if choice_num == len(valid_sessions) + 1:
                    # User chose to start new session
                    return None
                elif 1 <= choice_num <= len(valid_sessions):
                    # User chose to resume a session
                    selected_session = valid_sessions[choice_num - 1]
                    
                    # Confirm resumption
                    session_info = self.get_session_info(selected_session)
                    print(f"\nYou selected: {session_info['experiment_name']}")
                    print(f"Progress: {session_info['completed_reviews']}/{session_info['total_reviews']} reviews completed")
                    
                    confirm = input("Resume this session? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        return selected_session
                    elif confirm in ['n', 'no']:
                        print("Session resumption cancelled.")
                        return None
                    else:
                        print("Please enter 'y' for yes or 'n' for no.")
                        continue
                else:
                    print(f"Please enter a number between 1 and {len(valid_sessions) + 1}")
                    
            except ValueError:
                print("Please enter a valid number.")
            except KeyboardInterrupt:
                print("\nSession selection cancelled.")
                return None

    def resume_session_with_fallback(self, session_id: str, data_source: DataSource) -> bool:
        """
        Resume a session with graceful fallback for corrupted files.
        
        Args:
            session_id: Session ID to resume.
            data_source: Configured data source for the session.
            
        Returns:
            bool: True if session was successfully resumed, False if fallback was used.
        """
        try:
            # Attempt to resume the session
            success = self.resume_session(session_id)
            if success:
                # Restore data source
                self._data_source = data_source
                
                # Initialize report manager for resumed session
                self._report_manager.initialize_report(session_id, 'excel')
                
                print(f"Successfully resumed session: {session_id}")
                progress = self.get_session_progress()
                if progress:
                    print(f"Progress: {progress['completed_reviews']}/{progress['total_reviews']} "
                          f"reviews completed ({progress['progress_percentage']:.1f}%)")
                return True
                
        except FileNotFoundError:
            print(f"Error: Session file not found for {session_id}")
            return self._handle_session_fallback(session_id, "Session file not found")
            
        except ValueError as e:
            print(f"Error: Session file is corrupted - {e}")
            return self._handle_session_fallback(session_id, f"Corrupted session file: {e}")
            
        except Exception as e:
            print(f"Error: Unexpected error resuming session - {e}")
            return self._handle_session_fallback(session_id, f"Unexpected error: {e}")
        
        return False

    def _handle_session_fallback(self, session_id: str, error_message: str) -> bool:
        """
        Handle session resumption fallback options.
        
        Args:
            session_id: The session ID that failed to resume.
            error_message: Description of the error that occurred.
            
        Returns:
            bool: False (indicates fallback was used, not true resumption).
        """
        print(f"\nSession resumption failed: {error_message}")
        print("\nFallback options:")
        print("1. Start a fresh session (recommended)")
        print("2. Try to recover partial data (experimental)")
        print("3. Delete corrupted session file")
        print("4. Cancel and exit")
        
        while True:
            try:
                choice = input("Select an option (1-4): ").strip()
                
                if choice == '1':
                    print("Starting a fresh session. Previous session data cannot be recovered.")
                    return False
                    
                elif choice == '2':
                    return self._attempt_partial_recovery(session_id)
                    
                elif choice == '3':
                    return self._delete_corrupted_session(session_id)
                    
                elif choice == '4':
                    print("Operation cancelled.")
                    raise KeyboardInterrupt("User cancelled session resumption")
                    
                else:
                    print("Please enter a number between 1 and 4.")
                    
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                raise

    def _attempt_partial_recovery(self, session_id: str) -> bool:
        """
        Attempt to recover partial data from a corrupted session.
        
        Args:
            session_id: The session ID to attempt recovery for.
            
        Returns:
            bool: False (recovery creates a new session, not true resumption).
        """
        session_file = self._session_dir / f"{session_id}.pkl"
        
        try:
            print("Attempting partial data recovery...")
            
            # Try to read raw file data
            with open(session_file, 'rb') as f:
                raw_data = f.read()
            
            # Try different recovery strategies
            recovered_data = None
            
            # Strategy 1: Try to load with different pickle protocols
            for protocol in [pickle.HIGHEST_PROTOCOL, 4, 3, 2]:
                try:
                    recovered_data = pickle.loads(raw_data)
                    break
                except Exception:
                    continue
            
            if recovered_data and isinstance(recovered_data, dict):
                # Try to extract what we can
                experiment_name = recovered_data.get('session_state', {}).get('experiment_name', 'recovered_session')
                completed_reviews = recovered_data.get('session_state', {}).get('completed_reviews', [])
                
                print(f"Partial recovery successful!")
                print(f"Experiment name: {experiment_name}")
                print(f"Completed reviews found: {len(completed_reviews)}")
                print("Note: You will need to start a new session, but completed review data may be available in reports.")
                
                return False
            else:
                print("Partial recovery failed. No usable data could be extracted.")
                return False
                
        except Exception as e:
            print(f"Partial recovery failed: {e}")
            return False

    def _delete_corrupted_session(self, session_id: str) -> bool:
        """
        Delete a corrupted session file after user confirmation.
        
        Args:
            session_id: The session ID to delete.
            
        Returns:
            bool: False (session was deleted, not resumed).
        """
        session_file = self._session_dir / f"{session_id}.pkl"
        
        print(f"This will permanently delete the corrupted session file: {session_file}")
        confirm = input("Are you sure? This cannot be undone. (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            try:
                session_file.unlink()
                print("Corrupted session file deleted successfully.")
                return False
            except Exception as e:
                print(f"Error deleting session file: {e}")
                return False
        else:
            print("Session file deletion cancelled.")
            return False

    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """
        Clean up old session files to prevent accumulation.
        
        Args:
            days_old: Delete sessions older than this many days.
            
        Returns:
            int: Number of sessions cleaned up.
        """
        if days_old <= 0:
            raise ValueError("days_old must be positive")
        
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        cleaned_count = 0
        
        try:
            for session_file in self._session_dir.glob("*.pkl"):
                try:
                    # Check file modification time
                    if session_file.stat().st_mtime < cutoff_time:
                        session_file.unlink()
                        cleaned_count += 1
                except Exception:
                    # Skip files we can't process
                    continue
                    
        except Exception:
            # If we can't access the directory, just return 0
            pass
        
        return cleaned_count

    def _cleanup_session_resources(self) -> None:
        """Clean up session-specific resources."""
        try:
            if self._current_session:
                self.logger.info(f"Cleaning up resources for session: {self._current_session.session_id}")
                
                # Save final state if needed - but only if session directory exists
                try:
                    if self._session_dir.exists():
                        self.save_session_state()
                except Exception as save_error:
                    self.logger.warning(f"Could not save final session state during cleanup: {save_error}")
                
                # Clear references
                self._current_session = None
                self._data_source = None
                self._last_reviewed_pair = None
                
                self.logger.debug("Session resources cleaned up successfully")
            else:
                self.logger.debug("No active session to clean up")
        except Exception as e:
            self.logger.error(f"Error during session resource cleanup: {e}")

    @handle_errors(error_types=Exception, context={'operation': 'process_review_queue'})
    def process_review_queue_with_monitoring(self) -> None:
        """
        Process the review queue with comprehensive monitoring and error handling.
        """
        if not self._current_session:
            raise SessionError("No active session to process")
        
        if not self._ui_controller:
            raise SessionError("No UI controller available for review")
        
        self.logger.info(f"Starting review process for {len(self._current_session.remaining_queue)} items")
        
        # Monitor memory usage
        initial_memory = self.resource_manager.get_memory_usage()
        self.logger.debug(f"Initial memory usage: {initial_memory}")
        
        processed_count = 0
        error_count = 0
        
        try:
            while self._current_session.remaining_queue:
                # Check memory usage periodically
                if processed_count % 10 == 0:
                    if not self.resource_manager.check_memory_limit(1000.0):  # 1GB limit
                        self.logger.warning("Memory limit approached, forcing garbage collection")
                        gc_stats = self.resource_manager.force_garbage_collection()
                        self.logger.info(f"Garbage collection stats: {gc_stats}")
                
                # Get next code pair
                code_pair = self._current_session.remaining_queue.pop(0)
                
                try:
                    # Get review from UI
                    review_result = self.get_review_for_pair(code_pair)
                    
                    # Handle quit command
                    if review_result.reviewer_verdict == 'Quit':
                        self.logger.info("User requested quit - stopping review process")
                        break
                    
                    # Handle undo command
                    if review_result.reviewer_verdict == 'Undo':
                        self.logger.debug("Undo command processed")
                        # Put the current item back in the queue and continue
                        self._current_session.remaining_queue.insert(0, code_pair)
                        continue
                    
                    # Process the review result
                    self._report_manager.append_review_result(review_result)
                    self._current_session.completed_reviews.append(code_pair.identifier)
                    
                    # Store the reviewed pair for potential undo
                    self._last_reviewed_pair = code_pair
                    
                    # Save state after each review to prevent data loss
                    self.save_session_state()
                    
                    processed_count += 1
                    
                    if processed_count % 5 == 0:
                        self.logger.debug(f"Processed {processed_count} reviews")
                    
                except KeyboardInterrupt:
                    # Put the item back in the queue since it wasn't completed
                    self._current_session.remaining_queue.insert(0, code_pair)
                    self.logger.info("Session interrupted by user. Progress has been saved.")
                    break
                except Exception as e:
                    error_count += 1
                    error_context = {
                        'code_pair_id': code_pair.identifier,
                        'processed_count': processed_count,
                        'error_count': error_count
                    }
                    self.logger.error(f"Error processing review for {code_pair.identifier}: {e}")
                    log_exception(self.logger, e, error_context)
                    
                    # Continue with next pair rather than failing entire session
                    continue
            
            # Final statistics
            final_memory = self.resource_manager.get_memory_usage()
            self.logger.info(f"Review process completed - Processed: {processed_count}, Errors: {error_count}")
            self.logger.debug(f"Final memory usage: {final_memory}")
            
        except Exception as e:
            self.logger.error(f"Critical error in review process: {e}")
            log_exception(self.logger, e, {'processed_count': processed_count, 'error_count': error_count})
            raise

    def process_review_queue(self) -> None:
        """
        Process the queue of code pairs for review.
        
        This is the main review loop that coordinates UI display and result processing.
        For enhanced monitoring and error handling, use process_review_queue_with_monitoring().
        
        Raises:
            RuntimeError: If no active session exists.
        """
        # Delegate to the monitored version for better error handling
        self.process_review_queue_with_monitoring()

    def get_review_for_pair(self, code_pair: CodePair) -> ReviewResult:
        """
        Get a review result for a specific code pair.
        
        Args:
            code_pair: The code pair to review.
            
        Returns:
            ReviewResult: The completed review result.
            
        Raises:
            RuntimeError: If no active session exists.
        """
        if not self._current_session:
            raise RuntimeError("No active session")
        
        # Prepare progress information for UI
        progress_info = {
            'current': len(self._current_session.completed_reviews) + 1,
            'total': self._current_session.get_total_reviews(),
            'percentage': ((len(self._current_session.completed_reviews)) / 
                          self._current_session.get_total_reviews() * 100) if self._current_session.get_total_reviews() > 0 else 0
        }
        
        # Display code pair and get user input with proper parameters
        review_result = self._ui_controller.display_code_pair(
            code_pair, 
            progress_info, 
            self._current_session.experiment_name
        )
        
        return review_result

    def undo_last_review(self) -> bool:
        """
        Undo the last review and return the code pair to the queue.
        
        Returns:
            bool: True if undo was successful, False if no review to undo.
            
        Raises:
            RuntimeError: If no active session exists.
        """
        if not self._current_session:
            raise RuntimeError("No active session")
        
        # Check if there are any completed reviews to undo
        if not self._current_session.completed_reviews or not self._last_reviewed_pair:
            return False
        
        # Get the last review ID from report manager
        last_review_id = self._report_manager.get_last_review_id()
        if last_review_id is None:
            return False
        
        # Remove the last review from the report
        if not self._report_manager.remove_last_review():
            return False
        
        # Remove the last completed review from the session
        last_identifier = self._current_session.completed_reviews.pop()
        
        # Verify the identifier matches the stored pair
        if self._last_reviewed_pair.identifier != last_identifier:
            # Mismatch - try to recover by putting back the review
            self._current_session.completed_reviews.append(last_identifier)
            return False
        
        # Add the code pair back to the front of the queue
        self._current_session.remaining_queue.insert(0, self._last_reviewed_pair)
        
        # Clear the last reviewed pair since it's back in the queue
        self._last_reviewed_pair = None
        
        # Save the updated session state
        self.save_session_state()
        
        return True

    def can_undo(self) -> bool:
        """
        Check if undo operation is possible.
        
        Returns:
            bool: True if there are reviews that can be undone.
        """
        if not self._current_session:
            return False
        
        return len(self._current_session.completed_reviews) > 0

    def get_undo_info(self) -> Optional[dict]:
        """
        Get information about the last review that can be undone.
        
        Returns:
            Optional[dict]: Information about the last review, or None if no undo possible.
        """
        if not self.can_undo():
            return None
        
        last_identifier = self._current_session.completed_reviews[-1]
        last_review_id = self._report_manager.get_last_review_id()
        
        return {
            'review_id': last_review_id,
            'source_identifier': last_identifier,
            'review_count': len(self._current_session.completed_reviews)
        }

    def save_session_state(self) -> None:
        """
        Save the current session state to prevent data loss.
        
        Uses atomic write operations to ensure data integrity.
        
        Raises:
            RuntimeError: If no active session exists.
            OSError: If file operations fail.
        """
        if not self._current_session:
            raise RuntimeError("No active session to save")
        
        session_file = self._session_dir / f"{self._current_session.session_id}.pkl"
        temp_file = session_file.with_suffix('.tmp')
        
        try:
            # Prepare session data for serialization
            session_data = {
                'session_state': self._current_session,
                'data_source_config': self._current_session.data_source_config,
                'next_review_id': self._next_review_id,
                'saved_timestamp': datetime.utcnow()
            }
            
            # Write to temporary file first (atomic operation)
            with open(temp_file, 'wb') as f:
                pickle.dump(session_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Atomic rename to final file
            temp_file.replace(session_file)
            
        except Exception as e:
            # Clean up temporary file if it exists
            if temp_file.exists():
                temp_file.unlink()
            raise OSError(f"Failed to save session state: {e}")

    def finalize_session(self) -> Optional[str]:
        """
        Finalize the current session and clean up resources.
        
        Returns:
            Optional[str]: Path to the final report file, or None if no session active.
        """
        if not self._current_session:
            return None
        
        try:
            # Finalize the report
            report_path = self._report_manager.finalize_report('excel')
            
            # Clean up session file
            session_file = self._session_dir / f"{self._current_session.session_id}.pkl"
            if session_file.exists():
                session_file.unlink()
            
            # Clear current session
            session_id = self._current_session.session_id
            self._current_session = None
            self._data_source = None
            self._next_review_id = 1
            
            return report_path
            
        except Exception as e:
            print(f"Warning: Error during session finalization: {e}")
            return None

    def get_session_progress(self) -> Optional[dict]:
        """
        Get current session progress information.
        
        Returns:
            Optional[dict]: Progress information or None if no active session.
        """
        if not self._current_session:
            return None
        
        return {
            'session_id': self._current_session.session_id,
            'experiment_name': self._current_session.experiment_name,
            'total_reviews': self._current_session.get_total_reviews(),
            'completed_reviews': len(self._current_session.completed_reviews),
            'remaining_reviews': len(self._current_session.remaining_queue),
            'progress_percentage': self._current_session.get_progress_percentage(),
            'created_timestamp': self._current_session.created_timestamp
        }

    def list_available_sessions(self) -> List[str]:
        """
        List all available session files for resumption.
        
        Returns:
            List[str]: List of session IDs that can be resumed.
        """
        session_files = list(self._session_dir.glob("*.pkl"))
        return [f.stem for f in session_files]

    def get_session_info(self, session_id: str) -> Optional[dict]:
        """
        Get information about a specific session without loading it.
        
        Args:
            session_id: The session ID to get information for.
            
        Returns:
            Optional[dict]: Session information or None if session doesn't exist.
        """
        session_file = self._session_dir / f"{session_id}.pkl"
        
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'rb') as f:
                session_data = pickle.load(f)
            
            session_state = session_data['session_state']
            return {
                'session_id': session_state.session_id,
                'experiment_name': session_state.experiment_name,
                'total_reviews': session_state.get_total_reviews(),
                'completed_reviews': len(session_state.completed_reviews),
                'remaining_reviews': len(session_state.remaining_queue),
                'progress_percentage': session_state.get_progress_percentage(),
                'created_timestamp': session_state.created_timestamp,
                'saved_timestamp': session_data.get('saved_timestamp'),
                'data_source_config': session_state.data_source_config
            }
            
        except Exception:
            return None