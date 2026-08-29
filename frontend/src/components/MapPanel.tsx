import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import type { Feature, FeatureCollection, LineString, Point } from "geojson";
import { fetchFacilityAssociations, fetchObservationAssociations } from "../api";
import type { IndustrialFacility, ThermalFacilityAssociation, ThermalObservation } from "../types";

interface MapPanelProps {
  observations: ThermalObservation[];
  facilities: IndustrialFacility[];
  selectedObservationId?: string | null;
  selectedFacilityId?: string | null;
  onSelectObservation?: (obs: ThermalObservation | null) => void;
  onSelectFacility?: (fac: IndustrialFacility | null) => void;
}

function observationsToGeoJSON(
  observations: ThermalObservation[],
): FeatureCollection<Point> {
  return {
    type: "FeatureCollection",
    features: observations.map((obs) => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [obs.longitude, obs.latitude] },
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

function facilitiesToGeoJSON(
  facilities: IndustrialFacility[],
): FeatureCollection<Point> {
  return {
    type: "FeatureCollection",
    features: facilities.map((f) => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [f.longitude, f.latitude] },
      properties: {
        id: f.id,
        osm_id: f.osm_id,
        osm_element_type: f.osm_element_type,
        name: f.name,
        facility_type: f.facility_type,
        source: f.source,
      },
    })),
  };
}

function displayValue(value: string | number | null | undefined): string {
  return value === null || value === undefined ? "Not supplied" : String(value);
}

function formatDistance(meters: number): string {
  if (meters < 1000) {
    return `${Math.round(meters)} m`;
  }
  return `${(meters / 1000).toFixed(2)} km`;
}

function formatTypeBadge(type: string): string {
  if (type === "very_close") return "Very Close (≤500m)";
  if (type === "nearby") return "Nearby (≤2km)";
  return "Contextual (≤5km)";
}

const FIRMS_SOURCE_ID = "thermal-observations";
const FIRMS_LAYER_ID = "thermal-circles";
const FACILITY_SOURCE_ID = "industrial-facilities";
const FACILITY_LAYER_ID = "facility-squares";
const LINES_SOURCE_ID = "association-lines";
const LINES_LAYER_ID = "association-lines-layer";

