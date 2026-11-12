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
    <div className="fixed inset-0 z-50 bg-[#111111]/65 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="editorial-panel rounded-xl w-full max-w-lg shadow-2xl overflow-hidden text-[#111111] dark:text-[#F3EEE3]">
        <div className="p-4 border-b border-[#E6DED0] dark:border-[#2F2B25] flex items-center justify-between bg-[#F8F5EE] dark:bg-[#161513]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-[#EAE3D5] dark:bg-[#22201D] border border-[#D4C9B6] dark:border-[#3A352E]">
              <SlidersHorizontal className="w-4 h-4 text-[#D9541E]" />
            </div>
            <div>
              <h2 className="font-heading font-bold text-[#111111] dark:text-white text-sm sm:text-base">
                Create What-If Scenario
              </h2>
              <p className="text-xs text-[#6B665E] dark:text-[#A69E92]">
                Modify concept parameters and compare against baseline
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#6B665E] hover:text-[#111111] dark:hover:text-white hover:bg-[#EAE3D5] dark:hover:bg-[#22201D] transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-[#111111] dark:text-[#E6DED0] mb-1.5 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-[#D9541E]" /> Target Location
            </label>
            <input
              type="text"
              required
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Koramangala, Bengaluru"
              className="w-full bg-[#F8F5EE] dark:bg-[#22201D] border border-[#C9BFAE] dark:border-[#3A352E] rounded-lg px-3 py-2 text-[#111111] dark:text-[#F3EEE3] focus:outline-none focus:border-[#D9541E] transition-colors"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-[#111111] dark:text-[#E6DED0] mb-1.5 flex items-center gap-1.5">
                <Utensils className="w-3.5 h-3.5 text-[#D9541E]" /> Primary Cuisine
              </label>
              <input
                type="text"
                required
                value={cuisine}
                onChange={(e) => setCuisine(e.target.value)}
                placeholder="e.g. Japanese, Cafe"
                className="w-full bg-[#F8F5EE] dark:bg-[#22201D] border border-[#C9BFAE] dark:border-[#3A352E] rounded-lg px-3 py-2 text-[#111111] dark:text-[#F3EEE3] focus:outline-none focus:border-[#D9541E] transition-colors"
              />
            </div>

            <div>
              <label className="block font-semibold text-[#111111] dark:text-[#E6DED0] mb-1.5 flex items-center gap-1.5">
                <IndianRupee className="w-3.5 h-3.5 text-[#254C3B] dark:text-[#4C9A77]" /> Cost for Two (₹)
              </label>
              <input
                type="number"
                required
                min="100"
                step="50"
                value={cost}
                onChange={(e) => setCost(e.target.value)}
                placeholder="1800"
                className="w-full bg-[#F8F5EE] dark:bg-[#22201D] border border-[#C9BFAE] dark:border-[#3A352E] rounded-lg px-3 py-2 text-[#111111] dark:text-[#F3EEE3] focus:outline-none focus:border-[#D9541E] transition-colors tabular-nums"
              />
            </div>
          </div>

          <div>
            <label className="block font-semibold text-[#111111] dark:text-[#E6DED0] mb-1.5 flex items-center gap-1.5">
              <Store className="w-3.5 h-3.5 text-[#6B665E]" /> Restaurant Concept Type
            </label>
            <select
              value={restType}
              onChange={(e) => setRestType(e.target.value)}
              className="w-full bg-[#F8F5EE] dark:bg-[#22201D] border border-[#C9BFAE] dark:border-[#3A352E] rounded-lg px-3 py-2 text-[#111111] dark:text-[#F3EEE3] focus:outline-none focus:border-[#D9541E] transition-colors"
            >
              <option value="Casual Dining">Casual Dining</option>
              <option value="Fine Dining">Fine Dining</option>
              <option value="Quick Bites">Quick Bites / Fast Food</option>
              <option value="Cafe">Cafe / Coffee Shop</option>
              <option value="Bakery">Bakery & Confectionery</option>
              <option value="Dessert Parlor">Dessert Parlor</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-1">
            <label className="flex items-center justify-between p-3 rounded-lg bg-[#F8F5EE] dark:bg-[#22201D] border border-[#DDD4C3] dark:border-[#3A352E] cursor-pointer">
              <span className="text-[#111111] dark:text-[#E6DED0] font-medium">Online Ordering</span>
              <input
                type="checkbox"
                checked={onlineOrder}
                onChange={(e) => setOnlineOrder(e.target.checked)}
                className="w-4 h-4 accent-[#D9541E]"
              />
            </label>

            <label className="flex items-center justify-between p-3 rounded-lg bg-[#F8F5EE] dark:bg-[#22201D] border border-[#DDD4C3] dark:border-[#3A352E] cursor-pointer">
              <span className="text-[#111111] dark:text-[#E6DED0] font-medium">Table Booking</span>
              <input
                type="checkbox"
                checked={bookTable}
                onChange={(e) => setBookTable(e.target.checked)}
                className="w-4 h-4 accent-[#D9541E]"
              />
            </label>
          </div>

          <div className="pt-3 border-t border-[#E6DED0] dark:border-[#2F2B25] flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="py-2 px-4 rounded-lg bg-[#E6DED0] dark:bg-[#22201D] hover:bg-[#DDD4C3] dark:hover:bg-[#2D2924] text-[#111111] dark:text-[#E6DED0] font-semibold transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="py-2 px-4 rounded-lg editorial-btn-primary font-semibold flex items-center gap-2 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Calculating Scenario...</span>
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
