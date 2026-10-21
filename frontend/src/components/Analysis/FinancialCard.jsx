import React, { useState, useMemo } from 'react';
import { DollarSign, Calculator, PieChart, SlidersHorizontal, RefreshCw, AlertTriangle, Info } from 'lucide-react';

/**
 * Canonical client-side financial recalculation engine.
 * Matches backend simulate_financials() formulas with 100% mathematical reconciliation.
 */
function calculateFinancialMetrics(assump) {
  const cpd = Math.max(0, Number(assump.customers_per_day) || 0);
  const days = Math.min(31, Math.max(1, Number(assump.working_days) || 30));
  const aov = Math.max(0, Number(assump.average_order_value) || 0);
  const rent = Math.max(0, Number(assump.rent) || 0);
  const staff = Math.max(0, Number(assump.staff_cost) || 0);
  const utils = Math.max(0, Number(assump.utilities) || 0);
  const mktg = Math.max(0, Number(assump.marketing) || 0);
  const other = Math.max(0, Number(assump.other_expenses) || 0);
  const foodPct = Math.min(100, Math.max(0, Number(assump.food_cost_percent) || 0));

  const monthlyCustomers = Math.round(cpd * days);
  const monthlyRevenue = monthlyCustomers * aov;
  const variableCostRatio = foodPct / 100;
  const variableCosts = monthlyRevenue * variableCostRatio;
  const itemizedFixed = rent + staff + utils + mktg + other;
  const fixedCosts = itemizedFixed > 0 ? itemizedFixed : (Number(assump.fixed_costs) || Number(assump.fixedCost) || 0);
  const totalExpenses = fixedCosts + variableCosts;
  const operatingProfit = monthlyRevenue - totalExpenses;
  const operatingMargin = monthlyRevenue > 0 ? (operatingProfit / monthlyRevenue) * 100 : 0.0;
  const contributionMarginRatio = 1.0 - variableCostRatio;

  let breakEvenRevenue = null;
  let breakEvenPerMonth = null;
  let breakEvenPerDay = null;
  let breakEvenTarget = null;
  let breakEvenAchievable = true;
  let breakEvenExplanation = '';

  if (contributionMarginRatio <= 0) {
    breakEvenAchievable = false;
    breakEvenExplanation = 'Break-even cannot be achieved under current assumptions because variable costs equal or exceed 100% of revenue, leaving zero contribution margin to cover fixed expenses.';
  } else if (fixedCosts === 0) {
    breakEvenRevenue = 0;
    breakEvenPerMonth = 0;
    breakEvenPerDay = 0;
    breakEvenTarget = 0;
    breakEvenAchievable = true;
    breakEvenExplanation = 'Fixed operating costs are ₹0; break-even is achieved with 0 customers.';
  } else if (aov <= 0) {
    breakEvenAchievable = false;
    breakEvenExplanation = 'Break-even cannot be achieved because average spend per customer is ₹0 while fixed operating costs exist.';
  } else {
    breakEvenRevenue = fixedCosts / contributionMarginRatio;
    breakEvenPerMonth = fixedCosts / (aov * contributionMarginRatio);
    breakEvenPerDay = breakEvenPerMonth / days;
    breakEvenTarget = Math.ceil(breakEvenPerDay);
    breakEvenAchievable = true;
    breakEvenExplanation = `Estimated ${breakEvenTarget} customers required per day (${breakEvenPerDay.toFixed(1)} exact, ~${Math.round(breakEvenPerMonth)}/month) to cover all fixed and variable operating costs.`;
  }

  return {
    cpd,
    days,
    aov,
    rent,
    staff,
    utils,
    mktg,
    other,
    foodPct,
    monthlyCustomers,
    monthlyRevenue,
    variableCosts,
    fixedCosts,
    fixedCost: fixedCosts,
    totalExpenses,
    operatingProfit,
    operatingMargin,
    contributionMarginRatio,
    breakEvenRevenue,
    breakEvenPerMonth,
    breakEvenPerDay,
    breakEvenTarget,
    breakEvenAchievable,
    breakEvenExplanation,
  };
}

