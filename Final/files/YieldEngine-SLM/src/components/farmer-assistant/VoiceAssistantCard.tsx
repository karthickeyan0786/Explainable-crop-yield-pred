import React from 'react';
import { LanguageCode, SlmExplanation } from '../../types';
import { LanguageSelector } from '../LanguageSelector';
import { SpeakButton } from '../SpeakButton';

const TTS_LANGUAGE_TAGS: Record<LanguageCode, string> = { en: 'en-IN', ta: 'ta-IN', hi: 'hi-IN' };

interface VoiceAssistantCardProps {
  language: LanguageCode;
  onLanguageChange: (lang: LanguageCode) => void;
  explanation: SlmExplanation | null;
}

/**
 * "Voice Assistant Card" per Requirement 5 -- language selector
 * (English / தமிழ் / हिन्दी) + the 🔊 Listen button, together in one card.
 * This is the primary accessibility feature for farmers who cannot read:
 * pick a language, tap Listen, hear the explanation spoken aloud.
 */
export const VoiceAssistantCard: React.FC<VoiceAssistantCardProps> = ({
  language, onLanguageChange, explanation,
}) => (
  <div className="card-container bg-surface-container-low">
    <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-3">
      Voice Assistant
    </h3>
    <div className="flex items-center justify-between gap-3 flex-wrap">
      <LanguageSelector value={language} onChange={onLanguageChange} />
      {explanation && (
        <SpeakButton
          text={explanation.explanation}
          lang={language}
          languageTag={TTS_LANGUAGE_TAGS[language]}
        />
      )}
    </div>
    <p className="font-body-sm text-[11px] text-on-surface-variant mt-3">
      Choose a language, then tap Listen to hear the explanation read aloud —
      useful even if you cannot read.
    </p>
  </div>
);
