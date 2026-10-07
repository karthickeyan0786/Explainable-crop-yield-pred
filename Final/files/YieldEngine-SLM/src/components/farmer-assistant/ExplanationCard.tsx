import React from 'react';
import { SlmExplanation } from '../../types';

interface ExplanationCardProps {
  explanation: SlmExplanation | null;
  loading: boolean;
}

/**
 * "Explanation Card" per Requirement 5 -- "Why is my yield low?" -- shows
 * the grounded SLM-generated narrative (or the tested offline template
 * fallback, transparently labeled) in the farmer's selected language.
 */
export const ExplanationCard: React.FC<ExplanationCardProps> = ({ explanation, loading }) => (
  <div className="card-container">
    <div className="flex items-center justify-between mb-3">
      <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
        Why is my yield low?
      </h3>
      {explanation && (
        <span className="font-body-sm text-[10px] text-on-surface-variant">
          {explanation.language}
          {explanation.source === 'template_fallback' ? ' · offline' : ' · SLM'}
        </span>
      )}
    </div>
    {loading && (
      <p className="font-body-sm text-body-sm text-on-surface-variant">Generating explanation…</p>
    )}
    {!loading && explanation && (
      <p className="font-body-sm text-body-sm text-on-surface leading-relaxed">
        {explanation.explanation}
      </p>
    )}
    {!loading && !explanation && (
      <p className="font-body-sm text-body-sm text-on-surface-variant">
        Run a prediction to see an explanation here.
      </p>
    )}
  </div>
);
