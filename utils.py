"""
PondMonitor Utilities Module

Provides centralized error handling, validation, and common utility functions.
Ensures consistent error responses and data validation across the application.

Features:
- Custom exception hierarchy
- Data validation utilities
- Error response formatting
- Request/response decorators
- Logging helpers
- Common data transformations
"""

import logging
import traceback
import functools
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass
from flask import jsonify, request, g
import re

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exception Hierarchy
# =============================================================================

class PondMonitorError(Exception):
    """Base exception for all PondMonitor errors"""
    
    def __init__(self, message: str, code: str = None, details: Dict = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc)


class ValidationError(PondMonitorError):
    """Raised when data validation fails"""
    pass


class ConfigurationError(PondMonitorError):
    """Raised when configuration is invalid"""
    pass


class ServiceError(PondMonitorError):
    """Raised when external service calls fail"""
    pass


class DataError(PondMonitorError):
    """Raised when data processing fails"""
    pass


class AuthenticationError(PondMonitorError):
    """Raised when authentication fails"""
    pass


class AuthorizationError(PondMonitorError):
    """Raised when authorization fails"""
    pass


class RateLimitError(PondMonitorError):
    """Raised when rate limits are exceeded"""
    pass


# =============================================================================
# Error Response Formatting
# =============================================================================

@dataclass
class ErrorResponse:
    """Standardized error response structure"""
    error: str
    code: str
    timestamp: str
    details: Optional[Dict] = None
    trace_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'error': self.error,
            'code': self.code,
            'timestamp': self.timestamp
        }
        if self.details:
            result['details'] = self.details
        if self.trace_id:
            result['trace_id'] = self.trace_id
        return result


def create_error_response(
    error: Union[Exception, str],
    code: str = None,
    details: Dict = None,
    status_code: int = 500
) -> Tuple[Dict[str, Any], int]:
    """
    Create standardized error response.
    
    Args:
        error: Exception instance or error message
        code: Error code (defaults to exception class name)
        details: Additional error details
        status_code: HTTP status code
    
    Returns:
        Tuple of (error_dict, status_code)
    """
    if isinstance(error, PondMonitorError):
        message = error.message
        error_code = error.code
        error_details = error.details
        if details:
            error_details.update(details)
    elif isinstance(error, Exception):
        message = str(error)
        error_code = code or error.__class__.__name__
        error_details = details or {}
    else:
        message = str(error)
        error_code = code or "UnknownError"
        error_details = details or {}
    
    # Get trace ID from Flask context if available
    trace_id = getattr(g, 'trace_id', None)
    
    response = ErrorResponse(
        error=message,
        code=error_code,
        timestamp=datetime.now(timezone.utc).isoformat(),
        details=error_details,
        trace_id=trace_id
    )
    
    return response.to_dict(), status_code


# =============================================================================
# Data Validation
# =============================================================================

