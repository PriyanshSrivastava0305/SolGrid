from unittest import TestCase
from unittest.mock import patch, MagicMock
import pandas as pd

class TestDashboardComponents(TestCase):
    def setUp(self):
        self.test_project = {
            "name": "Test Solar Plant",
            "latitude": 14.8971,
            "longitude": 77.5876,
            "capacity_mw": 500.0,
            "project_type": "Utility Scale",
            "developer": "Test Developer",
            "commissioning_year": 2024,
            "state": "Karnataka"
        }
        
    @patch('dashboard.components.map_compnent.px')
    @patch('dashboard.components.map_compnent.go')
    def test_project_map_creation(self, mock_go, mock_px):
        # Setup mock return values
        mock_scatter = MagicMock()
        mock_px.scatter_mapbox.return_value = mock_scatter
        mock_scatter.data = [MagicMock()]
        
        # Import here to use mocked dependencies
        from dashboard.components.map_compnent import create_project_map
        
        # Create test dataframe
        df = pd.DataFrame([self.test_project])
        map_figure = create_project_map(df)
        
        # Verify the scatter_mapbox was called with correct parameters
        mock_px.scatter_mapbox.assert_called_once()
        call_kwargs = mock_px.scatter_mapbox.call_args[1]
        
        self.assertEqual(call_kwargs['zoom'], 3.8)  # Default zoom level
        self.assertEqual(call_kwargs['mapbox_style'], "carto-positron")
        
    @patch('dashboard.components.map_compnent.px')
    def test_single_project_map(self, mock_px):
        # Setup mock return values
        mock_scatter = MagicMock()
        mock_px.scatter_mapbox.return_value = mock_scatter
        
        # Import here to use mocked dependencies
        from dashboard.components.map_compnent import create_single_project_map
        
        map_figure = create_single_project_map(self.test_project)
        
        # Verify scatter_mapbox was called with correct parameters
        mock_px.scatter_mapbox.assert_called_once()
        call_kwargs = mock_px.scatter_mapbox.call_args[1]
        
        self.assertEqual(call_kwargs['lat'], 'latitude')
        self.assertEqual(call_kwargs['lon'], 'longitude')
        self.assertEqual(call_kwargs['mapbox_style'], "carto-positron")