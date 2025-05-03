"""
Database schema definition for the Solar Detective project.
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    ForeignKey, Table, Text, Enum, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

# Enums for project types and data sources
class ProjectType(enum.Enum):
    UTILITY_SCALE = "utility_scale"
    ROOFTOP = "rooftop"
    FLOATING = "floating"
    HYBRID_STORAGE = "hybrid_storage"
    HYBRID_WIND = "hybrid_wind"
    OTHER = "other"

class CellTechnology(enum.Enum):
    MONO_SI = "mono_crystalline_silicon"
    POLY_SI = "poly_crystalline_silicon"
    THIN_FILM = "thin_film"
    AMORPHOUS_SI = "amorphous_silicon"
    CDTE = "cadmium_telluride"
    CIGS = "copper_indium_gallium_selenide"
    PEROVSKITE = "perovskite"
    OTHER = "other"
    UNKNOWN = "unknown"

class DataSourceType(enum.Enum):
    MNRE = "mnre"
    SECI = "seci"
    POSOCO = "posoco"
    PDF = "pdf"
    NEWS = "news"
    SATELLITE = "satellite"
    MANUAL = "manual"
    OTHER = "other"

# Many-to-many relationship tables
project_developers = Table(
    'project_developers',
    Base.metadata,
    Column('project_id', String, ForeignKey('projects.id'), primary_key=True),
    Column('developer_id', Integer, ForeignKey('developers.id'), primary_key=True)
)

project_owners = Table(
    'project_owners',
    Base.metadata,
    Column('project_id', String, ForeignKey('projects.id'), primary_key=True),
    Column('owner_id', Integer, ForeignKey('companies.id'), primary_key=True)
)

project_operators = Table(
    'project_operators',
    Base.metadata,
    Column('project_id', String, ForeignKey('projects.id'), primary_key=True),
    Column('operator_id', Integer, ForeignKey('companies.id'), primary_key=True)
)

project_manufacturers = Table(
    'project_manufacturers',
    Base.metadata,
    Column('project_id', String, ForeignKey('projects.id'), primary_key=True),
    Column('manufacturer_id', Integer, ForeignKey('manufacturers.id'), primary_key=True)
)

# Main tables
class Project(Base):
    """Solar project data."""
    __tablename__ = 'projects'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    capacity = Column(Float, nullable=False)  # in MW
    latitude = Column(Float)
    longitude = Column(Float)
    location = Column(String)
    state = Column(String)
    district = Column(String)
    project_type = Column(Enum(ProjectType))
    commissioning_year = Column(Integer)
    commissioning_date = Column(DateTime)
    cell_technology = Column(Enum(CellTechnology))
    is_bifacial = Column(Boolean)
    ppa_tariff = Column(Float)  # in INR/kWh
    ppa_duration = Column(Integer)  # in years
    ppa_signed_with = Column(String)
    grid_connection_voltage = Column(Float)  # in kV
    substation_name = Column(String)
    land_area = Column(Float)  # in acres
    expected_annual_generation = Column(Float)  # in MWh
    co2_offset = Column(Float)  # in tonnes per year
    investment_amount = Column(Float)  # in crores INR
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    data_sources = relationship("DataSource", back_populates="project")
    images = relationship("ProjectImage", back_populates="project")
    performance_metrics = relationship("PerformanceMetric", back_populates="project")
    developers = relationship("Developer", secondary=project_developers)
    owners = relationship("Company", secondary=project_owners)
    operators = relationship("Company", secondary=project_operators)
    manufacturers = relationship("Manufacturer", secondary=project_manufacturers)

class DataSource(Base):
    """Data sources for project information."""
    __tablename__ = 'data_sources'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    source_type = Column(Enum(DataSourceType), nullable=False)
    source_url = Column(String)
    source_name = Column(String)
    source_date = Column(DateTime)
    confidence_score = Column(Float)  # 0-1 score of confidence in this source
    data_extracted = Column(Text)  # JSON string of extracted data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="data_sources")

class ProjectImage(Base):
    """Images of solar projects."""
    __tablename__ = 'project_images'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    image_url = Column(String)
    image_path = Column(String)  # Local path if downloaded
    image_type = Column(String)  # e.g., 'satellite', 'ground', 'aerial'
    image_date = Column(DateTime)
    caption = Column(String)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="images")

class PerformanceMetric(Base):
    """Performance metrics for projects over time."""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    generation = Column(Float)  # in MWh
    capacity_factor = Column(Float)  # percentage
    availability = Column(Float)  # percentage
    irradiance = Column(Float)  # in kWh/m²
    temperature = Column(Float)  # in °C
    source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="performance_metrics")
    
    # Unique constraint to prevent duplicate entries
    __table_args__ = (UniqueConstraint('project_id', 'date', name='_project_date_uc'),)

class Company(Base):
    """Companies that can be owners or operators."""
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    website = Column(String)
    headquarters = Column(String)
    description = Column(Text)
    founded_year = Column(Integer)
    total_capacity = Column(Float)  # Total solar capacity in MW
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Developer(Base):
    """Companies that develop solar projects."""
    __tablename__ = 'developers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    website = Column(String)
    headquarters = Column(String)
    description = Column(Text)
    founded_year = Column(Integer)
    total_developed_capacity = Column(Float)  # Total capacity developed in MW
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Manufacturer(Base):
    """Manufacturers of solar equipment."""
    __tablename__ = 'manufacturers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    website = Column(String)
    headquarters = Column(String)
    description = Column(Text)
    components = Column(String)  # What they manufacture (panels, inverters, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)