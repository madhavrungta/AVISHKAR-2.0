# PostGIS Database Schema: `thermal_observations`

Table definition for persisting NASA FIRMS observations.

```sql
CREATE TABLE thermal_observations (
    id SERIAL PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geometry GEOMETRY(Point, 4326),
    bright_ti4 DOUBLE PRECISION,
    bright_ti5 DOUBLE PRECISION,
    scan DOUBLE PRECISION,
    track DOUBLE PRECISION,
    acq_date VARCHAR(10),
    acq_time VARCHAR(4),
    satellite VARCHAR(20),
    instrument VARCHAR(20),
    confidence VARCHAR(10),
    version VARCHAR(20),
    frp DOUBLE PRECISION,
    daynight VARCHAR(1),
    observation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    ingestion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    source VARCHAR(50) NOT NULL,
    ingestion_batch_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indices for rapid spatial and temporal queries
CREATE INDEX idx_thermal_lat_lon ON thermal_observations (latitude, longitude);
CREATE INDEX idx_thermal_source_date ON thermal_observations (source, acq_date);
CREATE INDEX idx_thermal_obs_time ON thermal_observations (observation_timestamp);
CREATE INDEX idx_thermal_frp ON thermal_observations (frp);
CREATE INDEX idx_thermal_geom ON thermal_observations USING GIST (geometry);
```
