# Know-Your-Zip — CLAUDE.md
## Read this EVERY session before touching ANY code.
## This is your source of truth. If you are unsure, re-read this file.

---

## What This App Is
A Miami-Dade County ZIP-code explorer and neighborhood intelligence tool.
- Users enter a ZIP code or street address
- The app shows nearby schools, hospitals, emergency services, transit stops, libraries, and parks on an interactive map
- An AI assistant (Llama 3.3) answers questions about the neighborhood using live government data
- Built exclusively on Miami-Dade County open data (ArcGIS REST Services)
- Designed so new government datasets can be added without touching the UI or entry point

**This is a flagship interview project. Every file must be production-quality.**

---

## Stack
- **Framework:** Streamlit
- **Language:** Python 3.11+ — strict typing with `mypy`. No bare `dict`, no `Any`. Ever.
- **AI Model:** ServiceNow-AI/Apriel-1.6-15b-Thinker via Together.ai SDK 1.x
- **Map:** Folium + streamlit-folium
- **Charts:** Plotly
- **Data:** Miami-Dade County ArcGIS REST Services (~20 public endpoints)
- **Caching:** `@st.cache_resource` + optional local pickle via `src/utils/data_loader.py`
- **Validation:** Pydantic v2 — ALL external API responses validated before use
- **Linting:** ruff (style) + mypy (types) — both must pass clean before any commit

---

## Canonical Folder Structure — Never Deviate From This
```
src/
├── api/                    ← one file per data domain; all inherit BaseAPIClient
│   ├── base.py             ← BaseAPIClient: retry, timeout, error handling
│   ├── education.py        ← public, private, charter schools
│   ├── healthcare.py       ← hospitals, mental health centers, clinics
│   ├── emergency.py        ← police stations, fire stations
│   ├── infrastructure.py   ← bus stops, libraries, parks
│   └── geo.py              ← ZIP boundaries, flood zones, evacuation routes, bus routes
├── models/                 ← Pydantic models for every data type
│   ├── school.py
│   ├── healthcare.py
│   ├── emergency.py
│   ├── infrastructure.py
│   └── location.py         ← ZipLocation, Coordinates, BoundingBox
├── utils/
│   ├── zip_validator.py    ← ZIP lookup only; uses src/api/geo.py
│   ├── geocoder.py         ← address → coordinates only (Nominatim wrapper)
│   ├── distance.py         ← ALL geodesic math here and ONLY here
│   ├── response.py         ← ResponseNormalizer
│   └── data_loader.py      ← cache persistence helpers
├── ui/
│   ├── dashboard.py        ← Plotly charts tab — UI only, no API calls
│   ├── map_explorer.py     ← Folium map tab coordinator — ≤200 lines
│   ├── map_builder.py      ← marker/layer construction functions
│   ├── filters.py          ← filter UI widgets and filter logic
│   └── ai_assistant.py     ← Chat tab — UI + prompt construction only
├── constants.py            ← ALL magic values live here, nowhere else
└── logger.py               ← single shared logger
app.py                      ← entry point: page config + tab routing ONLY, ≤60 lines
data/                       ← static GeoJSON assets (checked in)
legacy/                     ← FROZEN — nothing here may be imported
```

---

## Constants File — `src/constants.py`
**Every hardcoded value lives here. Nowhere else. No exceptions.**
```python
# Geography
MIAMI_DEFAULT_LAT: float = 25.7617
MIAMI_DEFAULT_LON: float = -80.1918
MIAMI_DEFAULT_ZOOM: int = 11
MIAMI_COUNTY_BOUNDS = {"lat_min": 25.1, "lat_max": 26.0, "lon_min": -80.9, "lon_max": -80.0}

# Search
DEFAULT_SEARCH_RADIUS_MILES: float = 5.0
MIN_SEARCH_RADIUS_MILES: float = 1.0
MAX_SEARCH_RADIUS_MILES: float = 20.0
MAX_FEATURES_PER_REQUEST: int = 500

# APIs
ARCGIS_BASE_URL = "https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services"
OPENDATA_BASE_URL = "https://opendata.arcgis.com/datasets/MDC"
API_TIMEOUT_SECONDS: int = 10
API_MAX_RETRIES: int = 3
API_RETRY_BACKOFF_FACTOR: float = 0.5

# AI
AI_MODEL = "ServiceNow-AI/Apriel-1.6-15b-Thinker"
AI_MAX_TOKENS: int = 1024
AI_TEMPERATURE: float = 0.7

# Cache
CACHE_TTL_SECONDS: int = 3600
```

