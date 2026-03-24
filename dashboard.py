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
from src.constants import (
    COVERAGE_SCORE_MAX,
    COVERAGE_DIVISOR_SCHOOLS,
    COVERAGE_DIVISOR_HEALTHCARE,
    COVERAGE_DIVISOR_EMERGENCY,
    COVERAGE_DIVISOR_INFRASTRUCTURE,
    RISK_THRESHOLD_LOW,
    RISK_THRESHOLD_MEDIUM,
    RISK_WEIGHT_FLOOD,
    RISK_WEIGHT_EMERGENCY,
    RISK_WEIGHT_HEALTHCARE,
    RISK_WEIGHT_INFRASTRUCTURE,
    CHART_COLOR_SEQUENCE,
)

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

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _safe_dataframe(rows: list, cols: list[str]) -> pd.DataFrame:
    """Return a DataFrame with only the columns that actually exist in the data."""
    df = pd.DataFrame(rows)
    present = [c for c in cols if c in df.columns]
    return df[present] if present else df


def _fetch_schools(coordinates: tuple, radius: float, nearby_zips: list, show_public: bool, show_private: bool, show_charter: bool) -> list:
    schools: list = []
    type_flags = [("public", show_public), ("private", show_private), ("charter", show_charter)]
    for school_type, enabled in type_flags:
        if not enabled:
            continue
        for zip_code in nearby_zips:
            result = apis["Education"].get_schools_by_zip(zip_code, school_type)
            if result and result.get("success"):
                for s in result["data"].get("schools", []):
                    s["school_type"] = school_type
                    schools.append(s)
    return schools


def _fetch_point_features(api_call, label: str, coordinates: tuple, radius: float) -> list:
    """Filter point GeoJSON features within radius and tag with label."""
    items: list = []
    data = api_call() or {}
    for feature in data.get("features", []):
        geom = feature.get("geometry") or {}
        raw = geom.get("coordinates", [])
        if len(raw) < 2:
            continue
        if geodesic(coordinates, (raw[1], raw[0])).miles <= radius:
            feature["properties"]["type"] = label
            items.append(feature)
    return items


def _fetch_flood_zones(coordinates: tuple, radius: float) -> list:
    zones: list = []
    data = apis["GeoData"].get_flood_zones() or {}
    for zone in data.get("features", []):
        geom = zone.get("geometry") or {}
        ring = geom.get("coordinates", [[]])[0]
        for coord in ring:
            if geodesic(coordinates, (coord[1], coord[0])).miles <= radius:
                zones.append(zone)
                break
    return zones


def _fetch_nearby_data(coordinates: tuple, radius: float, show: dict) -> dict:
    closest_zip = zip_validator.get_closest_zip(coordinates)
    nearby_zips = zip_validator.get_nearby_zips(closest_zip, radius) if closest_zip else []
    schools = _fetch_schools(coordinates, radius, nearby_zips, show["public_schools"], show["private_schools"], show["charter_schools"])
    healthcare: list = []
    if show["hospitals"]:
        healthcare += _fetch_point_features(apis["Healthcare"].get_hospitals, "Hospital", coordinates, radius)
    if show["mental_health"]:
        healthcare += _fetch_point_features(apis["Healthcare"].get_mental_health_centers, "Mental Health Center", coordinates, radius)
    if show["clinics"]:
        healthcare += _fetch_point_features(apis["Healthcare"].get_free_standing_clinics, "Clinic", coordinates, radius)
    emergency: list = []
    if show["police"]:
        emergency += _fetch_point_features(apis["Emergency"].get_police_stations, "Police Station", coordinates, radius)
    if show["fire"]:
        emergency += _fetch_point_features(apis["Emergency"].get_fire_stations, "Fire Station", coordinates, radius)
    infrastructure: list = []
    if show["bus_stops"]:
        infrastructure += _fetch_point_features(apis["Infrastructure"]["Bus Stops"].get_all_stops, "Bus Stop", coordinates, radius)
    if show["libraries"]:
        infrastructure += _fetch_point_features(apis["Infrastructure"]["Libraries"].get_all_libraries, "Library", coordinates, radius)
    if show["parks"]:
        try:
            infrastructure += _fetch_point_features(apis["Infrastructure"]["Parks"].get_all_parks, "Park", coordinates, radius)
        except Exception:
            pass
    flood_zones = _fetch_flood_zones(coordinates, radius) if show["flood_zones"] else []
    return {"schools": schools, "healthcare": healthcare, "emergency": emergency, "infrastructure": infrastructure, "geo_data": {"flood_zones": flood_zones}}


