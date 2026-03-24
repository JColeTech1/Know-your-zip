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
- **AI Model:** Llama 3.3-70B-Instruct-Turbo-Free via Together.ai SDK 1.x
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
AI_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
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
Session 2 (2026-03-24): Created all 5 domain API files (education, healthcare, emergency, infrastructure, geo) inheriting BaseAPIClient. Fixed broken imports in map_explorer.py and src/ui/data_fetcher.py. Next: create src/ui/dashboard.py and src/ui/ai_assistant.py (app.py imports them but they don't exist yet).
