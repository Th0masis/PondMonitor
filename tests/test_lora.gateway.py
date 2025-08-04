import unittest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LoraGateway import LoRaGateway

class TestLoRaGateway(unittest.TestCase):
    def setUp(self):
        self.gateway = LoRaGateway()
    
    def test_validate_data_valid(self):
        """Test data validation with valid data"""
        valid_data = {
            'temperature_c': 25.5,
            'battery_v': 12.6,
            'solar_v': 18.2
        }
        self.assertTrue(self.gateway.validate_data(valid_data))
    
    def test_validate_data_missing_fields(self):
        """Test data validation with missing fields"""
        invalid_data = {
            'temperature_c': 25.5,
            'battery_v': 12.6
            # missing solar_v
        }
        self.assertFalse(self.gateway.validate_data(invalid_data))
    
    def test_validate_data_out_of_range(self):
        """Test data validation with out-of-range values"""
        invalid_data = {
            'temperature_c': 150,  # Too high
            'battery_v': 12.6,
            'solar_v': 18.2
        }
        self.assertFalse(self.gateway.validate_data(invalid_data))
    
    def test_process_data_valid_json(self):
        """Test data processing with valid JSON"""
        test_data = {
            'temperature_c': 25.5,
            'battery_v': 12.6,
            'solar_v': 18.2,
            'signal_dbm': -75
        }
        raw_json = json.dumps(test_data)
        
        processed = self.gateway.process_data(raw_json)
        
        self.assertIsNotNone(processed)
        self.assertEqual(processed['temperature_c'], 25.5)
        self.assertEqual(processed['battery_v'], 12.6)
        self.assertIn('last_heartbeat', processed)
    
    def test_process_data_invalid_json(self):
        """Test data processing with invalid JSON"""
        invalid_json = "{'invalid': json}"
        
        result = self.gateway.process_data(invalid_json)
        
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()