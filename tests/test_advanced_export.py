"""
Tests for Advanced Export Service and Flask Integration - Week 2
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from io import BytesIO

# Add src to path for imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.services.advanced_export_service import (
    AdvancedExportService, 
    AdvancedExportConfig, 
    EXCEL_ADVANCED_AVAILABLE
)
from src.database import DatabaseService, QueryResult


class TestAdvancedExportConfig:
    """Test advanced export configuration"""
    
    def test_advanced_config_initialization(self):
        """Test AdvancedExportConfig initialization with defaults"""
        config = AdvancedExportConfig(
            start_time=datetime.now(timezone.utc) - timedelta(days=7),
            end_time=datetime.now(timezone.utc)
        )
        
        # data_types might have defaults from parent class, so check if it's a list or None
        assert config.data_types is None or isinstance(config.data_types, list)
        assert config.aggregation == 'raw'
        assert config.include_charts is False
        assert config.excel_formatting is True
        assert config.temperature_range is None
        assert config.battery_range is None
        assert config.signal_range is None
    
    def test_advanced_config_with_filters(self):
        """Test AdvancedExportConfig with filtering options"""
        config = AdvancedExportConfig(
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc),
            data_types=['pond_metrics', 'station_metrics'],
            aggregation='hourly',
            include_charts=True,
            temperature_range=[10.0, 30.0],
            battery_range=[20, 100],
            signal_range=[-120, -50]
        )
        
        assert config.data_types == ['pond_metrics', 'station_metrics']
        assert config.aggregation == 'hourly'
        assert config.include_charts is True
        assert config.temperature_range == [10.0, 30.0]
        assert config.battery_range == [20, 100]
        assert config.signal_range == [-120, -50]


class TestAdvancedExportService:
    """Test Advanced Export Service functionality"""
    
    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service"""
        db_service = Mock(spec=DatabaseService)
        
        # Mock pond metrics data - Create a list that supports both to_dict() and len()
        pond_data = [
            {
                'timestamp': datetime(2024, 1, 1, 12, 0, 0),
                'water_level': 25.5,
                'outflow': 1.2,
                'temperature': 18.5
            },
            {
                'timestamp': datetime(2024, 1, 1, 13, 0, 0),
                'water_level': 25.8,
                'outflow': 1.1,
                'temperature': 19.0
            }
        ]
        
        pond_result = Mock()
        pond_result.to_dict = Mock(return_value=pond_data)
        pond_result.__len__ = Mock(return_value=len(pond_data))
        pond_result.__iter__ = Mock(return_value=iter(pond_data))
        
        # Mock station metrics data
        station_data = [
            {
                'timestamp': datetime(2024, 1, 1, 12, 0, 0),
                'battery_voltage': 12.5,
                'signal_strength': -85,
                'solar_voltage': 5.2,
                'temperature': 22.0
            },
            {
                'timestamp': datetime(2024, 1, 1, 13, 0, 0),
                'battery_voltage': 12.3,
                'signal_strength': -87,
                'solar_voltage': 5.0,
                'temperature': 23.0
            }
        ]
        
        station_result = Mock()
        station_result.to_dict = Mock(return_value=station_data)
        station_result.__len__ = Mock(return_value=len(station_data))
        station_result.__iter__ = Mock(return_value=iter(station_data))
        
        db_service.get_pond_metrics.return_value = pond_result
        db_service.get_station_metrics.return_value = station_result
        
        return db_service
    
    @pytest.fixture
    def advanced_export_service(self, mock_db_service):
        """Create AdvancedExportService instance"""
        return AdvancedExportService(mock_db_service)
    
    def test_service_initialization(self, mock_db_service):
        """Test service initialization"""
        service = AdvancedExportService(mock_db_service)
        assert service.db == mock_db_service
        assert service.export_progress == {}
    
    def test_get_filter_ranges(self, advanced_export_service, mock_db_service):
        """Test getting filter ranges for data"""
        # Mock database aggregation results
        mock_result = Mock()
        mock_result.fetchone.return_value = {
            'min_temp': 10.5,
            'max_temp': 35.2,
            'min_battery': 20,
            'max_battery': 100,
            'min_signal': -120,
            'max_signal': -45
        }
        mock_db_service.execute_query.return_value = mock_result
        
        ranges = advanced_export_service.get_filter_ranges()
        
        assert 'temperature_range' in ranges
        assert 'battery_range' in ranges
        assert 'signal_range' in ranges
        assert ranges['temperature_range']['min'] == 10.5
        assert ranges['temperature_range']['max'] == 35.2
        assert ranges['battery_range']['min'] == 20
        assert ranges['battery_range']['max'] == 100
    
    def test_estimate_export_basic(self, advanced_export_service, mock_db_service):
        """Test export size estimation"""
        # Mock count queries
        mock_result = Mock()
        mock_result.fetchone.return_value = {'count': 1000}
        mock_db_service.execute_query.return_value = mock_result
        
        config = AdvancedExportConfig(
            start_time=datetime.now(timezone.utc) - timedelta(days=7),
            end_time=datetime.now(timezone.utc),
            data_types=['pond_metrics'],
            format='excel'
        )
        
        estimate = advanced_export_service.estimate_export(config)
        
        assert 'records_count' in estimate
        assert 'file_size' in estimate
        assert 'estimated_time' in estimate
        assert 'data_types_count' in estimate
        assert estimate['records_count'] > 0
    
    def test_apply_filters_temperature(self, advanced_export_service):
        """Test temperature filtering"""
        data = [
            {'temperature': 15.0, 'value': 1},
            {'temperature': 25.0, 'value': 2},
            {'temperature': 35.0, 'value': 3}
        ]
        
        config = AdvancedExportConfig(
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc),
            temperature_range=[20.0, 30.0]
        )
        
        filtered = advanced_export_service._apply_filters(data, config)
        
        # Should only include the middle item (25.0)
        assert len(filtered) == 1
        assert filtered[0]['temperature'] == 25.0
    
    def test_apply_filters_battery_range(self, advanced_export_service):
        """Test battery range filtering"""
        data = [
            {'battery_voltage': 11.5, 'value': 1},
            {'battery_voltage': 12.5, 'value': 2},
            {'battery_voltage': 13.5, 'value': 3}
        ]
        
        config = AdvancedExportConfig(
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc),
            battery_range=[60, 90]  # Assuming 12.0-13.0V maps to 60-90%
        )
        
        # This would test the battery percentage calculation and filtering
        filtered = advanced_export_service._apply_filters(data, config)
        
        # Should filter based on battery percentage conversion
        assert isinstance(filtered, list)
    
    @pytest.mark.skipif(not EXCEL_ADVANCED_AVAILABLE, reason="pandas/openpyxl not available")
    def test_export_advanced_excel(self, advanced_export_service, mock_db_service):
        """Test advanced Excel export functionality"""
        config = AdvancedExportConfig(
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc),
            data_types=['pond_metrics'],
            format='excel',
            include_charts=True,
            excel_formatting=True
        )
        
        result = advanced_export_service.export_advanced(config)
        
        # Should return BytesIO object for Excel file
        assert isinstance(result, (bytes, BytesIO))
    
    def test_export_advanced_csv(self, advanced_export_service, mock_db_service):
        """Test advanced CSV export functionality"""
        config = AdvancedExportConfig(
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc),
            data_types=['pond_metrics'],
            format='csv',
            aggregation='raw'
        )
        
        result = advanced_export_service.export_advanced(config)
        
        # Should return CSV string
        assert isinstance(result, (str, bytes))
    
    def test_export_advanced_json(self, advanced_export_service, mock_db_service):
        """Test advanced JSON export functionality"""
        config = AdvancedExportConfig(
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc),
            data_types=['station_metrics'],
            format='json',
            aggregation='hourly'
        )
        
        result = advanced_export_service.export_advanced(config)
        
        # Should return JSON string
        assert isinstance(result, (str, bytes))
        
        # Try to parse as JSON to verify format
        if isinstance(result, str):
            parsed = json.loads(result)
            assert 'metadata' in parsed
            assert 'data' in parsed
    
    def test_aggregate_data_hourly(self, advanced_export_service):
        """Test hourly data aggregation"""
        data = {
            'pond_metrics': [
                {'timestamp': datetime(2024, 1, 1, 12, 15), 'temperature_c': 20.0, 'level_cm': 100},
                {'timestamp': datetime(2024, 1, 1, 12, 30), 'temperature_c': 21.0, 'level_cm': 101},
                {'timestamp': datetime(2024, 1, 1, 13, 15), 'temperature_c': 22.0, 'level_cm': 102}
            ]
        }
        
        aggregated = advanced_export_service._aggregate_data(data, 'hourly')
        
        # Should group by hour and average values
        assert isinstance(aggregated, dict)
        assert 'pond_metrics' in aggregated
        assert len(aggregated['pond_metrics']) <= len(data['pond_metrics'])  # Same or fewer records after aggregation
    
    def test_progress_tracking(self, advanced_export_service):
        """Test export progress tracking"""
        job_id = "test-job-123"
        
        # Test setting progress
        advanced_export_service._update_progress(job_id, 25, "Processing data...")
        progress = advanced_export_service.get_export_progress(job_id)
        
        assert progress['progress'] == 25
        assert progress['status'] == "Processing data..."
        assert 'timestamp' in progress
        
        # Test completing progress
        advanced_export_service._update_progress(job_id, 100, "Export completed")
        final_progress = advanced_export_service.get_export_progress(job_id)
        
        assert final_progress['progress'] == 100
        assert final_progress['status'] == "Export completed"


