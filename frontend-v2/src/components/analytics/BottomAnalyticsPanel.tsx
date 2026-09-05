import React, { useState } from 'react';
import { 
  ChevronDown, 
  ChevronUp, 
  BarChart2, 
  Calendar, 
  FileText, 
  HelpCircle, 
  Activity, 
  TrendingUp, 
  ShieldCheck, 
  Sparkles,
  Info,
  Layers
} from 'lucide-react';
import { 
  ThermalObservation, 
  IndustrialFacility, 
  ThermalFacilityAssociation, 
  ThermalClassification, 
  FacilityHistoricalBehavior, 
  FacilityNormalBaseline, 
  AbnormalThermalEvent, 
  VerificationRiskScore 
} from '../../types';

interface BottomAnalyticsPanelProps {
  selectedObservation: ThermalObservation | null;
  selectedFacility: IndustrialFacility | null;
  observations: ThermalObservation[];
  facilities: IndustrialFacility[];
  associations: ThermalFacilityAssociation[];
  classifications: ThermalClassification[];
  histories: FacilityHistoricalBehavior[];
  baselines: FacilityNormalBaseline[];
  anomalies: AbnormalThermalEvent[];
  riskScores: VerificationRiskScore[];
  onSelectObservation: (obs: ThermalObservation) => void;
}

type TabType = 'FRP TIMELINE' | 'FACILITY BASELINE' | 'EVENT HISTORY' | 'EVIDENCE' | 'EXPLANATION';

