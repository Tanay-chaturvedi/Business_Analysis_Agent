import React from 'react';
import { Sparkles, MapPin, Store, Scale, Calculator, ArrowRight } from 'lucide-react';

export default function EmptyState({ onSelectPrompt }) {
  const suggestedPrompts = [
    {
      title: 'Japanese Casual Dining',
      prompt: 'Analyze a Japanese Casual Dining restaurant in Koramangala with cost for two ₹1800, online ordering yes and table booking yes',
      icon: MapPin,
      badge: 'Full Assessment',
    },
    {
      title: 'Neighborhood Cafe Feasibility',
      prompt: 'Analyze a Cafe in HSR Layout with cost for two ₹600, online ordering yes and table booking no',
      icon: Store,
      badge: 'Location & Competition',
    },
    {
      title: 'Quick Service Concept',
      prompt: 'Analyze a North Indian Quick Service outlet in Indiranagar, ₹450 for two, online ordering yes, table booking no',
      icon: Scale,
      badge: 'Unit Economics & ML',
    },
    {
      title: 'Fine Dining Evaluation',
      prompt: 'Analyze an Italian Fine Dining restaurant in Whitefield for ₹1600, online ordering no, table booking yes',
      icon: Calculator,
      badge: 'Margin & Break-Even',
    },
  ];

  return (
    <div className="max-w-3xl mx-auto px-2 sm:px-4 py-10 sm:py-16 text-center flex flex-col items-center justify-center">
      {/* Eyebrow Tag */}
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-[#E6DED0] dark:bg-[#22201D] border border-[#D4C9B6] dark:border-[#36312A] text-[#111111] dark:text-[#F3EEE3] text-[11px] font-semibold uppercase tracking-[0.06em] mb-6">
        <Sparkles className="w-3.5 h-3.5 text-[#D9541E]" />
        <span>Bengaluru Restaurant Advisory</span>
      </div>

      {/* Editorial Display Heading */}
      <h1 className="font-heading text-3xl sm:text-4xl font-extrabold text-[#111111] dark:text-[#F3EEE3] tracking-tight leading-[1.15] max-w-2xl mb-4">
        Turn your restaurant concept into a{' '}
        <span className="text-[#D9541E]">data-backed decision.</span>
      </h1>

      {/* Subheading */}
      <p className="text-[#6B665E] dark:text-[#A69E92] text-sm sm:text-base max-w-xl mb-10 leading-relaxed">
        Combine historical Zomato market benchmarks, Random Forest classification, live Google Places competitor intelligence, and financial simulation in one brief.
      </p>

      {/* Suggested Prompt Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full text-left">
        {suggestedPrompts.map((item, index) => {
          const Icon = item.icon;
          return (
            <button
              type="button"
              key={index}
              onClick={() => onSelectPrompt(item.prompt)}
              className="editorial-card-interactive p-4.5 rounded-xl cursor-pointer group flex flex-col justify-between text-left"
            >
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <span className="text-[10px] font-semibold text-[#6B665E] dark:text-[#A69E92] uppercase tracking-[0.06em] bg-[#F3EEE3] dark:bg-[#26231F] px-2 py-0.5 rounded border border-[#E6DED0] dark:border-[#36312A]">
                    {item.badge}
                  </span>
                  <Icon className="w-4 h-4 text-[#6B665E] dark:text-[#A69E92] group-hover:text-[#D9541E] transition-colors" />
                </div>
                <h3 className="font-heading font-bold text-[#111111] dark:text-[#F3EEE3] text-sm group-hover:text-[#D9541E] transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-[#6B665E] dark:text-[#A69E92] mt-1.5 line-clamp-2 leading-relaxed">
                  "{item.prompt}"
                </p>
              </div>

              <div className="mt-4 pt-2.5 border-t border-[#EAE3D5] dark:border-[#2C2823] flex items-center justify-between text-xs font-semibold text-[#D9541E]">
                <span>Run assessment</span>
                <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
