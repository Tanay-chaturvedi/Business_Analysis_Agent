import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * useTextToSpeech
 *
 * Manages browser Web Speech API state cleanly.
 * Returns: { speaking, paused, available, speak, pause, resume, stop }
 */
export function useTextToSpeech() {
  const [speaking, setSpeaking] = useState(false);
  const [paused, setPaused] = useState(false);
  const [available, setAvailable] = useState(false);
  const [voices, setVoices] = useState([]);
  const utteranceRef = useRef(null);

  // Check availability and load voices (voices may load asynchronously)
  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      setAvailable(false);
      return;
    }
    setAvailable(true);

    const loadVoices = () => {
      const v = window.speechSynthesis.getVoices();
      if (v.length > 0) setVoices(v);
    };

    // Voices may already be available (Chrome/Edge)
    loadVoices();

    // Or they load asynchronously (Firefox)
    window.speechSynthesis.addEventListener('voiceschanged', loadVoices);
    return () => {
      window.speechSynthesis.removeEventListener('voiceschanged', loadVoices);
    };
  }, []);

  /**
   * Pick the best available voice:
   * 1. en-IN  (Indian English)
   * 2. en-US
   * 3. en-GB
   * 4. any English
   * 5. browser default (null)
   */
  const selectVoice = useCallback(
    (voiceList) => {
      const list = voiceList.length > 0 ? voiceList : window.speechSynthesis.getVoices();

      const enIN = list.find((v) => v.lang === 'en-IN');
      if (enIN) return enIN;

      const enUS = list.find((v) => v.lang === 'en-US');
      if (enUS) return enUS;

      const enGB = list.find((v) => v.lang === 'en-GB');
      if (enGB) return enGB;

      const anyEn = list.find((v) => v.lang.startsWith('en'));
      if (anyEn) return anyEn;

      return null; // let browser pick
    },
    []
  );

  const stop = useCallback(() => {
    window.speechSynthesis.cancel();
    utteranceRef.current = null;
    setSpeaking(false);
    setPaused(false);
  }, []);

  const speak = useCallback(
    (text) => {
      if (!available || !text) return;

      // Cancel any currently playing speech first
      window.speechSynthesis.cancel();
      utteranceRef.current = null;

      const utterance = new window.SpeechSynthesisUtterance(text);
      utterance.lang = 'en-IN';
      utterance.rate = 0.95;
      utterance.pitch = 1;

      const chosen = selectVoice(voices);
      if (chosen) utterance.voice = chosen;

      utterance.onstart = () => {
        setSpeaking(true);
        setPaused(false);
      };

      utterance.onend = () => {
        setSpeaking(false);
        setPaused(false);
        utteranceRef.current = null;
      };

      utterance.onerror = (e) => {
        // 'interrupted' is a normal cancellation — not a real error
        if (e.error !== 'interrupted') {
          console.warn('SpeechSynthesis error:', e.error);
        }
        setSpeaking(false);
        setPaused(false);
        utteranceRef.current = null;
      };

      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    },
    [available, voices, selectVoice]
  );

  const pause = useCallback(() => {
    if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
      window.speechSynthesis.pause();
      setPaused(true);
    }
  }, []);

  const resume = useCallback(() => {
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      setPaused(false);
    }
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);

  return { speaking, paused, available, speak, pause, resume, stop };
}
