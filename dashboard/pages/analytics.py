"""
Analytics page for Solar Detective dashboard.
Provides insights and trends across the solar project database.
"""
import pandas as pd
import numpy as np
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the database connection
from storage.database import get_db_connection

def create_analytics_layout():
    """Create the layout for the analytics page"""
    
    # Fetch data from the database
    conn = get_db_connection()
    
    # For time series visualization
    yearly_capacity = pd.read_sql(
        """
        SELECT 
            commissioning_year as year, 
            SUM(capacity_mw) as new_capacity,
            COUNT(*) as project_count
        FROM 
            solar_projects
        GROUP BY 
            commissioning_year
        ORDER BY 
            commissioning_year
        """, 
        conn
    )
    
    # Calculate cumulative capacity over years
    yearly_capacity['cumulative_capacity'] = yearly_capacity['new_capacity'].cumsum()
    
    # Developer market share
    developer_share = pd.read_sql(
        """
        SELECT 
            developer, 
            SUM(capacity_mw) as total_capacity,
            COUNT(*) as project_count
        FROM 
            solar_projects
        GROUP BY 
            developer
        ORDER BY 
            total_capacity DESC
        LIMIT 10
        """, 
        conn
    )
    
    # Project type distribution
    type_distribution = pd.read_sql(
        """
        SELECT 
            project_type, 
            SUM(capacity_mw) as total_capacity,
            COUNT(*) as project_count
        FROM 
            solar_projects
        GROUP BY 
            project_type
        ORDER BY 
            total_capacity DESC
        """, 
        conn
    )
    
    # State-level distribution
    state_distribution = pd.read_sql(
        """
        SELECT 
            state, 
            SUM(capacity_mw) as total_capacity,
            COUNT(*) as project_count
        FROM 
            solar_projects
        GROUP BY 
            state
        ORDER BY 
            total_capacity DESC
        LIMIT 15
        """, 
        conn
    )
    
    # Get technical details distribution
    tech_distribution = pd.read_sql(
        """
        SELECT 
            t.cell_technology,
            t.module_type,
            COUNT(*) as project_count,
            SUM(p.capacity_mw) as total_capacity
        FROM 
            project_technical_details t
        JOIN
            solar_projects p ON t.project_id = p.id
        GROUP BY 
            t.cell_technology, t.module_type
        """, 
        conn
    )
    
    # Close connection
    conn.close()
    
    # Create growth trend chart
    growth_fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add bar chart for new capacity
    growth_fig.add_trace(
        go.Bar(
            x=yearly_capacity['year'],
            y=yearly_capacity['new_capacity'],
            name="New Capacity (MW)",
            marker_color='rgb(55, 83, 109)'
        ),
        secondary_y=False,
    )
    
    # Add line chart for cumulative capacity
    growth_fig.add_trace(
        go.Scatter(
            x=yearly_capacity['year'],
            y=yearly_capacity['cumulative_capacity'],
            name="Cumulative Capacity (MW)",
            marker_color='rgb(26, 118, 255)'
        ),
        secondary_y=True,
    )
    
    growth_fig.update_layout(
        title_text="Growth of Solar Capacity in India",
        xaxis=dict(title="Year"),
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(255, 255, 255, 0.8)'),
        barmode='group',
        bargap=0.15,
        bargroupgap=0.1,
        height=500
    )
    
    growth_fig.update_yaxes(title_text="New Capacity (MW)", secondary_y=False)
    growth_fig.update_yaxes(title_text="Cumulative Capacity (MW)", secondary_y=True)
    
    # Create developer market share pie chart
    developer_fig = px.pie(
        developer_share,
        values='total_capacity',
        names='developer',
        title='Top 10 Developers by Capacity (MW)',
        hover_data=['project_count']
    )
    developer_fig.update_traces(textposition='inside', textinfo='percent+label')
    
    # Create project type distribution chart
    type_fig = px.bar(
        type_distribution,
        x='project_type',
        y='total_capacity',
        color='project_type',
        title='Capacity by Project Type',
        hover_data=['project_count']
    )
    type_fig.update_layout(xaxis_title="Project Type", yaxis_title="Capacity (MW)")
    
    # Create state distribution chart
    state_fig = px.bar(
        state_distribution,
        x='state',
        y='total_capacity',
        color='state',
        title='Top 15 States by Solar Capacity',
        hover_data=['project_count']
    )
    state_fig.update_layout(xaxis_title="State", yaxis_title="Capacity (MW)")
    
    # Create technology distribution treemap
    if not tech_distribution.empty:
        tech_fig = px.treemap(
            tech_distribution,
            path=['cell_technology', 'module_type'],
            values='total_capacity',
            color='total_capacity',
            hover_data=['project_count'],
            title='Technology Distribution by Capacity'
        )
    else:
        tech_fig = go.Figure()
        tech_fig.update_layout(
            title="No technology data available",
            annotations=[dict(
                text="No technology data available",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5
            )]
        )
    
    # Create the layout
    layout = html.Div([
        html.H1("Solar Analytics", className="mb-4"),
        
        # Growth Trends
        dbc.Card([
            dbc.CardHeader(html.H4("Growth Trends", className="card-title")),
            dbc.CardBody(dcc.Graph(figure=growth_fig))
        ], className="mb-4"),
        
        # Market Share and Distribution
        dbc.Row([
            # Developer Market Share
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Developer Market Share", className="card-title")),
                    dbc.CardBody(dcc.Graph(figure=developer_fig))
                ])
            ], width=6),
            
            # Project Type Distribution
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Project Type Distribution", className="card-title")),
                    dbc.CardBody(dcc.Graph(figure=type_fig))
                ])
            ], width=6)
        ], className="mb-4"),
        
        # State Distribution and Technology
        dbc.Row([
            # State Distribution
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("State-wise Distribution", className="card-title")),
                    dbc.CardBody(dcc.Graph(figure=state_fig))
                ])
            ], width=6),
            
            # Technology Distribution
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Technology Distribution", className="card-title")),
                    dbc.CardBody(dcc.Graph(figure=tech_fig))
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Insights and Recommendations
        dbc.Card([
            dbc.CardHeader(html.H4("Key Insights", className="card-title")),
            dbc.CardBody([
                html.Div(id="analytics-insights", children=[
                    html.Ul([
                        html.Li(f"Total solar capacity: {yearly_capacity['cumulative_capacity'].iloc[-1]:,.2f} MW"),
                        html.Li(f"Total projects tracked: {yearly_capacity['project_count'].sum()}"),
                        html.Li(f"Highest growth year: {yearly_capacity.loc[yearly_capacity['new_capacity'].idxmax(), 'year']} with {yearly_capacity['new_capacity'].max():,.2f} MW added"),
                        html.Li(f"Leading developer: {developer_share.iloc[0]['developer']} with {developer_share.iloc[0]['total_capacity']:,.2f} MW capacity"),
                        html.Li(f"Most common project type: {type_distribution.iloc[0]['project_type']} with {type_distribution.iloc[0]['project_count']} projects"),
                        html.Li(f"Leading state: {state_distribution.iloc[0]['state']} with {state_distribution.iloc[0]['total_capacity']:,.2f} MW capacity")
                    ])
                ])
            ])
        ], className="mb-4"),
        
        # Custom analysis section
        dbc.Card([
            dbc.CardHeader(html.H4("Custom Analysis", className="card-title")),
            dbc.CardBody([
                html.P("Select parameters to generate custom analysis:"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Group By:"),
                        dcc.Dropdown(
                            id='group-by-dropdown',
                            options=[
                                {'label': 'Developer', 'value': 'developer'},
                                {'label': 'Project Type', 'value': 'project_type'},
                                {'label': 'State', 'value': 'state'},
                                {'label': 'Commissioning Year', 'value': 'commissioning_year'}
                            ],
                            value='state'
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("Metric:"),
                        dcc.Dropdown(
                            id='metric-dropdown',
                            options=[
                                {'label': 'Total Capacity (MW)', 'value': 'capacity'},
                                {'label': 'Project Count', 'value': 'count'},
                                {'label': 'Average Project Size (MW)', 'value': 'avg_size'}
                            ],
                            value='capacity'
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("Chart Type:"),
                        dcc.Dropdown(
                            id='chart-type-dropdown',
                            options=[
                                {'label': 'Bar Chart', 'value': 'bar'},
                                {'label': 'Pie Chart', 'value': 'pie'},
                                {'label': 'Line Chart', 'value': 'line'}
                            ],
                            value='bar'
                        )
                    ], width=4)
                ], className="mb-3"),
                
                dbc.Button("Generate Analysis", id="generate-analysis-btn", color="primary", className="mb-3"),
                
                # Custom chart container
                html.Div(id="custom-chart-container")
            ])
        ])
    ])
    
    return layout

