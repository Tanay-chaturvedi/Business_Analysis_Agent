import React from 'react';
import { Volume2, Pause, Square, Play } from 'lucide-react';
import { useTextToSpeech } from '../../hooks/useTextToSpeech';

export default function TextToSpeechButton({ text }) {
  const { speaking, paused, available, speak, pause, resume, stop } =
    useTextToSpeech();

  if (!available) {
    return (
      <p className="text-xs text-[#6B665E] dark:text-[#A69E92] italic mt-1">
        Audio playback isn't supported in this browser.
      </p>
    );
  }

  const handleListen = () => speak(text);
  const handlePause = () => pause();
  const handleResume = () => resume();
  const handleStop = () => stop();

  const isPlaying = speaking && !paused;

  const keyframesCSS = `
    @keyframes tts-wave1 {
      0%, 100% { transform: scaleY(0.4); }
      50% { transform: scaleY(1); }
    }
    @keyframes tts-wave2 {
      0%, 100% { transform: scaleY(0.8); }
      25% { transform: scaleY(0.3); }
      75% { transform: scaleY(1); }
    }
    @keyframes tts-wave3 {
      0%, 100% { transform: scaleY(1); }
      50% { transform: scaleY(0.3); }
    }
  `;

  return (
    <>
      <style>{keyframesCSS}</style>

      <div className="flex items-center gap-2 mt-3 flex-wrap">
        {isPlaying ? (
          <>
            <button
              type="button"
              onClick={handlePause}
              aria-label="Pause audio"
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-[#D9541E]/15 border border-[#D9541E]/35 text-[#D9541E] text-xs font-semibold hover:bg-[#D9541E]/20 transition-colors cursor-pointer"
            >
              <Pause className="w-3.5 h-3.5 fill-current" />
              <span>Pause</span>
              <SoundWave />
            </button>

            <button
              type="button"
              onClick={handleStop}
              aria-label="Stop audio"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#EAE3D5] dark:bg-[#22201D] border border-[#C9BFAE] dark:border-[#3A352E] text-[#111111] dark:text-[#E6DED0] text-xs font-semibold hover:bg-[#DDD4C3] dark:hover:bg-[#2D2924] transition-colors cursor-pointer"
            >
              <Square className="w-3 h-3 fill-current" />
              <span>Stop</span>
            </button>
          </>
        ) : paused ? (
          <>
            <button
              type="button"
              onClick={handleResume}
              aria-label="Resume audio"
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-[#254C3B]/15 border border-[#254C3B]/35 text-[#254C3B] dark:text-[#4C9A77] text-xs font-semibold hover:bg-[#254C3B]/20 transition-colors cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Resume</span>
            </button>

            <button
              type="button"
              onClick={handleStop}
              aria-label="Stop audio"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#EAE3D5] dark:bg-[#22201D] border border-[#C9BFAE] dark:border-[#3A352E] text-[#111111] dark:text-[#E6DED0] text-xs font-semibold hover:bg-[#DDD4C3] dark:hover:bg-[#2D2924] transition-colors cursor-pointer"
            >
              <Square className="w-3 h-3 fill-current" />
              <span>Stop</span>
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={handleListen}
            disabled={!text}
            aria-label="Listen to business takeaway"
            className="group inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-[#E6DED0] dark:bg-[#22201D] border border-[#C9BFAE] dark:border-[#3A352E] text-[#111111] dark:text-[#F3EEE3] text-xs font-semibold hover:border-[#D9541E] hover:text-[#D9541E] disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
          >
            <Volume2 className="w-3.5 h-3.5 text-[#D9541E]" />
            <span>Listen to Brief</span>
          </button>
        )}

        {isPlaying && (
          <span className="text-[11px] text-[#D9541E] font-semibold">
            Speaking…
          </span>
        )}
        {paused && (
          <span className="text-[11px] text-[#B4690E] dark:text-[#E09F3E] font-semibold">
            Paused
          </span>
        )}
      </div>
    </>
  );
}

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
      style={{ display: 'inline-flex', alignItems: 'flex-end', gap: '2px', height: '12px' }}
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
