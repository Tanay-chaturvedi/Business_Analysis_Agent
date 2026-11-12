import React from 'react';
import { Sparkles } from 'lucide-react';

/**
 * Reusable compact Ink Black (#111111) AI Insights section rendered
 * across all six BizAdvisor analysis cards.
 */
export default function AIInsightsPanel({
  insights,
  title = 'AI Insights',
  subtitle = 'Strategic Interpretation',
}) {
  if (!Array.isArray(insights) || insights.length === 0) {
    return null;
  }

  return (
    <div className="editorial-ai-panel rounded-lg p-3.5 sm:p-4 space-y-2.5">
      <div className="flex items-center justify-between gap-2 pb-2 border-b border-white/10">
        <div className="flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-[#D9541E] shrink-0" />
          <h4 className="text-[11px] font-bold uppercase tracking-[0.08em] text-white">
            {title}
          </h4>
        </div>
        <span className="text-[10px] font-medium text-[#A69E92]">
          {subtitle}
        </span>
      </div>

      <ul className="space-y-2">
        {insights.slice(0, 3).map((point, idx) => (
          <li
            key={idx}
            className="flex items-start gap-2.5 text-xs leading-relaxed text-[#EFEAE0]"
          >
            <span
              aria-hidden="true"
              className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#D9541E] shrink-0"
            />
            <span>{point}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