---

## NASA Power of 10 — Adapted for Python

1. **Functions max 40 lines.** If longer, extract helpers. No exceptions.
2. **Every loop has a hard cap.** Use `MAX_FEATURES_PER_REQUEST`. No `while True`. Ever.
3. **Every API call has try/except + timeout.** No silent failures. Log every exception via `src/logger.py`.
4. **No magic strings or numbers.** Use `src/constants.py`. Every single one.
5. **One file = one responsibility.** No UI code in API files. No API calls in chart/UI files.
6. **Typed signatures on every function.** Use `mypy`. Use dataclasses or Pydantic models — never bare `dict`.
7. **Commit after every feature.** Never accumulate uncommitted changes across sessions.
8. **No URL construction outside `src/api/base.py`.** All endpoint paths built in one place.
9. **All errors handled and logged.** Never `except: pass`. Never swallow an exception silently.
10. **Pydantic for all external data.** Every ArcGIS response validated against a Pydantic model before any code touches its fields.

---

## Security Rules

- **Secrets:** `TOGETHER_API_KEY` in `.env` or `st.secrets` only. Never hardcoded.
- **Input validation:** All user-supplied ZIP codes and addresses validated before any API call.
- **External data:** ArcGIS responses treated as untrusted. Pydantic models are the trust boundary.
- **No dynamic URL construction** from user input. ZIP codes validated to known format before use.
- **`.env` is in `.gitignore`.** Verify before every push.

---

## Adding a New Miami-Dade Dataset
Follow this exact sequence — zero changes to `app.py` or any `src/ui/` file:

1. Add endpoint URL constant(s) to `src/constants.py`
2. Create `src/models/<dataset>.py` with a Pydantic model for the response
3. Create `src/api/<dataset>.py` inheriting `BaseAPIClient`
4. Add a new layer option in `src/ui/filters.py`
5. Add marker rendering in `src/ui/map_builder.py`
6. Commit

---

## Context Management (Anti-Spaghetti Protocol)
- **Start every session:** "Read CLAUDE.md first."
- **One feature per session.** Finish it. Commit. Then start the next session.
- **Never touch more than 3 files at once.**
- **At 70% context:** run `/compact` before continuing.
- **At 90% context:** run `/clear` — start fresh, re-read CLAUDE.md.

---

## Current Session Focus
**UPDATE THIS AT THE START OF EVERY SESSION.**

Session 1 (2026-03-24): Writing CLAUDE.md + creating src/constants.py (Step 1 of 8 in the refactor plan).
Session 2 (2026-03-24): Created all 5 domain API files (education, healthcare, emergency, infrastructure, geo) inheriting BaseAPIClient. Fixed broken imports in map_explorer.py and src/ui/data_fetcher.py.
Session 3 (2026-03-24): Caching + shared location state.
  - src/bootstrap.py: added resolved_coords, fetch_key to shared session defaults
  - map_explorer.py: added _filters_hash + fetch deduplication (skips re-fetch if key unchanged); stores resolved_coords for cross-tab sharing
  - dashboard.py: reads resolved_coords from session state (no re-entry needed after Map search); fixed broken address branch (now calls _resolve_coords + _run_analysis); replaced magic numbers with src.constants values; extracted helpers to keep functions ≤40 lines; fixed fragile DataFrame column access
Session 4 (2026-03-24): Cross-tab state unification + AI assistant rewrite.
  - src/bootstrap.py: added 15 filter_* keys + last_location + filter_radius to _DEFAULTS so filter state persists across tabs
  - src/ui/filters.py: added key= params to all checkboxes and slider — filter state now auto-persists in session state (Map ↔ AI sync)
  - src/ui/ai_assistant.py: NEW production rewrite — reads resolved_coords (no re-geocoding when switching from Map tab), uses render_filter_sidebar(), uses src.api.* imports, uses Together chat completions API, all CLAUDE.md rules applied
  - app.py: updated Bot tab import from legacy root ai_assistant to src.ui.ai_assistant
