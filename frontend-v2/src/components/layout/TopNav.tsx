import React, { useState, useEffect } from 'react';
import { 
  Satellite, 
  Clock, 
  Bot, 
  RefreshCw, 
  ShieldAlert, 
  Sparkles, 
  CheckCircle2, 
  SlidersHorizontal,
  ChevronDown
} from 'lucide-react';
import { HealthStatus, RiskSummary } from '../../types';

interface TopNavProps {
  health: HealthStatus | null;
  riskSummary: RiskSummary | null;
  onOpenAI: () => void;
  onRefresh: () => void;
  onRunRiskEvaluation: () => void;
  loading: boolean;
  evaluatingRisk: boolean;
}

export const TopNav: React.FC<TopNavProps> = ({
  health,
  riskSummary,
  onOpenAI,
  onRefresh,
  onRunRiskEvaluation,
  loading,
  evaluatingRisk
}) => {
  const [timeUtc, setTimeUtc] = useState('');
  const [timeIst, setTimeIst] = useState('');

  useEffect(() => {
    const updateClocks = () => {
      const now = new Date();
      setTimeUtc(now.toUTCString().slice(17, 25) + ' UTC');
      setTimeIst(now.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false }) + ' IST');
    };
    updateClocks();
    const interval = setInterval(updateClocks, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-white/[0.08] bg-space-950/90 backdrop-blur-xl px-4 sm:px-6 flex items-center justify-between z-30 shrink-0 select-none">
      {/* Left: Brand & Identification */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500/20 to-blue-600/30 border border-cyan-500/40 flex items-center justify-center shadow-glow-cyan">
            <Satellite className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg sm:text-xl tracking-tight text-white font-display">
                AVISHKAR <span className="text-cyan-400">2.0</span>
              </span>
              <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[11px] font-bold bg-cyan-950/80 text-cyan-300 border border-cyan-500/30 uppercase font-mono">
                NTRO · SIH 26162
              </span>
              <span className="hidden md:inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-purple-950/80 text-purple-300 border border-purple-500/30 uppercase font-mono">
                SIH DEMO ENVIRONMENT · ML SHADOW MODE
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden md:block">Earth Observation & Industrial Thermal Intelligence</p>
          </div>
        </div>
      </div>

      {/* Center: Live Realtime Synchronized Clocks */}
      <div className="hidden lg:flex items-center gap-4 px-4 py-1.5 rounded-full bg-space-900/80 border border-white/[0.08] font-mono text-xs">
        <div className="flex items-center gap-1.5 text-slate-300">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400">ORBITAL TIME:</span>
          <span className="font-semibold text-slate-200">{timeUtc || '00:00:00 UTC'}</span>
        </div>
        <div className="h-3 w-px bg-slate-700" />
        <div className="flex items-center gap-1.5 text-slate-300">
          <span className="text-slate-400">GROUND IST:</span>
          <span className="font-semibold text-cyan-300">{timeIst || '00:00:00 IST'}</span>
        </div>
        <div className="h-3 w-px bg-slate-700" />
        <div className="flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-[11px] font-bold text-emerald-400 uppercase">TELEMETRY LIVE</span>
        </div>
      </div>

      {/* Right: Actions (AI Investigation + Risk Evaluation + Refresh) */}
      <div className="flex items-center gap-2.5">
        {/* Scientific Alert Disclaimer */}
        <div className="hidden xl:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-950/30 border border-amber-500/30 text-amber-300 text-xs font-medium">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
          <span>Thermal Anomaly ≠ Confirmed Fire</span>
        </div>

        {/* Re-Evaluate Risk Engine Button */}
        <button
          onClick={onRunRiskEvaluation}
          disabled={evaluatingRisk}
          className="hidden sm:flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-red-600/80 to-orange-600/80 hover:from-red-500 hover:to-orange-500 text-white text-xs font-semibold shadow-glow-red border border-red-400/40 transition-all active:scale-95 disabled:opacity-50"
          title="Execute Phase 7 Multi-Modal Risk Scoring Calculation"
        >
          <Sparkles className={`w-3.5 h-3.5 ${evaluatingRisk ? 'animate-spin' : ''}`} />
          <span>{evaluatingRisk ? 'Evaluating...' : 'Evaluate Risk'}</span>
        </button>

        {/* AI Investigation Trigger */}
        <button
          onClick={onOpenAI}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-cyan-950/80 hover:bg-cyan-900/90 text-cyan-300 border border-cyan-500/40 shadow-glow-cyan text-xs font-semibold transition-all active:scale-95"
        >
          <Bot className="w-4 h-4 text-cyan-400" />
          <span className="hidden sm:inline">AI Investigation</span>
        </button>

        {/* Global Telemetry Refresh */}
        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-2 rounded-lg bg-space-900 border border-white/[0.08] hover:border-cyan-500/40 text-slate-300 hover:text-cyan-300 transition-all active:scale-95"
          title="Refresh All Satellite Telemetry"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
        </button>
      </div>
    </header>
  );
};
