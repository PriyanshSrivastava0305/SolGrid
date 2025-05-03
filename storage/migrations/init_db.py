"""
Database initialization migration script.
Creates the initial tables for the Solar Detective database.
"""
import sys
import os
from pathlib import Path
import sqlite3
import pandas as pd

# Add parent directory to path to import from storage
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import DATABASE_PATH
from utility_func import get_logger

logger = get_logger(__name__)

def run_migration():
    """Run the initial database migration to create all tables."""
    print("Running initial database migration...")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS solar_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        capacity_mw REAL NOT NULL,
        latitude REAL,
        longitude REAL,
        state TEXT,
        district TEXT,
        project_type TEXT,
        commissioning_year INTEGER,
        developer TEXT,
        owner TEXT,
        operator TEXT,
        technology TEXT,
        grid_connection TEXT,
        ppa_tariff REAL,
        data_source TEXT
    );

    CREATE TABLE IF NOT EXISTS performance_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        date DATE,
        generation_mwh REAL,
        pr_ratio REAL,
        uptime_percent REAL,
        FOREIGN KEY (project_id) REFERENCES solar_projects(id)
    );
    """)

    # Insert sample data
    sample_projects = [
        {
            'name': 'Bhadla Solar Park Phase III',
            'capacity_mw': 1000.0,
            'latitude': 27.5329,
            'longitude': 71.9090,
            'state': 'Rajasthan',
            'district': 'Jodhpur',
            'project_type': 'Utility Scale',
            'commissioning_year': 2020,
            'developer': 'SECI',
            'technology': 'c-Si'
        },
        {
            'name': 'Pavagada Solar Park',
            'capacity_mw': 2050.0,
            'latitude': 14.3724,
            'longitude': 77.4688,
            'state': 'Karnataka',
            'district': 'Tumkur',
            'project_type': 'Utility Scale',
            'commissioning_year': 2019,
            'developer': 'KSPDCL',
            'technology': 'c-Si'
        },
        {
            'name': 'Rewa Ultra Mega Solar',
            'capacity_mw': 750.0,
            'latitude': 24.0667,
            'longitude': 81.7000,
            'state': 'Madhya Pradesh',
            'district': 'Rewa',
            'project_type': 'Utility Scale',
            'commissioning_year': 2018,
            'developer': 'RUMSL',
            'technology': 'c-Si'
        }
    ]

    for project in sample_projects:
        cursor.execute("""
        INSERT INTO solar_projects (
            name, capacity_mw, latitude, longitude, state, district,
            project_type, commissioning_year, developer, technology
        ) VALUES (
            :name, :capacity_mw, :latitude, :longitude, :state, :district,
            :project_type, :commissioning_year, :developer, :technology
        )
        """, project)

    conn.commit()
    conn.close()
    logger.info("Database initialized with schema and sample data")

if __name__ == "__main__":
    run_migration()