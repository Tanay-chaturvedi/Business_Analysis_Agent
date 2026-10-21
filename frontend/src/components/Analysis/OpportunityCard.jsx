import React from 'react';
import { Target, Award, ShieldAlert, Sparkles, SlidersHorizontal, CheckCircle2 } from 'lucide-react';

export default function OpportunityCard({ opportunityData, onCreateScenario }) {
  if (!opportunityData) return null;

  const {
    opportunity_score = {},
    opportunity_classification = {},
    strategic_recommendations = [],
  } = opportunityData;

  const score = opportunity_score.score !== undefined ? Number(opportunity_score.score).toFixed(1) : '72.4';
  const category = opportunity_score.category || 'High Opportunity';
  const perfRating = opportunity_classification.performance_rating || 'Strong';
  const compRating = opportunity_classification.competition_rating || 'Moderate';

  // Score status styling
  const getScoreColor = (val) => {
    const num = Number(val);
    if (num >= 70) return { text: 'text-emerald-600 dark:text-emerald-400', stroke: '#10b981', bg: 'bg-emerald-500/10 border-emerald-500/20' };
    if (num >= 50) return { text: 'text-amber-600 dark:text-amber-400', stroke: '#f59e0b', bg: 'bg-amber-500/10 border-amber-500/20' };
    return { text: 'text-rose-600 dark:text-rose-400', stroke: '#f43f5e', bg: 'bg-rose-500/10 border-rose-500/20' };
  };

  const styleTheme = getScoreColor(score);

  return (
    <div className="glass-panel p-5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-600 dark:text-purple-400">
            <Target className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm sm:text-base flex items-center gap-1.5">
              Business Opportunity Score
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Synthesized Multi-Agent Score</p>
          </div>
        </div>

        <button
          onClick={onCreateScenario}
          className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition-all cursor-pointer"
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          <span>+ Create Scenario</span>
        </button>
      </div>

      {/* Main Score Visual Indicator & Classifications */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-center bg-slate-50 dark:bg-slate-950/60 p-5 rounded-xl border border-slate-200 dark:border-slate-800/80">
        {/* Large Score Indicator */}
        <div className="flex flex-col items-center justify-center text-center sm:border-r border-slate-200 dark:border-slate-800 pr-0 sm:pr-4">
          <div className="relative w-28 h-28 flex items-center justify-center">
            {/* SVG Circular Progress Gauge */}
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-slate-200 dark:text-slate-800"
                strokeWidth="3.5"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                strokeWidth="3.5"
                strokeDasharray={`${score}, 100`}
                stroke={styleTheme.stroke}
                strokeLinecap="round"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className={`text-2xl font-extrabold tracking-tight ${styleTheme.text}`}>{score}</span>
              <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase">/ 100</span>
            </div>
          </div>

          <div className={`mt-2 text-xs font-bold px-3 py-0.5 rounded-full border ${styleTheme.bg} ${styleTheme.text}`}>
            {category}
          </div>
        </div>

        {/* Classification Cards */}
        <div className="sm:col-span-2 grid grid-cols-2 gap-3">
          <div className="bg-white dark:bg-slate-900/80 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
            <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
              <Award className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
              <span>Historical Performance</span>
            </div>
            <div className="text-base font-bold text-slate-900 dark:text-white mt-1">{perfRating}</div>
            <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">Based on ML model probabilities</p>
          </div>

          <div className="bg-white dark:bg-slate-900/80 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
            <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
              <span>Competition Intensity</span>
            </div>
            <div className="text-base font-bold text-slate-900 dark:text-white mt-1">{compRating}</div>
            <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">Google Places market saturation</p>
          </div>
        </div>
      </div>

      {/* Strategic AI Recommendations */}
      {strategic_recommendations.length > 0 && (
        <div className="space-y-2 pt-1">
          <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
            <span>Strategic Recommendations:</span>
          </div>
          <div className="space-y-1.5">
            {strategic_recommendations.slice(0, 3).map((rec, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-950/40 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800/60">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <span>{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
