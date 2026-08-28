import logging
from typing import List, Dict
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Add backend/ directory path to allow absolute imports from agent package
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agent.agent import IndustrialThermalInvestigationAgent

logger = logging.getLogger("firms_app.api.agent_route")
router = APIRouter(tags=["AI Investigation Agent"])

# Initialize the agent once at startup
# It will validate credentials and fallback to mock if needed
agent_instance = IndustrialThermalInvestigationAgent()

class InvestigationRequest(BaseModel):
    event_id: str = Field(..., description="The ID of the thermal event, e.g. EVT-0042 or 42.")
    question: str = Field(..., description="The question about the thermal event.")

class EvidenceSourcesResponse(BaseModel):
    used: List[str] = Field(default_factory=list, description="List of project tools used as evidence.")
    unavailable: List[str] = Field(default_factory=list, description="List of unavailable evidence elements.")

class InvestigationResponse(BaseModel):
    event_id: str = Field(..., description="ID of the investigated event.")
    question: str = Field(..., description="Question asked to the agent.")
    answer: str = Field(..., description="Evidence-based reasoning synthesis in Markdown.")
    evidence_sources: EvidenceSourcesResponse = Field(..., description="Audit checklist for consumed sources.")
    latency_ms: float = Field(..., description="Processing time in milliseconds.")

@router.post(
    "/agent/investigate",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask AI Investigation Agent about a specific thermal event"
)
def investigate_event(payload: InvestigationRequest):
    """
    Invokes the Google ADK Industrial Thermal Investigation Agent to reason about a thermal anomaly,
    correlating database facts and baselines to answer natural-language inquiries.
    """
    try:
        res = agent_instance.investigate(event_id=payload.event_id, question=payload.question)
        return res
    except Exception as e:
        logger.error(f"Error executing agent investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process agent inquiry: {str(e)}"
        )
