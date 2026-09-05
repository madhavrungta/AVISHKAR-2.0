import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.landcover_service import LandCoverService, WORLDCOVER_CLASSES

client = TestClient(app)

def test_landcover_class_mapping_constants():
    assert WORLDCOVER_CLASSES[10] == "TREE_COVER"
    assert WORLDCOVER_CLASSES[20] == "SHRUBLAND"
    assert WORLDCOVER_CLASSES[30] == "GRASSLAND"
    assert WORLDCOVER_CLASSES[40] == "CROPLAND"
    assert WORLDCOVER_CLASSES[50] == "BUILT_UP"
    assert WORLDCOVER_CLASSES[60] == "BARE_SPARSE_VEGETATION"
    assert WORLDCOVER_CLASSES[70] == "SNOW_ICE"
    assert WORLDCOVER_CLASSES[80] == "PERMANENT_WATER"
    assert WORLDCOVER_CLASSES[90] == "HERBACEOUS_WETLAND"
    assert WORLDCOVER_CLASSES[95] == "MANGROVE"
    assert WORLDCOVER_CLASSES[100] == "MOSS_LICHEN"

def test_landcover_builtup_coordinate():
    service = LandCoverService()
    # Mangalore Industrial / Built-up area
    res = service.get_land_cover(12.975, 74.835)
    assert res["class_code"] == 50
    assert res["class_name"] == "BUILT_UP"
    assert res["source"] == "ESA_WORLDCOVER"
    assert res["resolution_m"] == 10

def test_landcover_cropland_coordinate():
    service = LandCoverService()
    # Rural agricultural area
    res = service.get_land_cover(13.10, 74.95)
    assert res["class_code"] == 40
    assert res["class_name"] == "CROPLAND"
    assert res["source"] == "ESA_WORLDCOVER"

def test_landcover_forest_coordinate():
    service = LandCoverService()
    # Western Ghats forest zone
    res = service.get_land_cover(13.25, 75.10)
    assert res["class_code"] == 10
    assert res["class_name"] == "TREE_COVER"
    assert res["source"] == "ESA_WORLDCOVER"

def test_landcover_water_coordinate():
    service = LandCoverService()
    # Off-shore Arabian Sea water
    res = service.get_land_cover(12.90, 74.70)
    assert res["class_code"] == 80
    assert res["class_name"] == "PERMANENT_WATER"
    assert res["source"] == "ESA_WORLDCOVER"

def test_landcover_invalid_latitude():
    service = LandCoverService()
    with pytest.raises(ValueError, match="Invalid latitude"):
        service.get_land_cover(95.0, 74.835)

def test_landcover_invalid_longitude():
    service = LandCoverService()
    with pytest.raises(ValueError, match="Invalid longitude"):
        service.get_land_cover(12.975, -190.0)

def test_landcover_mock_override_and_caching():
    service = LandCoverService()
    # Mock override test
    res = service.get_land_cover(12.0, 75.0, mock_override_code=95)
    assert res["class_code"] == 95
    assert res["class_name"] == "MANGROVE"

def test_landcover_api_endpoint():
    res = client.get("/landcover?latitude=12.975&longitude=74.835")
    assert res.status_code == 200
    data = res.json()
    assert data["class_code"] == 50
    assert data["class_name"] == "BUILT_UP"
    assert data["source"] == "ESA_WORLDCOVER"
    assert data["resolution_m"] == 10

def test_landcover_api_endpoint_validation_error():
    res = client.get("/landcover?latitude=100.0&longitude=74.835")
    assert res.status_code == 422 # Validation error