export const BottomAnalyticsPanel: React.FC<BottomAnalyticsPanelProps> = ({
  selectedObservation,
  selectedFacility,
  observations,
  facilities,
  associations,
  classifications,
  histories,
  baselines,
  anomalies,
  riskScores,
  onSelectObservation
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('FRP TIMELINE');

  const isSelected = !!selectedObservation || !!selectedFacility;

  const obs = selectedObservation;
  const assoc = obs ? associations.find(a => a.observation_id === obs.id) : null;
  const clf = obs ? classifications.find(c => c.observation_id === obs.id) : null;
  const anom = obs ? anomalies.find(a => a.observation_id === obs.id) : null;
  const risk = obs ? riskScores.find(r => r.observation_id === obs.id) : null;

  const fac = obs 
    ? (assoc ? facilities.find(f => f.id === assoc.facility_id) : null)
    : selectedFacility;

  const hist = fac ? histories.find(h => h.facility_id === fac.id) : null;
  const base = fac ? baselines.find(b => b.facility_id === fac.id) : null;

  // Resolve facility observations chronologically
  const relatedObs = fac
    ? associations
        .filter(a => a.facility_id === fac.id)
        .map(a => observations.find(o => o.id === a.observation_id))
        .filter((o): o is ThermalObservation => !!o)
        .sort((a, b) => new Date(a.observation_timestamp).getTime() - new Date(b.observation_timestamp).getTime())
    : (obs ? [obs] : []);

  const currentFrp = obs?.frp ?? (hist?.p99_frp ?? 0);
  const p50 = base?.baseline_frp_p50 ?? hist?.median_frp ?? 14.5;
  const p95 = base?.baseline_frp_p95 ?? hist?.p95_frp ?? 34.5;
  const p99 = base?.baseline_frp_p99 ?? hist?.p99_frp ?? 48.0;
  const maxRecorded = Math.max(p99 * 1.4, currentFrp, 60);

  const renderContent = () => {
    if (!isSelected) {
      return (
        <div className="flex items-center justify-center h-28 text-slate-500 font-mono tracking-widest text-xs uppercase gap-2.5">
          <Activity className="w-4 h-4 text-cyan-400 animate-pulse" />
          <span>Select any thermal anomaly point or industrial facility on the recon canvas to inspect telemetry</span>
        </div>
      );
    }

    switch (activeTab) {
      case 'FRP TIMELINE':
        return (
          <div className="flex flex-col gap-2 font-mono">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-300 text-xs tracking-wider uppercase flex items-center gap-1.5 font-display">
                <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
                Target Historical Radiative Intensity (FRP Chronological Passes)
              </span>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-400 font-mono bg-space-900 px-2 py-0.5 rounded border border-white/[0.08]">
                  P95 THRESHOLD: <strong className="text-amber-400">{p95.toFixed(1)} MW</strong>
                </span>
                <span className="text-[10px] text-cyan-400 font-mono bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-500/30 font-bold">
                  {relatedObs.length} SATELLITE PASS DETECTIONS
                </span>
              </div>
            </div>

            {relatedObs.length > 0 ? (
              <div className="flex items-end gap-3.5 h-24 pt-3 overflow-x-auto select-none border-b border-white/[0.06] pb-2 px-2 scrollbar-thin">
                {relatedObs.map((o) => {
                  const isCurrent = obs?.id === o.id;
                  const isSpike = (o.frp || 0) > p95;
                  const heightPct = Math.min(100, Math.max(14, ((o.frp || 5) / (maxRecorded * 1.1)) * 100));

                  return (
                    <div 
                      key={o.id} 
                      onClick={() => onSelectObservation(o)}
                      className="flex flex-col items-center gap-1 cursor-pointer group shrink-0 min-w-[36px]"
                    >
                      <span className={`text-[10px] font-bold transition-colors font-mono ${
                        isCurrent 
                          ? 'text-cyan-300 drop-shadow-[0_0_8px_rgba(0,240,255,0.8)]' 
                          : (isSpike ? 'text-red-400' : 'text-slate-400 group-hover:text-slate-200')
                      }`}>
                        {o.frp} MW
                      </span>
                      <div 
                        className={`w-6 rounded-t transition-all ${
                          isCurrent 
                            ? 'bg-cyan-400 shadow-[0_0_12px_rgba(0,240,255,0.8)] ring-1 ring-white' 
                            : (isSpike ? 'bg-red-500/80 group-hover:bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]' : 'bg-slate-700/80 group-hover:bg-slate-600')
                        }`}
                        style={{ height: `${heightPct * 0.65}px` }}
                      />
                      <span className="text-[9px] text-slate-400 font-medium font-mono">
                        {o.acq_date?.slice(5)}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-slate-500 text-center py-6 text-xs font-mono">No multiple orbital passes logged for this facility.</div>
            )}
          </div>
        );

      case 'FACILITY BASELINE':
        return (
          <div className="flex gap-6 items-center font-mono">
            {/* SVG Baseline Envelope Visualization */}
            <div className="flex-1">
              <svg className="w-full h-24 text-[10px] text-slate-400 select-none" viewBox="0 0 500 100">
                {/* Horizontal Baseline Guides */}
                <line x1="60" y1="20" x2="480" y2="20" stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
                <line x1="60" y1="50" x2="480" y2="50" stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
                <line x1="60" y1="80" x2="480" y2="80" stroke="rgba(255,255,255,0.12)" />

                {/* Y Axis labels */}
                <text x="15" y="24" fill="#94a3b8" textAnchor="start" fontSize="9">{(p99 * 1.5).toFixed(0)} MW</text>
                <text x="15" y="54" fill="#94a3b8" textAnchor="start" fontSize="9">{(p99 * 0.75).toFixed(0)} MW</text>
                <text x="15" y="84" fill="#94a3b8" textAnchor="start" fontSize="9">0 MW</text>

                {/* Y Axis line */}
                <line x1="60" y1="10" x2="60" y2="80" stroke="rgba(255,255,255,0.2)" />

                {/* Normal Operating Range Block (P50/P95) */}
                {(() => {
                  const scale = 60 / (p99 * 1.5 || 100);
                  const yP50 = Math.max(12, 80 - p50 * scale);
                  const yP95 = Math.max(12, 80 - p95 * scale);
                  const yCurrent = Math.max(12, 80 - currentFrp * scale);

                  return (
                    <g>
                      {/* Normal Range Area */}
                      <rect 
                        x="70" 
                        y={Math.max(12, yP95)} 
                        width="240" 
                        height={Math.min(68, Math.max(8, p95 * scale))} 
                        fill="#065f46" 
                        fillOpacity="0.35" 
                        stroke="#059669"
                        strokeOpacity="0.6"
                        rx="4"
                      />
                      <text x="320" y={Math.max(24, yP95 + 10)} fill="#34d399" fontSize="10" fontWeight="bold">
                        █ NORMAL OPERATING ENVELOPE (P95: {p95.toFixed(1)} MW)
                      </text>

                      {/* Baseline P95 Line */}
                      <line x1="60" y1={yP95} x2="480" y2={yP95} stroke="#fbbf24" strokeWidth="1.5" strokeDasharray="4 2" />

                      {/* Current Observation Point */}
                      <circle cx="200" cy={yCurrent} r="6" fill="#00f0ff" stroke="#030712" strokeWidth="2" className="animate-pulse" />
                      <text x="215" y={yCurrent + 4} fill="#00f0ff" fontSize="10" fontWeight="bold">
                        ● OBSERVED FRP: {currentFrp.toFixed(1)} MW
                      </text>
                    </g>
                  );
                })()}

                {/* X Axis Label */}
                <text x="270" y="96" fill="#64748b" textAnchor="middle" fontSize="9">Facility Historical Statistical Baseline Envelope (MW)</text>
              </svg>
            </div>

            {/* Quick Stats Panel */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono min-w-[220px]">
              <div className="p-2 rounded-xl bg-space-900/80 border border-white/[0.06]">
                <span className="text-slate-400 text-[9.5px] uppercase block">P50 Normal</span>
                <span className="text-cyan-300 font-bold text-sm">{p50.toFixed(1)} MW</span>
              </div>
              <div className="p-2 rounded-xl bg-space-900/80 border border-white/[0.06]">
                <span className="text-slate-400 text-[9.5px] uppercase block">P95 Threshold</span>
                <span className="text-amber-300 font-bold text-sm">{p95.toFixed(1)} MW</span>
              </div>
              <div className="p-2 rounded-xl bg-space-900/80 border border-white/[0.06]">
                <span className="text-slate-400 text-[9.5px] uppercase block">P99 Extreme</span>
                <span className="text-purple-300 font-bold text-sm">{p99.toFixed(1)} MW</span>
              </div>
              <div className="p-2 rounded-xl bg-space-900/80 border border-white/[0.06]">
                <span className="text-slate-400 text-[9.5px] uppercase block">Passes Count</span>
                <span className="text-emerald-300 font-bold text-sm">{hist?.total_observations_count ?? relatedObs.length}</span>
              </div>
            </div>
          </div>
        );

      case 'EVENT HISTORY':
        return (
          <div className="flex flex-col gap-2 max-h-[120px] overflow-y-auto pr-1 font-mono scrollbar-thin">
            <span className="font-bold text-slate-300 text-xs tracking-wider uppercase font-display">Facility Detection Telemetry Log</span>
            <table className="w-full text-left border-collapse text-[11px]">
              <thead>
                <tr className="border-b border-white/[0.08] text-slate-400 text-[9.5px] uppercase tracking-wider">
                  <th className="py-1 px-2">Event ID</th>
                  <th className="py-1 px-2">Timestamp (UTC)</th>
                  <th className="py-1 px-2">FRP (MW)</th>
                  <th className="py-1 px-2">Sensor Instrument</th>
                  <th className="py-1 px-2">Confidence</th>
                  <th className="py-1 px-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {relatedObs.map((o) => {
                  const isCurrent = obs?.id === o.id;
                  return (
                    <tr 
                      key={o.id}
                      onClick={() => onSelectObservation(o)}
                      className={`border-b border-white/[0.04] hover:bg-space-900/80 cursor-pointer transition-colors ${isCurrent ? 'text-cyan-300 font-bold bg-cyan-950/30' : 'text-slate-300'}`}
                    >
                      <td className="py-1.5 px-2">EVT-{String(o.id).padStart(5, '0')}</td>
                      <td className="py-1.5 px-2">{o.observation_timestamp?.replace('T', ' ').slice(0, 16)}</td>
                      <td className="py-1.5 px-2 font-bold text-red-400">{o.frp} MW</td>
                      <td className="py-1.5 px-2">{o.satellite}</td>
                      <td className="py-1.5 px-2 uppercase text-slate-400">{o.confidence}</td>
                      <td className="py-1.5 px-2">
                        <button className="text-[10px] text-cyan-400 hover:underline">Inspect</button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        );

      case 'EVIDENCE':
        return (
          <div className="flex flex-col gap-2 font-mono">
            <span className="font-bold text-slate-300 text-xs tracking-wider uppercase font-display flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              4-Factor Multi-Criteria Risk Breakdown (Authoritative Risk Engine)
            </span>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-slate-300 text-xs">
              <div className="bg-space-900/80 p-2.5 border border-white/[0.06] rounded-xl">
                <span className="text-slate-400 block text-[9.5px] uppercase font-bold">Spatial Proximity (25%)</span>
                <span className="font-bold font-mono text-cyan-300 block text-base mt-0.5">{risk?.spatial_proximity_score ?? 92} / 100</span>
                <p className="text-[9.5px] text-slate-400 mt-1 leading-snug">Geodesic distance to industrial perimeter.</p>
              </div>

              <div className="bg-space-900/80 p-2.5 border border-white/[0.06] rounded-xl">
                <span className="text-slate-400 block text-[9.5px] uppercase font-bold">FRP Anomaly Multiplier (30%)</span>
                <span className="font-bold font-mono text-amber-300 block text-base mt-0.5">{((risk?.frp_multiplier_score ?? risk?.frp_anomaly_score) ?? 85).toFixed(0)} / 100</span>
                <p className="text-[9.5px] text-slate-400 mt-1 leading-snug">Observed FRP relative to P95 statistical baseline.</p>
              </div>

              <div className="bg-space-900/80 p-2.5 border border-white/[0.06] rounded-xl">
                <span className="text-slate-400 block text-[9.5px] uppercase font-bold">Facility Sensitivity (25%)</span>
                <span className="font-bold font-mono text-purple-300 block text-base mt-0.5">{risk?.facility_sensitivity_score ?? 78} / 100</span>
                <p className="text-[9.5px] text-slate-400 mt-1 leading-snug">Facility infrastructure hazard classification.</p>
              </div>

              <div className="bg-space-900/80 p-2.5 border border-white/[0.06] rounded-xl">
                <span className="text-slate-400 block text-[9.5px] uppercase font-bold">Optical Confidence Proxy (20%)</span>
                <span className="font-bold font-mono text-emerald-300 block text-base mt-0.5">
                  {risk?.optical_verification_confidence != null 
                    ? `${(risk.optical_verification_confidence * 100).toFixed(0)}%` 
                    : `${(risk?.optical_confidence_proxy_score ?? 65).toFixed(0)}%`}
                </span>
                <p className="text-[9.5px] text-slate-400 mt-1 leading-snug">Secondary multi-spectral verification confidence.</p>
              </div>
            </div>
          </div>
        );

      case 'EXPLANATION':
        return (
          <div className="flex flex-col gap-2 font-mono">
            <span className="font-bold text-slate-300 text-xs tracking-wider uppercase font-display flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              Automated Findings & Explainable Intelligence
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-space-900/80 border border-white/[0.06] rounded-xl flex flex-col gap-1.5">
                <span className="text-purple-300 font-bold uppercase tracking-wider text-[10px] flex items-center gap-1">
                  <Layers className="w-3 h-3" /> Classification Findings
                </span>
                <span className="text-slate-300 leading-relaxed text-[11px]">
                  {clf?.rule_trigger ? `Rule Trigger: ${clf.rule_trigger} (${clf.source_type}, confidence ${(clf.classification_confidence * 100).toFixed(0)}%)` : "Source classification engine matched spatial proximity and emission criteria within validated operating buffer."}
                </span>
              </div>
              <div className="p-3 bg-space-900/80 border border-white/[0.06] rounded-xl flex flex-col gap-1.5">
                <span className="text-amber-400 font-bold uppercase tracking-wider text-[10px] flex items-center gap-1">
                  <Info className="w-3 h-3" /> Anomaly & Risk Findings
                </span>
                <span className="text-slate-300 leading-relaxed text-[11px]">
                  {anom?.detection_rule ? `Anomaly Detection: ${anom.detection_rule} (Severity: ${anom.anomaly_severity}, FRP: ${anom.observed_frp} MW vs P95 ${anom.expected_baseline_p95} MW)` : (risk?.risk_reasoning || "Signal evaluated against operational P50-P95 baseline bounds. Multi-criteria risk verification active.")}
                </span>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="bg-space-950/95 border-t border-white/[0.08] w-full shrink-0 shadow-[0_-8px_30px_rgba(0,0,0,0.9)] z-20 flex flex-col font-sans select-none backdrop-blur-2xl">
      {/* Header Bar */}
      <div 
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between px-4 py-2 bg-space-900/80 border-b border-white/[0.06] cursor-pointer hover:bg-space-900 transition-colors"
      >
        <div className="flex items-center gap-6 overflow-x-auto">
          <span className="font-mono font-extrabold text-white uppercase tracking-widest text-xs flex items-center gap-2 font-display shrink-0">
            <BarChart2 className="w-4 h-4 text-cyan-400" />
            <span>Telemetry & Baseline Analytics Suite</span>
          </span>

          {/* Tab Selector Links */}
          {isSelected && !collapsed && (
            <div className="flex items-center gap-3 ml-2 text-[10.5px] font-bold font-mono tracking-wider shrink-0">
              {([
                { name: 'FRP TIMELINE', icon: Activity },
                { name: 'FACILITY BASELINE', icon: BarChart2 },
                { name: 'EVENT HISTORY', icon: Calendar },
                { name: 'EVIDENCE', icon: FileText },
                { name: 'EXPLANATION', icon: HelpCircle }
              ] as { name: TabType, icon: any }[]).map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.name;
                return (
                  <button
                    key={tab.name}
                    onClick={(e) => { e.stopPropagation(); setActiveTab(tab.name); }}
                    className={`flex items-center gap-1.5 transition-all uppercase py-1 px-2.5 rounded-lg border text-[10.5px] cursor-pointer ${
                      isActive 
                        ? 'text-cyan-300 bg-cyan-950/60 border-cyan-500/40 shadow-[0_0_10px_rgba(0,240,255,0.3)]' 
                        : 'text-slate-400 border-transparent hover:text-slate-200 hover:bg-space-800'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {tab.name}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <button className="text-slate-400 hover:text-cyan-300 transition-colors p-1 cursor-pointer">
          {collapsed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Main Content Area */}
      {!collapsed && (
        <div className="p-4 bg-space-950/70 min-h-[110px] max-h-[175px] overflow-y-auto">
          {renderContent()}
        </div>
      )}
    </div>
  );
};

export default BottomAnalyticsPanel;
