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
from pathlib import Path
from contextlib import closing

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import configuration and database
from config import MAPBOX_TOKEN
from storage.database import get_db_connection
from dashboard.components.map_compnent import create_project_map

# Constants
GEOJSON_PATH = Path(__file__).parent.parent / "assets" / "geojson" / "india_states.geojson"

def get_project_data():
    """Get project data from database with proper connection handling"""
    with closing(get_db_connection()) as conn:
        projects_df = pd.read_sql(
            """
            SELECT 
                id, name, capacity as capacity_mw, latitude, longitude, 
                project_type, commissioning_year, state,
                (SELECT name FROM developers WHERE id = d.developer_id) as developer,
                (SELECT name FROM companies WHERE id = o.owner_id) as owner,
                (SELECT name FROM companies WHERE id = op.operator_id) as operator
            FROM 
                projects p
                LEFT JOIN project_developers d ON p.id = d.project_id
                LEFT JOIN project_owners o ON p.id = o.project_id
                LEFT JOIN project_operators op ON p.id = op.project_id
            """, 
            conn
        )
        
        state_data = pd.read_sql(
            """
            SELECT 
                state, SUM(capacity) as total_capacity
            FROM 
                projects
            GROUP BY 
                state
            """, 
            conn
        )
        
        return projects_df, state_data

def create_overview_layout():
    """Create the layout for the overview page"""
    
    # Fetch data from the database using the new function
    try:
        projects_df, state_data = get_project_data()
    except Exception as e:
        return html.Div([
            html.H1("Error Loading Data", className="text-danger"),
            html.P(f"An error occurred while loading the data: {str(e)}"),
        ])
    
    # Calculate summary statistics
    total_projects = len(projects_df)
    total_capacity = projects_df['capacity_mw'].sum()
    latest_year = datetime.now().year
    recent_projects = projects_df[projects_df['commissioning_year'] >= latest_year - 2].shape[0]
    
    # Create the map figure using the component
    combined_map = create_project_map(
        projects_df=projects_df,
        state_data=state_data,
        center_lat=22,
        center_lon=82,
        zoom=3.8
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
            dbc.Col(dcc.Graph(
                id='projects-map',
                figure=combined_map,
                config={'displayModeBar': True, 'scrollZoom': True}
            ), width=9),
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
    """Update the map based on filter selections"""
    try:
        with closing(get_db_connection()) as conn:
            # Start building the SQL query with filters
            query = """
                SELECT 
                    p.id, p.name, p.capacity as capacity_mw, p.latitude, p.longitude, 
                    p.state, p.project_type, p.commissioning_year,
                    (SELECT name FROM developers WHERE id = d.developer_id) as developer,
                    (SELECT name FROM companies WHERE id = o.owner_id) as owner,
                    (SELECT name FROM companies WHERE id = op.operator_id) as operator
                FROM 
                    projects p
                    LEFT JOIN project_developers d ON p.id = d.project_id
                    LEFT JOIN project_owners o ON p.id = o.project_id
                    LEFT JOIN project_operators op ON p.id = op.project_id
                WHERE 1=1
            """
            params = []
            
            # Add filters to the query
            if project_types and len(project_types) > 0:
                placeholders = ", ".join(["?" for _ in project_types])
                query += f" AND p.project_type IN ({placeholders})"
                params.extend(project_types)
                
            if capacity_range:
                query += " AND p.capacity BETWEEN ? AND ?"
                params.extend(capacity_range)
                
            if year_range:
                query += " AND p.commissioning_year BETWEEN ? AND ?"
                params.extend(year_range)
                
            if developers and len(developers) > 0:
                placeholders = ", ".join(["?" for _ in developers])
                query += f" AND d.developer_id IN (SELECT id FROM developers WHERE name IN ({placeholders}))"
                params.extend(developers)
            
            # Execute the query
            filtered_df = pd.read_sql(query, conn, params=params)
            
            # Get state-level aggregates for the choropleth
            state_query = """
                SELECT 
                    p.state, SUM(p.capacity) as total_capacity
                FROM 
                    projects p
                    LEFT JOIN project_developers d ON p.id = d.project_id
                WHERE 1=1
            """
            
            # Add the same filters
            if project_types and len(project_types) > 0:
                placeholders = ", ".join(["?" for _ in project_types])
                state_query += f" AND p.project_type IN ({placeholders})"
                
            if capacity_range:
                state_query += " AND p.capacity BETWEEN ? AND ?"
                
            if year_range:
                state_query += " AND p.commissioning_year BETWEEN ? AND ?"
                
            if developers and len(developers) > 0:
                placeholders = ", ".join(["?" for _ in developers])
                state_query += f" AND d.developer_id IN (SELECT id FROM developers WHERE name IN ({placeholders}))"
            
            state_query += " GROUP BY p.state"
            state_data = pd.read_sql(state_query, conn, params=params)
            
            # Create the map using our component
            combined_map = create_project_map(
                projects_df=filtered_df,
                state_data=state_data,
                center_lat=22,
                center_lon=82,
                zoom=3.8
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
    except Exception as e:
        error_component = html.Div([
            html.H4("Error Updating Map", className="text-danger"),
            html.P(f"An error occurred: {str(e)}")
        ])
        return go.Figure(), error_component