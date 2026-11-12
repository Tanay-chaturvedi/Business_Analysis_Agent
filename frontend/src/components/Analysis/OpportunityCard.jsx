import React from 'react';
import { Target, Award, ShieldAlert, SlidersHorizontal } from 'lucide-react';
import AIInsightsPanel from './AIInsightsPanel';

export default function OpportunityCard({ opportunityData, onCreateScenario, insights }) {
  if (!opportunityData) return null;

  const {
    opportunity_score = {},
    opportunity_classification = {},
    historical_performance = {},
    competition_strength = {},
  } = opportunityData;

  const rawScore = opportunity_score.score !== undefined ? Number(opportunity_score.score) : null;
  const scoreDisplay = rawScore !== null && !isNaN(rawScore) ? rawScore.toFixed(1) : 'N/A';
  const signal =
    opportunity_score.signal ||
    (rawScore === null ? 'Moderate' : rawScore >= 70 ? 'High' : rawScore >= 40 ? 'Moderate' : 'Low');
  const category = opportunity_score.category || `${signal} Opportunity`;

  const perfSignal = historical_performance.signal || opportunity_classification.performance_rating || 'Moderate';
  const perfScore = historical_performance.score != null ? `${Number(historical_performance.score).toFixed(1)}/100` : null;
  const compSignal = competition_strength.signal || opportunity_classification.competition_rating || 'Moderate';
  const compScore = competition_strength.score != null ? `${Number(competition_strength.score).toFixed(1)}/100` : null;

  const getScoreTheme = (sig) => {
    const s = String(sig).toLowerCase();
    if (s === 'high') {
      return {
        text: 'text-[#254C3B] dark:text-[#4C9A77]',
        stroke: '#254C3B',
        badge: 'bg-[#254C3B]/10 border-[#254C3B]/30 text-[#254C3B] dark:text-[#4C9A77]',
      };
    }
    if (s === 'low') {
      return {
        text: 'text-[#A63222] dark:text-[#E06C5B]',
        stroke: '#A63222',
        badge: 'bg-[#A63222]/10 border-[#A63222]/30 text-[#A63222] dark:text-[#E06C5B]',
      };
    }
    return {
      text: 'text-[#D9541E]',
      stroke: '#D9541E',
      badge: 'bg-[#D9541E]/10 border-[#D9541E]/30 text-[#D9541E]',
    };
  };

  const styleTheme = getScoreTheme(signal);
  const dashValue = rawScore !== null && !isNaN(rawScore) ? Math.min(100, Math.max(0, rawScore)) : 0;

  return (
    <section className="editorial-panel rounded-xl p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#E6DED0] dark:border-[#2F2B25]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#EAE3D5] dark:bg-[#22201D] border border-[#D4C9B6] dark:border-[#3A352E] text-[#111111] dark:text-[#F3EEE3]">
            <Target className="w-4 h-4 text-[#D9541E]" />
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#6B665E] dark:text-[#A69E92]">
              04 · Composite Attractiveness
            </div>
            <h3 className="font-heading font-bold text-[#111111] dark:text-[#F3EEE3] text-sm sm:text-base">
              Business Opportunity Score
            </h3>
          </div>
        </div>

        <button
          type="button"
          onClick={onCreateScenario}
          className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg editorial-btn-primary text-xs font-semibold cursor-pointer"
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          <span>Create Scenario</span>
        </button>
      </div>

      {/* Gauge & Pillar Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-center editorial-subcard p-4 sm:p-5 rounded-lg">
        {/* Radial Gauge */}
        <div className="flex flex-col items-center justify-center text-center sm:border-r border-[#E6DED0] dark:border-[#2F2B25] sm:pr-4">
          <div className="relative w-26 h-26 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-[#E6DED0] dark:text-[#2F2B25]"
                strokeWidth="3.2"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                strokeWidth="3.2"
                strokeDasharray={`${dashValue}, 100`}
                stroke={styleTheme.stroke}
                strokeLinecap="round"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className={`text-2xl font-extrabold tracking-tight tabular-nums ${styleTheme.text}`}>
                {scoreDisplay}
              </span>
              <span className="text-[10px] font-semibold text-[#6B665E] dark:text-[#A69E92] uppercase">
                / 100
              </span>
            </div>
          </div>

          <div className={`mt-2.5 text-xs font-bold px-3 py-0.5 rounded-md border ${styleTheme.badge}`}>
            {category}
          </div>
        </div>

        {/* Score Pillars */}
        <div className="sm:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="bg-white dark:bg-[#1A1917] p-3.5 rounded-lg border border-[#E6DED0] dark:border-[#2F2B25]">
            <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] mb-1.5 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-[#D9541E]" />
                <span>ML Demand Pillar (60%)</span>
              </span>
              {perfScore && (
                <span className="font-bold text-[#111111] dark:text-[#F3EEE3] tabular-nums">{perfScore}</span>
              )}
            </div>
            <div className="text-sm font-bold text-[#111111] dark:text-[#F3EEE3]">{perfSignal}</div>
            <p className="text-[10px] text-[#6B665E] dark:text-[#A69E92] mt-1">
              Weighted class-probability alignment
            </p>
          </div>

          <div className="bg-white dark:bg-[#1A1917] p-3.5 rounded-lg border border-[#E6DED0] dark:border-[#2F2B25]">
            <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] mb-1.5 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-[#B4690E]" />
                <span>Market Saturation (40%)</span>
              </span>
              {compScore && (
                <span className="font-bold text-[#111111] dark:text-[#F3EEE3] tabular-nums">{compScore}</span>
              )}
            </div>
            <div className="text-sm font-bold text-[#111111] dark:text-[#F3EEE3]">{compSignal}</div>
            <p className="text-[10px] text-[#6B665E] dark:text-[#A69E92] mt-1">
              Derived from Google Places ratings & volume
            </p>
          </div>
        </div>
      </div>

      {/* Compact LLM AI Insights */}
      <AIInsightsPanel insights={insights} subtitle="Score Decomposition" />
    </section>
  );
}
