from typing import Dict, List, Any, Optional, Tuple
import re
import numpy as np
from geopy.distance import geodesic
import pandas as pd
from fuzzywuzzy import fuzz

from storage.database import DatabaseManager


class EntityMatcher:
    """
    Matches solar project entities across different data sources to avoid duplication
    and merge information from multiple sources.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the entity matcher with a database connection"""
        self.db_manager = db_manager
        
    def preprocess_name(self, name: str) -> str:
        """Preprocess project name for better matching"""
        if not name:
            return ""
        
        # Convert to lowercase
        name = name.lower()
        
        # Remove special characters
        name = re.sub(r'[^\w\s]', ' ', name)
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove common words that don't help with matching
        stopwords = ['solar', 'power', 'energy', 'plant', 'project', 'pvt', 'ltd', 'limited']
        name_words = name.split()
        filtered_words = [word for word in name_words if word not in stopwords]
        
        return ' '.join(filtered_words)
    
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two project names"""
        if not name1 or not name2:
            return 0.0
            
        # Preprocess names
        proc_name1 = self.preprocess_name(name1)
        proc_name2 = self.preprocess_name(name2)
        
        if not proc_name1 or not proc_name2:
            return 0.0
            
        # Use token sort ratio to handle word order differences
        return fuzz.token_sort_ratio(proc_name1, proc_name2) / 100.0
    
    def calculate_location_similarity(self, 
                                     lat1: Optional[float], 
                                     lon1: Optional[float],
                                     lat2: Optional[float], 
                                     lon2: Optional[float]) -> float:
        """Calculate similarity based on geographical location"""
        # If any coordinates are missing, we can't compare
        if None in [lat1, lon1, lat2, lon2]:
            return 0.0
            
        try:
            # Calculate distance in kilometers
            distance = geodesic((lat1, lon1), (lat2, lon2)).kilometers
            
            # Convert distance to similarity score (0-1)
            # Projects within 1km get high similarity, decreasing as distance increases
            # Maximum meaningful distance is considered 50km
            if distance < 1:
                return 1.0
            elif distance > 50:
                return 0.0
            else:
                # Linear decay from 1km (0.9) to 50km (0.0)
                return max(0.0, 0.9 - (0.9 * (distance - 1) / 49))
        except:
            return 0.0
    
    def calculate_capacity_similarity(self, cap1: Optional[float], cap2: Optional[float]) -> float:
        """Calculate similarity based on project capacity"""
        if cap1 is None or cap2 is None:
            return 0.0
            
        # If either capacity is zero, they're not similar
        if cap1 == 0 or cap2 == 0:
            return 0.0
            
        # Calculate the ratio of the smaller to larger capacity
        ratio = min(cap1, cap2) / max(cap1, cap2)
        
        # Projects with very similar capacities get high similarity scores
        if ratio > 0.95:
            return 1.0
        elif ratio > 0.8:
            return 0.8
        elif ratio > 0.5:
            return 0.5
        else:
            return 0.0
    
    def calculate_entity_similarity(self, project1: Dict[str, Any], project2: Dict[str, Any]
                                   ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate overall similarity between two project entities
        
        Returns:
            Tuple containing overall similarity score and component scores
        """
        # Calculate component similarities
        name_sim = self.calculate_name_similarity(project1.get('name'), project2.get('name'))
        
        location_sim = self.calculate_location_similarity(
            project1.get('latitude'), project1.get('longitude'),
            project2.get('latitude'), project2.get('longitude')
        )
        
        capacity_sim = self.calculate_capacity_similarity(
            project1.get('capacity_mw'), project2.get('capacity_mw')
        )
        
        # Additional metadata matching
        developer_sim = 0.0
        if project1.get('developer') and project2.get('developer'):
            developer_sim = self.calculate_name_similarity(
                project1.get('developer'), project2.get('developer')
            )
        
        # Calculate weighted average similarity
        # Weights can be adjusted based on which attributes are most reliable
        weights = {
            'name': 0.4,
            'location': 0.3,
            'capacity': 0.2,
            'developer': 0.1
        }
        
        component_scores = {
            'name': name_sim,
            'location': location_sim,
            'capacity': capacity_sim,
            'developer': developer_sim
        }
        
        # Calculate weighted average
        overall_sim = sum(score * weights[component] 
                          for component, score in component_scores.items())
        
        return overall_sim, component_scores
    
    def find_matching_projects(self, project_data: Dict[str, Any], 
                              threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find existing projects that may match the new project data
        
        Args:
            project_data: New project data to match
            threshold: Minimum similarity score to consider a match
            
        Returns:
            List of potential matches with similarity scores
        """
        # Get candidate projects from database
        # Use basic filters to reduce the number of comparisons
        filters = {}
        
        # Filter by state if available
        if project_data.get('state'):
            filters['state'] = project_data.get('state')
        
        # Filter by approximate capacity range if available
        capacity = project_data.get('capacity_mw')
        if capacity:
            # Set up database manager to fetch by capacity range
            # This would need to be implemented in DatabaseManager
            pass
        
        # Get potential candidates from database
        candidates = self.db_manager.search_solar_projects(filters=filters, limit=200)
        
        # Calculate similarity for each candidate
        matches = []
        for candidate in candidates:
            sim_score, components = self.calculate_entity_similarity(project_data, candidate)
            if sim_score >= threshold:
                matches.append({
                    'project': candidate,
                    'similarity': sim_score,
                    'component_scores': components
                })
        
        # Sort matches by similarity score (descending)
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches
    
    def merge_project_data(self, existing_data: Dict[str, Any], 
                          new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge data from a new source into existing project data
        
        Args:
            existing_data: Existing project data in the database
            new_data: New project data from a new source
            
        Returns:
            Merged project data
        """
        merged_data = existing_data.copy()
        
        # Track sources that contributed to this entity
        existing_sources = existing_data.get('data_sources', '').split(',') if existing_data.get('data_sources') else []
        new_sources = new_data.get('data_sources', '').split(',') if new_data.get('data_sources') else []
        
        all_sources = list(set(existing_sources + new_sources))
        merged_data['data_sources'] = ','.join(filter(None, all_sources))
        
        # For each field, keep the non-null value
        # If both values exist, keep the more detailed or more recent one
        for key, new_value in new_data.items():
            if key == 'id' or key == 'data_sources':
                continue
                
            existing_value = merged_data.get(key)
            
            # If the existing value is empty but new value exists, use the new value
            if (existing_value is None or existing_value == '' or existing_value == 0) and new_value:
                merged_data[key] = new_value
            # If both values exist, use heuristics for specific fields
            elif existing_value and new_value:
                # For dates, use the more precise or more recent one
                if key.endswith('_date'):
                    # Logic for comparing dates would go here
                    pass
                # For numerical values like capacity, use the more precise one if they're close
                if key in ['capacity_mw', 'average_annual_generation_mwh', 'capacity_utilization_factor']:
                    # If values are within 5% of each other, prefer the one with more decimal precision
                    if abs(existing_value - new_value) / max(existing_value, new_value) < 0.05:
                        # Choose the value with more decimal precision
                        str_existing = str(existing_value)
                        str_new = str(new_value)
                        merged_data[key] = new_value if len(str_new.split('.')[-1]) > len(str_existing.split('.')[-1]) else existing_value
                # For text fields, prefer the longer description which likely has more information
                elif isinstance(existing_value, str) and isinstance(new_value, str):
                    merged_data[key] = new_value if len(new_value) > len(existing_value) else existing_value
        
        # Update the last_updated field to today
        merged_data['last_updated'] = datetime.date.today()
        
        return merged_data
    
    def process_new_project(self, project_data: Dict[str, Any], 
                           similarity_threshold: float = 0.75,
                           auto_merge_threshold: float = 0.9) -> Dict[str, Any]:
        """
        Process a new project by finding matches and merging or creating as appropriate
        
        Args:
            project_data: New project data
            similarity_threshold: Threshold to consider as a potential match
            auto_merge_threshold: Threshold above which to automatically merge
            
        Returns:
            Dict with processing result and relevant information
        """
        # Find potential matches
        matches = self.find_matching_projects(project_data, threshold=similarity_threshold)
        
        # No matches found, create new project
        if not matches:
            project_id = self.db_manager.add_solar_project(project_data)
            return {
                'action': 'created',
                'project_id': project_id,
                'matches': []
            }
        
        # Check if we have a very high confidence match for auto-merging
        best_match = matches[0]
        if best_match['similarity'] >= auto_merge_threshold:
            # Auto-merge with the best match
            merged_data = self.merge_project_data(best_match['project'], project_data)
            self.db_manager.update_solar_project(best_match['project']['id'], merged_data)
            return {
                'action': 'merged',
                'project_id': best_match['project']['id'],
                'matches': [best_match],
                'merged_data': merged_data
            }
        
        # Otherwise, return matches for manual review
        return {
            'action': 'review_required',
            'matches': matches,
            'new_data': project_data
        }


# Add missing import at the top
import datetime