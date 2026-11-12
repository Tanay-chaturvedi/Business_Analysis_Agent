import React, { useState, useEffect } from 'react';
import { X, Star, MessageSquare, MapPin, Search, Navigation } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

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

  const filteredCompetitors = competitors.filter((c) =>
    (c.name || '').toLowerCase().includes(searchFilter.toLowerCase())
  );

  const validCoords = competitors.filter((c) => c.latitude && c.longitude);
  let defaultCenter = [12.9352, 77.6245];
  if (validCoords.length > 0) {
    defaultCenter = [validCoords[0].latitude, validCoords[0].longitude];
  }

  const activeCenter =
    selectedCompetitor && selectedCompetitor.latitude && selectedCompetitor.longitude
      ? [selectedCompetitor.latitude, selectedCompetitor.longitude]
      : defaultCenter;

  return (
    <div className="fixed inset-0 z-50 bg-[#111111]/65 backdrop-blur-xs flex items-center justify-center p-2 sm:p-6">
      <div className="editorial-panel rounded-xl w-full max-w-6xl h-[90vh] max-h-[90vh] flex flex-col shadow-2xl overflow-hidden text-[#111111] dark:text-[#F3EEE3]">
        {/* Modal Header */}
        <div className="p-4 border-b border-[#E6DED0] dark:border-[#2F2B25] flex items-center justify-between bg-[#F8F5EE] dark:bg-[#161513] shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[#EAE3D5] dark:bg-[#22201D] border border-[#D4C9B6] dark:border-[#3A352E]">
              <MapPin className="w-4 h-4 text-[#D9541E]" />
            </div>
            <div>
              <h2 className="font-heading font-bold text-[#111111] dark:text-white text-sm sm:text-base flex items-center gap-2">
                <span>Competitor Map</span>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-[#E6DED0] dark:bg-[#22201D] text-[#111111] dark:text-[#F3EEE3] border border-[#C9BFAE] dark:border-[#3A352E] tabular-nums">
                  {competitors.length} found
                </span>
              </h2>
              <p className="text-xs text-[#6B665E] dark:text-[#A69E92]">{locationName || 'Target Market Area'}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg text-[#6B665E] hover:text-[#111111] dark:hover:text-white hover:bg-[#EAE3D5] dark:hover:bg-[#22201D] transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Split Body */}
        <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 grid-rows-[256px_1fr] lg:grid-rows-1 overflow-hidden">
          <div className="lg:col-span-7 h-full relative bg-[#EAE3D5] dark:bg-[#1A1917] border-b lg:border-b-0 lg:border-r border-[#E6DED0] dark:border-[#2F2B25]">
            {validCoords.length > 0 ? (
              <MapContainer center={defaultCenter} zoom={13} scrollWheelZoom={true} className="w-full h-full">
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MapController center={activeCenter} />

                <Marker position={defaultCenter}>
                  <Popup>
                    <div className="p-1 max-w-xs">
                      <h4 className="font-bold text-sm text-[#D9541E]">Target Area Center</h4>
                      <p className="text-xs text-[#6B665E] mt-1">{locationName || 'Selected Location'}</p>
                    </div>
                  </Popup>
                </Marker>

                {validCoords.map((comp, idx) => (
                  <Marker key={idx} position={[comp.latitude, comp.longitude]}>
                    <Popup>
                      <div className="p-1 max-w-xs space-y-1">
                        <div className="font-bold text-sm text-[#111111] dark:text-white">{comp.name}</div>
                        <div className="flex items-center gap-2 text-xs">
                          <span className="flex items-center text-[#D9541E] font-bold">
                            <Star className="w-3 h-3 fill-[#D9541E] mr-0.5" />
                            {comp.rating || 'N/A'}
                          </span>
                          <span className="text-[#6B665E]">({comp.review_count || 0} reviews)</span>
                        </div>
                        {comp.address && <p className="text-[11px] text-[#6B665E] line-clamp-2">{comp.address}</p>}
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-full p-6 text-center space-y-2 text-[#6B665E]">
                <MapPin className="w-9 h-9 text-[#C9BFAE]" />
                <p className="text-xs font-semibold">Map Coordinates Unavailable</p>
                <p className="text-[11px] max-w-xs">Showing retrieved competitor list on the adjacent panel.</p>
              </div>
            )}

            <div className="absolute bottom-3 left-3 z-[400] bg-white/95 dark:bg-[#111111]/95 px-3 py-1.5 rounded-lg border border-[#DDD4C3] dark:border-[#3A352E] text-[11px] text-[#111111] dark:text-[#F3EEE3] shadow-sm flex items-center gap-2">
              <Navigation className="w-3.5 h-3.5 text-[#D9541E]" />
              <span>Select a competitor row to focus map</span>
            </div>
          </div>

          <div className="lg:col-span-5 h-full min-h-0 flex flex-col overflow-hidden bg-white dark:bg-[#1A1917]">
            <div className="p-3 border-b border-[#E6DED0] dark:border-[#2F2B25] bg-[#F8F5EE] dark:bg-[#161513] shrink-0">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#6B665E]" />
                <input
                  type="text"
                  placeholder="Filter competitors..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="w-full bg-white dark:bg-[#22201D] border border-[#C9BFAE] dark:border-[#3A352E] rounded-lg pl-9 pr-3 py-2 text-xs text-[#111111] dark:text-[#F3EEE3] placeholder-[#6B665E] focus:outline-none focus:border-[#D9541E]"
                />
              </div>
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain p-3 space-y-2">
              {filteredCompetitors.length === 0 ? (
                <div className="py-12 text-center text-xs text-[#6B665E]">
                  No competitors matching "{searchFilter}".
                </div>
              ) : (
                filteredCompetitors.map((comp, idx) => {
                  const isSelected = selectedCompetitor?.name === comp.name;
                  return (
                    <div
                      key={idx}
                      onClick={() => setSelectedCompetitor(comp)}
                      className={`p-3 rounded-lg border transition-colors cursor-pointer text-xs space-y-1.5 ${
                        isSelected
                          ? 'bg-[#D9541E]/8 border-[#D9541E]'
                          : 'bg-[#F8F5EE] dark:bg-[#22201D] hover:border-[#C9BFAE] border-[#E6DED0] dark:border-[#2F2B25]'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="font-bold text-[#111111] dark:text-[#F3EEE3] text-sm leading-snug">{comp.name}</h4>
                        <span className="flex items-center text-[#D9541E] font-bold text-xs shrink-0 bg-white dark:bg-[#1A1917] px-2 py-0.5 rounded border border-[#E6DED0] dark:border-[#3A352E] tabular-nums">
                          <Star className="w-3 h-3 fill-[#D9541E] mr-1" />
                          {comp.rating || 'N/A'}
                        </span>
                      </div>

                      {comp.address && (
                        <p className="text-[11px] text-[#6B665E] dark:text-[#A69E92] line-clamp-1 flex items-center gap-1">
                          <MapPin className="w-3 h-3 shrink-0" />
                          <span>{comp.address}</span>
                        </p>
                      )}

                      <div className="flex items-center justify-between pt-1 border-t border-[#E6DED0] dark:border-[#2F2B25] text-[10px] text-[#6B665E] dark:text-[#A69E92] tabular-nums">
                        <span className="flex items-center gap-1">
                          <MessageSquare className="w-3 h-3 text-[#D9541E]" />
                          <span>{comp.review_count || 0} reviews</span>
                        </span>
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
