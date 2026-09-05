import React from 'react';
import { motion } from 'framer-motion';
import { 
  X, 
  Flame, 
  Building2, 
  ShieldCheck, 
  TrendingUp, 
  Bot, 
  Radio, 
  CheckCircle2, 
  Clock, 
  MapPin,
  Layers,
  Sparkles,
  Info
} from 'lucide-react';
import { 
  ThermalObservation, 
  IndustrialFacility, 
  ThermalFacilityAssociation, 
  ThermalClassification, 
  FacilityHistoricalBehavior, 
  FacilityNormalBaseline, 
  AbnormalThermalEvent, 
  VerificationRiskScore,
  ImpactAssessmentResponse 
} from '../../types';
import { AnimatedRiskGauge } from './AnimatedRiskGauge';

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
  impactData?: ImpactAssessmentResponse | null;
  loadingImpact?: boolean;
  errorImpact?: string | null;
  impactRadius?: number;
  onChangeImpactRadius?: (radius: number) => void;
  onRetryImpact?: () => void;
  onClose: () => void;
  onOpenAIWithContext: (obsId: number) => void;
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
  impactData,
  loadingImpact = false,
  errorImpact = null,
  impactRadius = 5.0,
  onChangeImpactRadius,
  onRetryImpact,
  onClose,
  onOpenAIWithContext
}) => {
  if (!selectedObservation && !selectedFacility) return null;

  // Derive target data
  const isObservationView = !!selectedObservation;
  const currentObs = selectedObservation;

  // Phase 3B Impact Category Filter State
  const [impactCategoryFilter, setImpactCategoryFilter] = React.useState<'ALL' | 'INDUSTRIAL' | 'ENERGY' | 'HEALTHCARE' | 'TRANSPORTATION'>('ALL');

  // Derive counts
  const totalImpactEntities = impactData?.entities || [];
  const industrialCount = totalImpactEntities.filter(e => (e.entity_category || 'INDUSTRIAL') === 'INDUSTRIAL').length;
  const energyCount = totalImpactEntities.filter(e => e.entity_category === 'ENERGY').length;
  const healthcareCount = totalImpactEntities.filter(e => e.entity_category === 'HEALTHCARE').length;
  const transportCount = totalImpactEntities.filter(e => e.entity_category === 'TRANSPORTATION').length;

  const filteredImpactEntities = totalImpactEntities.filter(e => {
    if (impactCategoryFilter === 'INDUSTRIAL') return (e.entity_category || 'INDUSTRIAL') === 'INDUSTRIAL';
    if (impactCategoryFilter === 'ENERGY') return e.entity_category === 'ENERGY';
    if (impactCategoryFilter === 'HEALTHCARE') return e.entity_category === 'HEALTHCARE';
    if (impactCategoryFilter === 'TRANSPORTATION') return e.entity_category === 'TRANSPORTATION';
    return true;
  });

  // Find linked entities
  const linkedAssoc = currentObs 
    ? associations.find(a => a.observation_id === currentObs.id) 
    : null;

  const linkedFac = selectedFacility 
    || (linkedAssoc ? facilities.find(f => f.id === linkedAssoc.facility_id) : null);

  const linkedRisk = currentObs 
    ? riskScores.find(r => r.observation_id === currentObs.id) 
    : null;

  const linkedAnom = currentObs 
    ? anomalies.find(a => a.observation_id === currentObs.id) 
    : null;

  const linkedBase = linkedFac 
    ? baselines.find(b => b.facility_id === linkedFac.id) 
    : null;

  const linkedHist = linkedFac 
    ? histories.find(h => h.facility_id === linkedFac.id) 
    : null;

  const baselineP95 = linkedBase?.baseline_frp_p95 ?? linkedAnom?.expected_baseline_p95 ?? 34.5;
  const observedFrp = currentObs?.frp ?? 0;
  const variancePct = baselineP95 > 0 ? ((observedFrp - baselineP95) / baselineP95) * 100 : 0;

  return (
    <motion.aside
      initial={{ x: 420, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 420, opacity: 0 }}
      transition={{ type: 'spring', damping: 26, stiffness: 280 }}
      className="fixed top-16 right-0 bottom-0 w-full sm:w-[420px] bg-space-950/95 backdrop-blur-2xl border-l border-white/[0.08] shadow-2xl z-[9990] flex flex-col font-sans select-none overflow-hidden"
    >
      {/* Drawer Header */}
      <div className="p-4 border-b border-white/[0.08] flex items-center justify-between bg-space-900/40">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
          <span className="font-bold text-white text-sm font-display uppercase tracking-wider">
            {isObservationView ? 'Target Investigation Dossier' : 'Industrial Facility Dossier'}
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-space-850 text-slate-400 hover:text-white transition-colors"
          title="Close Dossier"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Scrollable Dossier Content */}
      <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-5">
        {/* Top Header Card */}
        <div className="p-4 rounded-2xl bg-gradient-to-br from-space-900 to-space-850 border border-white/[0.08] flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-cyan-400 uppercase font-bold">
              {isObservationView ? `OBSERVATION #${currentObs?.id}` : `OSM ID #${selectedFacility?.osm_id}`}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              {currentObs ? `${currentObs.acq_date} ${currentObs.acq_time} UTC` : 'Facility Profile'}
            </span>
          </div>

          <h3 className="text-lg font-bold text-white leading-tight font-display">
            {linkedFac?.name || 'Isolated Thermal Anomaly Candidate'}
          </h3>

          <div className="flex items-center gap-2 text-xs text-slate-400 font-mono mt-1">
            <MapPin className="w-3.5 h-3.5 text-cyan-400" />
            <span>
              {isObservationView
                ? `${(currentObs?.latitude ?? 0).toFixed(4)}° N, ${(currentObs?.longitude ?? 0).toFixed(4)}° E`
                : `${(selectedFacility?.latitude ?? 0).toFixed(4)}° N, ${(selectedFacility?.longitude ?? 0).toFixed(4)}° E`}
            </span>
          </div>
        </div>

        {/* 0-100 Circular Risk Gauge */}
        {linkedRisk && (
          <AnimatedRiskGauge 
            score={linkedRisk.composite_risk_score ?? 0} 
            tier={linkedRisk.risk_level || linkedRisk.priority_tier || 'LOW_RISK'} 
          />
        )}

        {/* Thermal Output vs Normal Operating Envelope */}
        {isObservationView && currentObs && (
          <div className="p-4 rounded-2xl bg-space-900/80 border border-white/[0.08] flex flex-col gap-3">
            <span className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              Thermal Output vs Historical P95 Baseline
            </span>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-3 rounded-xl bg-space-950/80 border border-white/[0.04]">
                <span className="text-slate-400 block text-[11px]">Observed FRP</span>
                <span className="text-lg font-bold font-mono text-red-400">{observedFrp} MW</span>
              </div>
              <div className="p-3 rounded-xl bg-space-950/80 border border-white/[0.04]">
                <span className="text-slate-400 block text-[11px]">P95 Threshold</span>
                <span className="text-lg font-bold font-mono text-cyan-300">{(baselineP95 ?? 0).toFixed(1)} MW</span>
              </div>
            </div>

            {/* Baseline Delta Variance */}
            <div className="p-3 rounded-xl bg-space-950/60 border border-white/[0.04] flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">Statistical Variance:</span>
              <span className={`font-bold ${variancePct > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {variancePct > 0 ? `+${(variancePct ?? 0).toFixed(0)}% Above Envelope` : 'Within Normal Baseline'}
              </span>
            </div>
          </div>
        )}

        {/* Facility Target Dossier */}
        {linkedFac && (
          <div className="p-4 rounded-2xl bg-space-900/80 border border-white/[0.08] flex flex-col gap-2.5">
            <span className="text-xs font-bold text-purple-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
              <Building2 className="w-4 h-4 text-purple-400" />
              Associated Infrastructure
            </span>

            <div className="text-xs flex flex-col gap-1.5">
              <div className="flex justify-between">
                <span className="text-slate-400">Facility Type:</span>
                <span className="font-semibold text-white uppercase">{linkedFac.facility_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Operator:</span>
                <span className="font-semibold text-slate-200">{linkedFac.operator || 'Not Listed'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Footprint Area:</span>
                <span className="font-mono text-slate-200">{(((linkedFac.surface_area_sqm || 0) / 10000)).toFixed(1)} Hectares</span>
              </div>
              {linkedAssoc && (
                <div className="flex justify-between border-t border-white/[0.04] pt-1.5 mt-1 font-mono">
                  <span className="text-slate-400">Proximity Distance:</span>
                  <span className="font-bold text-cyan-400">
                    {Math.round(linkedAssoc.distance_meters || 0)}m ({linkedAssoc.association_type || 'DIRECT_MATCH'})
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Multi-Criteria Evidence Verification Audit Checklist */}
        <div className="p-4 rounded-2xl bg-space-900/80 border border-white/[0.08] flex flex-col gap-2.5">
          <span className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Evidence Verification Audit
          </span>

          <div className="flex flex-col gap-2 text-xs font-mono">
            {/* 1. FRP Baseline Exceedance */}
            <div className="flex items-center gap-2">
              <span className={`w-4 h-4 rounded flex items-center justify-center border text-[10px] ${
                observedFrp > baselineP95
                  ? 'border-amber-400 text-amber-300 bg-amber-500/20'
                  : 'border-slate-700 text-slate-600 bg-space-950'
              }`}>
                {observedFrp > baselineP95 ? '✓' : '✗'}
              </span>
              <span className={observedFrp > baselineP95 ? 'text-white font-semibold' : 'text-slate-500 line-through'}>
                Observed FRP Exceeds Historical P95
              </span>
            </div>

            {/* 2. Multi-Pass Persistence */}
            <div className="flex items-center gap-2">
              <span className={`w-4 h-4 rounded flex items-center justify-center border text-[10px] ${
                linkedHist && (linkedHist.total_observations_count || 0) > 1
                  ? 'border-cyan-400 text-cyan-300 bg-cyan-500/20'
                  : 'border-slate-700 text-slate-600 bg-space-950'
              }`}>
                {linkedHist && (linkedHist.total_observations_count || 0) > 1 ? '✓' : '✗'}
              </span>
              <span className={linkedHist && (linkedHist.total_observations_count || 0) > 1 ? 'text-white font-semibold' : 'text-slate-500 line-through'}>
                Multi-Pass Persistent Thermal History
              </span>
            </div>

            {/* 3. Industrial Spatial Linkage */}
            <div className="flex items-center gap-2">
              <span className={`w-4 h-4 rounded flex items-center justify-center border text-[10px] ${
                linkedAssoc
                  ? 'border-purple-400 text-purple-300 bg-purple-500/20'
                  : 'border-slate-700 text-slate-600 bg-space-950'
              }`}>
                {linkedAssoc ? '✓' : '✗'}
              </span>
              <span className={linkedAssoc ? 'text-white font-semibold' : 'text-slate-500 line-through'}>
                Industrial Perimeter Spatial Linkage
              </span>
            </div>

            {/* 4. Multi-Sensor Corroboration */}
            <div className="flex items-center gap-2">
              <span className={`w-4 h-4 rounded flex items-center justify-center border text-[10px] ${
                currentObs?.satellite
                  ? 'border-emerald-400 text-emerald-300 bg-emerald-500/20'
                  : 'border-slate-700 text-slate-600 bg-space-950'
              }`}>
                {currentObs?.satellite ? '✓' : '✗'}
              </span>
              <span className={currentObs?.satellite ? 'text-white font-semibold' : 'text-slate-500 line-through'}>
                Multi-Sensor Corroboration
              </span>
            </div>
          </div>
        </div>

        {/* Impact Assessment — Potentially Exposed Nearby Entities */}
        {isObservationView && currentObs && (
          <div className="glass-panel p-4 rounded-2xl border border-white/[0.08] flex flex-col gap-3">
            <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
              <div className="flex items-center gap-2">
                <Building2 className="w-4 h-4 text-cyan-400" />
                <span className="font-bold text-white uppercase text-xs tracking-wider font-display">
                  POTENTIALLY EXPOSED NEARBY ENTITIES
                </span>
              </div>
              <span className="text-[10px] text-slate-400 font-mono font-bold">
                {loadingImpact ? 'SCANNING...' : `FOUND: ${impactData?.total_entities_found ?? 0}`}
              </span>
            </div>

            {/* Assessment Radius Quick Selector & Category Tabs */}
            <div className="flex flex-col gap-2 bg-space-900/80 p-2 rounded-xl border border-white/[0.06]">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono px-1">
                  Assessment Radius
                </span>
                <div className="flex items-center gap-1">
                  {[1.0, 5.0, 10.0].map((radius) => {
                    const isSelected = Math.abs(impactRadius - radius) < 0.1;
                    return (
                      <button
                        key={radius}
                        onClick={() => onChangeImpactRadius?.(radius)}
                        className={`px-2 py-0.5 rounded text-xs font-semibold font-mono transition-all ${
                          isSelected
                            ? 'bg-cyan-500 text-space-950 font-bold shadow-glow-cyan'
                            : 'text-slate-400 hover:text-white hover:bg-space-850'
                        }`}
                      >
                        {radius} km
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Phase 3B Responsive Two-Row Category Filter Layout */}
              <div className="flex flex-col gap-1.5 border-t border-white/[0.06] pt-2 font-mono text-[10px]">
                {/* Row 1: ALL | INDUSTRIAL | ENERGY */}
                <div className="grid grid-cols-3 gap-1">
                  <button
                    onClick={() => setImpactCategoryFilter('ALL')}
                    className={`py-1 px-1 rounded transition-all font-bold text-center truncate ${
                      impactCategoryFilter === 'ALL'
                        ? 'bg-white/10 text-white border border-white/20'
                        : 'text-slate-400 hover:text-white bg-space-950/60 border border-transparent'
                    }`}
                  >
                    ALL ({totalImpactEntities.length})
                  </button>
                  <button
                    onClick={() => setImpactCategoryFilter('INDUSTRIAL')}
                    className={`py-1 px-1 rounded transition-all font-bold text-center truncate ${
                      impactCategoryFilter === 'INDUSTRIAL'
                        ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/50'
                        : 'text-slate-400 hover:text-white bg-space-950/60 border border-transparent'
                    }`}
                  >
                    🏭 IND ({industrialCount})
                  </button>
                  <button
                    onClick={() => setImpactCategoryFilter('ENERGY')}
                    className={`py-1 px-1 rounded transition-all font-bold text-center truncate ${
                      impactCategoryFilter === 'ENERGY'
                        ? 'bg-amber-950 text-amber-300 border border-amber-500/50'
                        : 'text-slate-400 hover:text-white bg-space-950/60 border border-transparent'
                    }`}
                  >
                    ⚡ NRGI ({energyCount})
                  </button>
                </div>

                {/* Row 2: HEALTHCARE | TRANSPORTATION */}
                <div className="grid grid-cols-2 gap-1">
                  <button
                    onClick={() => setImpactCategoryFilter('HEALTHCARE')}
                    className={`py-1 px-1 rounded transition-all font-bold text-center truncate ${
                      impactCategoryFilter === 'HEALTHCARE'
                        ? 'bg-rose-950 text-rose-300 border border-rose-500/50'
                        : 'text-slate-400 hover:text-white bg-space-950/60 border border-transparent'
                    }`}
                  >
                    🏥 HEALTH ({healthcareCount})
                  </button>
                  <button
                    onClick={() => setImpactCategoryFilter('TRANSPORTATION')}
                    className={`py-1 px-1 rounded transition-all font-bold text-center truncate ${
                      impactCategoryFilter === 'TRANSPORTATION'
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/50'
                        : 'text-slate-400 hover:text-white bg-space-950/60 border border-transparent'
                    }`}
                  >
                    🛣️ TRANS ({transportCount})
                  </button>
                </div>
              </div>
            </div>

            {/* Loading State */}
            {loadingImpact && (
              <div className="p-3 bg-space-900/60 rounded-xl border border-white/[0.04] flex items-center justify-center gap-2 text-xs text-cyan-400 font-mono animate-pulse">
                <Radio className="w-4 h-4 animate-spin text-cyan-400" />
                <span>Querying PostGIS Spatial Proximity...</span>
              </div>
            )}

            {/* Error State */}
            {!loadingImpact && errorImpact && (
              <div className="p-3 bg-red-950/40 border border-red-500/30 rounded-xl flex items-center justify-between text-xs text-red-300">
                <span className="font-medium font-mono">{errorImpact}</span>
                {onRetryImpact && (
                  <button
                    onClick={onRetryImpact}
                    className="px-2 py-1 bg-red-900/60 hover:bg-red-800 rounded border border-red-500/50 text-[10px] font-bold uppercase tracking-wider text-white"
                  >
                    Retry
                  </button>
                )}
              </div>
            )}

            {/* Empty State */}
            {!loadingImpact && !errorImpact && impactData && impactData.total_entities_found === 0 && (
              <div className="p-3 bg-space-900/40 border border-white/[0.06] rounded-xl flex flex-col gap-1 text-center">
                <span className="font-bold text-xs text-slate-300 font-mono">
                  NO POTENTIALLY EXPOSED ENTITIES
                </span>
                <span className="text-[11px] text-slate-500">
                  No entities were found within the selected {impactRadius} km assessment radius.
                </span>
              </div>
            )}

            {/* Domain-specific Empty States */}
            {!loadingImpact && !errorImpact && impactData && impactData.total_entities_found > 0 && impactCategoryFilter === 'ENERGY' && energyCount === 0 && (
              <div className="p-3 bg-space-900/40 border border-amber-500/20 rounded-xl flex flex-col gap-1 text-center font-mono">
                <span className="font-bold text-xs text-amber-300">
                  NO ENERGY ENTITIES WITHIN ASSESSMENT RADIUS
                </span>
                <span className="text-[11px] text-slate-500 font-sans">
                  No power plants or electrical substations were found within the selected {impactRadius} km assessment radius.
                </span>
              </div>
            )}

            {!loadingImpact && !errorImpact && impactData && impactData.total_entities_found > 0 && impactCategoryFilter === 'HEALTHCARE' && healthcareCount === 0 && (
              <div className="p-3 bg-space-900/40 border border-rose-500/20 rounded-xl flex flex-col gap-1 text-center font-mono">
                <span className="font-bold text-xs text-rose-300">
                  NO HEALTHCARE ENTITIES WITHIN ASSESSMENT RADIUS
                </span>
                <span className="text-[11px] text-slate-500 font-sans">
                  No hospitals or emergency medical facilities were found within the selected {impactRadius} km assessment radius.
                </span>
              </div>
            )}

            {!loadingImpact && !errorImpact && impactData && impactData.total_entities_found > 0 && impactCategoryFilter === 'TRANSPORTATION' && transportCount === 0 && (
              <div className="p-3 bg-space-900/40 border border-emerald-500/20 rounded-xl flex flex-col gap-1 text-center font-mono">
                <span className="font-bold text-xs text-emerald-300">
                  NO TRANSPORTATION ENTITIES WITHIN ASSESSMENT RADIUS
                </span>
                <span className="text-[11px] text-slate-500 font-sans">
                  No major highways, trunk roads, or railway corridors were found within the selected {impactRadius} km assessment radius.
                </span>
              </div>
            )}

            {/* Entities List */}
            {!loadingImpact && !errorImpact && impactData && filteredImpactEntities.length > 0 && (
              <div className="flex flex-col gap-2 max-h-56 overflow-y-auto pr-1">
                {filteredImpactEntities.map((entity) => {
                  const distFormatted = entity.distance_meters < 1000
                    ? `${entity.distance_meters.toFixed(1)} m`
                    : `${entity.distance_km.toFixed(2)} km`;

                  const cat = entity.entity_category;
                  const isEnergy = cat === 'ENERGY';
                  const isHosp = cat === 'HEALTHCARE';
                  const isTrans = cat === 'TRANSPORTATION';

                  const categoryIcon = isEnergy ? '⚡' : isHosp ? '🏥' : isTrans ? '🛣️' : '🏭';
                  const categoryBadge = cat || 'INDUSTRIAL';
                  const categoryBadgeStyle = isEnergy
                    ? 'bg-amber-950/80 text-amber-300 border-amber-500/40'
                    : isHosp
                    ? 'bg-rose-950/80 text-rose-300 border-rose-500/40'
                    : isTrans
                    ? 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40'
                    : 'bg-cyan-950/80 text-cyan-300 border-cyan-500/40';

                  const sensTier = entity.sensitivity_tier || 'MODERATE';
                  const sensColorClass = sensTier === 'CRITICAL'
                    ? 'bg-rose-950/90 text-rose-300 border-rose-500/50'
                    : sensTier === 'HIGH'
                    ? 'bg-amber-950/90 text-amber-300 border-amber-500/50'
                    : 'bg-cyan-950/90 text-cyan-300 border-cyan-500/50';

                  const footprintLabel = (entity.footprint_scale || 'STANDARD_FACILITY').replace('_', ' ');

                  return (
                    <div
                      key={`impact-entity-${entity.facility_id}`}
                      className="p-2.5 bg-space-900/90 border border-white/[0.08] hover:border-cyan-500/50 rounded-xl flex flex-col gap-2 transition-all"
                    >
                      <div className="flex flex-col gap-0.5">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white text-xs truncate max-w-[170px]" title={entity.display_label || entity.name || 'Unnamed Entity'}>
                            {categoryIcon} {entity.display_label || entity.name || 'Unnamed Entity'}
                          </span>
                          <div className="flex items-center gap-1">
                            <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase font-mono border ${categoryBadgeStyle}`}>
                              {categoryBadge}
                            </span>
                            <span className="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase font-mono bg-space-950 text-purple-300 border border-purple-500/40">
                              {entity.facility_type?.toUpperCase() || 'SITE'}
                            </span>
                          </div>
                        </div>

                        {/* Phase 3D Location Context Sub-label */}
                        {entity.location_context && (
                          <span className="text-[10px] text-cyan-300 font-mono flex items-center gap-1 pl-5">
                            📍 {entity.location_context}
                          </span>
                        )}
                      </div>

                      {/* Phase 2/3 Exposure & Sensitivity Profile Row */}
                      <div className="flex items-center justify-between gap-1 text-[10px] font-mono border-t border-b border-white/[0.04] py-1">
                        <div className="flex items-center gap-1.5">
                          <span className="text-slate-500 uppercase tracking-wider">SENSITIVITY:</span>
                          <span className={`px-1.5 py-0.5 rounded border font-bold ${sensColorClass}`}>
                            {sensTier}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-slate-500 uppercase tracking-wider">FOOTPRINT:</span>
                          <span className="text-slate-300 font-semibold uppercase">
                            {footprintLabel}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                        <span>Distance: <strong className="text-amber-400">{distFormatted}</strong></span>
                        <span className="text-slate-500">{entity.osm_id ? `OSM: ${entity.osm_id}` : `${entity.latitude.toFixed(4)}°, ${entity.longitude.toFixed(4)}°`}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Scientific Disclaimer */}
            <div className="p-2.5 bg-space-950/80 border border-white/[0.06] rounded-xl flex items-start gap-2 text-[10px] text-slate-400 font-mono leading-relaxed">
              <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <span>
                {impactData?.scientific_disclaimer || (
                  "Entities are identified by spatial proximity within the configured assessment radius. Proximity indicates potential exposure context and does not establish fire causality or confirmed impact."
                )}
              </span>
            </div>
          </div>
        )}

        {/* Trigger AI Deep Dive Button */}
        {isObservationView && currentObs && (
          <button
            onClick={() => onOpenAIWithContext(currentObs.id)}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-glow-cyan transition-all active:scale-98"
          >
            <Bot className="w-4 h-4" />
            <span>Launch AI Deep-Dive Investigation</span>
          </button>
        )}
      </div>
    </motion.aside>
  );
};
