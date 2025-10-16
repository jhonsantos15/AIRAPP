"""
Configuración de logging centralizada y thread-safe para múltiples procesos.
"""
import os
import logging
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from src.core.config import settings


# Global state
_logger_initialized = False
_logger_lock = threading.Lock()
_app_logger: Optional[logging.Logger] = None


class SafeRotatingFileHandler(RotatingFileHandler):
    """
    Thread-safe and multi-process safe rotating file handler.
    Handles permission errors gracefully when multiple processes access the same log file.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = threading.Lock()
    
    def doRollover(self):
        """
        Override doRollover to handle permission errors gracefully.
        """
        with self._lock:
            try:
                super().doRollover()
            except (OSError, PermissionError) as e:
                # Log the error to stderr but don't crash the application
                import sys
                print(f"Warning: Could not rotate log file {self.baseFilename}: {e}", file=sys.stderr)
                # Continue without rotating - just keep writing to the current file
    
    def emit(self, record):
        """
        Emit a record with error handling for file access issues.
        """
        try:
            super().emit(record)
        except (OSError, PermissionError) as e:
            # Handle file access errors gracefully
            import sys
            print(f"Warning: Could not write to log file {self.baseFilename}: {e}", file=sys.stderr)


def get_app_logger() -> logging.Logger:
    """
    Get the centralized application logger.
    Configures the logger only once per process.
    """
    global _logger_initialized, _app_logger
    
    with _logger_lock:
        if _logger_initialized and _app_logger:
            return _app_logger
        
        # Create logger
        logger_name = f"{settings.app_name}_pid{os.getpid()}"
        _app_logger = logging.getLogger(logger_name)
        
        # Avoid duplicate handlers
        if _app_logger.handlers:
            _logger_initialized = True
            return _app_logger
        
        # Set level
        _app_logger.setLevel(getattr(logging, settings.log_level))
        
        # Create log directory
        log_dir = Path(settings.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create process-specific log file to avoid conflicts
        log_path = Path(settings.log_file)
        process_log_file = log_path.parent / f"{log_path.stem}_pid{os.getpid()}{log_path.suffix}"
        
        # Create file handler
        file_handler = SafeRotatingFileHandler(
            str(process_log_file),
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count
        )
        
        # Create formatter
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(name)s [%(process)d:%(thread)d]: %(message)s"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, settings.log_level))
        
        # Add handler to logger
        _app_logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        _app_logger.propagate = False
        
        _logger_initialized = True
        
        # Log initialization
        try:
            _app_logger.info(f"{settings.app_name} logger initialized - PID: {os.getpid()}")
        except Exception as e:
            import sys
            print(f"Warning: Could not write initial log message: {e}", file=sys.stderr)
        
        return _app_logger


def setup_flask_logging(app) -> None:
    """
    Configure Flask app to use the centralized logger.
    """
    # Get the centralized logger
    app_logger = get_app_logger()
    
    # Remove existing Flask handlers
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
    
    # Add our handler to Flask logger
    for handler in app_logger.handlers:
        app.logger.addHandler(handler)
    
    # Set same level
    app.logger.setLevel(app_logger.level)
    app.logger.propagate = False
    
    try:
        app.logger.info(f"Flask app logging configured - PID: {os.getpid()}")
    except Exception as e:
        import sys
        print(f"Warning: Could not configure Flask logging: {e}", file=sys.stderr)