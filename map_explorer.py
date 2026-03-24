import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import re
from src.zip_validator import ZIPValidator
from education import EducationAPI
from emergency_services import EmergencyServicesAPI
from healthcare import HealthcareAPI
from infrastructure import BusStopsAPI, LibrariesAPI, ParksAPI
from geo_data import GeoDataAPI
import time
from typing import Dict, Any, List, Optional

# Color constants
SCHOOL_COLORS = {
    'public': 'blue',
    'private': 'lightblue',
    'charter': 'darkblue'
}

EMERGENCY_COLORS = {
    'Police Station': 'darkred',
    'Fire Station': 'red',
    'Emergency Medical': 'lightred'
}

HEALTHCARE_COLORS = {
    'hospital': 'green',
    'mental_health': 'lightgreen',
    'clinic': 'darkgreen'
}

INFRASTRUCTURE_COLORS = {
    'bus_stop': 'purple',
    'library': 'pink',
    'park': 'beige'
}

GEO_COLORS = {
    'flood_zone': 'blue',
    'evacuation_route': 'red',
    'bus_route': 'green'
}

USER_LOCATION_COLOR = 'black'

# Processing functions
def process_school_data(school, user_coords, radius):
    """Process school data and return marker info if within radius"""
    try:
        # Get school coordinates
        if 'geometry' in school and school['geometry']:
            coords = school['geometry']['coordinates']
            school_coords = (coords[1], coords[0])
        elif 'LAT' in school and 'LON' in school:
            school_coords = (school['LAT'], school['LON'])
        else:
            return None
        
        # Calculate distance
        distance = geodesic(user_coords, school_coords).miles
        if distance <= radius:
            school_type = school.get('school_type', 'public')
            return {
                'location': [school_coords[0], school_coords[1]],
                'popup': f"<b>{school_type.title()} School:</b> {school.get('NAME', 'Unknown')}<br>" + \
                        f"Address: {school.get('ADDRESS', 'N/A')}<br>" + \
                        f"Grades: {school.get('GRDLEVEL', 'N/A')}<br>" + \
                        f"Enrollment: {school.get('ENROLLMENT', 'N/A')}<br>" + \
                        f"Distance: {distance:.1f} miles",
                'icon': SCHOOL_COLORS.get(school_type, 'blue'),
                'distance': distance
            }
    except Exception as e:
        add_debug_info("School Processing", f"Error processing school {school.get('NAME', 'Unknown')}: {str(e)}")
        return None
    
    return None

def process_emergency_service(service, user_coords, radius, service_type):
    """Process emergency service data and return marker info if within radius"""
    try:
        if 'geometry' in service and service['geometry']:
            coords = service['geometry']['coordinates']
            service_coords = (coords[1], coords[0])
            
            # Calculate distance
            distance = geodesic(user_coords, service_coords).miles
            if distance <= radius:
                properties = service.get('properties', {})
                return {
                    'location': [service_coords[0], service_coords[1]],
                    'popup': f"<b>{service_type}:</b> {properties.get('NAME', 'Unknown')}<br>" + \
                            f"Address: {properties.get('ADDRESS', 'N/A')}<br>" + \
                            f"Phone: {properties.get('PHONE', 'N/A')}<br>" + \
                            f"Distance: {distance:.1f} miles",
                    'icon': EMERGENCY_COLORS.get(service_type, 'red'),
                    'distance': distance
                }
    except Exception as e:
        add_debug_info("Emergency Services", f"Error processing {service_type}: {str(e)}")
        return None
    
    return None

