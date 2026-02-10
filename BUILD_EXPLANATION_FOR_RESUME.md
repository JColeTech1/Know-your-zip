# Know Your ZIP — Detailed Build Explanation (for Resume + AI Prompting)

This document explains **what was built**, **how it works**, and **how to describe it professionally** for resumes, interviews, or AI tools (e.g., ChatGPT) that need enough context to write strong achievement bullets.

---

## 1) Project Summary (What You Built)

**Know Your ZIP** is a geospatial civic-intelligence web application built with **Python + Streamlit** that helps users explore neighborhood-level resources in **Miami-Dade County** by entering a ZIP code or address.

The app combines:
- public/community data APIs,
- location validation and normalization,
- distance-based filtering,
- visual analytics (charts + maps), and
- an AI assistant interface for location questions.

The result is a user-friendly local discovery platform for schools, healthcare, emergency services, transit, and parks.

---

## 2) Core Product Experience (User Flow)

A user opens the app and can navigate among three main surfaces:

1. **Dashboard**
   - High-level county overview charts.
   - Input for ZIP/address + adjustable radius.
   - Category toggles (schools, hospitals, police, fire, flood routes, bus routes, libraries, parks, etc.).
   - Results rendered as summaries/tables/insights.

2. **Map Explorer**
   - Interactive map interface centered around selected location.
   - Marker visualization for selected points of interest.

3. **AI Assistant**
   - Chat-style interface intended for natural-language local queries.

This architecture gives both technical and non-technical users two modes:
- **analytic mode** (dashboard + filters)
- **conversational mode** (AI assistant)

---

## 3) Technical Architecture (How It Works)

### Frontend Layer
- **Streamlit** drives UI, app routing, and widget state.
- Custom CSS is used for responsive design and dark-mode legibility.
- Session state controls active page, map defaults, markers, and chat history.

### Application Layer
- `app.py` orchestrates navigation and loads module-specific pages.
- `dashboard.py` coordinates multi-domain data retrieval and local filtering.
- Supporting feature modules provide API wrappers:
  - `education.py`
  - `healthcare.py`
  - `emergency_services.py`
  - `infrastructure.py`
  - `geo_data.py`

### Data/Utility Layer
- ZIP validation and canonicalization are handled by utilities in `src/`.
- Geospatial calculations use geocoding + distance computation to identify nearby resources within user-selected radius.
- Response normalization utilities help standardize inconsistent external API payloads.

### Visualization Layer
- Plotly-based charts (via `charts.py`) provide county-level insights.
- Map page (`map4.py`) provides geographic exploration.

### Quality Layer
- Test files under `test_app/` and `src/` cover core app behavior and zip-validation logic.

---

## 4) Engineering Problems This Build Solves

This project is stronger than a typical “simple dashboard” because it solves practical integration and UX challenges:

1. **Heterogeneous public data integration**
   - Different APIs expose different schemas and field quality.
   - The app normalizes those payloads into usable UI outputs.

2. **Location trust + user error handling**
   - Invalid ZIPs are rejected with user-friendly guidance and valid alternatives.

3. **Geospatial relevance**
   - Instead of dumping county data, it computes locality by radius from the user’s location.

4. **Cross-domain discoverability**
   - Education + healthcare + emergency + transit + recreation in one interface.

5. **Usable presentation layer**
   - Charts for summary, maps for spatial cognition, and AI chat for accessibility.

---

## 5) Resume-Ready “What I Built” Narrative

Use this when someone asks “what did you build?”

> I built a Python/Streamlit geospatial intelligence app called **Know Your ZIP** that helps Miami-Dade residents explore critical neighborhood resources by ZIP code or address. I integrated multiple civic/open-data sources (schools, healthcare, emergency services, transit, parks), added ZIP validation and radius-based proximity filtering, and delivered a multi-view UX with dashboards, map visualization, and an AI assistant interface for natural-language local queries.

---

## 6) Resume Bullets (Pick 2–4)

### General SWE Resume Bullets
- Built and deployed a **Streamlit-based geospatial web app** that aggregates multi-source civic data and delivers neighborhood insights by ZIP code and radius filtering.
- Engineered a **modular data-integration architecture** across education, healthcare, emergency, infrastructure, and geo-risk datasets, improving maintainability and feature velocity.
- Implemented **location validation and geospatial proximity logic** (geocoding + distance computation) to return context-relevant points of interest instead of static county-level lists.
- Designed a **multi-modal analytics experience** combining KPI charts, interactive maps, and conversational AI to improve data accessibility for non-technical users.

### Data / Analytics Focused Bullets
- Developed a local intelligence dashboard using **Plotly + Streamlit** to visualize county trends and provide drill-down by location and category.
- Standardized heterogeneous API responses into coherent output schemas for downstream visualization and user-facing analytics.

### Product / UX Focused Bullets
- Built a responsive, dark-mode-friendly UI with navigation state management and category controls to reduce friction in location-based exploration workflows.

---

## 7) ATS Keyword Bank (Include Naturally in Resume)

Use relevant terms from this list in your project description:

- Python
- Streamlit
- Geospatial Analytics
- Location Intelligence
- API Integration
- Data Normalization
- Data Visualization
- Plotly
- Geocoding
- Distance Calculations
- Open Data / Civic Tech
- Interactive Dashboard
- Mapping / GIS-style Experience
- Modular Architecture
- Test-Driven Validation (if emphasizing tests)

---

## 8) Interview Talking Points (STAR-Friendly)

### Situation
Residents need a single place to evaluate nearby public resources quickly.

### Task
Create an easy-to-use app that turns scattered open data into actionable neighborhood insights.

### Action
Built a modular Python/Streamlit platform with ZIP validation, geospatial filtering, category-specific API integrations, and combined chart/map/chat experiences.

### Result
Delivered a unified local discovery tool that improves visibility into schools, healthcare, emergency services, transit, and parks, while demonstrating full-stack data product skills (ingestion → transformation → UX).

---

## 9) “ChatGPT Prompt” You Can Reuse

If you want another AI to rewrite this for a specific role, paste this:

> I built a project called Know Your ZIP using Python and Streamlit. It aggregates civic/open datasets for Miami-Dade (schools, healthcare, emergency services, transit, parks), validates ZIPs, computes nearby resources by radius, and shows insights via dashboards, maps, and an AI assistant interface. Please rewrite this into (1) 3 resume bullets for a [Backend/Data/Product] role, (2) a 2-minute interview pitch, and (3) an ATS-optimized project description with quantified impact placeholders.

---

## 10) Quantification Ideas (to strengthen your resume)

If you can measure these, add numbers:

- Number of datasets/APIs integrated.
- Number of categories surfaced.
- Typical response time improvement after caching.
- Number of ZIP codes validated/covered.
- Any user testing feedback (task completion time, usability rating).

Even estimated ranges are better than no metrics (as long as clearly framed and honest).
