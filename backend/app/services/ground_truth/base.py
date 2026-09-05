from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import datetime

class GroundTruthClass(str, Enum):
    INDUSTRIAL_FIRE = "INDUSTRIAL_FIRE"
    GAS_FLARE = "GAS_FLARE"
    AGRICULTURAL_BURNING = "AGRICULTURAL_BURNING"
    MINING_ACTIVITY = "MINING_ACTIVITY"
    WILDFIRE = "WILDFIRE"
    UNKNOWN = "UNKNOWN"

class LabelConfidenceLevel(str, Enum):
    HIGH = "HIGH"         # Level 1: Official government / authoritative incident confirmation
    MEDIUM = "MEDIUM"     # Level 2: Trusted scientific / satellite-derived dataset (VNF, MCD64A1)
    LOW = "LOW"           # Level 3: Indirect / weak signal candidate
    UNKNOWN = "UNKNOWN"   # Level 5: Insufficient evidence

@dataclass
class GroundTruthEvidence:
    """
    Normalized ground-truth evidence record retrieved from an external independent source.
    """
    source_name: str
    source_type: str
    source_record_id: str
    class_label: GroundTruthClass
    latitude: float
    longitude: float
    event_start: datetime.datetime
    event_end: Optional[datetime.datetime] = None
    confidence_level: LabelConfidenceLevel = LabelConfidenceLevel.MEDIUM
    provenance_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    retrieved_at: str = ""

    def __post_init__(self):
        if not self.retrieved_at:
            self.retrieved_at = datetime.datetime.utcnow().isoformat() + "Z"

class BaseGroundTruthProvider:
    """
    Abstract base class for external ground-truth dataset providers.
    """
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    def fetch_evidence_near(
        self,
        latitude: float,
        longitude: float,
        timestamp: datetime.datetime,
        spatial_radius_m: float = 500.0,
        temporal_window_hours: float = 24.0
    ) -> List[GroundTruthEvidence]:
        """Fetches independent evidence records near a given coordinate and timestamp."""
        raise NotImplementedError("Subclasses must implement fetch_evidence_near")
