import React from 'react';
import { HelpCircle, Target, TrendingUp, MapPin, Store, DollarSign, AlertTriangle } from 'lucide-react';
import TextToSpeechButton from '../AudioPlayer/TextToSpeechButton';
import AIInsightsPanel from './AIInsightsPanel';

export default function WhatThisMeansCard({ analysis, recommendations }) {
  if (!analysis) return null;

  const loc = analysis.location_result || {};
  const perf = analysis.performance_result || {};
  const compResult = analysis.competition_result || {};
  const comp = compResult.competition_summary || analysis.full_competition_result?.competition_summary || compResult;
  const opp = analysis.opportunity_result || {};
  const fin = analysis.financial || analysis.financial_result || {};

  const oppScore = opp.opportunity_score?.score ?? 'N/A';
  const oppSignal = opp.opportunity_score?.signal ?? 'Moderate';

  const prediction = perf.prediction || 'High';
  const rawPredProb = perf.probabilities?.[prediction] ??
    Object.entries(perf.probabilities || {}).find(([k]) => k.toLowerCase() === String(prediction).toLowerCase())?.[1];
  const predProbValue = rawPredProb != null
    ? Number(rawPredProb <= 1.0 ? rawPredProb * 100 : rawPredProb).toFixed(1)
    : null;

  const locName = loc.location || 'Target Area';
  const isLocFound = loc.found !== false;
  const restCount = isLocFound && loc.historical_restaurant_count != null ? loc.historical_restaurant_count : 'N/A';
  const medianCost = isLocFound && loc.location_median_cost ? Math.round(loc.location_median_cost) : 'N/A';
  const onlineRate = isLocFound && loc.location_online_order_rate != null ? Math.round(loc.location_online_order_rate * 100) : 'N/A';

  const compCount = comp.competitor_count_retrieved ?? compResult.competitor_count ?? (Array.isArray(compResult.competitors) ? compResult.competitors.length : 'N/A');
  const avgRating = comp.avg_competitor_rating != null ? Number(comp.avg_competitor_rating).toFixed(2) : 'N/A';
  const highRatingComp = comp.high_rating_competitors ?? 0;
  const highReviewComp = comp.high_review_competitors ?? 0;

  const rev = fin.monthly_revenue != null ? `₹${Math.round(fin.monthly_revenue).toLocaleString('en-IN')}` : 'N/A';
  const exp = fin.monthly_expenses != null ? `₹${Math.round(fin.monthly_expenses).toLocaleString('en-IN')}` : 'N/A';
  const profit = fin.estimated_operating_profit != null ? `₹${Math.round(fin.estimated_operating_profit).toLocaleString('en-IN')}` : 'N/A';
  const margin = fin.operating_profit_margin != null ? `${Number(fin.operating_profit_margin).toFixed(1)}%` : 'N/A';
  const breakEven = fin.break_even_target_customers_per_day != null
    ? `${fin.break_even_target_customers_per_day}/day`
    : (fin.break_even_customers_per_day != null ? `${Math.ceil(fin.break_even_customers_per_day)}/day` : 'N/A');

  const cuisine = analysis.parameters?.primary_cuisine || perf.cuisine || '';
  const backendTakeaway = analysis.business_takeaway || null;
  const llmRecommendations = recommendations || analysis.ai_insights?.business_recommendations || analysis.business_recommendations;

  const fallbackTakeaway = [
    `The proposed ${cuisine || 'restaurant'} concept registers an Opportunity Score of ${oppScore} (${oppSignal}).`,
    predProbValue != null
      ? `The ML model classifies this concept in the ${prediction} tier with a ${predProbValue}% predicted-class probability.`
      : `The ML model classifies this concept in the ${prediction} tier.`,
    margin !== 'N/A'
      ? `Under modeled assumptions, operating profit margin is ${margin} with break-even at ${breakEven}.`
      : null,
    'This analysis should be treated as a directional data-backed indication rather than a guarantee of business success.',
  ]
    .filter(Boolean)
    .join(' ');

  const businessTakeaway = backendTakeaway || fallbackTakeaway;

  // Risk identification grounded in backend data
  let keyRisk = 'Active local competition requires strong value or culinary differentiation.';
  if (highReviewComp > 2 || highRatingComp > 3) {
    keyRisk = `Established market incumbents (${highRatingComp} outlets rated ≥4.5★ and ${highReviewComp} with ≥1,000 reviews) create high customer-trust barriers.`;
  } else if (fin.operating_profit_margin != null && fin.operating_profit_margin < 20) {
    keyRisk = `Tight projected operating margin (${margin}) leaves narrow buffer against food inflation or rent escalation.`;
  } else if (isLocFound && loc.location_book_table_rate != null && loc.location_book_table_rate < 0.10) {
    keyRisk = `Low historical table booking adoption (${Math.round(loc.location_book_table_rate * 100)}%) in ${locName} limits reservation-heavy formats.`;
  }

  return (
    <section className="editorial-panel rounded-xl p-5 space-y-4">
      {/* Card Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#E6DED0] dark:border-[#2F2B25]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#EAE3D5] dark:bg-[#22201D] border border-[#D4C9B6] dark:border-[#3A352E] text-[#111111] dark:text-[#F3EEE3]">
            <HelpCircle className="w-4 h-4 text-[#D9541E]" />
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#6B665E] dark:text-[#A69E92]">
              06 · Synthesized Advisory Brief
            </div>
            <h3 className="font-heading font-bold text-[#111111] dark:text-[#F3EEE3] text-sm sm:text-base">
              What This Means — Executive Summary
            </h3>
          </div>
        </div>
        <span className="text-[11px] font-semibold px-2.5 py-1 rounded-md bg-[#111111] dark:bg-[#26231F] text-white">
          Executive Brief
        </span>
      </div>

      {/* Structured Data Fact Rows */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
        <div className="editorial-subcard p-3 rounded-lg flex items-start gap-2.5">
          <Target className="w-4 h-4 text-[#D9541E] shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-[#111111] dark:text-white">Overall Opportunity</div>
            <p className="text-[#6B665E] dark:text-[#A69E92] mt-0.5 leading-relaxed">
              Evaluated as <strong className="text-[#111111] dark:text-[#F3EEE3]">{oppSignal} Opportunity</strong> (Score:{' '}
              <strong className="text-[#D9541E] tabular-nums">{oppScore}/100</strong>).
            </p>
          </div>
        </div>

        <div className="editorial-subcard p-3 rounded-lg flex items-start gap-2.5">
          <TrendingUp className="w-4 h-4 text-[#254C3B] dark:text-[#4C9A77] shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-[#111111] dark:text-white">ML Performance Tier</div>
            <p className="text-[#6B665E] dark:text-[#A69E92] mt-0.5 leading-relaxed">
              Classified as <strong className="text-[#111111] dark:text-[#F3EEE3]">{prediction}</strong>
              {predProbValue != null ? ` (${predProbValue}% predicted-class probability)` : ''}.
            </p>
          </div>
        </div>

        <div className="editorial-subcard p-3 rounded-lg flex items-start gap-2.5">
          <MapPin className="w-4 h-4 text-[#111111] dark:text-[#E6DED0] shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-[#111111] dark:text-white">Location Context</div>
            <p className="text-[#6B665E] dark:text-[#A69E92] mt-0.5 leading-relaxed">
              {isLocFound
                ? `${locName}: ${Number(restCount).toLocaleString('en-IN')} records · Median ₹${medianCost} · ${onlineRate}% delivery.`
                : `No historical dataset records found for ${locName}.`}
            </p>
          </div>
        </div>

        <div className="editorial-subcard p-3 rounded-lg flex items-start gap-2.5">
          <Store className="w-4 h-4 text-[#D9541E] shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-[#111111] dark:text-white">Live Competition</div>
            <p className="text-[#6B665E] dark:text-[#A69E92] mt-0.5 leading-relaxed">
              {compCount} competitors · Avg rating {avgRating}★ · {highRatingComp} rated ≥4.5★.
            </p>
          </div>
        </div>

        <div className="editorial-subcard p-3 rounded-lg flex items-start gap-2.5">
          <DollarSign className="w-4 h-4 text-[#254C3B] dark:text-[#4C9A77] shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-[#111111] dark:text-white">Projected Financials (Est.)</div>
            <p className="text-[#6B665E] dark:text-[#A69E92] mt-0.5 leading-relaxed tabular-nums">
              Rev {rev} · Exp {exp} · Profit <strong className="text-[#254C3B] dark:text-[#4C9A77]">{profit}</strong> ({margin}) · BEP {breakEven}.
            </p>
          </div>
        </div>

        <div className="editorial-subcard p-3 rounded-lg border-[#A63222]/30 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-[#A63222] dark:text-[#E06C5B] shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-[#A63222] dark:text-[#E06C5B]">Primary Risk Signal</div>
            <p className="text-[#6B665E] dark:text-[#A69E92] mt-0.5 leading-relaxed">{keyRisk}</p>
          </div>
        </div>
      </div>

      {/* Audio Summary / Business Takeaway Brief */}
      <div className="bg-[#F8F5EE] dark:bg-[#161513] rounded-lg border border-[#E6DED0] dark:border-[#2F2B25] p-4">
        <div className="text-[11px] font-bold uppercase tracking-[0.08em] text-[#6B665E] dark:text-[#A69E92] mb-1.5">
          Executive Audio Brief
        </div>
        <p className="text-xs sm:text-sm text-[#111111] dark:text-[#F3EEE3] leading-relaxed">
          {businessTakeaway}
        </p>
        <TextToSpeechButton text={businessTakeaway} />
      </div>

      {/* LLM-Generated Overall Business Recommendations Panel */}
      <AIInsightsPanel
        insights={llmRecommendations}
        title="AI Insights — Overall Business Takeaway"
        subtitle="Opportunity · Risk · Next Step"
      />
    </section>
  );
}
