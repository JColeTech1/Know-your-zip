# Know Your ZIP

> Miami-Dade County neighborhood intelligence — interactive map, analytics dashboard, and AI assistant powered entirely by live government data.

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/Framework-Streamlit-red)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

---

## What It Does

Enter any Miami-Dade County ZIP code or street address and instantly explore:

- **Map Explorer** — Interactive Folium map with toggleable layers: schools, hospitals, police/fire stations, bus stops, libraries, parks, flood zones, evacuation routes, and bus route overlays
- **Dashboard** — County-wide Plotly analytics: school distribution histograms, fire station proximity charts, park density treemaps, and a composite neighborhood coverage/risk score
- **AI Assistant** — Chat interface (ServiceNow-AI/Apriel-1.6-15b-Thinker via Together.ai) that answers neighborhood questions using live ArcGIS data fetched at query time

All three tabs share a single resolved location and filter state — search once on the Map, switch to AI or Dashboard without re-entering anything.

---

## Architecture

```
src/
├── api/                    ← one file per data domain; all inherit BaseAPIClient
│   ├── base.py             ← retry, timeout, parallel fetch (ThreadPoolExecutor)
│   ├── education.py        ← public, private, charter schools
│   ├── healthcare.py       ← hospitals, mental health centers, clinics
│   ├── emergency.py        ← police stations, fire stations
│   ├── infrastructure.py   ← bus stops, libraries, parks
│   └── geo.py              ← ZIP boundaries, flood zones, evacuation routes, bus routes
├── models/                 ← Pydantic v2 models for every external data type
│   ├── school.py
│   ├── healthcare.py
│   ├── emergency.py
│   ├── infrastructure.py
│   └── location.py         ← ZipLocation, Coordinates, BoundingBox
├── utils/
│   ├── zip_validator.py    ← ZIP lookup + boundary geometry (Shapely)
│   ├── geocoder.py         ← address → coordinates (Nominatim)
│   ├── distance.py         ← all geodesic math (miles_between, is_within_radius)
│   ├── response.py         ← ResponseNormalizer
│   └── data_loader.py      ← typed pickle cache helpers
├── ui/
│   ├── dashboard.py        ← Plotly charts tab — UI only, no API calls
│   ├── map_explorer.py     ← Folium map coordinator (≤200 lines)
│   ├── map_builder.py      ← marker and layer construction
│   ├── charts.py           ← reusable Plotly chart functions
│   ├── filters.py          ← filter widgets + FilterState dataclass
│   ├── data_fetcher.py     ← fetch + cache orchestration
│   └── ai_assistant.py     ← chat UI + Together.ai prompt construction
├── bootstrap.py            ← session state defaults + header rendering
├── constants.py            ← ALL magic values — nowhere else
└── logger.py               ← single shared logger
app.py                      ← entry point: page config + tab routing only (≤60 lines)
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| Framework | Streamlit |
| Language | Python 3.11+ with strict `mypy` typing |
| AI Model | ServiceNow-AI/Apriel-1.6-15b-Thinker via Together.ai SDK 1.x |
| Map | Folium + streamlit-folium |
| Charts | Plotly Express |
| Data | Miami-Dade County ArcGIS REST Services (~20 endpoints) |
| Validation | Pydantic v2 — all ArcGIS responses validated before use |
| Caching | `@st.cache_resource` + disk pickle (`src/utils/data_loader.py`) |
| Parallel fetch | `concurrent.futures.ThreadPoolExecutor` (4 workers) |
| Linting | ruff (style) + mypy (types) |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/yourusername/know-your-zip.git
cd know-your-zip

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Together.ai API key
echo "TOGETHER_API_KEY=your_key_here" > .env

# 4. Run
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501), enter a Miami-Dade ZIP code or address, and explore.

---

## Data Sources

All data is fetched live from Miami-Dade County's public ArcGIS REST Services — no third-party APIs, no scraping.

| Category | Datasets |
|----------|---------|
| Education | Public schools, private schools, charter schools |
| Healthcare | Hospitals, mental health centers, clinics |
| Emergency Services | Police stations, fire stations |
| Infrastructure | Bus stops, public libraries, parks |
| Geography | ZIP code boundaries, flood zones, evacuation routes, bus routes |

Base URL: `https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services`

---

## Design Principles

- **One responsibility per file** — UI never calls APIs; APIs never render
- **No magic values** — every constant lives in `src/constants.py`
- **All external data validated** — Pydantic models are the trust boundary for every ArcGIS response
- **All errors handled and logged** — no `except: pass`, no silent failures
- **New datasets require zero UI changes** — add a constants entry, a Pydantic model, an API class, a filter checkbox, and a map marker

---

## Contributing

See [CLAUDE.md](CLAUDE.md) for architecture rules, coding standards, and the session-by-session development log.
