import React, { useState, useRef } from 'react';
import { api } from '../services/api';

interface SpeakButtonProps {
  text: string;
  lang: string;              // 'en' | 'ta' | 'hi'
  languageTag: string;       // BCP-47 tag for Web Speech API, e.g. "ta-IN"
  label?: string;
}

/**
 * Voice Assistant button ("🔊 Listen"). Tries the backend TTS endpoint
 * first (gTTS by default -- see voice_service.py); if that's unavailable
 * for any reason (no internet, provider not configured, unsupported
 * language), falls back automatically to the browser's built-in
 * SpeechSynthesis API, which is real, working, and needs no backend at all.
 *
 * This two-tier design means the Listen button always does SOMETHING
 * useful for the farmer, even if the backend TTS providers aren't set up.
 */
export const SpeakButton: React.FC<SpeakButtonProps> = ({ text, lang, languageTag, label }) => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const speakWithBrowser = () => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    const synth = window.speechSynthesis;
    synth.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = languageTag;
    const voices = synth.getVoices();
    const matchingVoice = voices.find((v) => v.lang === languageTag)
      || voices.find((v) => v.lang.startsWith(languageTag.split('-')[0]));
    if (matchingVoice) utterance.voice = matchingVoice;
    utterance.rate = 0.95;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    synth.speak(utterance);
    setIsSpeaking(true);
  };

  const handleClick = async () => {
    if (isSpeaking) {
      window.speechSynthesis?.cancel();
      audioRef.current?.pause();
      setIsSpeaking(false);
      return;
    }

    setIsLoading(true);
    try {
      const blob = await api.getVoiceAudio(text, lang, 'gtts');
      if (blob) {
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => setIsSpeaking(false);
        audio.onerror = () => { setIsSpeaking(false); speakWithBrowser(); };
        await audio.play();
        setIsSpeaking(true);
      } else {
        // Backend TTS unavailable -- fall back to browser speech synthesis
        speakWithBrowser();
      }
    } catch {
      speakWithBrowser();
    } finally {
      setIsLoading(false);
    }
  };

  if (typeof window !== 'undefined' && !('speechSynthesis' in window) && !('fetch' in window)) {
    return null;
  }

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      type="button"
      className="flex items-center gap-2 px-4 py-2 border border-outline-variant font-label-caps text-label-caps uppercase tracking-wider text-on-surface hover:bg-surface-container-high transition-colors disabled:opacity-50"
    >
      <span className="material-symbols-outlined text-[18px]">
        {isLoading ? 'hourglass_empty' : isSpeaking ? 'stop_circle' : 'volume_up'}
      </span>
      {label || (isSpeaking ? 'Stop' : '🔊 Listen')}
    </button>
  );
};
