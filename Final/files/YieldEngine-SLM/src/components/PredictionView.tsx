import React, { useEffect, useState } from 'react';
import { FarmInput, PredictionResult, NavTab, OptionsResponse } from '../types';
import { api } from '../services/api';

interface PredictionViewProps {
  farmInput: FarmInput;
  onUpdateFarmInput: (input: FarmInput) => void;
  onUpdatePrediction: (result: PredictionResult) => void;
  onNavigateTab: (tab: NavTab) => void;
}

// Reusable numeric field
const NumberField: React.FC<{
  label: string; unit?: string; value: number;
  onChange: (v: number) => void; step?: number; min?: number; max?: number;
}> = ({ label, unit, value, onChange, step = 1, min, max }) => (
  <label className="block">
    <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-1 block">
      {label} {unit && <span className="normal-case text-[10px]">({unit})</span>}
    </span>
    <input
      type="number"
      className="w-full bg-surface-container-lowest border border-outline-variant px-3 py-2 font-data-mono text-data-mono text-on-surface focus:outline-none focus:border-primary"
      value={Number.isFinite(value) ? value : ''}
      step={step}
      min={min}
      max={max}
      onChange={(e) => onChange(parseFloat(e.target.value))}
    />
  </label>
);

const SelectField: React.FC<{
  label: string; value: string; options: string[]; onChange: (v: string) => void; disabled?: boolean;
}> = ({ label, value, options, onChange, disabled }) => (
  <label className="block">
    <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-1 block">
      {label}
    </span>
    <select
      className="w-full bg-surface-container-lowest border border-outline-variant px-3 py-2 font-data-mono text-data-mono text-on-surface focus:outline-none focus:border-primary disabled:opacity-50"
      value={value}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="" disabled>Select…</option>
      {options.map((o) => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  </label>
);

const SectionCard: React.FC<{ icon: string; title: string; children: React.ReactNode }> = ({ icon, title, children }) => (
  <div className="card-container">
    <h3 className="section-header font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant flex items-center">
      <span className="material-symbols-outlined text-[18px] mr-2 text-primary dark:text-primary-fixed">{icon}</span>
      {title}
    </h3>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">{children}</div>
  </div>
);

export const PredictionView: React.FC<PredictionViewProps> = ({
  farmInput, onUpdateFarmInput, onUpdatePrediction, onNavigateTab,
}) => {
  const [options, setOptions] = useState<OptionsResponse | null>(null);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getOptions()
      .then(setOptions)
      .catch((e) => setError(`Could not load form options from backend: ${e.message}`))
      .finally(() => setLoadingOptions(false));
  }, []);

  const set = <K extends keyof FarmInput>(key: K, value: FarmInput[K]) => {
    onUpdateFarmInput({ ...farmInput, [key]: value });
  };

  const districtOptions = options && farmInput.state ? (options.state_district_map[farmInput.state] || []) : [];

  // Live, read-only preview of the derived features (computed the same way
  // the backend computes them) -- shown so the form isn't hiding what feeds
  // the model, without letting the farmer enter internally-inconsistent values.
  const soilFertilityPreview = ((farmInput.nitrogen || 0) + (farmInput.potassium || 0)) / 2;
  const inputIntensityPreview = (farmInput.fertilizer_consumption || 0) + (farmInput.pesticide_consumption || 0);

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const result = await api.predict(farmInput);
      onUpdatePrediction(result);
      onNavigateTab('dashboard');
    } catch (e: any) {
      setError(e.message || 'Prediction failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClear = () => {
    onUpdateFarmInput({ ...farmInput, state: '', district: '', crop: '', season: '' });
  };

  const canSubmit =
    farmInput.state && farmInput.district && farmInput.crop && farmInput.season &&
    farmInput.area > 0 && !submitting;

  return (
    <div className="space-y-stack-loose">
      <div className="section-header">
        <h2 className="font-headline-md text-headline-md text-primary dark:text-primary-fixed mb-1">
          New Yield Prediction
        </h2>
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          Enter agricultural parameters to generate an AI-driven yield forecast and site-specific recommendations. Inputs are sent to the trained CatBoost model via the backend API.
        </p>
      </div>

      {error && (
        <div className="card-container border-l-4 border-l-error bg-error/5">
          <p className="font-body-sm text-body-sm text-error">{error}</p>
        </div>
      )}

      <SectionCard icon="location_on" title="Location & Crop Identity">
        <SelectField
          label="State" value={farmInput.state} options={options?.states || []}
          onChange={(v) => onUpdateFarmInput({ ...farmInput, state: v, district: '' })}
        />
        <SelectField
          label="District" value={farmInput.district} options={districtOptions}
          onChange={(v) => set('district', v)} disabled={!farmInput.state}
        />
        <SelectField label="Crop" value={farmInput.crop} options={options?.crops || []} onChange={(v) => set('crop', v)} />
        <SelectField label="Season" value={farmInput.season} options={options?.seasons || []} onChange={(v) => set('season', v)} />
        <NumberField label="Crop Year" value={farmInput.crop_year} onChange={(v) => set('crop_year', v)} step={1} min={1997} max={2035} />
        <NumberField label="Area" unit="hectares" value={farmInput.area} onChange={(v) => set('area', v)} step={0.1} min={0.01} />
      </SectionCard>

      <SectionCard icon="grass" title="Soil Characteristics">
        <SelectField label="Soil Type" value={farmInput.soil_type} options={options?.soil_types || []} onChange={(v) => set('soil_type', v)} />
        <NumberField label="pH Level" value={farmInput.ph_level} onChange={(v) => set('ph_level', v)} step={0.1} min={0} max={14} />
        <NumberField label="Organic Matter" unit="%" value={farmInput.organic_matter} onChange={(v) => set('organic_matter', v)} step={0.1} min={0} />
        <NumberField label="Nitrogen" unit="kg/ha" value={farmInput.nitrogen} onChange={(v) => set('nitrogen', v)} step={0.1} min={0} />
        <NumberField label="Potassium" unit="kg/ha" value={farmInput.potassium} onChange={(v) => set('potassium', v)} step={0.1} min={0} />
        <label className="block">
          <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-1 block">
            Soil Fertility Index <span className="normal-case text-[10px]">(auto-computed)</span>
          </span>
          <div className="w-full bg-surface-container border border-outline-variant px-3 py-2 font-data-mono text-data-mono text-on-surface-variant">
            {soilFertilityPreview.toFixed(2)}
          </div>
        </label>
      </SectionCard>

      <SectionCard icon="eco" title="Agricultural Inputs">
        <NumberField label="Fertilizer Applied" unit="kg/ha" value={farmInput.fertilizer_consumption} onChange={(v) => set('fertilizer_consumption', v)} step={0.1} min={0} />
        <NumberField label="Pesticide Applied" unit="g/ha" value={farmInput.pesticide_consumption} onChange={(v) => set('pesticide_consumption', v)} step={1} min={0} />
        <label className="block sm:col-span-2">
          <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-1 block">
            Input Intensity <span className="normal-case text-[10px]">(auto-computed: fertilizer + pesticide)</span>
          </span>
          <div className="w-full bg-surface-container border border-outline-variant px-3 py-2 font-data-mono text-data-mono text-on-surface-variant">
            {inputIntensityPreview.toFixed(2)}
          </div>
        </label>
      </SectionCard>

      <SectionCard icon="cloud" title="Climate & Weather">
        <NumberField label="Annual Rainfall" unit="mm" value={farmInput.annual_rainfall} onChange={(v) => set('annual_rainfall', v)} step={1} min={0} />
        <NumberField label="Avg Monthly Rainfall" unit="mm" value={farmInput.average_rainfall} onChange={(v) => set('average_rainfall', v)} step={1} min={0} />
        <NumberField label="Number of Rainy Months" value={farmInput.rainy_months_count} onChange={(v) => set('rainy_months_count', v)} step={1} min={0} max={12} />
        <NumberField label="Avg Temperature" unit="°C" value={farmInput.average_temperature} onChange={(v) => set('average_temperature', v)} step={0.1} />
        <NumberField label="Temperature Range" unit="°C" value={farmInput.temperature_range} onChange={(v) => set('temperature_range', v)} step={0.1} min={0} />
      </SectionCard>

      <div className="flex justify-end gap-3 pb-8">
        <button
          onClick={handleClear}
          className="px-6 py-3 border border-outline-variant font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant hover:bg-surface-container-high"
        >
          Clear Form
        </button>
        <button
          onClick={handleSubmit}
          disabled={!canSubmit || loadingOptions}
          className="px-8 py-3 bg-primary text-on-primary font-label-caps text-label-caps uppercase tracking-wider hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {submitting ? 'Predicting…' : 'Predict Yield'}
          <span className="material-symbols-outlined text-[18px]">bolt</span>
        </button>
      </div>
    </div>
  );
};
