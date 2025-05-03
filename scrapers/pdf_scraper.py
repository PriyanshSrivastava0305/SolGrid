"""
PDF Scraper module to extract structured data from company reports, 
investor presentations, and other PDF documents.
"""

import os
import re
import pandas as pd
import pdfplumber
import logging
from pathlib import Path
from datetime import datetime

from scrapers.base_scraper import BaseScraper
from utils import setup_logger, clean_text
from config import DATA_SOURCES

class PDFScraper(BaseScraper):
    def __init__(self):
        super().__init__("pdf")
        self.pdf_dir = os.path.join("data", "pdfs")
        self.output_dir = os.path.join("data", "raw", "pdf_extracted")
        os.makedirs(self.output_dir, exist_ok=True)
        self.logger = setup_logger("pdf_scraper")
        
        # Regex patterns for identifying solar project information
        self.patterns = {
            'capacity': r'(\d+(?:\.\d+)?)\s*(?:MW|mw|megawatt)',
            'location': r'(?:located\s+in|at|in)\s+([A-Za-z\s,]+(?:district|village|tehsil|city))',
            'commissioning_date': r'(?:commissioned|operational|COD|completed)(?:\s+on|\s+in|\s+by)?\s+(\w+\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4})',
            'technology': r'(?:using|with|based on)\s+([A-Za-z\-]+\s+(?:technology|module|cell|panel))',
            'developer': r'(?:developed by|developer|owned by|promoter)\s+([A-Za-z\s]+)(?:Ltd\.?|Limited|Pvt\.?|Corporation|Corp\.?|Inc\.?)?',
        }
    
    def _standardize_date(self, date_str):
        """Standardize date format"""
        if not date_str:
            return None
            
        date_formats = [
            '%B %Y',           # January 2024
            '%d-%m-%Y',        # 31-12-2024
            '%d/%m/%Y',        # 31/12/2024
            '%Y-%m-%d',        # 2024-12-31
            '%d.%m.%Y',        # 31.12.2024
            '%Y'               # 2024
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None

    def scrape(self):
        """Process all PDF files in the configured directory"""
        self.logger.info("Starting PDF scraping process")
        
        all_projects = []
        pdf_files = list(Path(self.pdf_dir).glob('**/*.pdf'))
        
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {self.pdf_dir}")
            return pd.DataFrame()
        
        for pdf_path in pdf_files:
            self.logger.info(f"Processing PDF: {pdf_path}")
            company_name = self._extract_company_name(pdf_path)
            projects = self._extract_projects_from_pdf(pdf_path, company_name)
            all_projects.extend(projects)
            
        # Convert to DataFrame and save
        if all_projects:
            projects_df = pd.DataFrame(all_projects)
            output_file = os.path.join(self.output_dir, 'extracted_solar_projects.csv')
            projects_df.to_csv(output_file, index=False)
            self.logger.info(f"Saved {len(projects_df)} projects to {output_file}")
            return projects_df
        else:
            self.logger.warning("No projects extracted from PDFs")
            return pd.DataFrame()

    def _extract_company_name(self, pdf_path):
        """Extract company name from filename or path"""
        filename = os.path.basename(pdf_path)
        
        # Common solar companies in India
        companies = ['Adani', 'ReNew', 'Tata Power', 'Azure', 'ACME', 'Hero', 
                    'Greenko', 'SB Energy', 'NTPC', 'Waaree', 'Sterling & Wilson']
        
        for company in companies:
            if company.lower() in filename.lower():
                return company
                
        # Default to filename without extension
        return os.path.splitext(filename)[0]

    def _extract_projects_from_pdf(self, pdf_path, company_name):
        """Extract solar project information from PDF"""
        projects = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                # Extract text from each page
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                
                # Look for project sections or tables
                project_sections = self._identify_project_sections(text)
                
                if project_sections:
                    # Process identified sections
                    for section in project_sections:
                        project = self._extract_project_details(section, company_name)
                        if project:
                            projects.append(project)
                else:
                    # If no clear sections, try to extract from tables
                    projects.extend(self._extract_from_tables(pdf, company_name))
                    
                    # If still no projects, try extraction from whole text
                    if not projects:
                        project = self._extract_project_details(text, company_name)
                        if project:
                            projects.append(project)
        
        except Exception as e:
            self.logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
        
        return projects

    def _identify_project_sections(self, text):
        """Identify sections in the text that likely contain project information"""
        # This is a simplified approach - real implementation would be more robust
        sections = []
        
        # Split by common section headers
        potential_headers = [
            "Project Details", "Our Projects", "Solar Assets", 
            "Operational Assets", "Project Portfolio", "Commissioned Projects"
        ]
        
        current_text = text
        for header in potential_headers:
            if header in current_text:
                parts = current_text.split(header)
                if len(parts) > 1:
                    # Take the content after the header
                    section_text = parts[1]
                    # Limit to a reasonable chunk (3000 chars) to avoid grabbing too much
                    sections.append(section_text[:3000])
        
        # If no sections found using headers, try paragraph-based approach
        if not sections:
            paragraphs = text.split('\n\n')
            for para in paragraphs:
                # Look for paragraphs that likely describe projects
                if re.search(self.patterns['capacity'], para) and len(para) > 100:
                    sections.append(para)
        
        return sections

    def _extract_project_details(self, text, company_name):
        """Extract project details using regex patterns"""
        project = {
            'developer': company_name,
            'source_type': 'pdf',
            'extraction_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Apply each pattern
        for field, pattern in self.patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                project[field] = clean_text(match.group(1))
        
        # Only return if we have at least capacity and one other field
        if 'capacity' in project and len(project) > 3:
            # Post-process some fields
            if 'capacity' in project:
                # Extract just the number
                capacity_str = project['capacity']
                capacity_num = re.search(r'\d+(?:\.\d+)?', capacity_str)
                if capacity_num:
                    project['capacity_mw'] = float(capacity_num.group(0))
            
            if 'commissioning_date' in project:
                project['commissioning_date'] = self._standardize_date(project['commissioning_date'])
                
            return project
        
        return None

    def _extract_from_tables(self, pdf, company_name):
        """Extract project information from tables in the PDF"""
        projects = []
        
        try:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) <= 1:  # Skip empty tables or just headers
                        continue
                    
                    # Try to identify if this is a project table
                    headers = [str(h).lower() if h else "" for h in table[0]]
                    
                    # Check if table likely contains project information
                    relevant_keywords = ['project', 'capacity', 'location', 'mw', 'date', 'status']
                    if any(keyword in ' '.join(headers) for keyword in relevant_keywords):
                        # Process rows
                        for row in table[1:]:  # Skip header row
                            project = self._extract_project_from_row(row, headers, company_name)
                            if project:
                                projects.append(project)
        
        except Exception as e:
            self.logger.error(f"Error extracting tables: {str(e)}")
        
        return projects

    def _extract_project_from_row(self, row, headers, company_name):
        """Extract project details from a table row"""
        if not row or all(cell is None or cell.strip() == '' for cell in row):
            return None
            
        project = {
            'developer': company_name,
            'source_type': 'pdf_table',
            'extraction_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Map headers to fields
        header_mapping = {
            'project': 'project_name',
            'name': 'project_name',
            'capacity': 'capacity',
            'size': 'capacity',
            'mw': 'capacity',
            'location': 'location',
            'state': 'state',
            'district': 'district',
            'date': 'commissioning_date',
            'commissioning': 'commissioning_date',
            'cod': 'commissioning_date',
            'technology': 'technology',
            'type': 'project_type',
            'status': 'status'
        }
        
        # Process each cell based on header
        for i, header in enumerate(headers):
            if i < len(row) and row[i]:
                header = header.lower().strip()
                for key, field in header_mapping.items():
                    if key in header and row[i]:
                        value = clean_text(str(row[i]))
                        
                        # Special handling for capacity
                        if field == 'capacity' and value:
                            # Extract the numeric part
                            capacity_match = re.search(r'\d+(?:\.\d+)?', value)
                            if capacity_match:
                                project['capacity_mw'] = float(capacity_match.group(0))
                            project[field] = value
                        # Special handling for dates
                        elif field == 'commissioning_date':
                            project[field] = self._standardize_date(value)
                        else:
                            project[field] = value
        
        # Only return if we have meaningful data
        return project if 'capacity_mw' in project or 'project_name' in project else None