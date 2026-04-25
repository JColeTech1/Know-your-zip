# Claude Findings — Know-Your-Zip Code Audit

**Audited by:** Claude Opus 4.6
**Date:** 2026-04-20

---

## What This App Does

Know-Your-Zip is a Miami-Dade County ZIP code explorer built with Streamlit. Users enter a ZIP code or street address and get:

1. **Map Tab** — Interactive Folium map showing nearby schools, hospitals, police/fire stations, bus stops, libraries, and parks, plus geographic overlays (flood zones, evacuation routes, bus routes)
2. **Dashboard Tab** — Plotly charts: school distribution histograms, fire station proximity donuts, park density treemaps, plus local proximity/coverage/risk analysis panels
3. **AI Chat Tab** — Together.ai-powered assistant (ServiceNow Apriel model) that answers neighborhood questions using live ArcGIS data as context

---

## Architecture Overview

- **`app.py`** — Thin entry point (~60 lines). Page config + tab routing only.
- **`src/bootstrap.py`** — Initializes 25+ session state keys for cross-tab persistence.
- **`src/constants.py`** — Single source of truth for all magic values (229 lines, fully typed).
- **`src/api/`** — 5 domain API files, all inheriting `BaseAPIClient` (retry, timeout, threading).
- **`src/models/`** — 5 Pydantic model files validating all ArcGIS responses before use.
- **`src/ui/`** — 7 files handling map rendering, dashboard charts, AI chat, filters, and data fetching.
- **`src/utils/`** — Distance math, geocoding, pickle caching, response normalization.

---

## What Matches CLAUDE.md (The Good)

| Rule | Status |
|------|--------|
| Entry point under 60 lines, routing only | Pass |
| All constants centralized in `src/constants.py` | Pass |
| API files inherit `BaseAPIClient` with retry/timeout | Pass |
| Pydantic models validate all external data | Pass |
| No API calls in UI rendering code | Pass |
| Comprehensive try/except + logging, no silent failures | Pass |
| Strict type annotations throughout production code | Pass |
| Functions kept to ~40 lines max | Pass |
| API key secured in `.env`/`st.secrets`, never hardcoded | Pass |
| ZIP validation before any API call | Pass |
| Session state deduplication for fetch calls | Pass |
| Dual-layer caching (Streamlit + disk pickle) | Pass |
| Clean separation: API coordination, UI rendering, pure data transforms | Pass |

---

## What Does NOT Match CLAUDE.md (The Problems)

### Dead / Orphaned Files

| File | Problem |
|------|---------|
| `src/data_extraction.py` (124 lines) | Not in canonical structure. Dead code — placeholder API endpoint (`example.com`), bare dicts, not imported anywhere. |
| `src/data_loader.py` (379 lines) | Legacy duplicate. Canonical version is `src/utils/data_loader.py` (78 lines). Both exist simultaneously. |
| `src/utils/response_normalizer.py` (121 lines) | Completely orphaned — nothing imports it. CLAUDE.md expects `response.py` with `ResponseNormalizer`. File uses outdated type hints (`Optional`, `Union`, bare `dict`). |

### Misplaced Files

| File | Expected Location | Current Location |
|------|-------------------|------------------|
| `src/zip_validator.py` | `src/utils/zip_validator.py` | `src/zip_validator.py` |
| `src/utils/response_normalizer.py` | `src/utils/response.py` | `src/utils/response_normalizer.py` |

### Rule Violations in Production Code

| File | Violation |
|------|-----------|
| `src/logger.py` | Hard-codes `10485760` and `5` instead of using `LOG_MAX_BYTES` / `LOG_BACKUP_COUNT` from `src/constants.py`. Missing type hints on function signature. |

### Missing Items

| Item | Status |
|------|--------|
| `legacy/` directory | Does not exist. CLAUDE.md defines it as FROZEN. |
| mypy clean pass | Never run. Session 10 was planned but never happened. |
| ruff clean pass | Never run. Same as above. |

---

## Legacy Test Files (`test_app/`)

All 6 files in `test_app/` are stale and violate every CLAUDE.md rule:

| File | Lines | Problems |
|------|-------|----------|
| `test_app.py` | 436 | Imports deleted root modules (`dashboard`, `map4`, `bot4`). |
| `test_bot4.py` | 437 | Uses deprecated `together.Complete.create()` API. Hardcodes wrong model (`Llama-3.3-70B`). Imports deleted legacy modules. Bare dicts. No Pydantic. |
| `test_charts.py` | 586 | Mixed legacy/canonical imports. Uses `geopy.distance.geodesic` directly instead of `src.utils.distance.miles_between`. |
| `test_dashboard.py` | 436 | Legacy imports. Hardcoded magic numbers. No filter state persistence. No fetch deduplication. |
| `test_map4.py` | 779 | ~500-line monolithic function. Legacy imports. Hardcoded color constants. Duplicated helpers that exist in `src/ui/map_builder.py`. |
| `test_minimal.py` | 48 | Empty placeholder. No functionality. |

