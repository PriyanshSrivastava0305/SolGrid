"""
Scraper for Ministry of New and Renewable Energy (MNRE) data.
"""
from typing import List, Dict, Any, Optional
import re
import pandas as pd
from bs4 import BeautifulSoup
import logging
import json
import time
from urllib.parse import urljoin

from config import DATA_SOURCES
from scrapers.base_scraper import BaseScraper
from utils import clean_text, extract_capacity, extract_year, extract_coordinates

class MNREScraper(BaseScraper):
    """Scraper for MNRE website data."""
    
    def __init__(self):
        super().__init__("mnre")
        self.base_urls = [
            'https://mnre.gov.in/solar/',
            'https://mnre.gov.in/solar/current-status/',
            'https://mnre.gov.in/solar-energy/overview/',
            'https://mnre.gov.in/solar/schemes/'
        ]
        self.search_paths = [
            'solar-energy',
            'solar-power',
            'grid-connected',
            'solar-rpg',
            'schemes-and-programs'
        ]
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape solar project data from MNRE website.
        
        Returns:
            List of dictionaries containing solar project data
        """
        self.logger.info("Starting MNRE data scraping")
        solar_projects = []
        
        # Try each base URL
        for base_url in self.base_urls:
            try:
                self.logger.info(f"Trying URL: {base_url}")
                response = self.make_request(base_url)
                if response and response.status_code == 200:
                    # Save the raw HTML
                    page_name = base_url.rstrip('/').split('/')[-1]
                    self.save_raw_data(response.text, f"mnre_{page_name}_page.html")
                    
                    # Parse the main page
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract any tables from the current page
                    page_projects = self._extract_tables_from_soup(soup)
                    if page_projects:
                        for project in page_projects:
                            project['source_url'] = base_url
                        solar_projects.extend(page_projects)
                    
                    # Look for links to other relevant pages
                    data_links = self._find_data_links(soup, base_url)
                    
                    # Process each data link
                    for link_info in data_links:
                        projects = self._process_link(link_info)
                        if projects:
                            solar_projects.extend(projects)
                            
                    # If we found meaningful data, no need to try other base URLs
                    if solar_projects:
                        break
            except Exception as e:
                self.logger.error(f"Error processing {base_url}: {str(e)}")
                continue
        
        # Try searching through common paths if we haven't found data yet
        if not solar_projects:
            for base_url in self.base_urls:
                for path in self.search_paths:
                    try:
                        url = urljoin(base_url, path)
                        self.logger.info(f"Searching path: {url}")
                        response = self.make_request(url)
                        if response and response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            page_projects = self._extract_tables_from_soup(soup)
                            if page_projects:
                                for project in page_projects:
                                    project['source_url'] = url
                                solar_projects.extend(page_projects)
                    except Exception as e:
                        self.logger.error(f"Error searching path {url}: {str(e)}")
                        continue
        
        self.logger.info(f"Scraped {len(solar_projects)} solar projects from MNRE")
        return solar_projects

    def _find_data_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Find links to data sources on the MNRE website."""
        links = []
        
        # Look for links to reports, data tables, or project pages
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = clean_text(a_tag.text)
            
            # Skip empty or javascript links
            if not href or href.startswith(('javascript:', '#')):
                continue
                
            # Make URL absolute
            if not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)
            
            # Skip external links
            if not any(url in href for url in ['mnre.gov.in', 'solarrooftop.gov.in']):
                continue
            
            # Categorize link based on content and patterns
            link_info = {'url': href, 'text': text}
            
            # Check for report links (PDFs, Excel files)
            if re.search(r'\.(pdf|xlsx?|csv|json)$', href, re.IGNORECASE):
                keywords = ['solar', 'project', 'report', 'data', 'renewable']
                if any(keyword in text.lower() for keyword in keywords):
                    link_info['type'] = 'report'
                    links.append(link_info)
            
            # Check for data table pages
            elif any(keyword in text.lower() for keyword in ['table', 'data', 'statistics', 'status']):
                if 'solar' in text.lower():
                    link_info['type'] = 'data_table'
                    links.append(link_info)
            
            # Check for project detail pages
            elif any(keyword in text.lower() for keyword in ['project', 'plant', 'installation']):
                if 'solar' in text.lower():
                    link_info['type'] = 'project_page'
                    links.append(link_info)
                    
        return links

    def _process_link(self, link_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a single data link based on its type."""
        url = link_info['url']
        link_type = link_info['type']
        projects = []
        
        try:
            if link_type == 'report':
                # Download and process report file
                file_path = self.download_file(url)
                if file_path and file_path.suffix.lower() in ['.pdf', '.xlsx', '.xls']:
                    projects = self._extract_data_from_file(file_path)
                    
            elif link_type == 'data_table':
                # Extract data from HTML tables
                projects = self._extract_table_data(url)
                
            elif link_type == 'project_page':
                # Extract project details
                project = self._extract_project_data(url)
                if project:
                    projects.append(project)
                    
            # Add source URL to all projects
            for project in projects:
                project['source_url'] = url
                
        except Exception as e:
            self.logger.error(f"Error processing link {url}: {str(e)}")
            
        return projects

    def _extract_data_from_file(self, file_path) -> List[Dict[str, Any]]:
        """
        Extract data from downloaded files (PDF, Excel, etc.).
        
        Args:
            file_path: Path to the downloaded file
            
        Returns:
            List of project data dictionaries
        """
        self.logger.info(f"Extracting data from file: {file_path}")
        
        projects = []
        
        # Process based on file extension
        suffix = file_path.suffix.lower()
        
        if suffix in ['.xlsx', '.xls']:
            # Process Excel files
            try:
                df = pd.read_excel(file_path)
                
                # Save raw DataFrame to CSV for debugging
                csv_path = file_path.with_suffix('.csv')
                df.to_csv(csv_path, index=False)
                
                # Process the DataFrame to extract project data
                projects = self._process_dataframe(df)
                
            except Exception as e:
                self.logger.error(f"Error processing Excel file {file_path}: {str(e)}")
        
        elif suffix == '.pdf':
            # Process PDF files
            # Note: This would require PDF extraction libraries
            self.logger.info(f"PDF processing for {file_path} not implemented yet")
            # For actual implementation, use libraries like PyPDF2, pdfplumber, or tabula-py
        
        return projects
    
    def _process_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Process a DataFrame to extract project data.
        
        Args:
            df: Pandas DataFrame containing project data
            
        Returns:
            List of project data dictionaries
        """
        projects = []
        
        # Normalize column names to make them case-insensitive
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Check if the DataFrame contains relevant columns
        relevant_cols = {
            'name': ['name', 'project name', 'project', 'plant name'],
            'capacity': ['capacity', 'capacity (mw)', 'installed capacity', 'mw'],
            'location': ['location', 'site', 'address', 'place'],
            'state': ['state', 'province'],
            'developer': ['developer', 'company', 'owner', 'operator'],
            'commissioning_year': ['commissioning year', 'year', 'date', 'commissioned']
        }
        
        # Map DataFrame columns to our standardized column names
        column_mapping = {}
        for our_col, possible_cols in relevant_cols.items():
            for col in df.columns:
                if any(possible.lower() in col.lower() for possible in possible_cols):
                    column_mapping[our_col] = col
                    break
        
        # Skip if we don't have essential columns
        if 'capacity' not in column_mapping:
            self.logger.warning("DataFrame doesn't contain capacity information")
            return projects
            
        # Process each row
        for _, row in df.iterrows():
            project = {
                'source': 'MNRE',
                'source_url': self.base_url,
                'data_type': 'tabular'
            }
            
            # Extract data using our column mapping
            for our_col, df_col in column_mapping.items():
                value = row[df_col]
                
                # Skip empty/NaN values
                if pd.isna(value):
                    continue
                    
                # Process based on column type
                if our_col == 'capacity':
                    if isinstance(value, (int, float)):
                        project['capacity_mw'] = float(value)
                    else:
                        extracted = extract_capacity(str(value))
                        if extracted:
                            project['capacity_mw'] = extracted
                
                elif our_col == 'commissioning_year':
                    if isinstance(value, (int, float)) and 2000 <= value <= 2030:
                        project['commissioning_year'] = int(value)
                    else:
                        extracted = extract_year(str(value))
                        if extracted:
                            project['commissioning_year'] = extracted
                
                elif our_col == 'location':
                    project['location'] = clean_text(str(value))
                    # Try to extract coordinates from location
                    coords = extract_coordinates(str(value))
                    if coords:
                        project['latitude'] = coords['latitude']
                        project['longitude'] = coords['longitude']
                
                else:
                    # For other columns, just use the value as is
                    project[our_col] = clean_text(str(value)) if isinstance(value, str) else value
            
            # Only add projects with at least capacity information
            if 'capacity_mw' in project:
                projects.append(project)
        
        return projects
    
    def _extract_table_data(self, url: str) -> List[Dict[str, Any]]:
        """
        Extract data from HTML tables on a page.
        
        Args:
            url: URL of the page containing tables
            
        Returns:
            List of project data dictionaries
        """
        self.logger.info(f"Extracting table data from: {url}")
        projects = []
        
        try:
            response = self.make_request(url)
            if not response:
                return projects
                
            # Save the raw HTML
            self.save_raw_data(response.text, f"mnre_table_page_{url.split('/')[-1]}.html")
            
            # Parse tables from the page
            soup = BeautifulSoup(response.text, 'html.parser')
            projects = self._extract_tables_from_soup(soup)
            
        except Exception as e:
            self.logger.error(f"Error extracting table data from {url}: {str(e)}")
        
        return projects
    
    def _extract_tables_from_soup(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract data from HTML tables in a BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of project data dictionaries
        """
        projects = []
        
        # Find all tables
        tables = soup.find_all('table')
        
        for table_idx, table in enumerate(tables):
            # Check if table contains relevant data
            headers = [th.text.strip().lower() for th in table.find_all('th')]
            
            # Skip tables without relevant headers
            if not headers or not any(keyword in ' '.join(headers) for keyword in ['solar', 'project', 'capacity']):
                continue
                
            # Extract data from the table
            rows = []
            for tr in table.find_all('tr'):
                cells = tr.find_all(['td', 'th'])
                if cells:
                    row = [cell.text.strip() for cell in cells]
                    rows.append(row)
            
            if not rows:
                continue
                
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(rows[1:], columns=rows[0])
            
            # Process the DataFrame
            table_projects = self._process_dataframe(df)
            projects.extend(table_projects)
        
        return projects
    
    def _extract_project_data(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract data from a project detail page.
        
        Args:
            url: URL of the project detail page
            
        Returns:
            Dictionary containing project data or None if extraction fails
        """
        self.logger.info(f"Extracting project data from: {url}")
        
        try:
            response = self.make_request(url)
            if not response:
                return None
                
            # Save the raw HTML
            self.save_raw_data(response.text, f"mnre_project_page_{url.split('/')[-1]}.html")
            
            # Parse the project page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract project data
            project_data = {
                'source': 'MNRE',
                'source_url': url,
                'data_type': 'project_page'
            }
            
            # Extract project name
            title_tag = soup.find(['h1', 'h2', 'h3', 'h4', 'h5'])
            if title_tag:
                project_data['name'] = clean_text(title_tag.text)
            
            # Extract project details from text content
            page_text = soup.get_text()
            
            # Extract capacity
            capacity = extract_capacity(page_text)
            if capacity:
                project_data['capacity_mw'] = capacity
                
            # Extract commissioning year
            year = extract_year(page_text)
            if year:
                project_data['commissioning_year'] = year
                
            # Extract coordinates if available
            coords = extract_coordinates(page_text)
            if coords:
                project_data['latitude'] = coords['latitude']
                project_data['longitude'] = coords['longitude']
            
            # Extract location/address information
            location_patterns = [
                r'(?:located|situated|based|installed)(?:\s+in|\s+at)?\s+([^,\.;]+(?:,[^,\.;]+){0,2})',
                r'location\s*:?\s*([^,\.;]+(?:,[^,\.;]+){0,2})',
                r'address\s*:?\s*([^,\.;]+(?:,[^,\.;]+){0,2})'
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    project_data['location'] = clean_text(match.group(1))
                    break
            
            # Extract developer/owner information
            developer_patterns = [
                r'(?:developed|owned|operated)(?:\s+by)?\s+([A-Z][^\.,;]{3,50})',
                r'developer\s*:?\s*([A-Z][^\.,;]{3,50})',
                r'owner\s*:?\s*([A-Z][^\.,;]{3,50})',
                r'company\s*:?\s*([A-Z][^\.,;]{3,50})'
            ]
            
            for pattern in developer_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    project_data['developer'] = clean_text(match.group(1))
                    break
            
            # Extract technology information
            if 'monocrystalline' in page_text.lower():
                project_data['technology'] = 'Monocrystalline Silicon'
            elif 'polycrystalline' in page_text.lower():
                project_data['technology'] = 'Polycrystalline Silicon'
            elif 'thin film' in page_text.lower():
                project_data['technology'] = 'Thin Film'
            elif 'cadmium telluride' in page_text.lower() or 'cdte' in page_text.lower():
                project_data['technology'] = 'CdTe'
            
            # Extract project type
            if any(keyword in page_text.lower() for keyword in ['rooftop', 'roof-top', 'roof top']):
                project_data['project_type'] = 'Rooftop'
            elif any(keyword in page_text.lower() for keyword in ['floating', 'water body', 'reservoir']):
                project_data['project_type'] = 'Floating'
            elif any(keyword in page_text.lower() for keyword in ['hybrid', 'wind-solar', 'wind solar']):
                project_data['project_type'] = 'Hybrid'
            else:
                project_data['project_type'] = 'Utility-Scale'
            
            # Only return if we have at least the capacity
            if 'capacity_mw' in project_data:
                return project_data
            
        except Exception as e:
            self.logger.error(f"Error extracting project data from {url}: {str(e)}")
        
        return None