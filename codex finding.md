# Codex Findings

## Repo Understanding
- The active app is a Streamlit 3-tab explorer (`Dashboard`, `Map Explorer`, `AI Assistant`) with shared session state.
- Data is pulled from Miami-Dade ArcGIS services and filtered by location/radius.
- The AI tab builds a location context summary from fetched marker data, then calls Together chat completions.

## What The Code Currently Does
- `app.py` routes between the 3 tabs and initializes shared state/styles.
- `src/ui/map_explorer.py` resolves ZIP/address, fetches category data, and renders a Folium map with overlays.
- `src/ui/dashboard.py` renders county-wide charts plus local proximity/coverage/risk analysis.
- `src/ui/ai_assistant.py` handles location-aware chat and sends prompts to the configured Together model.
- `src/zip_validator.py` loads Miami-Dade ZIP geometry and supports ZIP lookup, nearby ZIP search, area, and point-in-polygon checks.

## Documentation Alignment Check

### Matches
- README high-level product behavior largely matches the implementation (3 tabs, map layers, dashboard analytics, AI assistant).
- Shared location/filter state behavior is implemented across tabs.

### Mismatches
- Docs say UI modules do not call APIs, but `dashboard.py` and `charts.py` directly call API clients.
- Docs claim all external ArcGIS data is validated via Pydantic models, but runtime flow mostly uses raw feature dictionaries.
- Docs reference paths that do not match code (`src/utils/zip_validator.py`, `src/utils/response.py`).
- README says “no third-party APIs,” but address geocoding uses Nominatim (`geopy`).
- Quickstart mentions `.env`, but active runtime does not call `load_dotenv`; it reads `os.getenv`/`st.secrets`.
- CLAUDE rule says URL construction only in API base client, but `src/zip_validator.py` constructs a service URL directly.
- Dashboard school lookup can omit the center ZIP because `get_nearby_zips()` excludes the origin ZIP.
- Legacy/stale files are still present (`src/data_loader.py`, `src/data_extraction.py`, `test_app/*` legacy imports).

## Suggested Next Actions
1. Update README/CLAUDE to reflect current code reality.
2. Decide whether to enforce architecture rules strictly (especially Pydantic validation boundary).
3. Remove or archive stale modules/tests that no longer match active app architecture.
4. Patch dashboard ZIP selection logic so origin ZIP is included where expected.
