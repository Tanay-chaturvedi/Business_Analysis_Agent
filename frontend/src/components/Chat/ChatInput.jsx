import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Loader2, MapPin } from 'lucide-react';

export default function ChatInput({
  onSendMessage,
  isLoading,
  hasMessages,
  onOpenLocationPicker,
  selectedLocation,
}) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  const suggestedFollowups = [
    'What if I reduce the price to ₹1200?',
    'Compare Koramangala vs Indiranagar',
    'Show nearby competitors',
    'Explain the opportunity score breakdown',
  ];

  // Append selected location from LocationPicker
  useEffect(() => {
    if (selectedLocation) {
      if (!input.trim()) {
        setInput(selectedLocation);
      } else if (!input.toLowerCase().includes(selectedLocation.toLowerCase())) {
        setInput((prev) => `${prev.trim()} in ${selectedLocation}`);
      }
    }
  }, [selectedLocation]);

  // Auto resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [input]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="sticky bottom-0 left-0 right-0 p-4 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-t border-slate-200 dark:border-slate-800/80 transition-colors duration-200">
      <div className="max-w-4xl mx-auto space-y-2">
        {/* Top Control Bar: Browse Locations & Suggested Follow-up chips */}
        <div className="flex items-center justify-between gap-2 overflow-x-auto pb-1 text-xs no-scrollbar">
          <div className="flex items-center gap-2 shrink-0">
            {/* 📍 Browse Locations Button */}
            <button
              type="button"
              onClick={onOpenLocationPicker}
              className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-500/10 hover:bg-indigo-100 dark:hover:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-500/30 font-semibold text-[11px] transition-all cursor-pointer shadow-xs"
            >
              <MapPin className="w-3.5 h-3.5" />
              <span>Browse Locations</span>
            </button>
          </div>

          {hasMessages && (
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-slate-500 font-medium shrink-0 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-indigo-600 dark:text-indigo-400" /> Suggested:
              </span>
              {suggestedFollowups.map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(chip)}
                  disabled={isLoading}
                  className="shrink-0 px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800/70 hover:bg-slate-200 dark:hover:bg-slate-700/80 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700/60 transition-colors text-[11px] font-medium cursor-pointer"
                >
                  {chip}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Input Text Box */}
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a follow-up or type a business analysis idea..."
            disabled={isLoading}
            className="w-full bg-slate-50 dark:bg-slate-950/80 border border-slate-300 dark:border-slate-800 rounded-2xl pl-4 pr-12 py-3.5 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-none shadow-xs transition-colors"
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2.5 p-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 text-white transition-all shadow-md shadow-indigo-600/20 cursor-pointer"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </form>

        <div className="px-2 text-[10px] text-slate-400 dark:text-slate-500">
          Press <strong>Enter</strong> to send, <strong>Shift + Enter</strong> for newline
        </div>
      </div>
    </div>
  );
}
