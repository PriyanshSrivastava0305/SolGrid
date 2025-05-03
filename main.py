"""
Main entry point for the Solar Detective application.
"""
import argparse
import os
import sys
import logging
import multiprocessing
import time
from datetime import datetime

from config import (
    DATABASE_PATH, API_HOST, API_PORT, API_DEBUG,
    DASHBOARD_HOST, DASHBOARD_PORT, DASHBOARD_DEBUG
)
from utility_func import get_logger

logger = get_logger(__name__)

def init_database():
    """Initialize the database schema."""
    from storage.migrations.init_db import run_migration as init_db
    from storage.migrations.add_indices import run_migration as add_indices
    from storage.migrations.versions import get_current_version, list_migrations
    
    current_version = get_current_version()
    logger.info(f"Current database version: {current_version}")
    
    if current_version == 0:
        init_db()
        add_indices()
    
    list_migrations()

def run_scrapers(source=None):
    """Run the data scrapers."""
    from scrapers.mnre_scraper import MNREScraper
    from scrapers.seci_scraper import SECIScraper
    from scrapers.posco_scraper import POSCOScraper
    from scrapers.pdf_scraper import PDFScraper
    from scrapers.news_scraper import NewsScraper
    from scrapers.satellite_scraper import SatelliteScraper
    
    scrapers = {
        'mnre': MNREScraper(),
        'seci': SECIScraper(),
        'posco': POSCOScraper(),
        'pdf': PDFScraper(),
        'news': NewsScraper(),
        'satellite': SatelliteScraper()
    }
    
    if source and source in scrapers:
        logger.info(f"Running {source} scraper...")
        scrapers[source].scrape()
    elif source and source == 'all':
        logger.info("Running all scrapers...")
        for name, scraper in scrapers.items():
            logger.info(f"Running {name} scraper...")
            try:
                scraper.scrape()
            except Exception as e:
                logger.error(f"Error in {name} scraper: {str(e)}")
    else:
        logger.error(f"Unknown source: {source}. Available sources: {', '.join(scrapers.keys())} or 'all'")
        sys.exit(1)

def process_data():
    """Process the collected data."""
    from processing.data_processor import DataProcessor
    
    processor = DataProcessor()
    processor.process_all()

def run_api_server():
    """Start the API server."""
    from api.app import start_api
    
    logger.info(f"Starting API server on {API_HOST}:{API_PORT}...")
    start_api(host=API_HOST, port=API_PORT, debug=API_DEBUG)

def run_dashboard():
    """Start the dashboard application."""
    from dashboard.app import start_dashboard
    
    logger.info(f"Starting dashboard on {DASHBOARD_HOST}:{DASHBOARD_PORT}...")
    start_dashboard(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=DASHBOARD_DEBUG)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Solar Detective - India Solar Project Mapping Tool')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Initialize database command
    init_parser = subparsers.add_parser('init', help='Initialize the database')
    
    # Scraper command
    scrape_parser = subparsers.add_parser('scrape', help='Run data scrapers')
    scrape_parser.add_argument('--source', choices=['mnre', 'seci', 'posco', 'pdf', 'news', 'satellite', 'all'],
                              default='all', help='Data source to scrape (default: all)')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process collected data')
    
    # API server command
    api_parser = subparsers.add_parser('api', help='Start the API server')
    
    # Dashboard command
    dash_parser = subparsers.add_parser('dashboard', help='Start the dashboard')
    
    # Full pipeline command
    full_parser = subparsers.add_parser('full', help='Run the full pipeline: scrape, process, and start services')
    
    return parser.parse_args()

def main():
    """Main function to run the Solar Detective application."""
    args = parse_args()
    
    if not args.command:
        print("Please specify a command. Use --help for more information.")
        sys.exit(1)
    
    if args.command == 'init':
        init_database()
    
    elif args.command == 'scrape':
        run_scrapers(args.source)
    
    elif args.command == 'process':
        process_data()
    
    elif args.command == 'api':
        run_api_server()
    
    elif args.command == 'dashboard':
        run_dashboard()
    
    elif args.command == 'full':
        # Initialize database if needed
        if not os.path.exists(DATABASE_PATH):
            logger.info("Database not found, initializing...")
            init_database()
        
        # Run scrapers
        logger.info("Running all scrapers...")
        run_scrapers('all')
        
        # Process data
        logger.info("Processing data...")
        process_data()
        
        # Start API server and dashboard in separate processes
        api_process = multiprocessing.Process(target=run_api_server)
        dashboard_process = multiprocessing.Process(target=run_dashboard)
        
        api_process.start()
        dashboard_process.start()
        
        try:
            api_process.join()
            dashboard_process.join()
        except KeyboardInterrupt:
            logger.info("Shutting down services...")
            api_process.terminate()
            dashboard_process.terminate()
            api_process.join()
            dashboard_process.join()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in main application: {str(e)}", exc_info=True)
        sys.exit(1)