import React, { useState, useMemo } from 'react';
import { MapPin, Search, X, Check, Database } from 'lucide-react';
import { AVAILABLE_LOCATIONS } from '../../data/locations';

export default function LocationPicker({ isOpen, onClose, onSelectLocation }) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredLocations = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return AVAILABLE_LOCATIONS;
    return AVAILABLE_LOCATIONS.filter((loc) =>
      loc.toLowerCase().includes(q)
    );
  }, [searchQuery]);

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
    <div className="fixed inset-0 z-50 bg-[#111111]/65 backdrop-blur-xs flex items-center justify-center p-3 sm:p-6">
      <div className="editorial-panel rounded-xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden text-[#111111] dark:text-[#F3EEE3]">
        <div className="p-4 sm:p-5 border-b border-[#E6DED0] dark:border-[#2F2B25] bg-[#F8F5EE] dark:bg-[#161513] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[#EAE3D5] dark:bg-[#22201D] border border-[#D4C9B6] dark:border-[#3A352E]">
              <MapPin className="w-4 h-4 text-[#D9541E]" />
            </div>
            <div>
              <h2 className="font-heading font-bold text-[#111111] dark:text-white text-sm sm:text-base flex items-center gap-2">
                <span>Available Bengaluru Locations</span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[#E6DED0] dark:bg-[#22201D] text-[#111111] dark:text-[#F3EEE3] border border-[#C9BFAE] dark:border-[#3A352E] tabular-nums">
                  {AVAILABLE_LOCATIONS.length} Areas
                </span>
              </h2>
              <p className="text-xs text-[#6B665E] dark:text-[#A69E92]">Select a neighborhood with historical benchmark data</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg text-[#6B665E] hover:text-[#111111] dark:hover:text-white hover:bg-[#EAE3D5] dark:hover:bg-[#22201D] transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 border-b border-[#E6DED0] dark:border-[#2F2B25] bg-[#F8F5EE] dark:bg-[#161513] space-y-2.5 shrink-0">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[#6B665E]" />
            <input
              type="text"
              autoFocus
              placeholder="Search localities (e.g. Koramangala, HSR, Indiranagar)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white dark:bg-[#22201D] border border-[#C9BFAE] dark:border-[#3A352E] rounded-lg pl-10 pr-12 py-2 text-xs sm:text-sm text-[#111111] dark:text-[#F3EEE3] placeholder-[#6B665E] focus:outline-none focus:border-[#D9541E]"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6B665E] hover:text-[#111111] dark:hover:text-white text-xs cursor-pointer"
              >
                Clear
              </button>
            )}
          </div>

          <div className="flex items-center justify-between text-[11px] text-[#6B665E] dark:text-[#A69E92] px-0.5">
            <span className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-[#D9541E]" />
              <span>Zomato Historical Benchmark Index</span>
            </span>
            <span className="font-semibold text-[#111111] dark:text-[#F3EEE3] tabular-nums">
              {filteredLocations.length} matches
            </span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          {Object.keys(groupedLocations).length === 0 ? (
            <div className="py-12 text-center space-y-2 text-[#6B665E] text-xs">
              <MapPin className="w-8 h-8 text-[#C9BFAE] mx-auto" />
              <p>No location found matching "{searchQuery}"</p>
            </div>
          ) : (
            Object.keys(groupedLocations)
              .sort()
              .map((letter) => (
                <div key={letter} className="space-y-2">
                  <div className="text-xs font-bold text-[#D9541E] border-b border-[#E6DED0] dark:border-[#2F2B25] pb-1">
                    {letter}
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {groupedLocations[letter].map((loc) => (
                      <button
                        key={loc}
                        onClick={() => handleLocationClick(loc)}
                        className="flex items-center justify-between p-2.5 rounded-lg bg-[#F8F5EE] dark:bg-[#22201D] hover:border-[#D9541E] text-[#111111] dark:text-[#F3EEE3] hover:text-[#D9541E] border border-[#E6DED0] dark:border-[#2F2B25] transition-colors text-xs text-left group cursor-pointer"
                      >
                        <span className="font-medium truncate">{loc}</span>
                        <Check className="w-3.5 h-3.5 text-[#D9541E] opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
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
