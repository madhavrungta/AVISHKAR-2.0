import React, { useState } from 'react';
import { 
  ThermalObservation, 
  IndustrialFacility, 
  ThermalFacilityAssociation, 
  ThermalClassification, 
  FacilityHistoricalBehavior, 
  FacilityNormalBaseline, 
  AbnormalThermalEvent, 
  VerificationRiskScore 
} from '../types';
import { ChevronDown, ChevronUp, BarChart2, Calendar, FileText, HelpCircle, Activity } from 'lucide-react';

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

  // If nothing is selected, display a neat placeholder message
  const isSelected = !!selectedObservation || !!selectedFacility;

  // Resolve current active facility
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

  // Get observations related to the facility
  const relatedObs = fac
    ? associations
        .filter(a => a.facility_id === fac.id)
        .map(a => observations.find(o => o.id === a.observation_id))
        .filter((o): o is ThermalObservation => !!o)
        .sort((a, b) => new Date(a.observation_timestamp).getTime() - new Date(b.observation_timestamp).getTime())
    : [];

  const currentFrp = obs?.frp ?? (hist?.max_frp ?? 0);
  const p50 = base?.baseline_frp_p50 ?? hist?.median_frp ?? 5;
  const p95 = base?.baseline_frp_p95 ?? hist?.p95_frp ?? 25;
  const p99 = base?.baseline_frp_p99 ?? hist?.p99_frp ?? 50;

  const renderContent = () => {
    if (!isSelected) {
      return (
        <div className="flex items-center justify-center h-28 text-slate-500 font-mono tracking-wider text-[11px] uppercase">
          Select a thermal anomaly or industrial facility on the map to inspect intelligence profiles
        </div>
      );
    }

    switch (activeTab) {
      case 'FRP TIMELINE':
        return (
          <div className="flex flex-col gap-2.5">
            <span className="font-bold text-slate-400 text-[10px] tracking-wider uppercase">Facility Thermal Observation Timeline</span>
            {relatedObs.length > 0 ? (
              <div className="flex items-end gap-3 h-20 pt-4 overflow-x-auto select-none border-b border-slate-800 pb-2">
                {relatedObs.map((o) => {
                  const isCurrent = obs?.id === o.id;
                  const heightPct = Math.min(100, Math.max(10, (o.frp || 5) / 2));
                  return (
                    <div 
                      key={o.id} 
                      onClick={() => onSelectObservation(o)}
                      className="flex flex-col items-center gap-1 cursor-pointer group shrink-0"
                    >
                      <span className={`text-[9px] font-mono font-bold transition-colors ${isCurrent ? 'text-cyan-400' : 'text-slate-400 group-hover:text-slate-200'}`}>
                        {o.frp}W
                      </span>
                      <div 
                        className={`w-4 rounded-t-sm transition-all ${
                          isCurrent 
                            ? 'bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.5)]' 
                            : 'bg-slate-700 group-hover:bg-slate-650'
                        }`}
                        style={{ height: `${heightPct}px` }}
                      />
                      <span className="text-[8px] text-slate-500 font-mono">
                        {o.acq_date?.slice(5)}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-slate-500 text-center py-6">No historical observations found for this industrial facility.</div>
            )}
          </div>
        );

      case 'FACILITY BASELINE':
        return (
          <div className="flex gap-6 items-center">
            {/* SVG Baseline Bar Chart */}
            <div className="flex-1">
              <svg className="w-full h-24 font-mono text-[9px] text-slate-400 select-none">
                {/* Horizontal Baseline lines */}
                <line x1="50" y1="20" x2="350" y2="20" stroke="#334155" strokeDasharray="3 3" />
                <line x1="50" y1="50" x2="350" y2="50" stroke="#334155" strokeDasharray="3 3" />
                <line x1="50" y1="80" x2="350" y2="80" stroke="#334155" />

                {/* Y Axis labels */}
                <text x="15" y="24" fill="#64748b" textAnchor="start">200 MW</text>
                <text x="15" y="54" fill="#64748b" textAnchor="start">100 MW</text>
                <text x="15" y="84" fill="#64748b" textAnchor="start">0 MW</text>

                {/* Y Axis line */}
                <line x1="50" y1="10" x2="50" y2="80" stroke="#475569" />

                {/* Normal Operating Range Block (P50/P95) */}
                {(() => {
                  const yP50 = 80 - p50 * 0.3;
                  const yP95 = 80 - p95 * 0.3;
                  const yCurrent = 80 - currentFrp * 0.3;

                  return (
                    <>
                      {/* Normal Range Area */}
                      <rect 
                        x="60" 
                        y={Math.max(10, yP95)} 
                        width="180" 
                        height={Math.min(70, p95 * 0.3)} 
                        fill="#065f46" 
                        fillOpacity="0.4" 
                        stroke="#059669"
                        strokeOpacity="0.5"
                      />
                      <text x="250" y={Math.max(25, yP95 + 10)} fill="#34d399">█ NORMAL OPERATING ENVELOPE (P95)</text>

                      {/* Baseline P95 Line */}
                      <line x1="50" y1={yP95} x2="350" y2={yP95} stroke="#fbbf24" strokeWidth="1.5" />
                      <text x="355" y={yP95 + 3} fill="#fbbf24" textAnchor="start">── P95 BASELINE ({p95.toFixed(0)} MW)</text>

                      {/* Current Observation Point */}
                      <circle cx="150" cy={yCurrent} r="5" fill="#00f0ff" stroke="#0f172a" strokeWidth="1.5" />
                      <text x="160" y={yCurrent + 3} fill="#00f0ff" className="font-bold">● CURRENT FRP ({currentFrp.toFixed(0)} MW)</text>
                    </>
                  );
                })()}

                {/* X Axis Label */}
                <text x="200" y="96" fill="#64748b" textAnchor="middle">Facility Historical Activity Profile</text>
              </svg>
            </div>
          </div>
        );

      case 'EVENT HISTORY':
        return (
          <div className="flex flex-col gap-2 max-h-[110px] overflow-y-auto pr-1">
            <span className="font-bold text-slate-400 text-[10px] tracking-wider uppercase">Past Facility Events</span>
            <table className="w-full text-left border-collapse font-mono text-[10.5px]">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 text-[9px] uppercase tracking-wider">
                  <th className="py-1">Observation ID</th>
                  <th className="py-1">Timestamp</th>
                  <th className="py-1">FRP</th>
                  <th className="py-1">Satellite</th>
                  <th className="py-1">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {relatedObs.map((o) => (
                  <tr 
                    key={o.id}
                    onClick={() => onSelectObservation(o)}
                    className={`border-b border-slate-855/50 hover:bg-slate-855/40 cursor-pointer ${obs?.id === o.id ? 'text-cyan-400 font-bold' : 'text-slate-300'}`}
                  >
                    <td className="py-1">OBS #{o.id}</td>
                    <td className="py-1">{o.observation_timestamp?.replace('T', ' ').slice(0, 16)}</td>
                    <td className="py-1">{o.frp} MW</td>
                    <td className="py-1">{o.satellite}</td>
                    <td className="py-1 uppercase">{o.confidence}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      case 'EVIDENCE':
        return (
          <div className="flex flex-col gap-2">
            <span className="font-bold text-slate-400 text-[10px] tracking-wider uppercase">Detailed Scoring & Verification Metrics</span>
            <div className="grid grid-cols-4 gap-3 text-slate-300 text-[11px]">
              <div className="bg-slate-950/60 p-2.5 border border-slate-850 rounded">
                <span className="text-slate-500 block text-[9px] uppercase">Spatial Proximity</span>
                <span className="font-bold font-mono text-slate-200 block text-sm mt-0.5">{risk?.spatial_proximity_score ?? 0} / 100</span>
                <p className="text-[9.5px] text-slate-500 mt-1 leading-snug">Association distance in meters to nearest boundary.</p>
              </div>

              <div className="bg-slate-950/60 p-2.5 border border-slate-850 rounded">
                <span className="text-slate-500 block text-[9px] uppercase">FRP Multiplier</span>
                <span className="font-bold font-mono text-slate-200 block text-sm mt-0.5">{risk?.frp_multiplier_score ?? 0} / 100</span>
                <p className="text-[9.5px] text-slate-500 mt-1 leading-snug">Current FRP emission vs facility historical envelopes.</p>
              </div>

              <div className="bg-slate-950/60 p-2.5 border border-slate-850 rounded">
                <span className="text-slate-500 block text-[9px] uppercase">Sensitivity Layer</span>
                <span className="font-bold font-mono text-slate-200 block text-sm mt-0.5">{risk?.facility_sensitivity_score ?? 0} / 100</span>
                <p className="text-[9.5px] text-slate-500 mt-1 leading-snug">Environmental or infrastructure priority level.</p>
              </div>

              <div className="bg-slate-950/60 p-2.5 border border-slate-850 rounded">
                <span className="text-slate-500 block text-[9px] uppercase">Optical Confidence</span>
                <span className="font-bold font-mono text-slate-200 block text-sm mt-0.5">{(risk?.optical_verification_confidence ?? 0) * 100}%</span>
                <p className="text-[9.5px] text-slate-500 mt-1 leading-snug">Spectral verification index from secondary passes.</p>
              </div>
            </div>
          </div>
        );

      case 'EXPLANATION':
        return (
          <div className="flex flex-col gap-2">
            <span className="font-bold text-slate-400 text-[10px] tracking-wider uppercase">Natural Language Verification Findings</span>
            <div className="grid grid-cols-2 gap-3 text-[11px]">
              <div className="p-2.5 bg-slate-950/60 border border-slate-850 rounded flex flex-col gap-1">
                <span className="text-purple-300 font-bold uppercase tracking-wider text-[9px]">Classification Analysis</span>
                <span className="text-slate-300 leading-relaxed">
                  {clf?.classification_reason || "The algorithm evaluated the thermal signal ratio against typical signatures."}
                </span>
              </div>
              <div className="p-2.5 bg-slate-950/60 border border-slate-850 rounded flex flex-col gap-1">
                <span className="text-amber-400 font-bold uppercase tracking-wider text-[9px]">Anomaly & Risk Evaluation</span>
                <span className="text-slate-300 leading-relaxed">
                  {anom?.explanation_reason || "No abnormal alerts compiled. Current signal stays within normal limits."}
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
    <div className="bg-slate-900 border-t border-slate-800 w-full shrink-0 shadow-inner z-20 flex flex-col font-sans select-none">
      {/* Header bar */}
      <div 
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between px-4 py-2 bg-slate-950 border-b border-slate-850 cursor-pointer"
      >
        <div className="flex items-center gap-6">
          <span className="font-mono font-extrabold text-slate-100 uppercase tracking-widest text-xs flex items-center gap-1.5">
            <BarChart2 className="w-4 h-4 text-amber-500" />
            Baseline & Intelligence Analytics
          </span>

          {/* Tab Selector Links */}
          {isSelected && !collapsed && (
            <div className="flex items-center gap-3.5 ml-4 text-[10px] font-bold font-mono tracking-wider">
              {([
                { name: 'FRP TIMELINE', icon: Activity },
                { name: 'FACILITY BASELINE', icon: BarChart2 },
                { name: 'EVENT HISTORY', icon: Calendar },
                { name: 'EVIDENCE', icon: FileText },
                { name: 'EXPLANATION', icon: HelpCircle }
              ] as { name: TabType, icon: any }[]).map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.name}
                    onClick={(e) => { e.stopPropagation(); setActiveTab(tab.name); }}
                    className={`flex items-center gap-1 transition-colors uppercase border-b-2 py-1 ${
                      activeTab === tab.name 
                        ? 'text-amber-400 border-amber-500' 
                        : 'text-slate-500 border-transparent hover:text-slate-300'
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

        <button className="text-slate-400 hover:text-slate-200">
          {collapsed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Main Content Area */}
      {!collapsed && (
        <div className="p-4 bg-slate-900/40 min-h-[100px] max-h-[160px] overflow-y-auto">
          {renderContent()}
        </div>
      )}
    </div>
  );
};

export default BottomAnalyticsPanel;