class Validator:
    """Utility class for common data validation operations"""
    
    @staticmethod
    def validate_datetime_range(
        start: str, 
        end: str, 
        max_days: int = 30
    ) -> Tuple[datetime, datetime]:
        """
        Validate and parse datetime range parameters.
        
        Args:
            start: Start datetime string (ISO format)
            end: End datetime string (ISO format)
            max_days: Maximum allowed range in days
        
        Returns:
            Tuple of (start_datetime, end_datetime)
        
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Parse datetime strings
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValidationError(
                "Invalid datetime format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)",
                details={'start': start, 'end': end, 'parse_error': str(e)}
            )
        
        # Validate range
        if start_dt >= end_dt:
            raise ValidationError(
                "Start time must be before end time",
                details={'start': start, 'end': end}
            )
        
        # Check maximum range
        if (end_dt - start_dt).days > max_days:
            raise ValidationError(
                f"Time range cannot exceed {max_days} days",
                details={'start': start, 'end': end, 'days': (end_dt - start_dt).days}
            )
        
        # Check if start time is too far in the past
        max_past = datetime.now(timezone.utc) - timedelta(days=365)
        if start_dt < max_past:
            raise ValidationError(
                "Start time cannot be more than 1 year ago",
                details={'start': start, 'max_past': max_past.isoformat()}
            )
        
        return start_dt, end_dt
    
    @staticmethod
    def validate_sensor_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate sensor data values.
        
        Args:
            data: Sensor data dictionary
        
        Returns:
            Validated and sanitized data
        
        Raises:
            ValidationError: If validation fails
        """
        validated = {}
        errors = []
        
        # Temperature validation
        if 'temperature_c' in data:
            temp = data['temperature_c']
            if temp is not None:
                if not isinstance(temp, (int, float)):
                    errors.append("Temperature must be numeric")
                elif not -50 <= temp <= 80:
                    errors.append(f"Temperature {temp}°C is out of valid range (-50 to 80°C)")
                else:
                    validated['temperature_c'] = round(float(temp), 1)
        
        # Battery voltage validation
        if 'battery_v' in data:
            battery = data['battery_v']
            if battery is not None:
                if not isinstance(battery, (int, float)):
                    errors.append("Battery voltage must be numeric")
                elif not 0 <= battery <= 20:
                    errors.append(f"Battery voltage {battery}V is out of valid range (0 to 20V)")
                else:
                    validated['battery_v'] = round(float(battery), 2)
        
        # Solar voltage validation
        if 'solar_v' in data:
            solar = data['solar_v']
            if solar is not None:
                if not isinstance(solar, (int, float)):
                    errors.append("Solar voltage must be numeric")
                elif not 0 <= solar <= 25:
                    errors.append(f"Solar voltage {solar}V is out of valid range (0 to 25V)")
                else:
                    validated['solar_v'] = round(float(solar), 2)
        
        # Signal strength validation
        if 'signal_dbm' in data:
            signal = data['signal_dbm']
            if signal is not None:
                if not isinstance(signal, int):
                    errors.append("Signal strength must be integer")
                elif not -150 <= signal <= 0:
                    errors.append(f"Signal strength {signal}dBm is out of valid range (-150 to 0dBm)")
                else:
                    validated['signal_dbm'] = int(signal)
        
        # Water level validation
        if 'level_cm' in data:
            level = data['level_cm']
            if level is not None:
                if not isinstance(level, (int, float)):
                    errors.append("Water level must be numeric")
                elif not 0 <= level <= 500:
                    errors.append(f"Water level {level}cm is out of valid range (0 to 500cm)")
                else:
                    validated['level_cm'] = round(float(level), 1)
        
        # Outflow validation
        if 'outflow_lps' in data:
            outflow = data['outflow_lps']
            if outflow is not None:
                if not isinstance(outflow, (int, float)):
                    errors.append("Outflow rate must be numeric")
                elif not 0 <= outflow <= 100:
                    errors.append(f"Outflow rate {outflow}L/s is out of valid range (0 to 100L/s)")
                else:
                    validated['outflow_lps'] = round(float(outflow), 2)
        
        if errors:
            raise ValidationError(
                "Sensor data validation failed",
                details={'errors': errors, 'data': data}
            )
        
        return validated
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
        
        Returns:
            True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """
        Validate phone number format (international).
        
        Args:
            phone: Phone number to validate
        
        Returns:
            True if valid, False otherwise
        """
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        # Check if it's a reasonable length for international number
        return 7 <= len(digits) <= 15


# =============================================================================
# Flask Decorators
# =============================================================================