export default function FinancialCard({ financialData }) {
  // Extract initial baseline assumptions from backend payload
  const rawAssumptions = financialData?.assumptions || {};
  const baseline = useMemo(() => ({
    customers_per_day: financialData?.customers_per_day ?? rawAssumptions.customers_per_day ?? 100,
    working_days: rawAssumptions.working_days ?? 30,
    average_order_value: financialData?.average_order_value ?? rawAssumptions.average_order_value ?? 400,
    rent: financialData?.rent ?? rawAssumptions.rent ?? 60000,
    staff_cost: financialData?.staff_cost ?? rawAssumptions.staff_cost ?? 50000,
    utilities: financialData?.utilities ?? rawAssumptions.utilities ?? 15000,
    marketing: financialData?.marketing ?? rawAssumptions.marketing ?? 10000,
    other_expenses: financialData?.other_expenses ?? rawAssumptions.other_expenses ?? 5000,
    food_cost_percent: rawAssumptions.food_cost_percent ?? rawAssumptions.variable_cost_percent ?? 30,
    fixed_costs: financialData?.fixed_costs ?? financialData?.fixedCost,
  }), [financialData, rawAssumptions.customers_per_day, rawAssumptions.working_days, rawAssumptions.average_order_value, rawAssumptions.rent, rawAssumptions.staff_cost, rawAssumptions.utilities, rawAssumptions.marketing, rawAssumptions.other_expenses, rawAssumptions.food_cost_percent, rawAssumptions.variable_cost_percent]);

  const [assumptions, setAssumptions] = useState(baseline);
  const [showEditor, setShowEditor] = useState(false);

  // Check if current assumptions differ from initial baseline
  const isCustomized = useMemo(() => {
    return Object.keys(baseline).some(
      (k) => Number(assumptions[k]) !== Number(baseline[k])
    );
  }, [assumptions, baseline]);

  // Dynamically recalculated metrics
  const metrics = useMemo(() => calculateFinancialMetrics(assumptions), [assumptions]);

  if (!financialData) return null;

  const handleInputChange = (field, value) => {
    setAssumptions((prev) => ({
      ...prev,
      [field]: value === '' ? '' : Number(value),
    }));
  };

  const handleReset = () => {
    setAssumptions(baseline);
  };

  const formatINR = (val) => {
    if (val === null || val === undefined || isNaN(val)) return 'N/A';
    return `₹${Math.round(val).toLocaleString('en-IN')}`;
  };

  const isProfitable = metrics.operatingProfit >= 0;

  return (
    <div className="glass-panel p-5 rounded-2xl border border-emerald-200 dark:border-emerald-500/30 space-y-4 my-4 text-slate-900 dark:text-slate-100">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400">
            <DollarSign className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm sm:text-base">
                Financial Analysis
              </h3>
              {isCustomized ? (
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400">
                  Custom Assumptions
                </span>
              ) : (
                <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
                  Default Assumptions
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              Directional assumption-based projection
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isCustomized && (
            <button
              onClick={handleReset}
              title="Reset to default assumptions"
              className="text-xs flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors shadow-xs"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Reset</span>
            </button>
          )}
          <button
            onClick={() => setShowEditor(!showEditor)}
            className={`text-xs font-semibold flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-colors shadow-xs ${
              showEditor
                ? 'bg-emerald-600 text-white border-emerald-600'
                : 'bg-emerald-50 dark:bg-emerald-500/10 border-emerald-200 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-500/20'
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>{showEditor ? 'Hide Assumptions' : 'Edit Assumptions'}</span>
          </button>
        </div>
      </div>

      {/* Interactive Assumptions Editor Drawer */}
      {showEditor && (
        <div className="bg-slate-50 dark:bg-slate-950/80 p-4 rounded-xl border border-emerald-300 dark:border-emerald-500/40 space-y-3 shadow-inner">
          <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800 text-xs">
            <span className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
              <SlidersHorizontal className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              Adjust Financial Model Assumptions
            </span>
            <span className="text-[11px] text-slate-500 dark:text-slate-400">
              Live instant recalculation
            </span>
          </div>

          <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
            Modify any operating parameter below. Projections update immediately without restarting your analysis. All figures are planning estimates.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            {/* Daily Customers */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 flex justify-between">
                <span>Daily Customers</span>
                <span className="text-slate-400">min 0</span>
              </label>
              <input
                type="number"
                min="0"
                step="5"
                value={assumptions.customers_per_day}
                onChange={(e) => handleInputChange('customers_per_day', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-medium focus:ring-1 focus:ring-emerald-500 outline-none"
              />
            </div>

            {/* Operating Days / Month */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 flex justify-between">
                <span>Operating Days/Mo</span>
                <span className="text-slate-400">1–31</span>
              </label>
              <input
                type="number"
                min="1"
                max="31"
                step="1"
                value={assumptions.working_days}
                onChange={(e) => handleInputChange('working_days', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-medium focus:ring-1 focus:ring-emerald-500 outline-none"
              />
            </div>

            {/* Average Spend / Customer */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 flex justify-between">
                <span>Avg Spend/Cust (₹)</span>
                <span className="text-slate-400">Cost for 2 ÷ 2</span>
              </label>
              <input
                type="number"
                min="0"
                step="25"
                value={assumptions.average_order_value}
                onChange={(e) => handleInputChange('average_order_value', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-medium focus:ring-1 focus:ring-emerald-500 outline-none"
              />
            </div>

            {/* Monthly Rent */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 flex justify-between">
                <span>Monthly Rent (₹)</span>
                <span className="text-slate-400">Fixed</span>
              </label>
              <input
                type="number"
                min="0"
                step="5000"
                value={assumptions.rent}
                onChange={(e) => handleInputChange('rent', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-medium focus:ring-1 focus:ring-emerald-500 outline-none"
              />
            </div>

            {/* Staff Costs */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 flex justify-between">
                <span>Staff Salaries (₹)</span>
                <span className="text-slate-400">Fixed</span>
              </label>
              <input
                type="number"
                min="0"
                step="5000"
                value={assumptions.staff_cost}
                onChange={(e) => handleInputChange('staff_cost', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-medium focus:ring-1 focus:ring-emerald-500 outline-none"
              />
            </div>

            {/* Utilities */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 flex justify-between">
                <span>Utilities (₹)</span>
                <span className="text-slate-400">Power/Water</span>
              </label>
              <input
                type="number"
                min="0"
                step="1000"
                value={assumptions.utilities}
                onChange={(e) => handleInputChange('utilities', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-medium focus:ring-1 focus:ring-emerald-500 outline-none"
              />
            </div>

            {/* Marketing */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 flex justify-between">
                <span>Marketing (₹)</span>
                <span className="text-slate-400">Ads/Promo</span>
              </label>
              <input
                type="number"
                min="0"
                step="1000"
                value={assumptions.marketing}
                onChange={(e) => handleInputChange('marketing', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-medium focus:ring-1 focus:ring-emerald-500 outline-none"
              />
            </div>

            {/* Other Fixed Expenses */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 flex justify-between">
                <span>Other Fixed Costs (₹)</span>
                <span className="text-slate-400">Maintenance/Admin</span>
              </label>
              <input
                type="number"
                min="0"
                step="1000"
                value={assumptions.other_expenses}
                onChange={(e) => handleInputChange('other_expenses', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-medium focus:ring-1 focus:ring-emerald-500 outline-none"
              />
            </div>

            {/* Variable / Food Cost % */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 flex justify-between">
                <span>Variable Cost %</span>
                <span className="text-slate-400">0–100%</span>
              </label>
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                value={assumptions.food_cost_percent}
                onChange={(e) => handleInputChange('food_cost_percent', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-medium focus:ring-1 focus:ring-emerald-500 outline-none"
              />
            </div>
          </div>
        </div>
      )}

      {/* Top Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs text-center">
        {/* Monthly Revenue */}
        <div className="bg-slate-50 dark:bg-slate-950/70 p-3 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col justify-between shadow-xs">
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mb-1">Monthly Projected Revenue</div>
          <div className="font-bold text-emerald-600 dark:text-emerald-400 text-sm sm:text-base">
            {formatINR(metrics.monthlyRevenue)}
          </div>
          <div className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">
            {metrics.monthlyCustomers.toLocaleString('en-IN')} cust/mo ({metrics.cpd}/day × {metrics.days}d)
          </div>
        </div>

        {/* Monthly Expenses */}
        <div className="bg-slate-50 dark:bg-slate-950/70 p-3 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col justify-between shadow-xs">
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mb-1">Total Operating Expenses</div>
          <div className="font-bold text-slate-800 dark:text-slate-200 text-sm sm:text-base">
            {formatINR(metrics.totalExpenses)}
          </div>
          <div className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">
            Fixed ({formatINR(metrics.fixedCosts ?? metrics.fixedCost)}) + Var ({formatINR(metrics.variableCosts)})
          </div>
        </div>

        {/* Estimated Operating Profit */}
        <div className="bg-slate-50 dark:bg-slate-950/70 p-3 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col justify-between shadow-xs">
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mb-1">Est. Operating Profit</div>
          <div className={`font-bold text-sm sm:text-base ${isProfitable ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
            {formatINR(metrics.operatingProfit)}
          </div>
          <div className={`text-[10px] font-semibold mt-1 ${isProfitable ? 'text-emerald-600 dark:text-emerald-400/90' : 'text-rose-600 dark:text-rose-400/90'}`}>
            {metrics.operatingMargin.toFixed(1)}% margin
          </div>
        </div>

        {/* Monthly Customers */}
        <div className="bg-slate-50 dark:bg-slate-950/70 p-3 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col justify-between shadow-xs">
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mb-1">Monthly Customers</div>
          <div className="font-bold text-slate-800 dark:text-slate-200 text-sm">
            {metrics.monthlyCustomers.toLocaleString('en-IN')}
          </div>
          <div className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">~{metrics.cpd} per operating day</div>
        </div>

        {/* Avg Spend / Customer */}
        <div className="bg-slate-50 dark:bg-slate-950/70 p-3 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col justify-between shadow-xs">
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mb-1">Avg Spend / Customer</div>
          <div className="font-bold text-slate-800 dark:text-slate-200 text-sm">
            {formatINR(metrics.aov)}
          </div>
          <div className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">Estimated order value</div>
        </div>

        {/* Break-even Customers / Day */}
        <div className="bg-amber-50 dark:bg-slate-950/70 p-3 rounded-xl border border-amber-200 dark:border-amber-500/30 flex flex-col justify-between shadow-xs">
          <div className="text-[11px] text-amber-700 dark:text-amber-300 font-semibold mb-1">Break-even / Day</div>
          <div className="font-bold text-amber-600 dark:text-amber-400 text-sm sm:text-base">
            {metrics.breakEvenAchievable && metrics.breakEvenTarget !== null
              ? `${metrics.breakEvenTarget} / day`
              : 'Unachievable'}
          </div>
          <div className="text-[10px] text-amber-600/80 dark:text-amber-400/80 mt-1">
            {metrics.breakEvenAchievable && metrics.breakEvenPerDay !== null
              ? `(${metrics.breakEvenPerDay.toFixed(1)} exact)`
              : 'Variable cost ≥ 100%'}
          </div>
        </div>
      </div>

      {/* Break-even Explanation Banner */}
      <div className={`rounded-xl p-3 flex items-start gap-2.5 text-xs border ${
        metrics.breakEvenAchievable
          ? 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-500/20 text-amber-900 dark:text-amber-200'
          : 'bg-rose-50 dark:bg-rose-950/20 border-rose-200 dark:border-rose-500/20 text-rose-900 dark:text-rose-200'
      }`}>
        {metrics.breakEvenAchievable ? (
          <Calculator className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        ) : (
          <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
        )}
        <div className="space-y-0.5">
          <div className="font-semibold">
            {metrics.breakEvenAchievable ? 'Break-even Analysis' : 'Break-even Notice'}
          </div>
          <p className="text-slate-700 dark:text-slate-300 leading-relaxed text-[11px]">
            {metrics.breakEvenExplanation} This is an assumption-based projection, not a guaranteed real-world requirement.
          </p>
        </div>
      </div>

      {/* Expense & Profit Reconciled Breakdown */}
      <div className="bg-slate-50 dark:bg-slate-950/70 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs space-y-2">
        <div className="font-semibold text-slate-800 dark:text-slate-300 flex items-center justify-between border-b border-slate-200 dark:border-slate-900 pb-1.5">
          <span className="flex items-center gap-1.5">
            <PieChart className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            Itemized Operating Statement (Monthly)
          </span>
          <span className="text-[10px] text-slate-500 dark:text-slate-400">Reconciled Model</span>
        </div>

        <div className="space-y-1.5 text-slate-700 dark:text-slate-300 text-[11px]">
          {/* Revenue */}
          <div className="flex justify-between items-center py-0.5 border-b border-slate-200/60 dark:border-slate-900/50">
            <span className="text-slate-600 dark:text-slate-400">Monthly Projected Revenue:</span>
            <span className="font-semibold text-emerald-600 dark:text-emerald-400">{formatINR(metrics.monthlyRevenue)}</span>
          </div>

          {/* Variable Cost */}
          <div className="flex justify-between items-center py-0.5 border-b border-slate-200/60 dark:border-slate-900/50">
            <span className="text-slate-600 dark:text-slate-400">
              Variable Costs ({metrics.foodPct}% of revenue):
            </span>
            <span className="font-medium text-rose-600 dark:text-rose-400">-{formatINR(metrics.variableCosts)}</span>
          </div>

          {/* Total Fixed Costs */}
          <div className="flex justify-between items-center py-0.5 border-b border-slate-200/60 dark:border-slate-900/50">
            <span className="text-slate-700 dark:text-slate-300 font-semibold">
              Total Fixed Operating Costs:
            </span>
            <span className="font-semibold text-rose-600 dark:text-rose-400">-{formatINR(metrics.fixedCosts ?? metrics.fixedCost)}</span>
          </div>

          {/* Itemized Fixed Sub-items */}
          <div className="pl-3.5 py-1 space-y-1 bg-slate-100/70 dark:bg-slate-900/40 rounded-lg text-[10px] text-slate-600 dark:text-slate-400">
            <div className="flex justify-between items-center pr-2">
              <span>• Rent:</span>
              <span className="font-medium">{formatINR(metrics.rent)}</span>
            </div>
            <div className="flex justify-between items-center pr-2">
              <span>• Staff Salaries:</span>
              <span className="font-medium">{formatINR(metrics.staff)}</span>
            </div>
            <div className="flex justify-between items-center pr-2">
              <span>• Utilities (Power, Water, Gas):</span>
              <span className="font-medium">{formatINR(metrics.utils)}</span>
            </div>
            <div className="flex justify-between items-center pr-2">
              <span>• Marketing & Promotion:</span>
              <span className="font-medium">{formatINR(metrics.mktg)}</span>
            </div>
            <div className="flex justify-between items-center pr-2">
              <span>• Other Fixed Operating Expenses:</span>
              <span className="font-medium">{formatINR(metrics.other)}</span>
            </div>
            <div className="flex justify-between items-center pr-2 pt-0.5 border-t border-slate-200 dark:border-slate-800 font-semibold text-slate-700 dark:text-slate-300">
              <span>Subtotal Fixed Costs (Rent + Staff + Utils + Mktg + Other):</span>
              <span>{formatINR(metrics.fixedCosts ?? metrics.fixedCost)}</span>
            </div>
          </div>

          {/* Total Expenses */}
          <div className="flex justify-between items-center py-0.5 border-b border-slate-200/60 dark:border-slate-900/50 font-medium">
            <span className="text-slate-700 dark:text-slate-300">Total Operating Expenses (Fixed + Variable):</span>
            <span className="font-semibold text-rose-600 dark:text-rose-400">-{formatINR(metrics.totalExpenses)}</span>
          </div>

          {/* Estimated Operating Profit */}
          <div className="flex justify-between items-center pt-1.5 font-bold text-xs sm:text-sm">
            <span className="text-slate-900 dark:text-slate-100">Estimated Operating Profit:</span>
            <span className={isProfitable ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}>
              {formatINR(metrics.operatingProfit)}
            </span>
          </div>
        </div>
      </div>

      {/* Financial Transparency & Model Scope Notes */}
      <div className="bg-slate-100/90 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-[11px] text-slate-600 dark:text-slate-400 space-y-1.5">
        <div className="flex items-center gap-1.5 font-semibold text-slate-800 dark:text-slate-300">
          <Info className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 shrink-0" />
          <span>Financial Scope & Transparency Notes</span>
        </div>
        <p className="leading-relaxed">
          • <strong>Operating Profit vs. Net Profit:</strong> This projection models <em>Operating Profit</em> (Revenue − Operating Expenses). It does <strong>not</strong> include income tax, GST, depreciation on kitchen equipment/furniture, interest on bank loans, or owner drawings.
        </p>
        <p className="leading-relaxed">
          • <strong>Delivery Commissions:</strong> Platform aggregator commissions (e.g., Zomato / Swiggy 15%–25% on delivery orders) and payment gateway charges are excluded from base assumptions. Use the "Edit Assumptions" panel above to factor them into your Variable Cost % if relevant.
        </p>
        <p className="leading-relaxed">
          • <strong>Average Spend per Customer:</strong> Estimated as Cost for Two ÷ 2 ({formatINR(metrics.aov)}). Actual individual spending varies by party size, order mix, and beverages.
        </p>
      </div>
    </div>
  );
}
