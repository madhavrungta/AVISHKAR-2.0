import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Circle, CircleMarker, Polyline, Popup, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { 
  ThermalObservation, 
  IndustrialFacility, 
  ThermalFacilityAssociation, 
  ThermalClassification, 
  FacilityHistoricalBehavior, 
  FacilityNormalBaseline, 
  AbnormalThermalEvent, 
  VerificationRiskScore, 
  MapFilters,
  ImpactAssessmentResponse,
  ImpactEntity
} from '../../types';
import { Crosshair, Radio, Flame, Building2, ShieldAlert } from 'lucide-react';

interface MapWorkspaceProps {
  observations: ThermalObservation[];
  facilities: IndustrialFacility[];
  associations: ThermalFacilityAssociation[];
  classifications: ThermalClassification[];
  histories: FacilityHistoricalBehavior[];
  baselines: FacilityNormalBaseline[];
  anomalies: AbnormalThermalEvent[];
  riskScores: VerificationRiskScore[];
  filters: MapFilters;
  loading: boolean;
  selectedObservation: ThermalObservation | null;
  selectedFacility: IndustrialFacility | null;
  impactData?: ImpactAssessmentResponse | null;
  impactRadius?: number;
  onSelectObservation: (obs: ThermalObservation) => void;
  onSelectFacility: (fac: IndustrialFacility) => void;
}

// Coordinate Tracker Controller Component
const MapCoordinatesTracker: React.FC<{ onCoordsChange: (coords: { lat: number; lng: number } | null) => void }> = ({ onCoordsChange }) => {
  useMapEvents({
    mousemove: (e) => {
      onCoordsChange({ lat: e.latlng.lat, lng: e.latlng.lng });
    },
    mouseout: () => {
      onCoordsChange(null);
    }
  });
  return null;
};

// Container ResizeObserver & Invalidation Controller Component
const MapResizer: React.FC = () => {
  const map = useMap();

  useEffect(() => {
    const container = map.getContainer();
    if (!container) return;

    const observer = new ResizeObserver(() => {
      map.invalidateSize();
    });

    observer.observe(container);

    return () => {
      observer.disconnect();
    };
  }, [map]);

  return null;
};

// Smooth Camera Controller Component
const MapCameraAutoFly: React.FC<{
  targetCoords: [number, number] | null;
  targetKey: string | null;
}> = ({ targetCoords, targetKey }) => {
  const map = useMap();
  const prevKeyRef = React.useRef<string | null>(null);

  useEffect(() => {
    if (targetKey && targetCoords && prevKeyRef.current !== targetKey) {
      prevKeyRef.current = targetKey;
      map.invalidateSize();
      map.flyTo(targetCoords, 13, { duration: 1.5, easeLinearity: 0.25 });
    } else if (!targetKey) {
      prevKeyRef.current = null;
    }
  }, [targetKey, targetCoords, map]);

  return null;
};

