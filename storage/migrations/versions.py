"""
Track and manage database schema versions.
"""
import datetime
import os
import sqlite3
from pathlib import Path

# Add parent directory to path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import DATABASE_PATH
from storage.database import get_connection

VERSION_TABLE = "schema_versions"

def ensure_version_table_exists():
    """Create the schema version tracking table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create schema_versions table if it doesn't exist
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {VERSION_TABLE} (
        version_id INTEGER PRIMARY KEY,
        version_name TEXT NOT NULL,
        applied_at TIMESTAMP NOT NULL,
        description TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def get_current_version():
    """Get the current schema version."""
    ensure_version_table_exists()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT MAX(version_id) FROM {VERSION_TABLE}")
    result = cursor.fetchone()
    
    conn.close()
    
    if result[0] is None:
        return 0
    return result[0]

def record_migration(version_id, version_name, description=None):
    """Record a completed migration in the version table."""
    ensure_version_table_exists()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        f"INSERT INTO {VERSION_TABLE} (version_id, version_name, applied_at, description) "
        f"VALUES (?, ?, ?, ?)",
        (version_id, version_name, datetime.datetime.now(), description)
    )
    
    conn.commit()
    conn.close()
    
    print(f"Recorded migration: {version_id} - {version_name}")

def list_migrations():
    """List all applied migrations."""
    ensure_version_table_exists()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT version_id, version_name, applied_at, description FROM {VERSION_TABLE} ORDER BY version_id")
    migrations = cursor.fetchall()
    
    conn.close()
    
    if not migrations:
        print("No migrations have been applied yet.")
        return
    
    print("Applied migrations:")
    for migration in migrations:
        print(f"  {migration[0]} - {migration[1]} (applied: {migration[2]})")
        if migration[3]:
            print(f"    {migration[3]}")
    
    return migrations