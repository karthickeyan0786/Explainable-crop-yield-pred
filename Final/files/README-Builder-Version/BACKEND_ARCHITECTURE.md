# Backend Architecture

## FastAPI Application Structure

`main.py` is the only file with `@app.get`/`@app.post` decorators — a
deliberate constraint that keeps routing separate from business logic
(Requirement 6: "keep responsibilities separated").

## Service Layer

| File | Responsibility | Depends On |
|---|---|---|
| `model_service.py` | Feature engineering, per-crop model loading/caching, prediction, what-if candidate search | `artifacts/` (models, encoders, reference stats) |
| `shap_service.py` | Grounded, structured SHAP explanation | `model_service.py` |
| `slm_service.py` | Natural-language explanation (Ollama or offline template) | `translations.py`, `model_service.py` (for category lookups in the fallback path) |
| `translation_service.py` | Free-text translation (IndicTrans2/Google) | (standalone; not on the critical path today, see `TRANSLATION_WORKFLOW.md`) |
| `voice_service.py` | Text-to-speech audio generation | (standalone) |
| `translations.py` | Static phrase dictionaries, no logic | (none — pure data) |

A **lazy circular-import avoidance pattern** is used once:
`model_service.what_if_simulation()` needs `shap_service`'s grounded
factors, but `shap_service.py` imports `model_service` at module level.
The `import shap_service` inside `what_if_simulation()`'s function body
(rather than at the top of `model_service.py`) defers that import until
both modules are already fully loaded, avoiding a circular-import error at
startup.

## Model Loading

`model_service._load_model_for_crop(crop)` implements a lazy, cached model
registry: the first request for a given crop loads its `.cbm` file and
builds a `shap.TreeExplainer` for it (both cached in module-level dicts);
subsequent requests for the same crop reuse the cached objects. This
avoids the cost of eagerly loading all 53 models (and their explainers) at
server startup when many deployments will only ever see a handful of
common crops requested.

## Prediction Endpoints

`/api/predict`, `/api/explain`, and `/api/what-if` all funnel through the
same `model_service.build_feature_row()` → model prediction path — there
is exactly one feature-engineering implementation and one prediction call
site in the codebase, referenced by every endpoint that needs a
prediction, eliminating the risk of the three endpoints silently drifting
out of sync with each other.

## SHAP Generation

`shap_service.get_shap_explanation()` is called by `/api/predict` (for the
structured factor list) and again internally by `/api/explain` (to build
the SLM's grounding payload) and `/api/what-if` (to find the candidate
negative factors to try improving) — always the single source of SHAP
facts, never recomputed with different logic in different places.

## What-If Simulation Endpoint

`/api/what-if` calls `model_service.what_if_simulation()`, which internally
calls `shap_service.get_shap_explanation()` for the baseline factors, then
`get_candidates()` + `find_best_value()` per simulatable feature — see
`WHAT_IF_SIMULATION_ENGINE.md` for the full algorithm.

## Error Handling Pattern

Every route wraps its service calls in try/except: `KeyError` (an
unrecognized crop/state/season/soil-type value not in the training data's
encoding vocabulary) → `400`; anything else → `500` with the exception
message. `/api/voice` uses a distinct `503` with a `recommend_frontend_tts`
flag when backend TTS fails, so the frontend can distinguish "try the
browser fallback" from "something is actually broken."

## CORS

`allow_origins=["*"]` for local development — explicitly flagged in
`main.py`'s comments and `DEPLOYMENT_GUIDE.md` as something to tighten to
your actual frontend origin before any real deployment.