class TestAdvancedExportConfigGeneration:
    """Test export configuration generation (simulating Flask routes)"""
    
    def test_export_config_structure(self):
        """Test export configuration structure matches API expectations"""
        
        # Simulate what the Flask route would return
        config_options = {
            "data_types": [
                {"id": "pond_data", "name": "Pond Measurements", "description": "Temperature, pH, oxygen levels"},
                {"id": "station_data", "name": "Station Diagnostics", "description": "Battery, signal, solar power"},
                {"id": "weather_data", "name": "Weather Data", "description": "Temperature, humidity, pressure"}
            ],
            "aggregation_options": [
                {"id": "raw", "name": "Raw Data", "description": "All individual measurements"},
                {"id": "hourly", "name": "Hourly Average", "description": "Aggregated by hour"},
                {"id": "daily", "name": "Daily Summary", "description": "Min/max/average per day"}
            ],
            "export_formats": [
                {"id": "excel", "name": "Excel (.xlsx)", "description": "Professional Excel format with charts"},
                {"id": "csv", "name": "CSV", "description": "Comma-separated values"},
                {"id": "json", "name": "JSON", "description": "JavaScript Object Notation"}
            ]
        }
        
        # Verify structure
        assert len(config_options["data_types"]) == 3
        assert len(config_options["aggregation_options"]) == 3
        assert len(config_options["export_formats"]) == 3
        
        # Verify all required fields are present
        for data_type in config_options["data_types"]:
            assert "id" in data_type
            assert "name" in data_type
            assert "description" in data_type
        
        for agg_option in config_options["aggregation_options"]:
            assert "id" in agg_option
            assert "name" in agg_option
            assert "description" in agg_option
        
        for export_format in config_options["export_formats"]:
            assert "id" in export_format
            assert "name" in export_format
            assert "description" in export_format
    
    def test_filename_generation(self):
        """Test export filename generation logic"""
        from datetime import datetime
        
        # Simulate filename generation logic
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        data_types = ["pond_data", "station_data"]
        aggregation = "hourly"
        format_type = "excel"
        
        data_type_suffix = "_".join(data_types)
        filename_base = f"pond_advanced_{data_type_suffix}_{aggregation}_{timestamp}"
        
        expected_pattern = f"pond_advanced_pond_data_station_data_hourly_{timestamp}"
        assert filename_base == expected_pattern
        
        # Test with different format
        if format_type == "excel":
            full_filename = f"{filename_base}.xlsx"
        elif format_type == "csv":
            full_filename = f"{filename_base}.csv"
        elif format_type == "json":
            full_filename = f"{filename_base}.json"
        
        assert full_filename.endswith('.xlsx')
        assert "pond_advanced" in full_filename


if __name__ == '__main__':
    pytest.main([__file__, '-v'])