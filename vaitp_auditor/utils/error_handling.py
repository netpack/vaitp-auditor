"""
Comprehensive error handling utilities for VAITP-Auditor.
"""

import functools
import traceback
from typing import Any, Callable, Dict, Optional, Type, Union
from .logging_config import get_logger


class VaitpError(Exception):
    """Base exception class for VAITP-Auditor specific errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}


class ConfigurationError(VaitpError):
    """Raised when configuration is invalid or incomplete."""
    pass


class DataSourceError(VaitpError):
    """Base exception for data source related errors."""
    pass


class SessionError(VaitpError):
    """Raised when session operations fail."""
    pass


class UIError(VaitpError):
    """Raised when UI operations fail."""
    pass


class ReportError(VaitpError):
    """Raised when report generation fails."""
    pass


class ResourceError(VaitpError):
    """Raised when resource management fails (files, memory, etc.)."""
    pass


class ErrorHandler:
    """
    Centralized error handling with logging and recovery strategies.
    """
    
    def __init__(self, logger_name: str = "error_handler"):
        self.logger = get_logger(logger_name)
        self._error_counts = {}
        self._recovery_strategies = {}
    
    def register_recovery_strategy(
        self, 
        error_type: Type[Exception], 
        strategy: Callable[[Exception, Dict[str, Any]], Any]
    ) -> None:
        """
        Register a recovery strategy for a specific error type.
        
        Args:
            error_type: Type of exception to handle.
            strategy: Function to call for recovery.
        """
        self._recovery_strategies[error_type] = strategy
    
    def handle_error(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None,
        reraise: bool = True
    ) -> Optional[Any]:
        """
        Handle an error with logging and optional recovery.
        
        Args:
            error: Exception that occurred.
            context: Additional context information.
            reraise: Whether to reraise the exception after handling.
            
        Returns:
            Optional[Any]: Result from recovery strategy, if any.
            
        Raises:
            Exception: The original exception if reraise=True and no recovery.
        """
        context = context or {}
        error_type = type(error)
        
        # Track error frequency
        error_key = f"{error_type.__name__}:{str(error)}"
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
        
        # Log the error with context
        self._log_error_with_context(error, context)
        
        # Try recovery strategy if available
        if error_type in self._recovery_strategies:
            try:
                self.logger.info(f"Attempting recovery for {error_type.__name__}")
                result = self._recovery_strategies[error_type](error, context)
                self.logger.info(f"Recovery successful for {error_type.__name__}")
                return result
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed for {error_type.__name__}: {recovery_error}")
        
        # Reraise if requested and no recovery was successful
        if reraise:
            raise error
        
        return None
    
    def _log_error_with_context(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error with full context and stack trace."""
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        
        self.logger.error(
            f"{error.__class__.__name__}: {error}",
            extra={
                'context': context_str,
                'error_count': self._error_counts.get(f"{type(error).__name__}:{str(error)}", 1),
                'stack_trace': traceback.format_exc()
            }
        )
    
    def get_error_statistics(self) -> Dict[str, int]:
        """Get statistics about handled errors."""
        return self._error_counts.copy()
    
    def reset_error_counts(self) -> None:
        """Reset error count statistics."""
        self._error_counts.clear()


# Global error handler instance
_global_error_handler = ErrorHandler()


