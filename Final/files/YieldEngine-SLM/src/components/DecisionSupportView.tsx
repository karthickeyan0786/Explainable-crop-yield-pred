import React from 'react';
import { PredictionResult, NavTab } from '../types';

interface DecisionSupportViewProps {
  prediction: PredictionResult | null;
  onNavigateTab: (tab: NavTab) => void;
}

export const DecisionSupportView: React.FC<DecisionSupportViewProps> = ({ prediction, onNavigateTab }) => {
  if (!prediction) {
    return (
      <div className="card-container text-center py-16">
        <span className="material-symbols-outlined text-[48px] text-on-surface-variant mb-4 block">lightbulb</span>
        <h2 className="font-headline-md text-headline-md text-on-surface mb-2">No Prediction Yet</h2>
        <p className="font-body-sm text-body-sm text-on-surface-variant mb-6 max-w-md mx-auto">
          Recommendations are generated from the SHAP-identified negative factors for your specific prediction.
        </p>
        <button
          onClick={() => onNavigateTab('prediction')}
          className="px-8 py-3 bg-primary text-on-primary font-label-caps text-label-caps uppercase tracking-wider hover:brightness-110"
        >
          Go to Prediction
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-stack-loose">
      <div className="section-header">
        <h2 className="font-headline-md text-headline-md text-primary dark:text-primary-fixed mb-1">
          AI Crop Yield Decision Support
        </h2>
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          Actionable, model-driven recommendations targeting the factors currently reducing your predicted yield.
        </p>
      </div>

      <div className="card-container border-primary border-l-4">
        <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-2">
          Predicted Yield
        </h3>
        <span className="font-display-lg text-display-lg text-primary dark:text-primary-fixed">
          {prediction.predicted_yield.toFixed(2)} t/ha
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter">
        <div className="card-container">
          <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">
            Top Positive Factors
          </h3>
          <div className="space-y-2">
            {prediction.positive_factors.map((f, idx) => (
              <div key={idx} className="flex items-center font-data-mono text-data-mono">
                <span className="text-primary mr-2">✔</span>{f.label}
              </div>
            ))}
          </div>
        </div>

        <div className="card-container border-l-[3px] border-l-error">
          <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">
            Top Factors Reducing Yield
          </h3>
          <div className="space-y-2">
            {prediction.negative_factors.map((f, idx) => (
              <div key={idx} className="flex items-center font-data-mono text-data-mono">
                <span className="text-error mr-2">❌</span>{f.label}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div>
        <h3 className="font-headline-md text-headline-md text-primary dark:text-primary-fixed mb-4">
          Recommendations
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {prediction.recommendations.map((rec, idx) => (
            <div key={idx} className="card-container">
              <div className="font-label-caps text-label-caps text-error mb-1 uppercase tracking-wider">Problem</div>
              <div className="font-data-mono text-data-mono text-on-surface mb-3 pb-3 border-b border-outline-variant/50">
                {rec.issue}
              </div>
              <div className="font-label-caps text-label-caps text-primary dark:text-primary-fixed mb-1 uppercase tracking-wider">
                Recommended Action
              </div>
              <div className="font-body-sm text-body-sm text-on-surface mb-3">{rec.action}</div>
              <div className="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">
                Reason
              </div>
              <div className="font-body-sm text-body-sm text-on-surface-variant">{rec.reason}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
