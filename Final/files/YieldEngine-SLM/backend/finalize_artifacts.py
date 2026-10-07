"""
finalize_artifacts.py
------------------------
Deploys the CLEANED model as production, and rebuilds only the artifacts
that should reflect the cleaned data (model file, model_metrics.json,
dataset_stats.json, reference_stats.json for the What-If simulator).

Does NOT touch encoding_maps.json / decoding_maps.json / state_district_map.json
/ soil_type_options.json: those are category<->code VOCABULARY lookups built
from columns that were already integer-encoded before cleaning ever happens
(the codes are fixed regardless of which rows get removed), so the full
124-crop / all-states vocabulary must be preserved for the frontend dropdowns
and for decoding SHAP factor labels, even for crops that had some (not all)
of their rows removed as outliers.
"""
import json
import shutil
import numpy as np
import pandas as pd
pd.set_option('future.infer_string', False)
from sklearn.model_selection import train_test_split
import joblib

RAW_DIR = "/mnt/user-data/uploads"
ART_DIR = "/home/claude/yield-engine/backend/artifacts"
TARGET = "Yield"

FEATURES = joblib.load(f"{ART_DIR}/model_feature_list.joblib")
soil_encoder = joblib.load(f"{ART_DIR}/soil_type_label_encoder.joblib")

df = pd.read_csv(f"{RAW_DIR}/Final_Crop_Yield_Dataset.csv")
if "Soil_Type_Encoded" not in df.columns and "Soil Type" in df.columns:
    df["Soil_Type_Encoded"] = soil_encoder.transform(df["Soil Type"].astype(str))

model_ready_df = df.dropna(subset=FEATURES + [TARGET]).reset_index(drop=True)

# ---- re-apply the SAME cleaning rule used in retrain_compare.py ----
sentinel_mask = model_ready_df["Production"] == 729.0


def crop_far_outlier_mask(group):
    q1, q3 = group.quantile(0.25), group.quantile(0.75)
    iqr = q3 - q1
    return group > (q3 + 3 * iqr)


per_crop_outlier_mask = model_ready_df.groupby("Crop")[TARGET].transform(crop_far_outlier_mask)
combined_mask = sentinel_mask | per_crop_outlier_mask
cleaned_df = model_ready_df[~combined_mask].reset_index(drop=True)
print("Cleaned dataset:", cleaned_df.shape)

# ---- 1. Deploy the cleaned model as the production artifact ----
shutil.copy(f"{ART_DIR}/catboost_cleaned.cbm", f"{ART_DIR}/best_catboost_model.cbm")
print("Deployed catboost_cleaned.cbm -> best_catboost_model.cbm")

# ---- 2. model_metrics.json: real metrics from the cleaned model/test split ----
with open(f"{ART_DIR}/model_comparison_report.json") as f:
    comparison = json.load(f)

model_metrics = {
    "model_name": "CatBoost",
    "r2": comparison["cleaned"]["r2"],
    "mae": comparison["cleaned"]["mae"],
    "rmse": comparison["cleaned"]["rmse"],
    "mse": comparison["cleaned"]["mse"],
    "test_set_size": comparison["cleaned"]["test_size"],
    "train_set_size": comparison["cleaned"]["train_size"],
    "data_cleaning_applied": True,
    "rows_removed_as_outliers": comparison["cleaning"]["rows_removed"],
    "pct_rows_removed": round(comparison["cleaning"]["pct_removed"], 3),
    "previous_uncleaned_metrics": {
        "r2": comparison["original"]["r2"],
        "mae": comparison["original"]["mae"],
        "rmse": comparison["original"]["rmse"],
    },
}
with open(f"{ART_DIR}/model_metrics.json", "w") as f:
    json.dump(model_metrics, f, indent=2)
print("Saved model_metrics.json:", model_metrics)

# ---- 3. dataset_stats.json: reflect the cleaned, deployed dataset ----
dataset_stats = {
    "total_rows_before_dropna": int(len(df)),
    "total_rows_model_ready": int(len(cleaned_df)),
    "total_rows_before_cleaning": int(len(model_ready_df)),
    "rows_removed_as_outliers": int(combined_mask.sum()),
    "total_features": int(len(FEATURES)),
    "missing_values_before": int(df.isna().sum().sum()),
    "missing_values_after": int(cleaned_df[FEATURES + [TARGET]].isna().sum().sum()),
    "duplicate_rows": int(df.duplicated().sum()),
    "target_variable": TARGET,
    "feature_list": FEATURES,
    "outlier_cleaning_rule": comparison["cleaning"]["rule"],
}
with open(f"{ART_DIR}/dataset_stats.json", "w") as f:
    json.dump(dataset_stats, f, indent=2)
print("Saved dataset_stats.json")

# ---- 4. reference_stats.json: recompute from CLEANED training distribution
#         (used by the What-If simulator's candidate search) ----
X_clean = cleaned_df[FEATURES]
y_clean = cleaned_df[TARGET]
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
    X_clean, y_clean, test_size=0.2, random_state=42
)
train_ready_df = cleaned_df.loc[X_train_c.index]
top_yield_df = train_ready_df[train_ready_df[TARGET] >= train_ready_df[TARGET].quantile(0.75)]

SIMULATABLE_FEATURES = [
    "Area", "pH Level", "Organic Matter (%)", "Nitrogen Content (kg/ha)",
    "Potassium Content (kg/ha)", "Soil_Fertility_Index",
    "Fertilizer_Consumption", "Pesticide_Consumption",
    "Annual_Rainfall", "Average_Rainfall", "Rainy_Months_Count",
    "Average_Temperature", "Temperature_Range",
    "Weather_Index", "Climate_Index", "Input_Intensity", "Agricultural_Intensity",
]
reference_stats = {}
for feat in SIMULATABLE_FEATURES:
    series = X_train_c[feat]
    reference_stats[feat] = {
        "p50": float(series.quantile(0.5)),
        "p75": float(series.quantile(0.75)),
        "p90": float(series.quantile(0.9)),
        "top_yield_median": float(top_yield_df[feat].median()) if feat in top_yield_df.columns else float(series.median()),
        "min": float(series.min()),
        "max": float(series.max()),
        "median": float(series.median()),
    }
with open(f"{ART_DIR}/reference_stats.json", "w") as f:
    json.dump(reference_stats, f, indent=2)
print("Saved reference_stats.json (recomputed from cleaned training data)")

# ---- 5. Also verify Area's outlier problem specifically got addressed ----
print("\nArea stats in CLEANED training data:")
print(X_train_c["Area"].describe())
print("\n(For comparison, original uncleaned Area max was 8,580,100 -- this")
print(" cleaning rule targets Yield outliers, not Area directly, so check")
print(" whether Area extremes were incidentally reduced too.)")

print("\nDONE — artifacts finalized with the cleaned model.")
