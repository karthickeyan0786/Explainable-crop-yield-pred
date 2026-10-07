# What-If Simulation Engine

## Current Prediction

The baseline is always the real model output for the farmer's actual
entered values (`current_yield` in the API response) — never a stored or
assumed number.

## Adjustable Variables

Only features in `SIMULATABLE_FEATURES` are eligible for numeric
adjustment: soil chemistry (pH, Organic Matter, N/K, Soil Fertility
Index), Fertilizer/Pesticide Consumption, Rainfall/Temperature features,
and the derived indices. **Deliberately excluded**: `Crop_Encoded`,
`Season_Encoded`, `Soil_Type_Encoded` (their encoded integer values aren't
ordinally meaningful, and comparing raw predicted yield across different
crop types is unreliable given this dataset's cross-crop unit
inconsistency — see `MODEL_PIPELINE.md`), and `Area` (this dataset has
extreme Area outliers, up to 8.58 million "hectares" for individual rows,
almost certainly mixed-in district-aggregate records — a naive percentile
search on Area produced a nonsensical "expand from 1,635 to 27,100
hectares" suggestion during development, which is why it's excluded).

## Candidate Generation

For each simulatable negative factor, `get_candidates()` proposes several
REAL values drawn from the crop's own training distribution: the 50th,
75th, and 90th percentile, plus the median value among that crop's
top-yielding 25% of historical records — never an arbitrary or invented
number.

## Re-Running the Model

`find_best_value()` tries each candidate through the actual trained model
(`model.predict()`), keeping only the candidate that genuinely increases
the predicted yield (log-space comparison is valid here since `expm1()` is
monotonic — whichever candidate wins in log-space also wins in real t/ha
space). If no candidate improves the prediction, the feature is left
unchanged and simply doesn't appear in `changed_parameters` — the system
never fabricates a "successful" change.

## Improvement Estimation

```
percentage_improvement = (improved_yield - current_yield) / current_yield * 100
```
Computed only after every simulatable factor has been tried and the
resulting `improved_row` re-predicted — never a hardcoded or estimated
percentage.

## Scenario Comparison

The frontend's What-If page shows Current → Improved side by side, plus an
expandable "which inputs changed" section listing exactly which features
were adjusted and their before/after values — so the farmer (or a
reviewer) can see precisely what assumption produced the improvement
estimate, not just the headline percentage.

## Complete Architecture

```
Farmer Input
      │
      ▼
shap_service.get_shap_explanation()  ── same grounding facts as /api/explain
      │
      ▼
For each top negative-SHAP factor in SIMULATABLE_FEATURES:
      │
      ├──► get_candidates()      ── real training-data percentiles for this crop
      │
      └──► find_best_value()     ── try each candidate through the real model,
                                     keep only genuine improvements
      │
      ▼
improved_row (only genuinely-improving features changed)
      │
      ▼
model.predict(improved_row) → expm1() → improved_yield
      │
      ▼
{current_yield, improved_yield, percentage_improvement, changed_parameters}
```
