export type NavTab =
  | 'dashboard'
  | 'prediction'
  | 'explainable-ai'
  | 'decision-support'
  | 'what-if'
  | 'eda'
  | 'dataset';

// ---------------------------------------------------------------------------
// FARM INPUT — mirrors the FastAPI FarmInput schema exactly (23 real model
// features, grouped per the UI spec). Field names are snake_case to match
// the backend's Pydantic model directly (no translation layer needed).
// ---------------------------------------------------------------------------
export interface FarmInput {
  // Group 1 — Crop Information
  state: string;
  district: string;
  crop: string;
  season: string;
  crop_year: number;
  area: number;

  // Group 2 — Soil Characteristics
  soil_type: string;
  ph_level: number;
  organic_matter: number;
  nitrogen: number;
  potassium: number;
  // Soil_Fertility_Index is NOT collected here -- it's derived server-side
  // as mean(nitrogen, potassium), same formula used during training.

  // Group 3 — Agricultural Inputs
  fertilizer_consumption: number;
  pesticide_consumption: number;
  // Input_Intensity / Agricultural_Intensity are derived server-side.

  // Group 4 — Climate & Weather
  annual_rainfall: number;
  average_rainfall: number;
  rainy_months_count: number;
  average_temperature: number;
  temperature_range: number;
  // Weather_Index / Climate_Index are derived server-side.

  lang: LanguageCode;
}

export type LanguageCode = 'en' | 'ta' | 'hi';

export const DEFAULT_FARM_INPUT: FarmInput = {
  state: '',
  district: '',
  crop: '',
  season: '',
  crop_year: new Date().getFullYear(),
  area: 0,
  soil_type: '',
  ph_level: 6.5,
  organic_matter: 1.5,
  nitrogen: 25,
  potassium: 30,
  fertilizer_consumption: 30,
  pesticide_consumption: 800,
  annual_rainfall: 900,
  average_rainfall: 75,
  rainy_months_count: 6,
  average_temperature: 27,
  temperature_range: 12,
  lang: 'en',
};

export interface SlmExplanation {
  language: string;
  explanation: string;
  source: 'ollama' | 'template_fallback';
  model: string;
}

// ---------------------------------------------------------------------------
// API RESPONSE SHAPES — match model_service.py's return dicts exactly
// ---------------------------------------------------------------------------
export interface PositiveFactor {
  feature: string;
  label: string;
  shap_value: number;
}

export interface NegativeFactor {
  feature: string;
  label: string;
  context: string | null;
  shap_value: number;
}

export interface Recommendation {
  issue: string;
  action: string;
  reason: string;
}

export interface PredictionResult {
  predicted_yield: number; // t/ha, already inverse-log-transformed by the backend
  positive_factors: PositiveFactor[];
  negative_factors: NegativeFactor[];
  recommendations: Recommendation[];
}

export interface ChangedParameter {
  feature: string;
  label: string;
  before: number;
  after: number;
}

export interface WhatIfResult {
  current_yield: number;
  improved_yield: number;
  percentage_improvement: number;
  changed_parameters: ChangedParameter[];
}

export interface DatasetInfo {
  total_rows_before_dropna: number;
  total_rows_model_ready: number;
  total_features: number;
  missing_values_before: number;
  missing_values_after: number;
  duplicate_rows: number;
  target_variable: string;
  feature_list: string[];
}

export interface ModelMetrics {
  model_name: string;
  r2: number;
  mae: number;
  rmse: number;
  mse: number;
  test_set_size: number;
  train_set_size: number;
}

export interface OptionsResponse {
  states: string[];
  state_district_map: Record<string, string[]>;
  crops: string[];
  seasons: string[];
  soil_types: string[];
}

// ---------------------------------------------------------------------------
// EDA STATS — real, computed from the actual cleaned dataset (see
// backend/build_eda_stats.py), not fabricated placeholder numbers.
// ---------------------------------------------------------------------------
export interface StateRecordCount {
  state: string;
  record_count: number;
  pct_of_total: number;
}

export interface YieldCorrelation {
  feature: string;
  correlation: number;
}

export interface ScatterPoint {
  area: number;
  production: number;
}

export interface HistogramBin {
  bin_start: number;
  bin_end: number;
  count: number;
}

export interface EdaStats {
  n_rows: number;
  n_crops: number;
  n_states: number;
  top_producing_states: StateRecordCount[];
  top3_states_pct_of_total: number;
  crop_production_by_state_chart: { state: string; record_count: number }[];
  yield_correlations: YieldCorrelation[];
  area_production_scatter_sample: ScatterPoint[];
  area_production_scatter_crop: string;
  area_production_scatter_correlation: number;
  yield_histogram: HistogramBin[];
  rainfall_histogram: HistogramBin[];
}
