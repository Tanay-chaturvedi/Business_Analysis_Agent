import React from 'react';
import { CheckCircle2, Loader2, Circle, Bot, SlidersHorizontal } from 'lucide-react';

export default function AnalysisProgress({ currentStepIndex = 0, mode = 'full' }) {
  if (mode === 'scenario') {
    return (
      <div className="glass-panel p-4 rounded-xl border border-purple-500/30 max-w-xl my-4 animate-fade-in flex items-center gap-3 bg-purple-50 dark:bg-purple-950/20">
        <Loader2 className="w-5 h-5 text-purple-600 dark:text-purple-400 animate-spin shrink-0" />
        <div>
          <div className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
            <SlidersHorizontal className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
            Evaluating your scenario...
          </div>
          <div className="text-[11px] text-slate-600 dark:text-slate-400 font-medium">
            Recalculating ML model prediction & opportunity score for your updated inputs
          </div>
        </div>
      </div>
    );
  }

  if (mode === 'casual') {
    return (
      <div className="glass-panel p-3 px-4 rounded-xl border border-slate-200 dark:border-slate-800 max-w-sm my-3 animate-fade-in flex items-center gap-2.5">
        <Bot className="w-4 h-4 text-indigo-600 dark:text-indigo-400 animate-pulse shrink-0" />
        <span className="text-xs text-slate-700 dark:text-slate-300 font-medium">BizAdvisor is typing...</span>
      </div>
    );
  }

  const steps = [
    { label: 'Understanding business idea', desc: 'Extracting business requirements' },
    { label: 'Location Analysis', desc: 'Analyzing historical location data...' },
    { label: 'Performance Analysis', desc: 'Evaluating ML performance model...' },
    { label: 'Competition Analysis', desc: 'Checking real-time nearby competitors...' },
    { label: 'Opportunity Analysis', desc: 'Synthesizing opportunity score & strategy...' },
  ];

  return (
    <div className="glass-panel p-5 rounded-2xl border border-indigo-200 dark:border-indigo-500/20 max-w-xl my-4 animate-fade-in shadow-xl shadow-indigo-950/10">
      <div className="flex items-center gap-2.5 text-xs font-bold text-indigo-700 dark:text-indigo-300 uppercase tracking-wider mb-4 pb-2 border-b border-slate-200 dark:border-slate-800">
        <Bot className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
        <span>BizAdvisor is analyzing your idea</span>
      </div>

      <div className="space-y-3">
        {steps.map((step, idx) => {
          const isDone = idx < currentStepIndex;
          const isCurrent = idx === currentStepIndex;
          return (
            <div key={idx} className="flex items-start gap-3 text-xs transition-colors">
              {isDone ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
              ) : isCurrent ? (
                <Loader2 className="w-4 h-4 text-indigo-600 dark:text-indigo-400 animate-spin shrink-0 mt-0.5" />
              ) : (
                <Circle className="w-4 h-4 text-slate-300 dark:text-slate-600 shrink-0 mt-0.5" />
              )}
              <div>
                <div
                  className={`font-semibold ${isDone
                      ? 'text-emerald-700 dark:text-emerald-300'
                      : isCurrent
                        ? 'text-indigo-700 dark:text-indigo-300'
                        : 'text-slate-400 dark:text-slate-500'
                    }`}
                >
                  {step.label}
                </div>
                <div className={`text-[10px] ${isCurrent ? 'text-slate-600 dark:text-slate-400' : 'text-slate-400 dark:text-slate-500'}`}>
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
