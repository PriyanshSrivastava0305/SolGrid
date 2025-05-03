import logging
import requests
from typing import Optional, Dict
import time
from pathlib import Path

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger with the given name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def safe_request(
    url: str, 
    method: str = 'get', 
    max_retries: int = 3, 
    retry_delay: int = 5,
    timeout: int = 30,
    session: Optional[requests.Session] = None, 
    **kwargs
) -> Optional[requests.Response]:
    """
    Make a safe HTTP request with retries, timeouts, and error handling.
    
    Args:
        url: URL to request
        method: HTTP method ('get', 'post', etc.)
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        timeout: Request timeout in seconds
        session: Optional requests.Session to use
        **kwargs: Additional arguments to pass to the request
        
    Returns:
        Response object if successful, None otherwise
    """
    if 'timeout' not in kwargs:
        kwargs['timeout'] = timeout
        
    # Exponential backoff for retries
    for attempt in range(max_retries):
        try:
            if session:
                response = getattr(session, method.lower())(url, **kwargs)
            else:
                response = getattr(requests, method.lower())(url, **kwargs)
                
            # Check if we got a valid response
            response.raise_for_status()
            
            # Check for common anti-scraping redirects
            final_url = response.url.lower()
            if any(x in final_url for x in ['robot', 'captcha', 'security', 'cloudflare']):
                raise requests.exceptions.RequestException("Detected anti-scraping measure")
                
            return response
            
        except requests.exceptions.Timeout:
            logging.warning(f"Request to {url} timed out (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                
        except requests.exceptions.ConnectionError:
            logging.warning(f"Connection error for {url} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                
        except requests.exceptions.HTTPError as e:
            # Don't retry on 404s
            if e.response.status_code == 404:
                logging.error(f"Resource not found at {url}")
                return None
            logging.warning(f"HTTP error {e.response.status_code} for {url} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                
        except Exception as e:
            logging.error(f"Failed to {method} {url}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                
    return None

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    # Remove extra whitespace and normalize
    text = " ".join(text.split())
    return text.strip()

def extract_capacity(text: str) -> Optional[float]:
    """Extract capacity in MW from text."""
    import re
    
    # Common patterns for capacity
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:MW|megawatt)',
        r'capacity\s*:?\s*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*MW'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None

def extract_year(text: str) -> Optional[int]:
    """Extract year from text."""
    import re
    
    # Look for year patterns
    match = re.search(r'(?:19|20)\d{2}', text)
    if match:
        try:
            year = int(match.group(0))
            if 2000 <= year <= 2030:  # Reasonable range for solar projects
                return year
        except ValueError:
            pass
    return None

def extract_coordinates(text: str) -> Optional[Dict[str, float]]:
    """Extract latitude and longitude from text."""
    import re
    
    # Common coordinate patterns
    patterns = [
        r'(\d+(?:\.\d+)?)[°\s]*[NS][,\s]+(\d+(?:\.\d+)?)[°\s]*[EW]',  # 28.5°N, 77.2°E
        r'lat(?:itude)?[:\s]+(\d+(?:\.\d+)?)[,\s]+long(?:itude)?[:\s]+(\d+(?:\.\d+)?)',  # latitude: 28.5, longitude: 77.2
        r'\((\d+(?:\.\d+)?)[,\s]+(\d+(?:\.\d+)?)\)'  # (28.5, 77.2)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                if 6 <= lat <= 37 and 68 <= lon <= 97:  # India's bounding box
                    return {'latitude': lat, 'longitude': lon}
            except ValueError:
                continue
    return None

def normalize_company_name(name: str) -> str:
    """Normalize company names to a standard format."""
    if not name:
        return ""
        
    # Common abbreviations and their full forms
    replacements = {
        'ltd': 'Limited',
        'pvt': 'Private',
        'corp': 'Corporation',
        'inc': 'Incorporated',
        'llc': 'LLC',
        'llp': 'LLP',
        'intl': 'International',
        'tech': 'Technologies'
    }
    
    # Clean and normalize the text
    name = clean_text(name)
    name = name.lower()
    
    # Replace abbreviations
    words = name.split()
    normalized_words = []
    
    for word in words:
        # Remove dots from abbreviations
        word = word.replace('.', '')
        # Replace with full form if it's an abbreviation
        word = replacements.get(word, word)
        normalized_words.append(word)
    
    # Capitalize each word
    name = ' '.join(normalized_words).title()
    
    return name