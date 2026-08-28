export interface ThermalObservation {
  id: number;
  latitude: number;
  longitude: number;
  bright_ti4?: number;
  bright_ti5?: number;
  scan?: number;
  track?: number;
  acq_date?: string;
  acq_time?: string;
  satellite?: string;
  instrument?: string;
  confidence?: string;
  version?: string;
  frp?: number;
  daynight?: string;
  observation_timestamp: string;
  ingestion_timestamp: string;
  source: string;
  ingestion_batch_id: string;
  geometry_wkt?: string;
}

export interface IndustrialFacility {
  id: number;
  osm_id: string;
  name?: string;
  facility_type: string;
  operator?: string;
  latitude: number;
  longitude: number;
  area_sqm: number;
  raw_tags?: Record<string, any>;
  ingestion_batch_id: string;
  created_at: string;
  geometry_wkt?: string;
}

export interface ThermalFacilityAssociation {
  id: number;
  observation_id: number;
  facility_id: number;
  distance_meters: number;
  association_type: string;
  created_at: string;
  facility_name?: string;
  facility_type?: string;
  facility_latitude?: number;
  facility_longitude?: number;
}

export interface ThermalClassification {
  id: number;
  observation_id: number;
  predicted_class: string;
  confidence_score: number;
  classification_reason: string;
  feature_vector?: Record<string, any>;
  created_at: string;
}

export interface FacilityHistoricalBehavior {
  id: number;
  facility_id: number;
  total_observations: number;
  observation_days: number;
  min_frp: number;
  max_frp: number;
  mean_frp: number;
  median_frp: number;
  p95_frp: number;
  p99_frp: number;
  day_count: number;
  night_count: number;
  day_night_ratio: number;
  activity_tier: string;
  first_observed?: string;
  last_observed?: string;
  updated_at: string;
  facility_name?: string;
  facility_type?: string;
}

export interface FacilityNormalBaseline {
  id: number;
  facility_id: number;
  baseline_frp_p50: number;
  baseline_frp_p95: number;
  baseline_frp_p99: number;
  monthly_frequency: number;
  day_night_preference: string;
  baseline_status: string;
  updated_at: string;
  facility_name?: string;
  facility_type?: string;
}

export interface AbnormalThermalEvent {
  id: number;
  observation_id: number;
  facility_id: number;
  observed_frp: number;
  baseline_p95_frp: number;
  frp_multiplier_ratio: number;
  anomaly_severity: string;
  scientific_caution_label: string;
  explanation_reason: string;
  detected_at: string;
  facility_name?: string;
  facility_type?: string;
  latitude?: number;
  longitude?: number;
}

export interface VerificationRiskScore {
  id: number;
  observation_id: number;
  facility_id?: number;
  composite_risk_score: number;
  risk_level: string;
  spatial_proximity_score: number;
  frp_multiplier_score: number;
  facility_sensitivity_score: number;
  optical_verification_confidence: number;
  verification_source: string;
  risk_breakdown_json?: Record<string, any>;
  evaluated_at: string;
  facility_name?: string;
  facility_type?: string;
  latitude?: number;
  longitude?: number;
}

export interface AnalyticsSummary {
  total_observations: number;
  max_frp: number | null;
  min_frp: number | null;
  avg_frp: number | null;
  latest_observation: string | null;
  satellites_breakdown: Record<string, number>;
  sources_breakdown: Record<string, number>;
}

export interface FacilityAnalyticsSummary {
  total_facilities: number;
  total_area_sqkm: number;
  type_breakdown: Record<string, number>;
  largest_facility?: {
    id: number;
    name?: string;
    facility_type: string;
    area_sqm: number;
    latitude: number;
    longitude: number;
  } | null;
}

export interface ClassificationSummary {
  total_classifications: number;
  class_breakdown: Record<string, number>;
  avg_confidence: number;
}

export interface HistorySummary {
  total_monitored_facilities: number;
  tier_breakdown: Record<string, number>;
  max_p95_frp_overall: number;
  highest_activity_facility?: {
    facility_id: number;
    name?: string;
    facility_type: string;
    total_observations: number;
    p95_frp: number;
  } | null;
}

export interface BaselineSummary {
  total_baselines: number;
  established_count: number;
  preliminary_count: number;
  avg_p95_frp_overall: number;
}

export interface AnomalySummary {
  total_anomalies: number;
  severity_breakdown: Record<string, number>;
  max_multiplier_ratio: number;
  highest_anomaly?: {
    observation_id: number;
    facility_name?: string;
    facility_type: string;
    multiplier_ratio: number;
    severity: string;
  } | null;
}

export interface RiskSummary {
  total_evaluations: number;
  tier_breakdown: Record<string, number>;
  avg_composite_score: number;
  highest_risk_observation?: {
    observation_id: number;
    facility_name?: string;
    facility_type: string;
    composite_risk_score: number;
    risk_level: string;
    optical_confidence: number;
  } | null;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  database_status: string;
  firms_api_key_configured: boolean;
  firms_api_key_message: string;
  n8n_status?: string;
  default_source: string;
  default_area: string;
}

export interface ValidationReport {
  total_records: number;
  valid_records: number;
  invalid_records: number;
  duplicates: number;
  missing_values: number;
}

export interface IngestionResponse {
  status: string;
  batch_id: string;
  source: string;
  records_ingested: number;
  raw_file_path?: string;
  validation_report: ValidationReport;
  safety_message: string;
}

export interface OSMIngestionResponse {
  status: string;
  batch_id: string;
  facilities_ingested: number;
  raw_file_path?: string;
  types_summary: Record<string, number>;
}

export interface RunAssociationResponse {
  status: string;
  total_observations_processed: number;
  associations_created: number;
  direct_matches: number;
  proximate_matches: number;
  vicinity_matches: number;
  unassociated: number;
}

export interface RunClassificationResponse {
  status: string;
  total_processed: number;
  classifications_created: number;
  industrial_candidates: number;
  natural_forest_candidates: number;
  agricultural_candidates: number;
  other_unknown: number;
}

export interface RunHistoryResponse {
  status: string;
  facilities_profiled: number;
  highly_persistent: number;
  moderately_active: number;
  sporadic: number;
  no_historical_anomalies: number;
}

export interface GenerateBaselineResponse {
  status: string;
  baselines_generated: number;
  established_baselines: number;
  preliminary_defaults: number;
}

export interface DetectAnomalyResponse {
  status: string;
  total_evaluated: number;
  anomalies_detected: number;
  moderate_spikes: number;
  high_spikes: number;
  critical_anomalies: number;
}

export interface EvaluateRiskResponse {
  status: string;
  total_evaluated: number;
  critical_verified: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
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

