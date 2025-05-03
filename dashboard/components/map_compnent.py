"""
Interactive map component for the Solar Detective dashboard.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

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
    # Create scatter map for individual projects
    scatter_map = px.scatter_mapbox(
        projects_df,
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
        mapbox_style="carto-positron",
        title="Solar Projects in India"
    )
    
    # If state data is provided, add a choropleth layer
    if state_data is not None:
        try:
            # Load India GeoJSON
            india_geojson = json.load(open("dashboard/assets/india_states.geojson"))
            
            # Create choropleth map
            choropleth_map = px.choropleth_mapbox(
                state_data,
                geojson=india_geojson,
                locations='state',
                color='total_capacity',
                featureidkey="properties.state_name",
                color_continuous_scale="solar",
                mapbox_style="carto-positron",
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
    
    # Update layout
    combined_map.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=zoom,
        mapbox_center={"lat": center_lat, "lon": center_lon},
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
        mapbox_style="carto-positron",
    )
    
    # Update layout
    project_map.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=400,
        showlegend=False
    )
    
    return project_map