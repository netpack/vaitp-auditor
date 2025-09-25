"""
Command-line interface entry point for VAITP-Auditor.
"""

import argparse
import sys
import random
from datetime import datetime
from pathlib import Path

from .session_manager import SessionManager
from .data_sources import DataSourceFactory
from .core.models import SessionConfig
from .utils.logging_config import setup_logging, get_logger, cleanup_old_logs
from .utils.error_handling import handle_errors, VaitpError
from .utils.resource_manager import cleanup_resources, get_resource_manager


@handle_errors(error_types=Exception, reraise=False)
def main():
    """
    Main entry point for the VAITP-Auditor application.
    
    Determines whether to launch GUI or CLI mode based on arguments and environment.
    Default behavior is to launch GUI mode if available, otherwise CLI mode.
    """
    # Parse arguments first to check for help/version and mode selection
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Determine interface mode
    if should_use_gui_mode(args):
        launch_gui_mode(args)
        return
    
    # Continue with CLI mode
    run_cli_mode(args)


def should_use_gui_mode(args) -> bool:
    """
    Determine if GUI mode should be used based on arguments and environment.
    
    Priority order:
    1. Explicit --cli flag forces CLI mode
    2. Explicit --gui flag forces GUI mode (fails if dependencies unavailable)
    3. Default behavior: GUI mode if dependencies available and interactive terminal
    4. Fallback: CLI mode
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        bool: True if GUI mode should be used, False for CLI mode
    """
    logger = get_logger(__name__)
    
    # Explicit CLI mode requested
    if hasattr(args, 'cli') and args.cli:
        logger.debug("CLI mode explicitly requested via --cli flag")
        return False
    
    # Explicit GUI mode requested
    if hasattr(args, 'gui') and args.gui:
        logger.debug("GUI mode explicitly requested via --gui flag")
        # Check if GUI dependencies are available
        if not _check_gui_dependencies():
            logger.error("GUI mode requested but dependencies not available")
            print("Error: GUI mode requested but GUI dependencies are not installed.", file=sys.stderr)
            print("Please install GUI dependencies with: pip install customtkinter pygments pillow", file=sys.stderr)
            sys.exit(1)
        return True
    
    # Default behavior: use GUI if available and in interactive environment
    try:
        # Check if we're in an interactive terminal
        if not _is_interactive_environment():
            logger.debug("Non-interactive environment detected, using CLI mode")
            return False
        
        # Check if GUI dependencies are available
        if not _check_gui_dependencies():
            logger.debug("GUI dependencies not available, falling back to CLI mode")
            return False
        
        logger.debug("Interactive environment with GUI dependencies available, using GUI mode")
        return True
            
    except Exception as e:
        logger.warning(f"Error determining interface mode: {e}, falling back to CLI mode")
        return False


def _check_gui_dependencies() -> bool:
    """
    Check if GUI dependencies are available.
    
    Returns:
        bool: True if all GUI dependencies are available, False otherwise
    """
    try:
        import customtkinter
        import pygments
        import PIL
        return True
    except ImportError:
        return False


def _is_interactive_environment() -> bool:
    """
    Check if we're running in an interactive environment.
    
    Returns:
        bool: True if interactive environment, False otherwise
    """
    try:
        # Check if stdin and stdout are connected to a terminal
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            return False
        
        # Check for common non-interactive environment indicators
        import os
        
        # CI/CD environments
        ci_indicators = ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 'JENKINS_URL', 'TRAVIS']
        if any(os.getenv(var) for var in ci_indicators):
            return False
        
        # SSH without X11 forwarding
        if os.getenv('SSH_CLIENT') and not os.getenv('DISPLAY'):
            return False
        
        return True
        
    except Exception:
        return False


