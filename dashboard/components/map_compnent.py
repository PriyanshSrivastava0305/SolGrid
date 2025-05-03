"""
Interactive map component for the Solar Detective dashboard.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from pathlib import Path

# Constants
DEFAULT_MAPBOX_STYLE = "carto-positron"
GEOJSON_PATH = Path(__file__).parent.parent / "assets" / "geojson" / "india_states.geojson"

# Get Mapbox token from environment variable or config
def get_mapbox_token():
    token = os.getenv('MAPBOX_TOKEN')
    if not token:
        try:
            import config
            token = config.MAPBOX_TOKEN
        except (ImportError, AttributeError):
            print("Warning: No Mapbox token found. Map functionality may be limited.")
    return token or ''

MAPBOX_TOKEN = get_mapbox_token()

def validate_coordinates(lat, lon):
    """Validate latitude and longitude values"""
    try:
        lat = float(lat)
        lon = float(lon)
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return True
        return False
    except (ValueError, TypeError):
        return False

def load_geojson():
    """Safely load GeoJSON file"""
    try:
        with open(GEOJSON_PATH) as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load GeoJSON file: {e}")
        return None

def create_project_map(projects_df, state_data=None, center_lat=22, center_lon=82, zoom=3.8):
    """
    Create an interactive map showing solar projects and state-level data
    
    Parameters:
    projects_df (DataFrame): DataFrame containing project-level data
    state_data (DataFrame): DataFrame containing state-level aggregated data
    center_lat (float): Latitude for map center
    center_lon (float): Longitude for map center
    zoom (float): Initial zoom level
    
    Returns:
    plotly.graph_objects.Figure: Interactive map figure
    """
    # Validate and clean input data
    if not isinstance(projects_df, pd.DataFrame) or projects_df.empty:
        return go.Figure().update_layout(
            annotations=[{"text": "No project data available", "showarrow": False, "font": {"size": 20}}]
        )
    
    # Filter out invalid coordinates
    valid_projects = projects_df[
        projects_df.apply(lambda row: validate_coordinates(row['latitude'], row['longitude']), axis=1)
    ].copy()
    
    if valid_projects.empty:
        return go.Figure().update_layout(
            annotations=[{"text": "No valid project coordinates found", "showarrow": False, "font": {"size": 20}}]
        )

    # Create scatter map for individual projects
    scatter_map = px.scatter_mapbox(
        valid_projects,
        lat='latitude',
        lon='longitude',
        size='capacity_mw',
        color='project_type',
        hover_name='name',
        hover_data={
            'capacity_mw': True,
            'developer': True,
            'commissioning_year': True,
            'latitude': False,
            'longitude': False,
        },
        zoom=zoom,
        center={"lat": center_lat, "lon": center_lon},
        mapbox_style=DEFAULT_MAPBOX_STYLE,
        title="Solar Projects in India"
    )
    
    # If state data is provided, add a choropleth layer
    if state_data is not None:
        india_geojson = load_geojson()
        if india_geojson:
            try:
                # Create choropleth map
                choropleth_map = px.choropleth_mapbox(
                    state_data,
                    geojson=india_geojson,
                    locations='state',
                    color='total_capacity',
                    featureidkey="properties.state_name",
                    color_continuous_scale="solar",
                    mapbox_style=DEFAULT_MAPBOX_STYLE,
                    zoom=zoom,
                    center={"lat": center_lat, "lon": center_lon},
                    opacity=0.7,
                    labels={'total_capacity': 'Capacity (MW)'},
                )
                
                # Combine the two maps
                combined_map = go.Figure(choropleth_map.data + scatter_map.data)
            except Exception:
                # If there's an error with the choropleth (e.g., missing geojson), just use scatter map
                combined_map = scatter_map
        else:
            combined_map = scatter_map
    else:
        combined_map = scatter_map
    
    # Update layout with Mapbox token
    combined_map.update_layout(
        mapbox=dict(
            accesstoken=MAPBOX_TOKEN,
            style=DEFAULT_MAPBOX_STYLE,
            zoom=zoom,
            center={"lat": center_lat, "lon": center_lon}
        ),
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=600,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.8)"
        )
    )
    
    return combined_map


def create_single_project_map(project_data, zoom=10):
    """
    Create a map focused on a single solar project
    
    Parameters:
    project_data (dict): Dictionary containing project information
    zoom (float): Zoom level
    
    Returns:
    plotly.graph_objects.Figure: Map figure focused on a single project
    """
    if not project_data:
        return go.Figure().update_layout(
            annotations=[{"text": "No project data provided", "showarrow": False, "font": {"size": 20}}]
        )
    
    lat = project_data.get('latitude')
    lon = project_data.get('longitude')
    
    if not validate_coordinates(lat, lon):
        return go.Figure().update_layout(
            annotations=[{"text": "Invalid project coordinates", "showarrow": False, "font": {"size": 20}}]
        )

    # Create DataFrame from project data
    df = pd.DataFrame([{
        'name': project_data.get('name', 'Unknown Project'),
        'latitude': project_data.get('latitude'),
        'longitude': project_data.get('longitude'),
        'capacity_mw': project_data.get('capacity_mw'),
        'project_type': project_data.get('project_type'),
        'developer': project_data.get('developer'),
        'commissioning_year': project_data.get('commissioning_year')
    }])
    
    # Create map focused on this project
    project_map = px.scatter_mapbox(
        df,
        lat='latitude',
        lon='longitude',
        hover_name='name',
        size=[30],  # Fixed size for better visibility
        color_discrete_sequence=['#FF5733'],  # Highlight color
        zoom=zoom,
        center={"lat": project_data.get('latitude'), "lon": project_data.get('longitude')},
        mapbox_style=DEFAULT_MAPBOX_STYLE,
    )
    
    # Update layout with Mapbox token
    project_map.update_layout(
        mapbox=dict(
            accesstoken=MAPBOX_TOKEN,
            style=DEFAULT_MAPBOX_STYLE,
            zoom=zoom,
            center={"lat": project_data.get('latitude'), "lon": project_data.get('longitude')}
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=400,
        showlegend=False
    )
    
    return project_map