import React, { useState } from 'react';
import { User, Bot, Sparkles, MapPin, Store, Copy, Check } from 'lucide-react';
import LocationCard from '../Analysis/LocationCard';
import PerformanceCard from '../Analysis/PerformanceCard';
import CompetitionCard from '../Analysis/CompetitionCard';
import OpportunityCard from '../Analysis/OpportunityCard';
import FinancialCard from '../Analysis/FinancialCard';
import ScenarioCard from '../Analysis/ScenarioCard';
import WhatThisMeansCard from '../Analysis/WhatThisMeansCard';

function CopyButton({ text, className = '' }) {
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
      className={`p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800/80 hover:bg-slate-200 dark:hover:bg-slate-700/80 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition-all duration-200 flex items-center justify-center shrink-0 border border-slate-200 dark:border-slate-700/50 shadow-xs focus:outline-none cursor-pointer ${className}`}
    >
      {copied ? (
        <Check className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 stroke-[2.5]" />
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
        <strong key={index} className="font-bold text-slate-900 dark:text-white">
          {part.slice(2, -2)}
        </strong>
      );
    } else if (part.startsWith('*') && part.endsWith('*') && part.length >= 2) {
      return (
        <em key={index} className="italic text-slate-700 dark:text-slate-200">
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
              <span className="text-indigo-600 dark:text-indigo-400 font-bold">•</span>
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

  if (isUser) {
    return (
      <div className="flex justify-end my-4 animate-fade-in">
        <div className="flex items-center gap-2.5 max-w-xl">
          {/* Copy Icon Button BEFORE user message bubble */}
          <CopyButton text={message.content} />

          <div className="bg-indigo-600 text-white p-4 rounded-2xl rounded-tr-none shadow-md shadow-indigo-600/10 text-sm leading-relaxed">
            {message.content}
          </div>

          <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 flex items-center justify-center shrink-0 text-slate-700 dark:text-slate-300">
            <User className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
          </div>
        </div>
      </div>
    );
  }

  // Assistant message
  return (
    <div className="flex justify-start my-6 animate-fade-in w-full">
      <div className="flex items-start gap-3 max-w-4xl w-full">
        {/* AI Avatar */}
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shrink-0 text-white shadow-md shadow-indigo-500/20">
          <Bot className="w-5 h-5" />
        </div>

        {/* AI Response Container */}
        <div className="space-y-4 flex-1 min-w-0">
          {/* Executive Text Commentary */}
          {message.content && (
            <div className="text-slate-800 dark:text-slate-200 text-sm leading-relaxed bg-white dark:bg-slate-900/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-800/80 shadow-xs">
              <RenderFormattedContent content={message.content} />

              {/* Copy Icon Button AFTER complete AI response text */}
              <div className="flex justify-end mt-2 pt-2 border-t border-slate-100 dark:border-slate-800/50">
                <CopyButton text={message.content} />
              </div>
            </div>
          )}

          {/* Render Scenario Comparison Card if present and mode is scenario */}
          {mode === 'scenario' && message.scenarioComparison && (
            <ScenarioCard scenarioData={message.scenarioComparison} />
          )}

          {/* Render Rich Analysis Cards if present and mode is full */}
          {mode === 'full' && analysis && (
            <div className="space-y-4">
              {/* 1. Location Card */}
              {analysis.location_result && (
                <LocationCard locationData={analysis.location_result} />
              )}

              {/* 2. Performance Card */}
              {analysis.performance_result && (
                <PerformanceCard performanceData={analysis.performance_result} />
              )}

              {/* 3. Competition Card */}
              {analysis.competition_result && (
                <CompetitionCard
                  competitionData={analysis.competition_result}
                  onOpenMapModal={onOpenMapModal}
                />
              )}

              {/* 4. Opportunity Card */}
              {analysis.opportunity_result && (
                <OpportunityCard
                  opportunityData={analysis.opportunity_result}
                  onCreateScenario={onCreateScenario}
                />
              )}

              {/* 5. Financial Analysis Card */}
              {(analysis.financial || analysis.financial_result) && (
                <FinancialCard
                  financialData={analysis.financial || analysis.financial_result}
                />
              )}

              {/* 6. What This Means (User-Friendly English Summary) */}
              <WhatThisMeansCard analysis={analysis} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
