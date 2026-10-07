# API Documentation

Base URL (local dev): `http://localhost:8000`

## GET /health

Returns model load status and whether Ollama is currently reachable.

**Response:**
```json
{
  "status": "ok",
  "model": "CatBoost (per-crop architecture)",
  "architecture": "52 crop-specific models (>=500 rows each, 96.6% of data) + 1 pooled fallback model for smaller crops",
  "model_loaded": true,
  "n_crop_specific_models": 52,
  "feature_count": 23,
  "slm_ollama_reachable": false
}
```
**Internal flow:** attempts to load the "Rice" model (a representative
crop) to confirm the model registry actually works, and calls
`slm_service._get_ollama_client()` to genuinely check Ollama reachability
rather than assuming.

## GET /api/options

Real dropdown values, read from the actual training data's encoding
vocabulary — never hardcoded.

**Response (truncated):**
```json
{
  "states": ["Andhra Pradesh", "..."],
  "state_district_map": {"Maharashtra": ["PUNE", "..."]},
  "crops": ["Rice", "Wheat", "..."],
  "seasons": ["Kharif", "Rabi", "Summer", "Winter", "Autumn", "Whole Year"],
  "soil_types": ["Alkaline", "Black lava soil", "Clay", "Loamy"]
}
```

## POST /api/predict

**Request:**
```json
{
  "state": "Maharashtra", "district": "PUNE", "crop": "Rice", "season": "Kharif",
  "crop_year": 2015, "area": 1635, "soil_type": "Loamy",
  "ph_level": 6.8, "organic_matter": 2.0, "nitrogen": 29.8, "potassium": 40.0,
  "fertilizer_consumption": 37.2, "pesticide_consumption": 1755.4,
  "annual_rainfall": 900, "average_rainfall": 75, "rainy_months_count": 6,
  "average_temperature": 27, "temperature_range": 12
}
```

**Response:**
```json
{
  "predicted_yield": 1.5219,
  "positive_factors": [
    {"feature": "Average_Rainfall", "label": "Suitable rainfall", "shap_value": 0.31},
    {"feature": "Average_Temperature", "label": "Suitable temperature", "shap_value": 0.22}
  ],
  "negative_factors": [
    {"feature": "Area", "label": "Land utilization", "shap_value": -0.25, "context": null},
    {"feature": "Season_Encoded", "label": "Sowing season", "shap_value": -0.09, "context": "Current season: Kharif"}
  ],
  "recommendations": [
    {"issue": "Land utilization", "action": "Optimize field spacing and land utilization", "reason": "The explainability model identified land utilization as a negative contributor."}
  ],
  "model_used": "per_crop"
}
```
**Internal flow:** `build_feature_row()` → `shap_service.get_shap_explanation()`
→ strip internal-only `top_negative_raw` field → return.

## POST /api/explain

Same request body as `/api/predict`, plus `lang` (`"en"` | `"ta"` |
`"hi"`, default `"en"`).

**Response:**
```json
{
  "language": "தமிழ் (Tamil)",
  "explanation": "உங்கள் காரிஃப் பருவ நெல் பயிருக்கு, எதிர்பார்க்கப்படும் மகசூல் ஏறத்தாழ ஹெக்டேருக்கு 1.52 டன்கள். ...",
  "source": "template_fallback",
  "model": "template"
}
```
**Internal flow:** `build_feature_row()` → `shap_service.get_shap_explanation()`
(grounding facts) → `slm_service.generate_explanation()` (Ollama if
reachable, else the tested offline template) → return. `source`/`model`
tell you whether the live SLM or the fallback actually produced this
specific response — useful for monitoring how often Ollama is actually
being used in production.

## POST /api/voice

**Request:**
```json
{ "text": "Your explanation text here...", "lang": "ta", "provider": "gtts" }
```
**Response:** raw audio bytes (`audio/mpeg` for gTTS, `audio/wav` for
Coqui) on success; on failure, HTTP 503 with:
```json
{ "detail": { "error": "gTTS synthesis failed (likely a network issue): ...", "recommend_frontend_tts": true } }
```
**Internal flow:** `voice_service.synthesize_speech()` tries the requested
provider; on any failure, returns a structured error rather than raising,
which the route converts to a 503 the frontend explicitly checks for
before falling back to the Web Speech API.

## POST /api/what-if

Same request body as `/api/predict` (no `lang` needed — What-If operates
on structured facts only, not narrative text).

**Response:**
```json
{
  "current_yield": 1.5219,
  "improved_yield": 1.7101,
  "percentage_improvement": 12.36,
  "changed_parameters": [
    {"feature": "Temperature_Range", "label": "Temperature stability", "before": 12.0, "after": 10.98}
  ]
}
```

## GET /api/dataset-info, GET /api/model-metrics, GET /api/eda

Real, computed statistics — no invented figures. See
`DATABASE_AND_DATAFLOW.md` for what each contains and how it was computed.

## GET /api/languages

```json
{ "supported_languages": { "en": "English", "ta": "தமிழ் (Tamil)", "hi": "हिन्दी (Hindi)" } }
```
