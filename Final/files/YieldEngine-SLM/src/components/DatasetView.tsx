import React, { useEffect, useState } from 'react';
import { DatasetInfo, ModelMetrics } from '../types';
import { api } from '../services/api';

const StatCard: React.FC<{ label: string; value: string; icon: string; accent?: boolean }> = ({
  label, value, icon, accent,
}) => (
  <div className={`card-container flex flex-col ${accent ? 'border-primary border-l-4' : ''}`}>
    <div className="flex items-center justify-between mb-2">
      <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">{label}</span>
      <span className="material-symbols-outlined text-[18px] text-primary dark:text-primary-fixed">{icon}</span>
    </div>
    <span className="font-headline-md text-headline-md text-on-surface">{value}</span>
  </div>
);

const PIPELINE_STEPS = [
  'Raw Datasets (Crop, Soil, Temperature, Fertilizer, Pesticide)',
  'Dataset Cleaning (name standardization, duplicate/anomaly checks)',
  'Missing Value Handling',
  'Categorical Encoding (Crop / Season / State / District / Soil Type)',
  'Feature Engineering (Soil Fertility, Weather, Climate, Intensity indices)',
  'Merged Dataset',
  'Model-Ready Dataset',
  'CatBoost Model Training',
  'SHAP Explainability',
  'Decision Support',
];

export const DatasetView: React.FC = () => {
  const [info, setInfo] = useState<DatasetInfo | null>(null);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getDatasetInfo(), api.getModelMetrics()])
      .then(([d, m]) => { setInfo(d); setMetrics(m); })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-stack-loose">
      <div className="section-header">
        <h2 className="font-headline-md text-headline-md text-primary dark:text-primary-fixed mb-1">
          Dataset Overview & Model Performance
        </h2>
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          Real statistics from the actual training data and trained CatBoost model — nothing on this page is a
          placeholder figure.
        </p>
      </div>

      {error && (
        <div className="card-container border-l-4 border-l-error bg-error/5">
          <p className="font-body-sm text-body-sm text-error">Could not load dataset info: {error}</p>
        </div>
      )}

      <div>
        <h3 className="font-headline-md text-headline-md text-primary dark:text-primary-fixed mb-4">
          Data Inventory
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-gutter">
          <StatCard label="Total Records" value={info ? info.total_rows_model_ready.toLocaleString() : '—'} icon="table_rows" accent />
          <StatCard label="Features" value={info ? String(info.total_features) : '—'} icon="view_column" />
          <StatCard label="Missing Values (After)" value={info ? String(info.missing_values_after) : '—'} icon="check_circle" />
          <StatCard label="Duplicate Rows" value={info ? String(info.duplicate_rows) : '—'} icon="content_copy" />
        </div>
      </div>

      <div className="card-container">
        <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">
          Data Processing Pipeline
        </h3>
        <div className="flex flex-wrap items-center gap-2">
          {PIPELINE_STEPS.map((step, idx) => (
            <React.Fragment key={step}>
              <div className="bg-surface-container-high border border-outline-variant px-3 py-2 font-data-mono text-[11px] text-on-surface">
                {step}
              </div>
              {idx < PIPELINE_STEPS.length - 1 && (
                <span className="material-symbols-outlined text-[16px] text-on-surface-variant">arrow_forward</span>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gutter md:gap-stack-loose">
        <div className="card-container">
          <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">
            Feature List ({info?.feature_list.length ?? 0})
          </h3>
          <div className="flex flex-wrap gap-2">
            {(info?.feature_list || []).map((f) => (
              <span key={f} className="bg-surface-container-lowest border border-outline-variant px-2 py-1 font-data-mono text-[11px] text-on-surface">
                {f}
              </span>
            ))}
          </div>
        </div>

        <div className="card-container">
          <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">
            Model Evaluation Metrics
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse font-data-mono text-xs">
              <thead>
                <tr className="border-b border-outline-variant text-on-surface-variant uppercase tracking-wider">
                  <th className="p-2">Model</th>
                  <th className="p-2">MAE</th>
                  <th className="p-2">RMSE</th>
                  <th className="p-2">R²</th>
                </tr>
              </thead>
              <tbody>
                {metrics && (
                  <tr className="border-b border-outline-variant/40">
                    <td className="p-2 font-bold text-primary dark:text-primary-fixed">{metrics.model_name}</td>
                    <td className="p-2">{metrics.mae.toFixed(2)}</td>
                    <td className="p-2">{metrics.rmse.toFixed(2)}</td>
                    <td className="p-2">{metrics.r2.toFixed(3)}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant mt-4">
            Evaluated on a held-out {metrics ? metrics.test_set_size.toLocaleString() : '—'}-row test split
            (trained on {metrics ? metrics.train_set_size.toLocaleString() : '—'} rows). This project uses a single
            production model (CatBoost) rather than a multi-model comparison.
          </p>
        </div>
      </div>
    </div>
  );
};