def handle_errors(func: Callable) -> Callable:
    """
    Decorator to handle exceptions and return standardized error responses.
    
    Usage:
        @app.route('/api/data')
        @handle_errors
        def get_data():
            # Your route logic here
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            error_dict, status_code = create_error_response(e, status_code=400)
            return jsonify(error_dict), status_code
        except ServiceError as e:
            logger.error(f"Service error in {func.__name__}: {e}")
            error_dict, status_code = create_error_response(e, status_code=503)
            return jsonify(error_dict), status_code
        except AuthenticationError as e:
            logger.warning(f"Authentication error in {func.__name__}: {e}")
            error_dict, status_code = create_error_response(e, status_code=401)
            return jsonify(error_dict), status_code
        except AuthorizationError as e:
            logger.warning(f"Authorization error in {func.__name__}: {e}")
            error_dict, status_code = create_error_response(e, status_code=403)
            return jsonify(error_dict), status_code
        except RateLimitError as e:
            logger.warning(f"Rate limit error in {func.__name__}: {e}")
            error_dict, status_code = create_error_response(e, status_code=429)
            return jsonify(error_dict), status_code
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            logger.debug(traceback.format_exc())
            error_dict, status_code = create_error_response(
                "Internal server error",
                code="InternalServerError",
                status_code=500
            )
            return jsonify(error_dict), status_code
    
    return wrapper


def log_requests(func: Callable) -> Callable:
    """
    Decorator to log HTTP requests with timing and trace IDs.
    
    Usage:
        @app.route('/api/data')
        @log_requests
        def get_data():
            # Your route logic here
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Generate trace ID for request tracking
        trace_id = generate_trace_id()
        g.trace_id = trace_id
        
        # Log request start
        start_time = time.time()
        logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                'trace_id': trace_id,
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            }
        )
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Log successful request
            logger.info(
                f"Request completed: {request.method} {request.path} "
                f"in {duration:.3f}s",
                extra={
                    'trace_id': trace_id,
                    'duration': duration,
                    'status': 'success'
                }
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log failed request
            logger.error(
                f"Request failed: {request.method} {request.path} "
                f"after {duration:.3f}s - {e}",
                extra={
                    'trace_id': trace_id,
                    'duration': duration,
                    'status': 'error',
                    'error': str(e)
                }
            )
            
            raise
    
    return wrapper


def validate_json(required_fields: List[str] = None, 
                 optional_fields: List[str] = None) -> Callable:
    """
    Decorator to validate JSON request body.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
    
    Usage:
        @app.route('/api/data', methods=['POST'])
        @validate_json(required_fields=['name', 'value'])
        def create_data():
            data = request.get_json()
            # data is guaranteed to have required fields
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                raise ValidationError("Request must contain JSON data")
            
            data = request.get_json()
            if not data:
                raise ValidationError("Request body is empty")
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    raise ValidationError(
                        f"Missing required fields: {missing_fields}",
                        details={'missing_fields': missing_fields}
                    )
            
            # Check for unexpected fields
            if required_fields or optional_fields:
                allowed_fields = set(required_fields or []) | set(optional_fields or [])
                unexpected_fields = [field for field in data.keys() if field not in allowed_fields]
                if unexpected_fields:
                    raise ValidationError(
                        f"Unexpected fields: {unexpected_fields}",
                        details={'unexpected_fields': unexpected_fields}
                    )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# =============================================================================
# Utility Functions
# =============================================================================

def generate_trace_id() -> str:
    """Generate unique trace ID for request tracking"""
    import uuid
    return str(uuid.uuid4())[:8]


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to integer.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Integer value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def calculate_battery_percentage(voltage: float, 
                                min_voltage: float = 3.0, 
                                max_voltage: float = 4.2) -> int:
    """
    Calculate battery percentage from voltage.
    
    Args:
        voltage: Current battery voltage
        min_voltage: Minimum voltage (0%)
        max_voltage: Maximum voltage (100%)
    
    Returns:
        Battery percentage (0-100)
    """
    if voltage <= min_voltage:
        return 0
    if voltage >= max_voltage:
        return 100
    
    percentage = ((voltage - min_voltage) / (max_voltage - min_voltage)) * 100
    return round(max(0, min(100, percentage)))


def get_signal_quality(signal_dbm: int) -> Dict[str, Any]:
    """
    Get signal quality description from dBm value.
    
    Args:
        signal_dbm: Signal strength in dBm
    
    Returns:
        Dictionary with quality info
    """
    if signal_dbm >= -70:
        return {'quality': 'Excellent', 'color': '#10b981', 'bars': 4}
    elif signal_dbm >= -85:
        return {'quality': 'Good', 'color': '#3b82f6', 'bars': 3}
    elif signal_dbm >= -100:
        return {'quality': 'Fair', 'color': '#f59e0b', 'bars': 2}
    else:
        return {'quality': 'Poor', 'color': '#ef4444', 'bars': 1}


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
    
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
    
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove or replace dangerous characters
    import string
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    sanitized = ''.join(c for c in filename if c in valid_chars)
    
    # Remove multiple spaces and trim
    sanitized = ' '.join(sanitized.split())
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed_file"
    
    return sanitized


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, 
                   key: str, 
                   limit: int, 
                   window: int) -> bool:
        """
        Check if request is allowed under rate limit.
        
        Args:
            key: Unique key for rate limiting (e.g., IP address)
            limit: Maximum requests allowed
            window: Time window in seconds
        
        Returns:
            True if request is allowed
        """
        now = time.time()
        
        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup(now)
        
        # Get request history for this key
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove requests outside the window
        cutoff = now - window
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff]
        
        # Check if under limit
        if len(self.requests[key]) < limit:
            self.requests[key].append(now)
            return True
        
        return False
    
    def _cleanup(self, now: float) -> None:
        """Remove old entries to prevent memory leaks"""
        cutoff = now - 3600  # Remove entries older than 1 hour
        
        for key in list(self.requests.keys()):
            self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff]
            if not self.requests[key]:
                del self.requests[key]
        
        self.last_cleanup = now


# Global rate limiter instance
rate_limiter = RateLimiter()


if __name__ == "__main__":
    # Example usage and testing
    
    # Test validation
    try:
        start, end = Validator.validate_datetime_range(
            "2025-01-01T00:00:00",
            "2025-01-02T00:00:00"
        )
        print(f"✅ Date validation passed: {start} to {end}")
    except ValidationError as e:
        print(f"❌ Date validation failed: {e}")
    
    # Test sensor data validation
    try:
        data = {
            'temperature_c': 25.5,
            'battery_v': 12.6,
            'solar_v': 18.2,
            'signal_dbm': -75
        }
        validated = Validator.validate_sensor_data(data)
        print(f"✅ Sensor validation passed: {validated}")
    except ValidationError as e:
        print(f"❌ Sensor validation failed: {e}")
    
    # Test utility functions
    print(f"Battery percentage: {calculate_battery_percentage(3.7)}%")
    print(f"Signal quality: {get_signal_quality(-80)}")
    print(f"Duration: {format_duration(3665)}")