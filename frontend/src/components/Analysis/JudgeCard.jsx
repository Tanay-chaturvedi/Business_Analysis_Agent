/**
 * JudgeCard.jsx — Final Business Verdict Card
 * ============================================
 * Displays the Judge Agent's final verdict after all specialist analyses.
 * Shows a colour-coded verdict badge, plain-language explanation,
 * strengths, risks, and one concrete recommendation.
 *
 * Props:
 *   judgeData {object} — the judge_result object from the backend
 *
 * Renders nothing if judgeData is missing or verdict is "unavailable".
 */

import React from 'react';
import { Gavel, CheckCircle, AlertTriangle, XCircle, Lightbulb } from 'lucide-react';

// ---------------------------------------------------------------------------
// Verdict configuration: colour + icon for each of the three possible verdicts
// ---------------------------------------------------------------------------
const VERDICT_CONFIG = {
  Promising: {
    icon:        CheckCircle,
    // Green palette
    badgeBg:     'bg-[#D1FAE5] dark:bg-[#064E3B]',
    badgeText:   'text-[#065F46] dark:text-[#6EE7B7]',
    iconColor:   'text-[#059669] dark:text-[#34D399]',
    borderColor: 'border-[#059669]/30 dark:border-[#34D399]/30',
    label:       'Promising',
  },
  Risky: {
    icon:        AlertTriangle,
    // Amber palette
    badgeBg:     'bg-[#FEF3C7] dark:bg-[#78350F]',
    badgeText:   'text-[#92400E] dark:text-[#FCD34D]',
    iconColor:   'text-[#D97706] dark:text-[#FBBF24]',
    borderColor: 'border-[#D97706]/30 dark:border-[#FBBF24]/30',
    label:       'Risky',
  },
  'Not Recommended': {
    icon:        XCircle,
    // Red palette
    badgeBg:     'bg-[#FEE2E2] dark:bg-[#7F1D1D]',
    badgeText:   'text-[#991B1B] dark:text-[#FCA5A5]',
    iconColor:   'text-[#DC2626] dark:text-[#F87171]',
    borderColor: 'border-[#DC2626]/30 dark:border-[#F87171]/30',
    label:       'Not Recommended',
  },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export default function JudgeCard({ judgeData }) {
  // Render nothing if data is absent or the verdict is unavailable
  if (!judgeData || !judgeData.verdict || judgeData.verdict === 'unavailable') {
    return null;
  }

  const config = VERDICT_CONFIG[judgeData.verdict] || VERDICT_CONFIG['Risky'];
  const VerdictIcon = config.icon;

  const strengths      = Array.isArray(judgeData.strengths)      ? judgeData.strengths      : [];
  const risks          = Array.isArray(judgeData.risks)          ? judgeData.risks          : [];
  const explanation    = judgeData.explanation    || '';
  const recommendation = judgeData.recommendation || '';

  return (
    <section className={`editorial-panel rounded-xl p-5 space-y-4 border ${config.borderColor}`}>

      {/* ── Card Header ─────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#E6DED0] dark:border-[#2F2B25]">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg border ${config.borderColor} ${config.badgeBg}`}>
            <Gavel className={`w-4 h-4 ${config.iconColor}`} />
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#6B665E] dark:text-[#A69E92]">
              07 · Judge Agent — Final Verdict
            </div>
            <h3 className="font-heading font-bold text-[#111111] dark:text-[#F3EEE3] text-sm sm:text-base">
              AI Business Verdict
            </h3>
          </div>
        </div>

        {/* Verdict badge */}
        <span className={`flex items-center gap-1.5 text-[11px] font-bold px-3 py-1 rounded-full ${config.badgeBg} ${config.badgeText}`}>
          <VerdictIcon className="w-3.5 h-3.5" />
          {config.label}
        </span>
      </div>

      {/* ── Explanation ─────────────────────────────────────────────────── */}
      {explanation && (
        <p className="text-xs sm:text-sm text-[#111111] dark:text-[#F3EEE3] leading-relaxed">
          {explanation}
        </p>
      )}

      {/* ── Strengths & Risks side by side ──────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">

        {/* Strengths */}
        <div className="editorial-subcard p-3 rounded-lg">
          <div className="flex items-center gap-1.5 mb-2">
            <CheckCircle className="w-3.5 h-3.5 text-[#059669] dark:text-[#34D399] shrink-0" />
            <span className="font-semibold text-[#059669] dark:text-[#34D399] uppercase tracking-wide text-[10px]">
              Strengths
            </span>
          </div>
          {strengths.length > 0 ? (
            <ul className="space-y-1.5">
              {strengths.map((item, i) => (
                <li key={i} className="flex items-start gap-1.5 text-[#374151] dark:text-[#D1D5DB] leading-relaxed">
                  <span className="text-[#059669] dark:text-[#34D399] mt-0.5 shrink-0">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-[#6B665E] dark:text-[#A69E92] italic text-xs leading-relaxed">
              No major strengths identified from the available analysis
            </p>
          )}
        </div>

        {/* Risks */}
        <div className="editorial-subcard p-3 rounded-lg">
          <div className="flex items-center gap-1.5 mb-2">
            <AlertTriangle className="w-3.5 h-3.5 text-[#D97706] dark:text-[#FBBF24] shrink-0" />
            <span className="font-semibold text-[#D97706] dark:text-[#FBBF24] uppercase tracking-wide text-[10px]">
              Risks
            </span>
          </div>
          {risks.length > 0 ? (
            <ul className="space-y-1.5">
              {risks.map((item, i) => (
                <li key={i} className="flex items-start gap-1.5 text-[#374151] dark:text-[#D1D5DB] leading-relaxed">
                  <span className="text-[#D97706] dark:text-[#FBBF24] mt-0.5 shrink-0">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-[#6B665E] dark:text-[#A69E92] italic text-xs leading-relaxed">
              No major risks identified from the available analysis
            </p>
          )}
        </div>
      </div>

      {/* ── Recommendation ──────────────────────────────────────────────── */}
      {recommendation && (
        <div className="bg-[#F8F5EE] dark:bg-[#161513] rounded-lg border border-[#E6DED0] dark:border-[#2F2B25] p-3 flex items-start gap-2.5">
          <Lightbulb className="w-4 h-4 text-[#D9541E] shrink-0 mt-0.5" />
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#6B665E] dark:text-[#A69E92] mb-1">
              Recommended Next Step
            </div>
            <p className="text-xs sm:text-sm text-[#111111] dark:text-[#F3EEE3] leading-relaxed">
              {recommendation}
            </p>
          </div>
        </div>
      )}

    </section>
  );
}
