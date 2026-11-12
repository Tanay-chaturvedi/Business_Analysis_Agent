import React from 'react';
import { SlidersHorizontal, CheckCircle2, BrainCircuit, DollarSign, AlertCircle } from 'lucide-react';

export default function ScenarioCard({ scenarioData }) {
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
    financialComparison = null,
  } = scenarioData;

  const finComp = financial_comparison || financialComparison;
  const finBase = finComp?.baseline || {};
  const finScen = finComp?.scenario || {};
  const finChanges = finComp?.changes || {};

  const revDelta = finChanges.monthly_revenue?.absolute ?? ((finScen.monthly_revenue || 0) - (finBase.monthly_revenue || 0));
  const profitDelta = finChanges.estimated_operating_profit?.absolute ?? ((finScen.estimated_operating_profit || 0) - (finBase.estimated_operating_profit || 0));
  const marginDelta = finChanges.operating_profit_margin?.absolute ?? ((finScen.operating_profit_margin || 0) - (finBase.operating_profit_margin || 0));
  const bepDelta = finChanges.break_even_customers_per_day?.absolute ?? (
    (finScen.break_even_customers_per_day != null && finBase.break_even_customers_per_day != null)
      ? finScen.break_even_customers_per_day - finBase.break_even_customers_per_day
      : null
  );

  const hasFinancialChanges = finComp?.has_financial_changes ?? (
    Math.abs(revDelta) > 1e-3 || Math.abs(profitDelta) > 1e-3
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

  const changedKeys = (changed_fields || []).map((f) => (typeof f === 'object' ? f.field : f));

  const paramDefs = [
    { key: 'primary_cuisine', label: 'Cuisine', val: (p) => p.primary_cuisine },
    {
      key: 'approx_cost_for_two',
      label: 'Cost for Two',
      val: (p) =>
        p.approx_cost_for_two
          ? `₹${p.approx_cost_for_two}`
          : p.approx_costfor_two_people
            ? `₹${p.approx_costfor_two_people}`
            : null,
    },
    { key: 'location', label: 'Location', val: (p) => p.location },
    { key: 'online_order', label: 'Online Ordering', val: (p) => (p.online_order === true || p.online_order === 1 ? 'Yes' : 'No') },
    { key: 'book_table', label: 'Table Booking', val: (p) => (p.book_table === true || p.book_table === 1 ? 'Yes' : 'No') },
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
    if (driver.direction === 'positive') return 'Support for High tier increased.';
    if (driver.direction === 'negative') return 'Support for High tier decreased.';
    return 'Neutral impact on prediction.';
  };

  const primaryChangedField = whatChanged.length > 0 ? whatChanged[0].label : 'parameter';
  const probDirection = prob_delta_pct > 0 ? 'increased' : prob_delta_pct < 0 ? 'decreased' : 'remained unchanged';
  const scoreDirection = score_delta > 0 ? 'increased' : score_delta < 0 ? 'decreased' : 'remained unchanged';

  const whatThisMeansBullets = [
    `Modifying ${primaryChangedField} updated the Random Forest class distribution.`,
    `Predicted High-tier probability ${probDirection} from ${base_high_prob}% to ${scenario_high_prob}% (${prob_delta_pct >= 0 ? '+' : ''}${prob_delta_pct} pp).`,
    `Opportunity Score ${scoreDirection} from ${base_score} to ${scenario_score} (${score_delta >= 0 ? '+' : ''}${score_delta} pts).`,
    `Competition score ${compDelta === 0 ? `remained unchanged at ${baseCompScore}` : `shifted from ${baseCompScore} to ${scenCompScore}`}.`,
    hasFinancialChanges
      ? `Projected operating profit shifted by ${profitDelta >= 0 ? `+₹${Math.round(profitDelta).toLocaleString('en-IN')}` : `-₹${Math.round(Math.abs(profitDelta)).toLocaleString('en-IN')}`}.`
      : 'Financial estimates remained unchanged under current assumptions.',
  ];

  return (
    <section className="editorial-panel rounded-xl p-5 space-y-4 my-3 border-l-2 border-l-[#D9541E]">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#E6DED0] dark:border-[#2F2B25]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#EAE3D5] dark:bg-[#22201D] border border-[#D4C9B6] dark:border-[#3A352E]">
            <SlidersHorizontal className="w-4 h-4 text-[#D9541E]" />
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#6B665E] dark:text-[#A69E92]">
              What-If Sensitivity
            </div>
            <h3 className="font-heading font-bold text-[#111111] dark:text-[#F3EEE3] text-sm sm:text-base">
              Scenario Comparison
            </h3>
          </div>
        </div>

        <span className="text-[11px] font-semibold px-2.5 py-1 rounded-md bg-[#D9541E]/10 border border-[#D9541E]/30 text-[#D9541E]">
          Baseline vs Scenario
        </span>
      </div>

      {/* 1. Parameter Deltas */}
      <div className="editorial-subcard p-3.5 rounded-lg space-y-2 text-xs">
        <div className="font-bold text-[#111111] dark:text-[#F3EEE3] uppercase tracking-[0.06em] text-[10px] flex items-center justify-between">
          <span>Modified Parameters</span>
          <span className="text-[#6B665E] dark:text-[#A69E92] font-medium normal-case">
            {whatChanged.length} change{whatChanged.length === 1 ? '' : 's'}
          </span>
        </div>

        {whatChanged.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {whatChanged.map((item, idx) => (
              <div key={idx} className="flex justify-between items-center bg-white dark:bg-[#1A1917] p-2.5 rounded-md border border-[#E6DED0] dark:border-[#2F2B25]">
                <span className="text-[#6B665E] dark:text-[#A69E92] font-medium">{item.label}:</span>
                <span className="font-semibold text-[#111111] dark:text-[#F3EEE3]">
                  {item.oldVal} → <strong className="text-[#D9541E]">{item.newVal}</strong>
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-[#6B665E] dark:text-[#A69E92] italic py-1">No parameters altered from baseline.</div>
        )}
      </div>

      {/* 2. Score & Probability Table */}
      <div className="editorial-subcard p-3.5 rounded-lg space-y-2.5">
        <div className="text-[10px] font-bold text-[#111111] dark:text-[#F3EEE3] uppercase tracking-[0.06em]">
          Market & ML Comparison
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left tabular-nums">
            <thead className="text-[10px] text-[#6B665E] dark:text-[#A69E92] uppercase border-b border-[#E6DED0] dark:border-[#2F2B25]">
              <tr>
                <th className="py-2 pr-3">Metric</th>
                <th className="py-2 px-3">Baseline</th>
                <th className="py-2 px-3">Scenario</th>
                <th className="py-2 pl-3 text-right">Delta</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EAE3D5] dark:divide-[#2C2823] font-medium">
              <tr>
                <td className="py-2 pr-3 text-[#111111] dark:text-[#F3EEE3]">High-Tier Probability</td>
                <td className="py-2 px-3 text-[#6B665E]">{base_high_prob}%</td>
                <td className="py-2 px-3 text-[#111111] dark:text-white font-bold">{scenario_high_prob}%</td>
                <td
                  className={`py-2 pl-3 text-right font-bold ${
                    prob_delta_pct > 0
                      ? 'text-[#254C3B] dark:text-[#4C9A77]'
                      : prob_delta_pct < 0
                        ? 'text-[#A63222] dark:text-[#E06C5B]'
                        : 'text-[#6B665E]'
                  }`}
                >
                  {prob_delta_pct > 0 ? `+${prob_delta_pct} pp` : `${prob_delta_pct} pp`}
                </td>
              </tr>
              <tr>
                <td className="py-2 pr-3 text-[#111111] dark:text-[#F3EEE3]">Opportunity Score</td>
                <td className="py-2 px-3 text-[#6B665E]">{base_score}</td>
                <td className="py-2 px-3 text-[#111111] dark:text-white font-bold">{scenario_score}</td>
                <td
                  className={`py-2 pl-3 text-right font-bold ${
                    score_delta > 0
                      ? 'text-[#254C3B] dark:text-[#4C9A77]'
                      : score_delta < 0
                        ? 'text-[#A63222] dark:text-[#E06C5B]'
                        : 'text-[#6B665E]'
                  }`}
                >
                  {score_delta > 0 ? `+${score_delta}` : `${score_delta}`}
                </td>
              </tr>
              <tr>
                <td className="py-2 pr-3 text-[#111111] dark:text-[#F3EEE3]">Competition Score</td>
                <td className="py-2 px-3 text-[#6B665E]">{baseCompScore}</td>
                <td className="py-2 px-3 text-[#111111] dark:text-white">{scenCompScore}</td>
                <td
                  className={`py-2 pl-3 text-right font-bold ${
                    compDelta > 0
                      ? 'text-[#A63222] dark:text-[#E06C5B]'
                      : compDelta < 0
                        ? 'text-[#254C3B] dark:text-[#4C9A77]'
                        : 'text-[#6B665E]'
                  }`}
                >
                  {compDelta > 0 ? `+${compDelta}` : `${compDelta}`}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. Model Driver Changes */}
      {model_driver_changes.length > 0 && (
        <div className="editorial-subcard p-3.5 rounded-lg space-y-2.5 text-xs">
          <div className="font-bold text-[#111111] dark:text-[#F3EEE3] flex items-center justify-between text-[11px] uppercase tracking-wider">
            <span className="flex items-center gap-1.5">
              <BrainCircuit className="w-3.5 h-3.5 text-[#D9541E]" />
              <span>Model Input Shifts</span>
            </span>
          </div>
          <div className="space-y-2">
            {model_driver_changes.map((driver, idx) => {
              const isPos = driver.direction === 'positive';
              const isNeg = driver.direction === 'negative';
              return (
                <div key={idx} className="bg-white dark:bg-[#1A1917] p-2.5 rounded-md border border-[#E6DED0] dark:border-[#2F2B25] flex items-center justify-between gap-3">
                  <div>
                    <div className="font-semibold text-[#111111] dark:text-[#F3EEE3]">{driver.display_name}</div>
                    <div className={`text-[11px] font-medium mt-0.5 ${isPos ? 'text-[#254C3B] dark:text-[#4C9A77]' : isNeg ? 'text-[#A63222] dark:text-[#E06C5B]' : 'text-[#6B665E]'}`}>
                      • {getSimpleDriverEffect(driver)}
                    </div>
                  </div>
                  <span className="text-[11px] text-[#6B665E] bg-[#F3EEE3] dark:bg-[#22201D] px-2 py-1 rounded border border-[#E6DED0] dark:border-[#2F2B25] shrink-0">
                    {driver.baseline_value} → <strong className="text-[#D9541E]">{driver.scenario_value}</strong>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. Financial Impact */}
      <div className="editorial-subcard p-3.5 rounded-lg space-y-2.5 text-xs">
        <div className="font-bold text-[#111111] dark:text-[#F3EEE3] flex items-center justify-between text-[11px] uppercase tracking-wider">
          <span className="flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-[#254C3B] dark:text-[#4C9A77]" />
            <span>Financial Projection Impact</span>
          </span>
        </div>

        {hasFinancialChanges && finComp ? (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left tabular-nums">
              <thead className="text-[10px] text-[#6B665E] dark:text-[#A69E92] uppercase border-b border-[#E6DED0] dark:border-[#2F2B25]">
                <tr>
                  <th className="py-1.5 pr-2">Metric</th>
                  <th className="py-1.5 px-2">Baseline</th>
                  <th className="py-1.5 px-2">Scenario</th>
                  <th className="py-1.5 pl-2 text-right">Change</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EAE3D5] dark:divide-[#2C2823] font-medium">
                <tr>
                  <td className="py-1.5 pr-2 text-[#111111] dark:text-[#F3EEE3]">Revenue</td>
                  <td className="py-1.5 px-2 text-[#6B665E]">₹{Math.round(finBase.monthly_revenue || 0).toLocaleString('en-IN')}</td>
                  <td className="py-1.5 px-2 text-[#111111] dark:text-white font-bold">₹{Math.round(finScen.monthly_revenue || 0).toLocaleString('en-IN')}</td>
                  <td className={`py-1.5 pl-2 text-right font-bold ${revDelta >= 0 ? 'text-[#254C3B] dark:text-[#4C9A77]' : 'text-[#A63222] dark:text-[#E06C5B]'}`}>
                    {revDelta >= 0 ? `+₹${Math.round(revDelta).toLocaleString('en-IN')}` : `-₹${Math.round(Math.abs(revDelta)).toLocaleString('en-IN')}`}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 pr-2 text-[#111111] dark:text-[#F3EEE3]">Operating Profit</td>
                  <td className="py-1.5 px-2 text-[#6B665E]">₹{Math.round(finBase.estimated_operating_profit || 0).toLocaleString('en-IN')}</td>
                  <td className="py-1.5 px-2 text-[#111111] dark:text-white font-bold">₹{Math.round(finScen.estimated_operating_profit || 0).toLocaleString('en-IN')}</td>
                  <td className={`py-1.5 pl-2 text-right font-bold ${profitDelta >= 0 ? 'text-[#254C3B] dark:text-[#4C9A77]' : 'text-[#A63222] dark:text-[#E06C5B]'}`}>
                    {profitDelta >= 0 ? `+₹${Math.round(profitDelta).toLocaleString('en-IN')}` : `-₹${Math.round(Math.abs(profitDelta)).toLocaleString('en-IN')}`}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 pr-2 text-[#111111] dark:text-[#F3EEE3]">Profit Margin</td>
                  <td className="py-1.5 px-2 text-[#6B665E]">{finBase.operating_profit_margin != null ? `${finBase.operating_profit_margin.toFixed(1)}%` : 'N/A'}</td>
                  <td className="py-1.5 px-2 text-[#111111] dark:text-white font-bold">{finScen.operating_profit_margin != null ? `${finScen.operating_profit_margin.toFixed(1)}%` : 'N/A'}</td>
                  <td className={`py-1.5 pl-2 text-right font-bold ${marginDelta >= 0 ? 'text-[#254C3B] dark:text-[#4C9A77]' : 'text-[#A63222] dark:text-[#E06C5B]'}`}>
                    {marginDelta >= 0 ? `+${marginDelta.toFixed(1)} pp` : `${marginDelta.toFixed(1)} pp`}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 pr-2 text-[#111111] dark:text-[#F3EEE3]">Break-even/day</td>
                  <td className="py-1.5 px-2 text-[#6B665E]">{finBase.break_even_customers_per_day != null ? `${finBase.break_even_customers_per_day.toFixed(1)}` : 'N/A'}</td>
                  <td className="py-1.5 px-2 text-[#D9541E] font-bold">{finScen.break_even_customers_per_day != null ? `${finScen.break_even_customers_per_day.toFixed(1)}` : 'N/A'}</td>
                  <td className={`py-1.5 pl-2 text-right font-bold ${bepDelta <= 0 ? 'text-[#254C3B] dark:text-[#4C9A77]' : 'text-[#D9541E]'}`}>
                    {bepDelta != null ? (bepDelta >= 0 ? `+${bepDelta.toFixed(1)}` : `${bepDelta.toFixed(1)}`) : 'N/A'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-[#6B665E] dark:text-[#A69E92] bg-white dark:bg-[#1A1917] p-2.5 rounded-md border border-[#E6DED0] dark:border-[#2F2B25]">
            <AlertCircle className="w-4 h-4 text-[#254C3B] dark:text-[#4C9A77] shrink-0" />
            <span>No financial assumption change triggered by this parameter delta.</span>
          </div>
        )}
      </div>

      {/* 5. Scenario Summary Bullets */}
      <div className="editorial-ai-panel rounded-lg p-3.5 space-y-2 text-xs">
        <div className="font-bold text-white uppercase tracking-[0.08em] flex items-center gap-1.5 text-[11px] pb-1.5 border-b border-white/10">
          <CheckCircle2 className="w-3.5 h-3.5 text-[#D9541E]" />
          <span>Scenario Takeaways</span>
        </div>
        <ul className="space-y-1.5 text-[#EFEAE0]">
          {whatThisMeansBullets.map((bullet, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#D9541E] shrink-0" />
              <span>{bullet}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
