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
    'What if I switch to Cafe?',
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
    <div className="sticky bottom-0 left-0 right-0 px-4 sm:px-6 py-3.5 bg-[#F3EEE3]/95 dark:bg-[#111111]/95 backdrop-blur-md border-t border-[#DDD4C3] dark:border-[#2F2B25] transition-colors duration-200">
      <div className="max-w-4xl mx-auto space-y-2.5">
        {/* Controls Row: Browse Locations & Suggested Follow-ups */}
        <div className="flex items-center gap-2 overflow-x-auto pb-0.5 text-xs no-scrollbar">
          <button
            type="button"
            onClick={onOpenLocationPicker}
            className="shrink-0 flex items-center gap-1.5 px-3 py-1 rounded-md bg-[#E6DED0] dark:bg-[#22201D] hover:bg-[#DDD4C3] dark:hover:bg-[#2D2924] text-[#111111] dark:text-[#F3EEE3] border border-[#C9BFAE] dark:border-[#3A352E] font-semibold text-[11px] transition-colors cursor-pointer"
          >
            <MapPin className="w-3.5 h-3.5 text-[#D9541E]" />
            <span>Browse Locations</span>
          </button>

          {hasMessages && (
            <div className="flex items-center gap-1.5 shrink-0">
              <span className="text-[#6B665E] dark:text-[#A69E92] font-medium shrink-0 flex items-center gap-1 pl-1">
                <Sparkles className="w-3 h-3 text-[#D9541E]" />
                <span className="text-[11px]">Follow-ups:</span>
              </span>
              {suggestedFollowups.map((chip, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onSendMessage(chip)}
                  disabled={isLoading}
                  className="shrink-0 px-2.5 py-1 rounded-md bg-white dark:bg-[#1A1917] hover:border-[#D9541E] text-[#111111] dark:text-[#E6DED0] border border-[#DDD4C3] dark:border-[#2F2B25] transition-colors text-[11px] font-medium cursor-pointer"
                >
                  {chip}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Input Composer */}
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your restaurant idea, location, cuisine, budget — or ask a What-If question..."
            disabled={isLoading}
            className="w-full bg-white dark:bg-[#1A1917] border border-[#C9BFAE] dark:border-[#3A352E] rounded-xl pl-4 pr-12 py-3 text-sm text-[#111111] dark:text-[#F3EEE3] placeholder-[#6B665E] dark:placeholder-[#8C857B] focus:outline-none focus:border-[#D9541E] focus:ring-1 focus:ring-[#D9541E] resize-none shadow-2xs transition-colors"
          />

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            aria-label="Send message"
            className="absolute right-2 p-2 rounded-lg editorial-btn-primary cursor-pointer"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </form>

        <div className="px-1 flex items-center justify-between text-[10px] text-[#6B665E] dark:text-[#8C857B]">
          <span>
            Press <strong className="font-semibold text-[#111111] dark:text-[#E6DED0]">Enter</strong> to send ·{' '}
            <strong className="font-semibold text-[#111111] dark:text-[#E6DED0]">Shift + Enter</strong> for new line
          </span>
          <span className="hidden sm:inline">Authoritative ML + Google Places + Financial Engine</span>
        </div>
      </div>
    </div>
  );
}