def process_healthcare_facility(facility, user_coords, radius, facility_type):
    """Process healthcare facility data and return marker info if within radius"""
    try:
        if 'geometry' in facility and facility['geometry']:
            coords = facility['geometry']['coordinates']
            facility_coords = (coords[1], coords[0])
            
            # Calculate distance
            distance = geodesic(user_coords, facility_coords).miles
            if distance <= radius:
                properties = facility.get('properties', {})
                
                # Handle different property name formats
                name = properties.get('NAME', properties.get('name', properties.get('FACILITY_NAME', 'Unknown')))
                address = properties.get('ADDRESS', properties.get('address', properties.get('STREET_ADDRESS', 'N/A')))
                phone = properties.get('PHONE', properties.get('phone', properties.get('PHONE_NUMBER', 'N/A')))
                
                # Create facility type specific additional info
                additional_info = ""
                if facility_type == "hospital":
                    beds = properties.get('BEDS', properties.get('NUM_BEDS', 'N/A'))
                    additional_info = f"Number of Beds: {beds}<br>"
                elif facility_type == "mental_health":
                    services = properties.get('SERVICES', properties.get('SERVICE_TYPE', 'N/A'))
                    additional_info = f"Services: {services}<br>"
                elif facility_type == "clinic":
                    hours = properties.get('HOURS', properties.get('OPERATING_HOURS', 'N/A'))
                    additional_info = f"Hours: {hours}<br>"
                
                return {
                    'location': [facility_coords[0], facility_coords[1]],
                    'popup': f"<b>{facility_type.title()}:</b> {name}<br>" + \
                            f"Address: {address}<br>" + \
                            f"Phone: {phone}<br>" + \
                            additional_info + \
                            f"Distance: {distance:.1f} miles",
                    'icon': HEALTHCARE_COLORS.get(facility_type, 'green'),
                    'distance': distance
                }
    except Exception as e:
        add_debug_info("Healthcare", f"Error processing {facility_type}: {str(e)}")
        return None
    
    return None

def process_infrastructure(facility, user_coords, radius, facility_type):
    """Process infrastructure facility data and return marker info if within radius"""
    try:
        if 'geometry' in facility and facility['geometry']:
            coords = facility['geometry']['coordinates']
            facility_coords = (coords[1], coords[0])
            
            # Calculate distance
            distance = geodesic(user_coords, facility_coords).miles
            if distance <= radius:
                properties = facility.get('properties', {})
                
                # Handle different property name formats
                name = properties.get('NAME', properties.get('name', properties.get('FACILITY_NAME', 'Unknown')))
                address = properties.get('ADDRESS', properties.get('address', properties.get('STREET_ADDRESS', 'N/A')))
                
                # Facility type specific information
                additional_info = ""
                if facility_type == "bus_stop":
                    route = properties.get('ROUTE', properties.get('route', properties.get('BUS_ROUTE', 'N/A')))
                    additional_info = f"Route: {route}<br>"
                elif facility_type == "library":
                    hours = properties.get('HOURS', properties.get('hours', properties.get('OPERATING_HOURS', 'N/A')))
                    phone = properties.get('PHONE', properties.get('phone', properties.get('PHONE_NUMBER', 'N/A')))
                    additional_info = f"Hours: {hours}<br>Phone: {phone}<br>"
                elif facility_type == "park":
                    amenities = properties.get('AMENITIES', properties.get('amenities', properties.get('FACILITIES', 'N/A')))
                    additional_info = f"Amenities: {amenities}<br>"
                
                return {
                    'location': [facility_coords[0], facility_coords[1]],
                    'popup': f"<b>{facility_type.replace('_', ' ').title()}:</b> {name}<br>" + \
                            f"Address: {address}<br>" + \
                            additional_info + \
                            f"Distance: {distance:.1f} miles",
                    'icon': INFRASTRUCTURE_COLORS.get(facility_type, 'gray'),
                    'distance': distance
                }
    except Exception as e:
        add_debug_info("Infrastructure", f"Error processing {facility_type}: {str(e)}")
        return None
    
    return None

