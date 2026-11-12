import React, { useState } from 'react';
import { Cpu, ChevronDown, ChevronUp, Info } from 'lucide-react';
import AIInsightsPanel from './AIInsightsPanel';

export default function PerformanceCard({ performanceData, insights }) {
  const [showTechnical, setShowTechnical] = useState(false);

  if (!performanceData) return null;

  const { prediction = 'High', probabilities = {} } = performanceData;

  const formatProb = (val) => {
    if (val == null || isNaN(val)) return '0.0';
    const num = Number(val);
    const pct = num <= 1.0 ? num * 100 : num;
    return pct.toFixed(1);
  };

  const highProb = formatProb(probabilities.High ?? probabilities.high);
  const medProb = formatProb(probabilities.Medium ?? probabilities.medium);
  const lowProb = formatProb(probabilities.Low ?? probabilities.low);

  // Predicted-class probability strictly matching `probabilities[prediction]`
  const getPredictedProb = () => {
    if (!prediction) return highProb;
    const predLower = String(prediction).toLowerCase();
    for (const [key, val] of Object.entries(probabilities)) {
      if (key.toLowerCase() === predLower) {
        return formatProb(val);
      }
    }
    if (predLower === 'medium') return medProb;
    if (predLower === 'low') return lowProb;
    return highProb;
  };

  const predictedClassProb = getPredictedProb();

  const getBadgeStyle = (pred) => {
    switch (String(pred).toUpperCase()) {
      case 'HIGH':
        return 'bg-[#254C3B]/10 text-[#254C3B] dark:text-[#4C9A77] border-[#254C3B]/30';
      case 'MEDIUM':
        return 'bg-[#B4690E]/10 text-[#B4690E] dark:text-[#E09F3E] border-[#B4690E]/30';
      default:
        return 'bg-[#A63222]/10 text-[#A63222] dark:text-[#E06C5B] border-[#A63222]/30';
    }
  };

  const classCards = [
    {
      label: 'High',
      pct: highProb,
      dotColor: 'bg-[#254C3B] dark:bg-[#4C9A77]',
      valueColor: 'text-[#254C3B] dark:text-[#4C9A77]',
    },
    {
      label: 'Medium',
      pct: medProb,
      dotColor: 'bg-[#B4690E] dark:bg-[#E09F3E]',
      valueColor: 'text-[#B4690E] dark:text-[#E09F3E]',
    },
    {
      label: 'Low',
      pct: lowProb,
      dotColor: 'bg-[#A63222] dark:bg-[#E06C5B]',
      valueColor: 'text-[#A63222] dark:text-[#E06C5B]',
    },
  ];

  return (
    <section className="editorial-panel rounded-xl p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#E6DED0] dark:border-[#2F2B25]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#EAE3D5] dark:bg-[#22201D] border border-[#D4C9B6] dark:border-[#3A352E] text-[#111111] dark:text-[#F3EEE3]">
            <Cpu className="w-4 h-4 text-[#D9541E]" />
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#6B665E] dark:text-[#A69E92]">
              02 · Machine Learning Classification
            </div>
            <h3 className="font-heading font-bold text-[#111111] dark:text-[#F3EEE3] text-sm sm:text-base">
              ML Performance Prediction
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-[#6B665E] dark:text-[#A69E92] font-medium">Predicted Tier:</span>
          <span className={`text-xs font-bold px-3 py-1 rounded-md border ${getBadgeStyle(prediction)}`}>
            {prediction}
          </span>
        </div>
      </div>

      {/* Probability Breakdown Panel */}
      <div className="editorial-subcard p-4 rounded-lg space-y-3.5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <div className="text-xs font-semibold text-[#111111] dark:text-[#F3EEE3]">
              Class Probability Distribution
            </div>
            <p className="text-[11px] text-[#6B665E] dark:text-[#A69E92] mt-0.5">
              Predicted-class probability reflects peer-group similarity — not overall model accuracy.
            </p>
          </div>
          <div className="text-right">
            <span className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] mr-1.5">
              Predicted-Class Probability:
            </span>
            <span className="text-sm font-bold text-[#D9541E] tabular-nums">
              {predictedClassProb}%
            </span>
          </div>
        </div>

        {/* Clean Stacked Probability Distribution Bar */}
        <div className="h-2.5 w-full bg-[#E6DED0] dark:bg-[#2F2B25] rounded-full overflow-hidden flex">
          <div
            style={{ width: `${highProb}%` }}
            className="bg-[#254C3B] dark:bg-[#4C9A77] h-full transition-all duration-300"
            title={`High Probability: ${highProb}%`}
          />
          <div
            style={{ width: `${medProb}%` }}
            className="bg-[#B4690E] dark:bg-[#E09F3E] h-full transition-all duration-300"
            title={`Medium Probability: ${medProb}%`}
          />
          <div
            style={{ width: `${lowProb}%` }}
            className="bg-[#A63222] dark:bg-[#E06C5B] h-full transition-all duration-300"
            title={`Low Probability: ${lowProb}%`}
          />
        </div>

        {/* 3 Class Probability Tiles */}
        <div className="grid grid-cols-3 gap-2.5">
          {classCards.map((item) => {
            const isPredicted = String(prediction).toLowerCase() === item.label.toLowerCase();
            return (
              <div
                key={item.label}
                className={`p-2.5 rounded-lg border text-center transition-colors ${isPredicted
                    ? 'bg-white dark:bg-[#1A1917] border-[#D9541E] ring-1 ring-[#D9541E]/25'
                    : 'bg-white/70 dark:bg-[#161513] border-[#E6DED0] dark:border-[#2F2B25]'
                  }`}
              >
                <div className="text-[11px] font-medium text-[#6B665E] dark:text-[#A69E92] flex items-center justify-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${item.dotColor}`} />
                  <span>{item.label}</span>
                  {isPredicted && (
                    <span className="text-[9px] font-bold uppercase px-1.5 py-0.2 rounded bg-[#D9541E]/10 text-[#D9541E]">
                      Top
                    </span>
                  )}
                </div>
                <div className={`text-base font-bold mt-1 tabular-nums ${item.valueColor}`}>
                  {item.pct}%
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Expandable Technical Scope Details */}
      <div className="pt-1">
        <button
          type="button"
          onClick={() => setShowTechnical(!showTechnical)}
          className="text-xs text-[#6B665E] hover:text-[#111111] dark:text-[#A69E92] dark:hover:text-white font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
        >
          <Info className="w-3.5 h-3.5 text-[#D9541E]" />
          <span>Model Scope & Methodology</span>
          {showTechnical ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showTechnical && (
          <div className="mt-2.5 p-3.5 editorial-subcard rounded-lg text-xs text-[#6B665E] dark:text-[#A69E92] leading-relaxed space-y-1.5">
            <div className="font-semibold text-[#111111] dark:text-[#F3EEE3]">
              300-Tree Random Forest Classifier
            </div>
            <p className="text-[11px]">
              Evaluates pricing tier, cuisine format, digital ordering, table booking, and historical neighborhood benchmarks across 33,332 Bengaluru restaurant records. Class probabilities sum to 100% and express statistical tier distribution rather than deterministic financial success.
            </p>
          </div>
        )}
      </div>

      {/* Compact LLM AI Insights */}
      <AIInsightsPanel insights={insights} subtitle="Classification Guidance" />
    </section>
  );
}
