# Database and Data Flow

This project uses no live database — all "data" is either (a) static
artifacts produced once by an offline training pipeline and loaded at
backend startup, or (b) the per-request farmer input, which is never
persisted.

## Full Data Flow

```
5 Government of India CSVs
      │
      ▼
Merge + Clean (see DATA_PIPELINE.md)
      │
      ▼
Final_Crop_Yield_Dataset.csv (240,457 rows, post-cleaning)
      │
      ▼
Per-crop train/test split + CatBoost training (see MODEL_TRAINING_PROCESS.md)
      │
      ▼
backend/artifacts/  (committed to the repo, loaded at backend startup)
  ├── percrop_models/*.cbm       (53 trained CatBoost models)
  ├── model_feature_list.joblib
  ├── soil_type_label_encoder.joblib
  ├── encoding_maps.json / decoding_maps.json
  ├── state_district_map.json
  ├── soil_type_options.json
  ├── reference_stats.json / per_crop_reference_stats.json
  ├── dataset_stats.json
  ├── model_metrics.json / all_per_crop_results.csv
  └── eda_stats.json
      │
      ▼
model_service.py loads these once (module-level + lazy per-crop caching)
      │
      ▼
Runtime: Farmer Input (never persisted) ──► Prediction ──► Response
```

## Why No Live Database

The model registry, encoders, and reference statistics are all
**derived once from the training data and static thereafter** — there is
no need for a live database to serve them, and shipping small JSON/joblib
files keeps the backend's runtime footprint minimal (~17MB total for all
53 models + reference data) without requiring a database server as a
deployment dependency.

## What Each Artifact Contains

| File | Contents | Source |
|---|---|---|
| `percrop_models/*.cbm` | Trained CatBoost models | `train_all_per_crop.py` |
| `encoding_maps.json` / `decoding_maps.json` | Category↔integer-code lookups, read directly from paired training-data columns | `build_reference_data.py` |
| `reference_stats.json` / `per_crop_reference_stats.json` | Percentiles per feature (What-If candidate generation) | `build_reference_data.py` / `train_all_per_crop.py` |
| `dataset_stats.json` | Real row counts, missingness, cleaning rule applied | `finalize_artifacts.py` |
| `model_metrics.json` / `all_per_crop_results.csv` | Real R²/MAE/RMSE, pooled and per-crop | `finalize_artifacts.py` |
| `eda_stats.json` | Real EDA statistics (state record counts, single-crop Area-vs-Production correlation, yield/rainfall histograms) | `build_eda_stats.py` |

## Farmer Input Data Flow (Per-Request, Not Persisted)

Farmer-entered values flow through the request/response cycle only — they
are validated by Pydantic, transformed into a feature row, used for one
prediction, and discarded. No farmer input is written to disk or a
database by this backend. (A production deployment wanting to log
predictions for monitoring/auditing would need to add this explicitly —
see `FUTURE_SCOPE.md`.)
