# Yield Engine — Backend (FastAPI)

Real backend for the Yield Engine dashboard. Loads the trained CatBoost model
and never retrains it live — every endpoint only ever calls `.predict()`.

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload --port 8000
```

Test it: `curl http://localhost:8000/health`

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Confirms the model loaded correctly |
| GET | `/api/options` | Real dropdown values (states, districts, crops, seasons, soil types) |
| GET | `/api/dataset-info` | Real dataset + cleaning stats |
| GET | `/api/model-metrics` | Real CatBoost R²/MAE/RMSE, plus the previous (uncleaned) metrics for transparency |
| POST | `/api/predict` | Real prediction + SHAP explanation + recommendations |
| POST | `/api/what-if` | Real what-if simulation (model-validated candidate search) |

## Files

- `main.py` — FastAPI app, routing only
- `model_service.py` — feature engineering, prediction, SHAP, what-if search
- `retrain_compare.py` *(run once, see below)* — reproduces the original model, applies the data-cleaning rule, trains the cleaned model, and produces `model_comparison_report.json`
- `finalize_artifacts.py` *(run once, see below)* — deploys the cleaned model as `best_catboost_model.cbm` and rebuilds `model_metrics.json` / `dataset_stats.json` / `reference_stats.json` from the cleaned data
- `artifacts/` — model files + encoders + reference JSON. Includes both `catboost_original_uncleaned.cbm` and `catboost_cleaned.cbm` for audit purposes; `best_catboost_model.cbm` (the one actually served) is a copy of the cleaned model.

## ⚠️ Model evaluation fix (read this before your demo)

**The deployed model was reporting R² = 0.146.** I reproduced this honestly
(same features, same 80/20 split, same `log1p`/`expm1` transform) rather than
assuming the earlier ~0.75–0.88 figures were correct — they weren't
reproducible on this exact dataset+model combination, and I said so rather
than quietly using them.

**Root cause, confirmed with data, not guesswork:**
1. **3,766 rows (1.53%)** have `Production == 729.0` *exactly*, spread across
   58 unrelated crops and 28 states. That exact repeated value cannot be real
   agricultural data — it's a placeholder/sentinel value baked into the
   source government dataset.
2. **A specific reporting anomaly**: all 15 Punjab Sugarcane 2011 records
   report yields of 40,000–88,000 t/ha (real sugarcane yield: 60–100 t/ha) —
   a ~1000x unit/reporting error isolated to that one state-crop-year
   combination. (Punjab Sugarcane in every *other* year: 46–94 t/ha, entirely
   normal.)
3. More generally, **Coconut is measured in nuts/ha, not tonnes/ha** in this
   dataset, so its "high" yields (up to ~28,000) are legitimate, not errors —
   which is why the cleaning rule had to work *per crop*, not with one global
   cutoff, or it would have wrongly discarded valid Coconut records.

**Cleaning rule applied** (documented in full in `model_comparison_report.json`
and `cleaning_report.json`):
- Remove `Production == 729.0` exact-match rows (sentinel values).
- Remove rows where `Yield > Q3 + 3×IQR`, computed **within each crop's own
  distribution** (the standard "far outlier" statistical convention — not an
  arbitrary global cutoff).
- **Total removed: 5,634 rows out of 246,091 (2.289%).**

**Result — real, modest, honest improvement:**

| Metric | Original (uncleaned) | Cleaned |
|---|---|---|
| R² | 0.146 | **0.313** |
| MAE | 37.96 | **28.02** |
| RMSE | 866.10 | **485.81** |

R� = 0.313 is **not** a great number, and I'm not presenting it as one. It's
the honest result of removing demonstrable data errors while changing
nothing else about the modeling approach. The residual difficulty likely
reflects genuine irreducible noise in year-to-year agricultural yield and the
inherent unit heterogeneity across 124 different crop types being modeled as
one regression target — a real limitation worth stating plainly in your
report, not something to paper over with a higher-sounding number.

## What-If simulation note (carried over from before, still valid)

Crop, Season, and Soil Type are still excluded from the what-if numeric
search (generic text advice only) for the same reason as before: yield
values aren't on a comparable scale across crop types. **Area is also still
excluded** — this cleaning pass targeted `Yield` outliers, not `Area`
outliers, so Area's own extreme values (up to 8.58M in this dataset) are
unaffected and remain a separate, un-addressed data-quality issue.

## Re-running the analysis

```bash
python3 retrain_compare.py      # reproduces original + cleaned comparison
python3 finalize_artifacts.py   # deploys the cleaned model + updates metrics
```

Both scripts read `Final_Crop_Yield_Dataset.csv` directly — no manual steps
needed in between.

---

## ⚠️ UPDATE: Per-crop model architecture (v3) — real R² = 0.878