def launch_gui_mode(args) -> None:
    """
    Launch the GUI mode of the application.
    
    Args:
        args: Parsed command-line arguments
    """
    logger = get_logger(__name__)
    
    try:
        # Import GUI main function
        from .gui.gui_app import main as gui_main
        
        # Set up logging for GUI mode
        log_level = "DEBUG" if hasattr(args, 'debug') and args.debug else "INFO"
        setup_logging(
            level=log_level,
            console_output=True,
            session_id=None,
            log_file=getattr(args, 'log_file', None)
        )
        
        logger.info("Launching VAITP-Auditor in GUI mode")
        
        # Launch GUI application with parsed arguments
        gui_main(args)
        
    except ImportError as e:
        logger.error(f"GUI mode import failed: {e}")
        print(f"Error: GUI mode not available - {e}", file=sys.stderr)
        print("Please install GUI dependencies with: pip install customtkinter pygments pillow", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error launching GUI mode: {e}")
        print(f"Error launching GUI mode: {e}", file=sys.stderr)
        sys.exit(1)


def run_cli_mode(args) -> None:
    """
    Run the CLI mode of the application.
    
    Args:
        args: Parsed command-line arguments
    """
    
    # Set up logging early
    logger = setup_logging(
        level="INFO",
        console_output=True,
        session_id=None
    )
    
    # Clean up old logs
    try:
        cleaned_logs = cleanup_old_logs(days_old=30)
        if cleaned_logs > 0:
            logger.debug(f"Cleaned up {cleaned_logs} old log files")
    except Exception as e:
        logger.warning(f"Failed to clean up old logs: {e}")
    
    logger.info("VAITP-Auditor starting up")
    
    print("VAITP-Auditor - Manual Code Verification Assistant")
    print("=" * 50)
    print("A tool for efficient manual verification of programmatically generated code snippets.")
    print()
    
    session_manager = None
    
    try:
        # Initialize session manager
        logger.debug("Initializing session manager")
        session_manager = SessionManager()
        
        # Check for existing sessions and offer resumption
        resumed_session = handle_session_resumption(session_manager)
        
        if not resumed_session:
            # Start new session with setup wizard
            start_new_session(session_manager, args)
        else:
            # Continue with resumed session
            print("Resuming review session...")
            logger.info("Resuming existing session")
            # Process the review queue (uses monitored version internally)
            session_manager.process_review_queue()
            
        # Finalize session
        finalize_session(session_manager)
        
        logger.info("VAITP-Auditor completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\nOperation cancelled by user.")
        print("Session progress has been saved and can be resumed later.")
        sys.exit(0)
    except VaitpError as e:
        logger.error(f"Application error: {e}")
        print(f"Error: {e}")
        if hasattr(e, 'context') and e.context:
            logger.debug(f"Error context: {e.context}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Unexpected error: {e}")
        print("Please check the log files for more details.")
        sys.exit(1)
    finally:
        # Clean up resources
        try:
            logger.debug("Cleaning up resources")
            cleanup_resources()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        # Get final resource statistics
        try:
            resource_manager = get_resource_manager()
            final_stats = resource_manager.get_resource_statistics()
            logger.debug(f"Final resource statistics: {final_stats}")
        except Exception as e:
            logger.error(f"Error getting final statistics: {e}")


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command-line argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog='vaitp-auditor',
        description='Manual Code Verification Assistant for programmatically generated code snippets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vaitp-auditor                    # Start GUI mode (default if available)
  vaitp-auditor --gui              # Explicitly start GUI mode
  vaitp-auditor --cli              # Start CLI mode
  vaitp-auditor --debug           # Enable debug logging
  vaitp-auditor --help            # Show this help message
  
Interface Mode Selection:
  By default, the application will launch in GUI mode if GUI dependencies
  are available and running in an interactive terminal. Use --cli to force
  CLI mode or --gui to force GUI mode (will fail if dependencies missing).
  
The tool will guide you through:
1. Experiment naming and configuration
2. Data source setup (supports folders, SQLite, Excel/CSV)
3. Sampling configuration
4. Output format selection
5. Manual code review process

For more information, visit: https://github.com/your-org/vaitp-auditor
        """
    )
    
    # Interface mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--gui',
        action='store_true',
        help='Force GUI mode (requires GUI dependencies: customtkinter, pygments, pillow)'
    )
    mode_group.add_argument(
        '--cli',
        action='store_true',
        help='Force CLI mode (terminal-based interface)'
    )
    
    # General options
    parser.add_argument(
        '--version',
        action='version',
        version='VAITP-Auditor 0.1.0'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging for troubleshooting'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        metavar='PATH',
        help='Path to log file (default: logs to console and auto-generated log files)'
    )
    
    # CLI-specific arguments
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Skip session resumption check and start a new session (CLI mode only)'
    )
    
    return parser


def handle_session_resumption(session_manager: SessionManager) -> bool:
    """
    Handle session resumption logic.
    
    Args:
        session_manager: The session manager instance.
        
    Returns:
        bool: True if a session was resumed, False if starting new session.
    """
    try:
        # Check for existing sessions
        session_id = session_manager.prompt_for_session_resumption()
        
        if session_id:
            # User chose to resume a session
            print(f"Attempting to resume session: {session_id}")
            
            # Get the data source type from session info
            session_info = session_manager.get_session_info(session_id)
            if not session_info:
                print("Failed to get session information. Starting new session instead.")
                return False
            
            data_source_config = session_info.get('data_source_config', {})
            source_type = data_source_config.get('data_source_type', 'folders')
            
            # Create and configure data source for resumed session
            print(f"\nReconfiguring {DataSourceFactory.get_source_description(source_type)} for resumed session...")
            data_source = DataSourceFactory.configure_data_source_interactive(source_type)
            
            if not data_source:
                print("Failed to configure data source. Starting new session instead.")
                return False
            
            # Attempt to resume with fallback handling
            success = session_manager.resume_session_with_fallback(session_id, data_source)
            
            if success:
                return True
            else:
                print("Session resumption failed. Starting new session.")
                return False
        
        return False
        
    except Exception as e:
        print(f"Error during session resumption: {e}")
        print("Starting new session instead.")
        return False


def start_new_session(session_manager: SessionManager, args) -> None:
    """
    Start a new review session with setup wizard.
    
    Args:
        session_manager: The session manager instance.
        args: Command-line arguments.
    """
    print("Starting new review session...")
    print()
    
    # Run setup wizard
    config = run_setup_wizard()
    
    if not config:
        print("Setup cancelled. Exiting.")
        sys.exit(0)
    
    # Create and configure data source
    data_source = create_data_source(config)
    
    if not data_source:
        print("Data source configuration failed. Exiting.")
        sys.exit(1)
    
    # Start the session
    try:
        session_id = session_manager.start_session(config, data_source)
        print(f"\nSession started successfully: {session_id}")
        
        # Display session information
        progress = session_manager.get_session_progress()
        if progress:
            print(f"Total items to review: {progress['total_reviews']}")
            print(f"Experiment: {progress['experiment_name']}")
            print()
        
        # Begin review process
        print("Starting code review process...")
        print("Use Ctrl+C at any time to save progress and exit.")
        print()
        
        session_manager.process_review_queue()
        
    except Exception as e:
        print(f"Failed to start session: {e}")
        sys.exit(1)


def run_setup_wizard() -> SessionConfig:
    """
    Run the interactive setup wizard to configure a new session.
    
    Returns:
        SessionConfig: Configuration for the new session, or None if cancelled.
    """
    print("Setup Wizard")
    print("-" * 20)
    print()
    
    try:
        # Step 1: Experiment naming
        experiment_name = get_experiment_name()
        if not experiment_name:
            return None
        
        # Step 2: Data source selection and configuration
        data_source_type = get_data_source_type()
        if not data_source_type:
            return None
        
        data_source_params = {}  # Will be configured by the data source itself
        
        # Step 3: Sampling configuration
        sample_percentage = get_sampling_percentage()
        if sample_percentage is None:
            return None
        
        # Step 4: Output format selection
        output_format = get_output_format()
        if not output_format:
            return None
        
        # Create configuration
        config = SessionConfig(
            experiment_name=experiment_name,
            data_source_type=data_source_type,
            data_source_params=data_source_params,
            sample_percentage=sample_percentage,
            output_format=output_format
        )
        
        # Display configuration summary
        display_configuration_summary(config)
        
        # Confirm configuration
        if not confirm_configuration():
            print("Configuration cancelled. Restarting setup wizard...")
            return run_setup_wizard()  # Recursive call to restart
        
        return config
        
    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
        return None
    except Exception as e:
        print(f"Error during setup: {e}")
        return None


def get_data_source_type() -> str:
    """
    Get data source type selection from user.
    
    Returns:
        str: Selected data source type, or None if cancelled.
    """
    print("\nStep 2: Data Source Selection")
    print("Choose the type of data source containing your code pairs.")
    print()
    
    available_types = DataSourceFactory.get_available_types()
    type_keys = list(available_types.keys())
    
    # Display available options
    for i, (key, description) in enumerate(available_types.items(), 1):
        print(f"{i}. {description}")
    
    print()
    
    while True:
        try:
            choice = input(f"Select data source type (1-{len(type_keys)}): ").strip()
            
            try:
                choice_index = int(choice) - 1
                
                if 0 <= choice_index < len(type_keys):
                    selected_type = type_keys[choice_index]
                    selected_description = available_types[selected_type]
                    print(f"Selected: {selected_description}")
                    return selected_type
                else:
                    print(f"Please enter a number between 1 and {len(type_keys)}.")
                    continue
                    
            except ValueError:
                print("Please enter a valid number.")
                continue
                
        except KeyboardInterrupt:
            return None


def get_experiment_name() -> str:
    """
    Get experiment name from user with automatic timestamp appending.
    
    Returns:
        str: Experiment name with timestamp, or None if cancelled.
    """
    print("Step 1: Experiment Naming")
    print("Enter a name for your code review experiment.")
    print("A timestamp will be automatically appended for unique identification.")
    print()
    
    while True:
        try:
            name = input("Experiment name: ").strip()
            
            if not name:
                print("Experiment name cannot be empty. Please try again.")
                continue
            
            # Validate name (basic alphanumeric + spaces, underscores, hyphens)
            if not all(c.isalnum() or c in ' _-' for c in name):
                print("Experiment name can only contain letters, numbers, spaces, underscores, and hyphens.")
                continue
            
            # Clean up the name
            clean_name = name.replace(' ', '_').replace('__', '_').strip('_')
            
            # Append timestamp for uniqueness
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            full_name = f"{clean_name}_{timestamp}"
            
            print(f"Full experiment name: {full_name}")
            return full_name
            
        except KeyboardInterrupt:
            return None


def get_sampling_percentage() -> float:
    """
    Get sampling percentage from user with validation.
    
    Returns:
        float: Sampling percentage (1-100), or None if cancelled.
    """
    print("\nStep 3: Sampling Configuration")
    print("Specify what percentage of the available code pairs to review.")
    print("This allows you to work with a manageable subset for large datasets.")
    print()
    
    while True:
        try:
            percentage_input = input("Sampling percentage (1-100, default 100): ").strip()
            
            if not percentage_input:
                # Default to 100%
                return 100.0
            
            try:
                percentage = float(percentage_input)
                
                if not (1 <= percentage <= 100):
                    print("Sampling percentage must be between 1 and 100.")
                    continue
                
                return percentage
                
            except ValueError:
                print("Please enter a valid number between 1 and 100.")
                continue
                
        except KeyboardInterrupt:
            return None


def get_output_format() -> str:
    """
    Get output format preference from user.
    
    Returns:
        str: Output format ('excel' or 'csv'), or None if cancelled.
    """
    print("\nStep 4: Output Format Selection")
    print("Choose the format for your review results report.")
    print()
    print("1. Excel (.xlsx) - Recommended for rich formatting and analysis")
    print("2. CSV (.csv) - For compatibility with other tools")
    print()
    
    while True:
        try:
            choice = input("Select output format (1-2, default 1): ").strip()
            
            if not choice or choice == '1':
                return 'excel'
            elif choice == '2':
                return 'csv'
            else:
                print("Please enter 1 for Excel or 2 for CSV.")
                continue
                
        except KeyboardInterrupt:
            return None


def create_data_source(config: SessionConfig):
    """
    Create and configure the data source based on configuration.
    
    Args:
        config: Session configuration.
        
    Returns:
        DataSource: Configured data source, or None if configuration failed.
    """
    try:
        data_source = DataSourceFactory.configure_data_source_interactive(config.data_source_type)
        
        if data_source:
            total_count = data_source.get_total_count()
            sampled_count = int(total_count * config.sample_percentage / 100)
            
            print(f"Items to review (with {config.sample_percentage}% sampling): {sampled_count}")
            return data_source
        else:
            return None
            
    except Exception as e:
        print(f"Error configuring data source: {e}")
        return None


def display_configuration_summary(config: SessionConfig) -> None:
    """
    Display a summary of the session configuration.
    
    Args:
        config: Session configuration to display.
    """
    print("\nConfiguration Summary")
    print("=" * 30)
    print(f"Experiment Name: {config.experiment_name}")
    print(f"Data Source: {DataSourceFactory.get_source_description(config.data_source_type)}")
    print(f"Sampling: {config.sample_percentage}% of available items")
    print(f"Output Format: {config.output_format.upper()}")
    print()


def confirm_configuration() -> bool:
    """
    Ask user to confirm the configuration.
    
    Returns:
        bool: True if confirmed, False if user wants to reconfigure.
    """
    while True:
        try:
            confirm = input("Proceed with this configuration? (y/n): ").strip().lower()
            
            if confirm in ['y', 'yes']:
                return True
            elif confirm in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
                continue
                
        except KeyboardInterrupt:
            return False


def finalize_session(session_manager: SessionManager) -> None:
    """
    Finalize the session and display results.
    
    Args:
        session_manager: The session manager instance.
    """
    try:
        # Get final progress information
        progress = session_manager.get_session_progress()
        
        if progress:
            print("\nSession Summary")
            print("=" * 20)
            print(f"Experiment: {progress['experiment_name']}")
            print(f"Reviews completed: {progress['completed_reviews']}/{progress['total_reviews']}")
            print(f"Progress: {progress['progress_percentage']:.1f}%")
        
        # Finalize and get report path
        report_path = session_manager.finalize_session()
        
        if report_path:
            print(f"\nResults saved to: {report_path}")
            print("Thank you for using VAITP-Auditor!")
        else:
            print("\nSession completed. Results may have been saved during the review process.")
            
    except Exception as e:
        print(f"Warning: Error during session finalization: {e}")
        print("Your review data should still be available in the reports directory.")


if __name__ == "__main__":
    main()