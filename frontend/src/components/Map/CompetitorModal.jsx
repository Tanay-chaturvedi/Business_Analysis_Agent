import React, { useState, useEffect } from 'react';
import { X, Star, MessageSquare, MapPin, Search, ExternalLink, Navigation } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet marker icons in React Vite build
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Helper component to center map smoothly on active competitor and trigger size invalidation
function MapController({ center }) {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
    if (center && center[0] && center[1]) {
      map.flyTo(center, 15, { duration: 1.2 });
    }
  }, [center, map]);
  return null;
}

export default function CompetitorModal({ isOpen, onClose, competitors = [], locationName = '' }) {
  const [selectedCompetitor, setSelectedCompetitor] = useState(null);
  const [searchFilter, setSearchFilter] = useState('');

  if (!isOpen) return null;

  // Filter competitors by search term
  const filteredCompetitors = competitors.filter((c) =>
    (c.name || '').toLowerCase().includes(searchFilter.toLowerCase())
  );

  // Determine center coordinates from competitors data
  const validCoords = competitors.filter(c => c.latitude && c.longitude);
  let defaultCenter = [12.9352, 77.6245]; // Koramangala, Bengaluru fallback
  if (validCoords.length > 0) {
    defaultCenter = [validCoords[0].latitude, validCoords[0].longitude];
  }

  const activeCenter = selectedCompetitor && selectedCompetitor.latitude && selectedCompetitor.longitude
    ? [selectedCompetitor.latitude, selectedCompetitor.longitude]
    : defaultCenter;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/70 dark:bg-black/80 backdrop-blur-md flex items-center justify-center p-2 sm:p-6 animate-fade-in">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-6xl h-[90vh] max-h-[90vh] flex flex-col shadow-2xl overflow-hidden text-slate-900 dark:text-slate-100 transition-colors">
        {/* Modal Top Header (Fixed at top) */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-950/60 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-slate-900 dark:text-white text-base sm:text-lg flex items-center gap-2">
                Competitor Discovery Map
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 dark:bg-slate-800 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-slate-700">
                  {competitors.length} Competitors Found
                </span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">{locationName || 'Target Market Area'}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Main Split Body */}
        <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 grid-rows-[256px_1fr] lg:grid-rows-1 overflow-hidden">
          {/* Left Column: Interactive Map Component */}
          <div className="lg:col-span-7 h-full relative bg-slate-100 dark:bg-slate-950 border-b lg:border-b-0 lg:border-r border-slate-200 dark:border-slate-800">
            {validCoords.length > 0 ? (
              <MapContainer center={defaultCenter} zoom={13} scrollWheelZoom={true} className="w-full h-full">
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MapController center={activeCenter} />

                {/* Target Location Center Marker */}
                <Marker position={defaultCenter}>
                  <Popup>
                    <div className="p-1 max-w-xs">
                      <h4 className="font-bold text-sm text-indigo-600 dark:text-indigo-400">Target Area Center</h4>
                      <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">{locationName || 'Selected Location'}</p>
                    </div>
                  </Popup>
                </Marker>

                {/* Competitors Markers */}
                {validCoords.map((comp, idx) => {
                  const isSel = selectedCompetitor?.name === comp.name;
                  return (
                    <Marker
                      key={idx}
                      position={[comp.latitude, comp.longitude]}
                    >
                      <Popup>
                        <div className="p-1 max-w-xs space-y-1 text-slate-900 dark:text-slate-100">
                          <div className="font-bold text-sm text-indigo-600 dark:text-indigo-300">{comp.name}</div>
                          <div className="flex items-center gap-2 text-xs">
                            <span className="flex items-center text-amber-500 font-bold">
                              <Star className="w-3 h-3 fill-amber-500 mr-0.5" />
                              {comp.rating || 'N/A'}
                            </span>
                            <span className="text-slate-500 dark:text-slate-400">({comp.review_count || 0} reviews)</span>
                          </div>
                          {comp.address && <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">{comp.address}</p>}
                        </div>
                      </Popup>
                    </Marker>
                  );
                })}
              </MapContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-full p-6 text-center space-y-2 text-slate-400">
                <MapPin className="w-10 h-10 text-slate-400 dark:text-slate-600" />
                <p className="text-xs font-semibold">Map Coordinates Unavailable</p>
                <p className="text-[11px] text-slate-500 max-w-xs">
                  Showing competitor list view on the right panel.
                </p>
              </div>
            )}

            {/* Map Overlay Filter Info Badge */}
            <div className="absolute bottom-3 left-3 z-[400] bg-white/90 dark:bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 text-[11px] text-slate-700 dark:text-slate-300 shadow-lg flex items-center gap-2">
              <Navigation className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
              <span>Click competitor in list to center map</span>
            </div>
          </div>

          {/* Right Column: Searchable Competitor List (Independently scrollable) */}
          <div className="lg:col-span-5 h-full min-h-0 flex flex-col overflow-hidden bg-white dark:bg-slate-900">
            {/* Search Input Bar (Fixed below header) */}
            <div className="p-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/40 shrink-0">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter competitors by name..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="w-full bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* Competitor Items List (Independently scrollable area) */}
            <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain p-3 space-y-2">
              {filteredCompetitors.length === 0 ? (
                <div className="py-12 text-center text-xs text-slate-500">
                  No competitors found matching "{searchFilter}".
                </div>
              ) : (
                filteredCompetitors.map((comp, idx) => {
                  const isSelected = selectedCompetitor?.name === comp.name;
                  return (
                    <div
                      key={idx}
                      onClick={() => setSelectedCompetitor(comp)}
                      className={`p-3 rounded-xl border transition-all cursor-pointer text-xs space-y-1.5 ${isSelected
                          ? 'bg-indigo-50 dark:bg-indigo-950/40 border-indigo-300 dark:border-indigo-500/50 shadow-sm'
                          : 'bg-slate-50 dark:bg-slate-950/40 hover:bg-slate-100 dark:hover:bg-slate-800/60 border-slate-200 dark:border-slate-800/60'
                        }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="font-bold text-slate-900 dark:text-slate-100 text-sm leading-snug">{comp.name}</h4>
                        <span className="flex items-center text-amber-500 font-bold text-xs shrink-0 bg-amber-50 dark:bg-amber-500/10 px-2 py-0.5 rounded border border-amber-200 dark:border-amber-500/20">
                          <Star className="w-3 h-3 fill-amber-500 mr-1" />
                          {comp.rating || 'N/A'}
                        </span>
                      </div>

                      {comp.address && (
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-1 flex items-center gap-1">
                          <MapPin className="w-3 h-3 shrink-0 text-slate-400" />
                          <span>{comp.address}</span>
                        </p>
                      )}

                      <div className="flex items-center justify-between pt-1 border-t border-slate-200/60 dark:border-slate-800/40 text-[10px] text-slate-500 dark:text-slate-400">
                        <span className="flex items-center gap-1">
                          <MessageSquare className="w-3 h-3 text-indigo-500" />
                          <span>{comp.review_count || 0} reviews</span>
                        </span>

                        {comp.user_ratings_total && (
                          <span>Total ratings: {comp.user_ratings_total}</span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
