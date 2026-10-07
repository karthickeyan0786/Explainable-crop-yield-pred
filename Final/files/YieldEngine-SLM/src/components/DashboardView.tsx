import React, { useEffect, useState } from 'react';
import { FarmInput, PredictionResult, NavTab, ModelMetrics, WhatIfResult, SlmExplanation, LanguageCode } from '../types';
import { api } from '../services/api';
import { PredictionCard } from './farmer-assistant/PredictionCard';
import { ExplanationCard } from './farmer-assistant/ExplanationCard';
import { RecommendationsCard } from './farmer-assistant/RecommendationsCard';
import { VoiceAssistantCard } from './farmer-assistant/VoiceAssistantCard';

interface DashboardViewProps {
  farmInput: FarmInput;
  prediction: PredictionResult | null;
  onNavigateTab: (tab: NavTab) => void;
}

// Horizontal bar meter matching the reference: label + value on top row,
// a thin colored bar below sized relative to the largest |SHAP| value shown.
const FactorBar: React.FC<{ label: string; value: number; maxAbs: number; positive: boolean }> = ({
  label, value, maxAbs, positive,
}) => {
  const widthPct = maxAbs > 0 ? Math.max(6, (Math.abs(value) / maxAbs) * 100) : 6;
  return (
    <div>
      <div className="flex justify-between items-baseline font-data-mono text-data-mono mb-1">
        <span className="text-on-surface">{label}</span>
        <span className={positive ? 'text-primary dark:text-primary-fixed font-bold' : 'text-error font-bold'}>
          {positive ? '+' : ''}{value.toFixed(2)}
        </span>
      </div>
      <div className="shap-bar w-full">
        <div className={positive ? 'shap-bar-positive' : 'shap-bar-negative'} style={{ width: `${widthPct}%` }} />
      </div>
    </div>
  );
};

const FarmContextRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="mb-3 last:mb-0">
    <div className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-1">
      {label}
    </div>
    <div className="border border-outline-variant bg-surface-container-lowest px-3 py-2 font-data-mono text-data-mono text-on-surface">
      {value || '—'}
    </div>
  </div>
);

