import React from 'react';
import { Volume2, Pause, Square, Play } from 'lucide-react';
import { useTextToSpeech } from '../../hooks/useTextToSpeech';

/**
 * TextToSpeechButton
 *
 * Accepts a `text` prop and renders a polished listen/pause/stop control.
 * Uses the useTextToSpeech hook internally.
 *
 * Props:
 *   text {string} - Exact text to be spoken. Do NOT transform it.
 */
export default function TextToSpeechButton({ text }) {
  const { speaking, paused, available, speak, pause, resume, stop } =
    useTextToSpeech();

  // Feature unavailable — show a subtle non-crashing notice
  if (!available) {
    return (
      <p className="text-xs text-slate-500 dark:text-slate-400 italic mt-1">
        Audio playback isn't supported in this browser.
      </p>
    );
  }

  // ── Handlers ────────────────────────────────────────────────────────────────
  const handleListen = () => speak(text);
  const handlePause = () => pause();
  const handleResume = () => resume();
  const handleStop = () => stop();

  // ── Derived UI state ─────────────────────────────────────────────────────────
  const isPlaying = speaking && !paused;

  // ── Animations (CSS injected inline via style tag) ───────────────────────────
  const keyframesCSS = `
    @keyframes tts-wave1 {
      0%, 100% { transform: scaleY(0.4); }
      50%       { transform: scaleY(1); }
    }
    @keyframes tts-wave2 {
      0%, 100% { transform: scaleY(0.8); }
      25%       { transform: scaleY(0.3); }
      75%       { transform: scaleY(1); }
    }
    @keyframes tts-wave3 {
      0%, 100% { transform: scaleY(1); }
      50%       { transform: scaleY(0.3); }
    }
  `;

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <>
      <style>{keyframesCSS}</style>

      <div className="flex items-center gap-2 mt-3 flex-wrap">
        {/* ── Primary action button ── */}
        {isPlaying ? (
          /* PLAYING state: Pause + Stop */
          <>
            <button
              type="button"
              onClick={handlePause}
              aria-label="Pause audio"
              className="
                inline-flex items-center gap-2 px-3 py-1.5 rounded-lg
                bg-indigo-100 dark:bg-indigo-500/15 border border-indigo-300 dark:border-indigo-500/30 text-indigo-700 dark:text-indigo-300
                text-xs font-semibold
                hover:bg-indigo-200 dark:hover:bg-indigo-500/25 dark:hover:text-indigo-200
                active:scale-95
                transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-indigo-500/40
                cursor-pointer shadow-xs
              "
            >
              <Pause className="w-3.5 h-3.5 fill-indigo-700 dark:fill-indigo-300" />
              <span>Pause</span>
              {/* Animated sound wave indicator */}
              <SoundWave />
            </button>

            <button
              type="button"
              onClick={handleStop}
              aria-label="Stop audio"
              className="
                inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                bg-slate-100 dark:bg-slate-800/70 border border-slate-300 dark:border-slate-700/50 text-slate-600 dark:text-slate-400
                text-xs font-semibold
                hover:bg-slate-200 dark:hover:bg-slate-700/70 hover:text-slate-900 dark:hover:text-slate-200
                active:scale-95
                transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-slate-500/40
                cursor-pointer shadow-xs
              "
            >
              <Square className="w-3 h-3 fill-slate-500 dark:fill-slate-400" />
              <span>Stop</span>
            </button>
          </>
        ) : paused ? (
          /* PAUSED state: Resume + Stop */
          <>
            <button
              type="button"
              onClick={handleResume}
              aria-label="Resume audio"
              className="
                inline-flex items-center gap-2 px-3 py-1.5 rounded-lg
                bg-emerald-100 dark:bg-emerald-500/15 border border-emerald-300 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-300
                text-xs font-semibold
                hover:bg-emerald-200 dark:hover:bg-emerald-500/25 dark:hover:text-emerald-200
                active:scale-95
                transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-emerald-500/40
                cursor-pointer shadow-xs
              "
            >
              <Play className="w-3.5 h-3.5 fill-emerald-700 dark:fill-emerald-300" />
              <span>Resume</span>
            </button>

            <button
              type="button"
              onClick={handleStop}
              aria-label="Stop audio"
              className="
                inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                bg-slate-100 dark:bg-slate-800/70 border border-slate-300 dark:border-slate-700/50 text-slate-600 dark:text-slate-400
                text-xs font-semibold
                hover:bg-slate-200 dark:hover:bg-slate-700/70 hover:text-slate-900 dark:hover:text-slate-200
                active:scale-95
                transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-slate-500/40
                cursor-pointer shadow-xs
              "
            >
              <Square className="w-3 h-3 fill-slate-500 dark:fill-slate-400" />
              <span>Stop</span>
            </button>
          </>
        ) : (
          /* IDLE / FINISHED state: Listen / Listen again */
          <button
            type="button"
            onClick={handleListen}
            disabled={!text}
            aria-label="Listen to business takeaway"
            className="
              group inline-flex items-center gap-2 px-3 py-1.5 rounded-lg
              bg-indigo-50 dark:bg-slate-800/60 border border-indigo-200 dark:border-slate-700/50 text-indigo-700 dark:text-slate-300
              text-xs font-semibold
              hover:bg-indigo-100 dark:hover:bg-indigo-500/15 dark:hover:border-indigo-500/30 dark:hover:text-indigo-300
              active:scale-95
              disabled:opacity-40 disabled:cursor-not-allowed
              transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-indigo-500/40
              cursor-pointer shadow-xs
            "
          >
            <Volume2
              className="
                w-3.5 h-3.5
                group-hover:scale-110
                transition-transform duration-200
              "
            />
            <span>Listen</span>
          </button>
        )}

        {/* Speaking label */}
        {isPlaying && (
          <span className="text-xs text-indigo-600 dark:text-indigo-400/80 font-semibold animate-pulse">
            Speaking…
          </span>
        )}
        {paused && (
          <span className="text-xs text-amber-600 dark:text-amber-400/80 font-semibold">
            Paused
          </span>
        )}
      </div>
    </>
  );
}

/**
 * SoundWave — three animated bars shown while audio is playing.
 */
function SoundWave() {
  const barBase = {
    display: 'inline-block',
    width: '2px',
    borderRadius: '2px',
    backgroundColor: 'currentColor',
    transformOrigin: 'bottom',
  };

  return (
    <span
      aria-hidden="true"
      style={{ display: 'inline-flex', items: 'flex-end', gap: '2px', height: '12px' }}
    >
      <span
        style={{
          ...barBase,
          height: '8px',
          animation: 'tts-wave1 0.6s ease-in-out infinite',
          animationDelay: '0s',
        }}
      />
      <span
        style={{
          ...barBase,
          height: '12px',
          animation: 'tts-wave2 0.6s ease-in-out infinite',
          animationDelay: '0.15s',
        }}
      />
      <span
        style={{
          ...barBase,
          height: '7px',
          animation: 'tts-wave3 0.6s ease-in-out infinite',
          animationDelay: '0.3s',
        }}
      />
    </span>
  );
}