Session 5 (2026-03-24): Dashboard filter sync + fetch deduplication + model swap.
  - src/ui/dashboard.py: NEW canonical location — src.api.* imports, render_filter_sidebar(), fetch dedup (dash_fetch_key/dash_data), loop caps, all CLAUDE.md rules applied
  - src/bootstrap.py: added dash_fetch_key + dash_data session-state defaults
  - app.py: updated Dashboard import from root dashboard to src.ui.dashboard
  - src/constants.py: swapped AI_MODEL to ServiceNow-AI/Apriel-1.6-15b-Thinker
Session 6 (2026-03-24): charts.py migration + root-file retirement.
  - src/ui/charts.py: NEW canonical location — migrated plot_schools_histogram, plot_fire_station_proximity_pie, plot_zip_park_density_treemap + helper _get_schools_by_zip; fixed all imports to src.api.*; replaced geodesic with miles_between (src.utils.distance); added None-safety, loop caps, type annotations, constants for all magic values
  - src/constants.py: added CHART_HISTOGRAM_YAXIS_MAX, CHART_TITLE_FONT_SIZE, CHART_BAR_TEXT_FONT_SIZE, FIRE_PROXIMITY_LABEL_*, FIRE_PROXIMITY_*_MAX, COLOR_CORAL_LIGHTEST, COLOR_CORAL_MEDIUM
  - src/ui/dashboard.py: replaced legacy `from charts import` with `from src.ui.charts import`
  - charts.py, dashboard.py (root): deleted (dead code — app.py already used src.ui.dashboard)
  Next: audit src/zip_validator.py — legacy class has bare print() debug statements, bare dict, and no type annotations; candidate for future session refactor.
Session 7 (2026-03-24): Unified location state + canonical map_explorer migration.
  - src/ui/map_explorer.py: NEW canonical location — migrated from root map_explorer.py; removed redundant _init_session_state(); added st.session_state["location_submitted"] = True after successful fetch
  - app.py: fixed Map tab import to `from src.ui import map_explorer` (consistent with Dashboard/AI)
  - src/bootstrap.py: added location_submitted: False and ai_context_key: None to _DEFAULTS
  - src/ui/dashboard.py: removed location form + _resolve_coords/_get_coords_for_input/_render_valid_zips helpers; main() now reads resolved_coords/last_location from session state; shows info banner if location_submitted is False
  - src/ui/ai_assistant.py: removed location form + _resolve_location/_handle_location_submit/_render_location_panel; added _ensure_location_context() auto-builds AI context from session state on radius/location change; shows info banner if location_submitted is False
Session 8 (2026-03-24): Pickle cache + ThreadPoolExecutor in BaseAPIClient.
  - src/constants.py: added CACHE_KEY_SCHOOLS_BY_ZIP, FETCH_MANY_MAX_WORKERS
  - src/utils/data_loader.py: NEW — typed pickle cache helpers (load_pickle, save_pickle, is_cache_valid, cache_path)
  - src/api/base.py: added fetch_many() with ThreadPoolExecutor for parallel ArcGIS requests
  - src/ui/charts.py: replaced @st.cache_data on _get_schools_by_zip() with disk pickle cache (load_pickle/save_pickle); cache persists across server restarts
Session 9 (2026-03-24): ZIPValidator rewrite + legacy root file retirement.
  - src/zip_validator.py: full rewrite — removed all print() statements; replaced with structured logger calls; added type annotations; used ARCGIS_BASE_URL+SERVICE_ZIP_CODES+API_TIMEOUT_SECONDS from constants; uses src.utils.distance.miles_between; loop caps with MAX_FEATURES_PER_REQUEST
  - Deleted root-level legacy files: education.py, emergency_services.py, geo_data.py, healthcare.py, infrastructure.py, ai_assistant.py, map_explorer.py, __init__.py
  Next: Session 10 — mypy + ruff clean pass; src/utils/zip_validator.py migration (canonical location per CLAUDE.md)
