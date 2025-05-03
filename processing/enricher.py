import pandas as pd
import geopandas as gpd
import numpy as np
import logging
import requests
import json
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime
from scrapers.satellite_scraper import SatelliteScraper

class DataEnricher:
    """
    Enriches solar project data with additional information from various sources:
    - Weather and irradiance data
    - Grid infrastructure proximity
    - Satellite imagery analysis
    - Socioeconomic indicators
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the data enricher.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        self.satellite_scraper = SatelliteScraper(
            api_key=config.get('satellite_api_key') if config else None
        )
        
        # Cache for expensive API calls
        self._irradiance_cache = {}
        self._grid_data_cache = {}
        
    def enrich_projects(self, projects_df: pd.DataFrame) -> pd.DataFrame:
        """
        Main method to enrich a dataframe of solar projects with additional data.
        
        Args:
            projects_df: DataFrame containing solar projects
            
        Returns:
            Enriched DataFrame with additional columns
        """
        self.logger.info(f"Enriching {len(projects_df)} solar projects with additional data")
        
        # Create a copy to avoid modifying the original
        enriched_df = projects_df.copy()
        
        # Add solar resource data (GHI, DNI, etc.)
        enriched_df = self.add_solar_resource_data(enriched_df)
        
        # Add grid proximity data
        enriched_df = self.add_grid_proximity_data(enriched_df)
        
        # Add satellite imagery verification
        enriched_df = self.add_satellite_verification(enriched_df)
        
        # Add regional socioeconomic indicators
        enriched_df = self.add_socioeconomic_data(enriched_df)
        
        # Add performance estimation
        enriched_df = self.add_performance_estimation(enriched_df)
        
        self.logger.info("Enrichment complete")
        return enriched_df
    
    def add_solar_resource_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add solar resource data (irradiance) to projects.
        
        Args:
            df: Projects DataFrame with latitude and longitude columns
            
        Returns:
            DataFrame with added solar resource columns
        """
        self.logger.info("Adding solar resource data")
        
        # Create new columns for solar resource data
        df['annual_ghi_kwh_m2'] = None
        df['annual_dni_kwh_m2'] = None
        df['optimal_tilt'] = None
        
        # Process each row
        for idx, row in df.iterrows():
            if pd.isna(row['latitude']) or pd.isna(row['longitude']):
                continue
                
            # Check cache first
            cache_key = f"{row['latitude']:.3f}_{row['longitude']:.3f}"
            if cache_key in self._irradiance_cache:
                resource_data = self._irradiance_cache[cache_key]
            else:
                # Get solar potential data
                resource_data = self.satellite_scraper.estimate_solar_potential(
                    row['latitude'], row['longitude']
                )
                # Store in cache
                self._irradiance_cache[cache_key] = resource_data
            
            # Update DataFrame with retrieved values
            df.at[idx, 'annual_ghi_kwh_m2'] = resource_data['annual']['ghi_kwh_m2']
            df.at[idx, 'annual_dni_kwh_m2'] = resource_data['annual']['dni_kwh_m2']
            df.at[idx, 'optimal_tilt'] = resource_data['optimal_tilt']
            df.at[idx, 'estimated_capacity_factor'] = resource_data['performance']['capacity_factor']
            
        return df
    
    def add_grid_proximity_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add data about proximity to transmission infrastructure.
        
        Args:
            df: Projects DataFrame with latitude and longitude columns
            
        Returns:
            DataFrame with added grid proximity columns
        """
        self.logger.info("Adding grid proximity data")
        
        # Add grid proximity columns
        df['distance_to_substation_km'] = None
        df['substation_voltage_kv'] = None
        df['distance_to_transmission_km'] = None
        
        # Define typical substation locations for simulation
        # In a real implementation, this would use actual grid infrastructure data
        substations = [
            {"lat": 28.6139, "lon": 77.2090, "voltage": 400, "name": "Delhi Substation"},
            {"lat": 19.0760, "lon": 72.8777, "voltage": 220, "name": "Mumbai Substation"},
            {"lat": 12.9716, "lon": 77.5946, "voltage": 400, "name": "Bangalore Substation"},
            {"lat": 17.3850, "lon": 78.4867, "voltage": 220, "name": "Hyderabad Substation"},
            {"lat": 13.0827, "lon": 80.2707, "voltage": 400, "name": "Chennai Substation"},
            {"lat": 22.5726, "lon": 88.3639, "voltage": 220, "name": "Kolkata Substation"},
            {"lat": 23.2599, "lon": 77.4126, "voltage": 132, "name": "Bhopal Substation"},
            {"lat": 26.9124, "lon": 75.7873, "voltage": 220, "name": "Jaipur Substation"},
            {"lat": 21.1702, "lon": 72.8311, "voltage": 400, "name": "Surat Substation"},
            {"lat": 23.0225, "lon": 72.5714, "voltage": 220, "name": "Ahmedabad Substation"}
        ]
        
        # Process each row
        for idx, row in df.iterrows():
            if pd.isna(row['latitude']) or pd.isna(row['longitude']):
                continue
                
            # Find nearest substation
            min_distance = float('inf')
            nearest_substation = None
            
            for substation in substations:
                # Calculate distance (simplified using Euclidean for demo)
                # In production, use haversine formula
                dlat = substation["lat"] - row['latitude']
                dlon = substation["lon"] - row['longitude']
                distance = np.sqrt(dlat**2 + dlon**2) * 111  # Rough km conversion
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_substation = substation
            
            # Add simulated distance to transmission line (slightly less than substation)
            trans_distance = min_distance * np.random.uniform(0.5, 0.9)
            
            # Update DataFrame
            df.at[idx, 'distance_to_substation_km'] = min_distance
            df.at[idx, 'nearest_substation'] = nearest_substation['name'] if nearest_substation else None
            df.at[idx, 'substation_voltage_kv'] = nearest_substation['voltage'] if nearest_substation else None
            df.at[idx, 'distance_to_transmission_km'] = trans_distance
        
        return df
    
    def add_satellite_verification(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Verify solar projects using satellite imagery and add verification metrics.
        
        Args:
            df: Projects DataFrame with latitude and longitude columns
            
        Returns:
            DataFrame with added satellite verification columns
        """
        self.logger.info("Adding satellite imagery verification")
        
        # Add verification columns
        df['satellite_verified'] = False
        df['satellite_verification_date'] = None
        df['satellite_estimated_area_sqm'] = None
        df['satellite_image_path'] = None
        
        # Process each row
        for idx, row in df.iterrows():
            if pd.isna(row['latitude']) or pd.isna(row['longitude']):
                continue
            
            try:
                # Download satellite image for the location
                image_path = self.satellite_scraper.download_satellite_image(
                    row['latitude'], row['longitude'], radius_km=2.0
                )
                
                if image_path:
                    # Detect solar arrays in the image
                    detections = self.satellite_scraper.detect_solar_arrays(image_path)
                    
                    # If any detections found, mark as verified
                    if detections:
                        # Use the largest detection if multiple found
                        largest_detection = max(detections, key=lambda x: x['area_sqm'])
                        
                        df.at[idx, 'satellite_verified'] = True
                        df.at[idx, 'satellite_verification_date'] = datetime.now().strftime('%Y-%m-%d')
                        df.at[idx, 'satellite_estimated_area_sqm'] = largest_detection['area_sqm']
                        df.at[idx, 'satellite_image_path'] = image_path
                        
                        # If capacity was missing, estimate from area
                        if pd.isna(row['capacity_mw']) and 'estimated_capacity_mw' in largest_detection:
                            df.at[idx, 'estimated_capacity_mw'] = largest_detection['estimated_capacity_mw']
                
            except Exception as e:
                self.logger.error(f"Error in satellite verification for project {idx}: {e}")
        
        return df
    
    def add_socioeconomic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add socioeconomic indicators for the region where projects are located.
        
        Args:
            df: Projects DataFrame with state column
            
        Returns:
            DataFrame with added socioeconomic columns
        """
        self.logger.info("Adding socioeconomic data")
        
        # Sample socioeconomic data for Indian states (fictional data for demonstration)
        state_data = {
            "Tamil Nadu": {
                "population": 72147030,
                "electrification_rate": 99.3,
                "gdp_per_capita_inr": 154307,
                "renewable_policy_score": 8.5
            },
            "Gujarat": {
                "population": 60439692,
                "electrification_rate": 99.9,
                "gdp_per_capita_inr": 174652,
                "renewable_policy_score": 9.0
            },
            "Rajasthan": {
                "population": 68548437,
                "electrification_rate": 91.5,
                "gdp_per_capita_inr": 119097,
                "renewable_policy_score": 8.0
            },
            "Karnataka": {
                "population": 61095297,
                "electrification_rate": 98.8,
                "gdp_per_capita_inr": 207062,
                "renewable_policy_score": 8.7
            },
            "Maharashtra": {
                "population": 112374333,
                "electrification_rate": 99.0,
                "gdp_per_capita_inr": 191736,
                "renewable_policy_score": 7.8
            },
            "Andhra Pradesh": {
                "population": 49577103,
                "electrification_rate": 99.2,
                "gdp_per_capita_inr": 142054,
                "renewable_policy_score": 8.3
            },
            "Telangana": {
                "population": 35193978,
                "electrification_rate": 98.0,
                "gdp_per_capita_inr": 228216,
                "renewable_policy_score": 7.5
            }
        }
        
        # Add socioeconomic columns
        df['state_population'] = None
        df['state_electrification_rate'] = None
        df['state_gdp_per_capita_inr'] = None
        df['state_renewable_policy_score'] = None
        
        # Fill in values based on state
        for idx, row in df.iterrows():
            if pd.isna(row.get('state')):
                continue
                
            state = row['state']
            if state in state_data:
                for key, value in state_data[state].items():
                    df.at[idx, f'state_{key}'] = value
        
        return df
    
    def add_performance_estimation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add performance estimation for projects based on available data.
        
        Args:
            df: Projects DataFrame with capacity and irradiance data
            
        Returns:
            DataFrame with added performance columns
        """
        self.logger.info("Adding performance estimates")
        
        # Create performance columns
        df['estimated_annual_generation_mwh'] = None
        df['estimated_capacity_factor'] = df.get('estimated_capacity_factor', None)
        df['estimated_co2_offset_tons'] = None
        
        # Calculate for each project
        for idx, row in df.iterrows():
            # Skip if we don't have capacity data
            if pd.isna(row.get('capacity_mw')):
                continue
                
            # Get or estimate capacity factor
            if pd.isna(row.get('estimated_capacity_factor')):
                # If we have irradiance data, use that for capacity factor estimate
                if not pd.isna(row.get('annual_ghi_kwh_m2')):
                    # Simplified model: CF = GHI / 2200 * 0.17
                    cap_factor = (row['annual_ghi_kwh_m2'] / 2200) * 0.17
                    df.at[idx, 'estimated_capacity_factor'] = cap_factor
                else:
                    # Default capacity factor by technology if available
                    if row.get('technology_type') == 'mono_crystalline':
                        df.at[idx, 'estimated_capacity_factor'] = 0.19
                    elif row.get('technology_type') == 'poly_crystalline':
                        df.at[idx, 'estimated_capacity_factor'] = 0.18
                    elif row.get('technology_type') == 'thin_film':
                        df.at[idx, 'estimated_capacity_factor'] = 0.17
                    else:
                        # Average for India
                        df.at[idx, 'estimated_capacity_factor'] = 0.18
            
            # Calculate annual generation
            cap_factor = df.at[idx, 'estimated_capacity_factor']
            capacity = row['capacity_mw']
            annual_gen = capacity * cap_factor * 8760  # MWh
            df.at[idx, 'estimated_annual_generation_mwh'] = annual_gen
            
            # Calculate CO2 offset (0.82 tons CO2 per MWh in India's grid)
            df.at[idx, 'estimated_co2_offset_tons'] = annual_gen * 0.82
        
        return df