import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shapely.geometry import Polygon
from app.database import Base
from app.models.industrial_facility import IndustrialFacility
from app.services.osm_service import OSMDataService, OSMIngestionError

SAMPLE_OVERPASS_JSON = {
    "elements": [
        {
            "type": "node",
            "id": 1001,
            "lat": 28.6140,
            "lon": 77.2090
        },
        {
            "type": "node",
            "id": 1002,
            "lat": 28.6150,
            "lon": 77.2090
        },
        {
            "type": "node",
            "id": 1003,
            "lat": 28.6150,
            "lon": 77.2100
        },
        {
            "type": "node",
            "id": 1004,
            "lat": 28.6140,
            "lon": 77.2100
        },
        {
            "type": "way",
            "id": 5001,
            "nodes": [1001, 1002, 1003, 1004, 1001],
            "tags": {
                "name": "Jamnagar Petroleum Refinery",
                "man_made": "petroleum_refinery",
                "operator": "Reliance Industries"
            }
        },
        {
            "type": "node",
            "id": 1005,
            "lat": 19.0760,
            "lon": 72.8777,
            "tags": {
                "name": "Trombay Thermal Power Plant",
                "power": "plant",
                "operator": "Tata Power"
            }
        }
    ]
}

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_overpass_query_builder():
    service = OSMDataService()
    query = service.build_overpass_query("68.0,6.0,97.0,37.0")
    assert "[out:json]" in query
    assert "6.0,68.0,37.0,97.0" in query  # Overpass (south, west, north, east) order

def test_categorize_facility_type():
    service = OSMDataService()
    assert service.categorize_facility_type({"man_made": "petroleum_refinery"}) == "refinery"
    assert service.categorize_facility_type({"power": "plant"}) == "power_plant"
    assert service.categorize_facility_type({"industrial": "steel"}) == "steel_works"
    assert service.categorize_facility_type({"industrial": "chemical"}) == "chemical"
    assert service.categorize_facility_type({"landuse": "industrial"}) == "industrial"

def test_parse_osm_elements():
    service = OSMDataService()
    parsed = service.parse_osm_elements(SAMPLE_OVERPASS_JSON, "test_batch_123")
    
    assert len(parsed) == 2
    
    # Verify polygon way (refinery)
    refinery = next(f for f in parsed if f["facility_type"] == "refinery")
    assert refinery["name"] == "Jamnagar Petroleum Refinery"
    assert refinery["operator"] == "Reliance Industries"
    assert refinery["area_sqm"] > 0.0
    
    # Verify node facility (power plant)
    power_plant = next(f for f in parsed if f["facility_type"] == "power_plant")
    assert power_plant["name"] == "Trombay Thermal Power Plant"

def test_ingest_osm_facilities_mock(db_session):
    service = OSMDataService()
    response = service.ingest_osm_facilities(
        db=db_session,
        bbox_str="68.0,6.0,97.0,37.0",
        raw_json_override=SAMPLE_OVERPASS_JSON
    )
    
    assert response.status == "success"
    assert response.facilities_ingested == 2
    assert os.path.exists(response.raw_file_path)
    
    db_facs = db_session.query(IndustrialFacility).all()
    assert len(db_facs) == 2
