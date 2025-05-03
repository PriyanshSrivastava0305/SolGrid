from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from storage.database import Database
from api.models import SolarProject, ProjectFilters, ProjectStats

app = FastAPI(
    title="Solar Detective API",
    description="API for accessing India's solar infrastructure data",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

@app.get("/projects", response_model=List[SolarProject])
async def get_projects(
    db: Database = Depends(get_db),
    capacity_min: Optional[float] = None,
    capacity_max: Optional[float] = None,
    developer: Optional[str] = None,
    state: Optional[str] = None,
    project_type: Optional[str] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    technology: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get solar projects with optional filtering"""
    filters = ProjectFilters(
        capacity_min=capacity_min,
        capacity_max=capacity_max,
        developer=developer,
        state=state,
        project_type=project_type,
        year_min=year_min,
        year_max=year_max,
        technology=technology
    )
    
    projects = db.get_projects(filters, limit)
    if not projects:
        return []
    return projects

@app.get("/projects/{project_id}", response_model=SolarProject)
async def get_project(project_id: str, db: Database = Depends(get_db)):
    """Get a specific solar project by ID"""
    project = db.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.get("/stats", response_model=ProjectStats)
async def get_stats(db: Database = Depends(get_db)):
    """Get overall statistics about solar projects"""
    return db.get_statistics()

@app.get("/developers")
async def get_developers(db: Database = Depends(get_db)):
    """Get list of all developers"""
    return db.get_unique_values("developer")

@app.get("/states")
async def get_states(db: Database = Depends(get_db)):
    """Get list of all states with solar projects"""
    return db.get_unique_values("state")

@app.get("/technologies")
async def get_technologies(db: Database = Depends(get_db)):
    """Get list of all solar technologies in use"""
    return db.get_unique_values("technology")

@app.get("/project-types")
async def get_project_types(db: Database = Depends(get_db)):
    """Get list of all project types"""
    return db.get_unique_values("project_type")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)