def filter_geographic_data(geo_data, user_coords, radius):
    """Filter geographic data based on user location and radius"""
    # Convert user_coords to tuple if it's a list
    if isinstance(user_coords, list):
        user_coords = tuple(user_coords)
        
    filtered_data = {}
    
    if 'flood_zones' in geo_data:
        filtered_zones = []
        for feature in geo_data['flood_zones']['features']:
            try:
                if 'geometry' in feature and feature['geometry']:
                    # Check if any point in the polygon is within radius
                    coords = feature['geometry']['coordinates'][0]  # First ring of polygon
                    for coord in coords:
                        point_coords = (coord[1], coord[0])  # Convert to (lat, lon)
                        distance = geodesic(user_coords, point_coords).miles
                        if distance <= radius:
                            filtered_zones.append(feature)
                            break
            except Exception as e:
                add_debug_info("GeoData Filter", f"Error processing flood zone: {str(e)}")
                continue
                
        if filtered_zones:
            filtered_data['flood_zones'] = {
                'type': 'FeatureCollection',
                'features': filtered_zones
            }
            filtered_data['flood_zone_color'] = geo_data['flood_zone_color']
    
    if 'evacuation_routes' in geo_data:
        filtered_routes = []
        for feature in geo_data['evacuation_routes']['features']:
            try:
                if 'geometry' in feature and feature['geometry']:
                    # Check if any point in the line is within radius
                    coords = feature['geometry']['coordinates']
                    if isinstance(coords[0][0], list):  # Handle MultiLineString
                        coords = [c for sublist in coords for c in sublist]
                    for coord in coords:
                        point_coords = (coord[1], coord[0])  # Convert to (lat, lon)
                        distance = geodesic(user_coords, point_coords).miles
                        if distance <= radius:
                            filtered_routes.append(feature)
                            break
            except Exception as e:
                add_debug_info("GeoData Filter", f"Error processing evacuation route: {str(e)}")
                continue
                
        if filtered_routes:
            filtered_data['evacuation_routes'] = {
                'type': 'FeatureCollection',
                'features': filtered_routes
            }
            filtered_data['evacuation_route_color'] = geo_data['evacuation_route_color']
    
    if 'bus_routes' in geo_data:
        filtered_routes = []
        for feature in geo_data['bus_routes']['features']:
            try:
                if 'geometry' in feature and feature['geometry']:
                    # Check if any point in the line is within radius
                    coords = feature['geometry']['coordinates']
                    if isinstance(coords[0][0], list):  # Handle MultiLineString
                        coords = [c for sublist in coords for c in sublist]
                    for coord in coords:
                        point_coords = (coord[1], coord[0])  # Convert to (lat, lon)
                        distance = geodesic(user_coords, point_coords).miles
                        if distance <= radius:
                            filtered_routes.append(feature)
                            break
            except Exception as e:
                add_debug_info("GeoData Filter", f"Error processing bus route: {str(e)}")
                continue
                
        if filtered_routes:
            filtered_data['bus_routes'] = {
                'type': 'FeatureCollection',
                'features': filtered_routes
            }
            filtered_data['bus_route_color'] = geo_data['bus_route_color']
    
    return filtered_data

# Initialize session state variables
if 'map_center' not in st.session_state:
    st.session_state.map_center = [25.7617, -80.1918]  # Miami coordinates
if 'zoom_level' not in st.session_state:
    st.session_state.zoom_level = 10
if 'markers' not in st.session_state:
    st.session_state.markers = []
if 'last_location' not in st.session_state:
    st.session_state.last_location = None
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = []

def add_debug_info(category: str, message: str):
    """Add debug information to session state"""
    st.session_state.debug_info.append(f"{category}: {message}")

def convert_to_latlong(center):
    """Convert center format between Streamlit-Folium and Folium."""
    if isinstance(center, dict) and 'lat' in center and 'lng' in center:
        return [center['lat'], center['lng']]
    return center

def get_nearby_zip_codes(zip_validator, center_coords, radius_miles):
    """Get all ZIP codes within the specified radius"""
    all_zip_codes = zip_validator.get_all_zip_codes()
    nearby_zips = []
    
    for zip_code in all_zip_codes:
        zip_coords = zip_validator.get_zip_coordinates(zip_code)
        if zip_coords:
            distance = geodesic(center_coords, zip_coords).miles
            if distance <= radius_miles:
                nearby_zips.append(zip_code)
    
    return nearby_zips

# Initialize APIs and validator
@st.cache_resource
def get_apis():
    return {
        'Education': EducationAPI(),
        'Emergency': EmergencyServicesAPI(),
        'Healthcare': HealthcareAPI(),
        'Infrastructure': {
            'Bus Stops': BusStopsAPI(),
            'Libraries': LibrariesAPI(),
            'Parks': ParksAPI()
        },
        'GeoData': GeoDataAPI()
    }

@st.cache_resource
def get_zip_validator():
    return ZIPValidator()

apis = get_apis()
zip_validator = get_zip_validator()

