import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.thermal_observation import ThermalObservation
from app.models.industrial_facility import IndustrialFacility
from app.models.facility_association import ThermalFacilityAssociation
from app.services.impact_service import ImpactAssessmentService

client = TestClient(app)

@pytest.fixture
def db_session():
    """Provides an isolated in-memory SQLite database session for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    def override_get_db():
        try:
            yield session
        finally:
            pass

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    yield session
    session.close()
    if previous_override is not None:
        app.dependency_overrides[get_db] = previous_override
    else:
        app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def sample_data(db_session):
    """Seeds test thermal observations and industrial facilities into active session."""
    now = datetime.datetime.utcnow()

    # Seed Thermal Event #1 at (12.9753 N, 74.8354 E - Mangalore)
    obs1 = ThermalObservation(
        latitude=12.9753,
        longitude=74.8354,
        frp=95.0,
        satellite="NPP",
        observation_timestamp=now,
        source="VIIRS_SNPP_NRT",
        ingestion_batch_id="batch_test_101"
    )
    # Seed Isolated Thermal Event #2 at (0.0 N, 0.0 E)
    obs2 = ThermalObservation(
        latitude=0.0,
        longitude=0.0,
        frp=10.0,
        satellite="N20",
        observation_timestamp=now,
        source="VIIRS_NOAA20_NRT",
        ingestion_batch_id="batch_test_102"
    )

    db_session.add_all([obs1, obs2])
    db_session.commit()
    db_session.refresh(obs1)
    db_session.refresh(obs2)

    # Seed Facility A (Near obs1 ~1.1 km away: 12.9650 N, 74.8354 E)
    fac_a = IndustrialFacility(
        osm_id="way/1001",
        name="Mangalore Refinery & Petrochemicals",
        facility_type="refinery",
        latitude=12.9650,
        longitude=74.8354,
        ingestion_batch_id="batch_fac_1"
    )
    # Seed Facility B (Medium distance from obs1 ~3.5 km away: 12.9440 N, 74.8354 E)
    fac_b = IndustrialFacility(
        osm_id="way/1002",
        name="Mangalore Thermal Power Station",
        facility_type="power_plant",
        latitude=12.9440,
        longitude=74.8354,
        ingestion_batch_id="batch_fac_2"
    )
    # Seed Facility C (Far distance from obs1 ~15.0 km away: 12.8400 N, 74.8354 E)
    fac_c = IndustrialFacility(
        osm_id="way/1003",
        name="Distant Chemical Plant",
        facility_type="chemical",
        latitude=12.8400,
        longitude=74.8354,
        ingestion_batch_id="batch_fac_3"
    )

    db_session.add_all([fac_a, fac_b, fac_c])
    db_session.commit()
    db_session.refresh(fac_a)
    db_session.refresh(fac_b)
    db_session.refresh(fac_c)

    return {
        "obs1_id": obs1.id,
        "obs2_id": obs2.id,
        "fac_a_id": fac_a.id,
        "fac_b_id": fac_b.id,
        "fac_c_id": fac_c.id
    }

# 1. Known event with facility inside radius
def test_impact_known_event_inside_radius(db_session, sample_data):
    obs_id = sample_data["obs1_id"]
    response = client.get(f"/impact/{obs_id}?assessment_radius_km=5.0")
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == obs_id
    assert data["total_entities_found"] > 0
    assert len(data["entities"]) > 0

# 2. Multiple facilities inside radius -> ALL returned
def test_impact_multiple_facilities_returned(db_session, sample_data):
    obs_id = sample_data["obs1_id"]
    response = client.get(f"/impact/{obs_id}?assessment_radius_km=5.0")
    assert response.status_code == 200
    data = response.json()
    assert data["total_entities_found"] == 2
    facility_ids = [e["facility_id"] for e in data["entities"]]
    assert sample_data["fac_a_id"] in facility_ids
    assert sample_data["fac_b_id"] in facility_ids

# 3. Results ordered nearest -> farthest
def test_impact_results_ordered_by_distance_ascending(db_session, sample_data):
    obs_id = sample_data["obs1_id"]
    response = client.get(f"/impact/{obs_id}?assessment_radius_km=5.0")
    assert response.status_code == 200
    entities = response.json()["entities"]
    assert len(entities) == 2
    assert entities[0]["distance_meters"] <= entities[1]["distance_meters"]
    assert entities[0]["facility_id"] == sample_data["fac_a_id"]

# 4. Facility outside radius excluded
def test_impact_facility_outside_radius_excluded(db_session, sample_data):
    obs_id = sample_data["obs1_id"]
    response = client.get(f"/impact/{obs_id}?assessment_radius_km=2.0")
    assert response.status_code == 200
    data = response.json()
    assert data["total_entities_found"] == 1
    assert data["entities"][0]["facility_id"] == sample_data["fac_a_id"]

# 5. No facilities within radius -> HTTP 200 + empty entities
def test_impact_no_facilities_within_radius(db_session, sample_data):
    obs_id = sample_data["obs2_id"]
    response = client.get(f"/impact/{obs_id}?assessment_radius_km=5.0")
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == obs_id
    assert data["total_entities_found"] == 0
    assert data["entities"] == []

# 6. Unknown event -> HTTP 404
def test_impact_unknown_event_returns_404(db_session, sample_data):
    response = client.get("/impact/999999?assessment_radius_km=5.0")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

# 7. Radius below 0.1 -> HTTP 422
def test_impact_radius_below_minimum_returns_422(db_session, sample_data):
    obs_id = sample_data["obs1_id"]
    response = client.get(f"/impact/{obs_id}?assessment_radius_km=0.05")
    assert response.status_code == 422

# 8. Radius above 50 -> HTTP 422
def test_impact_radius_above_maximum_returns_422(db_session, sample_data):
    obs_id = sample_data["obs1_id"]
    response = client.get(f"/impact/{obs_id}?assessment_radius_km=55.0")
    assert response.status_code == 422

# 9. Default radius = 5 km
def test_impact_default_radius(db_session, sample_data):
    obs_id = sample_data["obs1_id"]
    response = client.get(f"/impact/{obs_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["assessment_radius_km"] == 5.0

# 10. Distance values are non-negative
def test_impact_distance_non_negative(db_session, sample_data):
    obs_id = sample_data["obs1_id"]
    response = client.get(f"/impact/{obs_id}?assessment_radius_km=5.0")
    assert response.status_code == 200
    for entity in response.json()["entities"]:
        assert entity["distance_meters"] >= 0.0
        assert entity["distance_km"] >= 0.0

# 11. Existing association data/behavior remains unchanged
def test_existing_association_behavior_unchanged(db_session, sample_data):
    response = client.get("/associations")
    assert response.status_code == 200

# 12. Scientific disclaimer is present
def test_impact_scientific_disclaimer_present(db_session, sample_data):
    obs_id = sample_data["obs1_id"]
    response = client.get(f"/impact/{obs_id}")
    assert response.status_code == 200
    disclaimer = response.json().get("scientific_disclaimer")
    assert disclaimer is not None
    assert "proximity indicates potential exposure context" in disclaimer.lower()
    assert "does not establish fire causality" in disclaimer.lower()


# =====================================================================
# Phase 2 — Sensitivity & Footprint Mapping Unit Tests
# =====================================================================

def test_phase2_sensitivity_refinery():
    assert ImpactAssessmentService.get_sensitivity_tier("refinery") == "CRITICAL"
    assert ImpactAssessmentService.get_sensitivity_tier("REFINERY") == "CRITICAL"

def test_phase2_sensitivity_chemical():
    assert ImpactAssessmentService.get_sensitivity_tier("chemical") == "CRITICAL"
    assert ImpactAssessmentService.get_sensitivity_tier("Chemical") == "CRITICAL"

def test_phase2_sensitivity_power_plant():
    assert ImpactAssessmentService.get_sensitivity_tier("power_plant") == "HIGH"
    assert ImpactAssessmentService.get_sensitivity_tier("POWER_PLANT") == "HIGH"

def test_phase2_sensitivity_steel_works():
    assert ImpactAssessmentService.get_sensitivity_tier("steel_works") == "MODERATE"

def test_phase2_sensitivity_industrial():
    assert ImpactAssessmentService.get_sensitivity_tier("industrial") == "MODERATE"

def test_phase2_sensitivity_unknown_type():
    assert ImpactAssessmentService.get_sensitivity_tier("unknown_sector_123") == "MODERATE"

def test_phase2_sensitivity_null_type():
    assert ImpactAssessmentService.get_sensitivity_tier(None) == "MODERATE"

def test_phase2_footprint_mega_facility():
    assert ImpactAssessmentService.get_footprint_scale(450000.0) == "MEGA_FACILITY"

def test_phase2_footprint_large_facility():
    assert ImpactAssessmentService.get_footprint_scale(200000.0) == "LARGE_FACILITY"
    assert ImpactAssessmentService.get_footprint_scale(150000.0) == "LARGE_FACILITY"
    assert ImpactAssessmentService.get_footprint_scale(300000.0) == "LARGE_FACILITY"

def test_phase2_footprint_standard_facility():
    assert ImpactAssessmentService.get_footprint_scale(50000.0) == "STANDARD_FACILITY"
    assert ImpactAssessmentService.get_footprint_scale(149999.0) == "STANDARD_FACILITY"

def test_phase2_footprint_null_area():
    assert ImpactAssessmentService.get_footprint_scale(None) == "STANDARD_FACILITY"

def test_phase2_footprint_invalid_area():
    assert ImpactAssessmentService.get_footprint_scale("invalid_area_str") == "STANDARD_FACILITY"
    assert ImpactAssessmentService.get_footprint_scale(float("nan")) == "STANDARD_FACILITY"

def test_phase2_impact_distance_calculations_unchanged(db_session, sample_data):
    obs_id = sample_data["obs1_id"]
    response = client.get(f"/impact/{obs_id}?assessment_radius_km=5.0")
    assert response.status_code == 200
    entities = response.json()["entities"]
    assert len(entities) == 2
    assert entities[0]["facility_id"] == sample_data["fac_a_id"]
    assert entities[0]["sensitivity_tier"] == "CRITICAL"
    assert entities[1]["facility_id"] == sample_data["fac_b_id"]
    assert entities[1]["sensitivity_tier"] == "HIGH"

def test_phase2_existing_associations_unchanged(db_session, sample_data):
    res = client.get("/associations")
    assert res.status_code == 200

def test_phase2_existing_risk_scoring_unchanged(db_session, sample_data):
    res = client.get("/risk")
    assert res.status_code == 200


# =====================================================================
# Phase 3A — Energy Infrastructure Expansion Unit Tests
# =====================================================================

def test_phase3a_entity_category_mapping():
    assert ImpactAssessmentService.get_entity_category("refinery") == "INDUSTRIAL"
    assert ImpactAssessmentService.get_entity_category("chemical") == "INDUSTRIAL"
    assert ImpactAssessmentService.get_entity_category("steel_works") == "INDUSTRIAL"
    assert ImpactAssessmentService.get_entity_category("industrial") == "INDUSTRIAL"
    assert ImpactAssessmentService.get_entity_category("power_plant") == "ENERGY"
    assert ImpactAssessmentService.get_entity_category("substation") == "ENERGY"
    assert ImpactAssessmentService.get_entity_category(None) == "INDUSTRIAL"

def test_phase3a_substation_sensitivity_tier():
    assert ImpactAssessmentService.get_sensitivity_tier("substation") == "HIGH"
    assert ImpactAssessmentService.get_sensitivity_tier("SUBSTATION") == "HIGH"

def test_phase3a_impact_response_has_category_and_geometry(db_session, sample_data):
    obs_id = sample_data["obs1_id"]
    response = client.get(f"/impact/{obs_id}?assessment_radius_km=5.0")
    assert response.status_code == 200
    entities = response.json()["entities"]
    assert len(entities) == 2
    
    # fac_a (refinery) -> INDUSTRIAL
    assert entities[0]["facility_id"] == sample_data["fac_a_id"]
    assert entities[0]["entity_category"] == "INDUSTRIAL"
    assert entities[0]["entity_type"] == "refinery"

    # fac_b (power_plant) -> ENERGY
    assert entities[1]["facility_id"] == sample_data["fac_b_id"]
    assert entities[1]["entity_category"] == "ENERGY"
    assert entities[1]["entity_type"] == "power_plant"
    assert entities[1]["sensitivity_tier"] == "HIGH"

def test_phase3a_substation_ingestion_and_impact(db_session, sample_data):
    # Seed a substation ~500m from obs1
    substation = IndustrialFacility(
        osm_id="way/9999",
        name="Mangalore Main Electrical Substation",
        facility_type="substation",
        latitude=12.9780,
        longitude=74.8354,
        area_sqm=5000.0,
        ingestion_batch_id="batch_substation_test"
    )
    db_session.add(substation)
    db_session.commit()
    db_session.refresh(substation)

    obs_id = sample_data["obs1_id"]
    response = client.get(f"/impact/{obs_id}?assessment_radius_km=5.0")
    assert response.status_code == 200
    entities = response.json()["entities"]
    
    sub_entity = next((e for e in entities if e["facility_id"] == substation.id), None)
    assert sub_entity is not None
    assert sub_entity["entity_category"] == "ENERGY"
    assert sub_entity["entity_type"] == "substation"
    assert sub_entity["sensitivity_tier"] == "HIGH"
    assert sub_entity["footprint_scale"] == "STANDARD_FACILITY"

def test_phase3a_no_duplicate_entities_returned(db_session, sample_data):
    obs_id = sample_data["obs1_id"]
    response = client.get(f"/impact/{obs_id}?assessment_radius_km=5.0")
    assert response.status_code == 200
    entities = response.json()["entities"]
    facility_ids = [e["facility_id"] for e in entities]
    assert len(facility_ids) == len(set(facility_ids))


# =====================================================================
# Phase 3B — Healthcare & Transportation Infrastructure Unit Tests
# =====================================================================

from app.models.healthcare_facility import HealthcareFacility
from app.models.transportation_entity import TransportationEntity

def test_phase3b_healthcare_hospital_ingestion_and_impact(db_session, sample_data):
    hosp = HealthcareFacility(
        osm_id="way/88881",
        name="Mangalore Central District Hospital",
        entity_type="hospital",
        latitude=12.9760,
        longitude=74.8360,
        area_sqm=12000.0,
        ingestion_batch_id="batch_hosp_test"
    )
    db_session.add(hosp)
    db_session.commit()

    obs_id = sample_data["obs1_id"]
    res = client.get(f"/impact/{obs_id}?assessment_radius_km=5.0")
    assert res.status_code == 200
    entities = res.json()["entities"]
    
    hosp_entity = next((e for e in entities if e["entity_category"] == "HEALTHCARE"), None)
    assert hosp_entity is not None
    assert hosp_entity["entity_type"] == "hospital"
    assert hosp_entity["name"] == "Mangalore Central District Hospital"
    assert hosp_entity["sensitivity_tier"] == "HIGH"

def test_phase3b_transportation_road_and_railway_ingestion_and_impact(db_session, sample_data):
    road = TransportationEntity(
        osm_id="way/77771",
        name="NH-66 Coastal Highway Corridor",
        entity_type="motorway",
        transport_category="road",
        latitude=12.9755,
        longitude=74.8355,
        ingestion_batch_id="batch_trans_test"
    )
    rail = TransportationEntity(
        osm_id="way/77772",
        name="Konkan Freight Rail Line",
        entity_type="railway",
        transport_category="railway",
        latitude=12.9770,
        longitude=74.8370,
        ingestion_batch_id="batch_trans_test"
    )
    db_session.add_all([road, rail])
    db_session.commit()

    obs_id = sample_data["obs1_id"]
    res = client.get(f"/impact/{obs_id}?assessment_radius_km=5.0")
    assert res.status_code == 200
    entities = res.json()["entities"]
    
    trans_entities = [e for e in entities if e["entity_category"] == "TRANSPORTATION"]
    assert len(trans_entities) >= 2
    assert any(e["entity_type"] == "motorway" and e["geometry_type"] == "LINESTRING" for e in trans_entities)
    assert any(e["entity_type"] == "railway" and e["geometry_type"] == "LINESTRING" for e in trans_entities)

def test_phase3b_duplicate_prevention(db_session):
    from app.services.osm_service import OSMDataService
    service = OSMDataService()
    
    mock_data = {
        "elements": [
            {"type": "node", "id": 101, "lat": 12.97, "lon": 74.83, "tags": {"amenity": "hospital", "name": "City Hospital"}},
            {"type": "way", "id": 201, "nodes": [101, 101], "tags": {"highway": "motorway", "name": "Expressway"}}
        ]
    }
    
    count1 = service.ingest_healthcare_facilities(db_session, raw_json_override=mock_data)
    count2 = service.ingest_healthcare_facilities(db_session, raw_json_override=mock_data)
    assert count1 == 1
    assert count2 == 0 # Duplicate skipped

def test_phase3b_distance_ascending_order(db_session, sample_data):
    obs_id = sample_data["obs1_id"]
    res = client.get(f"/impact/{obs_id}?assessment_radius_km=5.0")
    assert res.status_code == 200
    entities = res.json()["entities"]
    distances = [e["distance_meters"] for e in entities]
    assert distances == sorted(distances)

# ==============================================================================
# PHASE 3D UNIT TESTS — LIVE OSM LOCATION & ENRICHMENT
# ==============================================================================

def test_phase3d_display_label_hierarchy():
    from app.services.nominatim_enrichment_service import NominatimEnrichmentService
    
    # Test A: Named OSM entity
    label, src = NominatimEnrichmentService.build_display_label("Konkan Railway", None, "railway")
    assert label == "Konkan Railway"
    assert src == "OSM"
    
    # Test B: Road with ref
    label, src = NominatimEnrichmentService.build_display_label(None, "NH66", "trunk")
    assert label == "Trunk Road — NH66"
    assert src == "OSM_REF"
    
    # Test C: Unnamed railway
    label, src = NominatimEnrichmentService.build_display_label(None, None, "railway")
    assert label == "Unnamed Railway Corridor"
    assert src == "OSM_CLASSIFICATION"
    
    # Test C2: Unnamed primary road
    label, src = NominatimEnrichmentService.build_display_label(None, None, "primary")
    assert label == "Unnamed Primary Road"
    assert src == "OSM_CLASSIFICATION"

def test_phase3d_location_extraction():
    from app.services.nominatim_enrichment_service import NominatimEnrichmentService
    
    # Test D: City + State extraction
    addr = {"city": "Mangalore", "state": "Karnataka", "country": "India"}
    ctx = NominatimEnrichmentService.extract_location_context(addr)
    assert ctx == "Mangalore, Karnataka"
    
    # Test E: Missing location handling
    assert NominatimEnrichmentService.extract_location_context({}) is None

def test_phase3d_osm_id_conversion():
    from app.services.nominatim_enrichment_service import NominatimEnrichmentService
    
    # Test H: OSM ID conversion
    assert NominatimEnrichmentService.convert_osm_id_to_lookup_id("node/123") == "N123"
    assert NominatimEnrichmentService.convert_osm_id_to_lookup_id("way/45678") == "W45678"
    assert NominatimEnrichmentService.convert_osm_id_to_lookup_id("relation/999") == "R999"

def test_phase3d_enrichment_duplicate_and_failure(db_session):
    from app.services.nominatim_enrichment_service import NominatimEnrichmentService
    from app.models.transportation_entity import TransportationEntity
    
    # Create test entity in DB
    entity = TransportationEntity(
        osm_id="way/999888",
        name=None,
        entity_type="railway",
        transport_category="railway",
        latitude=12.97,
        longitude=74.83,
        location_context="Mangalore, Karnataka", # Already enriched
        display_label="Unnamed Railway Corridor",
        name_source="OSM_CLASSIFICATION",
        location_source="NOMINATIM_LOOKUP",
        ingestion_batch_id="test_batch"
    )
    db_session.add(entity)
    db_session.commit()
    
    service = NominatimEnrichmentService()
    # Test G: Second run with location_context already populated makes 0 external requests
    stats = service.enrich_transportation_entities(db_session)
    assert stats["locations_enriched"] == 0




