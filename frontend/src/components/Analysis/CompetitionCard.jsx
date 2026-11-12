import React, { useState } from 'react';
import { Store, Star, MessageSquare, Award, Map, ChevronDown, ChevronUp } from 'lucide-react';
import AIInsightsPanel from './AIInsightsPanel';

export default function CompetitionCard({ competitionData, onOpenMapModal, insights }) {
  const [showList, setShowList] = useState(false);

  if (!competitionData) return null;

  const {
    competitor_count,
    competition_summary = {},
    competitors = [],
  } = competitionData;

  const resolvedCount =
    competitor_count ??
    competition_summary.competitor_count_retrieved ??
    competitors.length ??
    0;

  const avgRating = competition_summary.avg_competitor_rating != null
    ? Number(competition_summary.avg_competitor_rating).toFixed(2)
    : 'N/A';
  const medianRating = competition_summary.median_competitor_rating != null
    ? Number(competition_summary.median_competitor_rating).toFixed(2)
    : avgRating;
  const avgReviews = competition_summary.avg_competitor_reviews != null
    ? Math.round(competition_summary.avg_competitor_reviews).toLocaleString('en-IN')
    : '0';
  const highRated = competition_summary.high_rating_competitors ?? 0;
  const highReviewed = competition_summary.high_review_competitors ?? 0;

  return (
    <section className="editorial-panel rounded-xl p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#E6DED0] dark:border-[#2F2B25]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#EAE3D5] dark:bg-[#22201D] border border-[#D4C9B6] dark:border-[#3A352E] text-[#111111] dark:text-[#F3EEE3]">
            <Store className="w-4 h-4 text-[#D9541E]" />
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#6B665E] dark:text-[#A69E92]">
              03 · Live Market Supply
            </div>
            <h3 className="font-heading font-bold text-[#111111] dark:text-[#F3EEE3] text-sm sm:text-base">
              Competition Analysis
            </h3>
          </div>
        </div>

        <button
          type="button"
          onClick={() => onOpenMapModal(competitors, competitionData)}
          className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg bg-[#111111] dark:bg-[#26231F] hover:bg-[#D9541E] text-white border border-[#111111] dark:border-[#3A352E] text-xs font-semibold transition-colors cursor-pointer"
        >
          <Map className="w-3.5 h-3.5" />
          <span>View Map ({competitors.length})</span>
        </button>
      </div>

      {/* 6 KPI Tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
        <div className="editorial-subcard p-3 rounded-lg">
          <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] mb-1 flex items-center gap-1">
            <Store className="w-3 h-3 text-[#D9541E]" />
            <span>Competitors</span>
          </div>
          <div className="text-lg font-bold text-[#111111] dark:text-white tabular-nums">{resolvedCount}</div>
        </div>

        <div className="editorial-subcard p-3 rounded-lg">
          <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] mb-1 flex items-center gap-1">
            <Star className="w-3 h-3 text-[#D9541E] fill-[#D9541E]" />
            <span>Avg Rating</span>
          </div>
          <div className="text-lg font-bold text-[#111111] dark:text-white tabular-nums">{avgRating}</div>
        </div>

        <div className="editorial-subcard p-3 rounded-lg">
          <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] mb-1 flex items-center gap-1">
            <Star className="w-3 h-3 text-[#6B665E]" />
            <span>Median Rating</span>
          </div>
          <div className="text-lg font-bold text-[#111111] dark:text-white tabular-nums">{medianRating}</div>
        </div>

        <div className="editorial-subcard p-3 rounded-lg">
          <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] mb-1 flex items-center gap-1">
            <MessageSquare className="w-3 h-3 text-[#6B665E]" />
            <span>Avg Reviews</span>
          </div>
          <div className="text-lg font-bold text-[#111111] dark:text-white tabular-nums">{avgReviews}</div>
        </div>

        <div className="editorial-subcard p-3 rounded-lg">
          <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] mb-1 flex items-center gap-1">
            <Award className="w-3 h-3 text-[#D9541E]" />
            <span>Rated ≥ 4.5★</span>
          </div>
          <div className="text-lg font-bold text-[#D9541E] tabular-nums">{highRated}</div>
        </div>

        <div className="editorial-subcard p-3 rounded-lg">
          <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] mb-1 flex items-center gap-1">
            <Award className="w-3 h-3 text-[#111111] dark:text-[#F3EEE3]" />
            <span>Reviews ≥ 1k</span>
          </div>
          <div className="text-lg font-bold text-[#111111] dark:text-white tabular-nums">{highReviewed}</div>
        </div>
      </div>

      {/* Expandable Competitor Directory Table */}
      {competitors.length > 0 && (
        <div>
          <button
            type="button"
            onClick={() => setShowList(!showList)}
            className="w-full flex items-center justify-between text-xs font-semibold text-[#6B665E] hover:text-[#111111] dark:text-[#A69E92] dark:hover:text-white py-1 transition-colors cursor-pointer"
          >
            <span>Inspect Retrieved Competitors ({competitors.length})</span>
            {showList ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showList && (
            <div className="mt-2 overflow-hidden rounded-lg border border-[#E6DED0] dark:border-[#2F2B25] max-h-60 overflow-y-auto">
              <table className="w-full text-xs text-left">
                <thead className="sticky top-0 bg-[#F3EEE3] dark:bg-[#22201D] text-[10px] font-bold uppercase tracking-wider text-[#6B665E] dark:text-[#A69E92] border-b border-[#E6DED0] dark:border-[#2F2B25]">
                  <tr>
                    <th className="py-2 px-3">Establishment</th>
                    <th className="py-2 px-3 text-right">Rating</th>
                    <th className="py-2 px-3 text-right">Reviews</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#EAE3D5] dark:divide-[#2C2823] bg-white dark:bg-[#1A1917]">
                  {competitors.map((comp, idx) => (
                    <tr key={idx} className="hover:bg-[#F8F5EE] dark:hover:bg-[#22201D]">
                      <td className="py-2 px-3">
                        <div className="font-semibold text-[#111111] dark:text-[#F3EEE3]">{comp.name}</div>
                        {comp.address && (
                          <div className="text-[10px] text-[#6B665E] dark:text-[#A69E92] line-clamp-1">{comp.address}</div>
                        )}
                      </td>
                      <td className="py-2 px-3 text-right font-semibold text-[#D9541E] tabular-nums whitespace-nowrap">
                        {comp.rating || 'N/A'} ★
                      </td>
                      <td className="py-2 px-3 text-right text-[#6B665E] dark:text-[#A69E92] tabular-nums whitespace-nowrap">
                        {Number(comp.review_count || 0).toLocaleString('en-IN')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Compact LLM AI Insights */}
      <AIInsightsPanel insights={insights} subtitle="Google Places Intelligence" />
    </section>
  );
}
