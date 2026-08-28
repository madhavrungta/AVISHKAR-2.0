import React from 'react';
import { ShieldCheck, RefreshCw, AlertTriangle, Radio } from 'lucide-react';
import { HealthStatus } from '../types';

interface HeaderProps {
  onRunEvaluator: () => void;
  onRefresh: () => void;
  loading: boolean;
  health: HealthStatus | null;
}

export const Header: React.FC<HeaderProps> = ({ onRunEvaluator, onRefresh, loading, health }) => {
  const isOnline = health?.status === 'online';

  return (
    <header className="h-14 bg-slate-900 border-b border-slate-800 px-4 flex items-center justify-between shrink-0 shadow-lg z-30 select-none font-sans">
      {/* Left Branding */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-mono font-extrabold text-slate-100 tracking-wider text-sm">
                NTRO GIS-INTEL
              </span>
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-850 text-slate-400 border border-slate-700 font-mono font-bold">
                SIH 26162
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-semibold tracking-wide uppercase">
              Industrial Thermal Intelligence
            </p>
          </div>
        </div>

        <div className="h-8 w-px bg-slate-800" />

        <div className="hidden md:flex flex-col text-[11px]">
          <span className="text-slate-500 font-bold uppercase tracking-wider text-[9px]">Pipeline Status</span>
          <span className="text-slate-300 font-medium flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
            Phase 8: Multi-Modal Satellite Verification & Risk Scoring
          </span>
        </div>
      </div>

      {/* Center Scientific Warning */}
      <div className="hidden lg:flex bg-amber-950/20 border border-amber-500/30 text-amber-400 text-[10px] px-3.5 py-1 rounded font-mono font-bold tracking-wider uppercase select-none">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mr-1.5" />
        Thermal Anomaly ≠ Confirmed Fire
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3.5">
        {/* Connection status */}
        <div className="flex flex-col items-end text-[10px]">
          <span className="text-slate-500 font-bold uppercase tracking-wider text-[8px]">System Connection</span>
          <div className="flex items-center gap-1">
            <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'}`} />
            <span className={`font-mono font-bold tracking-wider uppercase ${isOnline ? 'text-emerald-400' : 'text-red-500'}`}>
              {isOnline ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
        </div>

        <button
          onClick={onRunEvaluator}
          disabled={loading}
          className="px-3 py-1.5 text-[11px] rounded bg-slate-850 hover:bg-slate-800 border border-slate-750 text-slate-200 transition-all flex items-center gap-1.5 font-mono uppercase font-bold disabled:opacity-50"
          title="Trigger Multi-Modal Risk Evaluation Job"
        >
          <ShieldCheck className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-purple-300' : 'text-purple-400'}`} />
          <span>Run Risk Evaluator</span>
        </button>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-1.5 rounded bg-slate-850 hover:bg-slate-800 border border-slate-750 text-slate-300 transition-colors"
          title="Refresh All Dashboard Data"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-amber-400' : ''}`} />
        </button>
      </div>
    </header>
  );
};

export default Header;
