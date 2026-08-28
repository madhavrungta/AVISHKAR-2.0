import React, { useState } from 'react';
import { IngestionResponse } from '../types';
import { Download, RefreshCw, AlertTriangle, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';

interface IngestionControlProps {
  onIngestComplete: () => void;
  apiKeyConfigured: boolean;
}

export const IngestionControl: React.FC<IngestionControlProps> = ({ onIngestComplete, apiKeyConfigured }) => {
  const [source, setSource] = useState('VIIRS_SNPP_NRT');
  const [area, setArea] = useState('68.0,6.0,97.0,37.0');
  const [days, setDays] = useState(1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [minimized, setMinimized] = useState(false);

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch('/api/ingestion/firms', {
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
      setError(err.message || 'Error executing ingestion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/95 border border-slate-700/80 rounded-lg shadow-2xl text-xs text-slate-200 backdrop-blur-md transition-all duration-200 select-none overflow-hidden max-w-md w-full">
      {/* Panel Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-slate-950/70 border-b border-slate-800 cursor-pointer" onClick={() => setMinimized(!minimized)}>
        <div className="flex items-center gap-2 font-bold text-slate-100">
          <Download className="w-3.5 h-3.5 text-amber-400" />
          <span>NASA FIRMS On-Demand Ingestion</span>
        </div>
        <button className="text-slate-400 hover:text-slate-200">
          {minimized ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>
      </div>

      {!minimized && (
        <div className="p-3">
          <form onSubmit={handleIngest} className="flex flex-col gap-2.5">
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-[10px] text-slate-400 font-semibold mb-0.5">Sensor Source</label>
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 focus:outline-none focus:border-amber-500 text-[11px]"
                >
                  <option value="VIIRS_SNPP_NRT">VIIRS Suomi-NPP</option>
                  <option value="VIIRS_NOAA20_NRT">VIIRS NOAA-20</option>
                  <option value="VIIRS_NOAA21_NRT">VIIRS NOAA-21</option>
                  <option value="MODIS_NRT">MODIS Terra/Aqua</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] text-slate-400 font-semibold mb-0.5">Bounding Box (W,S,E,N)</label>
                <input
                  type="text"
                  value={area}
                  onChange={(e) => setArea(e.target.value)}
                  placeholder="68.0,6.0,97.0,37.0"
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 focus:outline-none focus:border-amber-500 font-mono text-[11px]"
                />
              </div>

              <div>
                <label className="block text-[10px] text-slate-400 font-semibold mb-0.5">Day Range (1–5)</label>
                <input
                  type="number"
                  min={1}
                  max={5}
                  value={days}
                  onChange={(e) => setDays(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 focus:outline-none focus:border-amber-500 text-center font-mono text-[11px]"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !apiKeyConfigured}
              className={`w-full py-1.5 rounded font-semibold flex items-center justify-center gap-2 transition-all ${
                !apiKeyConfigured
                  ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
                  : loading
                  ? 'bg-amber-600 text-white opacity-80 cursor-wait'
                  : 'bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold shadow'
              }`}
            >
              {loading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Fetching Satellite Data...</span>
                </>
              ) : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  <span>Execute FIRMS API Ingestion</span>
                </>
              )}
            </button>
          </form>

          {/* Safety Notice if key missing */}
          {!apiKeyConfigured && (
            <div className="mt-2 p-2 bg-amber-950/60 border border-amber-500/40 rounded text-amber-300 text-[11px] flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
              <span>FIRMS_MAP_KEY is missing. Configure key in <code>backend/.env</code> to ingest live observations.</span>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mt-2 p-2 bg-red-950/70 border border-red-500/50 rounded text-red-300 text-[11px] flex items-start gap-1.5">
              <AlertTriangle className="w-4 h-4 shrink-0 text-red-400 mt-0.5" />
              <div>
                <span className="font-semibold text-red-200 block">● Ingestion Failed</span>
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Success Ingestion Status Feedback */}
          {result && (
            <div className="mt-2 p-2 bg-emerald-950/70 border border-emerald-500/50 rounded text-emerald-300 text-[11px] flex flex-col gap-1">
              <div className="flex items-center justify-between border-b border-emerald-500/30 pb-1">
                <span className="flex items-center gap-1 font-semibold text-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  ● Ingestion Successful
                </span>
                <span className="font-mono text-[10px] text-emerald-400">{result.records_ingested} Records</span>
              </div>
              <div className="grid grid-cols-2 gap-x-2 pt-0.5 text-[10.5px]">
                <div>Batch ID: <code className="text-emerald-200 font-mono">{result.batch_id}</code></div>
                <div>Valid: <span className="font-bold text-emerald-200">{result.validation_report.valid_records}</span> | Duplicates: <span className="font-bold text-emerald-200">{result.validation_report.duplicates}</span></div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default IngestionControl;
