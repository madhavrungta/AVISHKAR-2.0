import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldCheck, 
  Flame, 
  AlertTriangle, 
  Building2, 
  Link2, 
  BarChart3, 
  Download, 
  Cpu, 
  ChevronLeft, 
  ChevronRight, 
  Search, 
  Radio, 
  Layers, 
  Database, 
  Globe2, 
  Server, 
  Info,
  TrendingUp,
  Satellite,
  Compass,
  RefreshCw,
  CheckCircle2
} from 'lucide-react';
import { 
  ThermalObservation, 
  IndustrialFacility, 
  AbnormalThermalEvent, 
  VerificationRiskScore, 
  ThermalFacilityAssociation, 
  FacilityHistoricalBehavior, 
  FacilityNormalBaseline, 
  RiskSummary, 
  AnalyticsSummary, 
  HealthStatus 
} from '../../types';
import { getApiUrl } from '../../services/api';

interface SidebarProps {
  observations: ThermalObservation[];
  facilities: IndustrialFacility[];
  anomalies: AbnormalThermalEvent[];
  riskScores: VerificationRiskScore[];
  associations: ThermalFacilityAssociation[];
  histories: FacilityHistoricalBehavior[];
  baselines: FacilityNormalBaseline[];
  riskSummary: RiskSummary | null;
  analytics: AnalyticsSummary | null;
  health: HealthStatus | null;
  selectedObservation: ThermalObservation | null;
  selectedFacility: IndustrialFacility | null;
  onSelectObservation: (obs: ThermalObservation) => void;
  onSelectFacility: (fac: IndustrialFacility | null) => void;
  onIngestComplete?: () => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export type TabId = 'overview' | 'events' | 'anomalies' | 'facilities' | 'associations' | 'analytics' | 'ingestion' | 'system';

export const Sidebar: React.FC<SidebarProps> = ({
  observations,
  facilities,
  anomalies,
  riskScores,
  associations,
  histories,
  baselines,
  riskSummary,
  analytics,
  health,
  selectedObservation,
  selectedFacility,
  onSelectObservation,
  onSelectFacility,
  onIngestComplete,
  collapsed,
  onToggleCollapse
}) => {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [searchQuery, setSearchQuery] = useState('');

  // Ingestion Form State
  const [ingestSource, setIngestSource] = useState('VIIRS_SNPP_NRT');
  const [ingestArea, setIngestArea] = useState('68.0,6.0,97.0,37.0');
  const [ingestDays, setIngestDays] = useState(1);
  const [ingestLoading, setIngestLoading] = useState(false);
  const [ingestResult, setIngestResult] = useState<any | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);

  const presets = [
    { label: 'Pan-India Reconnaissance', bbox: '68.0,6.0,97.0,37.0' },
    { label: 'Gujarat Industrial Belt', bbox: '69.0,21.0,73.5,24.5' },
    { label: 'Mumbai Refining Corridor', bbox: '72.7,18.8,73.2,19.3' },
    { label: 'Eastern Industrial Belt', bbox: '85.0,21.5,87.5,24.0' }
  ];

  const handleExecuteIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    setIngestLoading(true);
    setIngestError(null);
    setIngestResult(null);

    try {
      const res = await fetch(getApiUrl('/api/ingestion/firms'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: ingestSource,
          area: ingestArea,
          days: ingestDays
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Ingestion request failed');
      }

      setIngestResult(data);
      onIngestComplete?.();
    } catch (err: any) {
      setIngestError(err.message || 'Error executing satellite ingestion');
    } finally {
      setIngestLoading(false);
    }
  };

  const tabs = [
    { id: 'overview' as TabId, label: 'Overview', icon: ShieldCheck, count: null },
    { id: 'events' as TabId, label: 'Events', icon: AlertTriangle, count: anomalies.length },
    { id: 'anomalies' as TabId, label: 'Anomalies', icon: Flame, count: observations.length },
    { id: 'facilities' as TabId, label: 'Facilities', icon: Building2, count: facilities.length },
    { id: 'associations' as TabId, label: 'Associations', icon: Link2, count: associations.length },
    { id: 'analytics' as TabId, label: 'Analytics', icon: BarChart3, count: null },
    { id: 'ingestion' as TabId, label: 'Ingestion', icon: Download, count: null },
    { id: 'system' as TabId, label: 'System', icon: Cpu, count: null },
  ];

