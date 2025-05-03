import pytest
import sys
from pathlib import Path

def main():
    """Run all tests with proper configuration"""
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Run tests with verbose output
    return pytest.main(['-v', 'tests/'])

if __name__ == '__main__':
    sys.exit(main())