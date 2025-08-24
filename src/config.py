"""
PondMonitor Configuration System

Centralized configuration management with validation and type safety.
Replaces scattered os.getenv() calls throughout the application.

Features:
- Environment-specific configurations
- Type validation and conversion
- Default values with documentation
- Configuration validation on startup
- Secure handling of sensitive data
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "pond_data"
    user: str = "pond_user"
    password: str = "secretpassword"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    
    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def get_connection_dict(self) -> Dict[str, Any]:
        """Get connection parameters as dictionary for psycopg2"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "connect_timeout": 10
        }


@dataclass
class RedisConfig:
    """Redis connection configuration"""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    database: int = 0
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    decode_responses: bool = True
    
    def get_connection_dict(self) -> Dict[str, Any]:
        """Get Redis connection parameters"""
        config = {
            "host": self.host,
            "port": self.port,
            "db": self.database,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "decode_responses": self.decode_responses
        }
        if self.password:
            config["password"] = self.password
        return config


@dataclass
class WeatherConfig:
    """Weather API configuration"""
    latitude: float = 49.6265900
    longitude: float = 18.3016172
    altitude: int = 350
    cache_duration: int = 3600  # 1 hour in seconds
    user_agent: str = "PondMonitor/1.0 (pond@monitor.cz)"
    api_timeout: int = 15
    
    def validate(self) -> None:
        """Validate weather configuration"""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Invalid longitude: {self.longitude}")
        if self.altitude < -500 or self.altitude > 9000:
            raise ValueError(f"Invalid altitude: {self.altitude}")


@dataclass
class SerialConfig:
    """Serial/LoRa communication configuration"""
    port: str = "/dev/ttyUSB0"
    baud_rate: int = 9600
    timeout: int = 1
    testing_mode: bool = False
    simulate_data: bool = False
    retry_delay: int = 5
    max_retries: int = 3
    
    def validate(self) -> None:
        """Validate serial configuration"""
        if not self.testing_mode and not Path(self.port).exists():
            logger.warning(f"Serial port {self.port} does not exist")
        if self.baud_rate not in [9600, 19200, 38400, 57600, 115200]:
            logger.warning(f"Unusual baud rate: {self.baud_rate}")


