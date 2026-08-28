import React from 'react';
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
import { X, ShieldAlert, Check } from 'lucide-react';
import { AskInvestigationAI } from './AskInvestigationAI';

interface EventDetailDrawerProps {
  selectedObservation: ThermalObservation | null;
  selectedFacility: IndustrialFacility | null;
  associations: ThermalFacilityAssociation[];
  classifications: ThermalClassification[];
  histories: FacilityHistoricalBehavior[];
  baselines: FacilityNormalBaseline[];
  anomalies: AbnormalThermalEvent[];
  riskScores: VerificationRiskScore[];
  facilities: IndustrialFacility[];
  onClose: () => void;
}

export const EventDetailDrawer: React.FC<EventDetailDrawerProps> = ({
  selectedObservation,
  selectedFacility,
  associations,
  classifications,
  histories,
  baselines,
  anomalies,
  riskScores,
  facilities,
  onClose
}) => {
  if (!selectedObservation && !selectedFacility) return null;

  const obs = selectedObservation;
  const assoc = obs ? associations.find(a => a.observation_id === obs.id) : null;
  const clf = obs ? classifications.find(c => c.observation_id === obs.id) : null;
  const anom = obs ? anomalies.find(a => a.observation_id === obs.id) : null;
  const risk = obs ? riskScores.find(r => r.observation_id === obs.id) : null;
  
  const relatedFac = obs 
    ? (assoc ? facilities.find(f => f.id === assoc.facility_id) : null)
    : selectedFacility;

  const fac = relatedFac;
  const hist = fac ? histories.find(h => h.facility_id === fac.id) : null;
  const base = fac ? baselines.find(b => b.facility_id === fac.id) : null;

  const currentFrp = obs?.frp ?? (hist?.max_frp ?? 0);
  const p95 = base?.baseline_frp_p95 ?? hist?.p95_frp ?? 25;
  const deviation = p95 > 0 ? ((currentFrp - p95) / p95) * 100 : 0;
  const persistence = hist ? `${(hist.total_observations * 1.2).toFixed(1)} hours` : 'N/A';

  const riskLabel = risk ? risk.risk_level.replace(/_/g, ' ') : (anom ? 'HIGH INVESTIGATION PRIORITY' : 'MODERATE PRIORITY');

  // Evidence list
  const hasAboveBaseline = currentFrp > p95;
  const hasPersistent = hist ? hist.total_observations > 2 : false;
  const hasAssoc = !!assoc;
  const hasMultiple = hist ? hist.total_observations > 1 : false;

  // Real backend reasons
  const evidenceBullets: string[] = [];
  if (risk?.spatial_proximity_score) evidenceBullets.push(`Proximity score ${risk.spatial_proximity_score}/100 to facility.`);
  if (risk?.frp_multiplier_score) evidenceBullets.push(`FRP intensity multiplier score ${risk.frp_multiplier_score}/100.`);
  if (anom?.explanation_reason) evidenceBullets.push(anom.explanation_reason);
  if (clf?.classification_reason) evidenceBullets.push(clf.classification_reason);

  return (
    <aside className="fixed top-14 right-0 w-80 bg-slate-900 border-l border-slate-800 text-slate-100 h-[calc(100vh-3.5rem)] overflow-y-auto z-[1000] shadow-2xl flex flex-col text-xs font-mono select-none">
      {/* Header */}
      <div className="p-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-950/80 sticky top-0 z-10">
        <div>
          <h2 className="font-extrabold text-slate-100 text-sm tracking-wider">
            {obs ? `EVENT EVT-${String(obs.id).padStart(5, '0')}` : `FACILITY FAC-${String(fac?.id).padStart(4, '0')}`}
          </h2>
          <span className="text-[9px] font-bold text-red-500 tracking-tight block mt-0.5 uppercase">
            {riskLabel}
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          title="Close Intelligence Drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="p-4 flex flex-col gap-4 text-slate-300">
        {/* Description */}
        <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider pb-1">
          Potential Industrial Thermal Event
        </div>

        <div className="h-px bg-slate-800" />

        {/* Facility Info */}
        <div>
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1.5">FACILITY</div>
          {fac ? (
            <div className="flex flex-col gap-1 text-[11px]">
              <span className="font-bold text-purple-300">{fac.name || 'Industrial Facility'}</span>
              <span className="text-slate-400">Type: <span className="text-slate-200 font-bold uppercase">{fac.facility_type}</span></span>
              {fac.operator && <span className="text-slate-400">Operator: <span className="text-slate-200">{fac.operator}</span></span>}
            </div>
          ) : (
            <span className="text-slate-500">No associated facility in database.</span>
          )}
        </div>

        <div className="h-px bg-slate-800" />

        {/* Current Observation */}
        <div>
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1.5">CURRENT OBSERVATION</div>
          <div className="flex flex-col gap-1 text-[11px]">
            <div className="flex justify-between">
              <span className="text-slate-400">FRP</span>
              <span className="font-bold text-slate-200">{currentFrp.toFixed(0)} MW</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Historical P95</span>
              <span className="font-bold text-slate-250">{p95.toFixed(0)} MW</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Deviation</span>
              <span className={`font-bold ${deviation >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {deviation >= 0 ? '+' : ''}{deviation.toFixed(0)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Persistence</span>
              <span className="font-bold text-slate-200">{persistence}</span>
            </div>
          </div>
        </div>

        <div className="h-px bg-slate-800" />

        {/* Evidence Checklist */}
        <div>
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2">EVIDENCE</div>
          <div className="flex flex-col gap-1.5 text-[11px]">
            <div className="flex items-center gap-2">
              <span className={`w-3.5 h-3.5 rounded flex items-center justify-center border ${hasAboveBaseline ? 'border-amber-500 text-amber-500 bg-amber-500/10' : 'border-slate-800 text-slate-600'}`}>
                {hasAboveBaseline && <Check className="w-3 h-3" />}
              </span>
              <span className={hasAboveBaseline ? 'text-slate-200' : 'text-slate-500 line-through'}>Above historical baseline</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`w-3.5 h-3.5 rounded flex items-center justify-center border ${hasPersistent ? 'border-amber-500 text-amber-500 bg-amber-500/10' : 'border-slate-800 text-slate-600'}`}>
                {hasPersistent && <Check className="w-3 h-3" />}
              </span>
              <span className={hasPersistent ? 'text-slate-200' : 'text-slate-500 line-through'}>Persistent thermal activity</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`w-3.5 h-3.5 rounded flex items-center justify-center border ${hasAssoc ? 'border-amber-500 text-amber-500 bg-amber-500/10' : 'border-slate-800 text-slate-600'}`}>
                {hasAssoc && <Check className="w-3 h-3" />}
              </span>
              <span className={hasAssoc ? 'text-slate-200' : 'text-slate-500 line-through'}>Industrial facility association</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`w-3.5 h-3.5 rounded flex items-center justify-center border ${hasMultiple ? 'border-amber-500 text-amber-500 bg-amber-500/10' : 'border-slate-800 text-slate-600'}`}>
                {hasMultiple && <Check className="w-3 h-3" />}
              </span>
              <span className={hasMultiple ? 'text-slate-200' : 'text-slate-500 line-through'}>Multiple observations</span>
            </div>

            <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mt-2">OPTICAL EVIDENCE</div>
            <div className="text-slate-400 font-semibold bg-slate-950/60 p-2 border border-slate-850 rounded text-center">
              Not available
            </div>
          </div>
        </div>

        <div className="h-px bg-slate-800" />

        {/* Why Prioritized */}
        <div>
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2 flex items-center gap-1">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
            WHY PRIORITIZED?
          </div>
          {evidenceBullets.length > 0 ? (
            <ul className="list-disc pl-4 flex flex-col gap-1.5 text-[10.5px] leading-relaxed text-slate-300">
              {evidenceBullets.map((bullet, idx) => (
                <li key={idx}>{bullet}</li>
              ))}
            </ul>
          ) : (
            <span className="text-slate-500">No active prioritisation metrics flagged.</span>
          )}
        </div>

        {obs && (
          <>
            <div className="h-px bg-slate-800" />
            <AskInvestigationAI eventId={String(obs.id)} />
          </>
        )}
      </div>
    </aside>
  );
};

export default EventDetailDrawer;
