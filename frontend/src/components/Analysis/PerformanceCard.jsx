import React, { useState } from 'react';
import { Bot, ChevronDown, ChevronUp, CheckCircle2, ArrowDownRight, Sparkles, Info, HelpCircle } from 'lucide-react';

function getFallbackName(rawName) {
  if (!rawName) return 'Feature';
  const clean = rawName.replace(/^categorical__/, '').replace(/^numerical__/, '');
  return clean.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function getInfluenceLabel(ratio) {
  if (ratio >= 0.7) return 'Strong influence';
  if (ratio >= 0.3) return 'Moderate influence';
  return 'Minor influence';
}

function BusinessFeatureCard({ feat, maxAbsShap, isPos }) {
  const dName = feat.display_name || getFallbackName(feat.feature || feat.name);
  const rawShap = feat.shap_value ?? feat.contribution ?? 0;
  const valStr = feat.feature_value || feat.value;
  const absShap = Math.abs(rawShap);
  const ratio = maxAbsShap > 0 ? absShap / maxAbsShap : 0.25;
  const barPercent = Math.min(100, Math.max(15, ratio * 100));
  const influenceText = getInfluenceLabel(ratio);

  return (
    <div className="bg-slate-50 dark:bg-slate-950/70 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2.5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        {/* Factor Name & Input Value */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-slate-900 dark:text-slate-100 text-xs sm:text-sm">{dName}</span>
          {valStr && (
            <span className="px-2 py-0.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-medium text-slate-700 dark:text-slate-300">
              {valStr}
            </span>
          )}
        </div>

        {/* Business Friendly Status Tag */}
        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${isPos
                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30'
                : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30'
              }`}
          >
            {isPos ? '✓ Supports the prediction' : '↓ Reduces the prediction'}
          </span>
        </div>
      </div>

      {/* Influence Bar & Label */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-medium">
          <span>Model Influence</span>
          <span className={isPos ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}>{influenceText}</span>
        </div>
        <div className="h-1.5 w-full bg-slate-200 dark:bg-slate-900 rounded-full overflow-hidden border border-slate-300 dark:border-slate-800/80">
          <div
            style={{ width: `${barPercent}%` }}
            className={`h-full rounded-full transition-all duration-500 ${isPos ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
          />
        </div>
      </div>

      {/* Plain Language Interpretation */}
      <p className="text-[11px] text-slate-500 dark:text-slate-400 italic pt-0.5">
        {isPos
          ? `This factor positively influenced the model's prediction.`
          : `This factor pulled down the model's prediction for this class.`}
      </p>
    </div>
  );
}

export default function PerformanceCard({ performanceData }) {
  const [showTechnical, setShowTechnical] = useState(false);

  if (!performanceData) return null;

  const { prediction = 'HIGH', probabilities = {}, explanation = {} } = performanceData;

  const highProb = ((probabilities.High || 0) * 100).toFixed(1);
  const medProb = ((probabilities.Medium || 0) * 100).toFixed(1);
  const lowProb = ((probabilities.Low || 0) * 100).toFixed(1);

  const getBadgeColor = (pred) => {
    switch (pred.toUpperCase()) {
      case 'HIGH':
        return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30';
      default:
        return 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30';
    }
  };

  const topFeatures = explanation.top_features || [];

  // Group into positive (supporting) and negative (reducing) drivers
  const positiveDrivers = topFeatures
    .filter((f) => (f.direction === 'positive') || ((f.shap_value ?? f.contribution ?? 0) >= 0))
    .sort((a, b) => Math.abs(b.shap_value ?? b.contribution ?? 0) - Math.abs(a.shap_value ?? a.contribution ?? 0));

  const negativeDrivers = topFeatures
    .filter((f) => (f.direction === 'negative') || ((f.shap_value ?? f.contribution ?? 0) < 0))
    .sort((a, b) => Math.abs(b.shap_value ?? b.contribution ?? 0) - Math.abs(a.shap_value ?? a.contribution ?? 0));

  // Maximum SHAP magnitude for relative bar width
  const maxAbsShap = Math.max(
    ...topFeatures.map((f) => Math.abs(f.shap_value ?? f.contribution ?? 0)),
    0.001
  );

  return (
    <div className="glass-panel p-5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4">
      {/* Card Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-600 dark:text-indigo-400">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm sm:text-base flex items-center gap-1.5">
              ML Performance Prediction
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Random Forest Intelligence</p>
          </div>
        </div>

        {/* Prediction Badge */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 dark:text-slate-400">Prediction:</span>
          <span className={`text-xs font-bold px-3 py-1 rounded-full border ${getBadgeColor(prediction)}`}>
            {prediction}
          </span>
        </div>
      </div>

      {/* Horizontal Probability Bar Visualization */}
      <div className="space-y-3 bg-slate-50 dark:bg-slate-950/60 p-4 rounded-xl border border-slate-200 dark:border-slate-800/80">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
          <span>Model Confidence Breakdown</span>
          <span className="text-indigo-600 dark:text-indigo-400 font-bold">Model Confidence: {highProb}%</span>
        </div>

        {/* Stacked Bar */}
        <div className="h-3 w-full bg-slate-200 dark:bg-slate-900 rounded-full overflow-hidden flex p-0.5 border border-slate-300 dark:border-slate-800">
          <div
            style={{ width: `${highProb}%` }}
            className="bg-emerald-500 h-full rounded-l-full transition-all duration-500"
            title={`High Confidence: ${highProb}%`}
          />
          <div
            style={{ width: `${medProb}%` }}
            className="bg-amber-500 h-full transition-all duration-500"
            title={`Medium Confidence: ${medProb}%`}
          />
          <div
            style={{ width: `${lowProb}%` }}
            className="bg-rose-500 h-full rounded-r-full transition-all duration-500"
            title={`Low Confidence: ${lowProb}%`}
          />
        </div>

        {/* Legend Chips */}
        <div className="grid grid-cols-3 gap-2 pt-1 text-center text-xs">
          <div className="bg-white dark:bg-slate-900/80 p-2 rounded-lg border border-slate-200 dark:border-slate-800 shadow-xs">
            <div className="text-[10px] text-slate-500 dark:text-slate-400 font-medium flex items-center justify-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" /> High
            </div>
            <div className="font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">{highProb}%</div>
          </div>
          <div className="bg-white dark:bg-slate-900/80 p-2 rounded-lg border border-slate-200 dark:border-slate-800 shadow-xs">
            <div className="text-[10px] text-slate-500 dark:text-slate-400 font-medium flex items-center justify-center gap-1">
              <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" /> Medium
            </div>
            <div className="font-bold text-amber-600 dark:text-amber-400 mt-0.5">{medProb}%</div>
          </div>
          <div className="bg-white dark:bg-slate-900/80 p-2 rounded-lg border border-slate-200 dark:border-slate-800 shadow-xs">
            <div className="text-[10px] text-slate-500 dark:text-slate-400 font-medium flex items-center justify-center gap-1">
              <span className="w-2 h-2 rounded-full bg-rose-500 inline-block" /> Low
            </div>
            <div className="font-bold text-rose-600 dark:text-rose-400 mt-0.5">{lowProb}%</div>
          </div>
        </div>
      </div>

      {/* WHY DID THE MODEL PREDICT THIS? Section */}
      <div className="space-y-4 border-t border-slate-200 dark:border-slate-800/80 pt-4">
        <div>
          <h4 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            WHY DID THE MODEL PREDICT THIS?
          </h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mt-0.5">
            Key factors influencing the prediction
          </p>
        </div>

        {topFeatures.length > 0 ? (
          <div className="space-y-4">
            {/* Supporting Factors Section */}
            {positiveDrivers.length > 0 && (
              <div className="space-y-2.5">
                <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 border-b border-emerald-500/20 pb-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <span>Factors Supporting the Prediction</span>
                </div>
                <div className="space-y-2">
                  {positiveDrivers.map((feat, idx) => (
                    <BusinessFeatureCard key={idx} feat={feat} maxAbsShap={maxAbsShap} isPos={true} />
                  ))}
                </div>
              </div>
            )}

            {/* Reducing Factors Section */}
            {negativeDrivers.length > 0 && (
              <div className="space-y-2.5">
                <div className="text-xs font-bold text-rose-600 dark:text-rose-400 flex items-center gap-1.5 border-b border-rose-500/20 pb-1.5">
                  <ArrowDownRight className="w-4 h-4 text-rose-600 dark:text-rose-400" />
                  <span>Factors Reducing the Prediction</span>
                </div>
                <div className="space-y-2">
                  {negativeDrivers.map((feat, idx) => (
                    <BusinessFeatureCard key={idx} feat={feat} maxAbsShap={maxAbsShap} isPos={false} />
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-3 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-200 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 italic">
            Model explanation is unavailable for this prediction.
          </div>
        )}

        {/* Optional Technical Details Toggle */}
        <div className="pt-2 border-t border-slate-200 dark:border-slate-900">
          <button
            onClick={() => setShowTechnical(!showTechnical)}
            className="text-xs text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-300 font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <HelpCircle className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
            <span>How is this explained? / Technical details</span>
            {showTechnical ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showTechnical && (
            <div className="mt-2.5 p-3.5 bg-slate-100 dark:bg-slate-950/90 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2 text-xs text-slate-700 dark:text-slate-300">
              <div className="flex items-center gap-1.5 text-indigo-600 dark:text-indigo-300 font-semibold">
                <Info className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
                <span>SHAP (SHapley Additive exPlanations) Method</span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                These factors are identified using SHAP, a mathematical method that measures how much each feature pulled the model's output towards or away from a prediction class. They explain model behavior and do not prove direct causality.
              </p>
              {topFeatures.length > 0 && (
                <div className="pt-2 space-y-1 font-mono text-[11px]">
                  <div className="text-[10px] text-slate-400 dark:text-slate-500 uppercase font-sans font-bold">Raw SHAP Values</div>
                  {topFeatures.map((f, idx) => {
                    const rawVal = f.shap_value ?? f.contribution ?? 0;
                    return (
                      <div key={idx} className="flex justify-between items-center bg-white dark:bg-slate-900/60 px-2 py-1 rounded border border-slate-200 dark:border-slate-800/80">
                        <span className="text-slate-600 dark:text-slate-400">{f.feature || f.name}</span>
                        <span className={rawVal >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}>
                          {rawVal >= 0 ? `+${rawVal.toFixed(4)}` : rawVal.toFixed(4)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
