"""
Main dashboard application for Solar Detective.
This file initializes the Dash application and integrates all dashboard components.
"""
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import os
from pathlib import Path
import sys
import logging

# Add project root to Python path
root_dir = str(Path(__file__).parent.parent)
sys.path.append(root_dir)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration and components
try:
    from config import DASHBOARD_HOST, DASHBOARD_PORT, DASHBOARD_DEBUG
    from storage.database import init_db, get_db_connection
    from pages.overview import create_overview_layout
    from pages.project_details import create_project_details_layout
    from pages.analytics import create_analytics_layout
except Exception as e:
    logger.error(f"Error importing dependencies: {e}")
    raise

# Initialize the database
try:
    logger.info("Initializing database...")
    from storage.migrations.init_db import run_migration
    run_migration()
    logger.info("Database initialization complete")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    raise

# Initialize the Dash app with Bootstrap theme and error handling
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Add error handling middleware
@app.server.errorhandler(500)
def handle_error(error):
    return html.Div([
        html.H1("Error", className="text-danger"),
        html.P("An error occurred while processing your request. Please try again later."),
        html.Pre(str(error))
    ])

# Define the app layout with navigation
app.layout = html.Div([
    # URL location component to track current page
    dcc.Location(id='url', refresh=False),
    
    # Navigation header
    dbc.Navbar(
        dbc.Container([
            html.A(
                dbc.Row([
                    dbc.Col(html.Img(src="assets/logo.png", height="40px"), width="auto"),
                    dbc.Col(dbc.NavbarBrand("Solar Detective", className="ms-2")),
                ], align="center", className="g-0"),
                href="/",
                style={"textDecoration": "none"},
            ),
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Overview", href="/")),
                dbc.NavItem(dbc.NavLink("Project Details", href="/projects")),
                dbc.NavItem(dbc.NavLink("Analytics", href="/analytics")),
                dbc.NavItem(dbc.NavLink("About", href="/about")),
            ], className="ms-auto", navbar=True),
        ]),
        color="primary",
        dark=True,
    ),
    
    # Content container - will be populated based on the URL
    dbc.Container(id='page-content', className="mt-4", fluid=True),
])

# Callback to render different pages based on URL pathname
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    try:
        if pathname == '/':
            return create_overview_layout()
        elif pathname == '/projects':
            return create_project_details_layout()
        elif pathname == '/analytics':
            return create_analytics_layout()
        elif pathname == '/about':
            return html.Div([
                html.H1("About Solar Detective"),
                html.P("""
                    Solar Detective is an AI-powered platform that maps India's solar 
                    infrastructure by collecting, processing, and visualizing data from 
                    various sources including government portals, company reports, news articles, 
                    and satellite imagery.
                """),
                html.P("""
                    Our mission is to provide transparency in India's renewable energy landscape, 
                    enabling better decision-making for developers, investors, and policymakers.
                """),
            ])
        # If the pathname isn't recognized, return a 404 message
        return html.Div([
            html.H1("404: Page not found", className="text-danger"),
            html.P(f"The pathname {pathname} was not recognized..."),
            dcc.Link("Go to Home", href="/")
        ])
    except Exception as e:
        return html.Div([
            html.H1("Error", className="text-danger"),
            html.P(f"An error occurred while loading the page: {str(e)}"),
            dcc.Link("Go to Home", href="/")
        ])

# Run the server with configuration from environment
if __name__ == '__main__':
    host = '127.0.0.1'  # Force localhost binding
    port = 8050  # Use fixed port for testing
    debug = True  # Enable debug mode for better error reporting
    
    print(f"\nStarting dashboard server...")
    print(f"Dashboard will be available at: http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        app.run_server(
            host=host,
            port=port,
            debug=debug,
            use_reloader=True  # Enable auto-reload on code changes
        )
    except Exception as e:
        print(f"Error starting dashboard server: {str(e)}")
        raise  # Re-raise the exception for proper error handling