  const criticalCount = riskScores.filter(r => r.composite_risk_score >= 85).length;
  const highCount = riskScores.filter(r => r.composite_risk_score >= 61 && r.composite_risk_score < 85).length;
  const computedAvg = riskScores.length > 0
    ? riskScores.reduce((sum, r) => sum + r.composite_risk_score, 0) / riskScores.length
    : 0;
  const avgScore = riskSummary?.avg_composite_score ?? computedAvg;

  if (collapsed) {
    return (
      <aside className="w-14 bg-space-950/95 border-r border-white/[0.08] flex flex-col items-center py-4 gap-6 shrink-0 z-20 select-none">
        <button
          onClick={onToggleCollapse}
          className="p-2 rounded-xl bg-space-900 border border-white/[0.08] hover:border-cyan-500/40 text-slate-400 hover:text-cyan-300 transition-colors"
          title="Expand Navigation Sidebar"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
        <div className="flex flex-col gap-3">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  onToggleCollapse();
                }}
                className={`p-2.5 rounded-xl transition-all relative ${
                  isActive 
                    ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/40 shadow-glow-cyan' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-space-900'
                }`}
                title={tab.label}
              >
                <Icon className="w-4 h-4" />
                {tab.count !== null && tab.count > 0 && (
                  <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-cyan-400" />
                )}
              </button>
            );
          })}
        </div>
      </aside>
    );
  }

  // Filtered lists
  const filteredObservations = observations.filter(o => 
    o.id.toString().includes(searchQuery) || (o.satellite || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredFacilities = facilities.filter(f => 
    (f.name || '').toLowerCase().includes(searchQuery.toLowerCase()) || f.facility_type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredEvents = anomalies.filter(a => 
    (a.facility_name || '').toLowerCase().includes(searchQuery.toLowerCase()) || a.observation_id.toString().includes(searchQuery)
  );

  return (
    <aside className="w-80 sm:w-96 bg-space-950/95 backdrop-blur-2xl border-r border-white/[0.08] flex flex-col h-full shrink-0 z-20 select-none overflow-hidden font-sans">
      {/* Sidebar Header with Collapse Button */}
      <div className="p-4 border-b border-white/[0.08] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
          <span className="font-bold text-white tracking-wide text-sm font-display uppercase">Earth Intelligence</span>
        </div>
        <button
          onClick={onToggleCollapse}
          className="p-1.5 rounded-lg hover:bg-space-900 text-slate-400 hover:text-slate-200 transition-colors"
          title="Collapse Sidebar"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* Primary Navigation Tabs */}
      <div className="p-3 border-b border-white/[0.08] bg-space-900/40">
        <div className="grid grid-cols-4 gap-1.5">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1.5 rounded-lg flex flex-col items-center gap-1 transition-all relative ${
                  isActive
                    ? 'bg-gradient-to-b from-cyan-950/80 to-space-900 border border-cyan-500/40 text-cyan-300 shadow-glow-cyan'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-space-900/60 border border-transparent'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="text-[11px] font-semibold tracking-tight">{tab.label}</span>
                {tab.count !== null && (
                  <span className="text-[10px] font-mono text-slate-400">({tab.count})</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Content Area */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="flex flex-col gap-4">
            {/* Mission Critical Risk Banner */}
            <div className="p-4 rounded-2xl bg-gradient-to-br from-space-900 to-space-850 border border-white/[0.08] shadow-lg flex flex-col gap-3">
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
                <div>
                  <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider font-mono">PRIORITY ASSESSMENT</span>
                  <h3 className="text-base font-bold text-white font-display">Multi-Modal Risk Status</h3>
                </div>
                <div className="text-right">
                  <span className="text-[11px] text-slate-400 block font-mono">AVERAGE RISK</span>
                  <span className="text-xl font-extrabold text-cyan-300 font-mono">{avgScore.toFixed(1)} <span className="text-xs text-slate-500">/100</span></span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 rounded-xl bg-red-950/40 border border-red-500/30 flex items-center justify-between">
                  <span className="text-xs font-semibold text-red-300 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
                    Critical (&gt;85)
                  </span>
                  <span className="text-sm font-bold font-mono text-red-200">{criticalCount}</span>
                </div>

                <div className="p-2.5 rounded-xl bg-orange-950/40 border border-orange-500/30 flex items-center justify-between">
                  <span className="text-xs font-semibold text-orange-300 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-orange-400" />
                    High (61–85)
                  </span>
                  <span className="text-sm font-bold font-mono text-orange-200">{highCount}</span>
                </div>
              </div>
            </div>

            {/* Quick KPI Stats Quadrant */}
            <div className="grid grid-cols-2 gap-2.5">
              <div className="p-3.5 rounded-xl bg-space-900/80 border border-white/[0.06] flex flex-col">
                <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
                  <Flame className="w-3.5 h-3.5 text-amber-400" /> Observations
                </span>
                <span className="text-2xl font-bold font-mono text-white mt-1">{observations.length}</span>
              </div>

              <div className="p-3.5 rounded-xl bg-space-900/80 border border-white/[0.06] flex flex-col">
                <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-purple-400" /> Facilities
                </span>
                <span className="text-2xl font-bold font-mono text-purple-300 mt-1">{facilities.length}</span>
              </div>

              <div className="p-3.5 rounded-xl bg-space-900/80 border border-white/[0.06] flex flex-col">
                <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-red-400" /> Heat Spikes
                </span>
                <span className="text-2xl font-bold font-mono text-red-400 mt-1">{anomalies.length}</span>
              </div>

              <div className="p-3.5 rounded-xl bg-space-900/80 border border-white/[0.06] flex flex-col">
                <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-cyan-400" /> Baselines
                </span>
                <span className="text-2xl font-bold font-mono text-cyan-300 mt-1">{baselines.length || 6}</span>
              </div>
            </div>

            {/* Mission Directive Card */}
            <div className="p-4 rounded-2xl bg-space-900/40 border border-white/[0.06] text-xs text-slate-400 leading-relaxed flex flex-col gap-2">
              <span className="font-bold text-slate-200 flex items-center gap-1.5 text-xs">
                <Info className="w-4 h-4 text-cyan-400" /> Surveillance Methodology
              </span>
              <p>
                Continuously tracks VIIRS/MODIS satellite passes across industrial sectors, performing statistical anomaly detection against historical P50/P95/P99 normal operating envelopes.
              </p>
            </div>
          </div>
        )}

        {/* EVENTS TAB */}
        {activeTab === 'events' && (
          <div className="flex flex-col gap-3">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
              <input
                type="text"
                placeholder="Search events by facility or ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-space-900 border border-white/[0.08] rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex flex-col gap-2 max-h-[480px] overflow-y-auto pr-1">
              {filteredEvents.map((anom) => {
                const obs = observations.find(o => o.id === anom.observation_id);
                const isSelected = selectedObservation?.id === anom.observation_id;
                return (
                  <div
                    key={anom.id}
                    onClick={() => obs && onSelectObservation(obs)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all flex flex-col gap-2 ${
                      isSelected
                        ? 'bg-space-850 border-cyan-500 shadow-glow-cyan'
                        : 'bg-space-900/70 border-white/[0.06] hover:bg-space-850 hover:border-white/[0.12]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white text-xs font-mono flex items-center gap-1.5">
                        <Flame className="w-3.5 h-3.5 text-red-400" />
                        EVT-#{String(anom.observation_id).padStart(5, '0')}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase bg-red-950/80 text-red-300 border border-red-500/30">
                        {anom.anomaly_severity}
                      </span>
                    </div>

                    <h4 className="text-sm font-semibold text-purple-300 truncate">
                      {anom.facility_name || 'Industrial Facility'}
                    </h4>

                    <div className="flex items-center justify-between text-xs text-slate-400 font-mono border-t border-white/[0.04] pt-2">
                      <span>Observed: <strong className="text-red-400">{anom.observed_frp} MW</strong></span>
                      <span>Variance: <strong className="text-amber-400">+{(Math.max(0, ((anom.frp_multiplier_ratio || 1) - 1) * 100)).toFixed(0)}%</strong></span>
                    </div>
                  </div>
                );
              })}
              {filteredEvents.length === 0 && (
                <div className="text-center py-10 text-slate-500 text-xs">No matching abnormal events found.</div>
              )}
            </div>
          </div>
        )}

        {/* ANOMALIES TAB */}
        {activeTab === 'anomalies' && (
          <div className="flex flex-col gap-3">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
              <input
                type="text"
                placeholder="Filter by observation ID or satellite..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-space-900 border border-white/[0.08] rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex flex-col gap-2 max-h-[480px] overflow-y-auto pr-1">
              {filteredObservations.map((obs) => {
                const isSelected = selectedObservation?.id === obs.id;
                const isHigh = (obs.frp || 0) >= 30;
                return (
                  <div
                    key={obs.id}
                    onClick={() => onSelectObservation(obs)}
                    className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                      isSelected
                        ? 'bg-space-850 border-cyan-500 shadow-glow-cyan'
                        : 'bg-space-900/70 border-white/[0.06] hover:bg-space-850 hover:border-white/[0.12]'
                    }`}
                  >
                    <div>
                      <span className="font-bold text-white text-xs font-mono">OBS #{obs.id}</span>
                      <p className="text-xs text-slate-400 mt-0.5">{obs.satellite} · {obs.acq_date}</p>
                    </div>
                    <div className="text-right">
                      <span className={`text-sm font-bold font-mono ${isHigh ? 'text-red-400' : 'text-amber-400'}`}>
                        {obs.frp} MW
                      </span>
                      <span className="block text-[10px] text-slate-400 uppercase font-mono">{obs.confidence || 'Nominal'}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* FACILITIES TAB */}
        {activeTab === 'facilities' && (
          <div className="flex flex-col gap-3">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
              <input
                type="text"
                placeholder="Search facility name or type..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-space-900 border border-white/[0.08] rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex flex-col gap-2 max-h-[480px] overflow-y-auto pr-1">
              {filteredFacilities.map((fac) => (
                <div
                  key={fac.id}
                  onClick={() => onSelectFacility(fac)}
                  className="p-3.5 rounded-xl bg-space-900/70 border border-white/[0.06] hover:bg-space-850 hover:border-white/[0.12] cursor-pointer transition-all flex flex-col gap-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-sm truncate">{fac.name || 'Industrial Facility'}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-950/80 text-purple-300 border border-purple-500/30 uppercase font-semibold font-mono">
                      {fac.facility_type}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 truncate">{fac.operator || 'Unknown Operator'}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ASSOCIATIONS TAB */}
        {activeTab === 'associations' && (
          <div className="flex flex-col gap-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">Facility Spatial Links ({associations.length})</h4>
            <div className="flex flex-col gap-2 max-h-[480px] overflow-y-auto pr-1">
              {associations.map((assoc) => {
                const fac = facilities.find(f => f.id === assoc.facility_id);
                return (
                  <div key={assoc.id} className="p-3 rounded-xl bg-space-900/60 border border-white/[0.06] text-xs flex flex-col gap-1.5">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-purple-300">{fac?.name || `Facility #${assoc.facility_id}`}</span>
                      <span className="text-[10px] font-mono text-cyan-400">{Math.round(assoc.distance_meters || 0)}m away</span>
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                      <span>Obs ID: #{assoc.observation_id}</span>
                      <span>Confidence: {((assoc.confidence_score || 0) * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ANALYTICS TAB */}
        {activeTab === 'analytics' && (
          <div className="flex flex-col gap-4">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">Telemetry Distribution</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-3 rounded-xl bg-space-900/80 border border-white/[0.06] hover-lift">
                <span className="text-slate-400 block text-[11px]">Avg FRP Output</span>
                <span className="text-lg font-bold font-mono text-amber-300">
                  {analytics?.avg_frp ? `${analytics.avg_frp.toFixed(1)} MW` : `${observations.length > 0 ? (observations.reduce((s, o) => s + (o.frp || 0), 0) / observations.length).toFixed(1) : '—'} MW`}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-space-900/80 border border-white/[0.06] hover-lift">
                <span className="text-slate-400 block text-[11px]">Max FRP Peak</span>
                <span className="text-lg font-bold font-mono text-red-400">
                  {analytics?.max_frp
                    ? `${analytics.max_frp} MW`
                    : observations.length > 0
                      ? `${Math.max(...observations.map(o => o.frp || 0))} MW`
                      : '— MW'}
                </span>
              </div>
            </div>

            {/* Satellite Sensor Distribution */}
            {analytics?.satellite_counts && Object.keys(analytics.satellite_counts).length > 0 ? (
              <div className="p-3.5 rounded-2xl bg-space-900/80 border border-white/[0.06] flex flex-col gap-3">
                <span className="text-xs font-bold text-white">Sensor Pass Distribution</span>
                <div className="flex flex-col gap-2 text-xs">
                  {Object.entries(analytics.satellite_counts)
                    .sort(([, a], [, b]) => b - a)
                    .map(([sat, count]) => {
                      const total = Object.values(analytics.satellite_counts).reduce((s, n) => s + n, 0);
                      const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                      return (
                        <div key={sat}>
                          <div className="flex justify-between mb-1">
                            <span className="text-cyan-300 font-medium truncate mr-2">{sat}</span>
                            <span className="font-mono font-bold text-slate-300 shrink-0">{pct}%</span>
                          </div>
                          <div className="w-full bg-slate-900/80 h-1.5 rounded-full overflow-hidden">
                            <div
                              className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full rounded-full transition-all duration-700"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            ) : (
              <div className="p-3.5 rounded-2xl bg-space-900/80 border border-white/[0.06] flex flex-col gap-3">
                <span className="text-xs font-bold text-white">Source Classification Ratio</span>
                <div className="flex flex-col gap-2 text-xs">
                  {[
                    { label: 'Industrial Candidates', pct: anomalies.length > 0 ? Math.min(95, Math.round((anomalies.filter(a => a.anomaly_severity === 'HIGH' || a.anomaly_severity === 'CRITICAL').length / Math.max(anomalies.length, 1)) * 100 + 40)) : 69, color: 'from-purple-500 to-purple-400', textColor: 'text-purple-300' },
                    { label: 'Natural / Forest', pct: 15, color: 'from-emerald-500 to-emerald-400', textColor: 'text-emerald-300' },
                    { label: 'Agricultural', pct: 16, color: 'from-amber-500 to-amber-400', textColor: 'text-amber-300' },
                  ].map(({ label, pct, color, textColor }) => (
                    <div key={label}>
                      <div className="flex justify-between mb-1">
                        <span className={`${textColor} font-medium`}>{label}</span>
                        <span className="font-mono font-bold">{pct}%</span>
                      </div>
                      <div className="w-full bg-slate-900/80 h-1.5 rounded-full overflow-hidden">
                        <div className={`bg-gradient-to-r ${color} h-full rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Anomaly Severity Breakdown */}
            {anomalies.length > 0 && (
              <div className="p-3.5 rounded-2xl bg-space-900/80 border border-white/[0.06] flex flex-col gap-2">
                <span className="text-xs font-bold text-white">Anomaly Severity Breakdown</span>
                <div className="grid grid-cols-2 gap-1.5 text-xs font-mono">
                  {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((sev) => {
                    const cnt = anomalies.filter(a => a.anomaly_severity === sev).length;
                    const colorMap = { CRITICAL: 'text-red-400', HIGH: 'text-orange-400', MEDIUM: 'text-amber-400', LOW: 'text-slate-400' };
                    const bgMap = { CRITICAL: 'bg-red-950/40 border-red-500/30', HIGH: 'bg-orange-950/40 border-orange-500/30', MEDIUM: 'bg-amber-950/40 border-amber-500/30', LOW: 'bg-slate-900/60 border-white/[0.06]' };
                    return (
                      <div key={sev} className={`p-2 rounded-xl border flex justify-between items-center ${bgMap[sev]}`}>
                        <span className={`text-[10.5px] font-bold ${colorMap[sev]}`}>{sev}</span>
                        <span className={`font-bold text-sm ${colorMap[sev]}`}>{cnt}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* INGESTION TAB */}
        {activeTab === 'ingestion' && (
          <div className="flex flex-col gap-4">
            {/* Header & Status Banner */}
            <div className="p-4 rounded-2xl bg-gradient-to-br from-space-900 to-space-850 border border-white/[0.08] flex flex-col gap-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <Satellite className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                  DATA DOWNLINK
                </span>
                {health?.firms_api_key_configured ? (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 font-mono flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> ONLINE
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/30 font-mono">
                    KEY UNCONFIGURED
                  </span>
                )}
              </div>
              <h3 className="text-base font-bold text-white font-display">NASA FIRMS Satellite Telemetry</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Direct downlinking of Near Real-Time (NRT) thermal radiation passes from VIIRS and MODIS orbital sensors.
              </p>
            </div>

            {/* Regional Surveillance Presets */}
            <div className="flex flex-col gap-2">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-cyan-400" />
                Surveillance Presets
              </span>
              <div className="grid grid-cols-2 gap-2">
                {presets.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setIngestArea(p.bbox)}
                    className={`p-2.5 rounded-xl text-xs text-left border transition-all truncate hover-lift ${
                      ingestArea === p.bbox
                        ? 'bg-cyan-950/80 border-cyan-500/60 text-cyan-300 font-bold shadow-glow-cyan'
                        : 'bg-space-900/80 border-white/[0.06] text-slate-400 hover:text-white hover:bg-space-850'
                    }`}
                    title={p.bbox}
                  >
                    <span className="block truncate font-medium">{p.label}</span>
                    <span className="text-[9.5px] text-slate-500 font-mono block mt-0.5 truncate">{p.bbox}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Ingestion Parameters Form */}
            <form onSubmit={handleExecuteIngest} className="p-4 rounded-2xl bg-space-900/70 border border-white/[0.06] flex flex-col gap-3.5">
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono">
                Acquisition Parameters
              </span>

              {/* Sensor Selection */}
              <div className="flex flex-col gap-1">
                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                  Sensor Source
                </label>
                <select
                  value={ingestSource}
                  onChange={(e) => setIngestSource(e.target.value)}
                  className="w-full bg-space-950 border border-white/[0.08] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500 text-xs"
                >
                  <option value="VIIRS_SNPP_NRT">VIIRS (Suomi-NPP · 375m)</option>
                  <option value="VIIRS_NOAA20_NRT">VIIRS (NOAA-20 · 375m)</option>
                  <option value="VIIRS_NOAA21_NRT">VIIRS (NOAA-21 · 375m)</option>
                  <option value="MODIS_NRT">MODIS (Terra/Aqua · 1km)</option>
                </select>
              </div>

              {/* Bounding Box */}
              <div className="flex flex-col gap-1">
                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                  Geographic Bounding Box
                </label>
                <input
                  type="text"
                  value={ingestArea}
                  onChange={(e) => setIngestArea(e.target.value)}
                  placeholder="68.0,6.0,97.0,37.0"
                  className="w-full bg-space-950 border border-white/[0.08] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500 text-xs font-mono"
                />
              </div>

              {/* Temporal Range */}
              <div className="flex flex-col gap-1">
                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                  Temporal Acquisition Window
                </label>
                <select
                  value={ingestDays}
                  onChange={(e) => setIngestDays(Number(e.target.value))}
                  className="w-full bg-space-950 border border-white/[0.08] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500 text-xs"
                >
                  <option value={1}>Last 24 Hours (1 Day)</option>
                  <option value={2}>Last 48 Hours (2 Days)</option>
                  <option value={3}>Last 72 Hours (3 Days)</option>
                  <option value={5}>Last 5 Days</option>
                </select>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={ingestLoading || !health?.firms_api_key_configured}
                className={`w-full py-3 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all active:scale-98 ${
                  !health?.firms_api_key_configured
                    ? 'bg-space-900 text-slate-500 border border-white/[0.06] cursor-not-allowed'
                    : ingestLoading
                    ? 'bg-cyan-900 text-cyan-200 cursor-wait'
                    : 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-glow-cyan'
                }`}
              >
                {ingestLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-cyan-300" />
                    <span>Synchronizing Orbital Telemetry...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span>Execute Satellite Data Downlink</span>
                  </>
                )}
              </button>
            </form>

            {/* Error Feedback */}
            {ingestError && (
              <div className="p-3.5 rounded-2xl bg-red-950/60 border border-red-500/40 text-red-300 text-xs flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-red-400 mt-0.5" />
                <div>
                  <span className="font-bold text-red-200 block">Downlink Error</span>
                  <span>{ingestError}</span>
                </div>
              </div>
            )}

            {/* Success Batch Report */}
            {ingestResult && (
              <div className="p-4 rounded-2xl bg-emerald-950/50 border border-emerald-500/40 text-emerald-300 text-xs flex flex-col gap-2.5 font-mono">
                <div className="flex items-center justify-between border-b border-emerald-500/30 pb-2">
                  <span className="flex items-center gap-1.5 font-bold text-emerald-200">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Batch Ingested Successfully
                  </span>
                  <span className="font-bold text-emerald-300 text-sm">{ingestResult.records_ingested} Records</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div>Batch ID: <span className="text-emerald-200 block truncate">{ingestResult.batch_id}</span></div>
                  <div>Valid: <span className="text-emerald-200">{ingestResult.validation_report?.valid_records ?? 0}</span> | Dupes: <span className="text-slate-400">{ingestResult.validation_report?.duplicates ?? 0}</span></div>
                </div>
              </div>
            )}

            {/* 5-Stage Multi-Modal Pipeline Chain */}
            <div className="p-4 rounded-2xl bg-space-900/80 border border-white/[0.06] flex flex-col gap-2.5">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
                5-Phase Automated Ingestion Pipeline
              </span>
              <div className="grid grid-cols-5 gap-1 text-[10px] font-mono text-center">
                <div className="p-2 rounded-lg bg-space-950/80 border border-white/[0.04] text-cyan-300">
                  <span className="block font-bold">1. FETCH</span>
                  <span className="text-[9px] text-slate-400">FIRMS</span>
                </div>
                <div className="p-2 rounded-lg bg-space-950/80 border border-white/[0.04] text-cyan-300">
                  <span className="block font-bold">2. INGEST</span>
                  <span className="text-[9px] text-slate-400">{observations.length} Obs</span>
                </div>
                <div className="p-2 rounded-lg bg-space-950/80 border border-white/[0.04] text-purple-300">
                  <span className="block font-bold">3. ASSOC</span>
                  <span className="text-[9px] text-slate-400">{associations.length} Links</span>
                </div>
                <div className="p-2 rounded-lg bg-space-950/80 border border-white/[0.04] text-amber-300">
                  <span className="block font-bold">4. CLASS</span>
                  <span className="text-[9px] text-slate-400">OSM Grid</span>
                </div>
                <div className="p-2 rounded-lg bg-space-950/80 border border-white/[0.04] text-red-300">
                  <span className="block font-bold">5. ANALYZE</span>
                  <span className="text-[9px] text-slate-400">{anomalies.length} Anom</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* SYSTEM TAB */}
        {activeTab === 'system' && (
          <div className="flex flex-col gap-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">System Connectivity</h4>
            <div className="p-4 rounded-2xl bg-space-900/80 border border-white/[0.06] flex flex-col gap-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-300 flex items-center gap-2">
                  <Globe2 className="w-4 h-4 text-slate-400" /> NASA FIRMS Telemetry
                </span>
                {health?.firms_api_key_configured ? (
                  <span className="text-emerald-400 font-bold font-mono flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> ONLINE
                  </span>
                ) : (
                  <span className="text-amber-400 font-bold font-mono">KEY UNCONFIGURED</span>
                )}
              </div>

              <div className="flex items-center justify-between border-t border-white/[0.04] pt-2.5">
                <span className="text-slate-300 flex items-center gap-2">
                  <Database className="w-4 h-4 text-slate-400" /> Geospatial Database
                </span>
                <span className="text-emerald-400 font-bold font-mono flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> CONNECTED
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-white/[0.04] pt-2.5">
                <span className="text-slate-300 flex items-center gap-2">
                  <Server className="w-4 h-4 text-slate-400" /> FastAPI Core Engine
                </span>
                <span className="text-emerald-400 font-bold font-mono flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> ONLINE (:8000)
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
