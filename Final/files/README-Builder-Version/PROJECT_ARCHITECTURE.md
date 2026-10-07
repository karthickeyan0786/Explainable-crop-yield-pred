# Project Architecture

## High-Level Flow

```
User (Farmer)
      │
      ▼
React Frontend (Dashboard, Prediction form, Voice Assistant)
      │  HTTP (fetch, src/services/api.ts)
      ▼
FastAPI Backend (main.py)
      │
      ├──► model_service.py  ── feature engineering + per-crop CatBoost prediction
      │
      ├──► shap_service.py   ── grounded, structured SHAP explanation
      │
      ├──► slm_service.py    ── natural-language explanation (Ollama SLM or offline fallback)
      │
      ├──► translation_service.py ── free-text translation (IndicTrans2/Google, for narratives
      │                               generated only in English by an LLM path)
      │
      └──► voice_service.py  ── text-to-speech audio file (gTTS/Coqui)
      │
      ▼
Response (JSON or audio) back to the Frontend
```

## Why Each Block Exists

### React Frontend
The presentation layer. Deliberately kept as the ORIGINAL AI-Studio-exported
app structure wherever it already worked (Sidebar, Header, page routing) —
only the data layer (fake `calculateYield()`) and the new Farmer Assistant
panel were added/changed. This respects "reuse current code wherever
possible."

### FastAPI Backend (`main.py`)
Thin routing layer only. Every route function is a few lines: validate
input (Pydantic), call the appropriate service function(s), return the
result. No business logic lives here — this makes each service testable in
isolation (and was, in fact, tested that way throughout development, since
the live HTTP server in the development sandbox was unstable and business
logic had to be verified via direct Python calls to the service modules).

### `model_service.py` — Prediction Engine
Owns: the 23-feature engineering pipeline (raw farmer input → model-ready
row), the per-crop model registry (lazy-loaded, cached), and the What-If
candidate search. Deliberately does NOT own SHAP or SLM logic — a model
service should only ever answer "what does the model predict for this
input," nothing about why.

**Why per-crop, not one global model:** the single pooled model achieved
R²=0.146 (later 0.313 after data cleaning) because it was forced to relate
124 crop types with incompatible reporting units (tonnes vs. nuts vs.
bales) in one regression target. Training one model per crop (52 models,
≥500 rows each, 96.6% coverage) removes that cross-crop scale confusion
entirely — see `MODEL_PIPELINE.md` for the full quantitative story.

### `shap_service.py` — Explainability Engine
Owns: SHAP value computation, factor deduplication (by agronomic category,
so "Annual_Rainfall" and "Average_Rainfall" don't both show up as separate
factors), and the deterministic recommendation-generation rules. This is
the single source of "grounding facts" — everything downstream (SLM,
translation, voice) only ever operates on what this module produces, never
on its own independently-derived facts. This is the architectural
foundation of the anti-hallucination design.

### `slm_service.py` — Grounded Explanation Engine
Owns: prompt construction (with explicit grounding rules baked into every
prompt) and the Ollama/fallback provider selection. Converts structured
SHAP facts into a flowing, farmer-facing narrative in the requested
language. See `SLM_INTEGRATION.md` for the full grounding methodology.

### `translation_service.py` — Free-Text Translation Engine
Owns: IndicTrans2 and Google Translate integration for translating
free-form text (e.g., if an LLM path generates an explanation only in
English and it needs translating afterward, rather than being generated
directly in the target language). For the FIXED phrases used throughout
the dashboard (factor labels, recommendation actions), `model_service.py`
and `slm_service.py` use the faster, fully-tested `translations.py`
dictionary directly instead of calling this service — see
`TRANSLATION_WORKFLOW.md`.

### `voice_service.py` — Text-to-Speech Engine
Owns: gTTS and Coqui TTS integration for generating a downloadable/
playable audio file server-side. See `VOICE_ASSISTANT_WORKFLOW.md` for why
the frontend's browser-based Web Speech API is the practical default and
how the two backend options complement it.

## Design Decisions

1. **Service-layer separation over one large file.** Each service file has
   exactly one responsibility, testable independently. This was validated
   in practice: during development, `shap_service.py`'s output was fed
   directly into `slm_service.py` and tested via a plain Python script,
   without needing the FastAPI server running at all.
2. **Grounding is structural, not just a prompt suggestion.** The SLM
   literally cannot see anything except the JSON payload `shap_service.py`
   produces — there is no tool access, no retrieval, no ability to query
   the training data. This is the strongest practical grounding available
   without a much heavier RAG/tool-use architecture.
3. **Every "cloud" or "heavy local model" dependency has a tested,
   zero-dependency fallback.** Ollama unreachable → template narrative.
   IndicTrans2/Google unavailable → offline phrase dictionary. Backend TTS
   fails → browser Web Speech API. This was not a theoretical design goal —
   it was necessitated by, and verified against, an actual sandboxed
   development environment that blocked ollama.com, huggingface.co, and
   translate.googleapis.com outright (confirmed via `curl -I` returning
   `403 host_not_allowed` for each).

## Benefits

- New developers can understand and modify one service without reading the
  others.
- The system degrades gracefully instead of breaking when any external
  dependency (Ollama, translation API, TTS API) is unavailable.
- SHAP-derived facts are the single source of truth for both the
  structured UI (factor bars, recommendation cards) and the narrative
  explanation, so they can never contradict each other.

## Limitations

- The per-crop architecture means 53 separate model files (~17MB total) are
  loaded/cached rather than one — a larger deployment footprint than a
  single model, though still small in absolute terms.
- Grounding via strict prompting reduces but does not eliminate
  hallucination risk if a more elaborate LLM is substituted for Ollama's
  small models — see `SLM_INTEGRATION.md` for an honest discussion.
- Live Ollama/IndicTrans2/Google Translate/Coqui TTS integrations are
  implemented against each provider's official API but were **not**
  verified with a live call in the development environment used to build
  this — see each service's file-level docstring and the relevant workflow
  doc for exactly what was and wasn't tested.
