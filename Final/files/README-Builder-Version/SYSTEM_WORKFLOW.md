# System Workflow

End-to-end walkthrough of a single farmer interaction, step by step.

## Step 1: User Enters Crop Parameters
The `PredictionView` form (grouped: Location & Crop Identity, Soil
Characteristics, Agricultural Inputs, Climate & Weather) collects 18 raw
values. Derived fields (Soil Fertility Index, Input Intensity) are shown as
live read-only previews, computed client-side with the same formula the
backend uses, so the farmer sees them but cannot enter an internally
inconsistent value.

## Step 2: Data Validation
Pydantic's `FarmInput` schema in `main.py` validates types and ranges
(e.g. `ph_level: float = Field(ge=0, le=14)`) before any processing starts.
Invalid values are rejected with a 422 response before reaching the model.

## Step 3: Feature Engineering
`model_service.build_feature_row()` maps raw farmer input to the exact
23-column feature vector the trained model expects: categorical fields
(Crop, Season, State, District, Soil Type) are encoded via lookup tables
built from the real training data; derived cross-domain features
(Weather_Index, Climate_Index, Input_Intensity, Agricultural_Intensity,
Soil_Fertility_Index) are computed with the same formulas used during
training (see `DATA_PIPELINE.md`).

## Step 4: Model Prediction
`model_service._load_model_for_crop()` selects the crop-specific CatBoost
model if one exists (52 crops, ≥500 training rows each) or the pooled
fallback model otherwise. The model was trained on `log1p(Yield)`, so its
raw output is passed through `np.expm1()` before being treated as a real
t/ha value — this conversion is applied consistently everywhere a
prediction is produced.

## Step 5: SHAP Explanation
`shap_service.get_shap_explanation()` runs a `shap.TreeExplainer` on the
selected model for this one row, extracts the top-N positive and negative
contributing features (deduplicated by agronomic category), and generates
the deterministic recommendation list from the negative factors. This
structured payload is the single "grounding" artifact everything downstream
depends on.

## Step 6: Decision Support Generation
The recommendation list from Step 5 is not separately regenerated — it's
carried through as-is into both the Recommendations Card (direct display)
and the SLM prompt (Step 7), guaranteeing the two views never disagree.

## Step 7: SLM Explanation (Grounded, Multilingual)
`slm_service.generate_explanation()` builds a strict prompt containing only
the Step 5 facts, in the farmer's selected language, and sends it to Ollama
if reachable; if not, the tested offline template assembles the same
facts (translated via `translations.py`'s category-keyed dictionaries) into
a natural sentence structure appropriate to that language.

## Step 8: Voice Playback (Optional)
If the farmer taps 🔊 Listen, `SpeakButton.tsx` first tries
`POST /api/voice` (backend gTTS synthesis); if that fails for any reason,
it automatically falls back to the browser's native Web Speech API, which
reads the same translated text aloud with zero backend dependency.

## Step 9: Dashboard Visualization
All of the above renders into the Farmer Assistant panel: Prediction Card
(headline number), Voice Assistant Card (language + Listen), Explanation
Card (the Step 7 narrative), Recommendations Card (the Step 5/6 action
list) — plus the existing Explainable AI factor-bar section and Decision
Support cards below it, all fed from the same single `/api/predict` call
result to avoid redundant requests.

## What-If Simulation (Separate, On-Demand Flow)
Triggered separately (Dashboard auto-preview + dedicated What-If page):
`model_service.what_if_simulation()` re-uses Step 5's negative factors,
tries realistic candidate values (drawn from real training-data percentiles
per crop) for each simulatable feature, and keeps only changes the trained
model itself validates as improving the prediction — see
`WHAT_IF_SIMULATION_ENGINE.md`.
