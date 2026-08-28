# Google ADK Industrial Thermal Investigation Agent

This package implements the **Industrial Thermal Investigation Agent** using **Google ADK** (Agent Development Kit) on top of the existing SIH 26162 FastAPI back-end project.

---

## Agent Responsibilities
The agent acts as an intelligent reasoning and natural-language synthesis layer on top of the deterministic databases and models. It is **read-only** and does not modify database records.

Its primary responsibilities are:
1.  **Evidence Synthesis**: Combining satellite anomalies, OSM facility details, and historical statistics to explain why an event was prioritized.
2.  **Uncertainty Communication**: Identifying missing evidence (e.g., optical validation, weather) and communicating that proximity does not imply causality, nor is thermal detection alone proof of a confirmed fire.
3.  **Audit Trail Generation**: Outputting a list of evidence sources used vs. unavailable during reasoning.

---

## Configuration
Add the following to your `backend/.env` file:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

If the credentials are not provided, the agent falls back to a deterministic dry-run/mock provider to guarantee that local tests run cleanly without requiring credentials.

---

## Read-Only Tools
Exposed inside `agent/tools.py`:
*   `get_event(event_id)`: Gets event metadata, priority state, and composite anomaly score.
*   `get_thermal_observations(event_id)`: Fetches raw coordinates, satellite, and FRP metrics.
*   `get_facility(facility_id)`: Fetches associated facility metadata.
*   `get_facility_baseline(facility_id)`: Retrieves calculated P95, median, and MAD thresholds.
*   `get_event_timeline(event_id)`: Computes persistence (hours) and sequence lists.
*   `get_context(event_id)`: Default fallback context tool (returns "contextual evidence unavailable").

---

## Running Verification Tests
To run tool unit tests and agent hallucination prevention tests:
```bash
pytest agent/tests/ -v
```
