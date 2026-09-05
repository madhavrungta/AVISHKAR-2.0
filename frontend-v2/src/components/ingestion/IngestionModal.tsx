import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  X, 
  Satellite, 
  Radio, 
  Download, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle2, 
  Compass 
} from 'lucide-react';
import { IngestionResponse } from '../../types';
import { getApiUrl } from '../../services/api';

interface IngestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIngestComplete: () => void;
  apiKeyConfigured: boolean;
}

export const IngestionModal: React.FC<IngestionModalProps> = ({
  isOpen,
  onClose,
  onIngestComplete,
  apiKeyConfigured
}) => {
  const [source, setSource] = useState('VIIRS_SNPP_NRT');
  const [area, setArea] = useState('68.0,6.0,97.0,37.0');
  const [days, setDays] = useState(1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const presets = [
    { label: 'Pan-India Reconnaissance', bbox: '68.0,6.0,97.0,37.0' },
    { label: 'Gujarat Industrial Belt (Jamnagar)', bbox: '69.0,21.0,73.5,24.5' },
    { label: 'Mumbai-Trombay Refining Corridor', bbox: '72.7,18.8,73.2,19.3' },
    { label: 'Eastern Belt (Jamshedpur / Tata Steel)', bbox: '85.0,21.5,87.5,24.0' }
  ];

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(getApiUrl('/api/ingestion/firms'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source, area, days })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Ingestion request failed');
      }

      setResult(data);
      onIngestComplete();
    } catch (err: any) {
      setError(err.message || 'Error executing satellite ingestion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md font-sans select-none">
      <motion.div
        initial={{ scale: 0.92, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.92, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="w-full max-w-lg rounded-3xl bg-space-950 border border-white/[0.12] shadow-2xl p-6 flex flex-col gap-5 text-slate-100"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center shadow-glow-cyan">
              <Satellite className="w-5 h-5 text-cyan-400 animate-pulse" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white font-display">NASA FIRMS Satellite Data Downlink</h3>
              <p className="text-xs text-slate-400">On-demand sensor telemetry synchronization</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-space-900 text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Regional Quick Presets */}
        <div className="flex flex-col gap-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-cyan-400" />
            Regional Surveillance Presets
          </span>
          <div className="grid grid-cols-2 gap-2">
            {presets.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setArea(p.bbox)}
                className={`p-2 rounded-xl text-xs text-left border transition-all truncate ${
                  area === p.bbox
                    ? 'bg-cyan-950 border-cyan-500/60 text-cyan-300 font-bold shadow-glow-cyan'
                    : 'bg-space-900/80 border-white/[0.06] text-slate-400 hover:text-white hover:bg-space-850'
                }`}
                title={p.bbox}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Ingestion Parameters Form */}
        <form onSubmit={handleIngest} className="flex flex-col gap-4 border-t border-white/[0.06] pt-4">
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div>
              <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 font-mono">Sensor Source</label>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="w-full bg-space-900 border border-white/[0.08] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500 text-xs"
              >
                <option value="VIIRS_SNPP_NRT">VIIRS (Suomi-NPP)</option>
                <option value="VIIRS_NOAA20_NRT">VIIRS (NOAA-20)</option>
                <option value="VIIRS_NOAA21_NRT">VIIRS (NOAA-21)</option>
                <option value="MODIS_NRT">MODIS (Terra/Aqua)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 font-mono">Bounding Box</label>
              <input
                type="text"
                value={area}
                onChange={(e) => setArea(e.target.value)}
                placeholder="68.0,6.0,97.0,37.0"
                className="w-full bg-space-900 border border-white/[0.08] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500 text-xs font-mono"
              />
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 font-mono">Temporal Range</label>
              <select
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="w-full bg-space-900 border border-white/[0.08] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500 text-xs text-center"
              >
                <option value={1}>Last 24 Hours</option>
                <option value={2}>Last 48 Hours</option>
                <option value={3}>Last 72 Hours</option>
                <option value={5}>Last 5 Days</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !apiKeyConfigured}
            className={`w-full py-3 rounded-xl font-bold text-xs flex items-center justify-center gap-2 shadow-lg transition-all active:scale-98 ${
              !apiKeyConfigured
                ? 'bg-space-900 text-slate-500 border border-white/[0.06] cursor-not-allowed'
                : loading
                ? 'bg-cyan-900 text-cyan-200 cursor-wait'
                : 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-glow-cyan'
            }`}
          >
            {loading ? (
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

        {/* Safety Note if API Key missing */}
        {!apiKeyConfigured && (
          <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-500/30 text-amber-300 text-xs flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
            <span><code>FIRMS_MAP_KEY</code> not configured in <code>backend/.env</code>. Add your NASA key to stream live satellite passes.</span>
          </div>
        )}

        {/* Error Feedback */}
        {error && (
          <div className="p-3 rounded-xl bg-red-950/60 border border-red-500/40 text-red-300 text-xs flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-red-400 mt-0.5" />
            <div>
              <span className="font-bold text-red-200 block">Ingestion Error</span>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Ingestion Status Feedback & Fallback Notifications */}
        {result && (
          <div className={`p-3.5 rounded-2xl border text-xs flex flex-col gap-2 font-mono ${
            result.fallback_used
              ? 'bg-amber-950/60 border-amber-500/50 text-amber-200'
              : 'bg-emerald-950/50 border-emerald-500/40 text-emerald-300'
          }`}>
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-1.5">
              <span className="flex items-center gap-1.5 font-bold">
                <CheckCircle2 className={`w-4 h-4 ${result.fallback_used ? 'text-amber-400' : 'text-emerald-400'}`} />
                {result.fallback_used ? 'Orbital Telemetry Synchronized (Fallback Window)' : 'Satellite Telemetry Ingested'}
              </span>
              <span className="font-bold font-mono">{result.records_ingested} Records</span>
            </div>

            {/* Fallback Warning / Historical Window Banner */}
            {result.fallback_used && (
              <div className="p-2 rounded-xl bg-black/40 border border-amber-500/30 text-[11px] text-amber-300 font-sans leading-relaxed">
                {result.message || (
                  result.effective_days === 3
                    ? "No new detections in the last 24 hours. Recent observations from the last 3 days were loaded."
                    : result.effective_days === 5
                    ? "No new detections in the last 24 hours or 3 days. Expanded historical observations from the last 5 days were loaded."
                    : "No thermal anomalies were detected in the selected area during the last 5 days."
                )}
              </div>
            )}

            {!result.fallback_used && result.message && (
              <div className="text-[11px] text-emerald-200 font-sans">{result.message}</div>
            )}

            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>Batch ID: <span className="text-white">{result.batch_id}</span></div>
              <div>Valid: {result.validation_report.valid_records} | Dupes: {result.validation_report.duplicates}</div>
              <div>Requested Window: <span className="text-white">{result.requested_days || days}d</span></div>
              <div>Effective Window: <span className="text-white">{result.effective_days ? `${result.effective_days}d` : 'None'}</span></div>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};
