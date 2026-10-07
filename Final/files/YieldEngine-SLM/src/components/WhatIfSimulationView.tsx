import React, { useState } from 'react';
import { FarmInput, PredictionResult, WhatIfResult } from '../types';
import { api } from '../services/api';

interface WhatIfSimulationViewProps {
  farmInput: FarmInput;
  basePrediction: PredictionResult | null;
}

export const WhatIfSimulationView: React.FC<WhatIfSimulationViewProps> = ({ farmInput, basePrediction }) => {
  const [result, setResult] = useState<WhatIfResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await api.whatIf(farmInput);
      setResult(r);
      setExpanded(false);
    } catch (e: any) {
      setError(e.message || 'What-if simulation failed');
    } finally {
      setLoading(false);
    }
  };

  if (!basePrediction) {
    return (
      <div className="card-container text-center py-16">
        <span className="material-symbols-outlined text-[48px] text-on-surface-variant mb-4 block">science</span>
        <h2 className="font-headline-md text-headline-md text-on-surface mb-2">No Prediction Yet</h2>
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          Run a prediction first, then come back here to simulate improvements.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-stack-loose">
      <div className="section-header">
        <h2 className="font-headline-md text-headline-md text-primary dark:text-primary-fixed mb-1">
          What-If Yield Simulation
        </h2>
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          This is a model-based simulation, not a guaranteed real-world outcome. The system nudges only the
          negatively-contributing, realistically-adjustable inputs toward values seen in your training data's
          top-yielding records, then re-runs the actual trained CatBoost model — nothing here is a hardcoded
          percentage.
        </p>
      </div>

      {error && (
        <div className="card-container border-l-4 border-l-error bg-error/5">
          <p className="font-body-sm text-body-sm text-error">{error}</p>
        </div>
      )}

      {!result && (
        <div className="card-container text-center py-12">
          <button
            onClick={runSimulation}
            disabled={loading}
            className="px-8 py-3 bg-primary text-on-primary font-label-caps text-label-caps uppercase tracking-wider hover:brightness-110 disabled:opacity-50"
          >
            {loading ? 'Simulating…' : 'Explore Improvements'}
          </button>
        </div>
      )}

      {result && (
        <>
          <div className="card-container bg-surface-container-high">
            <div className="flex flex-col sm:flex-row items-center justify-around gap-6 py-4">
              <div className="text-center">
                <div className="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">
                  Current Yield
                </div>
                <div className="font-display-lg text-display-lg text-on-surface">
                  {result.current_yield.toFixed(2)} <span className="font-headline-md text-headline-md">t/ha</span>
                </div>
              </div>

              <span className="material-symbols-outlined text-[32px] text-outline rotate-90 sm:rotate-0">arrow_forward</span>

              <div className="text-center">
                <div className="font-label-caps text-label-caps text-primary dark:text-primary-fixed mb-1 uppercase">
                  After Recommended Improvements
                </div>
                <div className="font-display-lg text-display-lg text-primary dark:text-primary-fixed font-bold">
                  {result.improved_yield.toFixed(2)} <span className="font-headline-md text-headline-md">t/ha</span>
                </div>
              </div>
            </div>

            <div className="bg-surface-container-lowest border border-outline-variant p-4 mt-4 text-center">
              <div className="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">
                Estimated Improvement
              </div>
              <div className="font-headline-md text-headline-md text-primary dark:text-primary-fixed font-bold">
                {result.percentage_improvement >= 0 ? '+' : ''}{result.percentage_improvement.toFixed(1)}%
              </div>
            </div>
          </div>

          <div className="card-container">
            <button
              onClick={() => setExpanded((v) => !v)}
              className="w-full flex justify-between items-center font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant"
            >
              Which inputs changed
              <span className="material-symbols-outlined text-[18px]">{expanded ? 'expand_less' : 'expand_more'}</span>
            </button>

            {expanded && (
              <div className="mt-4 space-y-3">
                {result.changed_parameters.length === 0 && (
                  <p className="font-body-sm text-body-sm text-on-surface-variant">
                    No inputs could be realistically adjusted to improve this prediction — the current values are
                    already close to what the model considers favourable, or the limiting factors (e.g. crop
                    selection, sowing season) require a qualitative change rather than a numeric one. See the
                    Decision Support page for generic guidance on those.
                  </p>
                )}
                {result.changed_parameters.map((c, idx) => (
                  <div key={idx} className="flex items-center justify-between font-data-mono text-data-mono border-b border-outline-variant/40 pb-2">
                    <span>{c.label}</span>
                    <span>
                      {c.before.toFixed(2)} <span className="text-on-surface-variant mx-1">→</span>{' '}
                      <span className="text-primary dark:text-primary-fixed font-bold">{c.after.toFixed(2)}</span>
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end">
            <button
              onClick={runSimulation}
              disabled={loading}
              className="px-6 py-2 border border-outline-variant font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant hover:bg-surface-container-high disabled:opacity-50"
            >
              {loading ? 'Re-simulating…' : 'Re-run Simulation'}
            </button>
          </div>
        </>
      )}
    </div>
  );
};
