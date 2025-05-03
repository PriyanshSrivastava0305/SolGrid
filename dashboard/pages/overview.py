"""
Overview page for Solar Detective dashboard.
Displays an interactive map of all solar projects in India with key metrics.
"""
import pandas as pd
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import sys
import os

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the database connection
from storage.database import get_db_connection

def create_overview_layout():
    """Create the layout for the overview page"""
    
    # Fetch data from the database
    conn = get_db_connection()
    projects_df = pd.read_sql(
        """
        SELECT 
            id, name, capacity_mw, latitude, longitude, 
            project_type, commissioning_year, 
            developer, owner, operator
        FROM 
            solar_projects
        """, 
        conn
    )
    
    # Calculate summary statistics
    total_projects = len(projects_df)
    total_capacity = projects_df['capacity_mw'].sum()
    latest_year = datetime.now().year
    recent_projects = projects_df[projects_df['commissioning_year'] >= latest_year - 2].shape[0]
    
    # Create a choropleth map of India showing solar capacity by state
    state_data = pd.read_sql(
        """
        SELECT 
            state, SUM(capacity_mw) as total_capacity
        FROM 
            solar_projects
        GROUP BY 
            state
        """, 
        conn
    )
    
    # Close the connection
    conn.close()
    
    # Create the map figure
    india_geojson = json.load(open("dashboard/assets/india_states.geojson"))
    choropleth_map = px.choropleth_mapbox(
        state_data,
        geojson=india_geojson,
        locations='state',
        color='total_capacity',
        featureidkey="properties.state_name",
        color_continuous_scale="solar",
        mapbox_style="carto-positron",
        zoom=3.8,
        center={"lat": 22, "lon": 82},
        opacity=0.7,
        labels={'total_capacity': 'Capacity (MW)'},
        title="Solar Capacity by State",
    )
    
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
        zoom=3.8,
        center={"lat": 22, "lon": 82},
        mapbox_style="carto-positron",
        title="Solar Projects in India"
    )
    
    # Combine the two maps
    combined_map = go.Figure(choropleth_map.data + scatter_map.data)
    combined_map.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=3.8,
        mapbox_center={"lat": 22, "lon": 82},
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=600,
    )
    
    # Create filter controls
    filters = dbc.Card([
        dbc.CardHeader("Filter Projects"),
        dbc.CardBody([
            html.Div([
                html.Label("Project Type:"),
                dcc.Dropdown(
                    id='project-type-filter',
                    options=[{'label': t, 'value': t} for t in projects_df['project_type'].unique()],
                    multi=True,
                    placeholder="All Project Types"
                ),
            ], className="mb-3"),
            
            html.Div([
                html.Label("Capacity Range (MW):"),
                dcc.RangeSlider(
                    id='capacity-filter',
                    min=0,
                    max=max(projects_df['capacity_mw']),
                    value=[0, max(projects_df['capacity_mw'])],
                    marks={
                        0: '0',
                        100: '100',
                        500: '500',
                        1000: '1000',
                        2000: '2000'
                    }
                ),
            ], className="mb-3"),
            
            html.Div([
                html.Label("Commissioning Year:"),
                dcc.RangeSlider(
                    id='year-filter',
                    min=min(projects_df['commissioning_year']),
                    max=max(projects_df['commissioning_year']),
                    value=[min(projects_df['commissioning_year']), max(projects_df['commissioning_year'])],
                    marks={year: str(year) for year in range(
                        min(projects_df['commissioning_year']), 
                        max(projects_df['commissioning_year']) + 1, 
                        2
                    )}
                ),
            ], className="mb-3"),
            
            html.Div([
                html.Label("Developer:"),
                dcc.Dropdown(
                    id='developer-filter',
                    options=[{'label': d, 'value': d} for d in sorted(projects_df['developer'].unique())],
                    multi=True,
                    placeholder="All Developers"
                ),
            ], className="mb-3"),
        ]),
    ])
    
    # Create the summary cards
    summary_cards = dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{total_projects}", className="card-title text-center"),
                    html.P("Total Projects", className="card-text text-center"),
                ])
            ]),
            width=3
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{total_capacity:,.2f} MW", className="card-title text-center"),
                    html.P("Total Capacity", className="card-text text-center"),
                ])
            ]),
            width=3
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{len(projects_df['owner'].unique())}", className="card-title text-center"),
                    html.P("Unique Owners", className="card-text text-center"),
                ])
            ]),
            width=3
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{recent_projects}", className="card-title text-center"),
                    html.P("New Projects (Last 2 Years)", className="card-text text-center"),
                ])
            ]),
            width=3
        ),
    ], className="mb-4")
    
    # Put together the complete layout
    layout = html.Div([
        html.H1("India Solar Projects Overview", className="mb-4"),
        summary_cards,
        dbc.Row([
            dbc.Col(filters, width=3),
            dbc.Col(dcc.Graph(id='projects-map', figure=combined_map), width=9),
        ]),
        html.Div(id='filtered-projects-info', className="mt-4"),
    ])
    
    return layout

