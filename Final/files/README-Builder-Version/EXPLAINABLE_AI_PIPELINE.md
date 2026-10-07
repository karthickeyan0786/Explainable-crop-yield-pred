# Explainable AI Pipeline

## SHAP

SHapley Additive exPlanations, computed via `shap.TreeExplainer` — the
efficient, exact SHAP implementation for tree ensemble models like
CatBoost. For a single prediction, produces one SHAP value per feature:
how much that feature's specific value pushed the prediction above/below
the model's average output.

## Global vs. Local Explanations

This system uses **local explanations only** — one SHAP computation per
individual farmer prediction, not an aggregated global feature-importance
view. This was a deliberate choice: a farmer needs to know why *their*
field's prediction looks the way it does, not the model's average behavior
across the whole training set. (Global feature importance is available
separately via the Random-Forest-style `feature_importances_` analysis
documented in earlier phases of this project, but is not part of the
farmer-facing pipeline.)

## Waterfall Plots

Not exposed directly to the farmer (SHAP's raw waterfall visualization
requires reading a technical chart). Instead, the same underlying
information — which features pushed the prediction up/down, and by how
much relatively — is exposed as:
1. Horizontal SHAP bar meters in the Explainable AI dashboard section (for
   a technical reviewer/faculty audience)
2. A natural-language narrative via the SLM layer (for the farmer)

## Feature Importance vs. Per-Prediction SHAP

`shap_service.py` deliberately does NOT rank features by global
importance — every SHAP value shown is specific to the one prediction just
made, which is the more actionable and honest framing for decision
support ("why is *my* field's yield low" rather than "what matters on
average across the whole country").

## Positive Factors

`shap_service.get_shap_explanation()` extracts every feature with a
positive SHAP value, deduplicates by agronomic category (so
`Annual_Rainfall` and `Average_Rainfall` never both appear as separate
"rainfall" factors), and maps each to a farmer-friendly phrase (e.g.
`Average_Temperature` → "Suitable temperature") via the
`POSITIVE_PHRASES` / `POSITIVE_PHRASES_I18N` dictionaries.

## Negative Factors

Same extraction/deduplication logic for negative SHAP values, additionally
attaching a "context" string for categorical factors (e.g. "Current crop:
Rice") so the farmer sees not just "crop suitability" but which crop is
being evaluated.

## How the Frontend Displays Them

- **Dashboard's Explainable AI section**: `FactorBar` component — label +
  numeric SHAP value + a horizontal bar sized relative to the largest
  |SHAP| value shown, colored green (positive) or red (negative).
- **Farmer Assistant panel**: the same factors, but converted into the
  Step 7 SLM narrative (see `SYSTEM_WORKFLOW.md`) rather than shown as raw
  numbers — this is the low-literacy-accessible presentation.
- **Decision Support page**: factors shown as a simple ✔/❌ checklist
  alongside the full recommendation cards (Problem / Action / Reason).
