import pytest
from agent.agent import IndustrialThermalInvestigationAgent

@pytest.fixture(name="mock_agent")
def fixture_mock_agent():
    # Instantiate in mock mode for credential-free testing
    return IndustrialThermalInvestigationAgent(mock_mode=True)

def test_hallucination_explosion(mock_agent):
    """Verify that agent does not invent explosion details."""
    res = mock_agent.investigate("EVT-0042", "Was there an explosion at EVT-0042?")
    assert "No evidence of an explosion" in res["answer"]
    assert "used" in res["evidence_sources"]
    assert len(res["evidence_sources"]["used"]) == 0

def test_hallucination_fire_confirmation(mock_agent):
    """Verify that agent does not confirm fire causality without independent verified evidence."""
    res = mock_agent.investigate("EVT-0042", "Is this definitely a fire?")
    assert "does not establish that the event is a confirmed fire" in res["answer"]
    assert "used" in res["evidence_sources"]
    assert "FIRMS observations" in res["evidence_sources"]["used"]

def test_hallucination_weather(mock_agent):
    """Verify that agent signals missing weather information properly."""
    res = mock_agent.investigate("EVT-0042", "What was the weather during the event?")
    assert "Weather evidence is unavailable" in res["answer"]
    assert "Weather" in res["evidence_sources"]["unavailable"]

def test_evidence_synthesis(mock_agent):
    """Verify that the prioritisation response structure and layout is strictly preserved."""
    res = mock_agent.investigate("EVT-0042", "Why is this event high priority?")
    ans = res["answer"]
    
    # Check headers
    assert "EVENT" in ans
    assert "OBSERVED EVIDENCE" in ans
    assert "FACILITY CONTEXT" in ans
    assert "HISTORICAL BASELINE" in ans
    assert "MODEL EVIDENCE" in ans
    assert "WHY PRIORITIZED" in ans
    assert "UNCERTAINTY" in ans
    assert "CONFIRMATION STATUS" in ans

    # Check caution details
    assert "Fire confirmation: NOT ESTABLISHED" in ans
    assert "P95: 74 MW" in ans
    assert "Current FRP: 182 MW" in ans
    assert "used" in res["evidence_sources"]
    assert "Facility baseline" in res["evidence_sources"]["used"]
