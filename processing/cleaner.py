import re
import datetime
from typing import Dict, Any, Optional, List, Union
import pandas as pd
import numpy as np


class DataCleaner:
    """
    Cleans and standardizes raw solar project data from various sources
    """
    
    def __init__(self):
        """Initialize the data cleaner with reference data"""
        # State name standardization mapping
        self.state_mapping = {
            "andhra pradesh": "Andhra Pradesh",
            "ap": "Andhra Pradesh",
            "arunachal pradesh": "Arunachal Pradesh",
            "assam": "Assam",
            "bihar": "Bihar",
            "chhattisgarh": "Chhattisgarh",
            "delhi": "Delhi",
            "nct of delhi": "Delhi",
            "nct": "Delhi",
            "goa": "Goa",
            "gujarat": "Gujarat",
            "gj": "Gujarat",
            "haryana": "Haryana",
            "himachal pradesh": "Himachal Pradesh",
            "hp": "Himachal Pradesh",
            "jammu & kashmir": "Jammu & Kashmir",
            "jammu and kashmir": "Jammu & Kashmir",
            "j&k": "Jammu & Kashmir",
            "jk": "Jammu & Kashmir",
            "jharkhand": "Jharkhand",
            "karnataka": "Karnataka",
            "ka": "Karnataka",
            "kerala": "Kerala",
            "kl": "Kerala",
            "madhya pradesh": "Madhya Pradesh",
            "mp": "Madhya Pradesh",
            "maharashtra": "Maharashtra",
            "mh": "Maharashtra",
            "manipur": "Manipur",
            "meghalaya": "Meghalaya",
            "mizoram": "Mizoram",
            "nagaland": "Nagaland",
            "odisha": "Odisha",
            "orissa": "Odisha",
            "punjab": "Punjab",
            "pb": "Punjab",
            "rajasthan": "Rajasthan",
            "rj": "Rajasthan",
            "sikkim": "Sikkim",
            "tamil nadu": "Tamil Nadu",
            "tn": "Tamil Nadu",
            "telangana": "Telangana",
            "ts": "Telangana",
            "tg": "Telangana",
            "tripura": "Tripura",
            "uttarakhand": "Uttarakhand",
            "uttar pradesh": "Uttar Pradesh",
            "up": "Uttar Pradesh",
            "west bengal": "West Bengal",
            "wb": "West Bengal",
            "andaman and nicobar islands": "Andaman & Nicobar Islands",
            "a&n islands": "Andaman & Nicobar Islands",
            "andaman": "Andaman & Nicobar Islands",
            "chandigarh": "Chandigarh",
            "dadra and nagar haveli": "Dadra & Nagar Haveli and Daman & Diu",
            "daman and diu": "Dadra & Nagar Haveli and Daman & Diu",
            "dadra & nagar haveli": "Dadra & Nagar Haveli and Daman & Diu",
            "daman & diu": "Dadra & Nagar Haveli and Daman & Diu",
            "d&nh": "Dadra & Nagar Haveli and Daman & Diu",
            "lakshadweep": "Lakshadweep",
            "pondicherry": "Puducherry",
            "puducherry": "Puducherry",
        }
        
        # Cell technology standardization mapping
        self.cell_tech_mapping = {
            "mono crystalline": "Monocrystalline Silicon",
            "mono-crystalline": "Monocrystalline Silicon",
            "monocrystalline": "Monocrystalline Silicon",
            "mono perc": "Monocrystalline PERC",
            "mono-perc": "Monocrystalline PERC",
            "monocrystalline perc": "Monocrystalline PERC",
            "poly crystalline": "Polycrystalline Silicon",
            "poly-crystalline": "Polycrystalline Silicon",
            "polycrystalline": "Polycrystalline Silicon",
            "multi crystalline": "Polycrystalline Silicon",
            "multi-crystalline": "Polycrystalline Silicon",
            "multicrystalline": "Polycrystalline Silicon",
            "thin film": "Thin Film",
            "thin-film": "Thin Film",
            "cdte": "CdTe Thin Film",
            "cadmium telluride": "CdTe Thin Film",
            "cigs": "CIGS Thin Film",
            "copper indium gallium selenide": "CIGS Thin Film",
            "amorphous silicon": "Amorphous Silicon",
            "a-si": "Amorphous Silicon",
            # Add more mappings as needed
        }
        
        # Project type standardization mapping
        self.project_type_mapping = {
            "ground-mounted": "Utility-scale",
            "ground mounted": "Utility-scale",
            "utility scale": "Utility-scale",
            "utility-scale": "Utility-scale",
            "rooftop": "Rooftop",
            "roof-top": "Rooftop",
            "roof top": "Rooftop",
            "floating": "Floating",
            "floating solar": "Floating",
            "canal top": "Canal-top",
            "canal-top": "Canal-top",
            "hybrid": "Hybrid",
            "solar+storage": "Hybrid",
            "solar + storage": "Hybrid",
            "solar+wind": "Hybrid",
            "solar + wind": "Hybrid",
            # Add more mappings as needed
        }
    
    def clean_project_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and standardize raw project data
        
        Args:
            raw_data: Dictionary containing raw project data
            
        Returns:
            Dict: Cleaned and standardized project data
        """
        cleaned_data = {}
        
        # Clean basic info
        cleaned_data['name'] = self.clean_name(raw_data.get('name', ''))
        cleaned_data['capacity_mw'] = self.clean_capacity(raw_data.get('capacity', raw_data.get('capacity_mw')))
        
        # Clean location data
        location_data = self.clean_location(
            raw_data.get('latitude'), 
            raw_data.get('longitude'),
            raw_data.get('state'),
            raw_data.get('district'),
            raw_data.get('village'),
            raw_data.get('location')
        )
        cleaned_data.update(location_data)
        
        # Clean ownership data
        cleaned_data['developer'] = self.clean_company_name(raw_data.get('developer'))
        cleaned_data['owner'] = self.clean_company_name(raw_data.get('owner'))
        cleaned_data['operator'] = self.clean_company_name(raw_data.get('operator'))
        
        # Clean dates
        cleaned_data['commissioning_date'] = self.clean_date(raw_data.get('commissioning_date'))
        cleaned_data['construction_start_date'] = self.clean_date(raw_data.get('construction_start_date'))
        
        # Clean project type
        project_type_data = self.clean_project_type(
            raw_data.get('project_type'),
            raw_data.get('is_hybrid'),
            raw_data.get('hybrid_type')
        )
        cleaned_data.update(project_type_data)
        
        # Clean technical details
        cleaned_data['cell_technology'] = self.clean_cell_technology(raw_data.get('cell_technology'))
        cleaned_data['is_bifacial'] = self.clean_boolean(raw_data.get('is_bifacial'))
        cleaned_data['module_manufacturer'] = self.clean_company_name(raw_data.get('module_manufacturer'))
        cleaned_data['grid_connection_voltage'] = self.clean_voltage(raw_data.get('grid_connection_voltage'))
        
        # Clean business details
        cleaned_data['ppa_type'] = self.clean_ppa_type(raw_data.get('ppa_type'))
        cleaned_data['ppa_duration_years'] = self.clean_integer(raw_data.get('ppa_duration_years'))
        cleaned_data['ppa_tariff'] = self.clean_float(raw_data.get('ppa_tariff'))
        cleaned_data['offtaker'] = self.clean_company_name(raw_data.get('offtaker'))
        
        # Clean performance metrics
        cleaned_data['average_annual_generation_mwh'] = self.clean_float(raw_data.get('average_annual_generation_mwh'))
        cleaned_data['capacity_utilization_factor'] = self.clean_cuf(raw_data.get('capacity_utilization_factor'))
        
        # Clean environmental data
        cleaned_data['average_irradiance'] = self.clean_float(raw_data.get('average_irradiance'))
        cleaned_data['land_area_acres'] = self.clean_land_area(raw_data.get('land_area'))
        
        # Clean metadata
        cleaned_data['data_sources'] = raw_data.get('data_sources', '')
        cleaned_data['last_updated'] = datetime.date.today()
        cleaned_data['verification_status'] = 'Unverified'
        
        # Remove None values
        cleaned_data = {k: v for k, v in cleaned_data.items() if v is not None}
        
        return cleaned_data
    
    def clean_name(self, name: Optional[str]) -> Optional[str]:
        """Clean and standardize project name"""
        if not name:
            return None
            
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', str(name).strip())
        
        # Capitalize appropriately
        name = name.title()
        
        # Replace 'Pvt Ltd' with 'Pvt. Ltd.' etc.
        name = re.sub(r'Pvt Ltd', 'Pvt. Ltd.', name)
        name = re.sub(r'Pvt\.Ltd\.', 'Pvt. Ltd.', name)
        
        return name
    
    def clean_capacity(self, capacity: Any) -> Optional[float]:
        """Clean and standardize capacity in MW"""
        if capacity is None:
            return None
        
        if isinstance(capacity, (int, float)):
            return float(capacity)
            
        if isinstance(capacity, str):
            # Remove any non-numeric characters except decimal point
            capacity = re.sub(r'[^\d.]', '', capacity)
            try:
                return float(capacity)
            except ValueError:
                return None
                
        return None
    
    def clean_location(self, latitude: Any, longitude: Any, 
                      state: Optional[str] = None, 
                      district: Optional[str] = None,
                      village: Optional[str] = None,
                      location_text: Optional[str] = None) -> Dict[str, Any]:
        """Clean and extract location data"""
        result = {}
        
        # Clean latitude/longitude
        if latitude is not None:
            try:
                result['latitude'] = float(latitude)
            except (ValueError, TypeError):
                # Try to extract latitude from string
                if isinstance(latitude, str):
                    match = re.search(r'(-?\d+\.?\d*)', latitude)
                    if match:
                        result['latitude'] = float(match.group(1))
        
        if longitude is not None:
            try:
                result['longitude'] = float(longitude)
            except (ValueError, TypeError):
                # Try to extract longitude from string
                if isinstance(longitude, str):
                    match = re.search(r'(-?\d+\.?\d*)', longitude)
                    if match:
                        result['longitude'] = float(match.group(1))
        
        # Clean state
        if state:
            state = str(state).strip().lower()
            result['state'] = self.state_mapping.get(state, state.title())
        
        # Clean district and village
        if district:
            result['district'] = str(district).strip().title()
            
        if village:
            result['village'] = str(village).strip().title()
            
        # If location text is provided but no structured location data, try to extract
        if location_text and not (state or district or village):
            # This would be a more complex function to extract location information
            # from unstructured text - simplified version here
            location_text = str(location_text).strip()
            
            # Try to extract state names from the text
            for state_variant, standard_name in self.state_mapping.items():
                if state_variant in location_text.lower():
                    result['state'] = standard_name
                    break
        
        return result
    
    def clean_company_name(self, name: Optional[str]) -> Optional[str]:
        """Clean and standardize company names"""
        if not name:
            return None
            
        # Convert to string, remove extra whitespace
        name = re.sub(r'\s+', ' ', str(name).strip())
        
        # Standardize common company abbreviations
        name = re.sub(r'ltd\.?$', 'Ltd.', name, flags=re.IGNORECASE)
        name = re.sub(r'limited$', 'Ltd.', name, flags=re.IGNORECASE)
        name = re.sub(r'pvt\.?', 'Pvt.', name, flags=re.IGNORECASE)
        
        # Capitalize
        name = name.title()
        
        # Fix specific cases
        name_mapping = {
            "Ntpc": "NTPC",
            "Nhpc": "NHPC",
            "Seci": "SECI",
            "Tata Power": "Tata Power",
            "Adani Green Energy": "Adani Green Energy",
            "Renew Power": "ReNew Power",
            "Azure Power": "Azure Power",
            # Add more mappings as needed
        }
        
        for key, value in name_mapping.items():
            if key.lower() in name.lower():
                return value
        
        return name
    
    def clean_date(self, date_value: Any) -> Optional[datetime.date]:
        """Clean and standardize date values"""
        if not date_value:
            return None
            
        if isinstance(date_value, datetime.date):
            return date_value
            
        if isinstance(date_value, datetime.datetime):
            return date_value.date()
            
        if isinstance(date_value, str):
            # Try different date formats
            date_formats = [
                "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y",
                "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y",
                "%d.%m.%Y", "%m.%d.%Y", "%Y.%m.%d",
                "%b %d, %Y", "%d %b %Y", "%B %d, %Y", "%d %B %Y"
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.datetime.strptime(date_value, fmt).date()
                except ValueError:
                    continue
                    
            # Try to extract year
            year_match = re.search(r'\b(20\d{2})\b', date_value)
            if year_match:
                year = int(year_match.group(1))
                # Default to mid-year if only year is available
                return datetime.date(year, 7, 1)
        
        return None
    
    def clean_project_type(self, project_type: Optional[str],
                          is_hybrid: Optional[Union[bool, str]],
                          hybrid_type: Optional[str]) -> Dict[str, Any]:
        """Clean and standardize project type information"""
        result = {}
        
        # Determine if hybrid from any source
        hybrid_indicator = False
        
        if is_hybrid is not None:
            if isinstance(is_hybrid, bool):
                hybrid_indicator = is_hybrid
            elif isinstance(is_hybrid, str):
                hybrid_indicator = is_hybrid.lower() in ['true', 'yes', 'y', '1']
        
        if project_type:
            project_type = str(project_type).strip().lower()
            if "hybrid" in project_type or "+" in project_type:
                hybrid_indicator = True
                
            # Map to standard project type
            standard_type = self.project_type_mapping.get(project_type)
            if standard_type:
                result['project_type'] = standard_type
            else:
                result['project_type'] = project_type.title()
        
        # Set hybrid flag and type
        result['is_hybrid'] = hybrid_indicator
        
        if hybrid_indicator and hybrid_type:
            result['hybrid_type'] = str(hybrid_type).strip().title()
        elif hybrid_indicator and project_type and "+" in project_type:
            if "storage" in project_type.lower():
                result['hybrid_type'] = "Storage"
            elif "wind" in project_type.lower():
                result['hybrid_type'] = "Wind"
        
        return result
    
    def clean_cell_technology(self, cell_tech: Optional[str]) -> Optional[str]:
        """Clean and standardize cell technology information"""
        if not cell_tech:
            return None
            
        cell_tech = str(cell_tech).strip().lower()
        
        # Map to standard cell technology
        return self.cell_tech_mapping.get(cell_tech, cell_tech.title())
    
    def clean_boolean(self, value: Any) -> Optional[bool]:
        """Clean and standardize boolean values"""
        if value is None:
            return None
            
        if isinstance(value, bool):
            return value
            
        if isinstance(value, (int, float)):
            return bool(value)
            
        if isinstance(value, str):
            return value.lower() in ['true', 'yes', 'y', '1', 'on']
            
        return None
    
    def clean_voltage(self, voltage: Any) -> Optional[int]:
        """Clean and standardize voltage values in kV"""
        if voltage is None:
            return None
            
        if isinstance(voltage, (int, float)):
            return int(voltage)
            
        if isinstance(voltage, str):
            # Extract numbers
            match = re.search(r'(\d+)', voltage)
            if match:
                return int(match.group(1))
                
        return None
    
    def clean_ppa_type(self, ppa_type: Optional[str]) -> Optional[str]:
        """Clean and standardize PPA type"""
        if not ppa_type:
            return None
            
        ppa_type = str(ppa_type).strip().lower()
        
        # Map to standard PPA types
        mapping = {
            "power purchase agreement": "PPA",
            "merchant": "Merchant",
            "captive": "Captive",
            "open access": "Open Access",
            "group captive": "Group Captive",
            # Add more mappings as needed
        }
        
        return mapping.get(ppa_type, ppa_type.title())
    
    def clean_integer(self, value: Any) -> Optional[int]:
        """Clean and convert to integer"""
        if value is None:
            return None
            
        if isinstance(value, int):
            return value
            
        if isinstance(value, float):
            return int(value)
            
        if isinstance(value, str):
            try:
                return int(float(re.sub(r'[^\d.]', '', value)))
            except ValueError:
                return None
                
        return None
    
    def clean_float(self, value: Any) -> Optional[float]:
        """Clean and convert to float"""
        if value is None:
            return None
            
        if isinstance(value, (int, float)):
            return float(value)
            
        if isinstance(value, str):
            try:
                return float(re.sub(r'[^\d.]', '', value))
            except ValueError:
                return None
                
        return None
    
    def clean_cuf(self, cuf: Any) -> Optional[float]:
        """Clean and standardize Capacity Utilization Factor"""
        if cuf is None:
            return None
            
        if isinstance(cuf, (int, float)):
            # If CUF is provided as percentage (e.g. 19.5), convert to decimal
            if cuf > 1:
                return cuf / 100.0
            return cuf
            
        if isinstance(cuf, str):
            # Remove % symbol and convert to decimal
            cuf = re.sub(r'[^\d.]', '', cuf)
            try:
                cuf_float = float(cuf)
                if cuf_float > 1:
                    return cuf_float / 100.0
                return cuf_float
            except ValueError:
                return None
                
        return None
    
    def clean_land_area(self, area: Any) -> Optional[float]:
        """Clean and standardize land area in acres"""
        if area is None:
            return None
            
        if isinstance(area, (int, float)):
            return float(area)
            
        if isinstance(area, str):
            # Extract numeric value
            match = re.search(r'(\d+\.?\d*)', area)
            if not match:
                return None
                
            value = float(match.group(1))
            
            # Convert to acres if necessary
            if 'hectare' in area.lower() or 'ha' in area.lower():
                return value * 2.47105  # 1 hectare = 2.47105 acres
            elif 'sq km' in area.lower() or 'square kilometer' in area.lower():
                return value * 247.105  # 1 sq km = 247.105 acres
                
            return value
                
        return None