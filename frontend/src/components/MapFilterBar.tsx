import React, { useState } from 'react';
import { MapFilters } from '../types';
import { SlidersHorizontal, Layers, ChevronDown, ChevronUp, RotateCcw } from 'lucide-react';

interface MapFilterBarProps {
  filters: MapFilters;
  onChangeFilters: (updated: MapFilters) => void;
  onResetFilters: () => void;
}

export const MapFilterBar: React.FC<MapFilterBarProps> = ({ filters, onChangeFilters, onResetFilters }) => {
  const [open, setOpen] = useState(false);
  const [layerOpen, setLayerOpen] = useState(false);

  return (
    <div className="flex items-center gap-2 z-[999] select-none text-xs">
      {/* Quick Filter Toggle Button */}
      <div className="relative">
        <button
          onClick={() => { setOpen(!open); setLayerOpen(false); }}
          className={`px-2.5 py-1.5 rounded-md border flex items-center gap-1.5 font-medium shadow-lg backdrop-blur-md transition-colors ${
            open ? 'bg-slate-800 text-amber-400 border-amber-500/50' : 'bg-slate-900/90 text-slate-200 border-slate-700 hover:bg-slate-800'
          }`}
        >
          <SlidersHorizontal className="w-3.5 h-3.5 text-amber-400" />
          <span>Filters</span>
          {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>

        {/* Filter Popup Drawer */}
        {open && (
          <div className="absolute top-9 left-0 w-80 bg-slate-900/95 border border-slate-700/80 rounded-lg p-3 shadow-2xl backdrop-blur-md flex flex-col gap-2.5 text-slate-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
              <span className="font-bold text-slate-100 flex items-center gap-1">
                <SlidersHorizontal className="w-3.5 h-3.5 text-amber-400" />
                GIS Observations Filter
              </span>
              <button
                onClick={onResetFilters}
                className="text-[10px] text-slate-400 hover:text-amber-400 flex items-center gap-1"
                title="Reset all filters"
              >
                <RotateCcw className="w-3 h-3" />
                Reset
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[10px] text-slate-400 mb-0.5">Satellite</label>
                <select
                  value={filters.satellite}
                  onChange={(e) => onChangeFilters({ ...filters, satellite: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 text-[11px]"
                >
                  <option value="ALL">All Satellites</option>
                  <option value="VIIRS">VIIRS</option>
                  <option value="NOAA-20">NOAA-20</option>
                  <option value="NOAA-21">NOAA-21</option>
                  <option value="Suomi-NPP">Suomi-NPP</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] text-slate-400 mb-0.5">Confidence</label>
                <select
                  value={filters.confidence}
                  onChange={(e) => onChangeFilters({ ...filters, confidence: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 text-[11px]"
                >
                  <option value="ALL">All Confidence Tiers</option>
                  <option value="h">High (h)</option>
                  <option value="n">Nominal (n)</option>
                  <option value="l">Low (l)</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] text-slate-400 mb-0.5">Priority</label>
                <select
                  value={filters.priority}
                  onChange={(e) => onChangeFilters({ ...filters, priority: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 text-[11px]"
                >
                  <option value="ALL">All Priorities</option>
                  <option value="CRITICAL">Critical (&gt;85)</option>
                  <option value="HIGH">High (61-85)</option>
                  <option value="MEDIUM">Medium (31-60)</option>
                  <option value="LOW">Low (&le;30)</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] text-slate-400 mb-0.5">Facility Type</label>
                <select
                  value={filters.facilityType}
                  onChange={(e) => onChangeFilters({ ...filters, facilityType: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 text-[11px]"
                >
                  <option value="ALL">All Facility Types</option>
                  <option value="refinery">Refinery</option>
                  <option value="power_plant">Power Plant</option>
                  <option value="steel_works">Steel Works</option>
                  <option value="chemical">Chemical Plant</option>
                </select>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center text-[10px] text-slate-400 mb-1">
                <span>Min FRP Threshold: <strong className="text-amber-400 font-mono">{filters.minFrp} MW</strong></span>
                <span>Max FRP Threshold: <strong className="text-red-400 font-mono">{filters.maxFrp} MW</strong></span>
              </div>
              <input
                type="range"
                min={0}
                max={500}
                step={5}
                value={filters.minFrp}
                onChange={(e) => onChangeFilters({ ...filters, minFrp: Number(e.target.value) })}
                className="w-full accent-amber-500 bg-slate-950 h-1.5 rounded cursor-pointer"
              />
            </div>
          </div>
        )}
      </div>

      {/* Layer Control Dropdown */}
      <div className="relative">
        <button
          onClick={() => { setLayerOpen(!layerOpen); setOpen(false); }}
          className={`px-2.5 py-1.5 rounded-md border flex items-center gap-1.5 font-medium shadow-lg backdrop-blur-md transition-colors ${
            layerOpen ? 'bg-slate-800 text-purple-300 border-purple-500/50' : 'bg-slate-900/90 text-slate-200 border-slate-700 hover:bg-slate-800'
          }`}
        >
          <Layers className="w-3.5 h-3.5 text-purple-400" />
          <span>Layers</span>
          {layerOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>

        {layerOpen && (
          <div className="absolute top-9 left-0 w-64 bg-slate-900/95 border border-slate-700/80 rounded-lg p-3 shadow-2xl backdrop-blur-md flex flex-col gap-2 text-slate-200">
            <span className="font-bold text-slate-100 border-b border-slate-800 pb-1 flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-purple-400" />
              GIS Map Layers
            </span>

            <div className="flex flex-col gap-1.5 pt-1 text-[11px]">
              <label className="flex items-center gap-2 cursor-pointer text-slate-200">
                <input
                  type="checkbox"
                  checked={filters.showAnomalies}
                  onChange={(e) => onChangeFilters({ ...filters, showAnomalies: e.target.checked })}
                  className="rounded border-slate-700 bg-slate-950 text-amber-500 accent-amber-500"
                />
                <span>NASA FIRMS Thermal Anomalies</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-slate-200">
                <input
                  type="checkbox"
                  checked={filters.showFacilities}
                  onChange={(e) => onChangeFilters({ ...filters, showFacilities: e.target.checked })}
                  className="rounded border-slate-700 bg-slate-950 text-purple-500 accent-purple-500"
                />
                <span>OSM Industrial Facilities</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-slate-200">
                <input
                  type="checkbox"
                  checked={filters.showVectors}
                  onChange={(e) => onChangeFilters({ ...filters, showVectors: e.target.checked })}
                  className="rounded border-slate-700 bg-slate-950 text-blue-500 accent-blue-500"
                />
                <span>Facility Proximity Vectors</span>
              </label>

              <div className="border-t border-slate-800 pt-1.5 flex flex-col gap-1 text-[10px] text-slate-500">
                <span className="font-semibold text-slate-400 uppercase tracking-wide text-[9px]">Experimental / Planned Layers</span>
                <label className="flex items-center gap-2 opacity-50 cursor-not-allowed">
                  <input type="checkbox" disabled />
                  <span>Land Cover (Coming Soon)</span>
                </label>
                <label className="flex items-center gap-2 opacity-50 cursor-not-allowed">
                  <input type="checkbox" disabled />
                  <span>Optical Imagery (Coming Soon)</span>
                </label>
                <label className="flex items-center gap-2 opacity-50 cursor-not-allowed">
                  <input type="checkbox" disabled />
                  <span>Population Density (Coming Soon)</span>
                </label>
                <label className="flex items-center gap-2 opacity-50 cursor-not-allowed">
                  <input type="checkbox" disabled />
                  <span>Weather Radar (Coming Soon)</span>
                </label>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MapFilterBar;
