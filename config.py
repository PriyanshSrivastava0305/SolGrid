"""
Configuration settings for the Solar Detective project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
LOG_DIR = BASE_DIR / 'logs'

# Database configuration
DATABASE_PATH = str(DATA_DIR / 'solar_detective.db')
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# Mapbox configuration
MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN', '')  # Get token from environment variable
if not MAPBOX_TOKEN:
    print("Warning: No Mapbox token found. Set the MAPBOX_TOKEN environment variable for full map functionality.")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Data scraping configuration
SCRAPER_CACHE_DIR = DATA_DIR / 'cache'
PDF_STORAGE_DIR = DATA_DIR / 'pdfs'
SATELLITE_DATA_DIR = DATA_DIR / 'satellite'

# Ensure cache directories exist
for directory in [SCRAPER_CACHE_DIR, PDF_STORAGE_DIR, SATELLITE_DATA_DIR]:
    os.makedirs(directory, exist_ok=True)

# Data directories
RAW_DATA_DIR = DATA_DIR / 'raw'
os.makedirs(RAW_DATA_DIR, exist_ok=True)

# API configuration
API_HOST = os.environ.get('SOLAR_DETECTIVE_API_HOST', '0.0.0.0')
API_PORT = int(os.environ.get('SOLAR_DETECTIVE_API_PORT', 8000))
API_DEBUG = os.environ.get('SOLAR_DETECTIVE_API_DEBUG', 'True').lower() == 'true'

# Dashboard configuration
DASHBOARD_HOST = os.environ.get('SOLAR_DETECTIVE_DASHBOARD_HOST', '0.0.0.0')
DASHBOARD_PORT = int(os.environ.get('SOLAR_DETECTIVE_DASHBOARD_PORT', 8050))
DASHBOARD_DEBUG = os.environ.get('SOLAR_DETECTIVE_DASHBOARD_DEBUG', 'True').lower() == 'true'

# Data sources URLs
MNRE_URL = "https://mnre.gov.in/solar/current-status/"
SECI_URL = "https://www.seci.co.in/web-data/docs/list-of-solar-projects"
POSOCO_URL = "https://posoco.in/reports/daily-reports/"

# Major solar developers in India for PDF scraping
SOLAR_DEVELOPERS = [
    {"name": "Adani Green Energy", "url": "https://www.adanigreenenergy.com/investors/financials"},
    {"name": "ReNew Power", "url": "https://investor.renewpower.in/financial-information/quarterly-results"},
    {"name": "Tata Power Solar", "url": "https://www.tatapower.com/investor-relations/annual-reports.aspx"},
    {"name": "Azure Power", "url": "https://investors.azurepower.com/financial-information/quarterly-results"},
    {"name": "NTPC Renewable Energy", "url": "https://www.ntpc.co.in/en/investors/financials/annual-reports"},
    {"name": "Greenko Energy", "url": "https://www.greenkogroup.com/investor-relations.php"},
]

# News sources for solar project announcements
NEWS_SOURCES = [
    {"name": "PV Magazine India", "url": "https://www.pv-magazine-india.com/category/installations/"},
    {"name": "ETEnergyWorld", "url": "https://energy.economictimes.indiatimes.com/news/renewable"},
    {"name": "Mercom India", "url": "https://mercomindia.com/category/solar/"},
]

# Satellite/GIS data sources
SATELLITE_SOURCES = [
    {"name": "Sentinel Hub", "url": "https://www.sentinel-hub.com/"},
    {"name": "BHUVAN ISRO", "url": "https://bhuvan.nrsc.gov.in/"},
]

# Data sources configuration
DATA_SOURCES = {
    'mnre': 'https://mnre.gov.in/solar/current-status/',
    'seci': 'https://www.seci.co.in',
    'posoco': 'https://posoco.in',
    'satellite': 'https://earthexplorer.usgs.gov/',
    'news': [
        {
            'name': 'PV Magazine India',
            'url': 'https://www.pv-magazine-india.com',
            'search_pattern': 'https://www.pv-magazine-india.com/search/?q={term}'
        },
        {
            'name': 'ETEnergyWorld',
            'url': 'https://energy.economictimes.indiatimes.com',
            'search_pattern': 'https://energy.economictimes.indiatimes.com/search?q={term}'
        },
        {
            'name': 'Mercom India',
            'url': 'https://mercomindia.com',
            'search_pattern': 'https://mercomindia.com/?s={term}'
        }
    ]
}

# HTTP request configuration
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Logging configuration
LOG_LEVEL = os.environ.get('SOLAR_DETECTIVE_LOG_LEVEL', 'INFO')
LOG_FILE = LOG_DIR / 'solar_detective.log'

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)