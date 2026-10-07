import React from 'react';
import { PredictionResult, NavTab } from '../types';

interface ExplainableAiViewProps {
  prediction: PredictionResult | null;
  onNavigateTab: (tab: NavTab) => void;
}

const EmptyState: React.FC<{ onNavigateTab: (tab: NavTab) => void }> = ({ onNavigateTab }) => (
  <div className="card-container text-center py-16">
    <span className="material-symbols-outlined text-[48px] text-on-surface-variant mb-4 block">psychology</span>
    <h2 className="font-headline-md text-headline-md text-on-surface mb-2">No Prediction Yet</h2>
    <p className="font-body-sm text-body-sm text-on-surface-variant mb-6 max-w-md mx-auto">
      Run a prediction first — the SHAP explanation is generated from the actual model output for your specific inputs.
    </p>
    <button
      onClick={() => onNavigateTab('prediction')}
      className="px-8 py-3 bg-primary text-on-primary font-label-caps text-label-caps uppercase tracking-wider hover:brightness-110"
    >
      Go to Prediction
    </button>
  </div>
);

// Horizontal bar visualizing SHAP magnitude & direction. Width is scaled
// relative to the largest |SHAP| value among the factors shown, not a fixed
// arbitrary percentage.
const ShapBar: React.FC<{ label: string; value: number; maxAbs: number; positive: boolean }> = ({
  label, value, maxAbs, positive,
}) => {
  const widthPct = maxAbs > 0 ? Math.max(6, (Math.abs(value) / maxAbs) * 100) : 6;
  return (
    <div>
      <div className="flex justify-between font-data-mono text-data-mono mb-1">
        <span>{label}</span>
        <span className={positive ? 'text-primary dark:text-primary-fixed font-bold' : 'text-error font-bold'}>
          {positive ? '+' : ''}{value.toFixed(4)}
        </span>
      </div>
      <div className={`w-full bg-surface-container h-[12px] flex ${positive ? '' : 'justify-end'}`}>
        <div
          className={`h-[12px] ${positive ? 'bg-primary dark:bg-primary-container' : 'bg-error'}`}
          style={{ width: `${widthPct}%` }}
        />
      </div>
    </div>
  );
};

export const ExplainableAiView: React.FC<ExplainableAiViewProps> = ({ prediction, onNavigateTab }) => {
  if (!prediction) return <EmptyState onNavigateTab={onNavigateTab} />;

  const allAbs = [
    ...prediction.positive_factors.map((f) => Math.abs(f.shap_value)),
    ...prediction.negative_factors.map((f) => Math.abs(f.shap_value)),
  ];
  const maxAbs = allAbs.length ? Math.max(...allAbs) : 0;

  return (
    <div className="space-y-stack-loose">
      <div className="section-header">
        <h2 className="font-headline-md text-headline-md text-primary dark:text-primary-fixed mb-1">
          Explainable AI — Why this prediction?
        </h2>
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          SHAP (SHapley Additive exPlanations) values computed directly against the trained CatBoost model for this
          specific input — not a generic feature-importance ranking.
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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter md:gap-stack-loose">
        <div className="card-container">
          <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">
            Feature Contribution — Positive
          </h3>
          <div className="space-y-4">
            {prediction.positive_factors.map((f, idx) => (
              <ShapBar key={idx} label={f.label} value={f.shap_value} maxAbs={maxAbs} positive />
            ))}
          </div>
        </div>

        <div className="card-container border-l-[3px] border-l-error">
          <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">
            Feature Contribution — Negative
          </h3>
          <div className="space-y-4">
            {prediction.negative_factors.map((f, idx) => (
              <div key={idx}>
                <ShapBar label={f.label} value={f.shap_value} maxAbs={maxAbs} positive={false} />
                {f.context && (
                  <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">{f.context}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card-container bg-surface-container-low">
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          <strong className="text-on-surface">How to read this:</strong> a positive contribution pushes the predicted
          yield up relative to the model's average prediction; a negative contribution pulls it down. Encoded
          feature names (e.g. <code>Crop_Encoded</code>) are translated into plain agricultural language above —
          the raw category is shown in parentheses where relevant.
        </p>
      </div>
    </div>
  );
};
