"""
Base scraper class for extracting data from various sources.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
import logging
import time
import requests
from datetime import datetime

from config import RAW_DATA_DIR, HEADERS
from utils import setup_logger, safe_request

class BaseScraper(ABC):
    """Base class for all scrapers."""
    
    def __init__(self, source_name: str):
        """Initialize the scraper with a source name."""
        self.source_name = source_name
        self.logger = setup_logger(f"scraper_{source_name}")
        self.raw_data_dir = RAW_DATA_DIR / source_name
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape data from the source.
        
        Returns:
            List of dictionaries containing the scraped data.
        """
        pass
    
    def save_raw_data(self, data: Any, filename: str) -> Path:
        """
        Save raw data to a file.
        
        Args:
            data: Data to save
            filename: Name of the file
            
        Returns:
            Path to the saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.raw_data_dir / f"{filename}_{timestamp}"
        
        if isinstance(data, (str, bytes)):
            mode = 'wb' if isinstance(data, bytes) else 'w'
            encoding = None if isinstance(data, bytes) else 'utf-8'
            
            with open(filepath, mode, encoding=encoding) as f:
                f.write(data)
        else:
            # For other types (like JSON), convert to string
            with open(filepath, 'w', encoding='utf-8') as f:
                if hasattr(data, 'json'):  # For responses with json method
                    try:
                        f.write(data.json())
                    except:
                        f.write(str(data))
                else:
                    f.write(str(data))
        
        self.logger.info(f"Saved raw data to {filepath}")
        return filepath
    
    def make_request(self, url: str, method: str = 'get', **kwargs) -> Optional[requests.Response]:
        """Make a request with the session."""
        return safe_request(url, method, session=self.session, **kwargs)
    
    def download_file(self, url: str, filename: str = None) -> Optional[Path]:
        """
        Download a file from a URL.
        
        Args:
            url: URL to download from
            filename: Name to save the file as (optional)
            
        Returns:
            Path to the downloaded file or None if download failed
        """
        try:
            response = self.make_request(url, stream=True)
            
            if not response:
                return None
                
            if not filename:
                # Try to get filename from Content-Disposition header or URL
                content_disposition = response.headers.get('Content-Disposition')
                if content_disposition and 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"\'')
                else:
                    # Get filename from URL
                    filename = url.split('/')[-1].split('?')[0]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.raw_data_dir / f"{filename}_{timestamp}"
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Downloaded file to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error downloading file from {url}: {str(e)}")
            return None