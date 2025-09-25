"""
Centralized logging configuration for VAITP-Auditor.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class VaitpFormatter(logging.Formatter):
    """Custom formatter for VAITP-Auditor logs."""
    
    def __init__(self):
        super().__init__()
        self.default_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.error_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d in %(funcName)s()"
    
    def format(self, record):
        if record.levelno >= logging.ERROR:
            formatter = logging.Formatter(self.error_format)
        else:
            formatter = logging.Formatter(self.default_format)
        return formatter.format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    session_id: Optional[str] = None
) -> logging.Logger:
    """
    Set up centralized logging configuration for VAITP-Auditor.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to log file. If None, uses default location.
        console_output: Whether to output logs to console.
        session_id: Optional session ID to include in log file name.
        
    Returns:
        logging.Logger: Configured root logger for the application.
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logs directory
    log_dir = Path.home() / '.vaitp_auditor' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate log file name if not provided
    if log_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if session_id:
            log_file = log_dir / f"vaitp_auditor_{session_id}_{timestamp}.log"
        else:
            log_file = log_dir / f"vaitp_auditor_{timestamp}.log"
    else:
        log_file = Path(log_file)
    
    # Get root logger for the application
    logger = logging.getLogger('vaitp_auditor')
    logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create custom formatter
    formatter = VaitpFormatter()
    
    # Add file handler
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # File gets all messages
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file {log_file}: {e}")
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        # Use simpler format for console
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(console_handler)
    
    # Set up error handler for stderr
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter("ERROR: %(message)s")
    error_handler.setFormatter(error_formatter)
    logger.addHandler(error_handler)
    
    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False
    
    # Log initial setup message
    logger.info(f"Logging initialized - Level: {level}, File: {log_file}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the module/component requesting the logger.
        
    Returns:
        logging.Logger: Logger instance for the module.
    """
    return logging.getLogger(f'vaitp_auditor.{name}')


def log_exception(logger: logging.Logger, exception: Exception, context: dict = None) -> None:
    """
    Log an exception with optional context information.
    
    Args:
        logger: Logger instance to use.
        exception: Exception to log.
        context: Optional context dictionary with additional information.
    """
    context_str = ""
    if context:
        context_items = [f"{k}={v}" for k, v in context.items()]
        context_str = f" (Context: {', '.join(context_items)})"
    
    logger.error(f"{exception.__class__.__name__}: {exception}{context_str}", exc_info=True)


def cleanup_old_logs(days_old: int = 30) -> int:
    """
    Clean up old log files to prevent disk space issues.
    
    Args:
        days_old: Delete log files older than this many days.
        
    Returns:
        int: Number of log files cleaned up.
    """
    log_dir = Path.home() / '.vaitp_auditor' / 'logs'
    
    if not log_dir.exists():
        return 0
    
    cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
    cleaned_count = 0
    
    try:
        for log_file in log_dir.glob("*.log"):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    cleaned_count += 1
            except Exception:
                # Skip files we can't process
                continue
    except Exception:
        # If we can't access the directory, just return 0
        pass
    
    return cleaned_count