export function MapPanel({
  observations,
  facilities,
  onSelectObservation,
  onSelectFacility,
}: MapPanelProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);

  const [showFirms, setShowFirms] = useState(true);
  const [showFacilities, setShowFacilities] = useState(true);
  const [showLines, setShowLines] = useState(true);
  const [activeAssociations, setActiveAssociations] = useState<ThermalFacilityAssociation[]>([]);

  // Initialize map once
  useEffect(() => {
    if (containerRef.current === null || mapRef.current !== null) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      center: [77.2, 28.55],
      zoom: 9,
      attributionControl: { compact: true },
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
        layers: [{ id: "openstreetmap", type: "raster", source: "openstreetmap" }],
      },
    });

    map.on("load", () => {
      // Dynamic association connection lines layer (rendered under points)
      map.addSource(LINES_SOURCE_ID, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: LINES_LAYER_ID,
        type: "line",
        source: LINES_SOURCE_ID,
        paint: {
          "line-color": "#e11d48",
          "line-width": 2.5,
          "line-dasharray": [2, 2],
          "line-opacity": 0.85,
        },
      });

      // FIRMS thermal anomaly layer
      map.addSource(FIRMS_SOURCE_ID, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: FIRMS_LAYER_ID,
        type: "circle",
        source: FIRMS_SOURCE_ID,
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 1, 3, 6, 6, 10, 9],
          "circle-color": "#dc5a24",
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 1.5,
          "circle-opacity": 0.85,
        },
      });

      // Industrial facilities layer
      map.addSource(FACILITY_SOURCE_ID, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: FACILITY_LAYER_ID,
        type: "circle",
        source: FACILITY_SOURCE_ID,
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 1, 4, 6, 7, 10, 11],
          "circle-color": "#1d6fa4",
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 1.5,
          "circle-opacity": 0.9,
        },
      });

      // FIRMS popup and association linkage
      map.on("click", FIRMS_LAYER_ID, async (e) => {
        if (!e.features?.length) return;
        const coords = (e.features[0].geometry as Point).coordinates.slice() as [number, number];
        const p = e.features[0].properties!;
        const obsId = p.id as string;

        popupRef.current?.remove();

        // Initial popup with loading placeholder
        const popup = new maplibregl.Popup({ offset: 12, maxWidth: "340px" })
          .setLngLat(coords)
          .setHTML(`
            <div style="font-size:13px;color:#1e293b;line-height:1.5">
              <p style="font-weight:700;color:#dc5a24;margin:0 0 4px">🔥 NASA FIRMS Thermal Anomaly</p>
              <p style="margin:2px 0"><strong>Timestamp:</strong> ${displayValue(p.timestamp)}</p>
              <p style="margin:2px 0"><strong>FRP:</strong> ${displayValue(p.frp)} MW</p>
              <p style="margin:2px 0"><strong>Confidence:</strong> ${displayValue(p.confidence)}</p>
              <p style="margin:2px 0"><strong>Satellite:</strong> ${displayValue(p.satellite)}</p>
              <div style="margin-top:8px;padding-top:8px;border-top:1px solid #e2e8f0;font-size:12px;color:#64748b">
                <em>Checking spatial proximity to industrial facilities…</em>
              </div>
            </div>
          `)
          .addTo(map);
        popupRef.current = popup;

        try {
          const assocs = await fetchObservationAssociations(obsId);
          setActiveAssociations(assocs);

          // Build connection lines to candidate facilities
          const lineFeatures: Feature<LineString>[] = assocs
            .filter((a) => a.facility)
            .map((a) => ({
              type: "Feature",
              geometry: {
                type: "LineString",
                coordinates: [coords, [a.facility!.longitude, a.facility!.latitude]],
              },
              properties: { distance: a.distance_meters, type: a.association_type },
            }));

          const linesSource = map.getSource(LINES_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
          if (linesSource) {
            linesSource.setData({ type: "FeatureCollection", features: lineFeatures });
          }

          // Build associations HTML list
          let assocsHtml = "";
          if (assocs.length === 0) {
            assocsHtml = `
              <div style="margin-top:8px;padding:6px 8px;background:#f8fafc;border-radius:4px;font-size:12px;color:#64748b">
                No industrial facilities within search radius.
              </div>`;
          } else {
            const items = assocs
              .map(
                (a) => `
                <div style="margin-top:4px;padding:6px 8px;background:#f1f5f9;border-radius:4px;font-size:12px">
                  <div style="font-weight:600;color:#0f172a">🏭 ${a.facility?.name || "Unnamed facility"}</div>
                  <div style="color:#475569">Type: ${a.facility?.facility_type || "industrial"} · <strong>${formatDistance(a.distance_meters)}</strong> (${formatTypeBadge(a.association_type)})</div>
                  <div style="color:#64748b;font-size:11px">Proximity Score: <strong>${a.association_score}</strong></div>
                </div>
              `,
              )
              .join("");

            assocsHtml = `
              <div style="margin-top:8px;padding-top:8px;border-top:1px solid #e2e8f0">
                <p style="font-weight:600;font-size:12px;color:#0f172a;margin:0 0 4px">📍 Spatial Proximity Candidates (${assocs.length}):</p>
                <div style="max-height:140px;overflow-y:auto">${items}</div>
                <p style="margin-top:6px;font-size:10px;color:#94a3b8;line-height:1.3;font-style:italic">
                  ⚠️ Spatial proximity indicates co-location only. It does not confirm an industrial fire.
                </p>
              </div>`;
          }

          popup.setHTML(`
            <div style="font-size:13px;color:#1e293b;line-height:1.5">
              <p style="font-weight:700;color:#dc5a24;margin:0 0 4px">🔥 NASA FIRMS Thermal Anomaly</p>
              <p style="margin:2px 0"><strong>Timestamp:</strong> ${displayValue(p.timestamp)}</p>
              <p style="margin:2px 0"><strong>FRP:</strong> ${displayValue(p.frp)} MW</p>
              <p style="margin:2px 0"><strong>Confidence:</strong> ${displayValue(p.confidence)}</p>
              <p style="margin:2px 0"><strong>Satellite:</strong> ${displayValue(p.satellite)}</p>
              ${assocsHtml}
            </div>
          `);
        } catch {
          // Keep base popup if association fetch failed
        }
      });

      // Facility popup and association linkage
      map.on("click", FACILITY_LAYER_ID, async (e) => {
        if (!e.features?.length) return;
        const coords = (e.features[0].geometry as Point).coordinates.slice() as [number, number];
        const p = e.features[0].properties!;
        const facId = p.id as string;

        popupRef.current?.remove();

        const popup = new maplibregl.Popup({ offset: 12, maxWidth: "340px" })
          .setLngLat(coords)
          .setHTML(`
            <div style="font-size:13px;color:#1e293b;line-height:1.5">
              <p style="font-weight:700;color:#1d6fa4;margin:0 0 4px">🏭 Industrial Facility</p>
              <p style="margin:2px 0"><strong>Name:</strong> ${displayValue(p.name) === "Not supplied" ? "Unnamed facility" : displayValue(p.name)}</p>
              <p style="margin:2px 0"><strong>Type:</strong> ${displayValue(p.facility_type)}</p>
              <p style="margin:2px 0"><strong>OSM ID:</strong> ${displayValue(p.osm_id)} (${displayValue(p.osm_element_type)})</p>
              <div style="margin-top:8px;padding-top:8px;border-top:1px solid #e2e8f0;font-size:12px;color:#64748b">
                <em>Checking nearby thermal anomalies…</em>
              </div>
            </div>
          `)
          .addTo(map);
        popupRef.current = popup;

        try {
          const assocs = await fetchFacilityAssociations(facId);
          setActiveAssociations(assocs);

          // Build connection lines to associated anomalies
          const lineFeatures: Feature<LineString>[] = assocs
            .filter((a) => a.thermal_observation)
            .map((a) => ({
              type: "Feature",
              geometry: {
                type: "LineString",
                coordinates: [coords, [a.thermal_observation!.longitude, a.thermal_observation!.latitude]],
              },
              properties: { distance: a.distance_meters, type: a.association_type },
            }));

          const linesSource = map.getSource(LINES_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
          if (linesSource) {
            linesSource.setData({ type: "FeatureCollection", features: lineFeatures });
          }

          let assocsHtml = "";
          if (assocs.length === 0) {
            assocsHtml = `
              <div style="margin-top:8px;padding:6px 8px;background:#f8fafc;border-radius:4px;font-size:12px;color:#64748b">
                No thermal anomalies within proximity radius.
              </div>`;
          } else {
            const items = assocs
              .map(
                (a) => `
                <div style="margin-top:4px;padding:6px 8px;background:#fff1f2;border-radius:4px;font-size:12px">
                  <div style="font-weight:600;color:#9f1239">🔥 Thermal Anomaly · ${formatDistance(a.distance_meters)}</div>
                  <div style="color:#475569">FRP: ${a.thermal_observation?.frp ?? "N/A"} MW · Satellite: ${a.thermal_observation?.satellite ?? "VIIRS"}</div>
                  <div style="color:#64748b;font-size:11px">Relationship: <strong>${formatTypeBadge(a.association_type)}</strong> (Score: ${a.association_score})</div>
                </div>
              `,
              )
              .join("");

            assocsHtml = `
              <div style="margin-top:8px;padding-top:8px;border-top:1px solid #e2e8f0">
                <p style="font-weight:600;font-size:12px;color:#0f172a;margin:0 0 4px">🔥 Proximate Thermal Anomalies (${assocs.length}):</p>
                <div style="max-height:140px;overflow-y:auto">${items}</div>
                <p style="margin-top:6px;font-size:10px;color:#94a3b8;line-height:1.3;font-style:italic">
                  ⚠️ Spatial proximity indicates co-location only. It does not confirm an industrial fire.
                </p>
              </div>`;
          }

          popup.setHTML(`
            <div style="font-size:13px;color:#1e293b;line-height:1.5">
              <p style="font-weight:700;color:#1d6fa4;margin:0 0 4px">🏭 Industrial Facility</p>
              <p style="margin:2px 0"><strong>Name:</strong> ${displayValue(p.name) === "Not supplied" ? "Unnamed facility" : displayValue(p.name)}</p>
              <p style="margin:2px 0"><strong>Type:</strong> ${displayValue(p.facility_type)}</p>
              <p style="margin:2px 0"><strong>OSM ID:</strong> ${displayValue(p.osm_id)} (${displayValue(p.osm_element_type)})</p>
              ${assocsHtml}
            </div>
          `);
        } catch {
          // Keep base popup if association fetch failed
        }
      });

      // Clear lines on map background click
      map.on("click", (e) => {
        const features = map.queryRenderedFeatures(e.point, {
          layers: [FIRMS_LAYER_ID, FACILITY_LAYER_ID],
        });
        if (!features.length) {
          const linesSource = map.getSource(LINES_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
          if (linesSource) {
            linesSource.setData({ type: "FeatureCollection", features: [] });
          }
          setActiveAssociations([]);
        }
      });

      // Cursor affordance
      for (const layerId of [FIRMS_LAYER_ID, FACILITY_LAYER_ID]) {
        map.on("mouseenter", layerId, () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", layerId, () => {
          map.getCanvas().style.cursor = "";
        });
      }
    });

    mapRef.current = map;
    return () => {
      popupRef.current?.remove();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update FIRMS data
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const update = () => {
      const source = map.getSource(FIRMS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
      if (!source) return;
      source.setData(observationsToGeoJSON(observations));
      if (observations.length > 0) {
        const bounds = new maplibregl.LngLatBounds();
        for (const obs of observations) bounds.extend([obs.longitude, obs.latitude]);
        if (observations.length === 1) {
          map.flyTo({ center: bounds.getCenter(), zoom: 8, essential: true });
        } else {
          map.fitBounds(bounds, { padding: 64, maxZoom: 9, duration: 0 });
        }
      }
    };
    if (map.isStyleLoaded()) update();
    else map.on("load", update);
  }, [observations]);

  // Update facilities data
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const update = () => {
      const source = map.getSource(FACILITY_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
      if (!source) return;
      source.setData(facilitiesToGeoJSON(facilities));
      if (facilities.length > 0 && observations.length === 0) {
        const bounds = new maplibregl.LngLatBounds();
        for (const f of facilities) bounds.extend([f.longitude, f.latitude]);
        map.fitBounds(bounds, { padding: 64, maxZoom: 10, duration: 0 });
      }
    };
    if (map.isStyleLoaded()) update();
    else map.on("load", update);
  }, [facilities, observations.length]);

  // Toggle FIRMS layer visibility
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    map.setLayoutProperty(FIRMS_LAYER_ID, "visibility", showFirms ? "visible" : "none");
  }, [showFirms]);

  // Toggle facilities layer visibility
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    map.setLayoutProperty(FACILITY_LAYER_ID, "visibility", showFacilities ? "visible" : "none");
  }, [showFacilities]);

  // Toggle association lines visibility
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    map.setLayoutProperty(LINES_LAYER_ID, "visibility", showLines ? "visible" : "none");
  }, [showLines]);

  return (
    <div className="relative">
      {/* Layer toggles */}
      <div className="absolute top-3 right-3 z-10 flex flex-col gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-md text-xs">
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={showFirms}
            onChange={(e) => setShowFirms(e.target.checked)}
            className="accent-orange-500"
          />
          <span className="inline-block w-3 h-3 rounded-full bg-[#dc5a24]" />
          NASA FIRMS anomalies ({observations.length})
        </label>
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={showFacilities}
            onChange={(e) => setShowFacilities(e.target.checked)}
            className="accent-blue-600"
          />
          <span className="inline-block w-3 h-3 rounded-full bg-[#1d6fa4]" />
          Industrial facilities ({facilities.length})
        </label>
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={showLines}
            onChange={(e) => setShowLines(e.target.checked)}
            className="accent-rose-500"
          />
          <span className="inline-block w-3 h-0.5 bg-[#e11d48]" />
          Spatial association lines
        </label>
      </div>

      <div
        ref={containerRef}
        className="h-[65vh] min-h-[440px] w-full"
        aria-label="Thermal anomaly and industrial facility map with spatial association"
      />
    </div>
  );
}
