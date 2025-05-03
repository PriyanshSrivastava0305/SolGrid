"""
Utility functions for the Solar Detective project.
"""
import os
import logging
import re
import pandas as pd
import requests
from datetime import datetime
from typing import Dict, List, Union, Optional, Any, Tuple
from pathlib import Path

from config import LOG_LEVEL, LOG_FILE

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)

def download_file(url: str, local_path: str, overwrite: bool = False) -> str:
    """
    Download a file from URL to local path.
    
    Args:
        url: URL to download from
        local_path: Local path to save the file
        overwrite: Whether to overwrite if file exists
        
    Returns:
        Path to the downloaded file
    """
    if os.path.exists(local_path) and not overwrite:
        logger.info(f"File already exists at {local_path}")
        return local_path
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    try:
        logger.info(f"Downloading {url} to {local_path}")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Download complete: {local_path}")
        return local_path
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        if os.path.exists(local_path):
            os.remove(local_path)
        raise

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a filename.
    
    Args:
        filename: Original filename string
        
    Returns:
        Sanitized filename
    """
    # Replace invalid characters with underscore
    s = re.sub(r'[\\/*?:"<>|]', '_', filename)
    # Remove extra whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def extract_coordinates(location_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract latitude and longitude from a location string.
    Supports various formats like "28.6139° N, 77.2090° E" or "28.6139, 77.2090".
    
    Args:
        location_str: String containing location information
        
    Returns:
        Tuple of (latitude, longitude) or (None, None) if extraction fails
    """
    if not location_str or not isinstance(location_str, str):
        return None, None
    
    # Try to match decimal degree format with direction (e.g., "28.6139° N, 77.2090° E")
    pattern1 = r'(\d+\.?\d*)\s*°?\s*([NS])[,\s]*(\d+\.?\d*)\s*°?\s*([EW])'
    match = re.search(pattern1, location_str, re.IGNORECASE)
    if match:
        lat = float(match.group(1))
        if match.group(2).upper() == 'S':
            lat = -lat
        
        lon = float(match.group(3))
        if match.group(4).upper() == 'W':
            lon = -lon
        
        return lat, lon
    
    # Try to match decimal coordinates (e.g., "28.6139, 77.2090")
    pattern2 = r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)'
    match = re.search(pattern2, location_str)
    if match:
        return float(match.group(1)), float(match.group(2))
    
    return None, None

def parse_capacity(capacity_str: str) -> Optional[float]:
    """
    Parse capacity string to float in MW.
    Handles formats like "500 MW", "1.5 GW", etc.
    
    Args:
        capacity_str: String containing capacity information
        
    Returns:
        Capacity in MW as float, or None if parsing fails
    """
    if not capacity_str or not isinstance(capacity_str, str):
        return None
    
    # Remove commas and convert to lowercase
    capacity_str = capacity_str.replace(',', '').lower()
    
    # Extract numeric value and unit
    match = re.search(r'(\d+\.?\d*)\s*([a-z]*)', capacity_str)
    if not match:
        try:
            # Try direct conversion if no unit
            return float(capacity_str)
        except ValueError:
            return None
    
    value = float(match.group(1))
    unit = match.group(2)
    
    # Convert to MW
    if 'gw' in unit:
        return value * 1000
    elif 'kw' in unit:
        return value / 1000
    elif 'mw' in unit:
        return value
    else:
        # Assume MW if no unit provided
        return value

def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string to datetime object.
    Handles various date formats.
    
    Args:
        date_str: String containing date information
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    date_formats = [
        '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y',
        '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y',
        '%d %b %Y', '%d %B %Y',
        '%b %d, %Y', '%B %d, %Y',
        '%d.%m.%Y', '%m.%d.%Y', '%Y.%m.%d'
    ]
    
    for date_format in date_formats:
        try:
            return datetime.strptime(date_str.strip(), date_format)
        except ValueError:
            continue
    
    return None

def extract_year(text: Union[str, datetime, int]) -> Optional[int]:
    """
    Extract year from various input formats.
    
    Args:
        text: Input containing year information (string, datetime, or int)
        
    Returns:
        Year as integer or None if extraction fails
    """
    if isinstance(text, datetime):
        return text.year
    
    if isinstance(text, int):
        # Assume it's already a year if it's in a reasonable range
        if 1990 <= text <= 2100:
            return text
        return None
    
    if isinstance(text, str):
        # Try to extract year from string
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            return int(year_match.group(0))
        
        # Try to parse as date and extract year
        parsed_date = parse_date(text)
        if parsed_date:
            return parsed_date.year
    
    return None

def is_valid_project_data(project_data: Dict[str, Any]) -> bool:
    """
    Validate if the project data has the minimum required fields.
    
    Args:
        project_data: Dictionary containing project data
        
    Returns:
        True if data is valid, False otherwise
    """
    required_fields = ['name', 'capacity']
    return all(field in project_data and project_data[field] for field in required_fields)

def save_to_csv(data: List[Dict[str, Any]], file_path: str) -> None:
    """
    Save data to CSV file.
    
    Args:
        data: List of dictionaries containing data
        file_path: Path to save the CSV file
    """
    if not data:
        logger.warning(f"No data to save to {file_path}")
        return
    
    try:
        df = pd.DataFrame(data)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df.to_csv(file_path, index=False)
        logger.info(f"Data saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving data to {file_path}: {str(e)}")
        raise

def load_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Load data from CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of dictionaries containing data
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return []
    
    try:
        df = pd.read_csv(file_path)
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {str(e)}")
        return []

def generate_unique_id(project_data: Dict[str, Any]) -> str:
    """
    Generate a unique ID for a project based on its attributes.
    
    Args:
        project_data: Dictionary containing project data
        
    Returns:
        Unique ID string
    """
    # Use combination of name, capacity, and location if available
    components = []
    
    if 'name' in project_data and project_data['name']:
        components.append(str(project_data['name']).lower().replace(' ', '_'))
    
    if 'capacity' in project_data and project_data['capacity']:
        components.append(f"{project_data['capacity']}mw")
    
    if 'latitude' in project_data and 'longitude' in project_data:
        if project_data['latitude'] and project_data['longitude']:
            # Round coordinates to 3 decimal places for ID generation
            lat = round(float(project_data['latitude']), 3)
            lon = round(float(project_data['longitude']), 3)
            components.append(f"{lat}_{lon}")
    elif 'location' in project_data and project_data['location']:
        # Use first 10 chars of sanitized location if full coordinates aren't available
        loc = sanitize_filename(project_data['location'])
        components.append(loc[:10].lower().replace(' ', '_'))
    
    if not components:
        # Fallback to timestamp if no identifying information
        components.append(f"unknown_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    
    return "_".join(components)