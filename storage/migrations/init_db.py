"""
Database initialization migration script.
Creates the initial tables for the Solar Detective database.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import from storage
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from config import DATABASE_URL
from storage.schema import Base, Project, ProjectType, CellTechnology
from utility_func import get_logger
from datetime import datetime

logger = get_logger(__name__)

def run_migration():
    """Run the initial database migration to create all tables."""
    print("Running initial database migration...")
    
    # Create database engine
    engine = create_engine(DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Sample data can be added using SQLAlchemy models
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Add sample projects
    sample_projects = [
        Project(
            id="BHA-001",
            name="Bhadla Solar Park Phase III",
            capacity=1000.0,
            latitude=27.5329,
            longitude=71.9090,
            state="Rajasthan",
            district="Jodhpur",
            project_type=ProjectType.UTILITY_SCALE,
            commissioning_year=2020,
            cell_technology=CellTechnology.MONO_SI,
            grid_connection_voltage=400.0,
            land_area=5000.0,
            expected_annual_generation=1752000.0  # MWh (assuming 20% CUF)
        ),
        Project(
            id="PAV-001",
            name="Pavagada Solar Park",
            capacity=2050.0,
            latitude=14.3724,
            longitude=77.4688,
            state="Karnataka",
            district="Tumkur",
            project_type=ProjectType.UTILITY_SCALE,
            commissioning_year=2019,
            cell_technology=CellTechnology.POLY_SI,
            grid_connection_voltage=400.0,
            land_area=13000.0,
            expected_annual_generation=3591600.0  # MWh (assuming 20% CUF)
        ),
        Project(
            id="REW-001",
            name="Rewa Ultra Mega Solar",
            capacity=750.0,
            latitude=24.0667,
            longitude=81.7000,
            state="Madhya Pradesh",
            district="Rewa",
            project_type=ProjectType.UTILITY_SCALE,
            commissioning_year=2018,
            cell_technology=CellTechnology.MONO_SI,
            grid_connection_voltage=400.0,
            land_area=3500.0,
            expected_annual_generation=1314000.0  # MWh (assuming 20% CUF)
        )
    ]
    
    try:
        for project in sample_projects:
            session.add(project)
        session.commit()
        logger.info("Sample projects added successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding sample projects: {str(e)}")
    finally:
        session.close()
    
    logger.info("Database initialized with schema and sample data")

if __name__ == "__main__":
    run_migration()