# Callback for custom analysis
@callback(
    Output('custom-chart-container', 'children'),
    [Input('generate-analysis-btn', 'n_clicks')],
    [Input('group-by-dropdown', 'value'),
     Input('metric-dropdown', 'value'),
     Input('chart-type-dropdown', 'value')]
)
def generate_custom_analysis(n_clicks, group_by, metric, chart_type):
    if n_clicks is None:
        return html.Div("Click the 'Generate Analysis' button to create a custom chart.")
    
    # Connect to database
    conn = get_db_connection()
    
    # Build query based on selections
    if metric == 'capacity':
        value_col = "SUM(capacity_mw) as value"
        title_suffix = "Total Capacity (MW)"
    elif metric == 'count':
        value_col = "COUNT(*) as value"
        title_suffix = "Project Count"
    else:  # avg_size
        value_col = "AVG(capacity_mw) as value"
        title_suffix = "Average Project Size (MW)"
    
    query = f"""
        SELECT 
            {group_by}, 
            {value_col}
        FROM 
            solar_projects
        GROUP BY 
            {group_by}
        ORDER BY 
            value DESC
        LIMIT 20
    """
    
    # Execute query
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        return html.Div("No data available for the selected criteria.")
    
    # Create appropriate chart
    if chart_type == 'bar':
        fig = px.bar(
            df, 
            x=group_by, 
            y='value',
            title=f"{title_suffix} by {group_by.replace('_', ' ').title()}",
            labels={group_by: group_by.replace('_', ' ').title(), 'value': title_suffix}
        )
    elif chart_type == 'pie':
        fig = px.pie(
            df, 
            values='value', 
            names=group_by,
            title=f"{title_suffix} by {group_by.replace('_', ' ').title()}"
        )
    else:  # line chart
        # Sort by the group_by column if it's year for proper chronological order
        if group_by == 'commissioning_year':
            df = df.sort_values(by=group_by)
            
        fig = px.line(
            df, 
            x=group_by, 
            y='value',
            title=f"{title_suffix} by {group_by.replace('_', ' ').title()}",
            labels={group_by: group_by.replace('_', ' ').title(), 'value': title_suffix}
        )
    
    # Return the chart
    return dcc.Graph(figure=fig)