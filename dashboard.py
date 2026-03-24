import streamlit as st
import pandas as pd
import plotly.express as px
from education import EducationAPI
from healthcare import HealthcareAPI
from emergency_services import EmergencyServicesAPI
from geo_data import GeoDataAPI
from src.zip_validator import ZIPValidator
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from infrastructure import BusStopsAPI, LibrariesAPI, ParksAPI
from charts import plot_schools_histogram, plot_fire_station_proximity_pie, plot_zip_park_density_treemap

def categorize_location(lat: float, lon: float) -> str:
    """
    Categorize a location into one of Miami-Dade's regions based on coordinates.
    
    Approximate boundaries:
    - Northeast: North of 25.8500°N and East of -80.2000°W
    - Southeast: South of 25.8500°N and East of -80.2000°W
    - Southwest: South of 25.8500°N and West of -80.2000°W
    - Northwest: North of 25.8500°N and West of -80.2000°W
    """
    if lat >= 25.8500:  # North
        if lon >= -80.2000:  # East
            return "Northeast"
        else:
            return "Northwest"
    else:  # South
        if lon >= -80.2000:  # East
            return "Southeast"
        else:
            return "Southwest"

def analyze_parks_distribution(parks_api):
    """Analyze the distribution of parks across Miami-Dade County regions."""
    # Get all parks
    parks_data = parks_api.get_all_parks()
    
    # Initialize counters for each region
    region_counts = {
        "Northeast": 0,
        "Southeast": 0,
        "Southwest": 0,
        "Northwest": 0
    }
    
    # Initialize lists to store parks in each region
    region_parks = {
        "Northeast": [],
        "Southeast": [],
        "Southwest": [],
        "Northwest": []
    }
    
    if parks_data and 'features' in parks_data:
        for park in parks_data['features']:
            if 'geometry' in park and park['geometry']:
                coords = park['geometry']['coordinates']
                # GeoJSON uses [longitude, latitude] order
                lon, lat = coords[0], coords[1]
                region = categorize_location(lat, lon)
                region_counts[region] += 1
                region_parks[region].append(park['properties'].get('NAME', 'Unnamed Park'))
    
    return region_counts, region_parks

# Initialize APIs
@st.cache_resource
def get_apis():
    return {
        'Education': EducationAPI(),
        'Healthcare': HealthcareAPI(),
        'Emergency': EmergencyServicesAPI(),
        'GeoData': GeoDataAPI(),
        'Infrastructure': {
            'Bus Stops': BusStopsAPI(),
            'Libraries': LibrariesAPI(),
            'Parks': ParksAPI()
        }
    }

@st.cache_resource
def get_zip_validator():
    return ZIPValidator()

# Initialize APIs
apis = get_apis()
zip_validator = get_zip_validator()

