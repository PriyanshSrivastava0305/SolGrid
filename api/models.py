from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date

class Coordinate(BaseModel):
    latitude: float
    longitude: float

class TechnicalDetails(BaseModel):
    cell_technology: Optional[str] = None
    module_type: Optional[str] = None  # bifacial or monofacial
    grid_connection: Optional[str] = None
    inverter_type: Optional[str] = None
    tracking_system: Optional[str] = None  # fixed-tilt or tracker
    dc_capacity: Optional[float] = None  # DC capacity in MW
    dc_ac_ratio: Optional[float] = None  # DC to AC ratio

class BusinessDetails(BaseModel):
    manufacturer: Optional[str] = None  # Panel manufacturer
    epc_contractor: Optional[str] = None  # Engineering, Procurement, Construction contractor
    offtake_agreement: Optional[str] = None  # PPA details
    ppa_duration: Optional[int] = None  # Years
    ppa_tariff: Optional[float] = None  # ₹/kWh
    financing_model: Optional[str] = None
    capex: Optional[float] = None  # Capital expenditure (₹ crores)
    estimated_generation: Optional[float] = None  # Annual MWh

class PerformanceData(BaseModel):
    capacity_factor: Optional[float] = None  # Percentage
    annual_generation: Optional[float] = None  # MWh
    monthly_generation: Optional[Dict[str, float]] = None  # Month: MWh
    availability: Optional[float] = None  # Percentage

class SolarProject(BaseModel):
    id: str
    name: str
    capacity: float = Field(..., description="Capacity in MW")
    location: Coordinate
    address: Optional[str] = None
    district: Optional[str] = None
    state: str
    developer: str
    owner: Optional[str] = None
    operator: Optional[str] = None
    commission_date: Optional[date] = None  # Date of commissioning
    project_type: str  # Utility-scale, Rooftop, Floating, Hybrid
    status: str  # Under development, Operational, Decommissioned
    technical_details: Optional[TechnicalDetails] = None
    business_details: Optional[BusinessDetails] = None
    performance_data: Optional[PerformanceData] = None
    images: Optional[List[str]] = None  # URLs to project images
    data_sources: Optional[List[str]] = None  # Sources of information
    last_updated: date  # Date of last data update
    confidence_score: Optional[float] = None  # Data reliability score (0-1)

class ProjectFilters(BaseModel):
    capacity_min: Optional[float] = None
    capacity_max: Optional[float] = None
    developer: Optional[str] = None
    state: Optional[str] = None
    project_type: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    technology: Optional[str] = None

class YearlyCapacity(BaseModel):
    year: int
    capacity: float  # MW

class StateCapacity(BaseModel):
    state: str
    capacity: float  # MW

class DeveloperCapacity(BaseModel):
    developer: str
    capacity: float  # MW

class TechnologyBreakdown(BaseModel):
    technology: str
    capacity: float  # MW

class ProjectStats(BaseModel):
    total_projects: int
    total_capacity: float  # MW
    operational_capacity: float  # MW
    under_development_capacity: float  # MW
    yearly_growth: List[YearlyCapacity]
    state_distribution: List[StateCapacity]
    developer_distribution: List[DeveloperCapacity]
    technology_breakdown: List[TechnologyBreakdown]
    avg_capacity_factor: Optional[float] = None  # Percentage