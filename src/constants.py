"""
Central constants for Know-Your-Zip.
Every magic value in the project lives here. Nowhere else. No exceptions.
"""

# ---------------------------------------------------------------------------
# Geography — Miami-Dade County
# ---------------------------------------------------------------------------

MIAMI_DEFAULT_LAT: float = 25.7617
MIAMI_DEFAULT_LON: float = -80.1918
MIAMI_DEFAULT_ZOOM: int = 10
MIAMI_SEARCH_ZOOM: int = 12  # zoom level after a successful ZIP / address lookup

# Broad county boundary check (used to reject out-of-county coordinates)
MIAMI_COUNTY_BOUNDS: dict[str, float] = {
    "lat_min": 24.8,
    "lat_max": 26.2,
    "lon_min": -81.0,
    "lon_max": -79.8,
}

# North/South and East/West split for regional labeling
MIAMI_REGION_LAT_BOUNDARY: float = 25.85
MIAMI_REGION_LON_BOUNDARY: float = -80.20

# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

DEFAULT_SEARCH_RADIUS_MILES: float = 5.0
MIN_SEARCH_RADIUS_MILES: float = 1.0
MAX_SEARCH_RADIUS_MILES: float = 20.0
MAX_FEATURES_PER_REQUEST: int = 500

# Max distance (miles) when snapping an address to the nearest ZIP centroid
MAX_NEAREST_ZIP_MILES: float = 10.0

# ---------------------------------------------------------------------------
# ArcGIS REST API — Base URLs
# ---------------------------------------------------------------------------

ARCGIS_BASE_URL = "https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services"
OPENDATA_BASE_URL = "https://opendata.arcgis.com/datasets/MDC"

# Standard ArcGIS query parameters (appended to every feature query)
ARCGIS_QUERY_PARAMS: dict[str, str] = {
    "outFields": "*",
    "where": "1=1",
    "f": "geojson",
    "outSR": "4326",
}

# ---------------------------------------------------------------------------
# ArcGIS Service Paths (relative to ARCGIS_BASE_URL)
# ---------------------------------------------------------------------------

# Education
SERVICE_PUBLIC_SCHOOLS = "/SchoolSite_gdb/FeatureServer/0/query"
SERVICE_PRIVATE_SCHOOLS = "/PrivateSchool_gdb/FeatureServer/0/query"
SERVICE_CHARTER_SCHOOLS = "/CharterSchool_gdb/FeatureServer/0/query"
SERVICE_SCHOOL_RATINGS = "/SchoolRatings/FeatureServer/0/query"
SERVICE_SCHOOL_BOUNDARIES = "/SchoolBoundaries/FeatureServer/0/query"

# Healthcare (opendata.arcgis.com)
SERVICE_HOSPITALS = "https://opendata.arcgis.com/datasets/MDC::hospitals.geojson"
SERVICE_MENTAL_HEALTH = "/MentalHealthCenter_gdb/FeatureServer/0/query"
SERVICE_CLINICS = "/FreeStandingClinic_gdb/FeatureServer/0/query"

# Emergency Services
SERVICE_POLICE = "/PoliceStation_gdb/FeatureServer/0/query"
SERVICE_FIRE = "/FireStation_gdb/FeatureServer/0/query"

# Infrastructure
SERVICE_BUS_STOPS = "/Bus_Stop_Maintenance_View_Layer/FeatureServer/1/query"
SERVICE_LIBRARIES = "/Library_gdb/FeatureServer/0/query"
SERVICE_PARKS = "/Parks/FeatureServer/0/query"

# Geographic / GIS
SERVICE_ZIP_CODES = "/ZipCode_gdb/FeatureServer/0/query"
SERVICE_FLOOD_ZONES = "/FEMAFloodZone_gdb/FeatureServer/0/query"
SERVICE_EVACUATION_ROUTES = "/PrimaryEvacuationRoute_gdb/FeatureServer/0/query"
SERVICE_BUS_ROUTES = "/BusRoutes/FeatureServer/0/query"

# ---------------------------------------------------------------------------
# HTTP Client
# ---------------------------------------------------------------------------

API_TIMEOUT_SECONDS: int = 10
API_MAX_RETRIES: int = 3
API_RETRY_BACKOFF_FACTOR: float = 0.5
API_RETRY_DELAY_SECONDS: int = 2

# ---------------------------------------------------------------------------
# AI Model (Together.ai)
# ---------------------------------------------------------------------------

AI_MODEL = "ServiceNow-AI/Apriel-1.6-15b-Thinker"
AI_MAX_TOKENS: int = 1024
AI_TEMPERATURE: float = 0.7
AI_GEOCODER_USER_AGENT = "miami_explorer"

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

