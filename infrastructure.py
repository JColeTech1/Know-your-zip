"""
This module contains infrastructure code for handling API-related functionality.
It serves as a central location for API configurations, utilities, and common functions.
"""

import os
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class APIInfrastructure:
    """Base class for handling API infrastructure and common operations."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the API infrastructure.
        
        Args:
            base_url (str): The base URL for the API
            api_key (Optional[str]): API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key  # Never auto-read from env; callers must pass explicitly
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def make_request(self, 
                    endpoint: str, 
                    method: str = 'GET', 
                    data: Optional[Dict[str, Any]] = None,
                    params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make an API request with proper error handling.
        
        Args:
            endpoint (str): API endpoint to call
            method (str): HTTP method (GET, POST, etc.)
            data (Optional[Dict]): Request body data
            params (Optional[Dict]): URL parameters
            
        Returns:
            requests.Response: The API response
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            # Log the error and re-raise
            print(f"API request failed: {str(e)}")
            raise

class BusStopsAPI(APIInfrastructure):
    """Class for handling Miami-Dade bus stops API operations."""
    
    def __init__(self):
        """Initialize the bus stops API with the specific base URL."""
        super().__init__(
            base_url="https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/Bus_Stop_Maintenance_View_Layer/FeatureServer/1"
        )
    
    def get_all_stops(self) -> Dict[str, Any]:
        """
        Get all bus stops from the API.
        
        Returns:
            Dict[str, Any]: The bus stops data in GeoJSON format
        """
        params = {
            'outFields': '*',
            'where': '1=1',
            'f': 'geojson'
        }
        
        response = self.make_request('query', params=params)
        return response.json()

class LibrariesAPI(APIInfrastructure):
    """Class for handling Miami-Dade libraries API operations."""
    
    def __init__(self):
        """Initialize the libraries API with the specific base URL."""
        super().__init__(
            base_url="https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/Library_gdb/FeatureServer/0"
        )
    
    def get_all_libraries(self) -> Dict[str, Any]:
        """
        Get all libraries from the API.
        
        Returns:
            Dict[str, Any]: The libraries data in GeoJSON format
        """
        params = {
            'outFields': '*',
            'where': '1=1',
            'f': 'geojson'
        }
        
        response = self.make_request('query', params=params)
        return response.json()

class ParksAPI(APIInfrastructure):
    """Class for handling Miami-Dade parks API operations."""

    def __init__(self):
        """Initialize the parks API with the specific base URL."""
        super().__init__(
            base_url="https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/Parks/FeatureServer/0"
        )
    
    def get_all_parks(self) -> Dict[str, Any]:
        """
        Get all parks from the API.
        
        Returns:
            Dict[str, Any]: The parks data in GeoJSON format
        """
        params = {
            'outFields': '*',
            'where': '1=1',
            'f': 'geojson'
        }
        
        response = self.make_request('query', params=params)
        return response.json()

# Example usage:
# api = APIInfrastructure(base_url="https://api.example.com")
# response = api.make_request("endpoint", method="POST", data={"key": "value"})
# stops_api = BusStopsAPI()
# stops = stops_api.get_all_stops()
# libraries_api = LibrariesAPI()
# libraries = libraries_api.get_all_libraries()
# parks_api = ParksAPI()
# parks = parks_api.get_all_parks() 