def _render_proximity_tab(nearby_data: dict, radius: float) -> None:
    st.subheader("📍 Proximity Analysis")
    counts = {
        "Schools": len(nearby_data["schools"]),
        "Healthcare": len(nearby_data["healthcare"]),
        "Emergency": len(nearby_data["emergency"]),
        "Infrastructure": len(nearby_data["infrastructure"]),
    }
    fig = px.bar(x=list(counts.keys()), y=list(counts.values()),
                 title=f"Facilities Within {radius} Miles",
                 labels={"x": "Facility Type", "y": "Count"},
                 color=list(counts.keys()), color_discrete_sequence=CHART_COLOR_SEQUENCE)
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("View Detailed Facility List"):
        if nearby_data["schools"]:
            st.subheader("Schools")
            st.dataframe(_safe_dataframe(nearby_data["schools"], ["NAME", "school_type", "ADDRESS", "ZIPCODE"]))
        for label, key in [("Healthcare Facilities", "healthcare"), ("Emergency Services", "emergency"), ("Infrastructure", "infrastructure")]:
            if nearby_data[key]:
                st.subheader(label)
                st.dataframe(_safe_dataframe([f["properties"] for f in nearby_data[key]], ["NAME", "type", "ADDRESS"]))


def _render_coverage_tab(nearby_data: dict) -> None:
    st.subheader("📊 Service Coverage Analysis")
    coverage_data = pd.DataFrame({
        "Category": ["Education", "Healthcare", "Emergency", "Infrastructure"],
        "Coverage Score": [
            min(len(nearby_data["schools"]) / COVERAGE_DIVISOR_SCHOOLS, COVERAGE_SCORE_MAX),
            min(len(nearby_data["healthcare"]) / COVERAGE_DIVISOR_HEALTHCARE, COVERAGE_SCORE_MAX),
            min(len(nearby_data["emergency"]) / COVERAGE_DIVISOR_EMERGENCY, COVERAGE_SCORE_MAX),
            min(len(nearby_data["infrastructure"]) / COVERAGE_DIVISOR_INFRASTRUCTURE, COVERAGE_SCORE_MAX),
        ],
    })
    fig = px.bar(coverage_data, x="Category", y="Coverage Score",
                 title="Service Coverage (0-10 scale)", color="Category",
                 color_discrete_sequence=CHART_COLOR_SEQUENCE)
    st.plotly_chart(fig, use_container_width=True)
    st.info("Coverage scores are normalized on a scale of 0–10, where 10 represents excellent coverage.")


def _render_risk_tab(nearby_data: dict) -> None:
    st.subheader("⚠️ Risk Assessment")
    risk_data = pd.DataFrame({
        "Risk Factor": ["Flood Zone Coverage", "Emergency Service Access", "Healthcare Access", "Infrastructure Access"],
        "Risk Score": [
            min(len(nearby_data["geo_data"]["flood_zones"]) * RISK_WEIGHT_FLOOD, COVERAGE_SCORE_MAX),
            max(0, COVERAGE_SCORE_MAX - len(nearby_data["emergency"]) * RISK_WEIGHT_EMERGENCY),
            max(0, COVERAGE_SCORE_MAX - len(nearby_data["healthcare"]) * RISK_WEIGHT_HEALTHCARE),
            max(0, COVERAGE_SCORE_MAX - len(nearby_data["infrastructure"]) * RISK_WEIGHT_INFRASTRUCTURE),
        ],
    })
    fig = px.bar(risk_data, x="Risk Factor", y="Risk Score",
                 title="Risk Assessment (Higher = Higher Risk)", color="Risk Factor",
                 color_discrete_sequence=px.colors.sequential.Reds)
    st.plotly_chart(fig, use_container_width=True)
    risk_score = risk_data["Risk Score"].mean()
    risk_color = "green" if risk_score < RISK_THRESHOLD_LOW else "orange" if risk_score < RISK_THRESHOLD_MEDIUM else "red"
    st.markdown(f"### Overall Risk Level: <span style='color:{risk_color}'>{risk_score:.1f}/10</span>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Flood Zones", len(nearby_data["geo_data"]["flood_zones"]), help="Flood zones in your area")
    c2.metric("Emergency Services", len(nearby_data["emergency"]), help="Emergency services in your area")
    c3.metric("Healthcare Facilities", len(nearby_data["healthcare"]), help="Healthcare facilities in your area")


