"""
Scraper for POSOCO/Grid India data.
Extracts real-time dispatch and grid infrastructure data.
"""

import os
import pandas as pd
import requests
from datetime import datetime
import logging
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils import setup_logger, clean_text
from config import DATA_SOURCES

class POSCOScraper(BaseScraper):
    def __init__(self):
        super().__init__("posoco")
        self.base_url = DATA_SOURCES["posoco"]
        self.reports_url = f"{self.base_url}/reports/daily-reports"
        self.data_dir = os.path.join("data", "raw", "posoco")
        os.makedirs(self.data_dir, exist_ok=True)
        self.logger = setup_logger("posoco_scraper")

    def scrape(self):
        """Main scraping method for POSOCO/Grid India data"""
        self.logger.info("Starting POSOCO data scraping")
        
        # Scrape various data types
        self._scrape_renewable_reports()
        self._scrape_grid_connectivity()
        self._scrape_dispatch_data()
        
        self.logger.info("POSOCO data scraping completed")
        return True

    def _scrape_renewable_reports(self):
        """Scrape renewable energy integration reports"""
        try:
            self.logger.info("Scraping renewable reports")
            
            # Get the reports page
            response = requests.get(self.reports_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all report links (typically PDFs)
            reports = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'solar' in href.lower() or 'renewable' in href.lower():
                    if href.endswith('.pdf'):
                        title = clean_text(link.text.strip())
                        date = self._extract_date_from_text(link.text)
                        
                        reports.append({
                            'title': title,
                            'url': href if href.startswith('http') else f"{self.base_url}/{href.lstrip('/')}",
                            'date': date
                        })
            
            # Save reports metadata
            reports_df = pd.DataFrame(reports)
            reports_df.to_csv(os.path.join(self.data_dir, 'renewable_reports.csv'), index=False)
            
            # Download the most recent reports (limited to 5 to avoid overloading)
            reports_df = reports_df.sort_values('date', ascending=False).head(5)
            for _, row in reports_df.iterrows():
                self._download_pdf(row['url'], os.path.join(self.data_dir, f"{row['date']}_{row['title']}.pdf"))
                
            return reports_df
        except Exception as e:
            self.logger.error(f"Error scraping renewable reports: {str(e)}")
            return pd.DataFrame()

    def _scrape_grid_connectivity(self):
        """Scrape solar grid connectivity information"""
        try:
            self.logger.info("Scraping grid connectivity data")
            
            # This would normally use a specific endpoint for grid connectivity
            # For this prototype, we'll create a simulated dataset
            
            # In a real implementation, you'd scrape structured data from their website
            # For example:
            # response = requests.get(f"{self.base_url}/grid-connectivity")
            # soup = BeautifulSoup(response.content, 'html.parser')
            # tables = soup.find_all('table')
            # Parse table data...
            
            # Creating sample data for demonstration
            grid_data = [
                {
                    'region': 'Northern', 
                    'state': 'Rajasthan',
                    'substation': 'Bhadla',
                    'voltage_level': '400kV',
                    'connected_solar_capacity': 2245,
                    'max_capacity': 3000,
                    'last_updated': '2023-09-15'
                },
                {
                    'region': 'Western',
                    'state': 'Gujarat',
                    'substation': 'Charanka',
                    'voltage_level': '220kV',
                    'connected_solar_capacity': 850,
                    'max_capacity': 1000,
                    'last_updated': '2023-10-01'
                },
                # Additional sample entries would be here
            ]
            
            grid_df = pd.DataFrame(grid_data)
            grid_df.to_csv(os.path.join(self.data_dir, 'grid_connectivity.csv'), index=False)
            return grid_df
        except Exception as e:
            self.logger.error(f"Error scraping grid connectivity: {str(e)}")
            return pd.DataFrame()

    def _scrape_dispatch_data(self):
        """Scrape solar power generation/dispatch data"""
        try:
            self.logger.info("Scraping dispatch data")
            
            # This would normally fetch real-time or historical generation data
            # For this prototype, we'll create a simulated dataset
            
            # Create a sample file with generation data
            current_date = datetime.now().strftime('%Y-%m-%d')
            dispatch_data = {
                'date': [current_date] * 5,
                'state': ['Rajasthan', 'Gujarat', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh'],
                'installed_capacity_mw': [13300, 8800, 5500, 7400, 4900],
                'peak_generation_mw': [10500, 6900, 4200, 5800, 3700],
                'energy_generated_mwh': [85000, 55000, 32000, 45000, 29000],
                'grid_availability_percent': [98.5, 99.2, 97.8, 98.9, 96.5]
            }
            
            dispatch_df = pd.DataFrame(dispatch_data)
            dispatch_df.to_csv(os.path.join(self.data_dir, f'dispatch_data_{current_date}.csv'), index=False)
            return dispatch_df
        except Exception as e:
            self.logger.error(f"Error scraping dispatch data: {str(e)}")
            return pd.DataFrame()

    def _extract_date_from_text(self, text):
        """Extract date from text if available, otherwise return current date"""
        # Simple date extraction - in real implementation, use regex patterns
        # for various date formats found in POSOCO documents
        date_formats = ['%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y-%m-%d']
        
        # Placeholder implementation
        for fmt in date_formats:
            try:
                # This is simplified - in real code, you'd identify date patterns first
                return datetime.now().strftime('%Y-%m-%d')
            except:
                pass
        
        return datetime.now().strftime('%Y-%m-%d')

    def _download_pdf(self, url, save_path):
        """Download PDF file from URL"""
        try:
            response = requests.get(url, stream=True)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            self.logger.info(f"Downloaded PDF: {save_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error downloading PDF {url}: {str(e)}")
            return False