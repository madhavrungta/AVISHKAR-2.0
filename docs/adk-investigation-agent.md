# Architecture: Industrial Thermal Investigation Agent (Google ADK)

This document describes the architectural layout, safety policies, and system integration for the **Industrial Thermal Investigation Agent** built with the **Google Agent Development Kit (ADK)** for the SIH 26162 (NTRO) command center project.

---

## 1. Why ADK is Used
Google ADK (Agent Development Kit) provides a code-first, modular framework for constructing orchestrators, LLM reasoning steps, and tool binds:
*   **Modular Declarations**: Allows defining agent nodes with strict system scopes, avoiding complex orchestration frameworks like LangChain or LangGraph.
*   **Built-in Tools Binding**: Direct support for binding standard Python functions as tools, translating parameters automatically into schemas for Gemini model invocation.
*   **Audit-Traceable Telemetry**: Emits granular lifecycle events representing model thoughts, tool calls, and final responses.

---

## 2. Agent Responsibilities
The ADK agent acts as a natural-language synthesis layer. It resides strictly *outside* the scientific and spatial pipelines:
*   **Responsibilities**:
    1.  Evidence retrieval using authorized project tools.
    2.  Translating baseline deviations into clear prioritisation rationales.
    3.  Expressing uncertainties (e.g., missing optical verify passes).
*   **Non-Responsibilities** (Deterministic boundaries):
    *   No spatial calculations (delegated to PostGIS).
    *   No baseline metric computations (delegated to `BaselineService`).
    *   No risk scoring (delegated to `RiskEvaluatorService`).

---

## 3. Tool Architecture
All tools reside inside [`agent/tools.py`](file:///c:/Users/ARJUN/Downloads/archive%20%288%29%20%281%29/SIH/backend/agent/tools.py) as read-only Python operations querying DB session layers:
1.  `get_event(event_id)`: Event anomaly status, composite risk priority, and model multiplier.
2.  `get_thermal_observations(event_id)`: Observation data (FRP, coordinates, confidence, daynight).
3.  `get_facility(facility_id)`: OpenStreetMap metadata of associated boundaries.
4.  `get_facility_baseline(facility_id)`: Historical thresholds (median, P95, P99). Returns `"baseline unavailable"` explicitly if not generated.
5.  `get_event_timeline(event_id)`: Persistence values (hours) and chronological observations.
6.  `get_context(event_id)`: Placeholder for weather or optical data. Returns `"contextual evidence unavailable"`.

---

## 4. FastAPI Integration
FastAPI exposes the agent via a dedicated POST endpoint:
*   **Endpoint**: `/agent/investigate`
*   **Payload**: `{ "event_id": "EVT-0042", "question": "Why is this event high priority?" }`
*   **Response**: Contains the markdown answer, latency, and a structured `evidence_sources` dictionary listing tools successfully triggered during the agent turn.

---

## 5. Security Policies
*   **No Sensitive Credentials Commits**: API Keys (`GEMINI_API_KEY`) are loaded dynamically from environment variables (`.env`).
*   **Credential-Free Fallback**: If the Gemini API key is missing, the agent operates in mock mode to allow local offline build verification.
*   **No Destructive Actions**: Agent tools do not support modifying or writing SQL records.

---

## 6. Evidence Policy & Hallucination Prevention
1.  **Strict Context Boundaries**: If the requested query asks about items not returned by tools (e.g., weather or explosions), the agent must reply that such evidence is unavailable.
2.  **Terminology Guardrails**:
    *   Use *"Thermal Anomaly"* instead of *"Confirmed Fire"*.
    *   Use *"Spatially Associated Facility"* instead of *"Source Facility"*.
3.  **Proximity Caution**: The agent must explicitly state that spatial proximity does not prove causality.
4.  **Priority Explanation**: Priority levels are justified using multiplier thresholds (FRP relative to historical P95).

---

## 7. Example Investigation Call
*   **Request**: `Why is EVT-0042 high priority?`
*   **Execution Flow**:
    1.  Call `get_event("EVT-0042")` to retrieve priority = HIGH.
    2.  Call `get_thermal_observations("EVT-0042")` to retrieve current FRP = 182 MW.
    3.  Call `get_facility(...)` to retrieve associated Chemical Plant.
    4.  Call `get_facility_baseline(...)` to retrieve historical baseline P95 = 74 MW.
    5.  Call `get_event_timeline("EVT-0042")` to calculate persistence = 4.2 hours.
*   **Synthesis**: Highlights that current FRP (182 MW) exceeds historical P95 (74 MW) over 4.2 hours.
*   **Audit**:
    *   Used: `[ "FIRMS observations", "Facility baseline", "OSM facility", "Event timeline" ]`
    *   Unavailable: `[ "Optical evidence", "Weather" ]`

---

## 8. Evaluation Strategy
We implement automated hallucination verification tests in the backend pytest suite:
1.  Verify that asking about explosions returns a negative evidence notice.
2.  Verify that asking for confirmation of fire returns a caution notice stating that fire confirmation is not established from thermal data alone.
3.  Verify that asking for weather returns a weather unavailable warning.

---

## 9. Limitations
*   **Temporal Latency**: Agent calls add network round-trip overhead.
*   **Context Token Usage**: Complex histories consume higher context tokens.
