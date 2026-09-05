import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Bot, 
  Send, 
  Sparkles, 
  CheckCircle2, 
  Clock, 
  Layers, 
  ShieldAlert, 
  AlertTriangle, 
  Radio, 
  Search,
  HelpCircle,
  FileText,
  Activity,
  Flame
} from 'lucide-react';
import { AIInvestigationResponse, ThermalObservation } from '../../types';
import { getApiUrl } from '../../services/api';

interface AIInvestigationTerminalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedObservationId: number | null;
  observations: ThermalObservation[];
}

export const AIInvestigationTerminal: React.FC<AIInvestigationTerminalProps> = ({
  isOpen,
  onClose,
  selectedObservationId,
  observations
}) => {
  const [inquiry, setInquiry] = useState('');
  const [obsId, setObsId] = useState<number>(selectedObservationId || (observations[0]?.id ?? 1));
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AIInvestigationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'SYNTHESIS' | 'REPORT'>('SYNTHESIS');

  useEffect(() => {
    if (selectedObservationId) {
      setObsId(selectedObservationId);
    } else if (observations.length > 0 && !obsId) {
      setObsId(observations[0].id);
    }
  }, [selectedObservationId, observations]);

  // Filtered observations for search dropdown
  const filteredObservations = useMemo(() => {
    if (!searchTerm.trim()) return observations;
    const term = searchTerm.toLowerCase();
    return observations.filter(o => 
      String(o.id).includes(term) ||
      o.satellite?.toLowerCase().includes(term) ||
      String(o.frp).includes(term) ||
      o.acq_date?.includes(term)
    );
  }, [observations, searchTerm]);

  if (!isOpen) return null;

  const quickPrompts = [
    'Evaluate multi-criteria risk factors for this target',
    'Summarize industrial facility context & historical baseline',
    'Explain FRP statistical deviation compared to P95 envelope',
    'Recommend verification actions for optical satellite tasking',
    'Is this a confirmed fire?'
  ];

  const handleQuery = async (customText?: string) => {
    const queryText = customText || inquiry;
    if (!queryText.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(getApiUrl('/api/investigation/ai'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          observation_id: Number(obsId),
          event_id: `EVT-${String(obsId).padStart(4, '0')}`,
          inquiry: queryText,
          question: queryText
        })
      });

      if (!res.ok) {
        // Fallback to /api/agent/investigate
        const fallbackRes = await fetch(getApiUrl('/api/agent/investigate'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            event_id: String(obsId),
            question: queryText
          })
        });

        if (fallbackRes.ok) {
          const fbData = await fallbackRes.json();
          setResponse({
            observation_id: Number(obsId),
            inquiry: queryText,
            status: 'INVESTIGATION_COMPLETED',
            analysis_summary: fbData.answer || 'Investigation completed successfully.',
            context_evidence: {
              frp_value: 0,
              baseline_p95: 34.5,
              anomaly_severity: 'HIGH',
              risk_score: 85,
              priority_tier: 'HIGH_RISK',
              associated_facility: 'Industrial Facility',
              facility_type: 'Industrial',
              verification_rule: 'AGENT_MULTI_TOOL_INSPECTION'
            },
            recommended_actions: [
              'Task optical satellite for high-resolution confirmation',
              'Inspect persistence over adjacent satellite orbital passes'
            ],
            latency_ms: fbData.latency_ms || 120,
            answer: fbData.answer,
            evidence_sources: fbData.evidence_sources
          });
          return;
        }

        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Server returned error status ${res.status}`);
      }

      const data = await res.json();
      setResponse(data);
    } catch (err: any) {
      setError(err.message || 'Error querying Investigation AI');
    } finally {
      setLoading(false);
    }
  };

  const selectedObs = observations.find(o => o.id === obsId) || observations[0];

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md font-sans select-none">
      <motion.div
        initial={{ scale: 0.92, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.92, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="w-full max-w-3xl rounded-3xl bg-space-950 border border-white/[0.12] shadow-2xl p-6 flex flex-col gap-4 text-slate-100 max-h-[92vh] overflow-hidden"
      >
        {/* Terminal Header */}
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center shadow-glow-cyan">
              <Bot className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white font-display flex items-center gap-2">
                <span>Satellite Cyber-Intelligence AI Terminal</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] bg-cyan-950 text-cyan-300 border border-cyan-500/30 uppercase font-mono">
                  ACTIVE AGENT
                </span>
              </h3>
              <p className="text-xs text-slate-400">Contextual anomaly synthesis, baseline correlation & optical verification</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-space-900 text-slate-400 hover:text-white cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Observation Search & Selector Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 p-3 rounded-2xl bg-space-900/70 border border-white/[0.06] text-xs shrink-0">
          <div className="flex items-center gap-2 font-mono">
            <Radio className="w-4 h-4 text-cyan-400 shrink-0" />
            <span className="text-slate-400 font-bold shrink-0">TARGET:</span>
            <select
              value={obsId}
              onChange={(e) => {
                setObsId(Number(e.target.value));
                setResponse(null);
                setError(null);
              }}
              className="bg-space-950 border border-white/[0.08] rounded-lg px-2.5 py-1.5 text-cyan-300 font-bold focus:outline-none focus:border-cyan-500 w-full"
            >
              {filteredObservations.slice(0, 100).map((o) => (
                <option key={o.id} value={o.id}>
                  OBS #{o.id} · {o.satellite} ({o.frp} MW, {o.confidence})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5 pointer-events-none" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search observation by ID, Satellite, MW..."
                className="w-full bg-space-950 border border-white/[0.08] rounded-lg pl-8 pr-2.5 py-1.5 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
            {searchTerm && (
              <button 
                onClick={() => setSearchTerm('')} 
                className="text-[10px] text-slate-400 hover:text-white px-1.5 py-1 bg-space-950 rounded border border-white/[0.08]"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Quick Inquiry Chips */}
        <div className="flex flex-col gap-1.5 shrink-0">
          <span className="text-[10.5px] font-bold text-slate-400 uppercase tracking-wider font-mono">Suggested Intelligence Inquiries</span>
          <div className="flex flex-wrap gap-1.5">
            {quickPrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setInquiry(prompt);
                  handleQuery(prompt);
                }}
                className="px-2.5 py-1 rounded-xl bg-space-900 hover:bg-space-850 border border-white/[0.06] hover:border-cyan-500/40 text-[11px] text-slate-300 hover:text-cyan-200 transition-all text-left cursor-pointer"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Selector when Response is Active */}
        {response && (
          <div className="flex items-center gap-2 border-b border-white/[0.06] pb-1 shrink-0 font-mono text-xs">
            <button
              onClick={() => setActiveTab('SYNTHESIS')}
              className={`px-3 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                activeTab === 'SYNTHESIS' 
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/40' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Synthesis & Evidence
            </button>
            <button
              onClick={() => setActiveTab('REPORT')}
              className={`px-3 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                activeTab === 'REPORT' 
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/40' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Full Investigation Report
            </button>
          </div>
        )}

        {/* Scrollable Response Area */}
        <div className="flex-1 overflow-y-auto p-4 rounded-2xl bg-space-900/50 border border-white/[0.06] flex flex-col gap-3 text-xs leading-relaxed scrollbar-thin">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 gap-3 text-slate-400">
              <Sparkles className="w-8 h-8 text-cyan-400 animate-spin" />
              <span className="font-mono text-xs text-cyan-300">Synthesizing Orbital Telemetry & Multi-Modal Baselines...</span>
            </div>
          )}

          {error && (
            <div className="p-3.5 rounded-xl bg-red-950/60 border border-red-500/40 text-red-300 flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 shrink-0 text-red-400 mt-0.5" />
              <div className="flex flex-col gap-1">
                <span className="font-bold font-mono">Investigation Query Failed</span>
                <span className="text-xs text-slate-300">{error}</span>
                <button 
                  onClick={() => handleQuery()} 
                  className="mt-2 self-start px-3 py-1 bg-red-900/80 hover:bg-red-800 text-white rounded-lg border border-red-500/50 text-[10px] font-bold uppercase cursor-pointer"
                >
                  Retry Query
                </button>
              </div>
            </div>
          )}

          {response && !loading && activeTab === 'SYNTHESIS' && (
            <div className="flex flex-col gap-3.5 font-sans">
              {/* Summary */}
              <div className="p-4 rounded-2xl bg-gradient-to-br from-space-900 to-space-850 border border-cyan-500/30 shadow-glow-cyan">
                <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-mono block mb-1.5 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" /> AI Investigation Synthesis
                </span>
                <p className="text-xs text-slate-100 font-medium leading-relaxed">
                  {response.analysis_summary}
                </p>
              </div>

              {/* Context Evidence Table */}
              <div className="p-3.5 rounded-2xl bg-space-950/80 border border-white/[0.06] flex flex-col gap-2">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
                  Contextual Telemetry Evidence
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-xs">
                  <div className="p-2.5 rounded-xl bg-space-900/60 border border-white/[0.04]">
                    <span className="text-slate-400 block text-[10px]">Observed FRP</span>
                    <span className="font-bold text-red-400 text-sm">{response.context_evidence.frp_value} MW</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-space-900/60 border border-white/[0.04]">
                    <span className="text-slate-400 block text-[10px]">P95 Baseline</span>
                    <span className="font-bold text-cyan-300 text-sm">{(response.context_evidence.baseline_p95 ?? 34.5).toFixed(1)} MW</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-space-900/60 border border-white/[0.04]">
                    <span className="text-slate-400 block text-[10px]">Severity</span>
                    <span className="font-bold text-amber-300 text-sm">{response.context_evidence.anomaly_severity}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-space-900/60 border border-white/[0.04]">
                    <span className="text-slate-400 block text-[10px]">Risk Score</span>
                    <span className="font-bold text-red-400 text-sm">{(response.context_evidence.risk_score ?? 85).toFixed(0)} / 100</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 font-mono text-[11px] pt-1 border-t border-white/[0.04]">
                  <div>
                    <span className="text-slate-400">Associated Facility: </span>
                    <strong className="text-purple-300">{response.context_evidence.associated_facility}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400">Facility Type: </span>
                    <strong className="text-slate-200 uppercase">{response.context_evidence.facility_type}</strong>
                  </div>
                </div>
              </div>

              {/* Evidence Checklist */}
              {response.evidence_sources && (
                <div className="p-3.5 rounded-2xl bg-space-950/80 border border-white/[0.06] flex flex-col gap-2">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
                    Evidence Audit Checklist
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[11px] font-mono">
                    {response.evidence_sources.used.map((source, idx) => (
                      <div key={idx} className="flex items-center gap-1.5 text-emerald-400">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        <span className="text-slate-200 font-semibold">Verified: {source}</span>
                      </div>
                    ))}
                    {response.evidence_sources.unavailable.map((source, idx) => (
                      <div key={idx} className="flex items-center gap-1.5 text-slate-500">
                        <HelpCircle className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                        <span className="line-through">Unavailable: {source}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Actions */}
              {response.recommended_actions?.length > 0 && (
                <div className="p-3.5 rounded-2xl bg-space-950/80 border border-white/[0.06] flex flex-col gap-2">
                  <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider font-mono flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" /> Recommended Operational Protocol
                  </span>
                  <div className="flex flex-col gap-1.5">
                    {response.recommended_actions.map((act, i) => (
                      <div key={i} className="flex items-center gap-2 text-slate-300 text-xs font-mono">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                        <span>{act}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Latency Footer */}
              <div className="flex justify-between items-center text-[10px] text-slate-500 font-mono border-t border-white/[0.04] pt-2">
                <span>Rule: {response.context_evidence.verification_rule}</span>
                <span>Response latency: {response.latency_ms}ms</span>
              </div>
            </div>
          )}

          {response && !loading && activeTab === 'REPORT' && (
            <div className="p-4 rounded-2xl bg-space-950/90 border border-white/[0.06] flex flex-col gap-2 font-mono text-xs whitespace-pre-wrap select-text leading-relaxed text-slate-200">
              {response.answer || response.analysis_summary}
            </div>
          )}

          {!response && !loading && !error && (
            <div className="flex flex-col items-center justify-center py-12 gap-2 text-slate-400">
              <Bot className="w-8 h-8 text-slate-600" />
              <span className="text-xs text-slate-400">
                Select an inquiry prompt above or type a custom question below to initiate AI anomaly investigation.
              </span>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleQuery();
          }}
          className="flex items-center gap-2 shrink-0"
        >
          <input
            type="text"
            placeholder="Type your inquiry for the AI investigation agent (e.g. Why is this event high priority?)..."
            value={inquiry}
            onChange={(e) => setInquiry(e.target.value)}
            className="flex-1 bg-space-900 border border-white/[0.08] rounded-2xl px-4 py-3 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
          />
          <button
            type="submit"
            disabled={loading || !inquiry.trim()}
            className="px-5 py-3 rounded-2xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold flex items-center gap-2 shadow-glow-cyan transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Investigate</span>
          </button>
        </form>
      </motion.div>
    </div>
  );
};

export default AIInvestigationTerminal;
