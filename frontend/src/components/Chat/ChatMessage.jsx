import React, { useState } from 'react';
import { User, Compass, Copy, Check } from 'lucide-react';
import LocationCard from '../Analysis/LocationCard';
import PerformanceCard from '../Analysis/PerformanceCard';
import CompetitionCard from '../Analysis/CompetitionCard';
import OpportunityCard from '../Analysis/OpportunityCard';
import FinancialCard from '../Analysis/FinancialCard';
import ScenarioCard from '../Analysis/ScenarioCard';
import WhatThisMeansCard from '../Analysis/WhatThisMeansCard';

function CopyButton({ text, dark = false, className = '' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e) => {
    e.stopPropagation();
    if (!text) return;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      title={copied ? 'Copied!' : 'Copy text'}
      aria-label={copied ? 'Copied!' : 'Copy text'}
      className={`p-1.5 rounded-md border transition-colors flex items-center justify-center shrink-0 cursor-pointer ${
        dark
          ? 'bg-white/10 hover:bg-white/15 border-white/15 text-[#E6DED0]'
          : 'bg-[#F8F5EE] dark:bg-[#22201D] hover:bg-[#E6DED0] dark:hover:bg-[#2D2924] border-[#DDD4C3] dark:border-[#3A352E] text-[#6B665E] dark:text-[#A69E92] hover:text-[#111111] dark:hover:text-white'
      } ${className}`}
    >
      {copied ? (
        <Check className="w-3.5 h-3.5 text-[#254C3B] dark:text-[#4C9A77] stroke-[2.5]" />
      ) : (
        <Copy className="w-3.5 h-3.5 stroke-[1.8]" />
      )}
    </button>
  );
}

function parseMarkdownInline(text) {
  if (!text) return null;
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
      return (
        <strong key={index} className="font-semibold text-[#111111] dark:text-white">
          {part.slice(2, -2)}
        </strong>
      );
    } else if (part.startsWith('*') && part.endsWith('*') && part.length >= 2) {
      return (
        <em key={index} className="italic text-[#6B665E] dark:text-[#C8C1B6]">
          {part.slice(1, -1)}
        </em>
      );
    }
    return part;
  });
}

function RenderFormattedContent({ content }) {
  if (!content) return null;
  const lines = content.split('\n');

  return (
    <div className="space-y-1.5">
      {lines.map((line, lineIdx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={lineIdx} className="h-1.5" />;

        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          return (
            <div key={lineIdx} className="flex items-start gap-2 pl-2">
              <span className="text-[#D9541E] font-bold">•</span>
              <div>{parseMarkdownInline(trimmed.slice(2))}</div>
            </div>
          );
        }

        return (
          <p key={lineIdx} className="leading-relaxed">
            {parseMarkdownInline(line)}
          </p>
        );
      })}
    </div>
  );
}

export default function ChatMessage({ message, onOpenMapModal, onCreateScenario }) {
  const isUser = message.role === 'user';
  const mode = message.mode || (message.scenarioComparison ? 'scenario' : message.analysis ? 'full' : 'casual');
  const analysis = message.analysis;

  // Support both nested ai_insights and top-level insight fields cleanly
  const insightsRoot = analysis?.ai_insights || analysis || {};

  if (isUser) {
    return (
      <div className="flex justify-end my-4">
        <div className="flex items-center gap-2.5 max-w-xl">
          <CopyButton text={message.content} />

          <div className="bg-[#111111] dark:bg-[#22201D] text-white dark:text-[#F3EEE3] px-4 py-3 rounded-xl rounded-tr-sm border border-[#111111] dark:border-[#3A352E] text-sm leading-relaxed">
            {message.content}
          </div>

          <div className="w-8 h-8 rounded-lg bg-[#E6DED0] dark:bg-[#22201D] border border-[#C9BFAE] dark:border-[#3A352E] flex items-center justify-center shrink-0 text-[#111111] dark:text-[#F3EEE3]">
            <User className="w-4 h-4 text-[#D9541E]" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start my-6 w-full">
      <div className="flex items-start gap-3.5 max-w-4xl w-full">
        {/* Brand AI Avatar */}
        <div className="w-8 h-8 rounded-lg bg-[#D9541E] flex items-center justify-center shrink-0 text-white mt-0.5">
          <Compass className="w-4 h-4" />
        </div>

        {/* Response & Structured Dashboard Body */}
        <div className="space-y-5 flex-1 min-w-0">
          {message.content && (
            <div className="editorial-panel text-[#111111] dark:text-[#E6DED0] text-sm leading-relaxed p-4 sm:p-5 rounded-xl">
              <RenderFormattedContent content={message.content} />

              <div className="flex justify-end mt-3 pt-2.5 border-t border-[#EAE3D5] dark:border-[#2F2B25]">
                <CopyButton text={message.content} />
              </div>
            </div>
          )}

          {mode === 'scenario' && message.scenarioComparison && (
            <ScenarioCard scenarioData={message.scenarioComparison} />
          )}

          {mode === 'full' && analysis && (
            <div className="space-y-5">
              {/* 1. Location Analysis */}
              {analysis.location_result && (
                <LocationCard
                  locationData={analysis.location_result}
                  insights={insightsRoot.location_insights || analysis.location_insights}
                />
              )}

              {/* 2. ML Performance Prediction */}
              {analysis.performance_result && (
                <PerformanceCard
                  performanceData={analysis.performance_result}
                  insights={insightsRoot.performance_insights || analysis.performance_insights}
                />
              )}

              {/* 3. Competition Analysis */}
              {analysis.competition_result && (
                <CompetitionCard
                  competitionData={analysis.competition_result}
                  onOpenMapModal={onOpenMapModal}
                  insights={insightsRoot.competition_insights || analysis.competition_insights}
                />
              )}

              {/* 4. Business Opportunity Score */}
              {analysis.opportunity_result && (
                <OpportunityCard
                  opportunityData={analysis.opportunity_result}
                  onCreateScenario={onCreateScenario}
                  insights={insightsRoot.opportunity_insights || analysis.opportunity_insights}
                />
              )}

              {/* 5. Financial Analysis */}
              {(analysis.financial || analysis.financial_result) && (
                <FinancialCard
                  financialData={analysis.financial || analysis.financial_result}
                  onCreateScenario={onCreateScenario}
                  insights={insightsRoot.financial_insights || analysis.financial_insights}
                />
              )}

              {/* 6. Executive Summary / What This Means */}
              <WhatThisMeansCard
                analysis={analysis}
                recommendations={insightsRoot.business_recommendations || analysis.business_recommendations}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
