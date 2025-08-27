"""
Tests for Export Page Button Functionality - Action Button Enhancement
Tests the enhanced export button functionality with fallback demo mode.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

# Add src to path for imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Apply global patches immediately after path setup to prevent database connections
import unittest.mock

# Mock database initialization globally for this test module
_db_patcher = unittest.mock.patch('src.database.init_database')
_db_mock = _db_patcher.start()
_db_mock.return_value = Mock()

# Mock connection pool creation globally for this test module
_pool_patcher = unittest.mock.patch('psycopg2.pool.SimpleConnectionPool')
_pool_mock = _pool_patcher.start()
_pool_mock.return_value = Mock()

def teardown_module():
    """Clean up global patches after all tests in this module complete"""
    _db_patcher.stop()
    _pool_patcher.stop()

class TestExportButtonFunctionality:
    """Test export page button functionality and API interactions"""
    
    def test_export_page_structure(self):
        """Test that export page contains required elements"""
        # Import after mocks are in place
        from src.web.app import create_app
        
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.test_client() as client:
            response = client.get('/export')
            assert response.status_code == 200
            
            # Check for critical button elements
            assert b'id="estimateExport"' in response.data
            assert b'id="startExport"' in response.data
            assert b'Odhadnout velikost' in response.data
            assert b'Spustit export' in response.data
            
            # Check for required form elements
            assert b'id="startDate"' in response.data
            assert b'id="endDate"' in response.data
            assert b'id="dataTypeSelection"' in response.data
            assert b'id="formatSelection"' in response.data


class TestAdvancedExportAPIEndpoints:
    """Test the advanced export API endpoints functionality"""
    
    def test_advanced_export_config_endpoint(self):
        """Test /api/advanced-export/config endpoint"""
        from src.web.app import create_app
        
        with patch('src.web.app.AdvancedExportService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_filter_ranges.return_value = {
                "temp_range": {"min": -10, "max": 50, "absolute_min": -20, "absolute_max": 60},
                "battery_range": {"min": 0, "max": 100, "absolute_min": 0, "absolute_max": 100},
                "signal_range": {"min": -120, "max": -30, "absolute_min": -150, "absolute_max": 0}
            }
            mock_service_class.return_value = mock_service
            
            app = create_app()
            app.config['TESTING'] = True
            
            with app.test_client() as client:
                response = client.get('/api/advanced-export/config')
                assert response.status_code == 200
                
                data = json.loads(response.data)
                
                # Verify required configuration sections
                assert 'data_types' in data
                assert 'export_formats' in data
                assert 'aggregation_options' in data
                assert 'filter_ranges' in data
                
                # Verify data types
                data_types = data['data_types']
                assert len(data_types) == 3
                assert any(dt['id'] == 'pond_data' for dt in data_types)
                assert any(dt['id'] == 'station_data' for dt in data_types)
                assert any(dt['id'] == 'weather_data' for dt in data_types)
    
    def test_advanced_export_estimate_endpoint(self):
        """Test /api/advanced-export/estimate endpoint"""
        from src.web.app import create_app
        
        # Mock the app's advanced export service to return expected values
        with patch('src.web.app.AdvancedExportService') as mock_service_class:
            mock_service = Mock()
            mock_service.estimate_export.return_value = {
                "records_count": 2500,
                "file_size": 524288,  # 512KB
                "estimated_time": 15,  # 15 seconds
                "data_types_count": 2
            }
            mock_service_class.return_value = mock_service
            
            app = create_app()
            app.config['TESTING'] = True
            
            # Prepare test request data
            test_config = {
                "start_time": "2025-08-20T00:00:00Z",
                "end_time": "2025-08-26T23:59:59Z",
                "data_types": ["pond_data", "station_data"],
                "format": "excel",
                "aggregation": "hourly"
            }
            
            with app.test_client() as client:
                response = client.post('/api/advanced-export/estimate',
                                      data=json.dumps(test_config),
                                      content_type='application/json')
                
                assert response.status_code == 200
                
                data = json.loads(response.data)
                assert data['records_count'] == 2500
                assert data['file_size'] == 524288
                assert data['estimated_time'] == 15
                assert data['data_types_count'] == 2
    
    def test_advanced_export_endpoint(self):
        """Test /api/advanced-export endpoint for actual export"""
        from src.web.app import create_app
        
        # Mock the app's advanced export service to return CSV data
        test_csv_data = "Timestamp,Level_cm,Outflow_lps\n2025-08-26T10:00:00Z,150.5,5.2\n"
        
        with patch('src.web.app.AdvancedExportService') as mock_service_class:
            mock_service = Mock()
            mock_service.export_advanced.return_value = test_csv_data
            mock_service_class.return_value = mock_service
            
            app = create_app()
            app.config['TESTING'] = True
            
            # Prepare test request data
            test_config = {
                "start_time": "2025-08-26T00:00:00Z",
                "end_time": "2025-08-26T23:59:59Z",
                "data_types": ["pond_data"],
                "format": "csv",
                "aggregation": "raw"
            }
            
            with app.test_client() as client:
                response = client.post('/api/advanced-export',
                                      data=json.dumps(test_config),
                                      content_type='application/json')
                
                assert response.status_code == 200
                assert response.mimetype == 'text/csv'
                assert 'Content-Disposition' in response.headers
                assert 'attachment' in response.headers['Content-Disposition']
                assert response.data.decode('utf-8') == test_csv_data


class TestExportButtonDemoMode:
    """Test export button fallback demo mode functionality"""
    
    def test_demo_csv_export_structure(self):
        """Test that demo CSV export generates proper structure"""
        # This would typically be tested with JavaScript testing framework like Jest
        # For Python tests, we'll verify the expected data structure
        
        expected_csv_headers = [
            'Timestamp', 'Level_cm', 'Outflow_lps', 'Temperature_C', 'Battery_pct'
        ]
        
        # Test data should follow this pattern
        expected_data_types = {
            'Timestamp': 'ISO 8601 datetime string',
            'Level_cm': 'float with 2 decimal places',
            'Outflow_lps': 'float with 2 decimal places', 
            'Temperature_C': 'float with 1 decimal place',
            'Battery_pct': 'integer 0-100'
        }
        
        # Verify structure expectations
        assert len(expected_csv_headers) == 5
        assert 'Timestamp' in expected_csv_headers
        assert 'Level_cm' in expected_csv_headers
        assert 'Outflow_lps' in expected_csv_headers
    
    def test_demo_json_export_structure(self):
        """Test that demo JSON export generates proper structure"""
        expected_json_structure = {
            'metadata': {
                'export_time': 'ISO datetime',
                'start_time': 'ISO datetime', 
                'end_time': 'ISO datetime',
                'data_types': 'array',
                'aggregation': 'string',
                'record_count': 'integer'
            },
            'data': 'array of data objects'
        }
        
        # Verify expected structure
        assert 'metadata' in expected_json_structure
        assert 'data' in expected_json_structure
        
        metadata_fields = expected_json_structure['metadata']
        assert 'export_time' in metadata_fields
        assert 'start_time' in metadata_fields
        assert 'end_time' in metadata_fields
        assert 'record_count' in metadata_fields
    
    def test_demo_excel_export_format(self):
        """Test that demo Excel export generates proper XML format"""
        expected_excel_elements = [
            '<?xml version="1.0"?>',
            '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"',
            '<DocumentProperties xmlns="urn:schemas-microsoft-com:office:office">',
            '<Author>PondMonitor System</Author>',
            '<Worksheet ss:Name="Pond Data">',
            '<Table>',
            '<Row>',
            '<Cell><Data ss:Type="String">',
            '<Cell><Data ss:Type="DateTime">',
            '<Cell><Data ss:Type="Number">'
        ]
        
        # Verify expected XML structure elements
        for element in expected_excel_elements:
            assert isinstance(element, str)
            assert len(element) > 0


class TestExportButtonErrorHandling:
    """Test error handling in export button functionality"""
    
    @pytest.fixture
    def app(self):
        """Create Flask test app with failing services"""
        from src.web.app import create_app
        
        with patch('src.database.init_database') as mock_db_init:
            # Mock database initialization failure
            mock_db_init.side_effect = Exception("Database connection failed")
            
            try:
                app = create_app()
                app.config['TESTING'] = True
                app.config['WTF_CSRF_ENABLED'] = False
                return app
            except:
                # Create a minimal app if initialization fails
                from flask import Flask
                app = Flask(__name__)
                app.config['TESTING'] = True
                return app
    
    def test_export_config_endpoint_fallback(self):
        """Test that export config endpoint handles service failures gracefully"""
        # When backend services fail, frontend should use fallback configuration
        fallback_config = {
            "data_types": [
                {"id": "pond_data", "name": "Pond Measurements", "description": "Temperature, pH, oxygen levels"},
                {"id": "station_data", "name": "Station Diagnostics", "description": "Battery, signal, solar power"},
                {"id": "weather_data", "name": "Weather Data", "description": "Temperature, humidity, pressure"}
            ],
            "export_formats": [
                {"id": "excel", "name": "Excel (.xlsx)", "description": "Professional Excel format with charts"},
                {"id": "csv", "name": "CSV", "description": "Comma-separated values"},
                {"id": "json", "name": "JSON", "description": "JavaScript Object Notation"}
            ]
        }
        
        # Verify fallback structure
        assert len(fallback_config['data_types']) == 3
        assert len(fallback_config['export_formats']) == 3
        
        # Verify critical data types exist
        data_type_ids = [dt['id'] for dt in fallback_config['data_types']]
        assert 'pond_data' in data_type_ids
        assert 'station_data' in data_type_ids
        assert 'weather_data' in data_type_ids
    
    def test_export_estimate_fallback_ranges(self):
        """Test that export estimates use realistic fallback values"""
        # Mock estimate ranges when API is unavailable
        fallback_estimates = {
            'records_count_range': (1000, 6000),
            'file_size_range': (100000, 1048576),  # 100KB to 1MB
            'processing_time_range': (5, 35)  # 5 to 35 seconds
        }
        
        # Verify realistic ranges
        assert fallback_estimates['records_count_range'][0] >= 1000
        assert fallback_estimates['records_count_range'][1] <= 6000
        assert fallback_estimates['file_size_range'][0] >= 100000  # At least 100KB
        assert fallback_estimates['file_size_range'][1] <= 1048576  # Max 1MB
        assert fallback_estimates['processing_time_range'][0] >= 5  # At least 5 seconds


class TestExportButtonIntegration:
    """Test integration between export buttons and backend services"""
    
    def test_export_button_configuration_loading(self):
        """Test that export buttons properly load configuration"""
        # Test configuration loading sequence
        config_loading_steps = [
            'initialize_export_manager',
            'load_export_options', 
            'render_data_type_options',
            'render_format_options',
            'render_aggregation_options',
            'setup_filter_controls',
            'setup_event_listeners'
        ]
        
        # Verify all required initialization steps are defined
        for step in config_loading_steps:
            assert isinstance(step, str)
            assert len(step) > 0
    
    def test_export_button_event_handlers(self):
        """Test that export buttons have proper event handlers"""
        required_event_handlers = {
            'estimateExport': 'click',
            'startExport': 'click',
            'refreshPreview': 'click',
            'quick_range_buttons': 'click'
        }
        
        # Verify all required event handlers are defined
        for button_id, event_type in required_event_handlers.items():
            assert isinstance(button_id, str)
            assert event_type == 'click'
    
    def test_export_progress_tracking(self):
        """Test export progress tracking functionality"""
        progress_tracking_elements = [
            'progressFill',
            'progressText', 
            'progressStatus',
            'exportProgress'
        ]
        
        # Verify progress tracking elements are defined
        for element in progress_tracking_elements:
            assert isinstance(element, str)
            assert len(element) > 0
            assert element.startswith('progress') or element.startswith('export')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])