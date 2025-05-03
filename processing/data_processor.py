"""
Data processor to clean, merge, and standardize data from various sources.
"""

import os
import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import re

from utility_func import setup_logger, clean_text, standardize_date

class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.raw_data_dir = config['paths']['raw_data']
        self.processed_dir = config['paths']['processed_data']
        self.output_dir = config['paths']['output_data']
        
        # Create necessary directories
        for dir_path in [self.processed_dir, self.output_dir]:
            os.makedirs(dir_path, exist_ok=True)
            
        self.logger = setup_logger('data_processor', config['paths']['logs'])
        
        # Initialize geocoder with application name
        self.geolocator = Nominatim(user_agent="solar_detective_app")
        
        # Load state and district mapping
        self.india_states = self._load_state_mapping()
        
        # Threshold for considering projects as duplicates
        self.duplicate_threshold_km = config.get('processing', {}).get('duplicate_threshold_km', 1.0)

    def process(self):
        """Main processing method to clean and merge all data sources"""
        self.logger.info("Starting data processing")
        
        # Load data from all sources
        mnre_data = self._load_data('mnre')
        seci_data = self._load_data('seci')
        posoco_data = self._load_data('posoco')
        pdf_data = self._load_data('pdf')
        news_data = self._load_data('news')
        
        # Clean and standardize each dataset
        mnre_clean = self._clean_mnre_data(mnre_data)
        seci_clean = self._clean_seci_data(seci_data)
        pdf_clean = self._clean_pdf_data(pdf_data)
        news_clean = self._clean_news_data(news_data)
        
        # Merge all datasets
        merged_df = self._merge_datasets([
            mnre_clean, 
            seci_clean, 
            pdf_clean, 
            news_clean
        ])
        
        # Enrich with location data (geocoding)
        enriched_df = self._enrich_with_location(merged_df)
        
        # Deduplicate projects
        final_df = self._deduplicate_projects(enriched_df)
        
        # Add grid connectivity data if available
        if posoco_data is not None:
            final_df = self._add_grid_data(final_df, posoco_data)
        
        # Save the processed dataset
        output_path = os.path.join(self.output_dir, 'india_solar_projects.csv')
        final_df.to_csv(output_path, index=False)
        
        # Save as JSON for the dashboard
        json_path = os.path.join(self.output_dir, 'india_solar_projects.json')
        final_df.to_json(json_path, orient='records')
        
        self.logger.info(f"Data processing complete. Saved {len(final_df)} projects to {output_path}")
        
        return final_df

    def _load_data(self, source_name):
        """Load data from a specific source"""
        try:
            if source_name == 'pdf':
                pdf_dir = os.path.join(self.processed_dir, 'pdf_extracted')
                file_path = os.path.join(pdf_dir, 'extracted_solar_projects.csv')
            elif source_name == 'news':
                file_path = os.path.join(self.raw_data_dir, 'news', 'news_extracted_projects.csv')
            else:
                # For MNRE, SECI, POSOCO
                source_dir = os.path.join(self.raw_data_dir, source_name)
                
                # Find the newest CSV file in the directory
                csv_files = [f for f in os.listdir(source_dir) if f.endswith('.csv')]
                if not csv_files:
                    self.logger.warning(f"No CSV files found for {source_name}")
                    return None
                    
                # Use the most recent file
                newest_file = sorted(csv_files)[-1]  # Simple sorting by name
                file_path = os.path.join(source_dir, newest_file)
            
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                self.logger.info(f"Loaded {len(df)} records from {source_name}")
                return df
            else:
                self.logger.warning(f"File not found: {file_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error loading data from {source_name}: {str(e)}")
            return None

    def _clean_mnre_data(self, df):
        """Clean and standardize MNRE data"""
        if df is None or df.empty:
            self.logger.warning("No MNRE data to clean")
            return pd.DataFrame()
            
        try:
            # Make a copy to avoid modifying the original
            clean_df = df.copy()
            
            # Add source column
            clean_df['data_source'] = 'MNRE'
            
            # Rename columns to standard names
            column_mapping = {
                'project_name': 'project_name',
                'capacity': 'capacity',
                'capacity_mw': 'capacity_mw',
                'state': 'state',
                'district': 'district',
                'developer': 'developer',
                'commissioning_date': 'commissioning_date'
            }
            
            # Rename columns that exist in the dataframe
            existing_columns = [col for col in column_mapping.keys() if col in clean_df.columns]
            clean_df = clean_df.rename(columns={col: column_mapping[col] for col in existing_columns})
            
            # Ensure capacity_mw is numeric
            if 'capacity_mw' not in clean_df.columns and 'capacity' in clean_df.columns:
                # Try to extract capacity in MW from capacity column
                clean_df['capacity_mw'] = clean_df['capacity'].apply(self._extract_capacity)
            
            # Standardize state names
            if 'state' in clean_df.columns:
                clean_df['state'] = clean_df['state'].apply(lambda x: self._standardize_state(x) if pd.notna(x) else x)
            
            # Standardize dates
            if 'commissioning_date' in clean_df.columns:
                clean_df['commissioning_date'] = clean_df['commissioning_date'].apply(
                    lambda x: standardize_date(x) if pd.notna(x) else x
                )
                
            # Create location string for geocoding
            clean_df['location_string'] = self._create_location_string(clean_df)
            
            return clean_df
            
        except Exception as e:
            self.logger.error(f"Error cleaning MNRE data: {str(e)}")
            return pd.DataFrame()

    def _clean_seci_data(self, df):
        """Clean and standardize SECI data"""
        if df is None or df.empty:
            self.logger.warning("No SECI data to clean")
            return pd.DataFrame()
            
        try:
            # Similar structure to _clean_mnre_data
            clean_df = df.copy()
            clean_df['data_source'] = 'SECI'
            
            # Rename columns to standard names
            column_mapping = {
                'project_name': 'project_name',
                'capacity_mw': 'capacity_mw',
                'state': 'state',
                'developer': 'developer',
                'commissioning_date': 'commissioning_date',
                'ppa_tariff': 'tariff_inr_kwh',
                'status': 'status'
            }
            
            existing_columns = [col for col in column_mapping.keys() if col in clean_df.columns]
            clean_df = clean_df.rename(columns={col: column_mapping[col] for col in existing_columns})
            
            # Process specific to SECI data
            if 'capacity_mw' not in clean_df.columns and 'capacity' in clean_df.columns:
                clean_df['capacity_mw'] = clean_df['capacity'].apply(self._extract_capacity)
            
            if 'state' in clean_df.columns:
                clean_df['state'] = clean_df['state'].apply(lambda x: self._standardize_state(x) if pd.notna(x) else x)
            
            if 'commissioning_date' in clean_df.columns:
                clean_df['commissioning_date'] = clean_df['commissioning_date'].apply(
                    lambda x: standardize_date(x) if pd.notna(x) else x
                )
                
            clean_df['location_string'] = self._create_location_string(clean_df)
            
            return clean_df
            
        except Exception as e:
            self.logger.error(f"Error cleaning SECI data: {str(e)}")
            return pd.DataFrame()

    def _clean_pdf_data(self, df):
        """Clean and standardize data extracted from PDFs"""
        if df is None or df.empty:
            self.logger.warning("No PDF data to clean")
            return pd.DataFrame()
            
        try:
            clean_df = df.copy()
            clean_df['data_source'] = 'Company Reports'
            
            # Ensure capacity_mw is numeric
            if 'capacity_mw' not in clean_df.columns and 'capacity' in clean_df.columns:
                clean_df['capacity_mw'] = clean_df['capacity'].apply(self._extract_capacity)
            
            # Standardize location information
            if 'location' in clean_df.columns:
                # Extract state from location if state not present
                if 'state' not in clean_df.columns:
                    clean_df['state'] = clean_df['location'].apply(self._extract_state_from_location)
                # Create a district column if not present
                if 'district' not in clean_df.columns:
                    clean_df['district'] = clean_df['location'].apply(self._extract_district_from_location)
            
            # Standardize state names
            if 'state' in clean_df.columns:
                clean_df['state'] = clean_df['state'].apply(lambda x: self._standardize_state(x) if pd.notna(x) else x)
            
            # Standardize dates
            if 'commissioning_date' in clean_df.columns:
                clean_df['commissioning_date'] = clean_df['commissioning_date'].apply(
                    lambda x: standardize_date(x) if pd.notna(x) else x
                )
                
            clean_df['location_string'] = self._create_location_string(clean_df)
            
            return clean_df
            
        except Exception as e:
            self.logger.error(f"Error cleaning PDF data: {str(e)}")
            return pd.DataFrame()

    def _clean_news_data(self, df):
        """Clean and standardize data extracted from news articles"""
        if df is None or df.empty:
            self.logger.warning("No news data to clean")
            return pd.DataFrame()
            
        try:
            clean_df = df.copy()
            clean_df['data_source'] = 'News Articles'
            
            # News data often requires more cleaning
            if 'capacity_mw' not in clean_df.columns and 'capacity' in clean_df.columns:
                clean_df['capacity_mw'] = clean_df['capacity'].apply(self._extract_capacity)
            
            # Extract location information
            if 'location' in clean_df.columns:
                if 'state' not in clean_df.columns:
                    clean_df['state'] = clean_df['location'].apply(self._extract_state_from_location)
                if 'district' not in clean_df.columns:
                    clean_df['district'] = clean_df['location'].apply(self._extract_district_from_location)
            
            # Standardize state names
            if 'state' in clean_df.columns:
                clean_df['state'] = clean_df['state'].apply(lambda x: self._standardize_state(x) if pd.notna(x) else x)
            
            # Create project name if not available
            if 'project_name' not in clean_df.columns:
                clean_df['project_name'] = clean_df.apply(
                    lambda row: self._generate_project_name(row), axis=1
                )
            
            # Standardize dates
            if 'commissioning_date' in clean_df.columns:
                clean_df['commissioning_date'] = clean_df['commissioning_date'].apply(
                    lambda x: standardize_date(x) if pd.notna(x) else x
                )
                
            # Create location string for geocoding
            clean_df['location_string'] = self._create_location_string(clean_df)
            
            # Add article URL as reference
            if 'url' in clean_df.columns:
                clean_df['reference'] = clean_df['url']
            
            return clean_df
            
        except Exception as e:
            self.logger.error(f"Error cleaning news data: {str(e)}")
            return pd.DataFrame()

    def _merge_datasets(self, dataframes):
        """Merge multiple cleaned datasets into a single dataframe"""
        # Filter out empty dataframes
        valid_dfs = [df for df in dataframes if df is not None and not df.empty]
        
        if not valid_dfs:
            self.logger.warning("No valid dataframes to merge")
            return pd.DataFrame()
            
        try:
            # Identify common columns to use for the merged dataset
            base_columns = self._get_common_columns(valid_dfs)
            
            # Initialize with the first dataframe
            merged_df = valid_dfs[0].copy()
            
            # Add each subsequent dataframe
            for i, df in enumerate(valid_dfs[1:], 1):
                self.logger.info(f"Merging dataframe {i+1} with {len(df)} records")
                merged_df = pd.concat([merged_df, df], ignore_index=True, sort=False)
            
            # Ensure all necessary columns exist
            for col in base_columns:
                if col not in merged_df.columns:
                    merged_df[col] = np.nan
            
            self.logger.info(f"Merged dataset contains {len(merged_df)} records")
            return merged_df
            
        except Exception as e:
            self.logger.error(f"Error merging datasets: {str(e)}")
            return pd.DataFrame()

    def _get_common_columns(self, dataframes):
        """Identify common columns across dataframes for standardization"""
        # Essential columns that should exist in the final dataset
        essential_columns = [
            'project_name', 'capacity_mw', 'state', 'district', 'developer', 
            'commissioning_date', 'data_source', 'location_string'
        ]
        
        # Find columns that actually exist in at least one dataframe
        all_columns = set()
        for df in dataframes:
            all_columns.update(df.columns)
            
        # Ensure essential columns are included
        return list(all_columns.union(essential_columns))

    def _enrich_with_location(self, df):
        """Add geographical coordinates using geocoding"""
        if df is None or df.empty:
            return df
            
        try:
            # Create a copy to avoid modifying the original
            enriched_df = df.copy()
            
            # Add lat/lon columns if they don't exist
            if 'latitude' not in enriched_df.columns:
                enriched_df['latitude'] = np.nan
            if 'longitude' not in enriched_df.columns:
                enriched_df['longitude'] = np.nan
                
            # Count rows needing geocoding
            missing_coords = enriched_df[
                (enriched_df['latitude'].isna() | enriched_df['longitude'].isna()) & 
                enriched_df['location_string'].notna()
            ]
            
            self.logger.info(f"Geocoding {len(missing_coords)} locations")
            
            # Process in batches to avoid overwhelming the geocoding service
            batch_size = 50
            for i in range(0, len(missing_coords), batch_size):
                batch = missing_coords.iloc[i:i+batch_size]
                
                for idx, row in batch.iterrows():
                    if pd.notna(row['location_string']):
                        try:
                            # Get coordinates
                            lat, lon = self._geocode_location(row['location_string'])
                            if lat and lon:
                                enriched_df.at[idx, 'latitude'] = lat
                                enriched_df.at[idx, 'longitude'] = lon
                                
                            # Respect rate limits
                            time.sleep(1)
                            
                        except Exception as e:
                            self.logger.error(f"Error geocoding {row['location_string']}: {str(e)}")
                
                self.logger.info(f"Geocoded batch {i//batch_size + 1}")
            
            # Calculate how many locations were successfully geocoded
            geocoded_count = enriched_df[enriched_df['latitude'].notna() & enriched_df['longitude'].notna()].shape[0]
            self.logger.info(f"Successfully geocoded {geocoded_count} locations")
            
            return enriched_df
            
        except Exception as e:
            self.logger.error(f"Error enriching with location data: {str(e)}")
            return df

    def _geocode_location(self, location_string):
        """Geocode a location string to get latitude and longitude"""
        if not location_string or pd.isna(location_string):
            return None, None
        
        # Add 'India' to the location string if not present
        if 'india' not in location_string.lower():
            search_string = f"{location_string}, India"
        else:
            search_string = location_string
            
        try:
            # Try to geocode the location
            location = self.geolocator.geocode(search_string, timeout=10)
            
            if location:
                return location.latitude, location.longitude
            else:
                # If failed, try with just the state
                state_match = re.search(r'([A-Za-z\s]+)(?:,|$)', location_string)
                if state_match:
                    state = state_match.group(1).strip()
                    location = self.geolocator.geocode(f"{state}, India", timeout=10)
                    if location:
                        return location.latitude, location.longitude
                        
            return None, None
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            self.logger.warning(f"Geocoding error for '{location_string}': {str(e)}")
            time.sleep(2)  # Back off a bit
            return None, None

    def _deduplicate_projects(self, df):
        """Identify and merge duplicate project entries"""
        if df is None or df.empty:
            return df
            
        try:
            # Create a copy to avoid modifying the original
            dedup_df = df.copy()
            
            # Sort by data quality (MNRE and SECI data is likely more reliable)
            source_priority = {
                'MNRE': 1, 
                'SECI': 2, 
                'Company Reports': 3, 
                'News Articles': 4
            }
            
            # Add source priority column
            dedup_df['source_priority'] = dedup_df['data_source'].map(
                lambda x: source_priority.get(x, 5)
            )
            
            # Sort by priority and then by how complete the record is
            dedup_df['completeness'] = dedup_df.notna().sum(axis=1)
            dedup_df = dedup_df.sort_values(['source_priority', 'completeness'], 
                                           ascending=[True, False])
            
            # Reset index to ensure proper merging
            dedup_df = dedup_df.reset_index(drop=True)
            
            # Initialize duplicate groups
            dedup_df['duplicate_group'] = np.nan
            next_group = 1
            
            # Find duplicates based on location proximity and similar capacity
            for i, row in dedup_df.iterrows():
                # Skip if already assigned to a group
                if pd.notna(dedup_df.at[i, 'duplicate_group']):
                    continue
                    
                # Assign new group
                dedup_df.at[i, 'duplicate_group'] = next_group
                
                # Check for duplicates
                for j in range(i+1, len(dedup_df)):
                    # Skip if already assigned
                    if pd.notna(dedup_df.at[j, 'duplicate_group']):
                        continue
                        
                    # Check if same project based on criteria
                    if self._are_same_project(row, dedup_df.iloc[j]):
                        dedup_df.at[j, 'duplicate_group'] = next_group
                        
                next_group += 1
                
            # Merge duplicates
            merged_records = []
            for group in range(1, next_group):
                group_records = dedup_df[dedup_df['duplicate_group'] == group]
                if len(group_records) > 0:
                    merged_record = self._merge_duplicate_records(group_records)
                    merged_records.append(merged_record)
                    
            # Create final dataframe
            final_df = pd.DataFrame(merged_records)
            
            # Drop utility columns
            if 'source_priority' in final_df.columns:
                final_df = final_df.drop(columns=['source_priority'])
            if 'completeness' in final_df.columns:
                final_df = final_df.drop(columns=['completeness'])
            if 'duplicate_group' in final_df.columns:
                final_df = final_df.drop(columns=['duplicate_group'])
                
            self.logger.info(f"Deduplication complete. Reduced from {len(df)} to {len(final_df)} records")
            
            return final_df
            
        except Exception as e:
            self.logger.error(f"Error during deduplication: {str(e)}")
            return df

    def _are_same_project(self, row1, row2):
        """Determine if two records refer to the same project"""
        # Projects are the same if they have similar capacity and are close geographically
        
        # Check capacity similarity (within 10%)
        capacity_match = False
        if pd.notna(row1['capacity_mw']) and pd.notna(row2['capacity_mw']):
            capacity1 = float(row1['capacity_mw'])
            capacity2 = float(row2['capacity_mw'])
            
            # Calculate percentage difference
            if capacity1 > 0 and capacity2 > 0:
                diff_pct = abs(capacity1 - capacity2) / max(capacity1, capacity2)
                capacity_match = diff_pct <= 0.1  # Within 10%
        
        # Check geographical proximity
        location_match = False
        if (pd.notna(row1['latitude']) and pd.notna(row1['longitude']) and 
            pd.notna(row2['latitude']) and pd.notna(row2['longitude'])):
            
            # Calculate distance in km
            distance = self._haversine_distance(
                row1['latitude'], row1['longitude'],
                row2['latitude'], row2['longitude']
            )
            
            location_match = distance <= self.duplicate_threshold_km
        
        # Alternative: match on project name and developer
        name_match = False
        if pd.notna(row1['project_name']) and pd.notna(row2['project_name']):
            # Normalize names for comparison
            name1 = re.sub(r'[^a-zA-Z0-9]', '', row1['project_name'].lower())
            name2 = re.sub(r'[^a-zA-Z0-9]', '', row2['project_name'].lower())
            
            # Check for similarity
            name_match = (name1 == name2) or name1 in name2 or name2 in name1
            
            # If names match, also check developer if available
            if name_match and pd.notna(row1['developer']) and pd.notna(row2['developer']):
                dev1 = re.sub(r'[^a-zA-Z0-9]', '', row1['developer'].lower())
                dev2 = re.sub(r'[^a-zA-Z0-9]', '', row2['developer'].lower())
                
                dev_match = (dev1 == dev2) or dev1 in dev2 or dev2 in dev1
                name_match = name_match and dev_match
        
        # Return true if projects match by either criteria
        return (capacity_match and location_match) or name_match

    def _merge_duplicate_records(self, group_df):
        """Merge duplicate records into a single record with best available data"""
        # Start with the first record (highest priority)
        merged = group_df.iloc[0].to_dict()
        
        # For each field, take the first non-null value
        for col in group_df.columns:
            if col in ['source_priority', 'completeness', 'duplicate_group']:
                continue
                
            if pd.isna(merged[col]):
                # Find first non-null value
                non_null = group_df[group_df[col].notna()]
                if not non_null.empty:
                    merged[col] = non_null.iloc[0][col]
        
        # Special handling for data_source - combine all sources
        sources = group_df['data_source'].unique()
        merged['data_source'] = ', '.join(sources)
        
        # Handle references - combine all
        if 'reference' in group_df.columns:
            refs = group_df['reference'].dropna().unique()
            merged['reference'] = '; '.join(str(r) for r in refs if pd.notna(r))
            
        return merged

    def _add_grid_data(self, df, grid_df):
        """Add grid connectivity information to projects"""
        if df is None or df.empty or grid_df is None or grid_df.empty:
            return df
            
        try:
            # Create a copy to avoid modifying the original
            result_df = df.copy()
            
            # Add grid columns if they don't exist
            grid_columns = ['substation', 'voltage_level', 'grid_availability_percent']
            for col in grid_columns:
                if col not in result_df.columns:
                    result_df[col] = np.nan
            
            # Match projects to grid data by state
            for idx, row in result_df.iterrows():
                if pd.notna(row['state']):
                    # Find matching grid data for this state
                    state_grid = grid_df[grid_df['state'] == row['state']]
                    
                    if not state_grid.empty:
                        # Find the nearest substation (simplified approach)
                        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                            nearest_idx, distance = self._find_nearest_substation(
                                row, state_grid
                            )
                            
                            if nearest_idx is not None and distance < 50:  # Within 50km
                                nearest = state_grid.iloc[nearest_idx]
                                result_df.at[idx, 'substation'] = nearest['substation']
                                result_df.at[idx, 'voltage_level'] = nearest['voltage_level']
                                result_df.at[idx, 'grid_availability_percent'] = nearest['grid_availability_percent']
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"Error adding grid data: {str(e)}")
            return df

    def _find_nearest_substation(self, project_row, grid_df):
        """Find the nearest substation to a project"""
        # This is a simplified implementation
        # In reality, you would have geocoded substations as well
        
        # Create a dummy implementation that returns the first substation for demonstration
        if not grid_df.empty:
            return 0, 10.0  # Return first substation at 10km distance
        
        return None, float('inf')

    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate the great circle distance between two points in km"""
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        r = 6371  # Radius of earth in kilometers
        
        return c * r

    def _create_location_string(self, df):
        """Create a location string for geocoding from available location data"""
        def make_location(row):
            location_parts = []
            
            # Add specific location if available
            if 'location' in row and pd.notna(row['location']):
                location_parts.append(row['location'])
            elif 'district' in row and pd.notna(row['district']):
                location_parts.append(row['district'])
                
            # Add state
            if 'state' in row and pd.notna(row['state']):
                location_parts.append(row['state'])
                
            # Always add country
            location_parts.append('India')
            
            return ', '.join(location_parts) if location_parts else None
            
        return df.apply(make_location, axis=1)

    def _extract_capacity(self, capacity_str):
        """Extract numeric capacity in MW from string"""
        if pd.isna(capacity_str):
            return np.nan
            
        # Convert to string if not already
        capacity_str = str(capacity_str)
        
        # Extract numeric part
        match = re.search(r'(\d+(?:\.\d+)?)', capacity_str)
        if match:
            capacity_num = float(match.group(1))

            # Continue from where the snippet left off
            capacity_num = float(match.group(1))
            
            # Handle unit conversion (KW to MW)
            if 'kw' in capacity_str.lower() or 'kilowatt' in capacity_str.lower():
                capacity_num /= 1000
                
            return capacity_num
        return np.nan

    def _standardize_state(self, state_name):
        """Standardize state names to canonical form"""
        if pd.isna(state_name):
            return np.nan
            
        # Convert to lowercase for comparison
        state_lower = state_name.lower().strip()
        
        # Check if it matches any standard state name
        for std_state, variants in self.india_states.items():
            if state_lower == std_state.lower() or state_lower in [v.lower() for v in variants]:
                return std_state
                
        # If no match found, return the original with proper capitalization
        return state_name.strip().title()

    def _extract_state_from_location(self, location_text):
        """Extract state name from a location string"""
        if pd.isna(location_text):
            return np.nan
            
        # Convert to string if not already
        location_text = str(location_text)
        
        # Look for known state names in the location text
        for state, variants in self.india_states.items():
            # Check standard name and variants
            all_forms = [state.lower()] + [v.lower() for v in variants]
            
            for form in all_forms:
                if form in location_text.lower():
                    return state
                    
        return np.nan

    def _extract_district_from_location(self, location_text):
        """Extract district name from a location string"""
        if pd.isna(location_text):
            return np.nan
            
        # Basic implementation - extract the first part of a comma-separated location
        parts = str(location_text).split(',')
        if parts:
            # Return the first part that isn't a known state name
            for part in parts:
                part = part.strip()
                is_state = False
                
                for state, variants in self.india_states.items():
                    if (part.lower() == state.lower() or 
                        part.lower() in [v.lower() for v in variants]):
                        is_state = True
                        break
                        
                if not is_state and part:
                    return part.title()
                    
        return np.nan

    def _generate_project_name(self, row):
        """Generate a project name if none exists"""
        parts = []
        
        # Add developer if available
        if 'developer' in row and pd.notna(row['developer']):
            parts.append(row['developer'])
            
        # Add location
        if 'district' in row and pd.notna(row['district']):
            parts.append(row['district'])
        elif 'state' in row and pd.notna(row['state']):
            parts.append(row['state'])
            
        # Add capacity
        if 'capacity_mw' in row and pd.notna(row['capacity_mw']):
            parts.append(f"{row['capacity_mw']}MW")
            
        # Add solar type if available
        if 'project_type' in row and pd.notna(row['project_type']):
            parts.append(row['project_type'])
        else:
            parts.append("Solar Project")
            
        return " ".join(parts)

    def _load_state_mapping(self):
        """Load mapping of state names and their variations"""
        # Standard mapping of Indian states and their variations
        return {
            "Andhra Pradesh": ["AP", "Andhra"],
            "Arunachal Pradesh": ["Arunachal"],
            "Assam": [],
            "Bihar": [],
            "Chhattisgarh": ["Chattisgarh", "CG"],
            "Goa": [],
            "Gujarat": ["GJ"],
            "Haryana": ["HR"],
            "Himachal Pradesh": ["Himachal", "HP"],
            "Jharkhand": [],
            "Karnataka": ["KA"],
            "Kerala": ["KL"],
            "Madhya Pradesh": ["MP"],
            "Maharashtra": ["MH"],
            "Manipur": [],
            "Meghalaya": [],
            "Mizoram": [],
            "Nagaland": [],
            "Odisha": ["Orissa"],
            "Punjab": ["PB"],
            "Rajasthan": ["RJ"],
            "Sikkim": [],
            "Tamil Nadu": ["Tamilnadu", "TN"],
            "Telangana": ["TS"],
            "Tripura": [],
            "Uttar Pradesh": ["UP"],
            "Uttarakhand": ["UK", "Uttaranchal"],
            "West Bengal": ["WB"],
            "Delhi": ["NCT", "Delhi NCR", "New Delhi"],
            "Jammu and Kashmir": ["J&K", "JK"],
            "Ladakh": [],
            "Puducherry": ["Pondicherry"],
            "Andaman and Nicobar Islands": ["Andaman", "Nicobar"],
            "Chandigarh": [],
            "Dadra and Nagar Haveli and Daman and Diu": ["Dadra", "Daman", "Diu"],
            "Lakshadweep": []
        }