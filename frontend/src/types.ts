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

