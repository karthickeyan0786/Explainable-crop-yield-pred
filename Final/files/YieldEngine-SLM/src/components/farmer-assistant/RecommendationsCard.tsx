import React from 'react';
import { Recommendation } from '../../types';

interface RecommendationsCardProps {
  recommendations: Recommendation[];
}

/**
 * "Recommendations Card" per Requirement 5 -- "What should I do?" -- shows
 * the deterministic, rule-based recommendation actions (the same ones fed
 * to the SLM as grounding facts, so this card and the Explanation Card
 * never contradict each other).
 */
export const RecommendationsCard: React.FC<RecommendationsCardProps> = ({ recommendations }) => (
  <div className="card-container">
    <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-3">
      What should I do?
    </h3>
    {recommendations.length === 0 && (
      <p className="font-body-sm text-body-sm text-on-surface-variant">
        Run a prediction to see recommendations here.
      </p>
    )}
    <div className="space-y-2">
      {recommendations.map((rec, idx) => (
        <div key={idx} className="flex items-start font-data-mono text-data-mono">
          <span className="text-primary dark:text-primary-fixed mr-2 mt-0.5">✔</span>
          <span>{rec.action}</span>
        </div>
      ))}
    </div>
  </div>
);
