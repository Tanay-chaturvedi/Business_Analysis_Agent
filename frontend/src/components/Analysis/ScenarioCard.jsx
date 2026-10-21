import React, { useState } from 'react';
import { SlidersHorizontal, CheckCircle2, ChevronDown, ChevronUp, BrainCircuit, DollarSign, AlertCircle } from 'lucide-react';

export default function ScenarioCard({ scenarioData }) {
  const [showTechnicalShap, setShowTechnicalShap] = useState(false);

  if (!scenarioData || !scenarioData.comparison) return null;

  const {
    baseline = {},
    scenario = {},
    comparison = {},
    deltas = {},
    changed_fields = [],
    model_driver_changes = [],
    opportunity_breakdown = {},
    financial_comparison = null,
    financialComparison = null
  } = scenarioData;

  const finComp = financial_comparison || financialComparison;
  const finBase = finComp?.baseline || {};
  const finScen = finComp?.scenario || {};
  const finChanges = finComp?.changes || {};

  const revDelta = finChanges.monthly_revenue?.absolute ?? ((finScen.monthly_revenue || 0) - (finBase.monthly_revenue || 0));
  const expDelta = finChanges.monthly_expenses?.absolute ?? ((finScen.monthly_expenses || 0) - (finBase.monthly_expenses || 0));
  const profitDelta = finChanges.estimated_operating_profit?.absolute ?? ((finScen.estimated_operating_profit || 0) - (finBase.estimated_operating_profit || 0));
  const marginDelta = finChanges.operating_profit_margin?.absolute ?? ((finScen.operating_profit_margin || 0) - (finBase.operating_profit_margin || 0));
  const bepDelta = finChanges.break_even_customers_per_day?.absolute ?? (
    (finScen.break_even_customers_per_day != null && finBase.break_even_customers_per_day != null)
      ? finScen.break_even_customers_per_day - finBase.break_even_customers_per_day
      : null
  );

  const hasFinancialChanges = finComp?.has_financial_changes ?? (
    Math.abs(revDelta) > 1e-3 || Math.abs(expDelta) > 1e-3 || Math.abs(profitDelta) > 1e-3
  );

  const {
    base_score,
    scenario_score,
    score_delta,
    base_high_prob,
    scenario_high_prob,
    prob_delta_pct,
  } = comparison;

  const bParams = baseline.parameters || {};
  const sParams = scenario.parameters || {};

  const changedKeys = (changed_fields || []).map(f => typeof f === 'object' ? f.field : f);

  const paramDefs = [
    { key: 'primary_cuisine', label: 'Cuisine', val: (p) => p.primary_cuisine },
    { key: 'approx_cost_for_two', label: 'Cost for Two', val: (p) => p.approx_cost_for_two ? `₹${p.approx_cost_for_two}` : (p.approx_costfor_two_people ? `₹${p.approx_costfor_two_people}` : null) },
    { key: 'location', label: 'Location', val: (p) => p.location },
    { key: 'online_order', label: 'Online Ordering', val: (p) => p.online_order === true || p.online_order === 1 ? 'Yes' : 'No' },
    { key: 'book_table', label: 'Table Booking', val: (p) => p.book_table === true || p.book_table === 1 ? 'Yes' : 'No' },
    { key: 'primary_rest_type', label: 'Restaurant Type', val: (p) => p.primary_rest_type || p.restaurant_type },
  ];

  const whatChanged = [];
  paramDefs.forEach(({ key, label, val }) => {
    const bVal = val(bParams);
    const sVal = val(sParams);

    if (changedKeys.includes(key) || (bVal !== undefined && sVal !== undefined && bVal !== sVal)) {
      whatChanged.push({ label, oldVal: bVal || 'Baseline', newVal: sVal || 'Scenario' });
    }
  });

  const baseCompScore = baseline.competition_score ?? opportunity_breakdown.baseline_competition ?? 54.6;
  const scenCompScore = scenario.competition_score ?? opportunity_breakdown.scenario_competition ?? 54.6;
  const compDelta = deltas.competition_score ?? opportunity_breakdown.competition_delta ?? 0;

  const getSimpleDriverEffect = (driver) => {
    if (driver.shap_delta > 0) return 'Support for the prediction increased.';
    if (driver.shap_delta < 0) return 'Support for the prediction decreased.';
    return 'Neutral impact on prediction.';
  };

  const primaryChangedField = whatChanged.length > 0 ? whatChanged[0].label : 'parameter';
  const probDirection = prob_delta_pct > 0 ? 'increased' : prob_delta_pct < 0 ? 'decreased' : 'remained unchanged';
  const scoreDirection = score_delta > 0 ? 'increased' : score_delta < 0 ? 'decreased' : 'remained unchanged';

  const whatThisMeansBullets = [
    `Modifying the ${primaryChangedField} changed the model's predicted performance evaluation.`,
    `The predicted High-performance probability ${probDirection} from ${base_high_prob}% to ${scenario_high_prob}% (${prob_delta_pct >= 0 ? '+' : ''}${prob_delta_pct} pp).`,
    `The Opportunity Score ${scoreDirection} from ${base_score} to ${scenario_score} (${score_delta >= 0 ? '+' : ''}${score_delta} pts).`,
    `Competition score ${compDelta === 0 ? 'remained unchanged at ' + baseCompScore : 'shifted from ' + baseCompScore + ' to ' + scenCompScore} because competition inputs ${compDelta === 0 ? 'were not altered' : 'were updated'}.`,
    hasFinancialChanges
      ? `Financial estimates shifted: operating profit changed by ${profitDelta >= 0 ? '+₹' + Math.round(profitDelta).toLocaleString('en-IN') : '-₹' + Math.round(Math.abs(profitDelta)).toLocaleString('en-IN')}.`
      : `Financial impact: No change based on current financial assumptions.`,
    `Overall, the scenario shows ${score_delta > 0 ? 'a favorable' : score_delta < 0 ? 'a lower' : 'an identical'} opportunity profile compared with the baseline.`
  ];

  return (
    <div className="glass-panel p-5 rounded-2xl border border-purple-200 dark:border-purple-500/30 space-y-5 my-4 bg-white dark:bg-slate-900/90 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-600 dark:text-purple-400">
            <SlidersHorizontal className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm sm:text-base tracking-wide">
              WHAT-IF SCENARIO COMPARISON
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Baseline vs Scenario Analysis</p>
          </div>
        </div>

        <span className="text-xs font-bold px-3 py-1 rounded-full bg-purple-50 dark:bg-purple-500/10 border border-purple-200 dark:border-purple-500/30 text-purple-700 dark:text-purple-300">
          Scenario Mode
        </span>
      </div>

      {/* 1. SCENARIO CHANGES */}
      <div className="bg-purple-50 dark:bg-slate-950/70 p-4 rounded-xl border border-purple-200 dark:border-purple-500/30 space-y-2 text-xs">
        <div className="font-semibold text-purple-800 dark:text-purple-300 uppercase tracking-wider flex items-center justify-between">
          <span>SCENARIO CHANGES</span>
          <span className="text-[10px] bg-purple-100 dark:bg-purple-500/20 px-2 py-0.5 rounded text-purple-800 dark:text-purple-200 font-medium">
            {whatChanged.length} parameter{whatChanged.length === 1 ? '' : 's'} changed
          </span>
        </div>

        {whatChanged.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
            {whatChanged.map((item, idx) => (
              <div key={idx} className="flex justify-between items-center bg-white dark:bg-slate-900/80 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-xs">
                <span className="text-slate-600 dark:text-slate-400 font-medium">{item.label}:</span>
                <span className="font-semibold text-slate-900 dark:text-slate-200">
                  {item.oldVal} → <strong className="text-purple-700 dark:text-purple-300">{item.newVal}</strong>
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-slate-500 dark:text-slate-400 italic py-1">No parameters changed from baseline.</div>
        )}
      </div>

      {/* 2. SCENARIO COMPARISON TABLE */}
      <div className="bg-slate-50 dark:bg-slate-950/70 p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-3">
        <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
          SCENARIO COMPARISON
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left text-slate-700 dark:text-slate-300">
            <thead className="text-[11px] text-slate-500 dark:text-slate-400 uppercase bg-slate-100 dark:bg-slate-900/80 border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Metric</th>
                <th className="py-2.5 px-3">Baseline</th>
                <th className="py-2.5 px-3">Scenario</th>
                <th className="py-2.5 px-3 text-right">Change</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800/60 font-medium">
              <tr>
                <td className="py-2.5 px-3 text-slate-900 dark:text-slate-200">High Probability</td>
                <td className="py-2.5 px-3">{base_high_prob}%</td>
                <td className="py-2.5 px-3 text-slate-900 dark:text-white font-bold">{scenario_high_prob}%</td>
                <td className={`py-2.5 px-3 text-right font-bold ${prob_delta_pct > 0 ? 'text-emerald-600 dark:text-emerald-400' : prob_delta_pct < 0 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-500'}`}>
                  {prob_delta_pct > 0 ? `+${prob_delta_pct} pp` : `${prob_delta_pct} pp`}
                </td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-slate-900 dark:text-slate-200">Opportunity Score</td>
                <td className="py-2.5 px-3">{base_score}</td>
                <td className="py-2.5 px-3 text-slate-900 dark:text-white font-bold">{scenario_score}</td>
                <td className={`py-2.5 px-3 text-right font-bold ${score_delta > 0 ? 'text-emerald-600 dark:text-emerald-400' : score_delta < 0 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-500'}`}>
                  {score_delta > 0 ? `+${score_delta}` : `${score_delta}`}
                </td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-slate-900 dark:text-slate-200">Competition Score</td>
                <td className="py-2.5 px-3">{baseCompScore}</td>
                <td className="py-2.5 px-3">{scenCompScore}</td>
                <td className={`py-2.5 px-3 text-right font-bold ${compDelta > 0 ? 'text-rose-600 dark:text-rose-400' : compDelta < 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-500'}`}>
                  {compDelta > 0 ? `+${compDelta}` : `${compDelta}`}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. MODEL DRIVER CHANGES */}
      <div className="bg-indigo-50 dark:bg-indigo-950/20 p-4 rounded-xl border border-indigo-200 dark:border-indigo-500/30 space-y-3 text-xs">
        <div className="font-bold text-indigo-900 dark:text-indigo-300 flex items-center justify-between text-xs sm:text-sm">
          <span className="flex items-center gap-1.5">
            <BrainCircuit className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
            <span>MODEL DRIVER CHANGES</span>
          </span>
          <span className="text-[10px] text-slate-500 dark:text-slate-400 font-normal">Random Forest & SHAP</span>
        </div>

        {model_driver_changes.length > 0 ? (
          <div className="space-y-2">
            {model_driver_changes.map((driver, idx) => {
              const effectText = getSimpleDriverEffect(driver);
              const isPos = driver.shap_delta > 0;
              const isNeg = driver.shap_delta < 0;

              return (
                <div key={idx} className="bg-white dark:bg-slate-900/90 p-3 rounded-xl border border-slate-200 dark:border-slate-800 flex items-center justify-between gap-3 shadow-xs">
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-slate-100">{driver.display_name}</div>
                    <div className={`text-xs font-medium mt-0.5 ${isPos ? 'text-emerald-600 dark:text-emerald-400' : isNeg ? 'text-rose-600 dark:text-rose-400' : 'text-slate-500'}`}>
                      • {effectText}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-slate-500 dark:text-slate-400 text-[11px] bg-slate-100 dark:bg-slate-950 px-2 py-1 rounded border border-slate-200 dark:border-slate-800 block">
                      {driver.baseline_value} → <strong className="text-indigo-600 dark:text-indigo-300">{driver.scenario_value}</strong>
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-slate-500 dark:text-slate-400 italic">No significant model driver shifts detected for this scenario.</p>
        )}

        {/* Collapsible Technical SHAP Values */}
        <div className="pt-2 border-t border-indigo-200 dark:border-indigo-500/20">
          <button
            type="button"
            onClick={() => setShowTechnicalShap(!showTechnicalShap)}
            className="flex items-center gap-1.5 text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 transition-colors cursor-pointer"
          >
            {showTechnicalShap ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            <span>{showTechnicalShap ? 'Hide Exact SHAP Feature Values' : 'Show Exact SHAP Feature Values (Technical)'}</span>
          </button>

          {showTechnicalShap && (
            <div className="mt-2 p-3 bg-slate-100 dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800 text-[11px] space-y-1.5 text-slate-700 dark:text-slate-300">
              <div className="text-slate-500 dark:text-slate-400 italic mb-1">
                Note: SHAP values represent statistical feature contributions to the Random Forest model's output and do not indicate direct causal relationships.
              </div>
              {model_driver_changes.map((driver, idx) => (
                <div key={idx} className="flex justify-between border-b border-slate-200 dark:border-slate-900 pb-1">
                  <span className="text-slate-700 dark:text-slate-300">{driver.display_name}:</span>
                  <span className="font-mono text-indigo-700 dark:text-indigo-300">
                    Baseline: {driver.baseline_shap != null ? driver.baseline_shap.toFixed(4) : 'N/A'} | Scenario: {driver.scenario_shap != null ? driver.scenario_shap.toFixed(4) : 'N/A'} | Δ: {driver.shap_delta != null ? (driver.shap_delta >= 0 ? '+' : '') + driver.shap_delta.toFixed(4) : 'N/A'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 4. FINANCIAL IMPACT */}
      <div className="bg-emerald-50 dark:bg-emerald-950/20 p-4 rounded-xl border border-emerald-200 dark:border-emerald-500/30 space-y-3 text-xs">
        <div className="font-bold text-emerald-800 dark:text-emerald-300 flex items-center justify-between text-xs sm:text-sm">
          <span className="flex items-center gap-1.5">
            <DollarSign className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span>FINANCIAL IMPACT</span>
          </span>
          <span className="text-[10px] bg-emerald-100 dark:bg-emerald-500/20 px-2 py-0.5 rounded text-emerald-800 dark:text-emerald-200 font-medium">
            Financial Engine
          </span>
        </div>

        {hasFinancialChanges && finComp ? (
          <div className="space-y-3">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left text-slate-700 dark:text-slate-300">
                <thead className="text-[11px] text-slate-500 dark:text-slate-400 uppercase bg-white dark:bg-slate-900/80 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="py-2 px-2.5">Financial Metric</th>
                    <th className="py-2 px-2.5">Baseline</th>
                    <th className="py-2 px-2.5">Scenario</th>
                    <th className="py-2 px-2.5 text-right">Change</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800/60 font-medium">
                  <tr>
                    <td className="py-2 px-2.5 text-slate-900 dark:text-slate-200">Revenue</td>
                    <td className="py-2 px-2.5">₹{Math.round(finBase.monthly_revenue || 0).toLocaleString('en-IN')}</td>
                    <td className="py-2 px-2.5 text-slate-900 dark:text-white font-bold">₹{Math.round(finScen.monthly_revenue || 0).toLocaleString('en-IN')}</td>
                    <td className={`py-2 px-2.5 text-right font-bold ${revDelta >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
                      {revDelta >= 0 ? `+₹${Math.round(revDelta).toLocaleString('en-IN')}` : `-₹${Math.round(Math.abs(revDelta)).toLocaleString('en-IN')}`}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-2.5 text-slate-900 dark:text-slate-200">Operating Profit</td>
                    <td className="py-2 px-2.5">₹{Math.round(finBase.estimated_operating_profit || 0).toLocaleString('en-IN')}</td>
                    <td className="py-2 px-2.5 text-slate-900 dark:text-white font-bold">₹{Math.round(finScen.estimated_operating_profit || 0).toLocaleString('en-IN')}</td>
                    <td className={`py-2 px-2.5 text-right font-bold ${profitDelta >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
                      {profitDelta >= 0 ? `+₹${Math.round(profitDelta).toLocaleString('en-IN')}` : `-₹${Math.round(Math.abs(profitDelta)).toLocaleString('en-IN')}`}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-2.5 text-slate-900 dark:text-slate-200">Profit Margin</td>
                    <td className="py-2 px-2.5">{finBase.operating_profit_margin != null ? `${finBase.operating_profit_margin.toFixed(1)}%` : 'N/A'}</td>
                    <td className="py-2 px-2.5 text-slate-900 dark:text-white font-bold">{finScen.operating_profit_margin != null ? `${finScen.operating_profit_margin.toFixed(1)}%` : 'N/A'}</td>
                    <td className={`py-2 px-2.5 text-right font-bold ${marginDelta >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
                      {marginDelta >= 0 ? `+${marginDelta.toFixed(1)} pp` : `${marginDelta.toFixed(1)} pp`}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-2.5 text-slate-900 dark:text-slate-200">Break-even/day</td>
                    <td className="py-2 px-2.5">{finBase.break_even_customers_per_day != null ? `${finBase.break_even_customers_per_day.toFixed(1)}` : 'N/A'}</td>
                    <td className="py-2 px-2.5 text-amber-600 dark:text-amber-300 font-bold">{finScen.break_even_customers_per_day != null ? `${finScen.break_even_customers_per_day.toFixed(1)}` : 'N/A'}</td>
                    <td className={`py-2 px-2.5 text-right font-bold ${bepDelta <= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
                      {bepDelta != null ? (bepDelta >= 0 ? `+${bepDelta.toFixed(1)}` : `${bepDelta.toFixed(1)}`) : 'N/A'}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900/60 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
            <AlertCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span className="font-medium">Financial impact: No change based on the current financial assumptions.</span>
          </div>
        )}
      </div>

      {/* 5. WHAT THIS MEANS */}
      <div className="bg-slate-50 dark:bg-slate-950/80 p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-3 text-xs">
        <div className="font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-1.5 text-xs sm:text-sm">
          <CheckCircle2 className="w-4 h-4 text-purple-600 dark:text-purple-400 shrink-0" />
          <span>WHAT THIS MEANS</span>
        </div>

        <div className="space-y-2 text-slate-700 dark:text-slate-300">
          {whatThisMeansBullets.map((bullet, i) => (
            <div key={i} className="flex items-start gap-2 bg-white dark:bg-slate-900/60 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-xs">
              <span className="text-purple-600 dark:text-purple-400 font-bold">•</span>
              <span>{bullet}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
