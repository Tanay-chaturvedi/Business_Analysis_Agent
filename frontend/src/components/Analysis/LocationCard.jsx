import React from 'react';
import { MapPin, Utensils, IndianRupee, Smartphone, CalendarCheck } from 'lucide-react';

export default function LocationCard({ locationData }) {
  if (!locationData) return null;

  const {
    location,
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
    <div className="glass-panel p-5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm sm:text-base flex items-center gap-1.5">
              Location Analysis
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">{location}</p>
          </div>
        </div>
        <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
          Historical Location Data
        </span>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Historical Restaurants */}
        <div className="bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
            <Utensils className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
            <span>Historical Restaurants</span>
          </div>
          <div className="text-xl font-bold text-slate-900 dark:text-white">{historical_restaurant_count}</div>
        </div>

        {/* Median Cost */}
        <div className="bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
            <IndianRupee className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>Median Cost for Two</span>
          </div>
          <div className="text-xl font-bold text-slate-900 dark:text-white">₹{Number(location_median_cost).toLocaleString('en-IN')}</div>
        </div>

        {/* Online Ordering Rate */}
        <div className="bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80 space-y-1">
          <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 flex items-center justify-between">
            <span className="flex items-center gap-1">
              <Smartphone className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              <span>Online Ordering Rate</span>
            </span>
          </div>
          <div className="text-xl font-bold text-slate-900 dark:text-white">{onlineOrderPct}%</div>
          <div className="h-1.5 w-full bg-slate-200 dark:bg-slate-900 rounded-full overflow-hidden">
            <div
              style={{ width: `${Math.min(Math.max(Number(onlineOrderPct), 0), 100)}%` }}
              className="h-full bg-blue-500 rounded-full"
            />
          </div>
        </div>

        {/* Table Booking Rate */}
        <div className="bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80 space-y-1">
          <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 flex items-center justify-between">
            <span className="flex items-center gap-1">
              <CalendarCheck className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
              <span>Table Booking Rate</span>
            </span>
          </div>
          <div className="text-xl font-bold text-slate-900 dark:text-white">{tableBookingPct}%</div>
          <div className="h-1.5 w-full bg-slate-200 dark:bg-slate-900 rounded-full overflow-hidden">
            <div
              style={{ width: `${Math.min(Math.max(Number(tableBookingPct), 0), 100)}%` }}
              className="h-full bg-purple-500 rounded-full"
            />
          </div>
        </div>
      </div>

      {/* Diversity Tags: Cuisines & Rest Types */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
        {top_cuisines.length > 0 && (
          <div className="bg-slate-50 dark:bg-slate-950/40 p-3 rounded-xl border border-slate-200 dark:border-slate-800/60 text-xs">
            <span className="text-slate-500 dark:text-slate-400 font-semibold block mb-1.5">Cuisine Diversity:</span>
            <div className="flex items-center gap-1.5 flex-wrap">
              {top_cuisines.slice(0, 5).map((cuis, i) => (
                <span key={i} className="px-2 py-0.5 rounded-md bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700/60 text-[11px] font-medium shadow-xs">
                  {cuis}
                </span>
              ))}
            </div>
          </div>
        )}

        {top_rest_types.length > 0 && (
          <div className="bg-slate-50 dark:bg-slate-950/40 p-3 rounded-xl border border-slate-200 dark:border-slate-800/60 text-xs">
            <span className="text-slate-500 dark:text-slate-400 font-semibold block mb-1.5">Business Type Diversity:</span>
            <div className="flex items-center gap-1.5 flex-wrap">
              {top_rest_types.slice(0, 5).map((type, i) => (
                <span key={i} className="px-2 py-0.5 rounded-md bg-indigo-50 dark:bg-slate-900 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30 text-[11px] font-medium shadow-xs">
                  {type}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
