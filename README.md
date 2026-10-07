# Yield Engine — AI Crop Yield Prediction & Multilingual Farmer Assistant

## Project Overview

Yield Engine is a full-stack Explainable AI system that predicts crop
yield for Indian agricultural data, explains *why* it made that
prediction using SHAP, converts that explanation into natural,
spoken-style language via a grounded Small Language Model (SLM), and
delivers it to farmers in their own language (English, Tamil, Hindi) —
including as spoken audio, so it's usable by farmers who cannot read.

## Motivation

Standard ML dashboards show accuracy metrics and SHAP bar charts. Those
are useful for a data scientist and meaningless to a farmer. This project
exists to close that gap: take a real, validated prediction pipeline and
make its output genuinely usable by the person it's meant to help — in
their language, spoken aloud if needed, with concrete, grounded
recommendations rather than abstract feature-importance numbers.

## Problem Statement

1. Crop yield in this dataset spans 124 crop types reported in
   incompatible units (tonnes/ha for most, nuts/ha for Coconut, etc.). A
   single pooled regression model achieved only R²=0.146–0.313 because it
   was forced to relate incompatible scales in one target.
2. SHAP explanations are precise but not naturally readable by a
   non-technical user.
3. Most farmer-facing agri-tech tools are English-only text interfaces,
   which excludes low-literacy and non-English-speaking users.

## Features

- **Per-crop CatBoost architecture**: 52 crop-specific models (covering
  96.6% of the data) + 1 pooled fallback model, raising real, honestly
  measured R² from 0.146 (single pooled model) to 0.878 (pooled test set
  across the per-crop architecture) — see `MODEL_PIPELINE.md` for the full,
  non-inflated story including per-crop breakdown (0.46–0.95).
- **SHAP explainability**: structured, grounded positive/negative factor
  extraction per prediction.
- **Grounded SLM explanation layer**: converts SHAP facts into a natural,
  spoken-style paragraph, strictly prompted to use only the given facts
  (Ollama/Phi-3 Mini primary, deterministic offline template fallback).
- **Multilingual support**: English, Tamil, Hindi — factor labels,
  recommendations, and the full narrative explanation are all translated,
  not just wrapped in local sentence structure around English text.
- **Voice Assistant**: 🔊 Listen button, backend TTS (gTTS/Coqui, both
  implemented) with automatic fallback to the browser's Web Speech API.
- **What-If Simulation**: model-validated (not fabricated) improvement
  estimates, only ever moving realistically-adjustable inputs.
- **React dashboard**: Dashboard, Prediction, Explainable AI, Decision
  Support, What-If Simulation, EDA, Dataset pages.

## Screenshots

*(Placeholder — insert screenshots of the Dashboard, Prediction form, and
Voice Assistant card here before publishing.)*

## Technology Stack

| Layer | Technology |
|---|---|
| ML Model | CatBoost (per-crop architecture) |
| Explainability | SHAP (TreeExplainer) |
| SLM | Ollama (Phi-3 Mini / Gemma 2B / TinyLlama) + offline template fallback |
| Translation | IndicTrans2 (primary) + Google Translate API (fallback) + offline phrase dictionary (practical default) |
| Voice | gTTS + Coqui TTS (backend) + Web Speech API (frontend, tested default) |
| Backend | Python, FastAPI |
| Frontend | React, TypeScript, Vite, Tailwind |

## Folder Structure

See `PROJECT_ARCHITECTURE.md` for the full annotated tree. Top level:

```
YieldEngine-SLM/
├── backend/
│   ├── main.py                  # API routes
│   ├── model_service.py         # feature engineering + per-crop CatBoost
│   ├── shap_service.py          # grounded SHAP extraction
│   ├── slm_service.py           # grounded SLM explanation (Ollama + fallback)
│   ├── translation_service.py   # IndicTrans2 + Google Translate + fallback
│   ├── voice_service.py         # gTTS + Coqui TTS
│   ├── translations.py          # offline phrase dictionaries (en/ta/hi)
│   └── artifacts/                # trained models, encoders, reference stats
├── src/
│   ├── components/
│   │   ├── farmer-assistant/     # PredictionCard, ExplanationCard, RecommendationsCard, VoiceAssistantCard
│   │   ├── LanguageSelector.tsx
│   │   ├── SpeakButton.tsx
│   │   └── ...existing pages...
│   ├── services/api.ts
│   └── types.ts
└── ...
```

## Installation Guide

**Backend:**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

**Frontend:**
```bash
npm install
cp .env.example .env.local   # points VITE_API_BASE_URL at your backend
```

## Running Instructions

```bash
# Terminal 1
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2
npm run dev
```

Optional, for the local SLM (Ollama):
```bash
ollama serve
ollama pull phi3:mini
```
Without Ollama running, the app automatically uses the tested offline
template fallback — nothing breaks.

## API Overview

See `API_DOCUMENTATION.md` for full request/response examples. Summary:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Model + SLM reachability status |
| `GET /api/options` | Dropdown values (states, crops, seasons, soil types) |
| `POST /api/predict` | Prediction + structured SHAP factors + recommendations |
| `POST /api/explain` | Grounded SLM narrative, in the requested language |
| `POST /api/voice` | Text-to-speech audio file |
| `POST /api/what-if` | Model-validated what-if simulation |
| `GET /api/dataset-info`, `GET /api/model-metrics`, `GET /api/eda` | Real dataset/model statistics |

## Explainable AI Features

SHAP-based positive/negative factor extraction per prediction, deduplicated
by agronomic category, translated into farmer-friendly language — see
`EXPLAINABLE_AI_PIPELINE.md`.

## What-If Simulation Features

Only nudges features that are genuinely realistic to adjust and that the
trained model itself validates as improving the prediction — Crop, Season,
Soil Type, and Area are excluded from numeric search because this
dataset's units aren't comparable across those categories (documented
honestly, not hidden) — see `WHAT_IF_SIMULATION_ENGINE.md`.

## Decision Support Features

Deterministic, rule-based recommendation engine — the same recommendations
are both displayed directly AND fed to the SLM as grounding facts, so the
Explanation Card and Recommendations Card never contradict each other —
see `DECISION_SUPPORT_ENGINE.md`.

## Future Enhancements

See `FUTURE_SCOPE.md`.

## Research Contribution

See `RESEARCH_CONTRIBUTION.md` for the full IEEE-style novelty discussion.
