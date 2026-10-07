import {
  FarmInput,
  PredictionResult,
  WhatIfResult,
  DatasetInfo,
  ModelMetrics,
  OptionsResponse,
  EdaStats,
  SlmExplanation,
} from '../types';

// Configure via .env: VITE_API_BASE_URL=http://localhost:8000
const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  health: () => apiFetch<{ status: string; model: string; model_loaded: boolean; feature_count: number }>('/health'),

  getOptions: () => apiFetch<OptionsResponse>('/api/options'),

  getDatasetInfo: () => apiFetch<DatasetInfo>('/api/dataset-info'),

  getModelMetrics: () => apiFetch<ModelMetrics>('/api/model-metrics'),

  getEdaStats: () => apiFetch<EdaStats>('/api/eda'),

  predict: (input: FarmInput) =>
    apiFetch<PredictionResult>('/api/predict', {
      method: 'POST',
      body: JSON.stringify(input),
    }),

  whatIf: (input: FarmInput) =>
    apiFetch<WhatIfResult>('/api/what-if', {
      method: 'POST',
      body: JSON.stringify(input),
    }),

  // NEW: grounded SLM explanation in the requested language (input.lang)
  getExplanation: (input: FarmInput) =>
    apiFetch<SlmExplanation>('/api/explain', {
      method: 'POST',
      body: JSON.stringify(input),
    }),

  // NEW: backend-generated audio (gTTS/Coqui). Returns null if the backend
  // TTS provider is unavailable, so the caller can fall back to the
  // browser's Web Speech API instead of showing a hard error.
  getVoiceAudio: async (text: string, lang: string, provider: 'gtts' | 'coqui' = 'gtts'): Promise<Blob | null> => {
    const res = await fetch(`${API_BASE_URL}/api/voice`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, lang, provider }),
    });
    if (!res.ok) return null;
    return res.blob();
  },
};
