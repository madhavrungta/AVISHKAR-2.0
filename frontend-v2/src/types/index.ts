export interface ThermalObservation {
  id: number;
  latitude: number;
  longitude: number;
  brightness: number;
  scan?: number;
  track?: number;
  acq_date: string;
  acq_time: string;
  satellite: string;
  instrument?: string;
  confidence?: string;
  version?: string;
  bright_t31?: number;
  frp?: number;
  daynight?: string;
  source_file?: string;
  ingestion_batch_id?: string;
  observation_timestamp: string;
  created_at?: string;
}

export interface IndustrialFacility {
  id: number;
  osm_id: number;
  name: string | null;
  facility_type: string;
  operator: string | null;
  latitude: number;
  longitude: number;
  surface_area_sqm: number;
  buffer_radius_meters: number;
  created_at: string;
}

export interface ThermalFacilityAssociation {
  id: number;
  observation_id: number;
  facility_id: number;
  distance_meters: number;
  is_within_facility_buffer: boolean;
  confidence_score: number;
  association_type?: string;
  created_at: string;
}

export interface ThermalClassification {
  id: number;
  observation_id: number;
  source_type: 'INDUSTRIAL' | 'NATURAL_FOREST' | 'AGRICULTURAL' | 'URBAN_RESIDENTIAL' | 'UNKNOWN';
  classification_confidence: number;
  land_cover_context: string | null;
  rule_trigger: string;
  created_at: string;
}

export interface FacilityHistoricalBehavior {
  id: number;
  facility_id: number;
  total_observations_count: number;
  mean_frp: number;
  median_frp: number;
  std_frp: number;
  p95_frp: number;
  p99_frp: number;
  active_months_mask: number;
  day_vs_night_ratio: number;
  last_analyzed_date: string;
  created_at: string;
}

export interface FacilityNormalBaseline {
  id: number;
  facility_id: number;
  baseline_frp_p50: number;
  baseline_frp_p95: number;
  baseline_frp_p99: number;
  baseline_temporal_spread: number;
  operating_mode: string;
  established_date: string;
  is_active: boolean;
  created_at: string;
}

export interface AbnormalThermalEvent {
  id: number;
  observation_id: number;
  facility_id: number | null;
  observed_frp: number;
  expected_baseline_p95: number;
  frp_multiplier_ratio: number;
  anomaly_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  detection_rule: string;
  facility_name?: string;
  facility_type?: string;
  created_at: string;
}

export interface VerificationRiskScore {
  id: number;
  observation_id: number;
  facility_id?: number | null;
  composite_risk_score: number;
  risk_level: 'CRITICAL_VERIFIED_RISK' | 'HIGH_RISK' | 'MEDIUM_RISK' | 'LOW_RISK';
  priority_tier?: 'CRITICAL_VERIFIED_RISK' | 'HIGH_RISK' | 'MEDIUM_RISK' | 'LOW_RISK';
  spatial_proximity_score: number;
  frp_multiplier_score?: number;
  frp_anomaly_score?: number;
  facility_sensitivity_score: number;
  optical_verification_confidence?: number;
  optical_confidence_proxy_score?: number;
  verification_source?: string;
  risk_reasoning?: string;
  verification_audit_status?: string;
  created_at?: string;
  evaluated_at?: string;
}

export interface AnalyticsSummary {
  total_observations: number;
  total_facilities: number;
  total_associations: number;
  total_anomalies: number;
  total_risk_evaluations: number;
  avg_frp: number;
  max_frp: number;
  satellite_counts: Record<string, number>;
  confidence_distribution: Record<string, number>;
}

export interface FacilityAnalyticsSummary {
  total_facilities: number;
  facility_types: Record<string, number>;
  top_active_facilities: Array<{
    id: number;
    name: string | null;
    facility_type: string;
    operator: string | null;
    observation_count: number;
  }>;
}

export interface ClassificationSummary {
  source_type_distribution: Record<string, number>;
  total_classifications: number;
}

export interface HistorySummary {
  facilities_profiled: number;
  avg_observations_per_facility: number;
}

export interface BaselineSummary {
  active_baselines_count: number;
  operating_mode_distribution: Record<string, number>;
}

export interface AnomalySummary {
  total_anomalies: number;
  severity_breakdown: Record<string, number>;
}

export interface RiskSummary {
  total_evaluated: number;
  tier_breakdown: Record<string, number>;
  avg_composite_score: number;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  database_status: string;
  firms_api_key_configured: boolean;
  firms_api_key_message: string;
  n8n_status: string;
  default_source: string;
  default_area: string;
}

export interface IngestionResponse {
  status: string;
  source: string;
  batch_id: string;
  records_ingested: number;
  validation_report: {
    total_records?: number;
    total_received?: number;
    valid_records: number;
    invalid_records: number;
    duplicates: number;
  };
  requested_days?: number;
  effective_days?: number | null;
  fallback_used?: boolean;
  message?: string | null;
}

export interface AIInvestigationResponse {
  observation_id: number;
  inquiry: string;
  status: string;
  analysis_summary: string;
  context_evidence: {
    frp_value: number;
    baseline_p95: number;
    anomaly_severity: string;
    risk_score: number;
    priority_tier: string;
    associated_facility: string;
    facility_type: string;
    verification_rule: string;
  };
  recommended_actions: string[];
  latency_ms: number;
  answer?: string;
  evidence_sources?: {
    used: string[];
    unavailable: string[];
  };
}

export interface MapFilters {
  satellite: string;
  minFrp: number;
  maxFrp: number;
  confidence: string;
  priority: string;
  facilityType: string;
  showAnomalies: boolean;
  showFacilities: boolean;
  showVectors: boolean;
  showEvents: boolean;
}

export interface ImpactEntity {
  entity_category: 'INDUSTRIAL' | 'ENERGY' | 'HEALTHCARE' | 'TRANSPORTATION';
  entity_type: string;
  facility_id: number;
  entity_id?: number;
  osm_id?: string;
  name: string | null;
  display_label?: string | null;
  location_context?: string | null;
  name_source?: string | null;
  location_source?: string | null;
  enriched_at?: string | null;
  facility_type: string | null;
  geometry_type: string;
  distance_meters: number;
  distance_km: number;
  sensitivity_tier: 'CRITICAL' | 'HIGH' | 'MODERATE' | null;
  footprint_scale: 'MEGA_FACILITY' | 'LARGE_FACILITY' | 'STANDARD_FACILITY' | null;
  latitude: number;
  longitude: number;
}

export interface ImpactAssessmentResponse {
  event_id: number;
  event_latitude: number;
  event_longitude: number;
  assessment_radius_km: number;
  total_entities_found: number;
  scientific_disclaimer: string;
  entities: ImpactEntity[];
}