def main():
    # Display the charts at the top
    st.header("📊 Miami-Dade County Overview")
    
    # Create a row with three columns for the charts
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.plotly_chart(plot_schools_histogram(), use_container_width=True)
    
    with col2:
        st.plotly_chart(plot_fire_station_proximity_pie(), use_container_width=True)
        
    with col3:
        st.plotly_chart(plot_zip_park_density_treemap(), use_container_width=True)
    
    # Create two columns for controls and main content
    control_col, main_col = st.columns([1, 3])

    with control_col:
        st.subheader("Control Panel")
        
        # Location input — key ties this to session state so value persists across tab switches
        location_input = st.text_input("Enter address or ZIP code", key="location_input")
        
        # Search radius
        radius = st.slider("Search radius (miles)", 1.0, 20.0, 5.0)
        
        # Category selection
        st.write("Education Facilities")
        show_public_schools = st.checkbox("Public Schools", value=True)
        show_private_schools = st.checkbox("Private Schools", value=True)
        show_charter_schools = st.checkbox("Charter Schools", value=True)
        
        st.write("Healthcare Facilities")
        show_hospitals = st.checkbox("Hospitals", value=True)
        show_mental_health = st.checkbox("Mental Health Centers", value=True)
        show_clinics = st.checkbox("Clinics", value=True)
        
        st.write("Emergency Services")
        show_police = st.checkbox("Police Stations", value=True)
        show_fire = st.checkbox("Fire Stations", value=True)
        
        st.write("Geographic Data")
        show_flood_zones = st.checkbox("Flood Zones", value=True)
        show_evacuation_routes = st.checkbox("Evacuation Routes", value=True)
        show_bus_routes = st.checkbox("Bus Routes", value=True)
        
        st.write("Infrastructure")
        show_bus_stops = st.checkbox("Bus Stops", value=True)
        show_libraries = st.checkbox("Libraries", value=True)
        show_parks = st.checkbox("Parks", value=True)

    with main_col:
        if location_input:
            st.header("🎯 Local Area Insights")
            
            # Get coordinates
            try:
                if location_input.isdigit() and len(location_input) == 5:
                    # Validate ZIP code
                    is_valid, message, zip_info = zip_validator.validate_zip(location_input)
                    if not is_valid:
                        st.error(message)
                        with st.expander("Show valid Miami-Dade County ZIP codes"):
                            valid_zips = sorted(list(zip_validator.get_all_zip_codes()))
                            zip_cols = st.columns(5)
                            for i, zip_code in enumerate(valid_zips):
                                zip_cols[i % 5].write(zip_code)
                    else:
                        coordinates = zip_validator.get_zip_coordinates(location_input)
                        if coordinates:
                            st.success(f"Found location: {coordinates}")
                            
                            # Get nearby facilities data
                            nearby_data = {
                                'schools': [],
                                'healthcare': [],
                                'emergency': [],
                                'infrastructure': [],
                                'geo_data': {
                                    'flood_zones': [],
                                    'evacuation_routes': [],
                                    'bus_routes': []
                                }
                            }
                            
                            # Get schools
                            nearby_zips = zip_validator.get_nearby_zips(location_input, radius)
                            for zip_code in nearby_zips:
                                if show_public_schools:
                                    schools = apis['Education'].get_schools_by_zip(zip_code, 'public')
                                    if schools and schools.get('success'):
                                        for school in schools['data'].get('schools', []):
                                            school['school_type'] = 'public'
                                            nearby_data['schools'].append(school)
                                
                                if show_private_schools:
                                    schools = apis['Education'].get_schools_by_zip(zip_code, 'private')
                                    if schools and schools.get('success'):
                                        for school in schools['data'].get('schools', []):
                                            school['school_type'] = 'private'
                                            nearby_data['schools'].append(school)
                                
                                if show_charter_schools:
                                    schools = apis['Education'].get_schools_by_zip(zip_code, 'charter')
                                    if schools and schools.get('success'):
                                        for school in schools['data'].get('schools', []):
                                            school['school_type'] = 'charter'
                                            nearby_data['schools'].append(school)
                            
                            # Get healthcare facilities
                            if show_hospitals:
                                hospitals = apis['Healthcare'].get_hospitals()
                                for facility in hospitals.get('features', []):
                                    if 'geometry' in facility and facility['geometry']:
                                        coords = facility['geometry']['coordinates']
                                        facility_coords = (coords[1], coords[0])
                                        if geodesic(coordinates, facility_coords).miles <= radius:
                                            facility['properties']['type'] = 'Hospital'
                                            nearby_data['healthcare'].append(facility)
                            
                            if show_mental_health:
                                mental_health = apis['Healthcare'].get_mental_health_centers()
                                for facility in mental_health.get('features', []):
                                    if 'geometry' in facility and facility['geometry']:
                                        coords = facility['geometry']['coordinates']
                                        facility_coords = (coords[1], coords[0])
                                        if geodesic(coordinates, facility_coords).miles <= radius:
                                            facility['properties']['type'] = 'Mental Health Center'
                                            nearby_data['healthcare'].append(facility)
                            
                            if show_clinics:
                                clinics = apis['Healthcare'].get_free_standing_clinics()
                                for facility in clinics.get('features', []):
                                    if 'geometry' in facility and facility['geometry']:
                                        coords = facility['geometry']['coordinates']
                                        facility_coords = (coords[1], coords[0])
                                        if geodesic(coordinates, facility_coords).miles <= radius:
                                            facility['properties']['type'] = 'Clinic'
                                            nearby_data['healthcare'].append(facility)
                            
                            # Get emergency services
                            if show_police:
                                police = apis['Emergency'].get_police_stations()
                                for service in police.get('features', []):
                                    if 'geometry' in service and service['geometry']:
                                        coords = service['geometry']['coordinates']
                                        service_coords = (coords[1], coords[0])
                                        if geodesic(coordinates, service_coords).miles <= radius:
                                            service['properties']['type'] = 'Police Station'
                                            nearby_data['emergency'].append(service)
                            
                            if show_fire:
                                fire = apis['Emergency'].get_fire_stations()
                                for service in fire.get('features', []):
                                    if 'geometry' in service and service['geometry']:
                                        coords = service['geometry']['coordinates']
                                        service_coords = (coords[1], coords[0])
                                        if geodesic(coordinates, service_coords).miles <= radius:
                                            service['properties']['type'] = 'Fire Station'
                                            nearby_data['emergency'].append(service)
                            
                            # Get geographic data
                            if show_flood_zones:
                                flood_zones = apis['GeoData'].get_flood_zones()
                                if flood_zones and 'features' in flood_zones:
                                    for zone in flood_zones['features']:
                                        if 'geometry' in zone and zone['geometry']:
                                            coords = zone['geometry']['coordinates'][0]
                                            for coord in coords:
                                                point_coords = (coord[1], coord[0])
                                                if geodesic(coordinates, point_coords).miles <= radius:
                                                    nearby_data['geo_data']['flood_zones'].append(zone)
                                                    break
                            
                            # Add infrastructure facilities
                            if show_bus_stops:
                                bus_stops = apis['Infrastructure']['Bus Stops'].get_all_stops()
                                for stop in bus_stops.get('features', []):
                                    if 'geometry' in stop and stop['geometry']:
                                        coords = stop['geometry']['coordinates']
                                        stop_coords = (coords[1], coords[0])
                                        if geodesic(coordinates, stop_coords).miles <= radius:
                                            stop['properties']['type'] = 'Bus Stop'
                                            nearby_data['infrastructure'].append(stop)
                            
                            if show_libraries:
                                libraries = apis['Infrastructure']['Libraries'].get_all_libraries()
                                for library in libraries.get('features', []):
                                    if 'geometry' in library and library['geometry']:
                                        coords = library['geometry']['coordinates']
                                        library_coords = (coords[1], coords[0])
                                        if geodesic(coordinates, library_coords).miles <= radius:
                                            library['properties']['type'] = 'Library'
                                            nearby_data['infrastructure'].append(library)
                            
                            if show_parks:
                                try:
                                    parks = apis['Infrastructure']['Parks'].get_all_parks()
                                except Exception:
                                    parks = {'features': []}
                                for park in parks.get('features', []):
                                    if 'geometry' in park and park['geometry']:
                                        coords = park['geometry']['coordinates']
                                        park_coords = (coords[1], coords[0])
                                        if geodesic(coordinates, park_coords).miles <= radius:
                                            park['properties']['type'] = 'Park'
                                            nearby_data['infrastructure'].append(park)
                            
                            # Create analysis tabs
                            tab1, tab2, tab3 = st.tabs([
                                "Proximity Analysis",
                                "Service Coverage Analysis",
                                "Risk Assessment"
                            ])
                            
                            with tab1:
                                st.subheader("📍 Proximity Analysis")
                                
                                # Create proximity chart
                                facility_counts = {
                                    'Schools': len(nearby_data['schools']),
                                    'Healthcare': len(nearby_data['healthcare']),
                                    'Emergency': len(nearby_data['emergency']),
                                    'Infrastructure': len(nearby_data['infrastructure'])
                                }
                                
                                fig = px.bar(
                                    x=list(facility_counts.keys()),
                                    y=list(facility_counts.values()),
                                    title=f'Number of Facilities Within {radius} Miles',
                                    labels={'x': 'Facility Type', 'y': 'Count'},
                                    color=list(facility_counts.keys()),
                                    color_discrete_sequence=px.colors.qualitative.Set3
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Show detailed facility lists in expanders
                                with st.expander("View Detailed Facility List"):
                                    if nearby_data['schools']:
                                        st.subheader("Schools")
                                        school_df = pd.DataFrame(nearby_data['schools'])
                                        st.dataframe(school_df[['NAME', 'school_type', 'ADDRESS', 'ZIPCODE']])
                                    
                                    if nearby_data['healthcare']:
                                        st.subheader("Healthcare Facilities")
                                        healthcare_df = pd.DataFrame([f['properties'] for f in nearby_data['healthcare']])
                                        st.dataframe(healthcare_df[['NAME', 'type', 'ADDRESS']])
                                    
                                    if nearby_data['emergency']:
                                        st.subheader("Emergency Services")
                                        emergency_df = pd.DataFrame([f['properties'] for f in nearby_data['emergency']])
                                        st.dataframe(emergency_df[['NAME', 'type', 'ADDRESS']])
                                    
                                    if nearby_data['infrastructure']:
                                        st.subheader("Infrastructure")
                                        infrastructure_df = pd.DataFrame([f['properties'] for f in nearby_data['infrastructure']])
                                        st.dataframe(infrastructure_df[['NAME', 'type', 'ADDRESS']])
                            
                            with tab2:
                                st.subheader("📊 Service Coverage Analysis")
                                
                                # Calculate coverage scores
                                coverage_data = pd.DataFrame({
                                    'Category': ['Education', 'Healthcare', 'Emergency', 'Infrastructure'],
                                    'Coverage Score': [
                                        min(len(nearby_data['schools']) / 5, 10),
                                        min(len(nearby_data['healthcare']) / 3, 10),
                                        min(len(nearby_data['emergency']) / 2, 10),
                                        min(len(nearby_data['infrastructure']) / 8, 10)
                                    ]
                                })
                                
                                fig = px.bar(
                                    coverage_data,
                                    x='Category',
                                    y='Coverage Score',
                                    title='Service Coverage Analysis (0-10 scale)',
                                    color='Category',
                                    color_discrete_sequence=px.colors.qualitative.Set1
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                st.info("Coverage scores are normalized on a scale of 0-10, where 10 represents excellent coverage.")
                            
                            with tab3:
                                st.subheader("⚠️ Risk Assessment")
                                
                                # Calculate risk factors
                                risk_data = pd.DataFrame({
                                    'Risk Factor': [
                                        'Flood Zone Coverage',
                                        'Emergency Service Access',
                                        'Healthcare Access',
                                        'Infrastructure Access'
                                    ],
                                    'Risk Score': [
                                        min(len(nearby_data['geo_data']['flood_zones']) * 2, 10),
                                        max(0, 10 - len(nearby_data['emergency']) * 3),
                                        max(0, 10 - len(nearby_data['healthcare']) * 2),
                                        max(0, 10 - len(nearby_data['infrastructure']) * 1)
                                    ]
                                })
                                
                                fig = px.bar(
                                    risk_data,
                                    x='Risk Factor',
                                    y='Risk Score',
                                    title='Risk Assessment (Higher Score = Higher Risk)',
                                    color='Risk Factor',
                                    color_discrete_sequence=px.colors.sequential.Reds
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Calculate overall risk score
                                risk_score = risk_data['Risk Score'].mean()
                                risk_color = 'green' if risk_score < 4 else 'yellow' if risk_score < 7 else 'red'
                                st.markdown(f"### Overall Risk Level: <span style='color: {risk_color}'>{risk_score:.1f}/10</span>", 
                                          unsafe_allow_html=True)
                                
                                # Add geographic data summary
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Flood Zones", 
                                            len(nearby_data['geo_data']['flood_zones']),
                                            help="Number of flood zones in your area")
                                with col2:
                                    st.metric("Emergency Services",
                                            len(nearby_data['emergency']),
                                            help="Number of emergency services in your area")
                                with col3:
                                    st.metric("Healthcare Facilities",
                                            len(nearby_data['healthcare']),
                                            help="Number of healthcare facilities in your area")
                else:
                    # Handle address input
                    geolocator = Nominatim(user_agent="miami_explorer")
                    location = geolocator.geocode(location_input)
                    if location:
                        st.success(f"Found location: ({location.latitude}, {location.longitude})")
                        coordinates = (location.latitude, location.longitude)
                        # Add same analysis as above but using location coordinates
                    else:
                        st.error("Could not find the specified address")
            except Exception as e:
                st.error(f"Error processing location: {str(e)}")

if __name__ == "__main__":
    main()