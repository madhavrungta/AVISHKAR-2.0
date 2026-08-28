import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Circle, Polyline, ZoomControl } from 'react-leaflet';
import { 
  ThermalObservation, 
  IndustrialFacility, 
  ThermalFacilityAssociation, 
  ThermalClassification,
  FacilityHistoricalBehavior,
  FacilityNormalBaseline,
  AbnormalThermalEvent,
  VerificationRiskScore,
  MapFilters 
} from '../types';

interface FirmsMapProps {
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
  onSelectObservation: (obs: ThermalObservation) => void;
  onSelectFacility: (fac: IndustrialFacility) => void;
}

export const FirmsMap: React.FC<FirmsMapProps> = ({ 
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
  onSelectObservation,
  onSelectFacility
}) => {
  const defaultCenter: [number, number] = [20.5937, 78.9629];
  const defaultZoom = 5;

  const getMarkerColor = (obsId: number, frp?: number) => {
    // Check if selected
    if (selectedObservation?.id === obsId) return '#00f0ff'; // Cyan

    // Check if high priority
    const risk = riskScores.find(r => r.observation_id === obsId);
    const isHighPriority = (risk && risk.composite_risk_score > 60) || anomalies.some(a => a.observation_id === obsId);
    if (isHighPriority) return '#dc2626'; // Red

    return '#f59e0b'; // Amber (thermal anomaly)
  };

  const getFacilityColor = (facId: number, type: string) => {
    if (selectedFacility?.id === facId) return '#00f0ff'; // Cyan (Selected)
    return '#6366f1'; // Indigo/Violet for industrial facilities
  };

  const getClassBadgeColor = (pClass: string) => {
    switch (pClass) {
      case 'INDUSTRIAL_CANDIDATE': return 'bg-purple-950 text-purple-200 border-purple-500/50';
      case 'NATURAL_FOREST_CANDIDATE': return 'bg-emerald-950 text-emerald-200 border-emerald-500/50';
      case 'AGRICULTURAL_CANDIDATE': return 'bg-amber-950 text-amber-200 border-amber-500/50';
      default: return 'bg-slate-800 text-slate-300 border-slate-600';
    }
  };

  const getRiskBadgeColor = (level: string) => {
    switch (level) {
      case 'CRITICAL_VERIFIED_RISK': return 'bg-red-950 text-red-200 border-red-500/80';
      case 'HIGH_RISK': return 'bg-orange-950 text-orange-200 border-orange-500/80';
      case 'MEDIUM_RISK': return 'bg-amber-950 text-amber-200 border-amber-500/70';
      default: return 'bg-slate-800 text-slate-300 border-slate-600';
    }
  };

  const assocMap = new Map<number, ThermalFacilityAssociation>();
  (associations || []).forEach(a => assocMap.set(a.observation_id, a));

  const clfMap = new Map<number, ThermalClassification>();
  (classifications || []).forEach(c => clfMap.set(c.observation_id, c));

  const histMap = new Map<number, FacilityHistoricalBehavior>();
  (histories || []).forEach(h => histMap.set(h.facility_id, h));

  const baseMap = new Map<number, FacilityNormalBaseline>();
  (baselines || []).forEach(b => baseMap.set(b.facility_id, b));

  const anomMap = new Map<number, AbnormalThermalEvent>();
  (anomalies || []).forEach(a => anomMap.set(a.observation_id, a));

  const riskMap = new Map<number, VerificationRiskScore>();
  (riskScores || []).forEach(r => riskMap.set(r.observation_id, r));

  // Filter Observations
  const filteredObservations = observations.filter((obs) => {
    if (!filters.showAnomalies) return false;

    const frp = obs.frp ?? 0;
    if (frp < filters.minFrp || frp > filters.maxFrp) return false;

    if (filters.satellite !== 'ALL' && obs.satellite && !obs.satellite.includes(filters.satellite)) {
      return false;
    }

    if (filters.confidence !== 'ALL' && obs.confidence !== filters.confidence) {
      return false;
    }

    if (filters.priority !== 'ALL') {
      const risk = riskMap.get(obs.id);
      if (filters.priority === 'CRITICAL' && (!risk || risk.composite_risk_score <= 85)) return false;
      if (filters.priority === 'HIGH' && (!risk || risk.composite_risk_score <= 60 || risk.composite_risk_score > 85)) return false;
      if (filters.priority === 'MEDIUM' && (!risk || risk.composite_risk_score <= 30 || risk.composite_risk_score > 60)) return false;
      if (filters.priority === 'LOW' && (risk && risk.composite_risk_score > 30)) return false;
    }

    return true;
  });

  // Filter Facilities
  const filteredFacilities = facilities.filter((fac) => {
    if (!filters.showFacilities) return false;
    if (filters.facilityType !== 'ALL' && fac.facility_type !== filters.facilityType) return false;
    return true;
  });

  return (
    <div className="relative w-full h-full bg-slate-950">
      {loading && (
        <div className="absolute top-3 right-3 z-[1000] bg-slate-900/90 text-amber-400 text-xs px-3 py-1.5 rounded-md shadow border border-amber-500/30 flex items-center gap-2 backdrop-blur-md font-mono">
          <div className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-ping" />
          <span>Processing GIS Telemetry...</span>
        </div>
      )}

      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        zoomControl={false}
        style={{ width: '100%', height: '100%' }}
        className="z-0"
      >
        <ZoomControl position="bottomright" />

        <TileLayer
          url={import.meta.env.VITE_MAP_TILE_URL || "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"}
          attribution='Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, &copy; OpenStreetMap contributors, and the GIS user community'
        />

        {/* Thermal Observations Markers */}
        {filteredObservations.map((obs) => {
          const color = getMarkerColor(obs.id, obs.frp);
          const assoc = assocMap.get(obs.id);
          const clf = clfMap.get(obs.id);
          const anom = anomMap.get(obs.id);
          const risk = riskMap.get(obs.id);

          const isHighPriority = (risk && risk.composite_risk_score > 60) || !!anom;
          const isSelected = selectedObservation?.id === obs.id;
          const radius = isSelected ? 12 : (isHighPriority ? 9 : Math.max(5, Math.min(8, (obs.frp || 5) / 8)));

          return (
            <CircleMarker
              key={`obs-${obs.id}`}
              center={[obs.latitude, obs.longitude]}
              radius={radius}
              eventHandlers={{
                click: () => onSelectObservation(obs)
              }}
              pathOptions={{
                color: isSelected ? '#ffffff' : (isHighPriority ? '#dc2626' : '#d97706'),
                fillColor: color,
                fillOpacity: isSelected ? 1.0 : 0.8,
                weight: isSelected ? 3.5 : (isHighPriority ? 2.5 : 1.5)
              }}
            >
              <Popup>
                <div className="p-1 min-w-[280px] max-w-[320px] text-xs font-mono">
                  <div className="flex items-center justify-between border-b border-slate-700 pb-1.5 mb-2">
                    <span className="font-bold text-amber-400 flex items-center gap-1">
                      🔥 Observation #{obs.id}
                    </span>
                    {risk ? (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border font-bold uppercase ${getRiskBadgeColor(risk.risk_level)}`}>
                        Score {risk.composite_risk_score.toFixed(0)}/100
                      </span>
                    ) : (
                      clf && (
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border font-bold uppercase ${getClassBadgeColor(clf.predicted_class)}`}>
                          {clf.predicted_class.replace('_CANDIDATE', '')}
                        </span>
                      )
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-y-1 gap-x-2 text-slate-200 text-[11px]">
                    <span className="text-slate-400">Acquisition Time:</span>
                    <span className="font-mono text-right">{obs.acq_date || 'N/A'} {obs.acq_time ? `${obs.acq_time} UTC` : ''}</span>

                    <span className="text-slate-400">FRP Intensity:</span>
                    <span className="font-bold text-red-400 text-right font-mono">{obs.frp != null ? `${obs.frp} MW` : 'N/A'}</span>

                    <span className="text-slate-400">Brightness TI4 / TI5:</span>
                    <span className="font-mono text-right text-slate-300">{obs.bright_ti4 ?? 'N/A'} K / {obs.bright_ti5 ?? 'N/A'} K</span>

                    <span className="text-slate-400">Confidence:</span>
                    <span className="text-right font-semibold uppercase text-slate-300">{obs.confidence || 'Nominal'}</span>

                    <span className="text-slate-400">Satellite Instrument:</span>
                    <span className="text-right font-medium text-slate-300">{obs.satellite || 'VIIRS'} ({obs.daynight === 'D' ? 'Day' : 'Night'})</span>

                    {assoc && assoc.facility_name && (
                      <>
                        <span className="text-slate-400 border-t border-slate-700/60 pt-1">Nearby Facility:</span>
                        <span className="text-right font-semibold text-purple-300 border-t border-slate-700/60 pt-1">{assoc.facility_name}</span>
                      </>
                    )}
                  </div>

                  <div className="mt-2 pt-1.5 border-t border-slate-800 flex justify-end">
                    <button
                      onClick={() => onSelectObservation(obs)}
                      className="text-[10px] text-amber-400 hover:text-amber-300 font-bold flex items-center gap-1"
                    >
                      View Intelligence Drawer &rarr;
                    </button>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        {/* Industrial Facilities Circles */}
        {filteredFacilities.map((fac) => {
          const isSelected = selectedFacility?.id === fac.id;
          const facColor = getFacilityColor(fac.id, fac.facility_type);
          const radiusMeters = Math.max(Math.sqrt(fac.area_sqm / Math.PI), 120);
          const base = baseMap.get(fac.id);

          return (
            <Circle
              key={`fac-${fac.id}`}
              center={[fac.latitude, fac.longitude]}
              radius={radiusMeters}
              eventHandlers={{
                click: () => onSelectFacility(fac)
              }}
              pathOptions={{
                color: isSelected ? '#00f0ff' : facColor,
                fillColor: facColor,
                fillOpacity: isSelected ? 0.45 : 0.25,
                weight: isSelected ? 3 : 1.5
              }}
            >
              <Popup>
                <div className="p-1 min-w-[260px] max-w-[300px] text-xs font-mono">
                  <div className="flex items-center justify-between border-b border-slate-700 pb-1.5 mb-2">
                    <span className="font-bold text-purple-400 flex items-center gap-1.5">
                      <span>🏭</span>
                      <span>{fac.name || 'Industrial Facility'}</span>
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded border border-purple-500/40 bg-purple-950 font-bold uppercase text-purple-300">
                      {fac.facility_type}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-y-1 gap-x-2 text-slate-200 text-[11px]">
                    <span className="text-slate-400">Operator:</span>
                    <span className="text-right text-slate-200">{fac.operator || 'Unknown'}</span>
                    <span className="text-slate-400">Area:</span>
                    <span className="text-right font-mono text-slate-200">{(fac.area_sqm / 1000).toFixed(1)} k m²</span>
                    {base && (
                      <>
                        <span className="text-slate-400">Historical P95 Baseline:</span>
                        <span className="text-right font-bold font-mono text-amber-300">{base.baseline_frp_p95} MW</span>
                      </>
                    )}
                  </div>

                  <div className="mt-2 pt-1.5 border-t border-slate-800 flex justify-end">
                    <button
                      onClick={() => onSelectFacility(fac)}
                      className="text-[10px] text-purple-400 hover:text-purple-300 font-bold flex items-center gap-1"
                    >
                      View Facility Baseline &rarr;
                    </button>
                  </div>
                </div>
              </Popup>
            </Circle>
          );
        })}

        {/* Facility Proximity Vectors */}
        {filters.showVectors && (
          associations.map((assoc) => {
            const obs = observations.find(o => o.id === assoc.observation_id);
            if (!obs || assoc.facility_latitude == null || assoc.facility_longitude == null) return null;
            return (
              <Polyline
                key={`vector-${assoc.id}`}
                positions={[
                  [obs.latitude, obs.longitude],
                  [assoc.facility_latitude, assoc.facility_longitude]
                ]}
                pathOptions={{
                  color: assoc.association_type === 'DIRECT_MATCH' ? '#dc2626' : '#f59e0b',
                  weight: 1.5,
                  dashArray: '4, 4',
                  opacity: 0.75
                }}
              />
            );
          })
        )}
      </MapContainer>

      {/* Floating Map Visual Legend (Restrained Monochrome/Intelligence Style) */}
      <div className="absolute bottom-4 left-4 z-[999] bg-slate-900 border border-slate-800 rounded p-2 shadow-2xl text-[9px] text-slate-300 font-mono flex flex-col gap-1 select-none w-48">
        <span className="font-bold text-slate-400 border-b border-slate-850 pb-0.5 uppercase tracking-wider text-[9px]">
          MAP LEGEND
        </span>
        <div className="flex flex-col gap-1 pt-0.5">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <span>Thermal Anomaly</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-650" />
            <span>High Priority Anomaly</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-indigo-500" />
            <span>Industrial Facility</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>Selected Event</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FirmsMap;
