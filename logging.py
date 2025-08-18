"""
PondMonitor Logging Configuration

Centralized logging setup with structured formatting, file rotation,
and different log levels for different components.

Features:
- Structured JSON logging for production
- Human-readable formatting for development
- File rotation with size and time-based policies
- Request tracing with correlation IDs
- Performance metrics logging
- Error alerting integration (future)
"""

import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

from config import LoggingConfig


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Outputs log records as JSON for easy parsing by log aggregation systems.
    """
    
    def __init__(self, include_extra: bool = True):
        """
        Initialize JSON formatter.
        
        Args:
            include_extra: Whether to include extra fields from log records
        """
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
        
        Returns:
            JSON-formatted log string
        """
        # Base log data
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add process and thread info
        log_data.update({
            'process_id': record.process,
            'process_name': record.processName,
            'thread_id': record.thread,
            'thread_name': record.threadName
        })
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields if enabled
        if self.include_extra:
            # Get extra fields (excluding standard fields)
            standard_fields = {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                'filename', 'module', 'lineno', 'funcName', 'created', 
                'msecs', 'relativeCreated', 'thread', 'threadName', 
                'processName', 'process', 'message', 'exc_info', 'exc_text',
                'stack_info'
            }
            
            extra_fields = {
                key: value for key, value in record.__dict__.items()
                if key not in standard_fields and not key.startswith('_')
            }
            
            if extra_fields:
                log_data['extra'] = extra_fields
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output.
    
    Adds color coding to different log levels for better visibility.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def __init__(self, use_colors: bool = True):
        """
        Initialize colored formatter.
        
        Args:
            use_colors: Whether to use color codes (disabled for non-TTY)
        """
        super().__init__()
        self.use_colors = use_colors and sys.stderr.isatty()
        
        # Format string
        self.format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(message)s [%(filename)s:%(lineno)d]'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.
        
        Args:
            record: Log record to format
        
        Returns:
            Formatted log string with colors
        """
        if self.use_colors and record.levelname in self.COLORS:
            # Add color to level name
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )
        
        # Format with timestamp
        formatter = logging.Formatter(self.format_string)
        return formatter.format(record)


class RequestTrackingFilter(logging.Filter):
    """
    Filter to add request tracking information to log records.
    
    Adds trace ID and request context to all log records within a request.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add request tracking info to log record.
        
        Args:
            record: Log record to modify
        
        Returns:
            Always True (don't filter any records)
        """
        try:
            # Try to get Flask request context
            from flask import g, request
            
            # Add trace ID if available
            if hasattr(g, 'trace_id'):
                record.trace_id = g.trace_id
            
            # Add request method and path
            if request:
                record.request_method = request.method
                record.request_path = request.path
                record.request_ip = request.remote_addr
                
        except (ImportError, RuntimeError):
            # Flask not available or outside request context
            pass
        
        return True


class PerformanceFilter(logging.Filter):
    """
    Filter to add performance metrics to log records.
    
    Tracks timing information for operations.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add performance metrics to log record.
        
        Args:
            record: Log record to modify
        
        Returns:
            Always True (don't filter any records)
        """
        # Add high-resolution timestamp for performance analysis
        import time
        record.precise_timestamp = time.time()
        
        # Add memory usage if available
        try:
            import psutil
            process = psutil.Process()
            record.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            record.cpu_percent = process.cpu_percent()
        except (ImportError, psutil.NoSuchProcess):
            pass
        
        return True


class LoggingSetup:
    """
    Main logging setup and configuration class.
    
    Provides methods to configure logging for different environments
    and components of the PondMonitor application.
    """
    
    def __init__(self, config: LoggingConfig):
        """
        Initialize logging setup.
        
        Args:
            config: Logging configuration
        """
        self.config = config
        self.handlers_created = {}
        
    def setup_logging(self, 
                     json_logging: bool = False,
                     enable_request_tracking: bool = True,
                     enable_performance_tracking: bool = False) -> None:
        """
        Setup logging configuration.
        
        Args:
            json_logging: Use JSON formatting for structured logs
            enable_request_tracking: Add request context to logs
            enable_performance_tracking: Add performance metrics to logs
        """
        # Create logs directory
        log_dir = Path(self.config.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config.get_level())
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Create console handler
        console_handler = self._create_console_handler(json_logging)
        root_logger.addHandler(console_handler)
        
        # Create file handler
        file_handler = self._create_file_handler(json_logging)
        root_logger.addHandler(file_handler)
        
        # Create error file handler
        error_handler = self._create_error_handler(json_logging)
        root_logger.addHandler(error_handler)
        
        # Add filters
        if enable_request_tracking:
            request_filter = RequestTrackingFilter()
            for handler in root_logger.handlers:
                handler.addFilter(request_filter)
        
        if enable_performance_tracking:
            perf_filter = PerformanceFilter()
            for handler in root_logger.handlers:
                handler.addFilter(perf_filter)
        
        # Configure specific loggers
        self._configure_component_loggers()
        
        # Log successful setup
        logger = logging.getLogger(__name__)
        logger.info(
            f"Logging configured successfully",
            extra={
                'log_level': self.config.level,
                'log_file': self.config.log_file,
                'json_logging': json_logging,
                'request_tracking': enable_request_tracking,
                'performance_tracking': enable_performance_tracking
            }
        )
    
    def _create_console_handler(self, json_logging: bool) -> logging.Handler:
        """Create console handler for stdout/stderr output"""
        handler = logging.StreamHandler(sys.stdout)
        
        if json_logging:
            formatter = JSONFormatter()
        else:
            formatter = ColoredFormatter()
        
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        
        return handler
    
    def _create_file_handler(self, json_logging: bool) -> logging.Handler:
        """Create rotating file handler for all logs"""
        handler = logging.handlers.RotatingFileHandler(
            filename=self.config.log_file,
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        
        if json_logging:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(self.config.format)
        
        handler.setFormatter(formatter)
        handler.setLevel(self.config.get_level())
        
        return handler
    
    def _create_error_handler(self, json_logging: bool) -> logging.Handler:
        """Create separate handler for error logs"""
        error_log_file = self.config.log_file.replace('.log', '_errors.log')
        
        handler = logging.handlers.RotatingFileHandler(
            filename=error_log_file,
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        
        if json_logging:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
                'Location: %(pathname)s:%(lineno)d in %(funcName)s\n'
                '%(exc_info)s\n' + '-' * 80
            )
        
        handler.setFormatter(formatter)
        handler.setLevel(logging.ERROR)
        
        return handler
    
    def _configure_component_loggers(self) -> None:
        """Configure specific loggers for different components"""
        
        # Database logger - more verbose in debug mode
        db_logger = logging.getLogger('database')
        if self.config.get_level() <= logging.DEBUG:
            db_logger.setLevel(logging.DEBUG)
        else:
            db_logger.setLevel(logging.INFO)
        
        # Weather service logger
        weather_logger = logging.getLogger('services.weather_service')
        weather_logger.setLevel(logging.INFO)
        
        # Export service logger
        export_logger = logging.getLogger('services.export_service')
        export_logger.setLevel(logging.INFO)
        
        # Flask logger - quieter by default
        flask_logger = logging.getLogger('werkzeug')
        flask_logger.setLevel(logging.WARNING)
        
        # HTTP requests logger
        requests_logger = logging.getLogger('urllib3')
        requests_logger.setLevel(logging.WARNING)
        
        # LoRa gateway logger
        lora_logger = logging.getLogger('LoraGateway')
        lora_logger.setLevel(logging.INFO)


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.
    
    Provides a logger instance configured for the specific class.
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger
    
    def log_method_call(self, method_name: str, **kwargs) -> None:
        """Log method call with parameters"""
        self.logger.debug(
            f"Calling {method_name}",
            extra={'method': method_name, 'parameters': kwargs}
        )
    
    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """Log performance metrics"""
        self.logger.info(
            f"Performance: {operation} completed in {duration:.3f}s",
            extra={
                'operation': operation,
                'duration': duration,
                'performance_data': kwargs
            }
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """Log error with context"""
        self.logger.error(
            f"Error: {error}",
            extra={'error_context': context or {}},
            exc_info=True
        )


def setup_logging(config: LoggingConfig,
                 environment: str = "production",
                 enable_request_tracking: bool = True) -> None:
    """
    Convenience function to setup logging.
    
    Args:
        config: Logging configuration
        environment: Environment type (development/production)
        enable_request_tracking: Enable request context tracking
    """
    logging_setup = LoggingSetup(config)
    
    # Use JSON logging in production
    json_logging = environment == "production"
    
    # Enable performance tracking in development
    performance_tracking = environment == "development"
    
    logging_setup.setup_logging(
        json_logging=json_logging,
        enable_request_tracking=enable_request_tracking,
        enable_performance_tracking=performance_tracking
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger by name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Context manager for performance logging
class PerformanceLogger:
    """Context manager for logging operation performance"""
    
    def __init__(self, logger: logging.Logger, operation: str, **context):
        """
        Initialize performance logger.
        
        Args:
            logger: Logger instance
            operation: Operation name
            **context: Additional context for logging
        """
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        """Start timing"""
        import time
        self.start_time = time.time()
        self.logger.debug(f"Starting operation: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log performance"""
        import time
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info(
                f"Operation completed: {self.operation} in {duration:.3f}s",
                extra={
                    'operation': self.operation,
                    'duration': duration,
                    'status': 'success',
                    **self.context
                }
            )
        else:
            self.logger.error(
                f"Operation failed: {self.operation} after {duration:.3f}s - {exc_val}",
                extra={
                    'operation': self.operation,
                    'duration': duration,
                    'status': 'error',
                    'error_type': exc_type.__name__ if exc_type else None,
                    **self.context
                },
                exc_info=True
            )


# Example usage
if __name__ == "__main__":
    from config import LoggingConfig
    
    # Create test logging configuration
    config = LoggingConfig(
        level="DEBUG",
        log_file="test_pondmonitor.log",
        max_bytes=1024 * 1024,  # 1MB
        backup_count=3
    )
    
    # Setup logging
    setup_logging(config, environment="development")
    
    # Test logging
    logger = get_logger(__name__)
    
    # Test different log levels
    logger.debug("Debug message with extra info", extra={'test_param': 'debug_value'})
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Test performance logging
    with PerformanceLogger(logger, "test_operation", test_param="test_value"):
        import time
        time.sleep(0.1)  # Simulate work
        logger.info("Work completed inside performance context")
    
    # Test class with LoggerMixin
    class TestClass(LoggerMixin):
        def test_method(self):
            self.log_method_call("test_method", param1="value1")
            self.logger.info("Method execution")
            
            # Simulate performance logging
            import time
            start = time.time()
            time.sleep(0.05)
            duration = time.time() - start
            self.log_performance("test_operation", duration, result="success")
    
    test_instance = TestClass()
    test_instance.test_method()
    
    print("Logging test completed. Check test_pondmonitor.log file.")