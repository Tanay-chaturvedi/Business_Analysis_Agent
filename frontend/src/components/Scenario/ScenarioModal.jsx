import React, { useState, useEffect } from 'react';
import { X, SlidersHorizontal, IndianRupee, MapPin, Utensils, Store, Loader2 } from 'lucide-react';

export default function ScenarioModal({ isOpen, onClose, currentParams, onSubmitScenario, isLoading }) {
  const [location, setLocation] = useState('Koramangala, Bengaluru');
  const [cuisine, setCuisine] = useState('Japanese');
  const [cost, setCost] = useState(1800);
  const [onlineOrder, setOnlineOrder] = useState(true);
  const [bookTable, setBookTable] = useState(true);
  const [restType, setRestType] = useState('Casual Dining');

  useEffect(() => {
    if (currentParams) {
      setLocation(currentParams.location || 'Koramangala, Bengaluru');
      setCuisine(currentParams.primary_cuisine || 'Japanese');
      setCost(currentParams.approx_cost_for_two || 1800);
      setOnlineOrder(currentParams.online_order !== undefined ? currentParams.online_order : true);
      setBookTable(currentParams.book_table !== undefined ? currentParams.book_table : true);
      setRestType(currentParams.restaurant_type || 'Casual Dining');
    }
  }, [currentParams, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const scenarioParams = {
      location,
      primary_cuisine: cuisine,
      approx_cost_for_two: Number(cost),
      online_order: onlineOrder,
      book_table: bookTable,
      restaurant_type: restType,
      cuisine_count: 2,
      search_query: `${cuisine} restaurant in ${location}`,
    };
    onSubmitScenario(currentParams || scenarioParams, scenarioParams);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/70 dark:bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden text-slate-900 dark:text-slate-100 transition-colors">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-600 dark:text-purple-400">
              <SlidersHorizontal className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-slate-900 dark:text-white text-base">Create What-If Scenario</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">Modify business parameters & compare outcomes</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
          {/* Target Location */}
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" /> Target Location
            </label>
            <input
              type="text"
              required
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Koramangala, Bengaluru"
              className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2.5 text-slate-900 dark:text-slate-200 focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>

          {/* Grid: Cuisine & Cost */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1">
                <Utensils className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" /> Primary Cuisine
              </label>
              <input
                type="text"
                required
                value={cuisine}
                onChange={(e) => setCuisine(e.target.value)}
                placeholder="e.g. Japanese, Cafe"
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2.5 text-slate-900 dark:text-slate-200 focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1">
                <IndianRupee className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Cost for Two (₹)
              </label>
              <input
                type="number"
                required
                min="100"
                step="50"
                value={cost}
                onChange={(e) => setCost(e.target.value)}
                placeholder="1800"
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2.5 text-slate-900 dark:text-slate-200 focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>
          </div>

          {/* Restaurant Type */}
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1">
              <Store className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" /> Restaurant Concept Type
            </label>
            <select
              value={restType}
              onChange={(e) => setRestType(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2.5 text-slate-900 dark:text-slate-200 focus:outline-none focus:border-purple-500 transition-colors"
            >
              <option value="Casual Dining">Casual Dining</option>
              <option value="Fine Dining">Fine Dining</option>
              <option value="Quick Bytes">Quick Bytes / Fast Food</option>
              <option value="Cafe">Cafe / Coffee Shop</option>
              <option value="Bakery">Bakery & Confectionery</option>
              <option value="Dessert Parlor">Dessert Parlor</option>
            </select>
          </div>

          {/* Toggles: Online Ordering & Table Booking */}
          <div className="grid grid-cols-2 gap-3 pt-1">
            <label className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 cursor-pointer">
              <span className="text-slate-700 dark:text-slate-300 font-medium">Online Ordering</span>
              <input
                type="checkbox"
                checked={onlineOrder}
                onChange={(e) => setOnlineOrder(e.target.checked)}
                className="w-4 h-4 rounded text-purple-600 focus:ring-purple-500 bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700"
              />
            </label>

            <label className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 cursor-pointer">
              <span className="text-slate-700 dark:text-slate-300 font-medium">Table Booking</span>
              <input
                type="checkbox"
                checked={bookTable}
                onChange={(e) => setBookTable(e.target.checked)}
                className="w-4 h-4 rounded text-purple-600 focus:ring-purple-500 bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700"
              />
            </label>
          </div>

          {/* Submit Button */}
          <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="py-2.5 px-4 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-semibold transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="py-2.5 px-5 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-semibold shadow-lg shadow-purple-600/20 transition-all flex items-center gap-2 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Calculating Backend Scenario...</span>
                </>
              ) : (
                <>
                  <SlidersHorizontal className="w-4 h-4" />
                  <span>Run Scenario Analysis</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
