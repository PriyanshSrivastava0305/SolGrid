"""
Project card component for the Solar Detective dashboard.
Used to display summary information about solar projects.
"""
from dash import html
import dash_bootstrap_components as dbc

def create_project_card(project_data):
    """
    Create a card displaying key information about a solar project
    
    Parameters:
    project_data (dict): Dictionary containing project information
    
    Returns:
    dash component: A card component displaying project information
    """
    
    # Create the card
    card = dbc.Card([
        dbc.CardHeader(
            html.H5(project_data.get('name', 'Unknown Project'), className="card-title")
        ),
        dbc.CardBody([
            html.Div([
                html.Strong("Capacity: "),
                html.Span(f"{project_data.get('capacity_mw', 'N/A')} MW")
            ], className="mb-2"),
            
            html.Div([
                html.Strong("Location: "),
                html.Span(f"{project_data.get('district', '')}, {project_data.get('state', 'N/A')}")
            ], className="mb-2"),
            
            html.Div([
                html.Strong("Developer: "),
                html.Span(project_data.get('developer', 'N/A'))
            ], className="mb-2"),
            
            html.Div([
                html.Strong("Type: "),
                html.Span(project_data.get('project_type', 'N/A'))
            ], className="mb-2"),
            
            html.Div([
                html.Strong("Commissioned: "),
                html.Span(str(project_data.get('commissioning_year', 'N/A')))
            ], className="mb-2"),
        ]),
        dbc.CardFooter([
            dbc.Button(
                "View Details", 
                id={"type": "view-details-btn", "index": project_data.get('id')},
                color="primary", 
                size="sm",
                className="me-2"
            ),
            dbc.Button(
                "Location", 
                id={"type": "view-location-btn", "index": project_data.get('id')},
                color="secondary", 
                size="sm"
            ),
        ])
    ], className="h-100")
    
    return card