export const DashboardView: React.FC<DashboardViewProps> = ({ farmInput, prediction, onNavigateTab }) => {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [whatIf, setWhatIf] = useState<WhatIfResult | null>(null);
  const [whatIfLoading, setWhatIfLoading] = useState(false);
  const [assistantLang, setAssistantLang] = useState<LanguageCode>('en');
  const [explanation, setExplanation] = useState<SlmExplanation | null>(null);
  const [explanationLoading, setExplanationLoading] = useState(false);

  useEffect(() => {
    api.getModelMetrics().then(setMetrics).catch(() => {});
  }, []);

  useEffect(() => {
    if (!prediction) {
      setExplanation(null);
      return;
    }
    setExplanationLoading(true);
    api.getExplanation({ ...farmInput, lang: assistantLang })
      .then(setExplanation)
      .catch(() => setExplanation(null))
      .finally(() => setExplanationLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prediction, assistantLang]);

  useEffect(() => {
    if (!prediction) {
      setWhatIf(null);
      return;
    }
    setWhatIfLoading(true);
    api.whatIf(farmInput)
      .then(setWhatIf)
      .catch(() => setWhatIf(null))
      .finally(() => setWhatIfLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prediction]);

  if (!prediction) {
    return (
      <div className="space-y-stack-loose">
        <div className="card-container text-center py-16">
          <span className="material-symbols-outlined text-[48px] text-on-surface-variant mb-4 block">analytics</span>
          <h2 className="font-headline-md text-headline-md text-on-surface mb-2">No Prediction Yet</h2>
          <p className="font-body-sm text-body-sm text-on-surface-variant mb-6 max-w-md mx-auto">
            Run a prediction to see the AI's yield estimate, explainability breakdown, and decision support here.
          </p>
          <button
            onClick={() => onNavigateTab('prediction')}
            className="px-8 py-3 bg-primary text-on-primary font-label-caps text-label-caps uppercase tracking-wider hover:brightness-110"
          >
            Go to Prediction
          </button>
        </div>

        {metrics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-gutter">
            <div className="card-container">
              <div className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-2">Model</div>
              <div className="font-headline-md text-headline-md text-on-surface">{metrics.model_name}</div>
            </div>
            <div className="card-container">
              <div className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-2">R² Score</div>
              <div className="font-headline-md text-headline-md text-on-surface">{metrics.r2.toFixed(3)}</div>
            </div>
            <div className="card-container">
              <div className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-2">MAE</div>
              <div className="font-headline-md text-headline-md text-on-surface">{metrics.mae.toFixed(2)}</div>
            </div>
            <div className="card-container">
              <div className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-2">RMSE</div>
              <div className="font-headline-md text-headline-md text-on-surface">{metrics.rmse.toFixed(2)}</div>
            </div>
          </div>
        )}
      </div>
    );
  }

  const allAbs = [
    ...prediction.positive_factors.map((f) => Math.abs(f.shap_value)),
    ...prediction.negative_factors.map((f) => Math.abs(f.shap_value)),
  ];
  const maxAbs = allAbs.length ? Math.max(...allAbs) : 0;

  return (
    <div className="space-y-loose">
      {/* Top Hero Row: Predicted Yield + Farm Context */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter md:gap-stack-loose mb-stack-loose">
        <div className="card-container col-span-1 md:col-span-8 flex flex-col justify-center border-primary border-l-4">
          <h2 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-2">
            Predicted Yield
          </h2>
          <div className="flex items-baseline mb-1">
            <span className="font-display-lg text-display-lg text-primary dark:text-primary-fixed mr-2">
              {prediction.predicted_yield.toFixed(2)}
            </span>
            <span className="font-headline-md text-headline-md text-on-surface-variant">t/ha</span>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Current estimated crop productivity
          </p>
        </div>

        <div className="card-container col-span-1 md:col-span-4 bg-surface-container-low border-outline-variant">
          <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-3">
            Farm Context
          </h3>
          <FarmContextRow label="Crop Type" value={farmInput.crop} />
          <FarmContextRow label="Season" value={farmInput.season} />
        </div>
      </div>

      {/* Farmer Assistant Panel: Prediction / Explanation / Recommendations / Voice */}
      <div className="mb-stack-loose">
        <div className="section-header">
          <h2 className="font-headline-md text-headline-md text-primary dark:text-primary-fixed mb-1">
            Farmer Assistant
          </h2>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            A grounded, natural-language explanation of your prediction — choose a language and listen.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter md:gap-stack-loose">
          <PredictionCard predictedYield={prediction.predicted_yield} crop={farmInput.crop} season={farmInput.season} />
          <VoiceAssistantCard language={assistantLang} onLanguageChange={setAssistantLang} explanation={explanation} />
          <ExplanationCard explanation={explanation} loading={explanationLoading} />
          <RecommendationsCard recommendations={prediction.recommendations} />
        </div>
      </div>

      {/* Explainable AI Section */}
      <div className="mb-stack-loose">
        <div className="section-header">
          <h2 className="font-headline-md text-headline-md text-primary dark:text-primary-fixed mb-1">
            Explainable AI
          </h2>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Why did the system make this prediction?
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter md:gap-stack-loose">
          <div className="card-container">
            <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4 flex items-center">
              <span className="material-symbols-outlined text-[16px] mr-2 text-primary dark:text-primary-fixed">add_circle</span>
              Positive Driving Factors
            </h3>
            <div className="space-y-4">
              {prediction.positive_factors.map((item, idx) => (
                <FactorBar key={idx} label={item.label} value={item.shap_value} maxAbs={maxAbs} positive />
              ))}
            </div>
          </div>

          <div className="card-container border-l-[3px] border-l-error">
            <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4 flex items-center">
              <span className="material-symbols-outlined text-[16px] mr-2 text-error">remove_circle</span>
              Negative Limiting Factors
            </h3>
            <div className="space-y-4">
              {prediction.negative_factors.map((item, idx) => (
                <div key={idx}>
                  <FactorBar label={item.label} value={item.shap_value} maxAbs={maxAbs} positive={false} />
                  {item.context && (
                    <p className="font-body-sm text-[11px] text-on-surface-variant mt-1">{item.context}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Decision Support & What-If Simulation Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter md:gap-stack-loose">
        <div className="lg:col-span-8 bg-[var(--bg-decision)] border border-outline-variant p-[20px]">
          <h2 className="font-headline-md text-headline-md text-primary dark:text-primary-fixed mb-4 border-b border-outline-variant/30 pb-2">
            Decision Support
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {prediction.recommendations.map((rec, idx) => (
              <div key={idx} className="bg-surface-container-lowest border border-outline-variant p-4">
                <div className="font-label-caps text-label-caps text-error mb-2 uppercase tracking-wider">Detected Issue</div>
                <div className="font-data-mono text-data-mono text-on-surface mb-3 pb-2 border-b border-outline-variant/50">
                  {rec.issue}
                </div>
                <div className="font-label-caps text-label-caps text-primary dark:text-primary-fixed mb-1 uppercase tracking-wider flex items-center">
                  <span className="material-symbols-outlined text-[14px] mr-1">arrow_right_alt</span> Recommended Action
                </div>
                <div className="font-body-sm text-body-sm text-on-surface-variant">{rec.action}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-4 card-container bg-surface-container-high border-primary/20 flex flex-col">
          <h2 className="font-headline-md text-headline-md text-primary dark:text-primary-fixed mb-1">
            What-If Simulation
          </h2>
          <p className="font-body-sm text-[11px] text-on-surface-variant mb-4 pb-3 border-b border-outline-variant/50">
            Potential yield after applying recommendations
          </p>

          {whatIfLoading && (
            <div className="flex-1 flex items-center justify-center py-6">
              <span className="font-data-mono text-data-mono text-on-surface-variant">Simulating…</span>
            </div>
          )}

          {!whatIfLoading && whatIf && (
            <>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-1">Before</div>
                  <div className="font-data-mono text-data-mono text-on-surface">{whatIf.current_yield.toFixed(2)} t/ha</div>
                </div>
                <span className="material-symbols-outlined text-on-surface-variant">arrow_forward</span>
                <div className="text-right">
                  <div className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-1">After</div>
                  <div className="font-data-mono text-data-mono text-primary dark:text-primary-fixed font-bold">
                    {whatIf.improved_yield.toFixed(2)} t/ha
                  </div>
                </div>
              </div>

              <div className="bg-surface-container-lowest border border-outline-variant p-3 mb-4 text-center">
                <div className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-1">
                  Estimated Improvement
                </div>
                <div className="font-headline-md text-headline-md text-primary dark:text-primary-fixed font-bold">
                  {whatIf.percentage_improvement >= 0 ? '+' : ''}{whatIf.percentage_improvement.toFixed(1)}%
                </div>
              </div>
            </>
          )}

          <button
            onClick={() => onNavigateTab('what-if')}
            className="w-full mt-auto bg-primary text-on-primary font-label-caps text-label-caps uppercase tracking-wider py-3 border border-transparent hover:brightness-110 transition-all rounded-none flex justify-center items-center cursor-pointer"
          >
            Explore What-If Scenario <span className="material-symbols-outlined ml-2 text-[16px]">science</span>
          </button>
        </div>
      </div>
    </div>
  );
};
