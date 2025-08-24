"""
PondMonitor Test Suite - Comprehensive Service Tests

Unit tests covering all major PondMonitor components:
- Configuration system with environment variable handling
- Database service layer with connection pooling and health checks
- Data validation utilities and error handling
- Export service with multiple format support (CSV, JSON, Excel)
- Weather service integration with met.no API
- Flask decorators and request handling
- Integration tests for service interoperability

Usage Examples:
  # Run all tests
  python -m pytest tests/ -v

  # Run with coverage
  python -m pytest tests/ -v --cov=. --cov-report=html

  # Run specific test class
  python -m pytest tests/test_service.py::TestPondMonitorConfig -v

  # Run specific test method
  python -m pytest tests/test_service.py::TestPondMonitorConfig::test_config_initialization -v

  # Using Make
  make test

  # Full test suite with integration tests
  ./scripts/test_week1.sh

Test Configuration:
  Uses .env.testing for isolated test environment
  No external dependencies or hardware required
  Mocked services for reliable, fast execution
"""

import pytest
import json
import tempfile
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Import our modules
from src.config import PondMonitorConfig, DatabaseConfig, WeatherConfig, create_test_config
from src.database import DatabaseService, QueryResult
from src.utils import (
    Validator, ValidationError, PondMonitorError, 
    calculate_battery_percentage, get_signal_quality,
    handle_errors, log_requests, RateLimiter
)
from src.services.export_service import ExportService, ExportConfig, ExportMetadata
from src.services.weather_service import WeatherService, WeatherData, WeatherIconMapper


class TestPondMonitorConfig:
    """Test configuration system"""
    
    def test_config_initialization(self):
        """Test basic configuration initialization"""
        config = create_test_config()
        
        assert config is not None
        assert config.database.host == "timescaledb"
        assert config.redis.host == "redis"
        assert config.flask.testing is True
        assert config.serial.testing_mode is True
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = create_test_config()
        
        # Should not raise any exceptions
        config.validate()
        
        # Test invalid weather coordinates
        config.weather.latitude = 100.0  # Invalid latitude
        with pytest.raises(ValueError):
            config.validate()
    
    def test_config_environment_variables(self):
        """Test configuration from environment variables"""
        # Set test environment variables
        test_env = {
            'POSTGRES_USER': 'test_user',
            'POSTGRES_PASSWORD': 'test_pass',
            'WEATHER_LAT': '50.0',
            'WEATHER_LON': '14.0'
        }
        
        config = create_test_config(**test_env)
        
        assert config.database.user == 'test_user'
        assert config.database.password == 'test_pass'
        assert config.weather.latitude == 50.0
        assert config.weather.longitude == 14.0
    
    def test_config_summary(self):
        """Test configuration summary generation"""
        config = create_test_config()
        summary = config.get_summary()
        
        assert 'database' in summary
        assert 'redis' in summary
        assert 'weather' in summary
        assert 'flask' in summary
        
        # Passwords should not be in summary
        assert 'password' not in str(summary).lower()