def handle_errors(
    error_types: Union[Type[Exception], tuple] = Exception,
    context: Optional[Dict[str, Any]] = None,
    reraise: bool = True,
    default_return: Any = None
):
    """
    Decorator for automatic error handling in functions.
    
    Args:
        error_types: Exception type(s) to catch.
        context: Additional context to include in error logs.
        reraise: Whether to reraise exceptions after handling.
        default_return: Value to return if error is caught and not reraised.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                func_context = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                }
                if context:
                    func_context.update(context)
                
                result = _global_error_handler.handle_error(e, func_context, reraise=False)
                
                if reraise:
                    raise e
                
                return result if result is not None else default_return
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    error_types: Union[Type[Exception], tuple] = Exception,
    context: Optional[Dict[str, Any]] = None,
    default_return: Any = None,
    **kwargs
) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute.
        *args: Positional arguments for the function.
        error_types: Exception type(s) to catch.
        context: Additional context for error logging.
        default_return: Value to return if an error occurs.
        **kwargs: Keyword arguments for the function.
        
    Returns:
        Any: Function result or default_return if error occurred.
    """
    try:
        return func(*args, **kwargs)
    except error_types as e:
        exec_context = {
            'function': func.__name__,
            'module': getattr(func, '__module__', 'unknown'),
            'args_count': len(args),
            'kwargs_keys': list(kwargs.keys())
        }
        if context:
            exec_context.update(context)
        
        _global_error_handler.handle_error(e, exec_context, reraise=False)
        return default_return


def validate_input(
    value: Any,
    validator: Callable[[Any], bool],
    error_message: str,
    error_type: Type[Exception] = ValueError
) -> Any:
    """
    Validate input with custom validator function.
    
    Args:
        value: Value to validate.
        validator: Function that returns True if value is valid.
        error_message: Error message to raise if validation fails.
        error_type: Type of exception to raise.
        
    Returns:
        Any: The validated value.
        
    Raises:
        Exception: Of error_type if validation fails.
    """
    try:
        if not validator(value):
            raise error_type(error_message)
        return value
    except Exception as e:
        if isinstance(e, error_type):
            raise
        # Wrap unexpected validation errors
        raise error_type(f"Validation failed: {e}")


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    error_types: Union[Type[Exception], tuple] = Exception
):
    """
    Decorator for retrying functions on specific errors.
    
    Args:
        max_attempts: Maximum number of retry attempts.
        delay: Initial delay between retries in seconds.
        backoff_factor: Factor to multiply delay by after each attempt.
        error_types: Exception type(s) to retry on.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except error_types as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:  # Don't sleep on last attempt
                        logger = get_logger('retry')
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger = get_logger('retry')
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            # Re-raise the last exception if all attempts failed
            raise last_exception
        
        return wrapper
    return decorator


def setup_error_recovery_strategies():
    """Set up default recovery strategies for common error types."""
    
    def file_permission_recovery(error: Exception, context: Dict[str, Any]) -> Optional[str]:
        """Recovery strategy for file permission errors."""
        logger = get_logger('recovery')
        
        if 'file_path' in context:
            file_path = context['file_path']
            logger.info(f"Attempting to create alternative path for {file_path}")
            
            # Try to create in user's home directory
            from pathlib import Path
            import tempfile
            
            try:
                temp_dir = Path.home() / '.vaitp_auditor' / 'temp'
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                # Create temporary file with similar name
                original_name = Path(file_path).name
                temp_file = temp_dir / f"temp_{original_name}"
                
                logger.info(f"Created alternative path: {temp_file}")
                return str(temp_file)
            except Exception as recovery_error:
                logger.error(f"File permission recovery failed: {recovery_error}")
        
        return None
    
    def database_connection_recovery(error: Exception, context: Dict[str, Any]) -> bool:
        """Recovery strategy for database connection errors."""
        logger = get_logger('recovery')
        logger.info("Attempting database connection recovery")
        
        # Simple retry strategy - could be enhanced with connection pooling
        import time
        time.sleep(1)  # Brief pause before retry
        
        return True  # Indicate that retry should be attempted
    
    def memory_error_recovery(error: Exception, context: Dict[str, Any]) -> bool:
        """Recovery strategy for memory errors."""
        logger = get_logger('recovery')
        logger.warning("Memory error detected - attempting garbage collection")
        
        import gc
        gc.collect()
        
        return True  # Indicate that operation should be retried
    
    # Register recovery strategies
    _global_error_handler.register_recovery_strategy(PermissionError, file_permission_recovery)
    _global_error_handler.register_recovery_strategy(ConnectionError, database_connection_recovery)
    _global_error_handler.register_recovery_strategy(MemoryError, memory_error_recovery)


# Initialize recovery strategies
setup_error_recovery_strategies()