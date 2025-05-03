"""
Project details page for Solar Detective dashboard.
Displays detailed information about individual solar projects.
"""
import pandas as pd
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the database connection
from storage.database import get_db_connection

def create_project_details_layout():
    """Create the layout for the project details page"""
    
    # Fetch all project names from the database for the dropdown
    conn = get_db_connection()
    projects_df = pd.read_sql(
        """
        SELECT id, name, capacity_mw, developer
        FROM solar_projects
        ORDER BY name
        """, 
        conn
    )
    conn.close()
    
    # Create options for the project selector dropdown
    project_options = [
        {'label': f"{row['name']} ({row['capacity_mw']} MW, {row['developer']})", 'value': row['id']} 
        for _, row in projects_df.iterrows()
    ]
    
    # Layout
    layout = html.Div([
        html.H1("Solar Project Details", className="mb-4"),
        
        # Project selector
        dbc.Card([
            dbc.CardHeader("Select a Project"),
            dbc.CardBody([
                dcc.Dropdown(
                    id='project-selector',
                    options=project_options,
                    placeholder="Select a project to view details...",
                ),
            ]),
        ], className="mb-4"),
        
        # Project details container (will be populated by callback)
        html.Div(id='project-details-container'),
    ])
    
    return layout

# Callback to load and display project details
@callback(
    Output('project-details-container', 'children'),
    [Input('project-selector', 'value')]
)
def display_project_details(project_id):
    if not project_id:
        return html.Div("Select a project from the dropdown to view its details.")
    
    # Connect to the database
    conn = get_db_connection()
    
    # Fetch basic project details
    project_df = pd.read_sql(
        """
        SELECT *
        FROM solar_projects
        WHERE id = ?
        """, 
        conn,
        params=(project_id,)
    )
    
    if project_df.empty:
        return html.Div("Project not found.", className="text-danger")
    
    # Get the project data as a dictionary for easier access
    project = project_df.iloc[0].to_dict()
    
    # Fetch technical details
    tech_df = pd.read_sql(
        """
        SELECT *
        FROM project_technical_details
        WHERE project_id = ?
        """, 
        conn,
        params=(project_id,)
    )
    
    # Fetch business details
    business_df = pd.read_sql(
        """
        SELECT *
        FROM project_business_details
        WHERE project_id = ?
        """, 
        conn,
        params=(project_id,)
    )
    
    # Fetch historical performance data
    performance_df = pd.read_sql(
        """
        SELECT date, generation_mwh, irradiance, performance_ratio
        FROM project_performance
        WHERE project_id = ?
        ORDER BY date
        """, 
        conn,
        params=(project_id,)
    )
    
    # Close the connection
    conn.close()
    
    # Project location map
    project_map = px.scatter_mapbox(
        pd.DataFrame([{
            'lat': project['latitude'],
            'lon': project['longitude'],
            'name': project['name'],
            'capacity': project['capacity_mw']
        }]),
        lat='lat',
        lon='lon',
        hover_name='name',
        size=[30],  # Fixed size for better visibility
        zoom=10,
        mapbox_style="carto-positron",
        height=300,
    )
    project_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    
    # Performance chart
    if not performance_df.empty:
        performance_chart = px.line(
            performance_df,
            x='date',
            y=['generation_mwh', 'performance_ratio'],
            title="Historical Performance",
            labels={
                'date': 'Date',
                'generation_mwh': 'Generation (MWh)',
                'performance_ratio': 'Performance Ratio'
            }
        )
    else:
        performance_chart = go.Figure()
        performance_chart.update_layout(
            title="No historical performance data available",
            xaxis_title="Date",
            yaxis_title="Value"
        )
    
    # Format technical details as a table if available
    if not tech_df.empty:
        tech_details = tech_df.iloc[0].to_dict()
        technical_info = html.Div([
            html.H5("Technical Specifications"),
            html.Table([
                html.Tr([html.Td("Cell Technology"), html.Td(tech_details.get('cell_technology', 'N/A'))]),
                html.Tr([html.Td("Module Type"), html.Td(tech_details.get('module_type', 'N/A'))]),
                html.Tr([html.Td("Inverter Type"), html.Td(tech_details.get('inverter_type', 'N/A'))]),
                html.Tr([html.Td("Tracking System"), html.Td(tech_details.get('tracking_system', 'N/A'))]),
                html.Tr([html.Td("Grid Connection"), html.Td(tech_details.get('grid_connection', 'N/A'))]),
                html.Tr([html.Td("Storage Capacity"), html.Td(f"{tech_details.get('storage_capacity_mwh', 'N/A')} MWh" if tech_details.get('storage_capacity_mwh') else 'N/A')]),
            ], className="table table-bordered")
        ])
    else:
        technical_info = html.Div([
            html.H5("Technical Specifications"),
            html.P("Technical details not available for this project.")
        ])
    
    # Format business details as a table if available
    if not business_df.empty:
        bus_details = business_df.iloc[0].to_dict()
        business_info = html.Div([
            html.H5("Business Information"),
            html.Table([
                html.Tr([html.Td("PPA Type"), html.Td(bus_details.get('ppa_type', 'N/A'))]),
                html.Tr([html.Td("PPA Duration"), html.Td(f"{bus_details.get('ppa_duration', 'N/A')} years" if bus_details.get('ppa_duration') else 'N/A')]),
                html.Tr([html.Td("Tariff"), html.Td(f"₹{bus_details.get('tariff_inr', 'N/A')}/kWh" if bus_details.get('tariff_inr') else 'N/A')]),
                html.Tr([html.Td("Financing Source"), html.Td(bus_details.get('financing_source', 'N/A'))]),
                html.Tr([html.Td("Total Investment"), html.Td(f"₹{bus_details.get('investment_crore', 'N/A')} Crore" if bus_details.get('investment_crore') else 'N/A')]),
            ], className="table table-bordered")
        ])
    else:
        business_info = html.Div([
            html.H5("Business Information"),
            html.P("Business details not available for this project.")
        ])
    
    # Create the complete project details card
    project_details = dbc.Card([
        dbc.CardHeader(html.H3(project['name'], className="card-title")),
        dbc.CardBody([
            dbc.Row([
                # Basic information column
                dbc.Col([
                    html.H4("Basic Information"),
                    html.Table([
                        html.Tr([html.Td("Capacity"), html.Td(f"{project['capacity_mw']} MW")]),
                        html.Tr([html.Td("Project Type"), html.Td(project['project_type'])]),
                        html.Tr([html.Td("Location"), html.Td(f"{project.get('district', '')}, {project['state']}")]),
                        html.Tr([html.Td("Commissioning Year"), html.Td(project['commissioning_year'])]),
                        html.Tr([html.Td("Developer"), html.Td(project['developer'])]),
                        html.Tr([html.Td("Owner"), html.Td(project['owner'])]),
                        html.Tr([html.Td("Operator"), html.Td(project['operator'])]),
                    ], className="table table-bordered"),
                    
                    html.Div([
                        dcc.Graph(figure=project_map)
                    ], className="mt-3"),
                ], width=6),
                
                # Technical and business details column
                dbc.Col([
                    technical_info,
                    html.Hr(),
                    business_info,
                ], width=6),
            ], className="mb-4"),
            
            # Performance data
            dbc.Row([
                dbc.Col([
                    html.H4("Performance Data"),
                    dcc.Graph(figure=performance_chart)
                ])
            ])
        ]),
        
        # Export and share buttons in the footer
        dbc.CardFooter([
            dbc.Button("Export Project Data", color="primary", className="me-2", id="export-btn"),
            dbc.Button("Share", color="secondary", id="share-btn"),
            # Hidden download component
            dcc.Download(id="download-project-data")
        ])
    ])
    
    return project_details