def main():
    # Title and description
    st.title("🗺️ Miami-Dade County Unified Map Explorer")
    st.write("Explore infrastructure, services, and geographic data in Miami-Dade County")

    # Create two columns for controls and map
    col1, col2 = st.columns([1, 2])

    with col1:
        # Use a form for address input and category selection
        with st.form(key="location_form", clear_on_submit=False):
            input_col, button_col = st.columns([4, 1])
            with input_col:
                location_input = st.text_input("Enter your address or ZIP code", key="location_input")
            with button_col:
                submit_location = st.form_submit_button("Enter Location")

            st.subheader("Select Categories to Display")

            # Education facilities
            st.write("Education")
            show_public_schools = st.checkbox("Public Schools", value=True)
            show_private_schools = st.checkbox("Private Schools", value=True)
            show_charter_schools = st.checkbox("Charter Schools", value=True)

            # Emergency services
            st.write("Emergency Services")
            show_police = st.checkbox("Police Stations", value=True)
            show_fire = st.checkbox("Fire Stations", value=True)

            # Healthcare facilities
            st.write("Healthcare")
            show_hospitals = st.checkbox("Hospitals", value=True)
            show_mental_health = st.checkbox("Mental Health Centers", value=True)
            show_clinics = st.checkbox("Free-Standing Clinics", value=True)

            # Infrastructure
            st.write("Infrastructure")
            show_bus_stops = st.checkbox("Bus Stops", value=True)
            show_libraries = st.checkbox("Libraries", value=True)
            show_parks = st.checkbox("Parks", value=True)

            # Geographic Data
            st.write("Geographic Data")
            show_flood_zones = st.checkbox("Flood Zones", value=True)
            show_evacuation_routes = st.checkbox("Evacuation Routes", value=True)
            show_bus_routes = st.checkbox("Bus Routes", value=True)

            # Search radius
            radius = st.slider("Search radius (miles)", 1.0, 20.0, 5.0)

            # Only process if form is submitted
            if submit_location:
                # Clear previous debug info
                st.session_state.debug_info = []
                
                if not location_input:
                    st.error("Please enter an address or ZIP code")
                else:
                    # Check if input is a ZIP code
                    zip_match = re.match(r'^\d{5}$', location_input.strip())
                    if zip_match:
                        # Validate ZIP code
                        is_valid, message, zip_info = zip_validator.validate_zip(location_input)
                        if not is_valid:
                            st.error(message)
                            with st.expander("Show valid Miami-Dade County ZIP codes"):
                                valid_zips = sorted(list(zip_validator.get_all_zip_codes()))
                                cols = st.columns(5)
                                for i, zip_code in enumerate(valid_zips):
                                    cols[i % 5].write(zip_code)
                            st.stop()
                        # Get coordinates from ZIP code
                        coordinates = zip_validator.get_zip_coordinates(location_input)
                        if not coordinates:
                            st.error("Could not get coordinates for this ZIP code")
                            st.stop()
                    else:
                        # Get coordinates from address
                        geolocator = Nominatim(user_agent="miami_explorer")
                        try:
                            location = geolocator.geocode(location_input, timeout=10)
                            if location:
                                coordinates = (location.latitude, location.longitude)
                            else:
                                st.error("Could not find coordinates for the provided location")
                                st.stop()
                        except Exception as e:
                            st.error(f"Error geocoding address: {str(e)}")
                            st.stop()
                    # Update map center and zoom
                    st.session_state.map_center = list(coordinates)
                    st.session_state.zoom_level = 12
                    st.session_state.last_location = location_input
                    
                    # Clear previous markers and geo data
                    st.session_state.markers = []
                    if hasattr(st.session_state, 'geo_data'):
                        del st.session_state.geo_data
                    
                    # Add user location marker
                    st.session_state.markers.append({
                        'location': list(coordinates),
                        'popup': "📍 Your Location",
                        'icon': USER_LOCATION_COLOR,
                        'is_user_location': True
                    })
                    
                    # Fetch and process data
                    with st.spinner("Fetching data..."):
                        # Get nearby ZIP codes
                        nearby_zips = get_nearby_zip_codes(zip_validator, coordinates, radius)
                        add_debug_info("ZIP Codes", f"Found {len(nearby_zips)} ZIP codes within {radius} miles")
                        
                        # Process infrastructure and services data
                        if show_public_schools or show_private_schools or show_charter_schools:
                            education_api = apis['Education']
                            
                            try:
                                all_schools = []
                                
                                # Fetch schools from each ZIP code
                                for zip_code in nearby_zips:
                                    if show_public_schools:
                                        schools = education_api.get_schools_by_zip(zip_code, 'public')
                                        if schools.get('success'):
                                            for school in schools['data'].get('schools', []):
                                                school['school_type'] = 'public'
                                                all_schools.append(school)
                                    
                                    if show_private_schools:
                                        schools = education_api.get_schools_by_zip(zip_code, 'private')
                                        if schools.get('success'):
                                            for school in schools['data'].get('schools', []):
                                                school['school_type'] = 'private'
                                                all_schools.append(school)
                                    
                                    if show_charter_schools:
                                        schools = education_api.get_schools_by_zip(zip_code, 'charter')
                                        if schools.get('success'):
                                            for school in schools['data'].get('schools', []):
                                                school['school_type'] = 'charter'
                                                all_schools.append(school)
                                
                                add_debug_info("Schools", f"Found {len(all_schools)} total schools in all ZIP codes")
                                
                                # Process each school and add markers if within radius
                                markers_added = 0
                                for school in all_schools:
                                    marker_info = process_school_data(school, coordinates, radius)
                                    if marker_info:
                                        st.session_state.markers.append(marker_info)
                                        markers_added += 1
                                
                                add_debug_info("Schools", f"Added {markers_added} school markers within {radius} miles")
                                
                            except Exception as e:
                                add_debug_info("Education", f"General education API error: {str(e)}")
                        
                        # Emergency services
                        if show_police or show_fire:
                            emergency_api = apis['Emergency']
                            
                            try:
                                if show_police:
                                    add_debug_info("Emergency", "Fetching police stations...")
                                    police_stations = emergency_api.get_police_stations()
                                    
                                    if police_stations and 'features' in police_stations:
                                        stations_added = 0
                                        for station in police_stations['features']:
                                            marker_info = process_emergency_service(station, coordinates, radius, "Police Station")
                                            if marker_info:
                                                st.session_state.markers.append(marker_info)
                                                stations_added += 1
                                        add_debug_info("Emergency", f"Added {stations_added} police stations within {radius} miles")
                                    else:
                                        add_debug_info("Emergency", "No police stations data received")
                                
                                if show_fire:
                                    add_debug_info("Emergency", "Fetching fire stations...")
                                    fire_stations = emergency_api.get_fire_stations()
                                    
                                    if fire_stations and 'features' in fire_stations:
                                        stations_added = 0
                                        for station in fire_stations['features']:
                                            marker_info = process_emergency_service(station, coordinates, radius, "Fire Station")
                                            if marker_info:
                                                st.session_state.markers.append(marker_info)
                                                stations_added += 1
                                        add_debug_info("Emergency", f"Added {stations_added} fire stations within {radius} miles")
                                    else:
                                        add_debug_info("Emergency", "No fire stations data received")
                                
                            except Exception as e:
                                add_debug_info("Emergency", f"Error fetching emergency services: {str(e)}")
                        
                        # Healthcare facilities
                        if show_hospitals or show_mental_health or show_clinics:
                            healthcare_api = apis['Healthcare']
                            
                            try:
                                if show_hospitals:
                                    add_debug_info("Healthcare", "Fetching hospitals...")
                                    hospitals = healthcare_api.get_hospitals()
                                    
                                    if hospitals and 'features' in hospitals:
                                        facilities_added = 0
                                        for hospital in hospitals['features']:
                                            marker_info = process_healthcare_facility(hospital, coordinates, radius, "hospital")
                                            if marker_info:
                                                st.session_state.markers.append(marker_info)
                                                facilities_added += 1
                                        add_debug_info("Healthcare", f"Added {facilities_added} hospitals within {radius} miles")
                                    else:
                                        add_debug_info("Healthcare", "No hospitals data received")
                                
                                if show_mental_health:
                                    add_debug_info("Healthcare", "Fetching mental health centers...")
                                    mental_health_centers = healthcare_api.get_mental_health_centers()
                                    
                                    if mental_health_centers and 'features' in mental_health_centers:
                                        facilities_added = 0
                                        for center in mental_health_centers['features']:
                                            marker_info = process_healthcare_facility(center, coordinates, radius, "mental_health")
                                            if marker_info:
                                                st.session_state.markers.append(marker_info)
                                                facilities_added += 1
                                        add_debug_info("Healthcare", f"Added {facilities_added} mental health centers within {radius} miles")
                                    else:
                                        add_debug_info("Healthcare", "No mental health centers data received")
                                
                                if show_clinics:
                                    add_debug_info("Healthcare", "Fetching free-standing clinics...")
                                    clinics = healthcare_api.get_free_standing_clinics()
                                    
                                    if clinics and 'features' in clinics:
                                        facilities_added = 0
                                        for clinic in clinics['features']:
                                            marker_info = process_healthcare_facility(clinic, coordinates, radius, "clinic")
                                            if marker_info:
                                                st.session_state.markers.append(marker_info)
                                                facilities_added += 1
                                        add_debug_info("Healthcare", f"Added {facilities_added} clinics within {radius} miles")
                                    else:
                                        add_debug_info("Healthcare", "No clinics data received")
                                
                            except Exception as e:
                                add_debug_info("Healthcare", f"Error fetching healthcare facilities: {str(e)}")
                        
                        # Infrastructure facilities
                        if show_bus_stops or show_libraries or show_parks:
                            try:
                                if show_bus_stops:
                                    add_debug_info("Infrastructure", "Fetching bus stops...")
                                    bus_stops = apis['Infrastructure']['Bus Stops'].get_all_stops()
                                    
                                    if bus_stops and 'features' in bus_stops:
                                        facilities_added = 0
                                        for stop in bus_stops['features']:
                                            marker_info = process_infrastructure(stop, coordinates, radius, "bus_stop")
                                            if marker_info:
                                                st.session_state.markers.append(marker_info)
                                                facilities_added += 1
                                        add_debug_info("Infrastructure", f"Added {facilities_added} bus stops within {radius} miles")
                                    else:
                                        add_debug_info("Infrastructure", "No bus stops data received")
                                
                                if show_libraries:
                                    add_debug_info("Infrastructure", "Fetching libraries...")
                                    libraries = apis['Infrastructure']['Libraries'].get_all_libraries()
                                    
                                    if libraries and 'features' in libraries:
                                        facilities_added = 0
                                        for library in libraries['features']:
                                            marker_info = process_infrastructure(library, coordinates, radius, "library")
                                            if marker_info:
                                                st.session_state.markers.append(marker_info)
                                                facilities_added += 1
                                        add_debug_info("Infrastructure", f"Added {facilities_added} libraries within {radius} miles")
                                    else:
                                        add_debug_info("Infrastructure", "No libraries data received")
                                
                                if show_parks:
                                    add_debug_info("Infrastructure", "Fetching parks...")
                                    parks = apis['Infrastructure']['Parks'].get_all_parks()
                                    
                                    if parks and 'features' in parks:
                                        facilities_added = 0
                                        for park in parks['features']:
                                            marker_info = process_infrastructure(park, coordinates, radius, "park")
                                            if marker_info:
                                                st.session_state.markers.append(marker_info)
                                                facilities_added += 1
                                        add_debug_info("Infrastructure", f"Added {facilities_added} parks within {radius} miles")
                                    else:
                                        add_debug_info("Infrastructure", "No parks data received")
                                
                            except Exception as e:
                                add_debug_info("Infrastructure", f"Error fetching infrastructure facilities: {str(e)}")
                        
                        # Process geographic data
                        if show_flood_zones or show_evacuation_routes or show_bus_routes:
                            geo_api = apis['GeoData']
                            
                            try:
                                # Fetch all geographic data first
                                all_geo_data = {}
                                
                                if show_flood_zones:
                                    add_debug_info("GeoData", "Fetching flood zones...")
                                    flood_zones = geo_api.get_flood_zones()
                                    if flood_zones and 'features' in flood_zones:
                                        all_geo_data['flood_zones'] = flood_zones
                                        all_geo_data['flood_zone_color'] = GEO_COLORS['flood_zone']
                                        add_debug_info("GeoData", f"Added flood zones data")
                                
                                if show_evacuation_routes:
                                    add_debug_info("GeoData", "Fetching evacuation routes...")
                                    evacuation_routes = geo_api.get_evacuation_routes()
                                    if evacuation_routes and 'features' in evacuation_routes:
                                        all_geo_data['evacuation_routes'] = evacuation_routes
                                        all_geo_data['evacuation_route_color'] = GEO_COLORS['evacuation_route']
                                        add_debug_info("GeoData", f"Added evacuation routes data")
                                
                                if show_bus_routes:
                                    add_debug_info("GeoData", "Fetching bus routes...")
                                    bus_routes = geo_api.get_bus_routes()
                                    if bus_routes and 'features' in bus_routes:
                                        all_geo_data['bus_routes'] = bus_routes
                                        all_geo_data['bus_route_color'] = GEO_COLORS['bus_route']
                                        add_debug_info("GeoData", f"Added bus routes data")
                                
                                # Filter geographic data based on user location and radius
                                if all_geo_data:
                                    st.session_state.geo_data = filter_geographic_data(all_geo_data, coordinates, radius)
                                    add_debug_info("GeoData", "Filtered geographic data based on location and radius")
                                
                            except Exception as e:
                                add_debug_info("GeoData", f"Error fetching geographic data: {str(e)}")
                    
                    # Show summary of found locations
                    st.success(f"Found {len(st.session_state.markers) - 1} locations within {radius} miles")

    # Display the map in col2
    with col2:
        # Create the base map
        map_center = convert_to_latlong(st.session_state.map_center)
        m = folium.Map(location=map_center, zoom_start=st.session_state.zoom_level)
        
        # Add markers
        for marker in st.session_state.markers:
            if marker.get('is_user_location'):
                # Special styling for user location
                folium.Marker(
                    marker['location'],
                    popup=folium.Popup(marker['popup'], max_width=300),
                    icon=folium.Icon(color=marker['icon'], icon='home', prefix='fa')
                ).add_to(m)
            else:
                # Regular markers for facilities
                folium.Marker(
                    marker['location'],
                    popup=folium.Popup(marker['popup'], max_width=300),
                    icon=folium.Icon(color=marker['icon'], icon='info-sign')
                ).add_to(m)
        
        # Add geographic data layers
        if hasattr(st.session_state, 'geo_data'):
            if 'flood_zones' in st.session_state.geo_data:
                folium.GeoJson(
                    st.session_state.geo_data['flood_zones'],
                    name='Flood Zones',
                    style_function=lambda x: {
                        'fillColor': st.session_state.geo_data['flood_zone_color'],
                        'color': st.session_state.geo_data['flood_zone_color'],
                        'weight': 1,
                        'fillOpacity': 0.3
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=['ZONESUBTY', 'FZONE', 'ELEV'],
                        aliases=['Zone Subtype:', 'Flood Zone:', 'Elevation:'],
                        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
                    )
                ).add_to(m)
            
            if 'evacuation_routes' in st.session_state.geo_data:
                folium.GeoJson(
                    st.session_state.geo_data['evacuation_routes'],
                    name='Evacuation Routes',
                    style_function=lambda x: {
                        'color': st.session_state.geo_data['evacuation_route_color'],
                        'weight': 3,
                        'opacity': 0.8
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=['SN', 'CREATEDBY'],
                        aliases=['Serial Number:', 'Created By:'],
                        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
                    )
                ).add_to(m)
            
            if 'bus_routes' in st.session_state.geo_data:
                folium.GeoJson(
                    st.session_state.geo_data['bus_routes'],
                    name='Bus Routes',
                    style_function=lambda x: {
                        'color': st.session_state.geo_data['bus_route_color'],
                        'weight': 2,
                        'opacity': 0.7
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=['LINEABBR', 'LINENAME', 'RTNAME'],
                        aliases=['Line:', 'Line Name:', 'Route Name:'],
                        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
                    )
                ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Display the map
        map_data = st_folium(
            m,
            width=800,
            height=600,
            key="main_map"
        )
        
        # Update center and zoom if map is moved
        if map_data is not None:
            if 'center' in map_data and map_data['center']:
                st.session_state.map_center = convert_to_latlong(map_data['center'])
            if 'zoom' in map_data and map_data['zoom']:
                st.session_state.zoom_level = map_data['zoom']

if __name__ == "__main__":
    main() 