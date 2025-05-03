import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test configuration fixtures can be added here
import pytest

@pytest.fixture
def sample_solar_project():
    return {
        "id": 1,
        "name": "Test Solar Plant",
        "latitude": 14.8971,
        "longitude": 77.5876,
        "capacity": 500.0,
        "state": "Karnataka",
        "commissioning_date": "2024-01-15",
        "developer": "Test Developer",
        "technology": "c-Si"
    }

@pytest.fixture
def temp_data_dir(tmp_path):
    """Provide a temporary directory for test data"""
    return tmp_path