# Callback for exporting project data
@callback(
    Output("download-project-data", "data"),
    [Input("export-btn", "n_clicks")],
    [State("project-selector", "value")]
)
def export_project_data(n_clicks, project_id):
    if n_clicks is None or not project_id:
        return None
    
    # Connect to the database
    conn = get_db_connection()
    
    # Fetch project data
    project_df = pd.read_sql(
        """
        SELECT *
        FROM solar_projects
        WHERE id = ?
        """, 
        conn,
        params=(project_id,)
    )
    
    # Fetch technical details
    tech_df = pd.read_sql(
        """
        SELECT *
        FROM project_technical_details
        WHERE project_id = ?
        """, 
        conn,
        params=(project_id,)
    )
    
    # Fetch business details
    business_df = pd.read_sql(
        """
        SELECT *
        FROM project_business_details
        WHERE project_id = ?
        """, 
        conn,
        params=(project_id,)
    )
    
    # Fetch performance data
    performance_df = pd.read_sql(
        """
        SELECT date, generation_mwh, irradiance, performance_ratio
        FROM project_performance
        WHERE project_id = ?
        ORDER BY date
        """, 
        conn,
        params=(project_id,)
    )
    
    # Close the connection
    conn.close()
    
    # Create a dictionary with all data
    data = {
        "project_info": project_df.to_dict('records')[0] if not project_df.empty else {},
        "technical_details": tech_df.to_dict('records')[0] if not tech_df.empty else {},
        "business_details": business_df.to_dict('records')[0] if not business_df.empty else {},
        "performance_data": performance_df.to_dict('records') if not performance_df.empty else []
    }
    
    # Return as CSV
    return {
        "content": pd.json_normalize(data, sep="_").to_csv(index=False),
        "filename": f"solar_project_{project_id}_{project_df.iloc[0]['name'].replace(' ', '_')}.csv"
    }