# Callback to update the map based on filters
@callback(
    [Output('projects-map', 'figure'),
     Output('filtered-projects-info', 'children')],
    [Input('project-type-filter', 'value'),
     Input('capacity-filter', 'value'),
     Input('year-filter', 'value'),
     Input('developer-filter', 'value')]
)
def update_map(project_types, capacity_range, year_range, developers):
    # Fetch data from the database
    conn = get_db_connection()
    
    # Start building the SQL query with filters
    query = """
        SELECT 
            id, name, capacity_mw, latitude, longitude, state,
            project_type, commissioning_year, 
            developer, owner, operator
        FROM 
            solar_projects
        WHERE 1=1
    """
    params = []
    
    # Add filters to the query
    if project_types and len(project_types) > 0:
        placeholders = ", ".join(["?" for _ in project_types])
        query += f" AND project_type IN ({placeholders})"
        params.extend(project_types)
        
    if capacity_range:
        query += " AND capacity_mw BETWEEN ? AND ?"
        params.extend(capacity_range)
        
    if year_range:
        query += " AND commissioning_year BETWEEN ? AND ?"
        params.extend(year_range)
        
    if developers and len(developers) > 0:
        placeholders = ", ".join(["?" for _ in developers])
        query += f" AND developer IN ({placeholders})"
        params.extend(developers)
    
    # Execute the query
    filtered_df = pd.read_sql(query, conn, params=params)
    
    # Also get state-level aggregates for the choropleth
    state_query = """
        SELECT 
            state, SUM(capacity_mw) as total_capacity
        FROM 
            solar_projects
        WHERE 1=1
    """
    
    # Add the same filters
    if project_types and len(project_types) > 0:
        placeholders = ", ".join(["?" for _ in project_types])
        state_query += f" AND project_type IN ({placeholders})"
        
    if capacity_range:
        state_query += " AND capacity_mw BETWEEN ? AND ?"
        
    if year_range:
        state_query += " AND commissioning_year BETWEEN ? AND ?"
        
    if developers and len(developers) > 0:
        placeholders = ", ".join(["?" for _ in developers])
        state_query += f" AND developer IN ({placeholders})"
    
    state_query += " GROUP BY state"
    
    # Execute the state query
    state_data = pd.read_sql(state_query, conn, params=params)
    
    # Close the connection
    conn.close()
    
    # Create the updated choropleth map
    india_geojson = json.load(open("dashboard/assets/india_states.geojson"))
    choropleth_map = px.choropleth_mapbox(
        state_data,
        geojson=india_geojson,
        locations='state',
        color='total_capacity',
        featureidkey="properties.state_name",
        color_continuous_scale="solar",
        mapbox_style="carto-positron",
        zoom=3.8,
        center={"lat": 22, "lon": 82},
        opacity=0.7,
        labels={'total_capacity': 'Capacity (MW)'},
    )
    
    # Create updated scatter map for individual projects
    scatter_map = px.scatter_mapbox(
        filtered_df,
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
        zoom=3.8,
        center={"lat": 22, "lon": 82},
        mapbox_style="carto-positron",
    )
    
    # Combine the two maps
    combined_map = go.Figure(choropleth_map.data + scatter_map.data)
    combined_map.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=3.8,
        mapbox_center={"lat": 22, "lon": 82},
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=600,
        title="Solar Projects in India (Filtered)"
    )
    
    # Create summary information
    total_projects = len(filtered_df)
    total_capacity = filtered_df['capacity_mw'].sum()
    
    info_component = html.Div([
        html.H4(f"Showing {total_projects} projects with {total_capacity:,.2f} MW total capacity"),
        html.P(f"Filtered by: " + 
              (f"Project Types: {', '.join(project_types)}" if project_types else "All Project Types") + 
              f" | Capacity: {capacity_range[0]} - {capacity_range[1]} MW" +
              f" | Years: {year_range[0]} - {year_range[1]}" +
              (f" | Developers: {', '.join(developers)}" if developers else " | All Developers"))
    ])
    
    return combined_map, info_component