"""
Migration script to add indices to improve query performance.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from storage.database import get_connection
from storage.migrations.versions import record_migration

def run_migration():
    """Add performance indices to the database."""
    print("Running migration: Adding performance indices...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Add spatial index on projects table for location-based queries
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_projects_location 
    ON projects (latitude, longitude)
    """)
    
    # Add index on projects table for common filtering operations
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_projects_capacity 
    ON projects (capacity)
    """)
    
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_projects_commissioning_year 
    ON projects (commissioning_year)
    """)
    
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_projects_project_type 
    ON projects (project_type)
    """)
    
    # Add index on data_sources table
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_data_sources_project_id 
    ON data_sources (project_id)
    """)
    
    conn.commit()
    conn.close()
    
    # Record this migration in the versions table
    record_migration(
        version_id=2,
        version_name="add_performance_indices",
        description="Added indices for location, capacity, year, type and data sources"
    )
    
    print("Performance indices added successfully.")

if __name__ == "__main__":
    run_migration()