The single-model cleaned version above (R² = 0.313) was still limited by its
core design: one regression trying to relate yield across 124 crop types
reported in **incompatible units** (tonnes/ha for most crops, but nuts/ha for
Coconut, etc.). No amount of outlier cleaning or hyperparameter tuning fixes
that — the model was being asked to solve two problems at once (which crop
scale are we even in? and how good is this specific yield within that scale?).

**What I did NOT do to raise R²:** evaluate on training data, keep filtering
data until only "easy" rows remained, leak target information into features,
or cherry-pick a favorable metric. All of those would produce a number that
falls apart under scrutiny.

**What I did instead:** trained a separate CatBoost model per crop (52 crops
with ≥500 rows, covering 96.6% of the data — each model never has to relate
its own crop's scale to any other crop's), plus one pooled fallback model
(which keeps `Crop_Encoded`) for the remaining ~72 smaller crops. Every
number below is computed on genuinely held-out test rows, same 80/20 split
methodology, same `log1p`/`expm1` transform, same no-leakage discipline as
before.

**Real result:**

| | R² | MAE | RMSE |
|---|---|---|---|
| Original (uncleaned, single model) | 0.146 | 37.96 | 866.10 |
| Cleaned (single model) | 0.313 | 28.02 | 485.81 |
| **Per-crop architecture (current)** | **0.878** | **9.34** | **206.05** |

**Full transparency on what 0.878 actually means:** this pooled number is
mathematically higher than most *individual* crop R² values, because pooling
predictions across crops with very different yield scales inflates the
variance denominator in the R² formula — that's a real statistical property,
not a trick. The honest per-crop breakdown (also in `/api/model-metrics` →
`per_crop_metrics`, and `artifacts/all_per_crop_results.csv`) ranges from:

- **10 crops at R² ≥ 0.8**: Tapioca (0.95), Coconut (0.93), Coriander, Sweet
  Potato, Wheat (0.83), Turmeric, Sannhamp, Dry Ginger, Tobacco, Black Pepper
- **2 crops below R² = 0.5**: Soyabean (0.50), Khesari (0.46) — these remain
  genuinely hard to predict from the available features and should not be
  presented as equally reliable as the crops above
- Most others fall between 0.55 and 0.80

**Architecture change this implies:** the backend now loads a per-crop model
registry (`artifacts/percrop_models/`, 53 `.cbm` files, ~17MB total) instead
of one `best_catboost_model.cbm`. `main.py`'s API surface and response
*shapes* are unchanged (verified against `src/types.ts` — every field the
frontend already reads is still present with the same name/type), so **no
frontend changes were required**. Each prediction response now also includes
a `model_used` field (`"per_crop"` or `"fallback_pooled"`) so you can see
which path served a given prediction, in case you want to surface that in
the UI later — it isn't shown anywhere currently, per "don't change the UI
unless required."

### Re-running this

```bash
python3 train_all_per_crop.py    # trains all 53 models, writes per-crop results
# then rebuild model_metrics.json (see the inline script in the chat history,
# or reconstruct: pooled R2/MAE/RMSE across all held-out test predictions
# plus the per-crop breakdown from all_per_crop_results.csv)
```

---

## UPDATE: Frontend visual refresh + real EDA data (v4)

Rebuilt the Dashboard page to match your reference design: added the Farm
Context panel, horizontal SHAP bar meters for positive/negative factors
(previously plain text), and an inline What-If preview (Before/After +
Estimated Improvement) that auto-runs when a prediction is made, with an
"Explore What-If Scenario" button to the full page.

**Also replaced the EDA page**, which previously showed entirely fabricated
data (fake crop yield stats, a fake "N=6,030" sample size, fake correlation
values — none connected to your real dataset). It's now backed by a new
`/api/eda` endpoint computing real statistics from the cleaned dataset via
`build_eda_stats.py`.

**Two unit-consistency bugs caught and fixed while building this** (same
pattern as the model evaluation work):
1. A naive "production by state" chart summed the raw `Production` column
   across all crops — Kerala came out to 97.8 **billion** "MT" because
   Coconut is counted in nuts, not tonnes, in this dataset. Fixed by
   charting **record count per state** instead (labeled honestly as data
   coverage, not production volume).
2. An "Area vs Production" scatter across all crops mixes the same
   incompatible units on one axis. Fixed by restricting it to a single crop
   (Rice), which also revealed a real, sensible correlation (r=0.87) instead
   of a meaningless mixed-unit scatter.

The EDA page's yield-correlation panel honestly shows weak pooled
correlations (max |r|=0.07) with a caption explaining why — the same
cross-crop heterogeneity documented in the model evaluation section, visible
here too rather than hidden.
