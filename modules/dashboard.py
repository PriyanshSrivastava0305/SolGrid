import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

def create_dashboard():
    # Create a SQLAlchemy engine
    engine = create_engine("mysql+mysqlconnector://root:system@localhost/solar_db")

    # Fetch data using pandas
    query = "SELECT name, capacity, location, latitude, longitude FROM projects"
    df = pd.read_sql(query, engine)

    # Drop rows with missing latitude or longitude
    df = df.dropna(subset=["latitude", "longitude"])

    # Create a map visualization
    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="name",
        hover_data=["capacity", "location"],
        zoom=5,
        height=600
    )
    fig.update_layout(mapbox_style="open-street-map")

    # Define the layout
    app = dash.Dash(__name__)
    app.layout = html.Div([
        html.H1("Solar Projects Dashboard"),
        dcc.Graph(figure=fig)
    ])

    # Run the app
    app.run(debug=True)