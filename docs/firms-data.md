# NASA FIRMS Data & Scientific Standard

## Supported Products

Phase 1 supports VIIRS active-fire / thermal-anomaly datasets:
- `VIIRS_SNPP_NRT`: Suomi-NPP VIIRS Near Real-Time (375m resolution)
- `VIIRS_NOAA20_NRT`: NOAA-20 VIIRS Near Real-Time (375m resolution)
- `VIIRS_NOAA21_NRT`: NOAA-21 VIIRS Near Real-Time (375m resolution)

---

## Schema Reference

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `latitude` | Float | Center latitude of thermal anomaly pixel (EPSG:4326) |
| `longitude` | Float | Center longitude of thermal anomaly pixel (EPSG:4326) |
| `bright_ti4` | Float | VIIRS Channel I-4 brightness temperature (Kelvin) |
| `bright_ti5` | Float | VIIRS Channel I-5 brightness temperature (Kelvin) |
| `scan` | Float | Spatial pixel scan width (km) |
| `track` | Float | Spatial pixel track height (km) |
| `acq_date` | String | Satellite acquisition date (`YYYY-MM-DD`) |
| `acq_time` | String | Satellite acquisition time (`HHMM` UTC) |
| `satellite` | String | Satellite identifier (`N`=Suomi-NPP, `N20`=NOAA-20, `N21`=NOAA-21) |
| `instrument` | String | Sensor name (`VIIRS`) |
| `confidence` | String | Algorithm confidence level (`low`, `nominal`, `high`) |
| `version` | String | Processing algorithm version (e.g. `2.0NRT`) |
| `frp` | Float | Fire Radiative Power (Megawatts - MW) |
| `daynight` | String | Day orbit (`D`) or Night orbit (`N`) |

---

## Scientific Distinction Standard

> [!IMPORTANT]
> **THERMAL ANOMALY $\ne$ CONFIRMED FIRE**
>
> A NASA FIRMS pixel indicates a surface temperature anomaly exceeding background baseline. In industrial zones, high thermal radiative output frequently originates from routine operations (gas flares, steel blast furnaces, refinery processing unit heat).
>
> The system strictly adheres to responsible terminology:
> - Thermal Anomaly
> - Potential Industrial Event
> - Candidate Heat Source
> - Requires Verification
