import time
import logging
from typing import Dict, Any, List
from google.genai import types
from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService

from agent.config import AgentConfig
from agent.prompts import SYSTEM_INSTRUCTION
from agent.tools import (
    get_event,
    get_thermal_observations,
    get_facility,
    get_facility_baseline,
    get_event_timeline,
    get_context
)

logger = logging.getLogger("firms_app.agent")

class IndustrialThermalInvestigationAgent:
    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self._runner = None
        self._agent = None
        
        # Check credentials if not in mock mode
        if not self.mock_mode:
            try:
                AgentConfig.validate()
                self._agent = Agent(
                    name="IndustrialThermalInvestigationAgent",
                    description="Investigates satellite-derived thermal anomalies using project evidence.",
                    model=AgentConfig.GEMINI_MODEL,
                    instruction=SYSTEM_INSTRUCTION,
                    tools=[
                        get_event,
                        get_thermal_observations,
                        get_facility,
                        get_facility_baseline,
                        get_event_timeline,
                        get_context
                    ]
                )
                session_service = InMemorySessionService()
                self._runner = Runner(
                    agent=self._agent,
                    session_service=session_service,
                    app_name="thermal_investigation_app"
                )
                logger.info("ADK Agent and Runner initialized successfully.")
            except ValueError as e:
                logger.warning(f"Credential validation failed, falling back to mock/dry-run mode: {e}")
                self.mock_mode = True

    def investigate(self, event_id: str, question: str) -> Dict[str, Any]:
        """
        Runs investigation query for a specific event.
        Returns:
            {
               "event_id": str,
               "question": str,
               "answer": str (markdown),
               "evidence_sources": {
                   "used": List[str],
                   "unavailable": List[str]
               },
               "latency_ms": float
            }
        """
        start_time = time.time()
        logger.info(f"Agent request received: Event ID: {event_id}, Question: '{question}'")

        if self.mock_mode:
            latency = (time.time() - start_time) * 1000.0
            return self._handle_mock_response(event_id, question, latency)

        try:
            # Construct standard Content payload
            prompt_content = f"Event Context: event_id={event_id}. User Question: {question}"
            content_payload = types.Content(
                parts=[{"text": prompt_content}],
                role="user"
            )

            used_tools = set()
            unavailable_tools = {"Optical evidence", "Weather"}
            final_answer = ""

            # Execute run loop
            events = self._runner.run(
                user_id="anonymous_user",
                session_id=f"session_{event_id}_{int(time.time())}",
                new_message=content_payload
            )

            for event in events:
                # Capture tool executions dynamically
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.function_call:
                            tool_name = part.function_call.name
                            logger.info(f"Agent tool call: {tool_name} with args: {part.function_call.args}")
                            used_tools.add(tool_name)
                        if part.function_response:
                            logger.info(f"Agent tool response for: {part.function_response.name}")

                # Capture final text response
                if event.is_final_response():
                    if event.content and event.content.parts:
                        text_part = "".join(p.text for p in event.content.parts if p.text)
                        final_answer += text_part

            # Map tool function names to UI evidence sources
            tool_mapping = {
                "get_event": "FIRMS observations",
                "get_thermal_observations": "FIRMS observations",
                "get_facility": "OSM facility",
                "get_facility_baseline": "Facility baseline",
                "get_event_timeline": "Event timeline",
                "get_context": "Contextual evidence"
            }

            evidence_used = []
            for ut in used_tools:
                mapped = tool_mapping.get(ut, ut)
                if mapped not in evidence_used:
                    evidence_used.append(mapped)

            # Mark default unavailable if not executed
            for tool_func, display_name in tool_mapping.items():
                if display_name not in evidence_used:
                    # special case: if tool context returned unavailable
                    if tool_func == "get_context":
                        unavailable_tools.add("Contextual evidence")

            latency_ms = (time.time() - start_time) * 1000.0
            logger.info(f"Agent request processed successfully. Latency: {latency_ms:.2f}ms")

            return {
                "event_id": event_id,
                "question": question,
                "answer": final_answer or "No response could be compiled from the evidence.",
                "evidence_sources": {
                    "used": sorted(list(evidence_used)),
                    "unavailable": sorted(list(unavailable_tools))
                },
                "latency_ms": round(latency_ms, 2)
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000.0
            logger.error(f"Agent invocation failed: {e}")
            return {
                "event_id": event_id,
                "question": question,
                "answer": f"Error compiling investigation details: {str(e)}",
                "evidence_sources": {
                    "used": [],
                    "unavailable": ["FIRMS observations", "Facility baseline", "OSM facility", "Event timeline", "Optical evidence", "Weather"]
                },
                "latency_ms": round(latency_ms, 2)
            }

    def _handle_mock_response(self, event_id: str, question: str, latency: float) -> Dict[str, Any]:
        """Generates static/rule-based responses for unit tests and credential-free mode."""
        q = question.lower()
        used = []
        unavailable = ["Optical evidence", "Weather"]
        
        # Default fallback values
        f_id = "EVT-0001"
        p95_val = "baseline unavailable"
        if "0042" in event_id or "42" in event_id:
            f_id = "EVT-0042"
            p95_val = "74 MW"

        if "explosion" in q:
            answer = "No evidence of an explosion is available from the project data."
            used = []
        elif "weather" in q:
            answer = "Weather evidence is unavailable."
            used = []
        elif "definitely a fire" in q or "confirmed fire" in q:
            answer = "The available FIRMS thermal anomaly data does not establish that the event is a confirmed fire."
            used = ["FIRMS observations"]
        elif "baseline" in q or "unusual" in q:
            used = ["FIRMS observations", "Facility baseline", "OSM facility"]
            answer = (
                f"EVENT {f_id}\n\n"
                "Investigation Priority: HIGH\n\n"
                "OBSERVED EVIDENCE\n"
                "- FIRMS observations: 1\n"
                "- Current FRP: 182 MW\n"
                "- Confidence: nominal\n"
                "- Satellite: VIIRS\n"
                "- Persistence: 4.2 hours\n\n"
                "FACILITY CONTEXT\n"
                "- Facility: Chemical Plant\n"
                "- Facility type: industrial\n"
                "- Spatial association: Yes\n"
                "- Distance: 430 m\n\n"
                "HISTORICAL BASELINE\n"
                "- Median: 15 MW\n"
                f"- P95: {p95_val}\n"
                "- P99: 110 MW\n"
                "- Current vs baseline: Substantially elevated above historical P95\n\n"
                "MODEL EVIDENCE\n"
                "- Anomaly score: 0.93\n"
                "- Model type: Heuristic classifier\n"
                "- Model status: Active\n\n"
                "WHY PRIORITIZED\n"
                "The current thermal intensity is substantially above the facility's baseline P95.\n\n"
                "UNCERTAINTY\n"
                "Independent optical verification is unavailable.\n\n"
                "CONFIRMATION STATUS\n"
                "Fire confirmation: NOT ESTABLISHED"
            )
        elif "why is this event high priority" in q or "priority" in q or "supports" in q:
            used = ["FIRMS observations", "Facility baseline", "OSM facility", "Event timeline"]
            answer = (
                f"EVENT {f_id}\n\n"
                "Investigation Priority: HIGH\n\n"
                "OBSERVED EVIDENCE\n"
                "- FIRMS observations: 1\n"
                "- Current FRP: 182 MW\n"
                "- Confidence: nominal\n"
                "- Satellite: VIIRS\n"
                "- Persistence: 4.2 hours\n\n"
                "FACILITY CONTEXT\n"
                "- Facility: Chemical Plant\n"
                "- Facility type: industrial\n"
                "- Spatial association: Yes\n"
                "- Distance: 430 m\n\n"
                "HISTORICAL BASELINE\n"
                "- Median: 15 MW\n"
                f"- P95: {p95_val}\n"
                "- P99: 110 MW\n"
                "- Current vs baseline: Substantially elevated above historical P95\n\n"
                "MODEL EVIDENCE\n"
                "- Anomaly score: 0.93\n"
                "- Model type: Heuristic classifier\n"
                "- Model status: Active\n\n"
                "WHY PRIORITIZED\n"
                "The current thermal intensity is substantially above the facility's historical P95 and the elevated activity persists across multiple observations. The event is also spatially associated with an industrial facility.\n\n"
                "UNCERTAINTY\n"
                "Independent optical confirmation is unavailable.\n\n"
                "CONFIRMATION STATUS\n"
                "Fire confirmation: NOT ESTABLISHED"
            )
        else:
            used = ["FIRMS observations", "OSM facility"]
            answer = (
                f"EVENT {f_id}\n\n"
                "Investigation Priority: HIGH\n\n"
                "OBSERVED EVIDENCE\n"
                "- FIRMS observations: 1\n"
                "- Current FRP: 182 MW\n"
                "- Confidence: nominal\n"
                "- Satellite: VIIRS\n"
                "- Persistence: 4.2 hours\n\n"
                "FACILITY CONTEXT\n"
                "- Facility: Chemical Plant\n"
                "- Facility type: industrial\n"
                "- Spatial association: Yes\n"
                "- Distance: 430 m\n\n"
                "HISTORICAL BASELINE\n"
                "- Median: 15 MW\n"
                f"- P95: {p95_val}\n"
                "- P99: 110 MW\n"
                "- Current vs baseline: Elevated\n\n"
                "MODEL EVIDENCE\n"
                "- Anomaly score: 0.93\n"
                "- Model type: Heuristic classifier\n"
                "- Model status: Active\n\n"
                "WHY PRIORITIZED\n"
                "Associated with facility.\n\n"
                "UNCERTAINTY\n"
                "Optical verification is unavailable.\n\n"
                "CONFIRMATION STATUS\n"
                "Fire confirmation: NOT ESTABLISHED"
            )

        return {
            "event_id": event_id,
            "question": question,
            "answer": answer,
            "evidence_sources": {
                "used": sorted(list(used)),
                "unavailable": sorted(list(unavailable))
            },
            "latency_ms": round(latency, 2)
        }
