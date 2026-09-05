import logging
import math
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.thermal_observation import ThermalObservation
from app.models.industrial_facility import IndustrialFacility
from app.models.healthcare_facility import HealthcareFacility
from app.models.transportation_entity import TransportationEntity
from app.schemas.impact import ImpactEntity, ImpactAssessmentResponse
from app.geospatial.utils import calculate_geodesic_distance_meters

logger = logging.getLogger("firms_app.impact_service")

class ImpactAssessmentService:
    """
    Service layer executing spatial proximity queries to identify all industrial facilities 
    and energy infrastructure within a configurable assessment radius of a thermal event, 
    annotated with entity category, intrinsic Sensitivity Tier, and Footprint Scale classes.
    """

    @staticmethod
    def get_entity_category(facility_type: Optional[str]) -> str:
        """
        Categorizes facility type into high-level domain category:
        - power_plant / substation -> ENERGY
        - refinery / chemical / steel_works / industrial / fallback -> INDUSTRIAL
        """
        if not facility_type:
            return "INDUSTRIAL"
        ft = str(facility_type).strip().lower()
        if ft in ["power_plant", "substation"]:
            return "ENERGY"
        return "INDUSTRIAL"

    @staticmethod
    def get_sensitivity_tier(facility_type: Optional[str]) -> str:
        """
        Maps facility sector type to standardized sensitivity tier:
        - refinery / chemical -> CRITICAL
        - power_plant / substation -> HIGH
        - steel_works / industrial / fallback -> MODERATE
        """
        if not facility_type:
            return "MODERATE"
        ft = str(facility_type).strip().lower()
        if ft in ["refinery", "chemical"]:
            return "CRITICAL"
        elif ft in ["power_plant", "substation"]:
            return "HIGH"
        elif ft in ["steel_works", "industrial"]:
            return "MODERATE"
        else:
            return "MODERATE"

    @staticmethod
    def get_footprint_scale(area_sqm: Optional[float]) -> str:
        """
        Maps facility physical surface area in m² to footprint scale class:
        - > 300,000 m² -> MEGA_FACILITY
        - 150,000 m² to 300,000 m² -> LARGE_FACILITY
        - < 150,000 m² or null/invalid -> STANDARD_FACILITY
        """
        if area_sqm is None:
            return "STANDARD_FACILITY"
        try:
            val = float(area_sqm)
            if math.isnan(val) or val < 0:
                return "STANDARD_FACILITY"
            if val > 300000.0:
                return "MEGA_FACILITY"
            elif val >= 150000.0:
                return "LARGE_FACILITY"
            else:
                return "STANDARD_FACILITY"
        except (ValueError, TypeError):
            return "STANDARD_FACILITY"

    def assess_impact(
        self, 
        db: Session, 
        event_id: int, 
        assessment_radius_km: float = 5.0
    ) -> Optional[ImpactAssessmentResponse]:
        """
        Queries all industrial facilities, energy entities, healthcare facilities, and transportation
        corridors located within the configured assessment radius (in kilometers) of a target thermal observation ID.
        """
        obs = db.query(ThermalObservation).filter(ThermalObservation.id == event_id).first()
        if not obs:
            return None

        radius_meters = float(assessment_radius_km) * 1000.0
        is_postgres = db.bind.dialect.name == "postgresql"
        
        raw_entities: List[Tuple[Any, str, float]] = [] # (entity, category, distance)

        # 1. Industrial & Energy Facilities
        if is_postgres:
            try:
                obs_point = func.ST_SetSRID(func.ST_MakePoint(obs.longitude, obs.latitude), 4326)
                
                query = db.query(
                    IndustrialFacility,
                    func.ST_Distance(
                        IndustrialFacility.geometry.cast(func.geography), 
                        obs_point.cast(func.geography)
                    ).label("dist")
                ).filter(
                    IndustrialFacility.geometry != None,
                    func.ST_DWithin(
                        IndustrialFacility.geometry.cast(func.geography), 
                        obs_point.cast(func.geography), 
                        radius_meters
                    )
                ).order_by("dist")

                for fac, dist in query.all():
                    cat = self.get_entity_category(fac.facility_type)
                    raw_entities.append((fac, cat, float(dist)))
            except Exception as e:
                logger.error(f"PostGIS ST_DWithin industrial query failed, falling back to geodesic calculation: {e}")
                is_postgres = False

        if not is_postgres:
            lat_delta = radius_meters / 111111.0
            cos_lat = math.cos(math.radians(obs.latitude))
            lon_delta = radius_meters / (111111.0 * cos_lat) if cos_lat != 0 else lat_delta

            bbox_query = db.query(IndustrialFacility).filter(
                IndustrialFacility.latitude >= obs.latitude - lat_delta,
                IndustrialFacility.latitude <= obs.latitude + lat_delta,
                IndustrialFacility.longitude >= obs.longitude - lon_delta,
                IndustrialFacility.longitude <= obs.longitude + lon_delta
            )
            for fac in bbox_query.all():
                dist = calculate_geodesic_distance_meters(obs.latitude, obs.longitude, fac.latitude, fac.longitude)
                if dist <= radius_meters:
                    cat = self.get_entity_category(fac.facility_type)
                    raw_entities.append((fac, cat, dist))

        # 2. Healthcare Facilities
        hosp_query = db.query(HealthcareFacility).filter(
            HealthcareFacility.latitude >= obs.latitude - (radius_meters / 111111.0),
            HealthcareFacility.latitude <= obs.latitude + (radius_meters / 111111.0),
            HealthcareFacility.longitude >= obs.longitude - (radius_meters / (111111.0 * max(0.1, math.cos(math.radians(obs.latitude))))),
            HealthcareFacility.longitude <= obs.longitude + (radius_meters / (111111.0 * max(0.1, math.cos(math.radians(obs.latitude)))))
        )
        for hosp in hosp_query.all():
            dist = calculate_geodesic_distance_meters(obs.latitude, obs.longitude, hosp.latitude, hosp.longitude)
            if dist <= radius_meters:
                raw_entities.append((hosp, "HEALTHCARE", dist))

        # 3. Transportation Entities
        trans_query = db.query(TransportationEntity).filter(
            TransportationEntity.latitude >= obs.latitude - (radius_meters / 111111.0),
            TransportationEntity.latitude <= obs.latitude + (radius_meters / 111111.0),
            TransportationEntity.longitude >= obs.longitude - (radius_meters / (111111.0 * max(0.1, math.cos(math.radians(obs.latitude))))),
            TransportationEntity.longitude <= obs.longitude + (radius_meters / (111111.0 * max(0.1, math.cos(math.radians(obs.latitude)))))
        )
        for trans in trans_query.all():
            dist = calculate_geodesic_distance_meters(obs.latitude, obs.longitude, trans.latitude, trans.longitude)
            if dist <= radius_meters:
                raw_entities.append((trans, "TRANSPORTATION", dist))

        # Ensure strict ascending sort by distance
        raw_entities.sort(key=lambda x: x[2])

        # Build typed response entities with Phase 3D Display Labels & Location Context Metadata
        entities: List[ImpactEntity] = []
        for item, cat, dist in raw_entities:
            dist_m = round(dist, 2)
            dist_km = round(dist / 1000.0, 4)

            display_label = None
            location_context = None
            name_source = None
            location_source = None
            enriched_at = None

            if isinstance(item, IndustrialFacility):
                area_val = getattr(item, "area_sqm", None) or getattr(item, "surface_area_sqm", None)
                entity_type = item.facility_type or "industrial_facility"
                geom_type = "POLYGON" if (area_val and area_val > 100.0) else "POINT"
                sens_tier = self.get_sensitivity_tier(item.facility_type)
                footprint = self.get_footprint_scale(area_val)
                fac_id = item.id
                osm_id = getattr(item, "osm_id", None)
                name = item.name
                display_label = item.name or "Industrial Facility"
                name_source = "OSM" if item.name else "OSM_CLASSIFICATION"
                fac_type = item.facility_type
                lat, lon = item.latitude, item.longitude
            elif isinstance(item, HealthcareFacility):
                area_val = item.area_sqm
                entity_type = item.entity_type or "hospital"
                geom_type = "POLYGON" if (area_val and area_val > 100.0) else "POINT"
                sens_tier = "HIGH"
                footprint = self.get_footprint_scale(area_val)
                fac_id = item.id
                osm_id = item.osm_id
                name = item.name
                display_label = item.name or "Healthcare Facility"
                name_source = "OSM" if item.name else "OSM_CLASSIFICATION"
                fac_type = "hospital"
                lat, lon = item.latitude, item.longitude
            elif isinstance(item, TransportationEntity):
                entity_type = item.entity_type
                geom_type = "LINESTRING"
                sens_tier = "MODERATE"
                footprint = "STANDARD_FACILITY"
                fac_id = item.id
                osm_id = item.osm_id
                name = item.name if (item.name and not item.name.startswith("Corridor #")) else None
                
                # Use pre-computed Phase 3D display_label or build deterministically
                if item.display_label:
                    display_label = item.display_label
                    name_source = item.name_source or "OSM"
                else:
                    from app.services.nominatim_enrichment_service import NominatimEnrichmentService
                    display_label, name_source = NominatimEnrichmentService.build_display_label(name, None, item.entity_type)

                location_context = item.location_context
                location_source = item.location_source
                enriched_at = item.enriched_at

                fac_type = item.entity_type
                lat, lon = item.latitude, item.longitude
            else:
                continue

            entities.append(
                ImpactEntity(
                    entity_category=cat,
                    entity_type=entity_type,
                    facility_id=fac_id,
                    entity_id=fac_id,
                    osm_id=osm_id,
                    name=name,
                    display_label=display_label,
                    location_context=location_context,
                    name_source=name_source,
                    location_source=location_source,
                    enriched_at=enriched_at,
                    facility_type=fac_type,
                    geometry_type=geom_type,
                    distance_meters=dist_m,
                    distance_km=dist_km,
                    sensitivity_tier=sens_tier,
                    footprint_scale=footprint,
                    latitude=lat,
                    longitude=lon
                )
            )

        return ImpactAssessmentResponse(
            event_id=obs.id,
            event_latitude=obs.latitude,
            event_longitude=obs.longitude,
            assessment_radius_km=assessment_radius_km,
            total_entities_found=len(entities),
            entities=entities
        )
