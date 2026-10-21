import React, { useState } from 'react';
import { Store, Star, MessageSquare, Award, Map, ChevronDown, ChevronUp } from 'lucide-react';

export default function CompetitionCard({ competitionData, onOpenMapModal }) {
  const [showList, setShowList] = useState(false);

  if (!competitionData) return null;

  const {
    competitor_count = 0,
    competition_summary = {},
    competitors = [],
  } = competitionData;

  const avgRating = competition_summary.avg_competitor_rating
    ? Number(competition_summary.avg_competitor_rating).toFixed(2)
    : 'N/A';
  const medianRating = competition_summary.median_competitor_rating
    ? Number(competition_summary.median_competitor_rating).toFixed(2)
    : avgRating;
  const avgReviews = competition_summary.avg_competitor_reviews
    ? Math.round(competition_summary.avg_competitor_reviews).toLocaleString('en-IN')
    : '0';
  const highRated = competition_summary.high_rating_competitors || 0;
  const highReviewed = competition_summary.high_review_competitors || 0;

  return (
    <div className="glass-panel p-5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400">
            <Store className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm sm:text-base flex items-center gap-1.5">
              Competition Analysis
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Google Places Real-Time Intelligence</p>
          </div>
        </div>

        {/* View Competitors Button */}
        <button
          onClick={() => onOpenMapModal(competitors, competitionData)}
          className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg bg-indigo-50 dark:bg-indigo-600/20 hover:bg-indigo-100 dark:hover:bg-indigo-600/30 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-500/30 text-xs font-semibold transition-all cursor-pointer shadow-xs"
        >
          <Map className="w-3.5 h-3.5" />
          <span>View Map ({competitors.length})</span>
        </button>
      </div>

      {/* Grid Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
        {/* Count */}
        <div className="bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
            <Store className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
            <span>Competitors</span>
          </div>
          <div className="text-xl font-bold text-slate-900 dark:text-white">{competitor_count}</div>
        </div>

        {/* Avg Rating */}
        <div className="bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
            <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
            <span>Avg Rating</span>
          </div>
          <div className="text-xl font-bold text-slate-900 dark:text-white flex items-baseline gap-1">
            {avgRating} <span className="text-xs text-amber-500">⭐</span>
          </div>
        </div>

        {/* Median Rating */}
        <div className="bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
            <Star className="w-3.5 h-3.5 text-amber-500" />
            <span>Median Rating</span>
          </div>
          <div className="text-xl font-bold text-slate-900 dark:text-white">{medianRating}</div>
        </div>

        {/* Avg Reviews */}
        <div className="bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
            <MessageSquare className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
            <span>Avg Reviews</span>
          </div>
          <div className="text-xl font-bold text-slate-900 dark:text-white">{avgReviews}</div>
        </div>

        {/* High Rated */}
        <div className="bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
            <Award className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>High Rated (≥4.5)</span>
          </div>
          <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400">{highRated}</div>
        </div>

        {/* High Reviews */}
        <div className="bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
            <Award className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
            <span>High Review (≥1k)</span>
          </div>
          <div className="text-xl font-bold text-purple-600 dark:text-purple-400">{highReviewed}</div>
        </div>
      </div>

      {/* Inline Expandable Competitor List */}
      {competitors.length > 0 && (
        <div className="pt-1">
          <button
            onClick={() => setShowList(!showList)}
            className="w-full flex items-center justify-between text-xs font-medium text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 py-1 transition-colors cursor-pointer"
          >
            <span>Top Competitors Preview ({competitors.length})</span>
            {showList ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showList && (
            <div className="mt-2 space-y-2 pt-2 border-t border-slate-200 dark:border-slate-800 max-h-60 overflow-y-auto pr-1">
              {competitors.map((comp, idx) => (
                <div key={idx} className="flex items-center justify-between bg-white dark:bg-slate-950/40 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800/60 text-xs shadow-xs">
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-slate-200">{comp.name}</div>
                    {comp.address && <div className="text-[10px] text-slate-500 line-clamp-1">{comp.address}</div>}
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="flex items-center text-amber-500 font-semibold text-[11px]">
                      <Star className="w-3 h-3 fill-amber-500 mr-0.5" />
                      {comp.rating || 'N/A'}
                    </span>
                    <span className="text-[10px] text-slate-500 dark:text-slate-400">({comp.review_count || 0} reviews)</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
