"""
Main Streamlit application for Solar Detective.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from pathlib import Path

# Configure the page
st.set_page_config(
    page_title="Solar Detective",
    page_icon="🌞",
    layout="wide"
)

# Add title and description
st.title("🌞 Solar Detective")
st.subheader("India's Solar Infrastructure Map")

# Connect to the database
DB_PATH = Path("data/solar_detective.db")
conn = sqlite3.connect(DB_PATH)

# Load the data
projects_df = pd.read_sql("""
    SELECT name, capacity_mw, latitude, longitude, state, 
           project_type, commissioning_year, developer
    FROM solar_projects
""", conn)

# Show key metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Projects", len(projects_df))
with col2:
    st.metric("Total Capacity (MW)", f"{projects_df['capacity_mw'].sum():,.0f}")
with col3:
    st.metric("States Covered", len(projects_df['state'].unique()))

# Create the map
st.subheader("Solar Project Locations")
fig = px.scatter_mapbox(
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
    zoom=4,
    center={"lat": 22, "lon": 82},
    mapbox_style="carto-positron",
    title="Solar Projects in India"
)

fig.update_layout(height=600)
st.plotly_chart(fig, use_container_width=True)

# Show project details
st.subheader("Project Details")
st.dataframe(
    projects_df.sort_values('capacity_mw', ascending=False),
    hide_index=True,
    use_container_width=True
)

# Close the database connection
conn.close()