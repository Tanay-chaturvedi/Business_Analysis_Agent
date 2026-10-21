import React, { useState, useMemo } from 'react';
import { MapPin, Search, X, Check, Database } from 'lucide-react';
import { AVAILABLE_LOCATIONS } from '../../data/locations';

export default function LocationPicker({ isOpen, onClose, onSelectLocation }) {
  const [searchQuery, setSearchQuery] = useState('');

  // Filter locations based on query
  const filteredLocations = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return AVAILABLE_LOCATIONS;
    return AVAILABLE_LOCATIONS.filter((loc) =>
      loc.toLowerCase().includes(q)
    );
  }, [searchQuery]);

  // Group locations alphabetically by first character
  const groupedLocations = useMemo(() => {
    const groups = {};
    filteredLocations.forEach((loc) => {
      const firstChar = loc.charAt(0).toUpperCase();
      if (!groups[firstChar]) {
        groups[firstChar] = [];
      }
      groups[firstChar].push(loc);
    });
    return groups;
  }, [filteredLocations]);

  if (!isOpen) return null;

  const handleLocationClick = (loc) => {
    onSelectLocation(loc);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/70 dark:bg-black/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-6 animate-fade-in">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden text-slate-900 dark:text-slate-100 transition-colors">
        {/* Modal Top Header */}
        <div className="p-4 sm:p-5 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-600 dark:text-indigo-400">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-slate-900 dark:text-white text-base sm:text-lg flex items-center gap-2">
                Available Locations
                <span className="text-[10px] font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/20">
                  {AVAILABLE_LOCATIONS.length} Areas
                </span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">Choose a location from our historical dataset</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Sticky Search Bar & Info Banner */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-950/40 space-y-3 shrink-0">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              autoFocus
              placeholder="Search locations (e.g. kor, ind, white)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl pl-10 pr-10 py-2.5 text-xs sm:text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 text-xs cursor-pointer"
              >
                Clear
              </button>
            )}
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 px-1">
            <span className="flex items-center gap-1">
              <Database className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
              <span>Locations available in historical dataset</span>
            </span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">{filteredLocations.length} matches</span>
          </div>
        </div>

        {/* Scrollable Grouped Location List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          {Object.keys(groupedLocations).length === 0 ? (
            <div className="py-12 text-center space-y-2 text-slate-400 dark:text-slate-500 text-xs">
              <MapPin className="w-8 h-8 text-slate-300 dark:text-slate-700 mx-auto" />
              <p>No historical location found matching "{searchQuery}"</p>
            </div>
          ) : (
            Object.keys(groupedLocations)
              .sort()
              .map((letter) => (
                <div key={letter} className="space-y-2">
                  <div className="text-xs font-bold text-indigo-600 dark:text-indigo-400 border-b border-slate-200 dark:border-slate-800 pb-1">
                    {letter}
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {groupedLocations[letter].map((loc) => (
                      <button
                        key={loc}
                        onClick={() => handleLocationClick(loc)}
                        className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 hover:bg-indigo-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-white border border-slate-200 dark:border-slate-800/80 transition-all text-xs text-left group cursor-pointer"
                      >
                        <span className="font-medium truncate">{loc}</span>
                        <Check className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                      </button>
                    ))}
                  </div>
                </div>
              ))
          )}
        </div>
      </div>
    </div>
  );
}