class TestDatabaseService:
    """Test database service layer"""
    
    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service for testing"""
        config = DatabaseConfig(
            host="localhost",
            database="test_db",
            user="test_user",
            password="test_pass"
        )
        
        db_service = DatabaseService(config)
        
        # Mock the connection pool
        db_service._pool = Mock()
        db_service._pool._pool = [Mock(), Mock()]  # Mock pool list for health check
        mock_conn = Mock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        db_service._pool.getconn.return_value = mock_conn
        db_service._pool.putconn = Mock()
        
        return db_service, mock_conn
    
    def test_query_result_operations(self):
        """Test QueryResult helper methods"""
        rows = [
            ('2025-01-01 10:00:00', 25.5, 12.6),
            ('2025-01-01 11:00:00', 26.0, 12.4)
        ]
        columns = ['timestamp', 'temperature_c', 'battery_v']
        
        result = QueryResult(
            rows=rows,
            row_count=2,
            column_names=columns,
            execution_time=0.05
        )
        
        # Test first() method
        first_row = result.first()
        assert first_row == rows[0]
        
        # Test first_dict() method
        first_dict = result.first_dict()
        assert first_dict['timestamp'] == '2025-01-01 10:00:00'
        assert first_dict['temperature_c'] == 25.5
        
        # Test to_dict_list() method
        dict_list = result.to_dict_list()
        assert len(dict_list) == 2
        assert dict_list[0]['temperature_c'] == 25.5
        assert dict_list[1]['temperature_c'] == 26.0
    
    def test_execute_query(self, mock_db_service):
        """Test query execution"""
        db_service, mock_conn = mock_db_service
        
        # Setup mock cursor
        mock_cursor = Mock()
        mock_cursor_context = Mock()
        mock_cursor_context.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor_context.__exit__ = Mock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor_context
        mock_cursor.description = [('id',), ('name',)]
        mock_cursor.fetchall.return_value = [(1, 'test'), (2, 'test2')]
        
        # Execute query
        result = db_service.execute_query("SELECT * FROM test_table")
        
        assert result.row_count == 2
        assert result.column_names == ['id', 'name']
        assert len(result.rows) == 2
    
    def test_pond_metrics_operations(self, mock_db_service):
        """Test pond metrics insert and retrieval"""
        db_service, mock_conn = mock_db_service
        
        # Mock successful insert
        mock_cursor = Mock()
        mock_cursor_context = Mock()
        mock_cursor_context.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor_context.__exit__ = Mock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor_context
        
        # Test insert
        success = db_service.insert_pond_metrics(150.5, 2.3)
        assert success is True
        
        # Verify query was called
        mock_cursor.execute.assert_called()
        assert "INSERT INTO pond_metrics" in mock_cursor.execute.call_args[0][0]
    
    def test_health_check(self, mock_db_service):
        """Test database health check"""
        db_service, mock_conn = mock_db_service
        
        # Mock successful health check
        mock_cursor = Mock()
        mock_cursor_context = Mock()
        mock_cursor_context.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor_context.__exit__ = Mock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor_context
        mock_cursor.fetchone.return_value = (1,)
        
        health = db_service.health_check()
        
        assert 'healthy' in health
        assert 'connection_time' in health
        assert 'query_stats' in health


class TestValidationUtilities:
    """Test validation utilities"""
    
    def test_datetime_range_validation(self):
        """Test datetime range validation"""
        # Valid range
        start, end = Validator.validate_datetime_range(
            "2025-01-01T00:00:00Z",
            "2025-01-02T00:00:00Z"
        )
        
        assert start < end
        assert start.tzinfo is not None
        
        # Invalid: start after end
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_datetime_range(
                "2025-01-02T00:00:00Z",
                "2025-01-01T00:00:00Z"
            )
        assert "Start time must be before end time" in str(exc_info.value)
        
        # Invalid: range too long
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_datetime_range(
                "2024-01-01T00:00:00Z",
                "2024-12-31T23:59:59Z"
            )
        assert "cannot exceed 30 days" in str(exc_info.value)
    
    def test_sensor_data_validation(self):
        """Test sensor data validation"""
        # Valid data
        valid_data = {
            'temperature_c': 25.5,
            'battery_v': 12.6,
            'solar_v': 18.2,
            'signal_dbm': -75,
            'level_cm': 150.0,
            'outflow_lps': 2.5
        }
        
        validated = Validator.validate_sensor_data(valid_data)
        assert validated['temperature_c'] == 25.5
        assert validated['battery_v'] == 12.6
        assert validated['signal_dbm'] == -75
        
        # Invalid temperature
        invalid_data = valid_data.copy()
        invalid_data['temperature_c'] = 100.0  # Too high
        
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_sensor_data(invalid_data)
        assert "out of valid range" in str(exc_info.value)
    
    def test_email_validation(self):
        """Test email validation"""
        assert Validator.validate_email("test@example.com") is True
        assert Validator.validate_email("user.name+tag@domain.co.uk") is True
        assert Validator.validate_email("invalid-email") is False
        assert Validator.validate_email("@domain.com") is False
        assert Validator.validate_email("user@") is False
    
    def test_phone_validation(self):
        """Test phone number validation"""
        assert Validator.validate_phone_number("+420123456789") is True
        assert Validator.validate_phone_number("123-456-7890") is True
        assert Validator.validate_phone_number("123") is False
        assert Validator.validate_phone_number("123456789012345678") is False


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_battery_percentage_calculation(self):
        """Test battery percentage calculation"""
        # Test normal range
        assert calculate_battery_percentage(3.7) == 58  # Mid-range
        assert calculate_battery_percentage(3.0) == 0   # Minimum
        assert calculate_battery_percentage(4.2) == 100 # Maximum
        
        # Test out of range
        assert calculate_battery_percentage(2.5) == 0   # Below minimum
        assert calculate_battery_percentage(5.0) == 100 # Above maximum
    
    def test_signal_quality_assessment(self):
        """Test signal quality assessment"""
        # Excellent signal
        quality = get_signal_quality(-65)
        assert quality['quality'] == 'Excellent'
        assert quality['bars'] == 4
        
        # Poor signal
        quality = get_signal_quality(-110)
        assert quality['quality'] == 'Poor'
        assert quality['bars'] == 1
    
    def test_rate_limiter(self):
        """Test rate limiting functionality"""
        rate_limiter = RateLimiter()
        
        # Should allow first request
        assert rate_limiter.is_allowed("test_key", 2, 60) is True
        
        # Should allow second request
        assert rate_limiter.is_allowed("test_key", 2, 60) is True
        
        # Should block third request
        assert rate_limiter.is_allowed("test_key", 2, 60) is False


class TestExportService:
    """Test export service"""
    
    @pytest.fixture
    def mock_export_service(self):
        """Create mock export service"""
        mock_db = Mock()
        mock_db.get_pond_metrics.return_value = [
            {
                'timestamp': '2025-01-01T10:00:00Z',
                'level_cm': 150.5,
                'outflow_lps': 2.3
            }
        ]
        mock_db.get_station_metrics.return_value = [
            {
                'timestamp': '2025-01-01T10:00:00Z',
                'temperature_c': 25.5,
                'battery_v': 12.6,
                'solar_v': 18.2,
                'signal_dbm': -75,
                'station_id': 'test_station'
            }
        ]
        
        return ExportService(mock_db)
    
    def test_export_config_validation(self):
        """Test export configuration validation"""
        # Valid config
        config = ExportConfig(
            start_time=datetime(2025, 1, 1, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 2, tzinfo=timezone.utc),
            format='csv'
        )
        config.validate()  # Should not raise
        
        # Invalid: start after end
        invalid_config = ExportConfig(
            start_time=datetime(2025, 1, 2, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, tzinfo=timezone.utc),
            format='csv'
        )
        
        with pytest.raises(ValidationError):
            invalid_config.validate()
    
    def test_csv_export(self, mock_export_service):
        """Test CSV export functionality"""
        config = ExportConfig(
            start_time=datetime(2025, 1, 1, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 2, tzinfo=timezone.utc),
            format='csv'
        )
        
        result = mock_export_service.export_data(config)
        
        assert isinstance(result, str)
        assert 'timestamp' in result
        assert 'level_cm' in result
        assert 'temperature_c' in result
    
    def test_json_export(self, mock_export_service):
        """Test JSON export functionality"""
        config = ExportConfig(
            start_time=datetime(2025, 1, 1, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 2, tzinfo=timezone.utc),
            format='json'
        )
        
        result = mock_export_service.export_data(config)
        
        assert isinstance(result, str)
        data = json.loads(result)
        assert 'data' in data
        assert 'metadata' in data
    
    def test_export_formats_list(self, mock_export_service):
        """Test available export formats"""
        formats = mock_export_service.get_export_formats()
        
        assert len(formats) >= 2  # At least CSV and JSON
        
        format_names = [f['format'] for f in formats]
        assert 'csv' in format_names
        assert 'json' in format_names
    
    def test_size_estimation(self, mock_export_service):
        """Test export size estimation"""
        config = ExportConfig(
            start_time=datetime(2025, 1, 1, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 2, tzinfo=timezone.utc),
            format='csv'
        )
        
        estimate = mock_export_service.estimate_export_size(config)
        
        assert 'record_count' in estimate
        assert 'formats' in estimate
        assert 'csv' in estimate['formats']


class TestWeatherService:
    """Test weather service"""
    
    @pytest.fixture
    def mock_weather_service(self):
        """Create mock weather service"""
        from src.config import WeatherConfig
        
        config = WeatherConfig()
        service = WeatherService(config)
        
        # Mock the cache and API calls
        service.cache = Mock()
        service.cache.get.return_value = None
        service.cache.set.return_value = True
        
        return service
    
    def test_weather_icon_mapping(self):
        """Test weather icon mapping"""
        # Test known symbols
        icon_info = WeatherIconMapper.get_icon_info('clearsky_day')
        assert icon_info['emoji'] == '☀️'
        assert 'Clear' in icon_info['description']
        
        # Test symbol guessing
        symbol = WeatherIconMapper.guess_symbol(5.0, 90)  # Heavy rain, cloudy
        assert symbol == 'rain'
        
        symbol = WeatherIconMapper.guess_symbol(0.0, 10)  # No rain, clear
        assert symbol == 'clearsky_day'
    
    @patch('src.services.weather_service.requests.get')
    def test_weather_data_fetch(self, mock_get, mock_weather_service):
        """Test weather data fetching"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'properties': {
                'timeseries': [
                    {
                        'time': '2025-01-01T12:00:00Z',
                        'data': {
                            'instant': {
                                'details': {
                                    'air_temperature': 25.5,
                                    'air_pressure_at_sea_level': 1013.2,
                                    'relative_humidity': 65.0,
                                    'wind_speed': 3.2,
                                    'wind_from_direction': 180,
                                    'cloud_area_fraction': 30
                                }
                            },
                            'next_1_hours': {
                                'details': {'precipitation_amount': 0.1},
                                'summary': {'symbol_code': 'lightrain_day'}
                            }
                        }
                    }
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test current weather
        current = mock_weather_service.get_current_weather()
        
        assert current is not None
        assert current.temperature == 25.5
        assert current.pressure == 1013.2
        assert current.symbol_code == 'lightrain_day'
    
    def test_weather_data_parsing(self, mock_weather_service):
        """Test weather data parsing"""
        # Test entry with complete data
        entry = {
            'time': '2025-01-01T12:00:00Z',
            'data': {
                'instant': {
                    'details': {
                        'air_temperature': 25.5,
                        'air_pressure_at_sea_level': 1013.2,
                        'relative_humidity': 65.0,
                        'wind_speed': 3.2,
                        'wind_from_direction': 180,
                        'wind_speed_of_gust': 5.1,
                        'cloud_area_fraction': 30
                    }
                },
                'next_1_hours': {
                    'details': {'precipitation_amount': 0.1},
                    'summary': {'symbol_code': 'lightrain_day'}
                }
            }
        }
        
        weather_data = mock_weather_service._parse_weather_entry(entry)
        
        assert weather_data.temperature == 25.5
        assert weather_data.pressure == 1013.2
        assert weather_data.humidity == 65.0
        assert weather_data.wind_speed == 3.2
        assert weather_data.wind_direction == 180
        assert weather_data.precipitation == 0.1
        assert weather_data.symbol_code == 'lightrain_day'


class TestFlaskDecorators:
    """Test Flask decorators"""
    
    def test_handle_errors_decorator(self):
        """Test error handling decorator"""
        from flask import Flask, jsonify
        
        app = Flask(__name__)
        
        @handle_errors
        def test_function():
            raise ValidationError("Test validation error")
        
        with app.app_context():
            response, status_code = test_function()
            
            assert status_code == 400
            assert 'error' in response.json
    
    def test_log_requests_decorator(self):
        """Test request logging decorator"""
        from flask import Flask, g
        
        app = Flask(__name__)
        
        @log_requests
        def test_function():
            return "success"
        
        with app.test_request_context('/test'):
            result = test_function()
            
            assert result == "success"
            assert hasattr(g, 'trace_id')


class TestIntegration:
    """Integration tests for combined functionality"""
    
    def test_config_to_services_integration(self):
        """Test that configuration properly initializes services"""
        config = create_test_config()
        
        # Test database service initialization
        from src.database import DatabaseService
        db_service = DatabaseService(config.database)
        assert db_service.config == config.database
        
        # Test weather service initialization
        from src.services.weather_service import WeatherService
        weather_service = WeatherService(config.weather, config.redis)
        assert weather_service.config == config.weather
    
    def test_export_with_database_integration(self):
        """Test export service integration with database"""
        # This would be a more complex integration test
        # involving actual database operations
        pass


# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def test_config():
    """Create test configuration for the entire test session"""
    return create_test_config()


@pytest.fixture
def temp_directory():
    """Create temporary directory for test files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


# Test runner script
if __name__ == "__main__":
    """
    Run tests manually without pytest
    """
    import sys
    
    # Simple test runner
    test_classes = [
        TestPondMonitorConfig,
        TestDatabaseService, 
        TestValidationUtilities,
        TestUtilityFunctions,
        TestExportService,
        TestWeatherService,
        TestFlaskDecorators,
        TestIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n🧪 Running {test_class.__name__}")
        instance = test_class()
        
        # Find all test methods
        test_methods = [
            method for method in dir(instance) 
            if method.startswith('test_') and callable(getattr(instance, method))
        ]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                # Setup fixtures if needed
                if hasattr(instance, 'setup_method'):
                    instance.setup_method()
                
                # Run test
                getattr(instance, test_method)()
                print(f"  ✅ {test_method}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ❌ {test_method}: {e}")
                failed_tests.append(f"{test_class.__name__}.{test_method}: {e}")
            
            finally:
                # Cleanup if needed
                if hasattr(instance, 'teardown_method'):
                    instance.teardown_method()
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\n❌ Failed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"\n🎉 All tests passed!")
        sys.exit(0)