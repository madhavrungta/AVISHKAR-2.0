import React, { useState } from 'react';
import { 
  SlidersHorizontal, 
  Layers, 
  ChevronDown, 
  ChevronUp, 
  RotateCcw, 
  Flame, 
  Building2, 
  Link2,
  ShieldAlert 
} from 'lucide-react';
import { MapFilters } from '../../types';

interface FloatingMapControlsProps {
  filters: MapFilters;
  onChangeFilters: (filters: MapFilters) => void;
  onResetFilters: () => void;
}

export const FloatingMapControls: React.FC<FloatingMapControlsProps> = ({
  filters,
  onChangeFilters,
  onResetFilters
}) => {
  const [filterOpen, setFilterOpen] = useState(false);
  const [layerOpen, setLayerOpen] = useState(false);

  const hasActiveFilters = 
    filters.satellite !== 'ALL' || 
    filters.confidence !== 'ALL' || 
    filters.priority !== 'ALL' || 
    filters.facilityType !== 'ALL' || 
    filters.minFrp > 0;

  return (
    <div className="flex items-center gap-2 z-[999] select-none text-xs font-mono pointer-events-auto">
      {/* 1. Telemetry Filters Button & Popover */}
      <div className="relative">
        <button
          onClick={() => { setFilterOpen(!filterOpen); setLayerOpen(false); }}
          className={`px-3 py-1.5 rounded-xl border flex items-center gap-2 font-bold tracking-wider uppercase shadow-[0_4px_20px_rgba(0,0,0,0.6)] backdrop-blur-xl transition-all cursor-pointer ${
            filterOpen || hasActiveFilters
              ? 'bg-space-950/95 text-amber-400 border-amber-500/60 shadow-[0_0_15px_rgba(245,158,11,0.25)]'
              : 'bg-space-950/85 text-slate-300 border-white/[0.08] hover:bg-space-900 hover:border-white/[0.15]'
          }`}
        >
          <SlidersHorizontal className="w-3.5 h-3.5 text-amber-400" />
          <span>Telemetry Filters</span>
          {hasActiveFilters && (
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
          )}
          {filterOpen ? <ChevronUp className="w-3 h-3 text-slate-400" /> : <ChevronDown className="w-3 h-3 text-slate-400" />}
        </button>

        {/* Telemetry Filter Popup Drawer */}
        {filterOpen && (
          <div className="absolute top-10 left-0 w-84 bg-space-950/95 border border-slate-700/80 rounded-2xl p-4 shadow-2xl backdrop-blur-2xl flex flex-col gap-3.5 text-slate-200 z-50 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-white/[0.06] pb-2 font-bold text-white">
              <span className="font-bold text-slate-100 flex items-center gap-1.5 text-[11px] uppercase tracking-wider font-display">
                <SlidersHorizontal className="w-3.5 h-3.5 text-amber-400" />
                Satellite Telemetry Filters
              </span>
              <button
                onClick={onResetFilters}
                className="text-[10px] text-slate-400 hover:text-amber-400 flex items-center gap-1 font-bold transition-colors uppercase tracking-wider cursor-pointer"
                title="Reset all filters to nominal defaults"
              >
                <RotateCcw className="w-3 h-3" />
                Reset
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              {/* Sensor Instrument */}
              <div>
                <label className="block text-[9.5px] font-bold text-slate-400 uppercase tracking-wider mb-1 font-mono">
                  Sensor Instrument
                </label>
                <select
                  value={filters.satellite}
                  onChange={(e) => onChangeFilters({ ...filters, satellite: e.target.value })}
                  className="w-full bg-space-900 border border-white/[0.08] rounded-xl px-2.5 py-1.5 text-slate-200 text-[11px] focus:outline-none focus:border-amber-500 font-mono"
                >
                  <option value="ALL">All</option>
                  <option value="VIIRS">VIIRS</option>
                  <option value="NOAA-20">NOAA-20 (VIIRS)</option>
                  <option value="NOAA-21">NOAA-21 (VIIRS)</option>
                  <option value="Suomi-NPP">Suomi-NPP</option>
                  <option value="MODIS">MODIS</option>
                </select>
              </div>

              {/* Detection Confidence */}
              <div>
                <label className="block text-[9.5px] font-bold text-slate-400 uppercase tracking-wider mb-1 font-mono">
                  Detection Confidence
                </label>
                <select
                  value={filters.confidence}
                  onChange={(e) => onChangeFilters({ ...filters, confidence: e.target.value })}
                  className="w-full bg-space-900 border border-white/[0.08] rounded-xl px-2.5 py-1.5 text-slate-200 text-[11px] focus:outline-none focus:border-amber-500 font-mono"
                >
                  <option value="ALL">All</option>
                  <option value="h">High (h)</option>
                  <option value="n">Nominal (n)</option>
                  <option value="l">Low (l)</option>
                </select>
              </div>

              {/* Risk Priority */}
              <div>
                <label className="block text-[9.5px] font-bold text-slate-400 uppercase tracking-wider mb-1 font-mono">
                  Risk Priority
                </label>
                <select
                  value={filters.priority}
                  onChange={(e) => onChangeFilters({ ...filters, priority: e.target.value })}
                  className="w-full bg-space-900 border border-white/[0.08] rounded-xl px-2.5 py-1.5 text-slate-200 text-[11px] focus:outline-none focus:border-amber-500 font-mono font-bold"
                >
                  <option value="ALL">All</option>
                  <option value="CRITICAL" className="text-red-400">Critical Verified (&gt;85)</option>
                  <option value="HIGH" className="text-orange-400">High Risk (61-85)</option>
                  <option value="MEDIUM" className="text-amber-400">Medium Risk (31-60)</option>
                  <option value="LOW" className="text-slate-400">Low Risk (&le;30)</option>
                </select>
              </div>

              {/* Facility Classification */}
              <div>
                <label className="block text-[9.5px] font-bold text-slate-400 uppercase tracking-wider mb-1 font-mono">
                  Facility Classification
                </label>
                <select
                  value={filters.facilityType}
                  onChange={(e) => onChangeFilters({ ...filters, facilityType: e.target.value })}
                  className="w-full bg-space-900 border border-white/[0.08] rounded-xl px-2.5 py-1.5 text-slate-200 text-[11px] focus:outline-none focus:border-amber-500 font-mono"
                >
                  <option value="ALL">All</option>
                  <option value="refinery">Petroleum Refinery</option>
                  <option value="power_plant">Thermal Power Plant</option>
                  <option value="steel_works">Steel Works</option>
                  <option value="chemical">Chemical / Petrochemical</option>
                  <option value="industrial">General Industrial</option>
                </select>
              </div>
            </div>

            {/* Min FRP Intensity Slider */}
            <div className="bg-space-900/80 p-2.5 rounded-xl border border-white/[0.06] flex flex-col gap-1.5">
              <div className="flex justify-between items-center text-[10px] text-slate-400">
                <span className="font-semibold uppercase tracking-wider font-mono">Min FRP Intensity</span>
                <span className="font-bold text-amber-400 font-mono">{filters.minFrp} MW</span>
              </div>
              <input
                type="range"
                min={0}
                max={300}
                step={5}
                value={filters.minFrp}
                onChange={(e) => onChangeFilters({ ...filters, minFrp: Number(e.target.value) })}
                className="w-full accent-amber-500 bg-space-950 h-1.5 rounded-lg cursor-pointer"
              />
              <div className="flex justify-between text-[8.5px] text-slate-500 font-mono">
                <span>0 MW</span>
                <span>150 MW</span>
                <span>300+ MW</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 2. GIS Layers Button & Popover */}
      <div className="relative">
        <button
          onClick={() => { setLayerOpen(!layerOpen); setFilterOpen(false); }}
          className={`px-3 py-1.5 rounded-xl border flex items-center gap-2 font-bold tracking-wider uppercase shadow-[0_4px_20px_rgba(0,0,0,0.6)] backdrop-blur-xl transition-all cursor-pointer ${
            layerOpen
              ? 'bg-space-950/95 text-cyan-400 border-cyan-500/60 shadow-[0_0_15px_rgba(0,240,255,0.25)]'
              : 'bg-space-950/85 text-slate-300 border-white/[0.08] hover:bg-space-900 hover:border-white/[0.15]'
          }`}
        >
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span>GIS Layers</span>
          {layerOpen ? <ChevronUp className="w-3 h-3 text-slate-400" /> : <ChevronDown className="w-3 h-3 text-slate-400" />}
        </button>

        {layerOpen && (
          <div className="absolute top-10 left-0 w-72 bg-space-950/95 border border-slate-700/80 rounded-2xl p-3.5 shadow-2xl backdrop-blur-2xl flex flex-col gap-2.5 text-slate-200 z-50 animate-in fade-in zoom-in-95 duration-200">
            <span className="font-bold text-slate-100 border-b border-white/[0.06] pb-1.5 flex items-center gap-1.5 text-[11px] uppercase tracking-wider font-display">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              GIS Geospatial Overlays
            </span>

            <div className="flex flex-col gap-1.5 pt-1 text-[11px]">
              <label className="flex items-center gap-2.5 cursor-pointer text-slate-200 hover:text-white p-1.5 rounded-xl hover:bg-space-900/60 transition-colors">
                <input
                  type="checkbox"
                  checked={filters.showAnomalies}
                  onChange={(e) => onChangeFilters({ ...filters, showAnomalies: e.target.checked })}
                  className="rounded border-slate-700 bg-space-950 text-amber-500 accent-amber-500 w-3.5 h-3.5"
                />
                <span className="flex items-center gap-1.5 font-medium font-mono text-[11px]">
                  <span className="w-2 h-2 rounded-full bg-amber-400" />
                  Thermal Anomalies (FIRMS)
                </span>
              </label>

              <label className="flex items-center gap-2.5 cursor-pointer text-slate-200 hover:text-white p-1.5 rounded-xl hover:bg-space-900/60 transition-colors">
                <input
                  type="checkbox"
                  checked={filters.showFacilities}
                  onChange={(e) => onChangeFilters({ ...filters, showFacilities: e.target.checked })}
                  className="rounded border-slate-700 bg-space-950 text-purple-500 accent-purple-500 w-3.5 h-3.5"
                />
                <span className="flex items-center gap-1.5 font-medium font-mono text-[11px]">
                  <span className="w-2 h-2 rounded-full bg-purple-400" />
                  Industrial Facilities (OSM)
                </span>
              </label>

              <label className="flex items-center gap-2.5 cursor-pointer text-slate-200 hover:text-white p-1.5 rounded-xl hover:bg-space-900/60 transition-colors">
                <input
                  type="checkbox"
                  checked={filters.showVectors}
                  onChange={(e) => onChangeFilters({ ...filters, showVectors: e.target.checked })}
                  className="rounded border-slate-700 bg-space-950 text-cyan-500 accent-cyan-500 w-3.5 h-3.5"
                />
                <span className="flex items-center gap-1.5 font-medium font-mono text-[11px]">
                  <span className="w-3 h-0.5 border-t-2 border-dashed border-cyan-400" />
                  Spatial Proximity Vectors
                </span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* 3. Quick Priority Chips */}
      <div className="hidden md:flex items-center gap-1.5 bg-space-950/85 border border-white/[0.08] px-2 py-1 rounded-xl backdrop-blur-xl text-[10px]">
        <span className="text-slate-500 font-bold uppercase text-[9px] mr-1">PRIORITY:</span>
        <button
          onClick={() => onChangeFilters({ ...filters, priority: 'ALL' })}
          className={`px-2 py-0.5 rounded-lg transition-all cursor-pointer ${
            filters.priority === 'ALL' 
              ? 'bg-space-800 text-white font-bold' 
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          ALL
        </button>
        <button
          onClick={() => onChangeFilters({ ...filters, priority: 'CRITICAL' })}
          className={`px-2 py-0.5 rounded-lg transition-all cursor-pointer ${
            filters.priority === 'CRITICAL' 
              ? 'bg-red-950 text-red-300 font-bold border border-red-500/40 shadow-glow-red' 
              : 'text-red-400/80 hover:text-red-300'
          }`}
        >
          CRITICAL
        </button>
        <button
          onClick={() => onChangeFilters({ ...filters, priority: 'HIGH' })}
          className={`px-2 py-0.5 rounded-lg transition-all cursor-pointer ${
            filters.priority === 'HIGH' 
              ? 'bg-orange-950 text-orange-300 font-bold border border-orange-500/40' 
              : 'text-orange-400/80 hover:text-orange-300'
          }`}
        >
          HIGH
        </button>
      </div>
    </div>
  );
};

export default FloatingMapControls;
