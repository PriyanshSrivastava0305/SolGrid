"""
Scraper for Solar Energy Corporation of India (SECI) data.
"""
from typing import List, Dict, Any, Optional
import re
import pandas as pd
from bs4 import BeautifulSoup
import logging
import json
import time

from config import DATA_SOURCES
from scrapers.base_scraper import BaseScraper
from utils import clean_text, extract_capacity, extract_year, extract_coordinates, normalize_company_name

class SECIScraper(BaseScraper):
    """Scraper for SECI website data."""
    
    def __init__(self):
        super().__init__("seci")
        self.base_url = DATA_SOURCES["seci"]
        # Define specific SECI pages to scrape
        self.project_listing_urls = [
            f"{self.base_url}solar-tenders",
            f"{self.base_url}commissioned-projects",
            f"{self.base_url}ongoing-projects"
        ]
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape solar project data from SECI website.
        
        Returns:
            List of dictionaries containing solar project data
        """
        self.logger.info("Starting SECI data scraping")
        solar_projects = []
        
        try:
            # Scrape main site for overview data
            main_page_projects = self._scrape_main_page()
            if main_page_projects:
                solar_projects.extend(main_page_projects)
            
            # Scrape each project listing page
            for url in self.project_listing_urls:
                self.logger.info(f"Scraping project listing page: {url}")
                listed_projects = self._scrape_project_listing(url)
                if listed_projects:
                    solar_projects.extend(listed_projects)
            
            # Scrape tender documents for additional project details
            tender_projects = self._scrape_tender_documents()
            if tender_projects:
                solar_projects.extend(tender_projects)
                
            self.logger.info(f"Scraped {len(solar_projects)} solar projects from SECI")
            
        except Exception as e:
            self.logger.error(f"Error scraping SECI website: {str(e)}")
        
        return solar_projects
    
    def _scrape_main_page(self) -> List[Dict[str, Any]]:
        """
        Scrape the SECI main page for overview data.
        
        Returns:
            List of project data dictionaries
        """
        projects = []
        
        try:
            response = self.make_request(self.base_url)
            if not response:
                return projects
                
            # Save the raw HTML
            self.save_raw_data(response.text, "seci_main_page.html")
            
            # Parse the main page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for capacity statistics or dashboard data
            stats_divs = soup.find_all(['div', 'section'], class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['stat', 'dashboard', 'project', 'capacity', 'overview']
            ))
            
            for div in stats_divs:
                # Check for structured data in dashboard format
                capacity_text = div.get_text()
                
                # Extract total installed solar capacity if available
                total_capacity_match = re.search(
                    r'total(?:\s+installed)?\s+(?:solar\s+)?capacity\s*:?\s*(\d+(?:\.\d+)?)\s*(?:GW|MW)',
                    capacity_text, 
                    re.IGNORECASE
                )
                
                if total_capacity_match:
                    capacity_value = float(total_capacity_match.group(1))
                    capacity_unit = total_capacity_match.group(2).upper()
                    
                    # Convert to MW if in GW
                    if capacity_unit == 'GW':
                        capacity_value *= 1000
                    
                    # Create an aggregate project entry
                    projects.append({
                        'name': 'Total SECI Solar Capacity',
                        'capacity_mw': capacity_value,
                        'source': 'SECI',
                        'source_url': self.base_url,
                        'data_type': 'aggregate',
                        'is_aggregate': True
                    })
            
            # Extract project data from any tables on the main page
            tables = soup.find_all('table')
            for table in tables:
                table_projects = self._extract_table_data(table)
                if table_projects:
                    projects.extend(table_projects)
            
        except Exception as e:
            self.logger.error(f"Error scraping SECI main page: {str(e)}")
        
        return projects
    
    def _scrape_project_listing(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape a project listing page from SECI website.
        
        Args:
            url: URL of the project listing page
            
        Returns:
            List of project data dictionaries
        """
        projects = []
        
        try:
            response = self.make_request(url)
            if not response:
                return projects
                
            # Save the raw HTML
            page_name = url.split('/')[-1]
            self.save_raw_data(response.text, f"seci_{page_name}_page.html")
            
            # Parse the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract tables
            tables = soup.find_all('table')
            for table in tables:
                table_projects = self._extract_table_data(table)
                if table_projects:
                    for project in table_projects:
                        project['source_url'] = url
                    projects.extend(table_projects)
            
            # Look for project cards or listings
            project_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                keyword in (x.lower() if x else '') for keyword in ['card', 'project', 'item', 'listing']
            ))
            
            for card in project_cards:
                project = self._extract_project_from_card(card, url)
                if project:
                    projects.append(project)
            
            # Look for links to individual project pages
            project_links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                text = a_tag.text.strip().lower()
                
                # Filter for likely project detail links
                if any(keyword in text for keyword in ['project', 'solar', 'detail', 'view']):
                    # Make URL absolute if it's relative
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            href = f"{self.base_url.rstrip('/')}{href}"
                        else:
                            href = f"{self.base_url.rstrip('/')}/{href}"
                    
                    project_links.append(href)
            
            # Process individual project pages
            for link in project_links[:10]:  # Limit to avoid too many requests
                project = self._scrape_project_detail(link)
                if project:
                    projects.append(project)
            
        except Exception as e:
            self.logger.error(f"Error scraping project listing page {url}: {str(e)}")
        
        return projects
    
    def _extract_table_data(self, table) -> List[Dict[str, Any]]:
        """
        Extract project data from an HTML table.
        
        Args:
            table: BeautifulSoup table element
            
        Returns:
            List of project data dictionaries
        """
        projects = []
        
        try:
            # Extract header row
            headers = []
            header_row = table.find('tr')
            if header_row:
                headers = [th.text.strip().lower() for th in header_row.find_all(['th', 'td'])]
            
            # Check if this table contains project data
            relevant_headers = ['project', 'capacity', 'location', 'developer', 'state']
            if not any(any(relevant in header for relevant in relevant_headers) for header in headers):
                return projects
            
            # Extract data rows
            rows = []
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = [td.text.strip() for td in row.find_all(['td', 'th'])]
                if cells and len(cells) == len(headers):
                    rows.append(cells)
            
            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=headers)
            
            # Map columns to our standard format
            column_mapping = {}
            for col in df.columns:
                col_lower = col.lower()
                if any(name in col_lower for name in ['project', 'name']):
                    column_mapping['name'] = col
                elif any(name in col_lower for name in ['capacity', 'mw']):
                    column_mapping['capacity'] = col
                elif any(name in col_lower for name in ['location', 'site', 'village']):
                    column_mapping['location'] = col
                elif any(name in col_lower for name in ['state', 'province']):
                    column_mapping['state'] = col
                elif any(name in col_lower for name in ['developer', 'company', 'owner', 'bidder']):
                    column_mapping['developer'] = col
                elif any(name in col_lower for name in ['commission', 'cod', 'operation', 'complete']):
                    column_mapping['commissioning'] = col
            
            # Process each row
            for _, row in df.iterrows():
                project = {
                    'source': 'SECI',
                    'data_type': 'tabular'
                }
                
                # Extract mapped columns
                for our_col, df_col in column_mapping.items():
                    value = row[df_col]
                    
                    if our_col == 'capacity':
                        capacity = extract_capacity(str(value))
                        if capacity:
                            project['capacity_mw'] = capacity
                    elif our_col == 'commissioning':
                        year = extract_year(str(value))
                        if year:
                            project['commissioning_year'] = year
                    else:
                        project[our_col] = clean_text(str(value))
                
                # Only add if we have at least capacity information
                if 'capacity_mw' in project:
                    projects.append(project)
            
        except Exception as e:
            self.logger.error(f"Error extracting table data: {str(e)}")
        
        return projects
    
    def _extract_project_from_card(self, card, source_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract project data from a card/list item element.
        
        Args:
            card: BeautifulSoup element for a project card
            source_url: URL of the page containing the card
            
        Returns:
            Dictionary with project data or None if extraction fails
        """
        try:
            # Initialize project data
            project = {
                'source': 'SECI',
                'source_url': source_url,
                'data_type': 'card'
            }
            
            # Get text content
            text = card.get_text()
            
            # Extract project name
            title_elem = card.find(['h2', 'h3', 'h4', 'div', 'p'], class_=lambda x: x and any(
                keyword in (x.lower() if x else '') for keyword in ['title', 'head', 'name']
            ))
            
            if title_elem:
                project['name'] = clean_text(title_elem.text)
            
            # Extract capacity
            capacity = extract_capacity(text)
            if capacity:
                project['capacity_mw'] = capacity
            
            # Extract location
            location_elem = card.find(['div', 'p', 'span'], string=lambda s: s and re.search(r'locat|site|address', s.lower()))
            if location_elem and location_elem.next_sibling:
                project['location'] = clean_text(location_elem.next_sibling.text)
            
            # Extract developer
            developer_elem = card.find(['div', 'p', 'span'], string=lambda s: s and re.search(r'develop|owner|company', s.lower()))
            if developer_elem and developer_elem.next_sibling:
                project['developer'] = clean_text(developer_elem.next_sibling.text)
            
            # Extract commissioning year
            year = extract_year(text)
            if year:
                project['commissioning_year'] = year
            
            # Only return if we have at least capacity information
            if 'capacity_mw' in project:
                return project
                
        except Exception as e:
            self.logger.error(f"Error extracting project from card: {str(e)}")
        
        return None
    
    def _scrape_project_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape an individual project detail page.
        
        Args:
            url: URL of the project detail page
            
        Returns:
            Dictionary with project data or None if extraction fails
        """
        try:
            response = self.make_request(url)
            if not response:
                return None
                
            # Save the raw HTML
            page_name = url.split('/')[-1]
            self.save_raw_data(response.text, f"seci_project_{page_name}.html")
            
            # Parse the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Initialize project data
            project = {
                'source': 'SECI',
                'source_url': url,
                'data_type': 'project_page'
            }
            
            # Extract project name from title
            title_elem = soup.find(['h1', 'h2', 'h3'])
            if title_elem:
                project['name'] = clean_text(title_elem.text)
            
            # Extract data from page content
            content = soup.get_text()
            
            # Extract capacity
            capacity = extract_capacity(content)
            if capacity:
                project['capacity_mw'] = capacity
            
            # Extract coordinates if available
            coords = extract_coordinates(content)
            if coords:
                project['latitude'] = coords['latitude']
                project['longitude'] = coords['longitude']
            
            # Extract commissioning year
            year = extract_year(content)
            if year:
                project['commissioning_year'] = year
            
            # Extract key project details using regex patterns
            info_patterns = {
                'developer': r'(?:developed|owned|operated)(?:\s+by)?\s+([A-Z][^\.,;]{3,50})',
                'location': r'(?:located|situated)(?:\s+in|\s+at)?\s+([^,\.;]+(?:,[^,\.;]+){0,2})',
                'state': r'state\s*:?\s*([A-Za-z\s]+)',
                'offtaker': r'(?:power purchase|PPA|offtake)(?:\s+agreement)?\s+with\s+([A-Z][^\.,;]{3,50})',
                'tariff': r'(?:tariff|rate)\s*:?\s*(?:Rs\.?|₹|INR)?\s*(\d+(?:\.\d+)?)',
                'technology': r'technology\s*:?\s*([A-Za-z\s\-]+)',
            }
            
            for key, pattern in info_patterns.items():
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    project[key] = clean_text(match.group(1))
            
            # Extract project type
            if any(keyword in content.lower() for keyword in ['rooftop', 'roof-top', 'roof top']):
                project['project_type'] = 'Rooftop'
            elif any(keyword in content.lower() for keyword in ['floating', 'water body', 'reservoir']):
                project['project_type'] = 'Floating'
            elif any(keyword in content.lower() for keyword in ['hybrid', 'wind-solar', 'wind solar']):
                project['project_type'] = 'Hybrid'
            else:
                project['project_type'] = 'Utility-Scale'
            
            # Only return if we have at least capacity information
            if 'capacity_mw' in project:
                return project
                
        except Exception as e:
            self.logger.error(f"Error scraping project detail page {url}: {str(e)}")
        
        return None
    
    def _scrape_tender_documents(self) -> List[Dict[str, Any]]:
        """
        Scrape tender documents for project details.
        
        Returns:
            List of project data dictionaries
        """
        projects = []
        tender_url = f"{self.base_url}tenders"
        
        try:
            response = self.make_request(tender_url)
            if not response:
                return projects
                
            # Save the raw HTML
            self.save_raw_data(response.text, "seci_tenders_page.html")
            
            # Parse the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find links to tender documents
            tender_links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                text = a_tag.text.strip().lower()
                
                # Filter for PDF links with relevant keywords
                if href.endswith('.pdf') and any(keyword in text for keyword in ['tender', 'document', 'rfp', 'solar']):
                    # Make URL absolute if it's relative
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            href = f"{self.base_url.rstrip('/')}{href}"
                        else:
                            href = f"{self.base_url.rstrip('/')}/{href}"
                    
                    tender_links.append((href, text))
            
            # Download and process a limited number of tender documents
            # In a full implementation, you would use PDF parsing libraries
            for href, text in tender_links[:5]:  # Limit to avoid too many downloads
                self.logger.info(f"Found tender document: {text} at {href}")
                
                # In a full implementation, download and parse the PDF
                # For now, create a placeholder entry with metadata
                if 'mw' in text.lower() or 'solar' in text.lower():
                    capacity = extract_capacity(text)
                    if capacity:
                        projects.append({
                            'name': clean_text(text),
                            'capacity_mw': capacity,
                            'source': 'SECI',
                            'source_url': href,
                            'data_type': 'tender_document',
                            'document_type': 'Tender'
                        })
            
        except Exception as e:
            self.logger.error(f"Error scraping tender documents: {str(e)}")
        
        return projects