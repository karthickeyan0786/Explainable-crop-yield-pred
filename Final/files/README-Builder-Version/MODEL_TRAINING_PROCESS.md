# Model Training Process

## Data Preparation

Load `Final_Crop_Yield_Dataset.csv` → apply the label encoder for Soil
Type (if not already present) → `dropna()` on the 23 required features
plus the `Yield` target → apply the two-part cleaning rule (sentinel
`Production==729` removal + per-crop Tukey far-outlier removal) → result:
240,457 model-ready rows. See `DATA_PIPELINE.md` for the full rule
definitions.

## Train/Test Split

**Per crop**, not once globally: for each of the 52 crops with ≥500 rows,
an independent 80/20 split (`train_test_split(..., test_size=0.2,
random_state=42)`) on that crop's own rows. The remaining smaller crops
are pooled into one combined dataset and split the same way. This means
every crop's test set is genuinely held out from that crop's own training
— no test row from any crop was ever used to train any model.

## Cross-Validation

Not used in the current training run — a single 80/20 split per crop was
chosen for training-time practicality (53 models to train), given each
crop's training set (≥500 rows minimum, several crops with 10,000+ rows)
is large enough for a single split to give a reasonably stable estimate.
This is a known, documented limitation (not hidden) — see `FUTURE_SCOPE.md`
for the recommended k-fold extension.

## CatBoost Training

Identical hyperparameters across every one of the 53 models, for a fair,
comparable evaluation:
```python
CatBoostRegressor(iterations=300, learning_rate=0.05, depth=6, random_state=42, verbose=False)
```
Trained on `np.log1p(y_train)` in every case.

## Hyperparameter Tuning

Not performed in the current training run (fixed hyperparameters as
above, chosen from prior experimentation on the pooled model, not
re-tuned per crop). A meaningful next step — see `FUTURE_SCOPE.md`.

## Model Evaluation

Per crop: `expm1()` the raw model output, compute `r2_score`,
`mean_absolute_error`, `mean_squared_error` (→ RMSE) against the real
`Yield` scale on that crop's held-out test rows. The **overall pooled**
metrics combine every crop's actual/predicted test pairs (52 crop models +
the fallback model) into one combined `r2_score`/`MAE`/`RMSE` calculation
— this is the real, held-out-test, no-leakage number reported as
`/api/model-metrics`'s headline `r2`/`mae`/`rmse` fields, with the full
per-crop breakdown also exposed via `per_crop_metrics` for transparency
(see `MODEL_PIPELINE.md` for why the pooled number is naturally higher
than most individual per-crop values, and why that's disclosed rather than
hidden).

## Saving Models

Each crop's trained model is saved as
`backend/artifacts/percrop_models/catboost_{crop_name}.cbm` (crop name
sanitized: `/`, spaces, parentheses stripped/replaced). The fallback model
is saved as `catboost_fallback.cbm`. All reference statistics and
metadata (percentiles, dataset stats, evaluation metrics) are saved
alongside as JSON/CSV.

## Deployment Artifacts

Everything the backend needs at runtime is pre-computed and committed to
`backend/artifacts/` — no raw training CSV is shipped with the deployed
application (the full dataset is ~93MB; the artifacts folder is ~17-20MB
total, dominated by the 53 model files themselves at ~330KB each).