@dataclass
class FlaskConfig:
    """Flask application configuration"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    testing: bool = False
    secret_key: str = "dev-key-change-in-production"
    environment: str = "production"
    
    def validate(self) -> None:
        """Validate Flask configuration"""
        if (self.environment == "production" and 
            not self.testing and 
            self.secret_key == "dev-key-change-in-production"):
            raise ValueError("Must set secure secret key for production")
        if self.debug and self.environment == "production":
            logger.warning("Debug mode enabled in production environment")


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "pondmonitor.log"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    def get_level(self) -> int:
        """Get logging level as integer"""
        return getattr(logging, self.level.upper(), logging.INFO)


@dataclass
class AlertingConfig:
    """Alerting system configuration (for future weeks)"""
    enabled: bool = False
    email_enabled: bool = False
    sms_enabled: bool = False
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    
    # Alert thresholds
    low_battery_threshold: float = 3.3
    high_temperature_threshold: float = 40.0
    low_temperature_threshold: float = -10.0
    signal_strength_threshold: int = -100


class PondMonitorConfig:
    """
    Main configuration class for PondMonitor application.
    
    Loads configuration from environment variables with sensible defaults.
    Provides validation and type conversion.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration from environment variables.
        
        Args:
            env_file: Optional path to .env file to load
        """
        self._load_env_file(env_file)
        
        # Initialize all configuration sections
        self.database = self._load_database_config()
        self.redis = self._load_redis_config()
        self.weather = self._load_weather_config()
        self.serial = self._load_serial_config()
        self.flask = self._load_flask_config()
        self.logging = self._load_logging_config()
        self.alerting = self._load_alerting_config()
        
        # Validate all configurations
        self.validate()
        
        logger.info("Configuration loaded successfully")
    
    def _load_env_file(self, env_file: Optional[str]) -> None:
        """Load environment variables from .env file if it exists"""
        if env_file and Path(env_file).exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
                logger.info(f"Loaded environment from {env_file}")
            except ImportError:
                logger.warning("python-dotenv not available, skipping .env file")
    
    def _get_env_var(self, key: str, default: Any = None, var_type: type = str) -> Any:
        """
        Get environment variable with type conversion and default value.
        
        Args:
            key: Environment variable key
            default: Default value if not found
            var_type: Type to convert to (str, int, float, bool)
        
        Returns:
            Converted value or default
        """
        value = os.getenv(key)
        if value is None:
            return default
        
        try:
            if var_type == bool:
                return value.lower() in ("true", "1", "yes", "on")
            elif var_type == int:
                return int(value)
            elif var_type == float:
                return float(value)
            else:
                return str(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid value for {key}: {value}, using default: {default}")
            return default
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment"""
        return DatabaseConfig(
            host=self._get_env_var("PG_HOST", "timescaledb"),
            port=self._get_env_var("PG_PORT", 5432, int),
            database=self._get_env_var("POSTGRES_DB", "pond_data"),
            user=self._get_env_var("POSTGRES_USER", "pond_user"),
            password=self._get_env_var("POSTGRES_PASSWORD", "secretpassword"),
            pool_size=self._get_env_var("DB_POOL_SIZE", 5, int),
            max_overflow=self._get_env_var("DB_MAX_OVERFLOW", 10, int),
            pool_timeout=self._get_env_var("DB_POOL_TIMEOUT", 30, int)
        )
    
    def _load_redis_config(self) -> RedisConfig:
        """Load Redis configuration from environment"""
        return RedisConfig(
            host=self._get_env_var("REDIS_HOST", "redis"),
            port=self._get_env_var("REDIS_PORT", 6379, int),
            password=self._get_env_var("REDIS_PASSWORD"),
            database=self._get_env_var("REDIS_DB", 0, int),
            socket_timeout=self._get_env_var("REDIS_SOCKET_TIMEOUT", 5, int),
            socket_connect_timeout=self._get_env_var("REDIS_CONNECT_TIMEOUT", 5, int)
        )
    
    def _load_weather_config(self) -> WeatherConfig:
        """Load weather API configuration from environment"""
        return WeatherConfig(
            latitude=self._get_env_var("WEATHER_LAT", 49.6265900, float),
            longitude=self._get_env_var("WEATHER_LON", 18.3016172, float),
            altitude=self._get_env_var("WEATHER_ALT", 350, int),
            cache_duration=self._get_env_var("WEATHER_CACHE_DURATION", 3600, int),
            user_agent=self._get_env_var("USER_AGENT", "PondMonitor/1.0 (pond@monitor.cz)"),
            api_timeout=self._get_env_var("WEATHER_API_TIMEOUT", 15, int)
        )
    
    def _load_serial_config(self) -> SerialConfig:
        """Load serial/LoRa configuration from environment"""
        return SerialConfig(
            port=self._get_env_var("SERIAL_PORT", "/dev/ttyUSB0"),
            baud_rate=self._get_env_var("BAUD_RATE", 9600, int),
            timeout=self._get_env_var("SERIAL_TIMEOUT", 1, int),
            testing_mode=self._get_env_var("TESTING_MODE", False, bool),
            simulate_data=self._get_env_var("SIMULATE_DATA", False, bool),
            retry_delay=self._get_env_var("RETRY_DELAY", 5, int),
            max_retries=self._get_env_var("MAX_RETRIES", 3, int)
        )
    
    def _load_flask_config(self) -> FlaskConfig:
        """Load Flask configuration from environment"""
        return FlaskConfig(
            host=self._get_env_var("FLASK_HOST", "0.0.0.0"),
            port=self._get_env_var("FLASK_PORT", 5000, int),
            debug=self._get_env_var("FLASK_DEBUG", False, bool),
            testing=self._get_env_var("FLASK_TESTING", False, bool),
            secret_key=self._get_env_var("FLASK_SECRET_KEY", "dev-key-change-in-production"),
            environment=self._get_env_var("FLASK_ENV", "production")
        )
    
    def _load_logging_config(self) -> LoggingConfig:
        """Load logging configuration from environment"""
        return LoggingConfig(
            level=self._get_env_var("LOG_LEVEL", "INFO"),
            log_file=self._get_env_var("LOG_FILE", "pondmonitor.log"),
            max_bytes=self._get_env_var("LOG_MAX_BYTES", 10 * 1024 * 1024, int),
            backup_count=self._get_env_var("LOG_BACKUP_COUNT", 5, int)
        )
    
    def _load_alerting_config(self) -> AlertingConfig:
        """Load alerting configuration from environment"""
        return AlertingConfig(
            enabled=self._get_env_var("ALERTING_ENABLED", False, bool),
            email_enabled=self._get_env_var("EMAIL_ALERTS_ENABLED", False, bool),
            sms_enabled=self._get_env_var("SMS_ALERTS_ENABLED", False, bool),
            smtp_server=self._get_env_var("SMTP_SERVER", ""),
            smtp_port=self._get_env_var("SMTP_PORT", 587, int),
            smtp_username=self._get_env_var("SMTP_USERNAME", ""),
            smtp_password=self._get_env_var("SMTP_PASSWORD", ""),
            low_battery_threshold=self._get_env_var("LOW_BATTERY_THRESHOLD", 3.3, float),
            high_temperature_threshold=self._get_env_var("HIGH_TEMP_THRESHOLD", 40.0, float),
            low_temperature_threshold=self._get_env_var("LOW_TEMP_THRESHOLD", -10.0, float),
            signal_strength_threshold=self._get_env_var("SIGNAL_THRESHOLD", -100, int)
        )
    
    def validate(self) -> None:
        """Validate all configuration sections"""
        try:
            self.weather.validate()
            self.serial.validate()
            self.flask.validate()
            logger.info("All configuration validation passed")
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
    
    def is_testing_mode(self) -> bool:
        """Check if application is running in testing mode"""
        return self.serial.testing_mode or self.flask.testing
    
    def is_development_mode(self) -> bool:
        """Check if application is in development mode"""
        return self.flask.environment == "development" or self.flask.debug
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get configuration summary for logging/debugging.
        Excludes sensitive information like passwords.
        """
        return {
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "user": self.database.user,
                "pool_size": self.database.pool_size
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port,
                "database": self.redis.database
            },
            "weather": {
                "latitude": self.weather.latitude,
                "longitude": self.weather.longitude,
                "altitude": self.weather.altitude,
                "cache_duration": self.weather.cache_duration
            },
            "serial": {
                "port": self.serial.port,
                "baud_rate": self.serial.baud_rate,
                "testing_mode": self.serial.testing_mode,
                "simulate_data": self.serial.simulate_data
            },
            "flask": {
                "host": self.flask.host,
                "port": self.flask.port,
                "environment": self.flask.environment,
                "debug": self.flask.debug
            },
            "logging": {
                "level": self.logging.level,
                "log_file": self.logging.log_file
            },
            "alerting": {
                "enabled": self.alerting.enabled,
                "email_enabled": self.alerting.email_enabled,
                "sms_enabled": self.alerting.sms_enabled
            }
        }


# Global configuration instance
# This will be initialized when the module is imported
config: Optional[PondMonitorConfig] = None


def init_config(env_file: Optional[str] = None) -> PondMonitorConfig:
    """
    Initialize global configuration instance.
    
    Args:
        env_file: Optional path to .env file
    
    Returns:
        Configured PondMonitorConfig instance
    """
    global config
    config = PondMonitorConfig(env_file)
    return config


def get_config() -> PondMonitorConfig:
    """
    Get the global configuration instance.
    
    Returns:
        PondMonitorConfig instance
    
    Raises:
        RuntimeError: If configuration hasn't been initialized
    """
    if config is None:
        raise RuntimeError("Configuration not initialized. Call init_config() first.")
    return config


# Configuration factory for testing
def create_test_config(**overrides) -> PondMonitorConfig:
    """
    Create a configuration instance for testing with overrides.
    
    Args:
        **overrides: Configuration values to override
    
    Returns:
        Test configuration instance
    """
    # Set testing environment variables temporarily
    original_env = {}
    for key, value in overrides.items():
        original_env[key] = os.getenv(key)
        os.environ[key] = str(value)
    
    try:
        # Set testing environment variables to avoid production validation
        os.environ['FLASK_TESTING'] = 'true'
        os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['PG_HOST'] = 'timescaledb'
        os.environ['REDIS_HOST'] = 'redis'
        
        test_config = PondMonitorConfig()
        test_config.flask.testing = True
        test_config.flask.secret_key = "test-secret-key"
        test_config.flask.environment = "testing"
        test_config.serial.testing_mode = True
        test_config.database.host = "timescaledb"
        test_config.redis.host = "redis"
        return test_config
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    # Example usage and configuration validation
    try:
        config = init_config(".env")
        print("Configuration loaded successfully!")
        print("\nConfiguration Summary:")
        import json
        print(json.dumps(config.get_summary(), indent=2))
    except Exception as e:
        print(f"Configuration error: {e}")