def _run_analysis(coordinates: tuple, location_label: str, radius: float, show: dict) -> None:
    st.success(f"Showing results for: {location_label}")
    with st.spinner("Fetching nearby data…"):
        nearby_data = _fetch_nearby_data(coordinates, radius, show)
    tab1, tab2, tab3 = st.tabs(["Proximity Analysis", "Service Coverage Analysis", "Risk Assessment"])
    with tab1:
        _render_proximity_tab(nearby_data, radius)
    with tab2:
        _render_coverage_tab(nearby_data)
    with tab3:
        _render_risk_tab(nearby_data)


def _resolve_coords(location_input: str) -> tuple | None:
    """Return (lat, lon) for a ZIP or address, or None on failure."""
    if location_input.isdigit() and len(location_input) == 5:
        is_valid, message, _ = zip_validator.validate_zip(location_input)
        if not is_valid:
            st.error(message)
            with st.expander("Show valid Miami-Dade County ZIP codes"):
                valid_zips = sorted(zip_validator.get_all_zip_codes())
                cols = st.columns(5)
                for i, z in enumerate(valid_zips):
                    cols[i % 5].write(z)
            return None
        return zip_validator.get_zip_coordinates(location_input)
    geolocator = Nominatim(user_agent="miami_explorer")
    location = geolocator.geocode(location_input)
    if not location:
        st.error("Could not find the specified address.")
        return None
    return (location.latitude, location.longitude)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    st.header("📊 Miami-Dade County Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(plot_schools_histogram(), use_container_width=True)
    with col2:
        st.plotly_chart(plot_fire_station_proximity_pie(), use_container_width=True)
    with col3:
        st.plotly_chart(plot_zip_park_density_treemap(), use_container_width=True)

    control_col, main_col = st.columns([1, 3])

    with control_col:
        st.subheader("Control Panel")
        # Shared key — value persists when switching tabs from Map Explorer
        if st.session_state.get("resolved_coords") and st.session_state.get("location_input"):
            st.info(f"Map location in use: **{st.session_state.location_input}**")
        location_input = st.text_input("Enter address or ZIP code", key="location_input")
        radius = st.slider("Search radius (miles)", 1.0, 20.0, 5.0)
        st.write("Education")
        show = {
            "public_schools": st.checkbox("Public Schools", value=True),
            "private_schools": st.checkbox("Private Schools", value=True),
            "charter_schools": st.checkbox("Charter Schools", value=True),
        }
        st.write("Healthcare")
        show["hospitals"] = st.checkbox("Hospitals", value=True)
        show["mental_health"] = st.checkbox("Mental Health Centers", value=True)
        show["clinics"] = st.checkbox("Clinics", value=True)
        st.write("Emergency Services")
        show["police"] = st.checkbox("Police Stations", value=True)
        show["fire"] = st.checkbox("Fire Stations", value=True)
        st.write("Geographic Data")
        show["flood_zones"] = st.checkbox("Flood Zones", value=True)
        show["bus_stops"] = st.checkbox("Bus Stops", value=True)
        show["libraries"] = st.checkbox("Libraries", value=True)
        show["parks"] = st.checkbox("Parks", value=True)

    with main_col:
        # Use pre-resolved coords from Map Explorer if available and input matches
        stored_coords = st.session_state.get("resolved_coords")
        stored_input = st.session_state.get("location_input", "")
        if stored_coords and location_input and location_input == stored_input:
            st.header("🎯 Local Area Insights")
            _run_analysis(stored_coords, location_input, radius, show)
        elif location_input:
            st.header("🎯 Local Area Insights")
            try:
                coordinates = _resolve_coords(location_input)
                if coordinates:
                    _run_analysis(coordinates, location_input, radius, show)
            except Exception as e:
                st.error(f"Error processing location: {e}")


if __name__ == "__main__":
    main()