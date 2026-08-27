import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import type { ThermalObservation } from "../types";

interface MapPanelProps {
  observations: ThermalObservation[];
}

function observationsToGeoJSON(
  observations: ThermalObservation[],
): GeoJSON.FeatureCollection<GeoJSON.Point> {
  return {
    type: "FeatureCollection",
    features: observations.map((obs) => ({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [obs.longitude, obs.latitude],
      },
      properties: {
        id: obs.id,
        timestamp: new Date(obs.observation_timestamp).toLocaleString(),
        frp: obs.frp,
        confidence: obs.confidence,
        satellite: obs.satellite,
        bright_ti4: obs.bright_ti4,
        bright_ti5: obs.bright_ti5,
        daynight: obs.daynight,
      },
    })),
  };
}

function displayValue(value: string | number | null | undefined): string {
  return value === null || value === undefined ? "Not supplied" : String(value);
}

const SOURCE_ID = "thermal-observations";
const CIRCLE_LAYER_ID = "thermal-circles";

export function MapPanel({ observations }: MapPanelProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);

  // Initialize map once
  useEffect(() => {
    if (containerRef.current === null || mapRef.current !== null) {
      return;
    }
    const map = new maplibregl.Map({
      container: containerRef.current,
      center: [0, 20],
      zoom: 1.2,
      attributionControl: true,
      style: {
        version: 8,
        sources: {
          openstreetmap: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
        },
        layers: [
          {
            id: "openstreetmap",
            type: "raster",
            source: "openstreetmap",
          },
        ],
      },
    });

    map.on("load", () => {
      map.addSource(SOURCE_ID, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      map.addLayer({
        id: CIRCLE_LAYER_ID,
        type: "circle",
        source: SOURCE_ID,
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            1, 3,
            6, 5,
            10, 8,
          ],
          "circle-color": "#dc5a24",
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 1.5,
          "circle-opacity": 0.85,
        },
      });

      // Popup on click
      map.on("click", CIRCLE_LAYER_ID, (e) => {
        if (!e.features || e.features.length === 0) return;
        const feature = e.features[0];
        const coords = (feature.geometry as GeoJSON.Point).coordinates.slice() as [number, number];
        const props = feature.properties!;

        const html = `
          <div style="font-size:13px;color:#1e293b;line-height:1.6">
            <p style="font-weight:600;margin:0 0 4px">NASA FIRMS thermal anomaly</p>
            <p style="margin:2px 0">Timestamp (UTC): ${displayValue(props.timestamp)}</p>
            <p style="margin:2px 0">FRP: ${displayValue(props.frp)}</p>
            <p style="margin:2px 0">Confidence: ${displayValue(props.confidence)}</p>
            <p style="margin:2px 0">Satellite: ${displayValue(props.satellite)}</p>
            <p style="margin:2px 0">Brightness Ti4: ${displayValue(props.bright_ti4)}</p>
            <p style="margin:2px 0">Brightness Ti5: ${displayValue(props.bright_ti5)}</p>
            <p style="margin:2px 0">Day / night: ${displayValue(props.daynight)}</p>
          </div>
        `;

        popupRef.current?.remove();
        popupRef.current = new maplibregl.Popup({ offset: 12 })
          .setLngLat(coords)
          .setHTML(html)
          .addTo(map);
      });

      // Cursor affordance
      map.on("mouseenter", CIRCLE_LAYER_ID, () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", CIRCLE_LAYER_ID, () => {
        map.getCanvas().style.cursor = "";
      });
    });

    mapRef.current = map;
    return () => {
      popupRef.current?.remove();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update data when observations change
  useEffect(() => {
    const map = mapRef.current;
    if (map === null) return;

    const updateSource = () => {
      const source = map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
      if (!source) return;

      const geojson = observationsToGeoJSON(observations);
      source.setData(geojson);

      if (observations.length > 0) {
        const bounds = new maplibregl.LngLatBounds();
        for (const obs of observations) {
          bounds.extend([obs.longitude, obs.latitude]);
        }
        if (observations.length === 1) {
          map.flyTo({ center: bounds.getCenter(), zoom: 7, essential: true });
        } else {
          map.fitBounds(bounds, { padding: 64, maxZoom: 9, duration: 0 });
        }
      }
    };

    if (map.isStyleLoaded()) {
      updateSource();
    } else {
      map.on("load", updateSource);
    }
  }, [observations]);

  return <div ref={containerRef} className="h-[65vh] min-h-[420px] w-full" aria-label="Thermal anomaly map" />;
}
