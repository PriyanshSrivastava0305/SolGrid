from unittest import TestCase
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from processing.data_processor import DataProcessor
from tests.test_utils import TEST_CONFIG, mock_setup_logger, mock_clean_text, mock_standardize_date

# Apply mocks
@patch('processing.data_processor.setup_logger', mock_setup_logger)
@patch('processing.data_processor.clean_text', mock_clean_text)
@patch('processing.data_processor.standardize_date', mock_standardize_date)
class TestDataProcessor(TestCase):
    def setUp(self):
        self.processor = DataProcessor(TEST_CONFIG)
        
        # Sample test data
        self.test_mnre_data = pd.DataFrame({
            'project_name': ['Solar Project A'],
            'capacity': ['500 MW'],
            'state': ['Karnataka'],
            'district': ['Bangalore'],
            'developer': ['Test Developer'],
            'commissioning_date': ['2024-01-15']
        })
        
    def test_capacity_extraction(self):
        """Test capacity extraction from various formats"""
        test_cases = {
            '500 MW': 500.0,
            '1.5 GW': 1500.0,
            '800KW': 0.8,
            '1,000MW': 1000.0,
            'invalid': np.nan
        }
        
        for input_str, expected in test_cases.items():
            result = self.processor._extract_capacity(input_str)
            if pd.isna(expected):
                self.assertTrue(pd.isna(result))
            else:
                self.assertEqual(result, expected)
                
    def test_location_string_creation(self):
        """Test creation of location strings for geocoding"""
        test_df = pd.DataFrame({
            'district': ['Bangalore', 'Mumbai', None],
            'state': ['Karnataka', 'Maharashtra', 'Gujarat'],
            'location': [None, 'Bandra', 'Kutch']
        })
        
        result = self.processor._create_location_string(test_df)
        
        self.assertEqual(result[0], 'Bangalore, Karnataka, India')
        self.assertEqual(result[1], 'Bandra, Maharashtra, India')
        self.assertEqual(result[2], 'Kutch, Gujarat, India')
        
    def test_state_standardization(self):
        """Test standardization of state names"""
        test_cases = {
            'Karnataka': 'Karnataka',
            'GUJARAT': 'Gujarat',
            'AP': 'Andhra Pradesh',
            'Delhi NCR': 'Delhi',
            'Unknown': 'Unknown'
        }
        
        for input_state, expected in test_cases.items():
            result = self.processor._standardize_state(input_state)
            self.assertEqual(result, expected)
            
    @patch('os.makedirs')
    def test_mnre_data_cleaning(self, mock_makedirs):
        """Test cleaning of MNRE data"""
        cleaned_data = self.processor._clean_mnre_data(self.test_mnre_data)
        
        self.assertIn('capacity_mw', cleaned_data.columns)
        self.assertEqual(cleaned_data['capacity_mw'].iloc[0], 500.0)
        self.assertEqual(cleaned_data['state'].iloc[0], 'Karnataka')
        self.assertEqual(cleaned_data['data_source'].iloc[0], 'MNRE')
        
    def test_project_deduplication(self):
        """Test deduplication of project entries"""
        test_data = pd.DataFrame({
            'project_name': ['Project A', 'Project A', 'Project B'],
            'capacity_mw': [500.0, 500.0, 300.0],
            'latitude': [14.8971, 14.8972, 15.0000],
            'longitude': [77.5876, 77.5877, 77.6000],
            'developer': ['Dev A', 'Dev A', 'Dev B'],
            'data_source': ['MNRE', 'SECI', 'MNRE']
        })
        
        deduped_data = self.processor._deduplicate_projects(test_data)
        
        # Should combine the duplicate Project A entries
        self.assertEqual(len(deduped_data), 2)
        self.assertIn('Project A', deduped_data['project_name'].values)
        self.assertIn('Project B', deduped_data['project_name'].values)