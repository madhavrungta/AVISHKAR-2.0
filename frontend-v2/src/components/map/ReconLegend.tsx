import React, { useState } from 'react';
import { Compass, ChevronDown, ChevronUp } from 'lucide-react';

export const ReconLegend: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  if (collapsed) {
    return (
      <button
        onClick={() => setCollapsed(false)}
        className="glass-panel-elevated px-3 py-1.5 rounded-xl border border-white/[0.08] shadow-2xl flex items-center gap-2 font-mono text-xs text-slate-300 hover:text-white pointer-events-auto backdrop-blur-2xl transition-all cursor-pointer hover:bg-space-850"
      >
        <Compass className="w-3.5 h-3.5 text-cyan-400" />
        <span className="font-bold text-[11px] uppercase tracking-wider font-display">Recon Legend</span>
        <span className="text-[9px] text-cyan-400/80 font-mono bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-500/30">WGS84</span>
        <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
      </button>
    );
  }

  return (
    <div className="glass-panel-elevated p-3 rounded-2xl border border-white/[0.08] shadow-2xl flex flex-col gap-2 font-mono text-[11px] select-none pointer-events-auto backdrop-blur-2xl w-64">
      <div 
        className="flex items-center justify-between border-b border-white/[0.06] pb-2 cursor-pointer hover:opacity-80 transition-opacity"
        onClick={() => setCollapsed(true)}
      >
        <span className="font-bold text-white uppercase tracking-wider flex items-center gap-1.5 text-xs font-display">
          <Compass className="w-3.5 h-3.5 text-cyan-400" />
          RECON LEGEND
        </span>
        <div className="flex items-center gap-1.5">
          <span className="text-[9px] text-cyan-400/90 font-mono bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-500/30">WGS84</span>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        </div>
      </div>

      <div className="flex flex-col gap-2 pt-0.5">
        <div className="flex items-center gap-2.5 text-slate-300">
          <div className="relative flex items-center justify-center w-3.5 h-3.5 shrink-0">
            <span className="absolute w-3.5 h-3.5 rounded-full bg-red-500/30 animate-ping" />
            <span className="relative w-2.5 h-2.5 rounded-full bg-red-500 border border-red-300 shadow-[0_0_8px_rgba(239,68,68,0.9)]" />
          </div>
          <span className="text-[11px]">Critical Anomaly / Spike</span>
        </div>

        <div className="flex items-center gap-2.5 text-slate-300">
          <div className="w-3.5 h-3.5 flex items-center justify-center shrink-0">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 border border-amber-300 shadow-[0_0_6px_rgba(245,158,11,0.6)]" />
          </div>
          <span className="text-[11px]">Thermal Anomaly (FIRMS)</span>
        </div>

        <div className="flex items-center gap-2.5 text-slate-300">
          <div className="w-3.5 h-3.5 flex items-center justify-center shrink-0">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-400 border border-purple-300 shadow-[0_0_6px_rgba(168,85,247,0.6)]" />
          </div>
          <span className="text-[11px]">Industrial Facility (OSM)</span>
        </div>

        <div className="flex items-center gap-2.5 text-slate-300">
          <div className="w-3.5 h-3.5 flex items-center justify-center shrink-0">
            <span className="w-3.5 border-t-2 border-dashed border-cyan-400" />
          </div>
          <span className="text-[11px]">Spatial Proximity Vector</span>
        </div>

        <div className="flex items-center gap-2.5 text-slate-300">
          <div className="relative flex items-center justify-center w-3.5 h-3.5 shrink-0">
            <span className="absolute w-3.5 h-3.5 rounded-full bg-cyan-400/40 animate-pulse" />
            <span className="relative w-2.5 h-2.5 rounded-full bg-cyan-300 border-2 border-white shadow-[0_0_10px_rgba(0,240,255,0.9)]" />
          </div>
          <span className="text-[11px]">Active Selected Target</span>
        </div>
      </div>
    </div>
  );
};

export default ReconLegend;
