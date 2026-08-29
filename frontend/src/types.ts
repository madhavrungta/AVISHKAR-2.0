export interface ThermalObservation {
  id: string;
  observation_timestamp: string;
  ingestion_timestamp: string;
  ingestion_batch_id: string;
  latitude: number;
  longitude: number;
  frp: number | null;
  bright_ti4: number | null;
  bright_ti5: number | null;
  confidence: string | null;
  satellite: string | null;
  instrument: string | null;
  daynight: string | null;
  scan: number | null;
  track: number | null;
  source: string;
}

export interface ThermalObservationPage {
  items: ThermalObservation[];
  limit: number;
  offset: number;
  total: number;
}

export interface IndustrialFacility {
  id: string;
  osm_id: number;
  osm_element_type: string;
  name: string | null;
  facility_type: string;
  latitude: number;
  longitude: number;
  source: string;
}

export interface FacilityPage {
  items: IndustrialFacility[];
  limit: number;
  offset: number;
  total: number;
}

export type AssociationType = "very_close" | "nearby" | "contextual";

export interface ThermalFacilityAssociation {
  id: string;
  thermal_observation_id: string;
  facility_id: string;
  distance_meters: number;
  association_type: AssociationType;
  association_score: number;
  created_at: string;
  thermal_observation?: ThermalObservation;
  facility?: IndustrialFacility;
  scientific_note?: string;
}

export interface AssociationPage {
  items: ThermalFacilityAssociation[];
  limit: number;
  offset: number;
  total: number;
}

export interface AssociationComputeResult {
  evaluated_observations: number;
  matched_observations: number;
  total_associations: number;
  by_type: Record<string, number>;
  radius_meters: number;
  computation_timestamp: string;
}

export interface AssociationSummary {
  total_associations: number;
  by_type: Record<string, number>;
  min_distance_meters: number | null;
  max_distance_meters: number | null;
  mean_distance_meters: number | null;
}

