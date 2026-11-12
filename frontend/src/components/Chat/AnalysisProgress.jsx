import React from 'react';
import { CheckCircle2, Loader2, Circle, Compass, SlidersHorizontal } from 'lucide-react';

export default function AnalysisProgress({ currentStepIndex = 0, mode = 'full' }) {
  if (mode === 'scenario') {
    return (
      <div className="editorial-panel p-4 rounded-xl max-w-xl my-4 flex items-center gap-3 border-l-2 border-l-[#D9541E]">
        <Loader2 className="w-5 h-5 text-[#D9541E] animate-spin shrink-0" />
        <div>
          <div className="text-xs font-bold text-[#111111] dark:text-[#F3EEE3] flex items-center gap-1.5">
            <SlidersHorizontal className="w-3.5 h-3.5 text-[#D9541E]" />
            <span>Evaluating What-If Scenario</span>
          </div>
          <div className="text-[11px] text-[#6B665E] dark:text-[#A69E92] font-medium mt-0.5">
            Recalculating ML prediction, opportunity score, and financial deltas...
          </div>
        </div>
      </div>
    );
  }

  if (mode === 'casual') {
    return (
      <div className="editorial-panel px-4 py-3 rounded-xl max-w-xs my-3 flex items-center gap-2.5">
        <Loader2 className="w-4 h-4 text-[#D9541E] animate-spin shrink-0" />
        <span className="text-xs text-[#111111] dark:text-[#F3EEE3] font-medium">
          BizAdvisor is preparing a response...
        </span>
      </div>
    );
  }

  const steps = [
    { label: 'Concept & Parameter Validation', desc: 'Confirming location, format, cuisine, and ticket inputs' },
    { label: 'Historical Location Context', desc: 'Querying Bengaluru Zomato location benchmarks' },
    { label: 'ML Performance & Competition', desc: 'Running Random Forest classifier and Google Places scan' },
    { label: 'Opportunity & Financial Modeling', desc: 'Scoring opportunity pillars and running unit economics' },
    { label: 'Synthesizing AI Insights', desc: 'Generating concise executive interpretations for every card' },
  ];

  return (
    <div className="editorial-panel p-5 rounded-xl max-w-xl my-4">
      <div className="flex items-center justify-between text-[11px] font-bold text-[#111111] dark:text-[#F3EEE3] uppercase tracking-[0.08em] mb-4 pb-2.5 border-b border-[#E6DED0] dark:border-[#2F2B25]">
        <span className="flex items-center gap-2">
          <Compass className="w-4 h-4 text-[#D9541E]" />
          <span>Multi-Agent Analysis Pipeline</span>
        </span>
        <span className="text-[10px] font-medium text-[#6B665E] dark:text-[#A69E92] normal-case tracking-normal">
          Running live analytics
        </span>
      </div>

      <div className="space-y-3">
        {steps.map((step, idx) => {
          const isDone = idx < currentStepIndex;
          const isCurrent = idx === currentStepIndex;
          return (
            <div key={idx} className="flex items-start gap-3 text-xs">
              {isDone ? (
                <CheckCircle2 className="w-4 h-4 text-[#254C3B] dark:text-[#4C9A77] shrink-0 mt-0.5" />
              ) : isCurrent ? (
                <Loader2 className="w-4 h-4 text-[#D9541E] animate-spin shrink-0 mt-0.5" />
              ) : (
                <Circle className="w-4 h-4 text-[#C9BFAE] dark:text-[#3A352E] shrink-0 mt-0.5" />
              )}
              <div>
                <div
                  className={`font-semibold ${
                    isDone
                      ? 'text-[#254C3B] dark:text-[#4C9A77]'
                      : isCurrent
                        ? 'text-[#111111] dark:text-white'
                        : 'text-[#6B665E] dark:text-[#7D766C]'
                  }`}
                >
                  {step.label}
                </div>
                <div
                  className={`text-[11px] mt-0.5 ${
                    isCurrent
                      ? 'text-[#6B665E] dark:text-[#A69E92]'
                      : 'text-[#8C857B] dark:text-[#666057]'
                  }`}
                >
                  {step.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
