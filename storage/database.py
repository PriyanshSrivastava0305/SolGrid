"""
Database interface for the Solar Detective project.
"""
import os
import sqlite3
from typing import Optional, Union, Dict, List, Any
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from config import DATABASE_URL, DATABASE_PATH
from utility_func import get_logger

logger = get_logger(__name__)

# Create SQLAlchemy engine and session
engine = None
SessionLocal = None

def get_engine():
    """Get the SQLAlchemy engine."""
    global engine
    if engine is None:
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        
        # Create engine
        engine = create_engine(DATABASE_URL)
        logger.info(f"Created database engine for {DATABASE_URL}")
    
    return engine

def get_session_maker():
    """Get the SQLAlchemy session maker."""
    global SessionLocal
    if SessionLocal is None:
        engine = get_engine()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Created database session maker")
    
    return SessionLocal

@contextmanager
def get_db_session():
    """Get a database session as a context manager."""
    session = get_session_maker()()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()

def get_connection():
    """Get a direct SQLite connection."""
    # Ensure the database directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

class DatabaseManager:
    """Database manager class for common database operations."""
    
    @staticmethod
    def add_or_update_project(project_data: Dict[str, Any], session: Optional[Session] = None) -> str:
        """
        Add or update a project in the database.
        
        Args:
            project_data: Dictionary containing project data
            session: SQLAlchemy session (optional)
            
        Returns:
            Project ID
        """
        from storage.schema import Project
        
        if session is None:
            with get_db_session() as session:
                return DatabaseManager.add_or_update_project(project_data, session)
        
        project_id = project_data.get('id')
        
        # Check if project exists
        if project_id:
            existing_project = session.query(Project).filter(Project.id == project_id).first()
            if existing_project:
                # Update existing project
                for key, value in project_data.items():
                    if hasattr(existing_project, key) and key != 'id':
                        setattr(existing_project, key, value)
                
                logger.info(f"Updated project: {project_id}")
                return project_id
        
        # Create new project
        new_project = Project(**project_data)
        session.add(new_project)
        session.flush()  # Flush to get the ID
        
        logger.info(f"Added new project: {new_project.id}")
        return new_project.id
    
    @staticmethod
    def get_project(project_id: str, session: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """
        Get a project by ID.
        
        Args:
            project_id: Project ID
            session: SQLAlchemy session (optional)
            
        Returns:
            Project data as dictionary or None if not found
        """
        from storage.schema import Project
        
        if session is None:
            with get_db_session() as session:
                return DatabaseManager.get_project(project_id, session)
        
        project = session.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            return None
        
        # Convert SQLAlchemy model to dict
        project_dict = {column.name: getattr(project, column.name) 
                       for column in project.__table__.columns}
        
        return project_dict
    
    @staticmethod
    def list_projects(filters: Optional[Dict[str, Any]] = None, 
                      limit: int = 100, 
                      offset: int = 0,
                      session: Optional[Session] = None) -> List[Dict[str, Any]]:
        """
        List projects with optional filtering.
        
        Args:
            filters: Dictionary of filter conditions
            limit: Maximum number of results
            offset: Result offset for pagination
            session: SQLAlchemy session (optional)
            
        Returns:
            List of project dictionaries
        """
        from storage.schema import Project
        
        if session is None:
            with get_db_session() as session:
                return DatabaseManager.list_projects(filters, limit, offset, session)
        
        query = session.query(Project)
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if hasattr(Project, key):
                    if isinstance(value, list):
                        query = query.filter(getattr(Project, key).in_(value))
                    else:
                        query = query.filter(getattr(Project, key) == value)
        
        # Apply limit and offset
        query = query.limit(limit).offset(offset)
        
        # Execute query and convert results to dicts
        projects = query.all()
        result = []
        
        for project in projects:
            project_dict = {column.name: getattr(project, column.name) 
                           for column in project.__table__.columns}
            result.append(project_dict)
        
        return result
    
    @staticmethod
    def delete_project(project_id: str, session: Optional[Session] = None) -> bool:
        """
        Delete a project.
        
        Args:
            project_id: Project ID
            session: SQLAlchemy session (optional)
            
        Returns:
            True if deleted, False if not found
        """
        from storage.schema import Project
        
        if session is None:
            with get_db_session() as session:
                return DatabaseManager.delete_project(project_id, session)
        
        project = session.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            return False
        
        session.delete(project)
        logger.info(f"Deleted project: {project_id}")
        
        return True
    
    @staticmethod
    def add_data_source(data_source: Dict[str, Any], session: Optional[Session] = None) -> int:
        """
        Add a data source.
        
        Args:
            data_source: Dictionary containing data source information
            session: SQLAlchemy session (optional)
            
        Returns:
            Data source ID
        """
        from storage.schema import DataSource
        
        if session is None:
            with get_db_session() as session:
                return DatabaseManager.add_data_source(data_source, session)
        
        new_source = DataSource(**data_source)
        session.add(new_source)
        session.flush()  # Flush to get the ID
        
        logger.info(f"Added data source: {new_source.id} for project {new_source.project_id}")
        
        return new_source.id
    
    @staticmethod
    def get_or_create_company(company_data: Dict[str, Any], session: Optional[Session] = None) -> int:
        """
        Get or create a company.
        
        Args:
            company_data: Dictionary containing company information
            session: SQLAlchemy session (optional)
            
        Returns:
            Company ID
        """
        from storage.schema import Company
        
        if session is None:
            with get_db_session() as session:
                return DatabaseManager.get_or_create_company(company_data, session)
        
        name = company_data.get('name')
        if not name:
            raise ValueError("Company name is required")
        
        # Check if company exists
        company = session.query(Company).filter(Company.name == name).first()
        
        if company:
            # Update existing company with new data
            for key, value in company_data.items():
                if hasattr(company, key) and key != 'id':
                    setattr(company, key, value)
            
            logger.info(f"Updated company: {company.id} - {name}")
            return company.id
        
        # Create new company
        new_company = Company(**company_data)
        session.add(new_company)
        session.flush()  # Flush to get the ID
        
        logger.info(f"Added new company: {new_company.id} - {name}")
        return new_company.id
    
    @staticmethod
    def get_or_create_developer(developer_data: Dict[str, Any], session: Optional[Session] = None) -> int:
        """
        Get or create a developer.
        
        Args:
            developer_data: Dictionary containing developer information
            session: SQLAlchemy session (optional)
            
        Returns:
            Developer ID
        """
        from storage.schema import Developer
        
        if session is None:
            with get_db_session() as session:
                return DatabaseManager.get_or_create_developer(developer_data, session)
        
        name = developer_data.get('name')
        if not name:
            raise ValueError("Developer name is required")
        
        # Check if developer exists
        developer = session.query(Developer).filter(Developer.name == name).first()
        
        if developer:
            # Update existing developer with new data
            for key, value in developer_data.items():
                if hasattr(developer, key) and key != 'id':
                    setattr(developer, key, value)
            
            logger.info(f"Updated developer: {developer.id} - {name}")
            return developer.id
        
        # Create new developer
        new_developer = Developer(**developer_data)
        session.add(new_developer)
        session.flush()  # Flush to get the ID
        
        logger.info(f"Added new developer: {new_developer.id} - {name}")
        return new_developer.id
    
    @staticmethod
    def get_or_create_manufacturer(manufacturer_data: Dict[str, Any], session: Optional[Session] = None) -> int:
        """
        Get or create a manufacturer.
        
        Args:
            manufacturer_data: Dictionary containing manufacturer information
            session: SQLAlchemy session (optional)
            
        Returns:
            Manufacturer ID
        """
        from storage.schema import Manufacturer
        
        if session is None:
            with get_db_session() as session:
                return DatabaseManager.get_or_create_manufacturer(manufacturer_data, session)
        
        name = manufacturer_data.get('name')
        if not name:
            raise ValueError("Manufacturer name is required")
        
        # Check if manufacturer exists
        manufacturer = session.query(Manufacturer).filter(Manufacturer.name == name).first()
        
        if manufacturer:
            # Update existing manufacturer with new data
            for key, value in manufacturer_data.items():
                if hasattr(manufacturer, key) and key != 'id':
                    setattr(manufacturer, key, value)
            
            logger.info(f"Updated manufacturer: {manufacturer.id} - {name}")
            return manufacturer.id
        
        # Create new manufacturer
        new_manufacturer = Manufacturer(**manufacturer_data)
        session.add(new_manufacturer)
        session.flush()  # Flush to get the ID
        
        logger.info(f"Added new manufacturer: {new_manufacturer.id} - {name}")
        return new_manufacturer.id
    
    @staticmethod
    def add_performance_metric(metric_data: Dict[str, Any], session: Optional[Session] = None) -> int:
        """
        Add a performance metric.
        
        Args:
            metric_data: Dictionary containing performance metric data
            session: SQLAlchemy session (optional)
            
        Returns:
            Metric ID
        """
        from storage.schema import PerformanceMetric
        
        if session is None:
            with get_db_session() as session:
                return DatabaseManager.add_performance_metric(metric_data, session)
        
        # Check if metric exists for this date and project
        project_id = metric_data.get('project_id')
        date = metric_data.get('date')
        
        existing_metric = session.query(PerformanceMetric).filter(
            PerformanceMetric.project_id == project_id,
            PerformanceMetric.date == date
        ).first()
        
        if existing_metric:
            # Update existing metric
            for key, value in metric_data.items():
                if hasattr(existing_metric, key) and key not in ['id', 'project_id', 'date']:
                    setattr(existing_metric, key, value)
            
            logger.info(f"Updated performance metric: {existing_metric.id} for project {project_id}")
            return existing_metric.id
        
        # Create new metric
        new_metric = PerformanceMetric(**metric_data)
        session.add(new_metric)
        session.flush()  # Flush to get the ID
        
        logger.info(f"Added performance metric: {new_metric.id} for project {project_id}")
        return new_metric.id