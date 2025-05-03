"""
Main dashboard application for Solar Detective.
This file initializes the Dash application and integrates all dashboard components.
"""
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

# Import dashboard pages
from pages.overview import create_overview_layout
from pages.project_details import create_project_details_layout
from pages.analytics import create_analytics_layout

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

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

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)