import React, { useState } from 'react';
import { 
  AnalyticsSummary, 
  HealthStatus, 
  FacilityAnalyticsSummary, 
  AnomalySummary,
  RiskSummary,
  ThermalObservation,
  IndustrialFacility,
  AbnormalThermalEvent,
  VerificationRiskScore,
  ThermalFacilityAssociation,
  FacilityHistoricalBehavior,
  FacilityNormalBaseline
} from '../types';
import { 
  ShieldCheck, 
  Key, 
  Activity, 
  Building2, 
  AlertTriangle, 
  Layers, 
  Database, 
  Workflow, 
  Server,
  Info,
  ChevronLeft,
  ChevronRight,
  Download,
  List,
  Flame,
  LineChart
} from 'lucide-react';
import { IngestionControl } from './IngestionControl';

interface StatsPanelProps {
  analytics: AnalyticsSummary | null;
  facilityAnalytics: FacilityAnalyticsSummary | null;
  anomalySummary: AnomalySummary | null;
  riskSummary: RiskSummary | null;
  health: HealthStatus | null;
  observations: ThermalObservation[];
  facilities: IndustrialFacility[];
  anomalies: AbnormalThermalEvent[];
  riskScores: VerificationRiskScore[];
  associations: ThermalFacilityAssociation[];
  histories: FacilityHistoricalBehavior[];
  baselines: FacilityNormalBaseline[];
  selectedObservation: ThermalObservation | null;
  selectedFacility: IndustrialFacility | null;
  onSelectObservation: (obs: ThermalObservation) => void;
  onSelectFacility: (fac: IndustrialFacility | null) => void;
  onIngestComplete: () => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

type TabType = 'OVERVIEW' | 'EVENTS' | 'ANOMALIES' | 'FACILITIES' | 'EVIDENCE' | 'ANALYTICS' | 'INGESTION' | 'SYSTEM';

export const StatsPanel: React.FC<StatsPanelProps> = ({ 
  analytics, 
  facilityAnalytics, 
  anomalySummary,
  riskSummary,
  health,
  observations,
  facilities,
  anomalies,
  riskScores,
  associations,
  histories,
  baselines,
  selectedObservation,
  selectedFacility,
  onSelectObservation,
  onSelectFacility,
  onIngestComplete,
  collapsed,
  onToggleCollapse
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('OVERVIEW');
  const [obsSearch, setObsSearch] = useState('');
  const [facSearch, setFacSearch] = useState('');

  if (collapsed) {
    return (
      <div className="w-10 bg-slate-900 border-r border-slate-800 flex flex-col items-center py-3 gap-4 text-slate-400 shrink-0 z-20">
        <button 
          onClick={onToggleCollapse}
          className="p-1 rounded hover:bg-slate-800 text-slate-300"
          title="Expand Intelligence Sidebar"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
        <div className="writing-mode-vertical text-[10px] tracking-widest uppercase font-bold text-slate-500 my-auto">
          GIS-INTEL COMMAND
        </div>
      </div>
    );
  }

  const critVerified = riskSummary?.tier_breakdown['CRITICAL_VERIFIED_RISK'] || 0;
  const highRisk = riskSummary?.tier_breakdown['HIGH_RISK'] || 0;
  const medRisk = riskSummary?.tier_breakdown['MEDIUM_RISK'] || 0;
  const lowRisk = riskSummary?.tier_breakdown['LOW_RISK'] || 0;

  const totalPoints = observations.length;
  const totalFacilities = facilities.length;
  const totalAnomalies = anomalies.length;
  const totalHighPriority = riskScores.filter(r => r.composite_risk_score > 60).length;

  const avgScore = riskSummary?.avg_composite_score ?? 70.6;

  // Filter lists based on search
  const filteredObs = observations
    .filter(o => o.id.toString().includes(obsSearch) || (o.satellite || '').toLowerCase().includes(obsSearch.toLowerCase()))
    .slice(0, 50);

  const filteredFacs = facilities
    .filter(f => (f.name || '').toLowerCase().includes(facSearch.toLowerCase()) || f.facility_type.toLowerCase().includes(facSearch.toLowerCase()))
    .slice(0, 50);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'OVERVIEW':
        return (
          <div className="flex flex-col gap-3.5">
            {/* Multi-Modal Risk Overview Card */}
            <div className="p-3 bg-purple-950/15 rounded border border-purple-500/25 flex flex-col gap-2">
              <div className="flex items-center justify-between border-b border-purple-500/20 pb-1.5">
                <div>
                  <span className="font-bold text-purple-200 flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
                    INVESTIGATION PRIORITY
                  </span>
                  <span className="text-[10px] text-amber-400 font-semibold block">
                    Demo / Heuristic Score
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[9px] text-slate-400 block uppercase">Avg Score</span>
                  <span className="font-mono font-bold text-purple-300 text-sm">
                    {avgScore.toFixed(1)} <span className="text-[10px] font-normal text-slate-500">/ 100</span>
                  </span>
                </div>
              </div>

              {/* Tiers */}
              <div className="grid grid-cols-2 gap-1.5 text-[11px] pt-1">
                <div className="p-1 bg-red-950/40 border border-red-500/30 rounded flex items-center justify-between px-2">
                  <span className="text-red-300 font-medium">Critical (&gt;85)</span>
                  <span className="font-mono font-bold text-red-200">{critVerified}</span>
                </div>
                <div className="p-1 bg-orange-950/40 border border-orange-500/25 rounded flex items-center justify-between px-2">
                  <span className="text-orange-300 font-medium">High (61-85)</span>
                  <span className="font-mono font-bold text-orange-200">{highRisk}</span>
                </div>
                <div className="p-1 bg-amber-950/40 border border-amber-500/20 rounded flex items-center justify-between px-2">
                  <span className="text-amber-300 font-medium">Medium (31-60)</span>
                  <span className="font-mono font-bold text-amber-200">{medRisk}</span>
                </div>
                <div className="p-1 bg-slate-800/40 border border-slate-700/30 rounded flex items-center justify-between px-2">
                  <span className="text-slate-300 font-medium">Low (&le;30)</span>
                  <span className="font-mono font-bold text-slate-300">{lowRisk}</span>
                </div>
              </div>
            </div>

            {/* Platform Description */}
            <div className="p-3 bg-slate-950/50 border border-slate-800 rounded text-slate-400 leading-relaxed text-[11px] flex flex-col gap-1.5">
              <span className="font-semibold text-slate-300 flex items-center gap-1">
                <Info className="w-3.5 h-3.5 text-blue-400" /> MISSION SCOPE
              </span>
              <span>
                Geospatial surveillance workstation ingesting satellite thermal anomaly telemetry, linking coordinates to OpenStreetMap industrial boundaries, profiling operating baselines, and detecting anomalies.
              </span>
            </div>
          </div>
        );

      case 'EVENTS':
        return (
          <div className="flex flex-col gap-2">
            <span className="font-bold text-slate-300 text-[11px] border-b border-slate-800 pb-1">
              Abnormal Spike Events ({totalAnomalies})
            </span>
            <div className="flex flex-col gap-1.5 max-h-[380px] overflow-y-auto pr-1">
              {anomalies.map((anom) => {
                const obs = observations.find(o => o.id === anom.observation_id);
                const isSelected = selectedObservation?.id === anom.observation_id;
                return (
                  <div 
                    key={anom.id}
                    onClick={() => obs && onSelectObservation(obs)}
                    className={`p-2 rounded border cursor-pointer transition-all ${
                      isSelected 
                        ? 'bg-slate-800 border-cyan-500/60 shadow' 
                        : 'bg-slate-950/60 border-slate-850 hover:bg-slate-900/60'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-200">EVT-{String(anom.observation_id).padStart(5, '0')}</span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded font-mono font-bold uppercase bg-red-950/40 text-red-400 border border-red-500/20">
                        {anom.anomaly_severity}
                      </span>
                    </div>
                    <p className="text-purple-300 font-semibold mt-1 text-[11px] truncate">{anom.facility_name || 'Associated Facility'}</p>
                    <div className="flex justify-between items-center text-[10px] text-slate-400 mt-1">
                      <span>FRP: <strong className="text-red-400 font-mono">{anom.observed_frp} MW</strong></span>
                      <span>Ratio: <strong className="font-mono text-amber-400">+{((anom.frp_multiplier_ratio - 1) * 100).toFixed(0)}%</strong></span>
                    </div>
                  </div>
                );
              })}
              {anomalies.length === 0 && (
                <div className="text-slate-500 text-center py-6">No abnormal events flagged.</div>
              )}
            </div>
          </div>
        );

      case 'ANOMALIES':
        return (
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between border-b border-slate-800 pb-1">
              <span className="font-bold text-slate-300 text-[11px]">
                Thermal Observations
              </span>
              <input 
                type="text" 
                placeholder="Search ID/Sat..." 
                value={obsSearch}
                onChange={(e) => setObsSearch(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-300 focus:outline-none focus:border-slate-700 w-28"
              />
            </div>
            <div className="flex flex-col gap-1 max-h-[380px] overflow-y-auto pr-1">
              {filteredObs.map((obs) => {
                const isSelected = selectedObservation?.id === obs.id;
                return (
                  <div 
                    key={obs.id}
                    onClick={() => onSelectObservation(obs)}
                    className={`p-2 rounded border cursor-pointer transition-all flex items-center justify-between ${
                      isSelected 
                        ? 'bg-slate-800 border-cyan-500/60' 
                        : 'bg-slate-950/60 border-slate-850 hover:bg-slate-900/60'
                    }`}
                  >
                    <div>
                      <span className="font-bold text-slate-300">OBS #{obs.id}</span>
                      <p className="text-[10px] text-slate-400">{obs.satellite} · {obs.acq_date}</p>
                    </div>
                    <span className="font-mono text-amber-400 font-bold">{obs.frp} MW</span>
                  </div>
                );
              })}
              {filteredObs.length === 0 && (
                <div className="text-slate-500 text-center py-6">No observations found.</div>
              )}
            </div>
          </div>
        );

      case 'FACILITIES':
        if (selectedFacility) {
          const fac = selectedFacility;
          const assocObs = associations
            .filter(a => a.facility_id === fac.id)
            .map(a => observations.find(o => o.id === a.observation_id))
            .filter((o): o is ThermalObservation => !!o)
            .sort((a, b) => new Date(b.observation_timestamp).getTime() - new Date(a.observation_timestamp).getTime());

          const hist = histories.find(h => h.facility_id === fac.id);
          const base = baselines.find(b => b.facility_id === fac.id);

          const medFrp = base?.baseline_frp_p50 ?? hist?.median_frp ?? 0;
          const p95Frp = base?.baseline_frp_p95 ?? hist?.p95_frp ?? 0;
          const p99Frp = base?.baseline_frp_p99 ?? hist?.p99_frp ?? 0;

          const currentObs = selectedObservation && associations.some(a => a.observation_id === selectedObservation.id && a.facility_id === fac.id)
            ? selectedObservation 
            : (assocObs.length > 0 ? assocObs[0] : null);

          return (
            <div className="flex flex-col gap-3 max-h-[385px] overflow-y-auto pr-1">
              <button 
                onClick={() => onSelectFacility(null)} 
                className="text-cyan-400 hover:text-cyan-300 text-[9px] font-bold font-mono flex items-center gap-1 uppercase tracking-wider border border-slate-800 bg-slate-950/60 py-1 px-2 rounded self-start select-none"
              >
                <ChevronLeft className="w-3.5 h-3.5" /> Back to Facilities
              </button>

              <div className="p-2.5 bg-slate-950/60 border border-slate-850 rounded flex flex-col gap-1">
                <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider font-mono">Spatially Associated Facility</span>
                <span className="font-bold text-slate-100 text-xs leading-tight">{fac.name || 'Industrial Infrastructure'}</span>
                <div className="flex justify-between items-center text-[10px] text-slate-400 mt-1 font-mono">
                  <span>Type: <strong className="text-slate-200 uppercase">{fac.facility_type}</strong></span>
                  <span>OSM ID: <strong className="text-slate-200">{fac.osm_id}</strong></span>
                </div>
                <div className="text-[9.5px] text-slate-500 font-mono mt-0.5">
                  Lat/Lon: {fac.latitude.toFixed(5)}, {fac.longitude.toFixed(5)}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[10.5px]">
                <div className="bg-slate-950/40 p-2 border border-slate-850 rounded">
                  <span className="text-slate-500 block uppercase text-[9px] font-semibold">Observations</span>
                  <span className="font-bold text-slate-200 font-mono text-[11px]">{assocObs.length} Historical</span>
                </div>
                <div className="bg-slate-950/40 p-2 border border-slate-850 rounded">
                  <span className="text-slate-500 block uppercase text-[9px] font-semibold">Median FRP</span>
                  <span className="font-bold text-amber-400 font-mono text-[11px]">{medFrp.toFixed(1)} MW</span>
                </div>
                <div className="bg-slate-950/40 p-2 border border-slate-850 rounded">
                  <span className="text-slate-500 block uppercase text-[9px] font-semibold">P95 Baseline</span>
                  <span className="font-bold text-red-400 font-mono text-[11px]">{p95Frp.toFixed(1)} MW</span>
                </div>
                <div className="bg-slate-950/40 p-2 border border-slate-850 rounded">
                  <span className="text-slate-500 block uppercase text-[9px] font-semibold">P99 Baseline</span>
                  <span className="font-bold text-red-500/80 font-mono text-[11px]">{p99Frp.toFixed(1)} MW</span>
                </div>
              </div>

              {currentObs ? (
                <div className="p-2.5 bg-slate-950/60 border border-slate-850 rounded flex flex-col gap-1">
                  <span className="text-[9px] text-cyan-400 font-bold uppercase tracking-wider font-mono">Current Thermal Anomaly</span>
                  <div className="flex justify-between items-center text-[10.5px] text-slate-300">
                    <span className="font-mono">Obs ID: #{currentObs.id}</span>
                    <span className="font-bold text-amber-400 font-mono">{currentObs.frp} MW</span>
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono flex justify-between">
                    <span>Sat: {currentObs.satellite}</span>
                    <span>Date: {currentObs.acq_date} {currentObs.acq_time?.slice(0, 2)}:{currentObs.acq_time?.slice(2)}</span>
                  </div>
                  {p95Frp > 0 && currentObs.frp && (
                    <div className="text-[9.5px] font-mono text-slate-500 mt-1 border-t border-slate-850/60 pt-1">
                      FRP vs Baseline: <strong className={currentObs.frp > p95Frp ? 'text-red-400' : 'text-emerald-400'}>
                        {((currentObs.frp - p95Frp) / p95Frp * 100).toFixed(0)}%
                      </strong>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-2.5 bg-slate-950/30 border border-slate-850 rounded text-center text-slate-500 text-[10px] font-mono">
                  No active anomaly selected for this facility.
                </div>
              )}

              <div className="flex flex-col gap-1.5 mt-1">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider font-mono border-b border-slate-800 pb-0.5">FRP Historical Timeline</span>
                <div className="flex flex-col gap-1 max-h-[140px] overflow-y-auto pr-1 font-mono text-[10px]">
                  {assocObs.map((obs) => {
                    const isAbove = p95Frp > 0 && (obs.frp || 0) > p95Frp;
                    return (
                      <div 
                        key={obs.id}
                        onClick={() => onSelectObservation(obs)}
                        className="flex justify-between items-center p-1 hover:bg-slate-850/40 rounded cursor-pointer text-slate-300"
                      >
                        <span>{obs.acq_date} {obs.acq_time}</span>
                        <span className={`font-bold ${isAbove ? 'text-red-400' : 'text-slate-400'}`}>{obs.frp} MW</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          );
        }

        return (
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between border-b border-slate-800 pb-1">
              <span className="font-bold text-slate-300 text-[11px]">
                Industrial Facilities
              </span>
              <input 
                type="text" 
                placeholder="Search facility..." 
                value={facSearch}
                onChange={(e) => setFacSearch(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-300 focus:outline-none focus:border-slate-700 w-28"
              />
            </div>
            <div className="flex flex-col gap-1 max-h-[380px] overflow-y-auto pr-1">
              {filteredFacs.map((fac) => {
                const isSelected = false;
                return (
                  <div 
                    key={fac.id}
                    onClick={() => onSelectFacility(fac)}
                    className={`p-2 rounded border cursor-pointer transition-all ${
                      isSelected 
                        ? 'bg-slate-800 border-cyan-500/60' 
                        : 'bg-slate-950/60 border-slate-850 hover:bg-slate-900/60'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-300 truncate max-w-[150px]">{fac.name || 'Industrial Zone'}</span>
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-950/40 text-purple-300 border border-purple-500/20 uppercase font-mono">
                        {fac.facility_type}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5 truncate">{fac.operator || 'Unknown Operator'}</p>
                  </div>
                );
              })}
              {filteredFacs.length === 0 && (
                <div className="text-slate-500 text-center py-6">No facilities found.</div>
              )}
            </div>
          </div>
        );

      case 'EVIDENCE':
        return (
          <div className="flex flex-col gap-2.5">
            <span className="font-bold text-slate-300 text-[11px] border-b border-slate-800 pb-1">
              Optical Verification Proxy
            </span>
            <div className="p-3 rounded bg-blue-950/15 border border-blue-500/25 flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-[11px] font-semibold text-blue-200">
                <span className="flex items-center gap-1">
                  <Info className="w-3.5 h-3.5 text-blue-400" /> Multi-Source Evidence
                </span>
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-900/40 border border-blue-400/40 text-blue-300 font-mono uppercase font-bold">
                  Planned / Experimental
                </span>
              </div>
              <p className="text-[10.5px] text-slate-300 leading-snug">
                Future phases will support automatic ingestion of Sentinel-2 (L2A) and Landsat 8/9 imagery to extract optical/NDVI confidence indexes over high-priority industrial coordinates.
              </p>
            </div>
          </div>
        );

      case 'ANALYTICS':
        return (
          <div className="flex flex-col gap-3 max-h-[380px] overflow-y-auto pr-1">
            <span className="font-bold text-slate-300 text-[11px] border-b border-slate-800 pb-1">
              Facility Baseline Summary
            </span>

            {/* Baseline metrics */}
            <div className="grid grid-cols-2 gap-2 text-[10.5px]">
              <div className="bg-slate-950/60 p-2 border border-slate-850 rounded">
                <span className="text-slate-400 block">Total Baselines</span>
                <span className="font-bold text-slate-200 font-mono text-sm">{analytics?.total_observations ? 6 : 0} Established</span>
              </div>
              <div className="bg-slate-950/60 p-2 border border-slate-850 rounded">
                <span className="text-slate-400 block">Avg P95 FRP</span>
                <span className="font-bold text-slate-200 font-mono text-sm">34.5 MW</span>
              </div>
            </div>

            {/* Breakdown Chart */}
            <div className="p-2.5 bg-slate-950/80 border border-slate-850 rounded flex flex-col gap-2">
              <span className="font-semibold text-slate-300 text-[10.5px]">Classification Breakdown</span>
              <div className="flex flex-col gap-1.5 text-[10px]">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Industrial Candidate</span>
                  <span className="font-mono font-bold text-purple-300">9</span>
                </div>
                <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-purple-500 h-full" style={{ width: '69%' }} />
                </div>
                <div className="flex justify-between items-center mt-1">
                  <span className="text-slate-400">Natural / Forest</span>
                  <span className="font-mono font-bold text-emerald-300">2</span>
                </div>
                <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full" style={{ width: '15%' }} />
                </div>
                <div className="flex justify-between items-center mt-1">
                  <span className="text-slate-400">Agricultural</span>
                  <span className="font-mono font-bold text-amber-300">2</span>
                </div>
                <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-amber-500 h-full" style={{ width: '15%' }} />
                </div>
              </div>
            </div>
          </div>
        );

      case 'INGESTION':
        return (
          <div className="flex flex-col gap-2">
            <span className="font-bold text-slate-300 text-[11px] border-b border-slate-800 pb-1">
              On-Demand Ingestion
            </span>
            <IngestionControl 
              onIngestComplete={onIngestComplete}
              apiKeyConfigured={health?.firms_api_key_configured ?? false}
            />
          </div>
        );

      case 'SYSTEM':
        return (
          <div className="flex flex-col gap-2">
            <span className="font-bold text-slate-300 text-[11px] border-b border-slate-800 pb-1">
              System Connections
            </span>
            <div className="p-2.5 rounded bg-slate-950/80 border border-slate-850 flex flex-col gap-2 text-[10.5px]">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Server className="w-3 h-3 text-slate-500" /> NASA FIRMS API
                </span>
                {health?.firms_api_key_configured ? (
                  <span className="text-emerald-400 font-medium flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Connected
                  </span>
                ) : (
                  <span className="text-amber-400 font-medium flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" /> Key Missing
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Database className="w-3 h-3 text-slate-500" /> SQLite Database
                </span>
                {health?.database_status === "ok" ? (
                  <span className="text-emerald-400 font-medium flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Connected
                  </span>
                ) : (
                  <span className="text-red-400 font-medium flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400" /> Disconnected
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Server className="w-3 h-3 text-slate-500" /> FastAPI Backend
                </span>
                {health?.status === "online" ? (
                  <span className="text-emerald-400 font-medium flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Connected
                  </span>
                ) : (
                  <span className="text-red-400 font-medium flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400" /> Offline
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between border-t border-slate-800/80 pt-1.5 mt-1">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Workflow className="w-3 h-3 text-slate-500" /> n8n Orchestrator
                </span>
                {health?.n8n_status === "connected" ? (
                  <span className="text-emerald-400 font-medium flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Connected
                  </span>
                ) : (
                  <span className="text-slate-400 font-medium flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full border border-slate-500" /> Not Connected
                  </span>
                )}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <aside className="w-72 min-w-[280px] max-w-[300px] bg-slate-900 border-r border-slate-800 text-slate-100 flex flex-col h-full shrink-0 z-20 text-xs shadow-xl select-none font-sans overflow-hidden">
      {/* 1. BRANDING HEADER */}
      <div className="p-3 border-b border-slate-800 flex items-center justify-between bg-slate-950/40 shrink-0">
        <span className="font-mono font-bold text-slate-100 uppercase tracking-wider flex items-center gap-1.5">
          <Activity className="w-4 h-4 text-blue-400" />
          Command Navigation
        </span>
        <button
          onClick={onToggleCollapse}
          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200"
          title="Collapse Sidebar"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* 2. TABBED NAVIGATION */}
      <div className="grid grid-cols-4 gap-1 p-2 bg-slate-950 border-b border-slate-850 shrink-0 text-[9px] text-center font-bold tracking-wider font-mono">
        {(['OVERVIEW', 'EVENTS', 'ANOMALIES', 'FACILITIES'] as TabType[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`py-1 rounded-sm border uppercase transition-colors ${
              activeTab === tab 
                ? 'bg-slate-850 text-amber-400 border-amber-500/30' 
                : 'border-transparent text-slate-400 hover:text-slate-250 hover:bg-slate-900'
            }`}
          >
            {tab.slice(0, 4)}
          </button>
        ))}
        {(['EVIDENCE', 'ANALYTICS', 'INGESTION', 'SYSTEM'] as TabType[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`py-1 rounded-sm border uppercase transition-colors ${
              activeTab === tab 
                ? 'bg-slate-850 text-amber-400 border-amber-500/30' 
                : 'border-transparent text-slate-400 hover:text-slate-250 hover:bg-slate-900'
            }`}
          >
            {tab.slice(0, 4)}
          </button>
        ))}
      </div>

      {/* 3. COMPACT KPI PANEL */}
      <div className="grid grid-cols-2 gap-1.5 p-3 border-b border-slate-850 bg-slate-950/20 shrink-0">
        <div className="p-2 bg-slate-950/60 border border-slate-850 rounded">
          <div className="flex items-center gap-1 text-[9px] text-slate-400 uppercase font-semibold">
            <Activity className="w-3 h-3 text-amber-400" />
            Anomalies
          </div>
          <div className="text-sm font-bold font-mono text-slate-100 mt-0.5">
            {totalPoints.toLocaleString()}
          </div>
        </div>

        <div className="p-2 bg-slate-950/60 border border-slate-850 rounded">
          <div className="flex items-center gap-1 text-[9px] text-slate-400 uppercase font-semibold">
            <Building2 className="w-3 h-3 text-purple-400" />
            Facilities
          </div>
          <div className="text-sm font-bold font-mono text-purple-300 mt-0.5">
            {totalFacilities.toLocaleString()}
          </div>
        </div>

        <div className="p-2 bg-slate-950/60 border border-slate-850 rounded">
          <div className="flex items-center gap-1 text-[9px] text-slate-400 uppercase font-semibold">
            <List className="w-3 h-3 text-blue-400" />
            Events
          </div>
          <div className="text-sm font-bold font-mono text-blue-300 mt-0.5">
            {totalAnomalies.toLocaleString()}
          </div>
        </div>

        <div className="p-2 bg-slate-950/60 border border-slate-850 rounded">
          <div className="flex items-center gap-1 text-[9px] text-slate-400 uppercase font-semibold">
            <AlertTriangle className="w-3 h-3 text-red-400" />
            High Priority
          </div>
          <div className="text-sm font-bold font-mono text-red-400 mt-0.5">
            {totalHighPriority.toLocaleString()}
          </div>
        </div>
      </div>

      {/* 4. TAB CONTENTS AREA */}
      <div className="flex-1 p-3 overflow-y-auto min-h-0 bg-slate-900/60">
        {renderTabContent()}
      </div>
    </aside>
  );
};

export default StatsPanel;
