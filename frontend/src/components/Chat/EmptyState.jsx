import React from 'react';
import { Sparkles, MapPin, Store, Scale, Calculator, ArrowRight } from 'lucide-react';

export default function EmptyState({ onSelectPrompt }) {
  const suggestedPrompts = [
    {
      title: 'Japanese Restaurant',
      location: 'Koramangala, Bengaluru',
      prompt: 'Analyze a Japanese restaurant in Koramangala',
      icon: MapPin,
      badge: 'Location & ML Analysis',
    },
    {
      title: 'Cafe Competitors',
      location: 'HSR Layout, Bengaluru',
      prompt: 'Find competitors for a cafe in HSR Layout',
      icon: Store,
      badge: 'Competitor Discovery',
    },
    {
      title: 'Location Comparison',
      location: 'Koramangala vs Indiranagar',
      prompt: 'Compare Koramangala vs Indiranagar',
      icon: Scale,
      badge: 'Multi-Location What-If',
    },
    {
      title: 'Price Adjustment',
      location: 'Koramangala, Bengaluru',
      prompt: 'What if I reduce my price to ₹1200?',
      icon: Calculator,
      badge: 'Price Sensitivity',
    },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-12 text-center my-auto flex flex-col items-center justify-center">
      {/* Icon Badge */}
      <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-600 dark:text-indigo-400 text-xs font-semibold mb-6">
        <Sparkles className="w-4 h-4" />
        <span>BizAdvisor AI Orchestrator</span>
      </div>

      {/* Main Heading */}
      <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight max-w-2xl mb-3">
        Turn your business idea into a <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-500 dark:from-indigo-400 dark:via-purple-400 dark:to-pink-400">data-backed decision.</span>
      </h1>

      {/* Subheading */}
      <p className="text-slate-600 dark:text-slate-400 text-sm sm:text-base max-w-xl mb-10 leading-relaxed">
        Analyze locations, competitors, historical performance and business opportunities with AI.
      </p>

      {/* Suggested Prompt Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full text-left">
        {suggestedPrompts.map((item, index) => {
          const Icon = item.icon;
          return (
            <div
              key={index}
              onClick={() => onSelectPrompt(item.prompt)}
              className="glass-card glass-card-hover p-4 rounded-2xl cursor-pointer group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider bg-indigo-500/10 px-2 py-0.5 rounded-md border border-indigo-500/20">
                    {item.badge}
                  </span>
                  <Icon className="w-4 h-4 text-slate-400 dark:text-slate-500 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors" />
                </div>
                <h3 className="font-semibold text-slate-900 dark:text-slate-200 text-sm group-hover:text-indigo-600 dark:group-hover:text-white transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                  "{item.prompt}"
                </p>
              </div>

              <div className="mt-4 flex items-center gap-1 text-xs font-medium text-indigo-600 dark:text-indigo-400 group-hover:text-indigo-700 dark:group-hover:text-indigo-300">
                <span>Analyze this scenario</span>
                <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
