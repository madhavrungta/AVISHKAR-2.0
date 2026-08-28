import os
import uuid
import logging
import datetime
from io import StringIO
from typing import List, Dict, Any, Tuple, Optional
import httpx
import pandas as pd
from sqlalchemy.orm import Session

try:
    from geoalchemy2.shape import from_shape
    HAS_GEOALCHEMY_SHAPE = True
except ImportError:
    from_shape = None
    HAS_GEOALCHEMY_SHAPE = False

from app.config import settings
from app.models.thermal_observation import ThermalObservation, is_sqlite, HAS_GEOALCHEMY2
from app.models.ingestion_batch import IngestionBatch
from app.schemas.thermal_observation import ValidationReport, FIRMSIngestionResponse
from app.geospatial.utils import create_point_geometry, convert_records_to_geodataframe


logger = logging.getLogger("firms_app.firms_service")

class FIRMSIngestionError(Exception):
    """Custom exception raised when FIRMS API ingestion fails."""
    pass

class FIRMSDataService:
    """
    Service layer for fetching, validating, persisting, and normalizing
    NASA FIRMS active-fire / thermal-anomaly data.
    """

    def __init__(self, map_key: Optional[str] = None):
        self.map_key = settings.FIRMS_MAP_KEY if map_key is None else map_key
        self.raw_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))
        os.makedirs(self.raw_data_dir, exist_ok=True)

    def validate_api_key(self) -> None:
        """Verifies that a valid FIRMS_MAP_KEY is configured before making external API calls."""
        key = (self.map_key or "").strip()
        if not key or key in ["your_key_here", "YOUR_MAP_KEY"]:
            msg = "FIRMS_MAP_KEY is not configured. Add it to backend/.env."
            logger.error(f"API Key Validation Error: {msg}")
            raise FIRMSIngestionError(msg)

    def build_api_url(
        self, 
        source: str, 
        area: str, 
        days: int, 
        date: Optional[str] = None
    ) -> str:
        """Constructs official NASA FIRMS API endpoint URL."""
        base_url = settings.FIRMS_BASE_URL.rstrip("/")
        # URL structure: https://firms.modaps.eosdis.nasa.gov/api/area/csv/[MAP_KEY]/[SOURCE]/[AREA]/[DAYS]/[DATE]
        url = f"{base_url}/{self.map_key}/{source}/{area}/{days}"
        if date:
            url += f"/{date}"
        return url

    def fetch_firms_csv(
        self, 
        source: str = "VIIRS_SNPP_NRT", 
        area: str = "68.0,6.0,97.0,37.0", 
        days: int = 1, 
        date: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Fetches CSV dataset from official NASA FIRMS API.
        
        Returns:
            Tuple[csv_content: str, batch_id: str]
        """
        self.validate_api_key()
        
        url = self.build_api_url(source=source, area=area, days=days, date=date)
        
        # Log request without exposing MAP_KEY
        safe_url = url.replace(self.map_key, "***MAP_KEY***")
        logger.info(f"Initiating NASA FIRMS API query: {safe_url}")

        batch_id = f"batch_{source}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        retries = 3
        timeout = httpx.Timeout(30.0, connect=10.0)

        for attempt in range(1, retries + 1):
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.get(url)
                    
                if response.status_code == 200:
                    csv_text = response.text
                    logger.info(f"NASA FIRMS API fetch successful ({len(csv_text)} bytes received).")
                    return csv_text, batch_id
                elif response.status_code in [400, 401, 403]:
                    logger.error(f"NASA FIRMS API authentication/request error (Status {response.status_code}): {response.text[:200]}")
                    raise FIRMSIngestionError(f"FIRMS API returned status {response.status_code}. Verify FIRMS_MAP_KEY.")
                else:
                    logger.warning(f"Attempt {attempt}/{retries}: API returned HTTP status {response.status_code}")
            except httpx.RequestError as exc:
                logger.warning(f"Attempt {attempt}/{retries}: Connection error requesting FIRMS data: {exc}")

        raise FIRMSIngestionError(f"Failed to fetch data from NASA FIRMS API after {retries} attempts.")

    def save_raw_data(self, csv_content: str, source: str, batch_id: str) -> str:
        """Saves exact raw CSV response with timestamped filename to preserve data lineage."""
        filename = f"firms_{source.lower()}_{batch_id}.csv"
        filepath = os.path.join(self.raw_data_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(csv_content)
            
        logger.info(f"Raw FIRMS CSV payload preserved at: {filepath}")
        return filepath

    def validate_and_clean_data(self, csv_content: str) -> Tuple[List[Dict[str, Any]], ValidationReport]:
        """
        Parses CSV, checks coordinates, values, duplicates, missing data, 
        and builds a detailed ValidationReport.
        """
        report = ValidationReport()
        if not csv_content.strip():
            return [], report

        try:
            df = pd.read_csv(StringIO(csv_content))
        except Exception as e:
            logger.error(f"Failed to parse FIRMS CSV response: {e}")
            return [], report

        report.total_records = len(df)
        if report.total_records == 0:
            return [], report

        # Expected FIRMS columns check
        required_cols = ["latitude", "longitude"]
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"Missing required coordinate column: {col}")
                return [], report

        valid_records = []
        seen_signatures = set()

        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            is_valid = True
            rejection_reasons = []

            # 1. Coordinate Validation
            try:
                lat = float(row_dict.get("latitude"))
                lon = float(row_dict.get("longitude"))
                if not (-90.0 <= lat <= 90.0):
                    is_valid = False
                    rejection_reasons.append(f"Latitude out of bounds: {lat}")
                if not (-180.0 <= lon <= 180.0):
                    is_valid = False
                    rejection_reasons.append(f"Longitude out of bounds: {lon}")
            except (ValueError, TypeError):
                is_valid = False
                rejection_reasons.append("Invalid or missing latitude/longitude numeric values")

            # 2. FRP Validation (if provided, must be >= 0)
            if "frp" in row_dict and pd.notnull(row_dict["frp"]):
                try:
                    frp = float(row_dict["frp"])
                    if frp < 0:
                        is_valid = False
                        rejection_reasons.append(f"Negative FRP value: {frp}")
                except (ValueError, TypeError):
                    row_dict["frp"] = None

            # 3. Duplicate Detection Signature
            acq_date = str(row_dict.get("acq_date", ""))
            acq_time = str(row_dict.get("acq_time", "")).zfill(4)
            satellite = str(row_dict.get("satellite", ""))
            
            sig = (lat if is_valid else 0, lon if is_valid else 0, acq_date, acq_time, satellite)
            if is_valid and sig in seen_signatures:
                is_valid = False
                report.duplicates += 1
                rejection_reasons.append("Duplicate observation record")
            elif is_valid:
                seen_signatures.add(sig)

            # 4. Check for missing critical values
            missing_fields = [k for k, v in row_dict.items() if pd.isnull(v)]
            if missing_fields:
                report.missing_values += 1

            if is_valid:
                # Calculate observation_timestamp
                obs_time = datetime.datetime.utcnow()
                if acq_date:
                    try:
                        time_str = acq_time if len(acq_time) == 4 else "0000"
                        hours = int(time_str[:2])
                        minutes = int(time_str[2:])
                        dt = datetime.datetime.strptime(acq_date, "%Y-%m-%d")
                        obs_time = dt.replace(hour=hours, minute=minutes)
                    except Exception:
                        pass
                
                cleaned_record = {
                    "latitude": float(row_dict["latitude"]),
                    "longitude": float(row_dict["longitude"]),
                    "bright_ti4": float(row_dict["bright_ti4"]) if "bright_ti4" in row_dict and pd.notnull(row_dict["bright_ti4"]) else None,
                    "bright_ti5": float(row_dict["bright_ti5"]) if "bright_ti5" in row_dict and pd.notnull(row_dict["bright_ti5"]) else None,
                    "scan": float(row_dict["scan"]) if "scan" in row_dict and pd.notnull(row_dict["scan"]) else None,
                    "track": float(row_dict["track"]) if "track" in row_dict and pd.notnull(row_dict["track"]) else None,
                    "acq_date": acq_date,
                    "acq_time": acq_time,
                    "satellite": str(row_dict.get("satellite", "")),
                    "instrument": str(row_dict.get("instrument", "VIIRS")),
                    "confidence": str(row_dict.get("confidence", "")),
                    "version": str(row_dict.get("version", "")),
                    "frp": float(row_dict["frp"]) if "frp" in row_dict and pd.notnull(row_dict["frp"]) else 0.0,
                    "daynight": str(row_dict.get("daynight", "D")),
                    "observation_timestamp": obs_time
                }
                valid_records.append(cleaned_record)
            else:
                report.invalid_records += 1
                report.rejected_records.append({
                    "row_index": idx,
                    "reasons": rejection_reasons,
                    "data": {k: str(v) for k, v in row_dict.items() if pd.notnull(v)}
                })

        report.valid_records = len(valid_records)
        return valid_records, report

    def ingest_firms_data(
        self, 
        db: Session,
        source: str = "VIIRS_SNPP_NRT", 
        area: str = "68.0,6.0,97.0,37.0", 
        days: int = 1,
        date: Optional[str] = None,
        raw_csv_override: Optional[str] = None
    ) -> FIRMSIngestionResponse:
        """
        Executes full ingestion pipeline:
        Fetch API CSV -> Save Raw Payload -> Clean & Validate -> Persist to PostGIS DB.
        """
        now = datetime.datetime.utcnow()
        batch_id = f"batch_{source}_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        if raw_csv_override is not None:
            batch_id = f"batch_mock_{now.strftime('%Y%m%d_%H%M%S')}"

        db_batch = IngestionBatch(
            id=batch_id,
            source=source,
            started_at=now,
            status="running"
        )
        db.add(db_batch)
        db.commit()

        try:
            if raw_csv_override is not None:
                csv_content = raw_csv_override
                raw_path = self.save_raw_data(csv_content, source, batch_id)
            else:
                csv_content, fetch_batch_id = self.fetch_firms_csv(source=source, area=area, days=days, date=date)
                raw_path = self.save_raw_data(csv_content, source, batch_id)

            cleaned_records, validation_report = self.validate_and_clean_data(csv_content)

            db_batch.records_received = validation_report.total_records
            db_batch.records_valid = validation_report.valid_records
            db_batch.records_rejected = validation_report.invalid_records

            ingested_count = 0
            for rec in cleaned_records:
                pt = create_point_geometry(rec["longitude"], rec["latitude"])
                
                # PostGIS geometry formatting
                geom_val = None
                if HAS_GEOALCHEMY2 and HAS_GEOALCHEMY_SHAPE and not is_sqlite and from_shape:
                    geom_val = from_shape(pt, srid=4326)
                else:
                    geom_val = pt.wkt

                obs = ThermalObservation(
                    latitude=rec["latitude"],
                    longitude=rec["longitude"],
                    geometry=geom_val,
                    bright_ti4=rec["bright_ti4"],
                    bright_ti5=rec["bright_ti5"],
                    scan=rec["scan"],
                    track=rec["track"],
                    acq_date=rec["acq_date"],
                    acq_time=rec["acq_time"],
                    satellite=rec["satellite"],
                    instrument=rec["instrument"],
                    confidence=rec["confidence"],
                    version=rec["version"],
                    frp=rec["frp"],
                    daynight=rec["daynight"],
                    observation_timestamp=rec["observation_timestamp"],
                    observation_time=rec["observation_timestamp"],
                    ingestion_timestamp=now,
                    source=source,
                    ingestion_batch_id=batch_id,
                    created_at=now
                )
                db.add(obs)
                ingested_count += 1

            db_batch.status = "completed"
            db_batch.completed_at = datetime.datetime.utcnow()
            db.commit()
            
            logger.info(f"Ingested {ingested_count} thermal observations into PostGIS database (Batch ID: {batch_id}).")

            safety_status = settings.get_firms_key_safety_status()

            return FIRMSIngestionResponse(
                status="success",
                batch_id=batch_id,
                source=source,
                records_ingested=ingested_count,
                raw_file_path=raw_path,
                validation_report=validation_report,
                safety_message=safety_status["message"]
            )
        except Exception as exc:
            db_batch.status = "failed"
            db_batch.error_message = str(exc)[:500]
            db_batch.completed_at = datetime.datetime.utcnow()
            db.commit()
            logger.error(f"Ingestion batch {batch_id} failed: {exc}")
            raise exc
