import React from 'react';
import { MapPin, Utensils, IndianRupee, Smartphone, CalendarCheck } from 'lucide-react';
import AIInsightsPanel from './AIInsightsPanel';

export default function LocationCard({ locationData, insights }) {
  if (!locationData) return null;

  const isFound = locationData.found !== false;
  const location = locationData.location || 'Unknown Location';

  if (!isFound) {
    return (
      <section className="editorial-panel rounded-xl p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#E6DED0] dark:border-[#2F2B25]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[#EAE3D5] dark:bg-[#22201D] border border-[#D4C9B6] dark:border-[#3A352E] text-[#111111] dark:text-[#F3EEE3]">
              <MapPin className="w-4 h-4 text-[#D9541E]" />
            </div>
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#6B665E] dark:text-[#A69E92]">
                01 · Market Geography
              </div>
              <h3 className="font-heading font-bold text-[#111111] dark:text-[#F3EEE3] text-sm sm:text-base">
                Location Analysis — {location}
              </h3>
            </div>
          </div>
          <span className="text-[11px] font-semibold px-2.5 py-1 rounded-md bg-[#B4690E]/10 text-[#B4690E] dark:text-[#E09F3E] border border-[#B4690E]/25">
            Historical Data Unavailable
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {['Historical Restaurants', 'Median Cost for Two', 'Online Ordering Rate', 'Table Booking Rate'].map((label, idx) => (
            <div key={idx} className="editorial-subcard p-3.5 rounded-lg">
              <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] mb-1">{label}</div>
              <div className="text-lg font-bold text-[#6B665E] dark:text-[#7D766C] tabular-nums">N/A</div>
            </div>
          ))}
        </div>

        <div className="p-3 bg-[#F8F5EE] dark:bg-[#1E1C19] rounded-lg border border-[#E6DED0] dark:border-[#2F2B25] text-xs text-[#6B665E] dark:text-[#A69E92]">
          No historical restaurant benchmark records exist in the Bengaluru dataset for "{location}". Live Google Places competitor scan and financial simulations remain active.
        </div>

        <AIInsightsPanel insights={insights} subtitle="Location Context" />
      </section>
    );
  }

  const {
    historical_restaurant_count = locationData.restaurant_count || 0,
    location_median_cost = 0,
    historical_online_order_rate,
    location_online_order_rate,
    online_order_rate,
    historical_table_booking_rate,
    location_book_table_rate,
    book_table_rate,
    top_cuisines = [],
    top_rest_types = [],
  } = locationData;

  const rawOnlineRate = historical_online_order_rate ?? location_online_order_rate ?? online_order_rate ?? 0;
  const rawTableRate = historical_table_booking_rate ?? location_book_table_rate ?? book_table_rate ?? 0;

  const onlineOrderPct = (rawOnlineRate * 100).toFixed(1);
  const tableBookingPct = (rawTableRate * 100).toFixed(1);

  return (
    <section className="editorial-panel rounded-xl p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#E6DED0] dark:border-[#2F2B25]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#EAE3D5] dark:bg-[#22201D] border border-[#D4C9B6] dark:border-[#3A352E] text-[#111111] dark:text-[#F3EEE3]">
            <MapPin className="w-4 h-4 text-[#D9541E]" />
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#6B665E] dark:text-[#A69E92]">
              01 · Market Geography
            </div>
            <h3 className="font-heading font-bold text-[#111111] dark:text-[#F3EEE3] text-sm sm:text-base">
              Location Analysis — {location}
            </h3>
          </div>
        </div>
        <span className="text-[11px] font-semibold px-2.5 py-1 rounded-md bg-[#254C3B]/10 text-[#254C3B] dark:text-[#4C9A77] border border-[#254C3B]/25">
          Verified Historical Dataset
        </span>
      </div>

      {/* KPI Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="editorial-subcard p-3.5 rounded-lg">
          <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] mb-1.5 flex items-center gap-1.5">
            <Utensils className="w-3.5 h-3.5 text-[#D9541E]" />
            <span>Historical Outlets</span>
          </div>
          <div className="text-xl font-bold text-[#111111] dark:text-white tabular-nums">
            {Number(historical_restaurant_count).toLocaleString('en-IN')}
          </div>
        </div>

        <div className="editorial-subcard p-3.5 rounded-lg">
          <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] mb-1.5 flex items-center gap-1.5">
            <IndianRupee className="w-3.5 h-3.5 text-[#254C3B] dark:text-[#4C9A77]" />
            <span>Median Cost (Two)</span>
          </div>
          <div className="text-xl font-bold text-[#111111] dark:text-white tabular-nums">
            ₹{Number(location_median_cost).toLocaleString('en-IN')}
          </div>
        </div>

        <div className="editorial-subcard p-3.5 rounded-lg space-y-1.5">
          <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] flex items-center gap-1.5">
            <Smartphone className="w-3.5 h-3.5 text-[#254C3B] dark:text-[#4C9A77]" />
            <span>Online Ordering</span>
          </div>
          <div className="text-xl font-bold text-[#111111] dark:text-white tabular-nums">{onlineOrderPct}%</div>
          <div className="h-1.5 w-full bg-[#E6DED0] dark:bg-[#2F2B25] rounded-full overflow-hidden">
            <div
              style={{ width: `${Math.min(Math.max(Number(onlineOrderPct), 0), 100)}%` }}
              className="h-full bg-[#254C3B] dark:bg-[#4C9A77] rounded-full"
            />
          </div>
        </div>

        <div className="editorial-subcard p-3.5 rounded-lg space-y-1.5">
          <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] flex items-center gap-1.5">
            <CalendarCheck className="w-3.5 h-3.5 text-[#D9541E]" />
            <span>Table Booking</span>
          </div>
          <div className="text-xl font-bold text-[#111111] dark:text-white tabular-nums">{tableBookingPct}%</div>
          <div className="h-1.5 w-full bg-[#E6DED0] dark:bg-[#2F2B25] rounded-full overflow-hidden">
            <div
              style={{ width: `${Math.min(Math.max(Number(tableBookingPct), 0), 100)}%` }}
              className="h-full bg-[#D9541E] rounded-full"
            />
          </div>
        </div>
      </div>

      {/* Diversity Tag Strips */}
      {(top_cuisines.length > 0 || top_rest_types.length > 0) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {top_cuisines.length > 0 && (
            <div className="editorial-subcard p-3 rounded-lg text-xs">
              <span className="text-[11px] text-[#6B665E] dark:text-[#A69E92] font-semibold uppercase tracking-wider block mb-2">
                Leading Cuisines
              </span>
              <div className="flex items-center gap-1.5 flex-wrap">
                {top_cuisines.slice(0, 5).map((cuis, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded bg-white dark:bg-[#1A1917] text-[#111111] dark:text-[#E6DED0] border border-[#DDD4C3] dark:border-[#3A352E] text-[11px] font-medium"
                  >
                    {cuis}
                  </span>
                ))}
              </div>
            </div>
          )}

          {top_rest_types.length > 0 && (
            <div className="editorial-subcard p-3 rounded-lg text-xs">
              <span className="text-[11px] text-[#6B665E] dark:text-[#A69E92] font-semibold uppercase tracking-wider block mb-2">
                Prevalent Formats
              </span>
              <div className="flex items-center gap-1.5 flex-wrap">
                {top_rest_types.slice(0, 5).map((type, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded bg-[#E6DED0] dark:bg-[#2B2722] text-[#111111] dark:text-[#F3EEE3] border border-[#D4C9B6] dark:border-[#3A352E] text-[11px] font-medium"
                  >
                    {type}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Compact LLM AI Insights */}
      <AIInsightsPanel insights={insights} subtitle="Historical Market Signals" />
    </section>
  );
}
