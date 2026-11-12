import React, { useState, useMemo } from 'react';
import { DollarSign, Calculator, PieChart, SlidersHorizontal, RefreshCw, AlertTriangle, Info, ArrowUpRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import AIInsightsPanel from './AIInsightsPanel';

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
  let breakEvenDays = null;
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
    breakEvenDays = 0;
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
    breakEvenDays = cpd > 0 ? breakEvenPerMonth / cpd : null;
    breakEvenAchievable = true;
    const daysText = breakEvenDays !== null ? ` (~${breakEvenDays.toFixed(1)} operating days at ${cpd}/day)` : '';
    breakEvenExplanation = `Estimated ${breakEvenTarget} customers required per day (${breakEvenPerDay.toFixed(1)} exact, ~${Math.round(breakEvenPerMonth)}/month${daysText}) to cover all fixed and variable operating costs.`;
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
    breakEvenDays,
    breakEvenAchievable,
    breakEvenExplanation,
  };
}

export default function FinancialCard({ financialData, onCreateScenario, insights }) {
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
  }), [
    financialData,
    rawAssumptions.customers_per_day,
    rawAssumptions.working_days,
    rawAssumptions.average_order_value,
    rawAssumptions.rent,
    rawAssumptions.staff_cost,
    rawAssumptions.utilities,
    rawAssumptions.marketing,
    rawAssumptions.other_expenses,
    rawAssumptions.food_cost_percent,
    rawAssumptions.variable_cost_percent,
  ]);

  const [assumptions, setAssumptions] = useState(baseline);
  const [showEditor, setShowEditor] = useState(false);

  const isCustomized = useMemo(() => {
    return Object.keys(baseline).some(
      (k) => Number(assumptions[k]) !== Number(baseline[k])
    );
  }, [assumptions, baseline]);

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

  const chartData = [
    { name: 'Revenue', amount: Math.round(metrics.monthlyRevenue), fill: '#254C3B' },
    { name: 'Expenses', amount: Math.round(metrics.totalExpenses), fill: '#6B665E' },
    { name: 'Op. Profit', amount: Math.round(metrics.operatingProfit), fill: isProfitable ? '#D9541E' : '#A63222' },
  ];

  return (
    <section className="editorial-panel rounded-xl p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#E6DED0] dark:border-[#2F2B25]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#EAE3D5] dark:bg-[#22201D] border border-[#D4C9B6] dark:border-[#3A352E] text-[#111111] dark:text-[#F3EEE3]">
            <DollarSign className="w-4 h-4 text-[#254C3B] dark:text-[#4C9A77]" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#6B665E] dark:text-[#A69E92]">
                05 · Unit Economics Simulator
              </span>
              {isCustomized ? (
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[#D9541E]/10 border border-[#D9541E]/30 text-[#D9541E]">
                  Custom Assumptions
                </span>
              ) : (
                <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-[#E6DED0] dark:bg-[#22201D] text-[#6B665E] dark:text-[#A69E92]">
                  Default Assumptions
                </span>
              )}
            </div>
            <h3 className="font-heading font-bold text-[#111111] dark:text-[#F3EEE3] text-sm sm:text-base mt-0.5">
              Financial Analysis <span className="text-xs font-normal text-[#6B665E] dark:text-[#A69E92]">(Assumption-Based Estimate)</span>
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {isCustomized && (
            <button
              type="button"
              onClick={handleReset}
              title="Reset to default assumptions"
              className="text-xs flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-[#C9BFAE] dark:border-[#3A352E] bg-white dark:bg-[#1A1917] text-[#111111] dark:text-[#E6DED0] hover:bg-[#EAE3D5] dark:hover:bg-[#24221E] transition-colors cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          )}
          <button
            type="button"
            onClick={() => setShowEditor(!showEditor)}
            className={`text-xs font-semibold flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-colors cursor-pointer ${showEditor
                ? 'bg-[#D9541E] text-white border-[#D9541E]'
                : 'bg-[#111111] dark:bg-[#26231F] text-white border-[#111111] dark:border-[#3A352E] hover:bg-[#D9541E] hover:border-[#D9541E]'
              }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>{showEditor ? 'Hide Assumptions' : 'Edit Assumptions'}</span>
          </button>
          {onCreateScenario && (
            <button
              type="button"
              onClick={onCreateScenario}
              className="text-xs font-semibold flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-[#D9541E]/40 text-[#D9541E] hover:bg-[#D9541E]/10 transition-colors cursor-pointer"
            >
              <ArrowUpRight className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Scenario</span>
            </button>
          )}
        </div>
      </div>

      {/* Interactive Assumptions Editor Drawer */}
      {showEditor && (
        <div className="bg-[#F8F5EE] dark:bg-[#161513] p-4 rounded-lg border border-[#D9541E]/40 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#E6DED0] dark:border-[#2F2B25] text-xs">
            <span className="font-bold text-[#111111] dark:text-[#F3EEE3] flex items-center gap-1.5">
              <SlidersHorizontal className="w-3.5 h-3.5 text-[#D9541E]" />
              Adjust Financial Model Assumptions
            </span>
            <span className="text-[11px] text-[#6B665E] dark:text-[#A69E92]">
              Live instant recalculation
            </span>
          </div>

          <p className="text-[11px] text-[#6B665E] dark:text-[#A69E92] leading-relaxed">
            Modify operating drivers below to stress-test profitability. Figures update deterministically and represent planning estimates, not guaranteed results.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-[#111111] dark:text-[#E6DED0] flex justify-between">
                <span>Daily Customers</span>
                <span className="text-[#6B665E]">min 0</span>
              </label>
              <input
                type="number"
                min="0"
                step="5"
                value={assumptions.customers_per_day}
                onChange={(e) => handleInputChange('customers_per_day', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-[#C9BFAE] dark:border-[#3A352E] bg-white dark:bg-[#1A1917] text-[#111111] dark:text-[#F3EEE3] font-medium focus:border-[#D9541E] outline-none tabular-nums"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-[#111111] dark:text-[#E6DED0] flex justify-between">
                <span>Operating Days / Mo</span>
                <span className="text-[#6B665E]">1–31</span>
              </label>
              <input
                type="number"
                min="1"
                max="31"
                step="1"
                value={assumptions.working_days}
                onChange={(e) => handleInputChange('working_days', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-[#C9BFAE] dark:border-[#3A352E] bg-white dark:bg-[#1A1917] text-[#111111] dark:text-[#F3EEE3] font-medium focus:border-[#D9541E] outline-none tabular-nums"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-[#111111] dark:text-[#E6DED0] flex justify-between">
                <span>Avg Spend / Cust (₹)</span>
                <span className="text-[#6B665E]">Cost for 2 ÷ 2</span>
              </label>
              <input
                type="number"
                min="0"
                step="25"
                value={assumptions.average_order_value}
                onChange={(e) => handleInputChange('average_order_value', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-[#C9BFAE] dark:border-[#3A352E] bg-white dark:bg-[#1A1917] text-[#111111] dark:text-[#F3EEE3] font-medium focus:border-[#D9541E] outline-none tabular-nums"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-[#111111] dark:text-[#E6DED0] flex justify-between">
                <span>Monthly Rent (₹)</span>
                <span className="text-[#6B665E]">Fixed</span>
              </label>
              <input
                type="number"
                min="0"
                step="5000"
                value={assumptions.rent}
                onChange={(e) => handleInputChange('rent', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-[#C9BFAE] dark:border-[#3A352E] bg-white dark:bg-[#1A1917] text-[#111111] dark:text-[#F3EEE3] font-medium focus:border-[#D9541E] outline-none tabular-nums"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-[#111111] dark:text-[#E6DED0] flex justify-between">
                <span>Staff Salaries (₹)</span>
                <span className="text-[#6B665E]">Fixed</span>
              </label>
              <input
                type="number"
                min="0"
                step="5000"
                value={assumptions.staff_cost}
                onChange={(e) => handleInputChange('staff_cost', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-[#C9BFAE] dark:border-[#3A352E] bg-white dark:bg-[#1A1917] text-[#111111] dark:text-[#F3EEE3] font-medium focus:border-[#D9541E] outline-none tabular-nums"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-[#111111] dark:text-[#E6DED0] flex justify-between">
                <span>Utilities (₹)</span>
                <span className="text-[#6B665E]">Power/Water</span>
              </label>
              <input
                type="number"
                min="0"
                step="1000"
                value={assumptions.utilities}
                onChange={(e) => handleInputChange('utilities', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-[#C9BFAE] dark:border-[#3A352E] bg-white dark:bg-[#1A1917] text-[#111111] dark:text-[#F3EEE3] font-medium focus:border-[#D9541E] outline-none tabular-nums"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-[#111111] dark:text-[#E6DED0] flex justify-between">
                <span>Marketing (₹)</span>
                <span className="text-[#6B665E]">Ads/Promo</span>
              </label>
              <input
                type="number"
                min="0"
                step="1000"
                value={assumptions.marketing}
                onChange={(e) => handleInputChange('marketing', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-[#C9BFAE] dark:border-[#3A352E] bg-white dark:bg-[#1A1917] text-[#111111] dark:text-[#F3EEE3] font-medium focus:border-[#D9541E] outline-none tabular-nums"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-[#111111] dark:text-[#E6DED0] flex justify-between">
                <span>Other Fixed Costs (₹)</span>
                <span className="text-[#6B665E]">Admin/Maint.</span>
              </label>
              <input
                type="number"
                min="0"
                step="1000"
                value={assumptions.other_expenses}
                onChange={(e) => handleInputChange('other_expenses', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-[#C9BFAE] dark:border-[#3A352E] bg-white dark:bg-[#1A1917] text-[#111111] dark:text-[#F3EEE3] font-medium focus:border-[#D9541E] outline-none tabular-nums"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-[#111111] dark:text-[#E6DED0] flex justify-between">
                <span>Variable Cost %</span>
                <span className="text-[#6B665E]">0–100%</span>
              </label>
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                value={assumptions.food_cost_percent}
                onChange={(e) => handleInputChange('food_cost_percent', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-[#C9BFAE] dark:border-[#3A352E] bg-white dark:bg-[#1A1917] text-[#111111] dark:text-[#F3EEE3] font-medium focus:border-[#D9541E] outline-none tabular-nums"
              />
            </div>
          </div>
        </div>
      )}

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
        <div className="editorial-subcard p-3.5 rounded-lg">
          <div className="text-[11px] text-[#6B665E] dark:text-[#A69E92] font-medium mb-1">
            Monthly Projected Revenue
          </div>
          <div className="font-bold text-[#254C3B] dark:text-[#4C9A77] text-base sm:text-lg tabular-nums">
            {formatINR(metrics.monthlyRevenue)}
          </div>
          <div className="text-[10px] text-[#6B665E] dark:text-[#A69E92] mt-1 tabular-nums">
            {metrics.monthlyCustomers.toLocaleString('en-IN')} cust/mo ({metrics.cpd}/day × {metrics.days}d)
          </div>
        </div>

        <div className="editorial-subcard p-3.5 rounded-lg">
          <div className="text-[11px] text-[#6B665E] dark:text-[#A69E92] font-medium mb-1">
            Total Operating Expenses
          </div>
          <div className="font-bold text-[#111111] dark:text-white text-base sm:text-lg tabular-nums">
            {formatINR(metrics.totalExpenses)}
          </div>
          <div className="text-[10px] text-[#6B665E] dark:text-[#A69E92] mt-1 tabular-nums">
            Fixed ({formatINR(metrics.fixedCosts ?? metrics.fixedCost)}) + Var ({formatINR(metrics.variableCosts)})
          </div>
        </div>

        <div className="editorial-subcard p-3.5 rounded-lg">
          <div className="text-[11px] text-[#6B665E] dark:text-[#A69E92] font-medium mb-1">
            Est. Operating Profit
          </div>
          <div
            className={`font-bold text-base sm:text-lg tabular-nums ${isProfitable ? 'text-[#254C3B] dark:text-[#4C9A77]' : 'text-[#A63222] dark:text-[#E06C5B]'
              }`}
          >
            {formatINR(metrics.operatingProfit)}
          </div>
          <div
            className={`text-[11px] font-semibold mt-1 tabular-nums ${isProfitable ? 'text-[#254C3B] dark:text-[#4C9A77]' : 'text-[#A63222] dark:text-[#E06C5B]'
              }`}
          >
            {metrics.operatingMargin.toFixed(1)}% projected margin
          </div>
        </div>

        <div className="editorial-subcard p-3.5 rounded-lg">
          <div className="text-[11px] text-[#6B665E] dark:text-[#A69E92] font-medium mb-1">
            Monthly Customers
          </div>
          <div className="font-bold text-[#111111] dark:text-white text-base tabular-nums">
            {metrics.monthlyCustomers.toLocaleString('en-IN')}
          </div>
          <div className="text-[10px] text-[#6B665E] dark:text-[#A69E92] mt-1">
            Assumed ~{metrics.cpd} per operating day
          </div>
        </div>

        <div className="editorial-subcard p-3.5 rounded-lg">
          <div className="text-[11px] text-[#6B665E] dark:text-[#A69E92] font-medium mb-1">
            Avg Spend / Customer
          </div>
          <div className="font-bold text-[#111111] dark:text-white text-base tabular-nums">
            {formatINR(metrics.aov)}
          </div>
          <div className="text-[10px] text-[#6B665E] dark:text-[#A69E92] mt-1">
            Derived from Cost for Two ÷ 2
          </div>
        </div>

        <div className="editorial-subcard p-3.5 rounded-lg border-l-2 border-l-[#D9541E]">
          <div className="text-[11px] text-[#D9541E] font-semibold mb-1">
            Break-Even Threshold
          </div>
          <div className="font-bold text-[#111111] dark:text-white text-base tabular-nums">
            {metrics.breakEvenAchievable && metrics.breakEvenTarget !== null
              ? `${metrics.breakEvenTarget} cust/day`
              : 'Unachievable'}
          </div>
          <div className="text-[10px] text-[#6B665E] dark:text-[#A69E92] mt-1 tabular-nums">
            {metrics.breakEvenAchievable && metrics.breakEvenDays !== null
              ? `~${metrics.breakEvenDays.toFixed(1)} operating days/mo`
              : metrics.breakEvenAchievable && metrics.breakEvenPerDay !== null
                ? `(${metrics.breakEvenPerDay.toFixed(1)} exact/day)`
                : 'Variable cost ≥ 100%'}
          </div>
        </div>
      </div>

      {/* Break-even Explanation Banner */}
      <div
        className={`rounded-lg p-3 flex items-start gap-2.5 text-xs border ${metrics.breakEvenAchievable
            ? 'bg-[#F8F5EE] dark:bg-[#1C1A17] border-[#DDD4C3] dark:border-[#2F2B25] text-[#111111] dark:text-[#E6DED0]'
            : 'bg-[#A63222]/10 border-[#A63222]/30 text-[#A63222] dark:text-[#E06C5B]'
          }`}
      >
        {metrics.breakEvenAchievable ? (
          <Calculator className="w-4 h-4 text-[#D9541E] shrink-0 mt-0.5" />
        ) : (
          <AlertTriangle className="w-4 h-4 text-[#A63222] dark:text-[#E06C5B] shrink-0 mt-0.5" />
        )}
        <div className="space-y-0.5">
          <div className="font-semibold">
            {metrics.breakEvenAchievable ? 'Break-Even Analysis' : 'Break-Even Notice'}
          </div>
          <p className="text-[#6B665E] dark:text-[#A69E92] leading-relaxed text-[11px]">
            {metrics.breakEvenExplanation} This is an assumption-based projection, not a guaranteed real-world outcome.
          </p>
        </div>
      </div>

      {/* Side-by-Side Visual Bar Chart & Reconciled Operating Statement */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Clean Monthly Economics Chart */}
        <div className="lg:col-span-5 editorial-subcard p-3.5 rounded-lg flex flex-col justify-between">
          <div className="text-[11px] font-semibold text-[#111111] dark:text-[#F3EEE3] mb-2">
            Monthly Cash-Flow Snapshot (₹)
          </div>
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 4 }}>
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#6B665E', fontSize: 11 }}
                  axisLine={{ stroke: '#DDD4C3' }}
                  tickLine={false}
                />
                <YAxis
                  tickFormatter={(v) => (Math.abs(v) >= 100000 ? `${(v / 100000).toFixed(1)}L` : `${Math.round(v / 1000)}k`)}
                  tick={{ fill: '#6B665E', fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  width={42}
                />
                <Tooltip
                  formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Projected']}
                  contentStyle={{
                    backgroundColor: '#111111',
                    border: '1px solid #2F2B25',
                    borderRadius: '8px',
                    color: '#FFFFFF',
                    fontSize: '12px',
                  }}
                  itemStyle={{ color: '#F3EEE3' }}
                />
                <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="text-[10px] text-[#6B665E] dark:text-[#A69E92] pt-1 border-t border-[#E6DED0] dark:border-[#2F2B25]">
            Assumption-based revenue vs expense model
          </div>
        </div>

        {/* Itemized Operating Statement Table */}
        <div className="lg:col-span-7 editorial-subcard p-3.5 rounded-lg text-xs">
          <div className="font-semibold text-[#111111] dark:text-[#F3EEE3] flex items-center justify-between border-b border-[#E6DED0] dark:border-[#2F2B25] pb-2 mb-2">
            <span className="flex items-center gap-1.5">
              <PieChart className="w-3.5 h-3.5 text-[#D9541E]" />
              <span>Itemized Operating Statement</span>
            </span>
            <span className="text-[10px] text-[#6B665E] dark:text-[#A69E92]">Monthly Basis</span>
          </div>

          <table className="w-full text-[11px] tabular-nums">
            <tbody className="divide-y divide-[#EAE3D5] dark:divide-[#2C2823]">
              <tr>
                <td className="py-1.5 text-[#6B665E] dark:text-[#A69E92]">Monthly Projected Revenue</td>
                <td className="py-1.5 text-right font-semibold text-[#254C3B] dark:text-[#4C9A77]">
                  {formatINR(metrics.monthlyRevenue)}
                </td>
              </tr>
              <tr>
                <td className="py-1.5 text-[#6B665E] dark:text-[#A69E92]">
                  Variable Costs ({metrics.foodPct}% food cost)
                </td>
                <td className="py-1.5 text-right font-medium text-[#A63222] dark:text-[#E06C5B]">
                  -{formatINR(metrics.variableCosts)}
                </td>
              </tr>
              <tr>
                <td className="py-1.5 font-semibold text-[#111111] dark:text-[#E6DED0]">
                  Total Fixed Operating Costs
                </td>
                <td className="py-1.5 text-right font-semibold text-[#A63222] dark:text-[#E06C5B]">
                  -{formatINR(metrics.fixedCosts ?? metrics.fixedCost)}
                </td>
              </tr>
              <tr className="bg-[#EFE9DC]/60 dark:bg-[#1B1916]">
                <td colSpan={2} className="py-1.5 px-2.5 text-[10px] text-[#6B665E] dark:text-[#A69E92]">
                  <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                    <span>Rent: {formatINR(metrics.rent)}</span>
                    <span>Staff: {formatINR(metrics.staff)}</span>
                    <span>Utilities: {formatINR(metrics.utils)}</span>
                    <span>Marketing: {formatINR(metrics.mktg)}</span>
                    <span>Other: {formatINR(metrics.other)}</span>
                  </div>
                </td>
              </tr>
              <tr>
                <td className="py-1.5 font-medium text-[#111111] dark:text-[#E6DED0]">
                  Total Operating Expenses (Fixed + Var)
                </td>
                <td className="py-1.5 text-right font-semibold text-[#A63222] dark:text-[#E06C5B]">
                  -{formatINR(metrics.totalExpenses)}
                </td>
              </tr>
              <tr>
                <td className="pt-2 pb-1 font-bold text-xs text-[#111111] dark:text-white">
                  Estimated Operating Profit
                </td>
                <td
                  className={`pt-2 pb-1 text-right font-bold text-xs ${isProfitable ? 'text-[#254C3B] dark:text-[#4C9A77]' : 'text-[#A63222] dark:text-[#E06C5B]'
                    }`}
                >
                  {formatINR(metrics.operatingProfit)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Transparency & Scope Disclosure */}
      <div className="bg-[#EAE3D5]/55 dark:bg-[#161513] p-3 rounded-lg border border-[#DDD4C3] dark:border-[#2F2B25] text-[11px] text-[#6B665E] dark:text-[#A69E92] space-y-1">
        <div className="flex items-center gap-1.5 font-semibold text-[#111111] dark:text-[#E6DED0]">
          <Info className="w-3.5 h-3.5 text-[#D9541E] shrink-0" />
          <span>Assumption Scope & Limitations</span>
        </div>
        <p className="leading-relaxed">
          All financial figures are directional planning projections, not guaranteed outcomes. Models <em>Operating Profit</em> excluding income tax, GST, loan EMI, depreciation, and delivery aggregator commissions (15%–25%). Use <strong>Edit Assumptions</strong> above to stress-test variable cost %.
        </p>
      </div>

      {/* Compact LLM AI Insights */}
      <AIInsightsPanel insights={insights} subtitle="Financial Interpretation" />
    </section>
  );
}
