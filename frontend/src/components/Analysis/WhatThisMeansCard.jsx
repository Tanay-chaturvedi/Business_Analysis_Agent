import React from 'react';
import { HelpCircle, Target, TrendingUp, MapPin, Store, DollarSign, AlertTriangle } from 'lucide-react';
import TextToSpeechButton from '../AudioPlayer/TextToSpeechButton';

export default function WhatThisMeansCard({ analysis }) {
  if (!analysis) return null;

  const loc = analysis.location_result || {};
  const perf = analysis.performance_result || {};
  const comp = analysis.competition_result || analysis.full_competition_result?.competition_summary || {};
  const opp = analysis.opportunity_result || {};
  const fin = analysis.financial || analysis.financial_result || {};

  const oppScore = opp.opportunity_score?.score ?? 'N/A';
  const oppSignal = opp.opportunity_score?.signal ?? 'Moderate';

  const prediction = perf.prediction || 'High';
  const highProb = perf.probabilities?.High != null ? Math.round(perf.probabilities.High * 100) : null;

  const locName = loc.location || 'Target Area';
  const restCount = loc.historical_restaurant_count ?? 'N/A';
  const medianCost = loc.location_median_cost ? Math.round(loc.location_median_cost) : 'N/A';
  const onlineRate = loc.location_online_order_rate != null ? Math.round(loc.location_online_order_rate * 100) : 'N/A';

  const compCount = comp.competitor_count_retrieved ?? 'N/A';
  const avgRating = comp.avg_competitor_rating != null ? comp.avg_competitor_rating.toFixed(1) : 'N/A';
  const highRatingComp = comp.high_rating_competitors ?? 0;
  const highReviewComp = comp.high_review_competitors ?? 0;

  const rev = fin.monthly_revenue ? `₹${Math.round(fin.monthly_revenue).toLocaleString('en-IN')}` : 'N/A';
  const exp = fin.monthly_expenses ? `₹${Math.round(fin.monthly_expenses).toLocaleString('en-IN')}` : 'N/A';
  const profit = fin.estimated_operating_profit != null ? `₹${Math.round(fin.estimated_operating_profit).toLocaleString('en-IN')}` : 'N/A';
  const margin = fin.operating_profit_margin != null ? `${fin.operating_profit_margin.toFixed(1)}%` : 'N/A';
  const breakEven = fin.break_even_customers_per_day != null ? `${Math.round(fin.break_even_customers_per_day)}/day` : 'N/A';

  const cuisine = analysis.parameters?.primary_cuisine || perf.cuisine || '';
  const backendTakeaway = analysis.business_takeaway || null;

  const fallbackTakeaway = [
    `The proposed ${cuisine || 'restaurant'} concept registers an Opportunity Score of ${oppScore} (${oppSignal}).`,
    highProb != null
      ? `The ML model predicts ${prediction} performance with a ${highProb}% probability score.`
      : `The ML model predicts ${prediction} performance.`,
    margin !== 'N/A'
      ? `Estimated operating profit margin sits at ${margin}, with break-even at ${breakEven}.`
      : null,
    'This analysis should be treated as a data-backed indication rather than a guarantee of business success.',
  ]
    .filter(Boolean)
    .join(' ');

  const businessTakeaway = backendTakeaway || fallbackTakeaway;

  // Risk identification grounded in backend data
  let keyRisk = 'High competitive presence in the immediate target radius.';
  if (highReviewComp > 2 || highRatingComp > 3) {
    keyRisk = `Strong local competitor presence (${highRatingComp} competitors rated ≥4.5★ and ${highReviewComp} high-review landmarks).`;
  } else if (fin.operating_profit_margin != null && fin.operating_profit_margin < 20) {
    keyRisk = `Tight operating profit margin (${margin}), requiring strict expense control.`;
  } else if (loc.location_book_table_rate != null && loc.location_book_table_rate < 0.10) {
    keyRisk = `Low historical table booking adoption (${Math.round(loc.location_book_table_rate * 100)}%) in this location.`;
  }

  return (
    <div className="glass-panel p-5 rounded-2xl border border-indigo-200 dark:border-indigo-500/30 space-y-4 my-4 bg-white dark:bg-slate-900/90 shadow-xl">
      {/* Card Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-600 dark:text-indigo-400">
            <HelpCircle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm sm:text-base tracking-wide">
              WHAT THIS MEANS
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Simple English Summary of Analysis Results</p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-50 dark:bg-indigo-500/10 border border-indigo-200 dark:border-indigo-500/30 text-indigo-700 dark:text-indigo-300">
          Executive Summary
        </span>
      </div>

      {/* Bullet Points */}
      <div className="space-y-3 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
        {/* Overall */}
        <div className="flex items-start gap-2.5 bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
          <Target className="w-4 h-4 text-purple-600 dark:text-purple-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-slate-900 dark:text-white font-semibold">Overall Opportunity:</strong>{' '}
            The model evaluates this restaurant concept as a <span className="text-purple-700 dark:text-purple-300 font-bold">{oppSignal} Opportunity</span> (Opportunity Score: <span className="text-slate-900 dark:text-white font-bold">{oppScore}/100</span>).
          </div>
        </div>

        {/* Demand & Performance */}
        <div className="flex items-start gap-2.5 bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
          <TrendingUp className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-slate-900 dark:text-white font-semibold">Demand & Performance:</strong>{' '}
            The Random Forest machine learning model predicts <span className="text-emerald-700 dark:text-emerald-300 font-bold">{prediction} performance</span>{highProb != null ? ` with a ${highProb}% probability score` : ''} based on historical location patterns.
          </div>
        </div>

        {/* Location */}
        <div className="flex items-start gap-2.5 bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
          <MapPin className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-slate-900 dark:text-white font-semibold">Location Context:</strong>{' '}
            <span className="text-slate-800 dark:text-slate-200">{locName}</span> contains {restCount} historical restaurant benchmarks with a median cost for two of ₹{medianCost} and {onlineRate}% online ordering adoption.
          </div>
        </div>

        {/* Competition */}
        <div className="flex items-start gap-2.5 bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
          <Store className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <strong className="text-slate-900 dark:text-white font-semibold">Competition:</strong>{' '}
            Identified {compCount} nearby competitors in Google Places with an average rating of {avgRating}★ and {highRatingComp} high-rated competitors (≥4.5★).
          </div>
        </div>

        {/* Money */}
        <div className="flex items-start gap-2.5 bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
          <DollarSign className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-slate-900 dark:text-white font-semibold">Financial Estimates:</strong>{' '}
            Simulated monthly revenue of <span className="text-teal-700 dark:text-teal-300 font-medium">{rev}</span> against operating expenses of <span className="text-slate-800 dark:text-slate-200">{exp}</span>, yielding estimated profit of <span className="text-emerald-700 dark:text-emerald-300 font-bold">{profit}</span> ({margin} margin) and break-even at {breakEven}.
          </div>
        </div>

        {/* Key Risk */}
        <div className="flex items-start gap-2.5 bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-rose-500/20">
          <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-rose-700 dark:text-rose-300 font-semibold">Key Risk:</strong>{' '}
            <span className="text-slate-800 dark:text-slate-300">{keyRisk}</span>
          </div>
        </div>

        {/* Business Takeaway — TTS enabled here ONLY */}
        <div className="bg-indigo-50 dark:bg-indigo-950/30 rounded-xl border border-indigo-200 dark:border-indigo-500/30 mt-2 overflow-hidden shadow-xs">
          {/* Section header */}
          <div className="flex items-center gap-2 px-3.5 pt-3 pb-2 border-b border-indigo-100 dark:border-indigo-500/20">
            <span className="text-base">💡</span>
            <span className="text-xs font-bold text-indigo-700 dark:text-indigo-300 uppercase tracking-wide">Business Takeaway</span>
          </div>

          {/* Takeaway paragraph */}
          <div className="px-3.5 py-3">
            <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
              {businessTakeaway}
            </p>

            {/* 🔊 Listen — TTS button scoped ONLY to the Business Takeaway */}
            <TextToSpeechButton text={businessTakeaway} />
          </div>
        </div>
      </div>
    </div>
  );
}
