"""Test utilities and common mocks for Solar Detective tests"""
import logging
from datetime import datetime
from unittest.mock import MagicMock

def mock_setup_logger(name, log_dir=None):
    """Mock logger setup for testing"""
    logger = MagicMock(spec=logging.Logger)
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    return logger

def mock_clean_text(text):
    """Mock text cleaning function"""
    if not text:
        return ""
    return str(text).strip()

def mock_standardize_date(date_str):
    """Mock date standardization function"""
    try:
        if isinstance(date_str, str):
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        return None
    except:
        return None

# Mock configuration for testing
TEST_CONFIG = {
    'paths': {
        'raw_data': 'data/raw',
        'processed_data': 'data/processed',
        'output_data': 'data/output',
        'logs': 'logs'
    },
    'processing': {
        'duplicate_threshold_km': 1.0
    }
}