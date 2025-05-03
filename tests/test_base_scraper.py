from unittest import TestCase
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil
from pathlib import Path
from tests.test_utils import mock_setup_logger

@patch('scrapers.base_scraper.setup_logger', mock_setup_logger)
class TestBaseScraper(TestCase):
    def setUp(self):
        from scrapers.base_scraper import BaseScraper
        self.temp_dir = tempfile.mkdtemp()
        self.test_scraper = BaseScraper("test_source")
        self.test_scraper.raw_data_dir = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('requests.Session')
    def test_scraper_initialization(self, mock_session):
        from scrapers.base_scraper import BaseScraper
        scraper = BaseScraper("test_source")
        self.assertEqual(scraper.source_name, "test_source")
        self.assertTrue(isinstance(scraper.raw_data_dir, Path))
        
    def test_save_raw_data(self):
        test_data = "test content"
        filepath = self.test_scraper.save_raw_data(test_data, "test_file.txt")
        self.assertTrue(filepath.exists())
        with open(filepath) as f:
            content = f.read()
        self.assertEqual(content, test_data)

    @patch('requests.Session')
    def test_make_request(self, mock_session):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_session.return_value.get.return_value = mock_response
        
        response = self.test_scraper.make_request("http://test.com/api")
        self.assertEqual(response.json(), {"data": "test"})
        
        # Verify proper headers were set
        mock_session.return_value.headers.update.assert_called_once()