// Sub-component for Facility Marker to access useMap context for popups
const FacilityMarkerItem: React.FC<{
  fac: IndustrialFacility;
  isSelected: boolean;
  isExposed: boolean;
  onSelectFacility: (fac: IndustrialFacility) => void;
}> = ({ fac, isSelected, isExposed, onSelectFacility }) => {
  const map = useMap();
  const radius = Math.max(300, Math.sqrt(fac.surface_area_sqm || 100000));
  const isEnergy = fac.facility_type === 'power_plant' || fac.facility_type === 'substation';

  const highlightColor = isEnergy ? '#f59e0b' : '#38bdf8';
  const highlightFill = isEnergy ? '#d97706' : '#0284c7';

  return (
    <React.Fragment>
      {/* Outer Pulse Ring for Potentially Exposed Facility/Energy Node within Impact Assessment Radius */}
      {isExposed && (
        <Circle
          center={[fac.latitude, fac.longitude]}
          radius={radius + 150}
          pathOptions={{
            color: highlightColor,
            fillColor: highlightColor,
            fillOpacity: 0.20,
            weight: 2,
            dashArray: '3, 3',
            className: 'animate-pulse'
          }}
        />
      )}

      <Circle
        center={[fac.latitude, fac.longitude]}
        radius={radius}
        pathOptions={{
          color: isSelected ? '#ffffff' : isExposed ? highlightColor : isEnergy ? '#f59e0b' : '#c084fc',
          fillColor: isSelected ? highlightColor : isExposed ? highlightFill : isEnergy ? '#d97706' : '#a855f7',
          fillOpacity: isSelected ? 0.3 : isExposed ? 0.25 : 0.12,
          weight: isSelected ? 2.5 : isExposed ? 2 : 1.5,
          dashArray: '4, 4'
        }}
        eventHandlers={{
          click: () => onSelectFacility(fac)
        }}
      >
      <Popup>
        <div className="p-2 flex flex-col gap-1.5 min-w-[200px] font-sans">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-1">
            <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider font-mono">INDUSTRIAL FACILITY</span>
            <span className="text-[10px] font-mono text-slate-400">OSM #{fac.osm_id}</span>
          </div>
          <h4 className="font-bold text-sm text-white">{fac.name || 'Industrial Facility'}</h4>
          <div className="flex justify-between text-xs text-slate-400">
            <span>Type: <strong className="text-purple-300 uppercase">{fac.facility_type}</strong></span>
            <span>Area: <strong className="text-slate-200">{(fac.surface_area_sqm / 10000).toFixed(1)} ha</strong></span>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSelectFacility(fac);
              map.closePopup();
            }}
            className="mt-2 w-full py-1.5 bg-purple-950/80 hover:bg-purple-900 border border-purple-500/40 text-purple-200 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
          >
            View Facility Profile
          </button>
        </div>
      </Popup>
    </Circle>
  </React.Fragment>
  );
};