Additionally, `src/test_zip_validator.py` (30 lines) has a broken import path and tests NYC/Beverly Hills ZIPs against a Miami-only database.

---

## Broken Test File

**`src/test_zip_validator.py`**
- Import error: `from zip_validator import ZIPValidator` — should be `from src.zip_validator import ZIPValidator`
- Tests ZIP codes 10001 (NYC) and 90210 (Beverly Hills) which don't exist in the Miami-Dade database
- Uses bare `print()` instead of pytest/unittest framework

---

## File Inventory

### Production Code (Active) — 27 files

| File | Lines | Quality |
|------|-------|---------|
| `app.py` | 60 | Excellent |
| `src/bootstrap.py` | 73 | Excellent |
| `src/constants.py` | 229 | Excellent |
| `src/logger.py` | 46 | Good (minor constants violation) |
| `src/styles.py` | 141 | Excellent |
| `src/zip_validator.py` | 260 | Excellent (misplaced) |
| `src/api/base.py` | 173 | Excellent |
| `src/api/education.py` | 93 | Excellent |
| `src/api/emergency.py` | 42 | Excellent |
| `src/api/geo.py` | 54 | Excellent |
| `src/api/healthcare.py` | 54 | Excellent |
| `src/api/infrastructure.py` | 63 | Excellent |
| `src/models/school.py` | 53 | Excellent |
| `src/models/healthcare.py` | 53 | Excellent |
| `src/models/emergency.py` | 46 | Excellent |
| `src/models/infrastructure.py` | 53 | Excellent |
| `src/models/location.py` | 86 | Excellent |
| `src/ui/map_explorer.py` | 213 | Excellent |
| `src/ui/map_builder.py` | 214 | Excellent |
| `src/ui/dashboard.py` | 409 | Excellent |
| `src/ui/ai_assistant.py` | 250 | Excellent |
| `src/ui/charts.py` | 357 | Excellent |
| `src/ui/filters.py` | 262 | Excellent |
| `src/ui/data_fetcher.py` | 203 | Excellent |
| `src/utils/data_loader.py` | 78 | Excellent |
| `src/utils/distance.py` | 40 | Excellent |
| `src/utils/geocoder.py` | 43 | Excellent |

### Dead / Orphaned Code — 3 files

| File | Lines | Action Needed |
|------|-------|---------------|
| `src/data_extraction.py` | 124 | Delete |
| `src/data_loader.py` | 379 | Delete (canonical version exists at `src/utils/data_loader.py`) |
| `src/utils/response_normalizer.py` | 121 | Delete or rewrite as `src/utils/response.py` |

### Legacy Tests — 7 files

| File | Lines | Action Needed |
|------|-------|---------------|
| `test_app/test_app.py` | 436 | Delete or rewrite |
| `test_app/test_bot4.py` | 437 | Delete or rewrite |
| `test_app/test_charts.py` | 586 | Delete or rewrite |
| `test_app/test_dashboard.py` | 436 | Delete or rewrite |
| `test_app/test_map4.py` | 779 | Delete or rewrite |
| `test_app/test_minimal.py` | 48 | Delete |
| `src/test_zip_validator.py` | 30 | Fix imports and test cases |

---

## Verdict

The **production code in `src/`** is genuinely well-built — clean architecture, strong typing, good error handling, proper separation of concerns. About **90% compliant** with CLAUDE.md.

The **dead weight** is the problem: 3 orphaned/duplicate files in `src/`, 7 stale legacy test files, a missing `legacy/` directory, and the planned mypy/ruff cleanup pass that never shipped. For a flagship interview project, these leftovers would raise questions about whether the codebase is actively maintained or just well-documented.

### Recommended Next Steps

1. Delete `src/data_extraction.py`, `src/data_loader.py`, `src/utils/response_normalizer.py`
2. Move `src/zip_validator.py` to `src/utils/zip_validator.py`
3. Fix `src/logger.py` to use constants
4. Delete or rewrite all `test_app/` files with proper pytest tests
5. Run mypy + ruff and fix all findings
6. Create `legacy/` directory (even if empty) to match CLAUDE.md structure