CACHE_TTL_SECONDS: int = 3600
CACHE_DIRECTORY = "cache"
CACHE_EXPIRY_DAYS: int = 1

# Pickle cache keys for expensive county-wide chart data
CACHE_KEY_SCHOOLS_BY_ZIP: str = "schools_by_zip"

# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------

# Max threads used by BaseAPIClient.fetch_many() for parallel ArcGIS requests
FETCH_MANY_MAX_WORKERS: int = 4

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_DIRECTORY = "logs"
LOG_MAX_BYTES: int = 10_485_760  # 10 MB
LOG_BACKUP_COUNT: int = 5

# ---------------------------------------------------------------------------
# Map Display
# ---------------------------------------------------------------------------

MAP_DEFAULT_WIDTH: int = 800
MAP_DEFAULT_HEIGHT: int = 600
MAP_POPUP_MAX_WIDTH: int = 300

# Layer opacity / weight
LAYER_FLOOD_FILL_OPACITY: float = 0.3
LAYER_FLOOD_WEIGHT: int = 1
LAYER_EVACUATION_WEIGHT: int = 3
LAYER_EVACUATION_OPACITY: float = 0.8
LAYER_BUS_ROUTE_WEIGHT: int = 2
LAYER_BUS_ROUTE_OPACITY: float = 0.7

# Marker colors by facility type (Folium named colors)
MARKER_COLOR: dict[str, str] = {
    "public_school": "blue",
    "private_school": "lightblue",
    "charter_school": "darkblue",
    "police": "darkred",
    "fire": "red",
    "hospital": "green",
    "mental_health": "lightgreen",
    "clinic": "darkgreen",
    "bus_stop": "purple",
    "library": "pink",
    "park": "beige",
    "user_location": "black",
}

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

# Brand palette
COLOR_PRIMARY = "#0E7C86"      # teal
COLOR_SECONDARY = "#FF6B4A"    # coral
COLOR_ACCENT_1 = "#4BBFD4"     # light blue
COLOR_ACCENT_2 = "#FFB39A"     # light coral
CHART_COLOR_SEQUENCE = [COLOR_PRIMARY, COLOR_ACCENT_1, COLOR_SECONDARY, COLOR_ACCENT_2]

CHART_HEIGHT: int = 450
CHART_HISTOGRAM_BINS: int = 6
CHART_HISTOGRAM_YAXIS_MAX: int = 40
CHART_TITLE_FONT_SIZE: int = 24
CHART_BAR_TEXT_FONT_SIZE: int = 14

# Fire station proximity pie — distance-to-nearest thresholds (miles)
FIRE_PROXIMITY_LABEL_NEAR: str = "0-1 mile"
FIRE_PROXIMITY_LABEL_CLOSE: str = "2-3 miles"
FIRE_PROXIMITY_LABEL_MEDIUM: str = "4-5 miles"
FIRE_PROXIMITY_LABEL_FAR: str = "6+ miles"
FIRE_PROXIMITY_NEAR_MAX: float = 1.0
FIRE_PROXIMITY_CLOSE_MAX: float = 3.0
FIRE_PROXIMITY_MEDIUM_MAX: float = 5.0

# Additional coral tones for the proximity pie gradient
COLOR_CORAL_LIGHTEST: str = "#FFDDD5"  # lightest coral (largest segment)
COLOR_CORAL_MEDIUM: str = "#FF8C69"    # medium coral

# ---------------------------------------------------------------------------
# Coverage & Risk Score Thresholds
# ---------------------------------------------------------------------------

# Divisors used to normalize raw counts into 0–10 coverage scores
COVERAGE_SCORE_MAX: int = 10
COVERAGE_DIVISOR_SCHOOLS: int = 5
COVERAGE_DIVISOR_HEALTHCARE: int = 3
COVERAGE_DIVISOR_EMERGENCY: int = 2
COVERAGE_DIVISOR_INFRASTRUCTURE: int = 8

# Risk score thresholds for color-coded badges
RISK_THRESHOLD_LOW: int = 4    # ≤4 → green (low risk)
RISK_THRESHOLD_MEDIUM: int = 7  # ≤7 → yellow (medium risk)
# >7 → red (high risk)

# Risk component multipliers
RISK_WEIGHT_FLOOD: int = 2
RISK_WEIGHT_EMERGENCY: int = 3
RISK_WEIGHT_HEALTHCARE: int = 2
RISK_WEIGHT_INFRASTRUCTURE: int = 1

# ---------------------------------------------------------------------------
# Input Validation
# ---------------------------------------------------------------------------

ZIP_CODE_PATTERN = r"^\d{5}$"
ZIP_CODE_LENGTH: int = 5
