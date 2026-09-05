import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.thermal_observation import ThermalObservation
from app.services.firms_service import FIRMSDataService, FIRMSIngestionError

# Mock FIRMS CSV Payload matching official VIIRS output format
SAMPLE_VALID_FIRMS_CSV = """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight
28.6139,77.2090,325.4,0.42,0.38,2026-08-26,0645,N,VIIRS,n,2.0NRT,295.1,12.5,D
19.0760,72.8777,310.2,0.50,0.40,2026-08-26,0645,N,VIIRS,n,2.0NRT,290.0,8.2,D
"""

SAMPLE_INVALID_COORDS_CSV = """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight
120.5000,77.2090,325.4,0.42,0.38,2026-08-26,0645,N,VIIRS,n,2.0NRT,295.1,12.5,D
28.6139,-250.0000,310.2,0.50,0.40,2026-08-26,0645,N,VIIRS,n,2.0NRT,290.0,8.2,D
"""

SAMPLE_DUPLICATE_CSV = """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight
28.6139,77.2090,325.4,0.42,0.38,2026-08-26,0645,N,VIIRS,n,2.0NRT,295.1,12.5,D
28.6139,77.2090,325.4,0.42,0.38,2026-08-26,0645,N,VIIRS,n,2.0NRT,295.1,12.5,D
"""

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_missing_api_key_raises_clear_error():
    service = FIRMSDataService(map_key="")
    with pytest.raises(FIRMSIngestionError) as exc_info:
        service.validate_api_key()
    assert "FIRMS_MAP_KEY is not configured" in str(exc_info.value)

def test_validate_and_clean_valid_data():
    service = FIRMSDataService(map_key="test_key_123456789")
    records, report = service.validate_and_clean_data(SAMPLE_VALID_FIRMS_CSV)
    
    assert len(records) == 2
    assert report.total_records == 2
    assert report.valid_records == 2
    assert report.invalid_records == 0
    assert records[0]["latitude"] == 28.6139
    assert records[0]["longitude"] == 77.2090
    assert records[0]["frp"] == 12.5

def test_invalid_coordinates_rejection():
    service = FIRMSDataService(map_key="test_key_123456789")
    records, report = service.validate_and_clean_data(SAMPLE_INVALID_COORDS_CSV)
    
    assert len(records) == 0
    assert report.total_records == 2
    assert report.invalid_records == 2
    assert len(report.rejected_records) == 2

def test_duplicate_filtering():
    service = FIRMSDataService(map_key="test_key_123456789")
    records, report = service.validate_and_clean_data(SAMPLE_DUPLICATE_CSV)
    
    assert len(records) == 1
    assert report.duplicates == 1

def test_ingest_firms_data_mock(db_session):
    service = FIRMSDataService(map_key="test_key_123456789")
    response = service.ingest_firms_data(
        db=db_session,
        source="VIIRS_SNPP_NRT",
        area="68,6,98,36",
        raw_csv_override=SAMPLE_VALID_FIRMS_CSV
    )
    
    assert response.status == "success"
    assert response.records_ingested == 2
    assert os.path.exists(response.raw_file_path)
    
    # Query database to confirm insertion
    db_records = db_session.query(ThermalObservation).all()
    assert len(db_records) == 2
    assert db_records[0].source == "VIIRS_SNPP_NRT"

def test_firms_ingestion_fallback_sequence(db_session, monkeypatch):
    service = FIRMSDataService(map_key="test_key_123456789")
    
    empty_csv = "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
    
    # Case 1: days=1 returns 0 -> days=3 returns valid records
    calls = []
    def mock_fetch(source, area, days, date=None):
        calls.append(days)
        if days == 1:
            return empty_csv, "batch_1"
        elif days == 3:
            return SAMPLE_VALID_FIRMS_CSV, "batch_3"
        return empty_csv, "batch_5"

    monkeypatch.setattr(service, "fetch_firms_csv", mock_fetch)

    res = service.ingest_firms_data(db=db_session, source="VIIRS_SNPP_NRT", area="68,6,98,36", days=1)
    assert calls == [1, 3]
    assert res.status == "success"
    assert res.records_ingested == 2
    assert res.requested_days == 1
    assert res.effective_days == 3
    assert res.fallback_used is True
    assert "last 3 days" in res.message

    # Case 2: days=1 and days=3 return 0 -> days=5 returns valid records
    calls.clear()
    def mock_fetch_5(source, area, days, date=None):
        calls.append(days)
        if days in [1, 3]:
            return empty_csv, f"batch_{days}"
        return SAMPLE_VALID_FIRMS_CSV, "batch_5"

    monkeypatch.setattr(service, "fetch_firms_csv", mock_fetch_5)

    res5 = service.ingest_firms_data(db=db_session, source="VIIRS_SNPP_NRT", area="68,6,98,36", days=1)
    assert calls == [1, 3, 5]
    assert res5.effective_days == 5
    assert res5.fallback_used is True
    assert "last 5 days" in res5.message

    # Case 3: All 3 return 0 records
    calls.clear()
    def mock_fetch_zero(source, area, days, date=None):
        calls.append(days)
        return empty_csv, f"batch_{days}"

    monkeypatch.setattr(service, "fetch_firms_csv", mock_fetch_zero)

    res_zero = service.ingest_firms_data(db=db_session, source="VIIRS_SNPP_NRT", area="68,6,98,36", days=1)
    assert calls == [1, 3, 5]
    assert res_zero.status == "success"
    assert res_zero.records_ingested == 0
    assert res_zero.requested_days == 1
    assert res_zero.effective_days is None
    assert res_zero.fallback_used is True
    assert "No thermal anomalies were detected" in res_zero.message

