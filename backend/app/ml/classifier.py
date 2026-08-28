import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("firms_app.ml.classifier")

class SourceClassifier:
    """
    Geospatial ML & Heuristic Source Classifier for evaluating 
    thermal anomalies into candidate source categories.
    
    Classes:
    - INDUSTRIAL_CANDIDATE
    - NATURAL_FOREST_CANDIDATE
    - AGRICULTURAL_CANDIDATE
    - OTHER_UNKNOWN
    """

    def predict(self, feature_vector: Dict[str, Any]) -> Tuple[str, float, str]:
        """
        Predicts candidate source class, confidence score (0.0-1.0), and explainable rationale.
        
        Args:
            feature_vector: Dictionary containing:
                - distance_meters: float
                - facility_type: str ('refinery', 'power_plant', 'steel_works', 'chemical', 'industrial', 'none')
                - frp: float
                - bright_ti4: float
                - bright_ti5: float
                - daynight: str ('D', 'N')
                - scan: float
                
        Returns:
            Tuple[predicted_class: str, confidence_score: float, explanation: str]
        """
        dist = float(feature_vector.get("distance_meters", 99999.0))
        fac_type = str(feature_vector.get("facility_type", "none")).lower()
        frp = float(feature_vector.get("frp", 0.0))
        daynight = str(feature_vector.get("daynight", "D")).upper()
        ti4 = float(feature_vector.get("bright_ti4", 300.0)) if feature_vector.get("bright_ti4") else 300.0
        ti5 = float(feature_vector.get("bright_ti5", 290.0)) if feature_vector.get("bright_ti5") else 290.0

        ti_ratio = round(ti4 / ti5, 3) if ti5 > 0 else 1.0

        # High priority industrial facilities
        major_industrial = ["refinery", "power_plant", "steel_works", "chemical"]

        # Rule 1: Industrial Candidate
        if dist <= 500.0 or (dist <= 1500.0 and fac_type in major_industrial):
            conf = min(0.95, round(0.70 + 0.25 * (1.0 - min(dist, 1500.0) / 1500.0), 2))
            reason = (
                f"Thermal anomaly located within {int(dist)}m of {fac_type.upper()} infrastructure. "
                f"High radiative intensity (FRP {frp} MW, TI4/TI5 ratio {ti_ratio}). "
                f"Classified as Candidate Industrial Source."
            )
            return "INDUSTRIAL_CANDIDATE", conf, reason

        # Rule 2: Natural / Forest Fire Candidate
        if dist > 3000.0 and frp >= 20.0:
            conf = 0.85
            reason = (
                f"Isolated thermal point located {int(dist)}m away from industrial infrastructure "
                f"with high thermal output (FRP {frp} MW). "
                f"Classified as Candidate Natural / Forest Heat Source."
            )
            return "NATURAL_FOREST_CANDIDATE", conf, reason

        # Rule 3: Agricultural / Crop Fire Candidate
        if dist > 2000.0 and frp < 20.0 and daynight == "D":
            conf = 0.75
            reason = (
                f"Daytime orbit pass detection in non-industrial region ({int(dist)}m from facilities) "
                f"with moderate thermal output (FRP {frp} MW). "
                f"Classified as Candidate Agricultural / Open-Field Heat Source."
            )
            return "AGRICULTURAL_CANDIDATE", conf, reason

        # Rule 4: Other / Unknown
        conf = 0.50
        reason = (
            f"Thermal anomaly at {int(dist)}m from nearest facility with FRP {frp} MW. "
            f"Requires multi-pass temporal baselining for conclusive categorization."
        )
        return "OTHER_UNKNOWN", conf, reason