// Sub-component for Observation Marker to access useMap context for popups
const ThermalObservationMarkerItem: React.FC<{
  obs: ThermalObservation;
  isSelected: boolean;
  risk?: VerificationRiskScore;
  anom?: AbnormalThermalEvent;
  onSelectObservation: (obs: ThermalObservation) => void;
}> = ({ obs, isSelected, risk, anom, onSelectObservation }) => {
  const map = useMap();
  const riskTier = risk?.risk_level || risk?.priority_tier;
  const composite = risk?.composite_risk_score ?? 0;
  const isCritical = riskTier === 'CRITICAL_VERIFIED_RISK' || composite >= 85 || (anom && anom.anomaly_severity === 'CRITICAL');
  const isHigh = riskTier === 'HIGH_RISK' || composite >= 60 || (obs.frp || 0) >= 40;

  const markerColor = isCritical ? '#ef4444' : isHigh ? '#f97316' : '#f59e0b';
  const markerRadius = isSelected ? 12 : isCritical ? 9 : isHigh ? 7 : 5;

  return (
    <React.Fragment>
      {/* Outer Dashed Radar Boundary Circle for Critical Hotspots */}
      {isCritical && (
        <CircleMarker
          center={[obs.latitude, obs.longitude]}
          radius={26}
          pathOptions={{
            color: '#ef4444',
            fillColor: '#ef4444',
            fillOpacity: 0.08,
            weight: 1.5,
            dashArray: '4, 4'
          }}
        />
      )}

      {/* Inner Pulsing Radar Ring */}
      {(isCritical || isSelected) && (
        <CircleMarker
          center={[obs.latitude, obs.longitude]}
          radius={markerRadius + 8}
          pathOptions={{
            color: isSelected ? '#38bdf8' : markerColor,
            fillColor: isSelected ? '#38bdf8' : markerColor,
            fillOpacity: 0.2,
            weight: 1.5,
            className: 'animate-ring-pulse'
          }}
        />
      )}

      <CircleMarker
        center={[obs.latitude, obs.longitude]}
        radius={markerRadius}
        pathOptions={{
          color: isSelected ? '#ffffff' : markerColor,
          fillColor: markerColor,
          fillOpacity: 0.9,
          weight: isSelected ? 3 : 1.5
        }}
        eventHandlers={{
          click: () => onSelectObservation(obs)
        }}
      >
        <Popup>
          <div className="p-2 flex flex-col gap-2 min-w-[220px] font-sans">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-1.5">
              <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider font-mono flex items-center gap-1">
                <Flame className="w-3 h-3 text-red-400" /> OBS #{obs.id}
              </span>
              {risk && (
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                  risk.composite_risk_score > 80 ? 'bg-red-950 text-red-300 border border-red-500/40' : 'bg-orange-950 text-orange-300 border border-orange-500/40'
                }`}>
                  Risk {risk.composite_risk_score.toFixed(0)}/100
                </span>
              )}
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Radiative Power:</span>
              <span className="font-bold text-red-400 font-mono text-sm">{obs.frp} MW</span>
            </div>

            <div className="flex justify-between text-xs text-slate-400 font-mono">
              <span>Brightness: {obs.brightness} K</span>
              <span>Sat: {obs.satellite}</span>
            </div>

            <div className="text-[11px] text-slate-500 font-mono">
              Pass: {obs.acq_date} {obs.acq_time} UTC
            </div>

            <button
              onClick={(e) => {
                e.stopPropagation();
                onSelectObservation(obs);
                map.closePopup();
              }}
              className="mt-1 w-full py-1.5 bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-500/40 text-cyan-300 text-xs font-semibold rounded-lg transition-colors shadow-glow-cyan cursor-pointer"
            >
              Open Target Dossier
            </button>
          </div>
        </Popup>
      </CircleMarker>
    </React.Fragment>
  );
};

export const MapWorkspace: React.FC<MapWorkspaceProps> = ({
  observations,
  facilities,
  associations,
  classifications,
  histories,
  baselines,
  anomalies,
  riskScores,
  filters,
  loading,
  selectedObservation,
  selectedFacility,
  impactData,
  impactRadius = 5.0,
  onSelectObservation,
  onSelectFacility
}) => {
  const [cursorCoords, setCursorCoords] = useState<{ lat: number; lng: number } | null>(null);

  // Filter Observations
  const filteredObservations = observations.filter((obs) => {
    if (!filters.showAnomalies) return false;
    if (filters.satellite !== 'ALL' && !obs.satellite?.toLowerCase().includes(filters.satellite.toLowerCase())) return false;
    if (filters.minFrp > 0 && (obs.frp || 0) < filters.minFrp) return false;

    if (filters.priority !== 'ALL') {
      const risk = riskScores.find(r => r.observation_id === obs.id);
      const anom = anomalies.find(a => a.observation_id === obs.id);
      const riskLevel = risk?.risk_level || risk?.priority_tier;
      const composite = risk?.composite_risk_score ?? 0;

      const isCriticalObs = riskLevel === 'CRITICAL_VERIFIED_RISK' || composite >= 85 || (anom && anom.anomaly_severity === 'CRITICAL');
      const isHighObs = riskLevel === 'HIGH_RISK' || (composite >= 60 && composite < 85) || (anom && anom.anomaly_severity === 'HIGH') || (obs.frp || 0) >= 40;
      const isMedObs = riskLevel === 'MEDIUM_RISK' || (composite >= 30 && composite < 60) || (anom && anom.anomaly_severity === 'MEDIUM');
      const isLowObs = riskLevel === 'LOW_RISK' || composite < 30;

      if (filters.priority === 'CRITICAL' && !isCriticalObs) return false;
      if (filters.priority === 'HIGH' && !isHighObs) return false;
      if (filters.priority === 'MEDIUM' && !isMedObs) return false;
      if (filters.priority === 'LOW' && !isLowObs) return false;
    }
    return true;
  });

  // Calculate target camera coords and stable key
  const targetKey = selectedObservation
    ? `obs-${selectedObservation.id}`
    : selectedFacility
    ? `fac-${selectedFacility.id}`
    : null;

  const targetCoords: [number, number] | null = selectedObservation
    ? [selectedObservation.latitude, selectedObservation.longitude]
    : selectedFacility
    ? [selectedFacility.latitude, selectedFacility.longitude]
    : null;

  return (
    <div className="w-full h-full relative min-h-0 overflow-hidden bg-[#060913]">
      {/* Top Right Live Telemetry Reticle HUD */}
      <div className="absolute top-4 right-4 z-20 pointer-events-none hidden md:flex items-center gap-3 glass-panel px-4 py-2 rounded-2xl border border-white/[0.08] shadow-2xl font-mono text-xs text-slate-300">
        <div className="flex items-center gap-2">
          <Crosshair className="w-4 h-4 text-cyan-400 animate-spin" style={{ animationDuration: '10s' }} />
          <span className="text-slate-400">RETICLE COORDINATES:</span>
          <span className="font-bold text-white">
            {cursorCoords
              ? `${cursorCoords.lat.toFixed(4)}° N, ${cursorCoords.lng.toFixed(4)}° E`
              : '23.5937° N, 82.9629° E (PAN-INDIA)'}
          </span>
        </div>
      </div>

      {/* Primary Leaflet Container */}
      <MapContainer
        center={[22.5, 78.5]}
        zoom={5}
        scrollWheelZoom={true}
        zoomControl={false}
        className="w-full h-full flex-1"
        style={{ width: '100%', height: '100%' }}
      >
        {/* Dark Stadia Alidade Smooth Dark Basemap — no API key required */}
        <TileLayer
          attribution='&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>'
          url="https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png"
          maxZoom={20}
          subdomains="abcd"
        />

        <MapResizer />
        <MapCoordinatesTracker onCoordsChange={setCursorCoords} />
        <MapCameraAutoFly targetCoords={targetCoords} targetKey={targetKey} />

        {/* Association Proximity Vectors */}
        {filters.showVectors && associations.map((assoc) => {
          const obs = observations.find(o => o.id === assoc.observation_id);
          const fac = facilities.find(f => f.id === assoc.facility_id);
          if (!obs || !fac) return null;

          const isSelected = selectedObservation?.id === obs.id || selectedFacility?.id === fac.id;

          return (
            <Polyline
              key={assoc.id}
              positions={[
                [obs.latitude, obs.longitude],
                [fac.latitude, fac.longitude]
              ]}
              pathOptions={{
                color: isSelected ? '#00f0ff' : '#a855f7',
                weight: isSelected ? 3 : 1.5,
                dashArray: isSelected ? '4, 4' : '2, 4',
                opacity: isSelected ? 0.9 : 0.4
              }}
            />
          );
        })}

        {/* Spatial Assessment Radius Boundary Circle around Selected Observation */}
        {selectedObservation && (
          <Circle
            center={[selectedObservation.latitude, selectedObservation.longitude]}
            radius={(impactData?.assessment_radius_km ?? impactRadius ?? 5.0) * 1000}
            pathOptions={{
              color: '#38bdf8',
              fillColor: '#0284c7',
              fillOpacity: 0.06,
              weight: 1.5,
              dashArray: '6, 6'
            }}
          />
        )}

        {/* Industrial Facilities Layer */}
        {filters.showFacilities && facilities.map((fac) => {
          const isExposed = impactData?.entities.some((e: ImpactEntity) => e.facility_id === fac.id) ?? false;
          return (
            <FacilityMarkerItem
              key={fac.id}
              fac={fac}
              isSelected={selectedFacility?.id === fac.id}
              isExposed={isExposed}
              onSelectFacility={onSelectFacility}
            />
          );
        })}

        {/* Thermal Anomaly Observations Layer */}
        {filteredObservations.map((obs) => (
          <ThermalObservationMarkerItem
            key={obs.id}
            obs={obs}
            isSelected={selectedObservation?.id === obs.id}
            risk={riskScores.find(r => r.observation_id === obs.id)}
            anom={anomalies.find(a => a.observation_id === obs.id)}
            onSelectObservation={onSelectObservation}
          />
        ))}
      </MapContainer>
    </div>
  );
};
