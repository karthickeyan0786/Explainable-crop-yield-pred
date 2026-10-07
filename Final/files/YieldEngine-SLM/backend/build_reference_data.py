"""
build_reference_data.py
-------------------------
Run ONCE to extract everything the FastAPI backend needs from the real
training data, without having to ship the full 93MB CSV with the app:
  - Categorical encoding maps (Crop/Season/State/District <-> encoded int),
    read directly from paired raw+encoded columns in the actual training
    data (not re-fit blind) so they are guaranteed correct.
  - State -> District list (for cascading dropdowns).
  - Reference percentiles per numeric feature (for the What-If candidate
    search), taken from the real training distribution.
  - Dataset overview stats (rows, features, missing values before/after).
  - Real CatBoost evaluation metrics (R2, MAE, RMSE, MSE) computed fresh
    against the exact same train/test split the model was actually trained
    with (same random_state=42, same log1p target, same feature order).
"""
import json
import numpy as np
import pandas as pd
pd.set_option('future.infer_string', False)
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from catboost import CatBoostRegressor
import joblib

RAW_DIR = "/mnt/user-data/uploads"
OUT_DIR = "/home/claude/yield-engine/backend/artifacts"

FEATURES = joblib.load(f"{OUT_DIR}/model_feature_list.joblib")
TARGET = "Yield"

print("Loading Final_Crop_Yield_Dataset.csv ...")
final_df = pd.read_csv(f"{RAW_DIR}/Final_Crop_Yield_Dataset.csv")
print("Shape:", final_df.shape)

# ---------------------------------------------------------------------------
# 1. CATEGORICAL ENCODING MAPS (read directly from paired columns -- exact,
#    no re-fitting risk)
# ---------------------------------------------------------------------------
CATEGORICAL_PAIRS = {
    "Crop_Encoded": "Crop",
    "Season_Encoded": "Season",
    "State_Name_Encoded": "State_Name",
    "District_Name_Encoded": "District_Name",
}
encoding_maps = {}
decoding_maps = {}
for encoded_col, raw_col in CATEGORICAL_PAIRS.items():
    pairs = final_df[[raw_col, encoded_col]].drop_duplicates(subset=raw_col)
    encoding_maps[raw_col] = dict(zip(pairs[raw_col], pairs[encoded_col].astype(int)))
    decoding_maps[encoded_col] = {int(v): k for k, v in encoding_maps[raw_col].items()}

with open(f"{OUT_DIR}/encoding_maps.json", "w") as f:
    json.dump(encoding_maps, f, indent=2)
with open(f"{OUT_DIR}/decoding_maps.json", "w") as f:
    json.dump(decoding_maps, f, indent=2)
print("Saved encoding_maps.json / decoding_maps.json")
print("  States:", len(encoding_maps["State_Name"]), "| Districts:", len(encoding_maps["District_Name"]))
print("  Crops:", len(encoding_maps["Crop"]), "| Seasons:", len(encoding_maps["Season"]))

# ---------------------------------------------------------------------------
# 2. STATE -> DISTRICT LIST (cascading dropdown)
# ---------------------------------------------------------------------------
state_district_map = (
    final_df[["State_Name", "District_Name"]]
    .drop_duplicates()
    .groupby("State_Name")["District_Name"]
    .apply(lambda s: sorted(s.unique().tolist()))
    .to_dict()
)
with open(f"{OUT_DIR}/state_district_map.json", "w") as f:
    json.dump(state_district_map, f, indent=2)
print("Saved state_district_map.json |", len(state_district_map), "states")

# ---------------------------------------------------------------------------
# 3. SOIL TYPE OPTIONS (from the encoder itself, already provided)
# ---------------------------------------------------------------------------
soil_encoder = joblib.load(f"{OUT_DIR}/soil_type_label_encoder.joblib")
with open(f"{OUT_DIR}/soil_type_options.json", "w") as f:
    json.dump(list(soil_encoder.classes_), f)
print("Saved soil_type_options.json")

# Final_Crop_Yield_Dataset.csv only has the raw "Soil Type" text column, same
# as cell 8 of the training notebook -- apply the SAME provided encoder here.
if "Soil_Type_Encoded" not in final_df.columns and "Soil Type" in final_df.columns:
    final_df["Soil_Type_Encoded"] = soil_encoder.transform(final_df["Soil Type"].astype(str))

# ---------------------------------------------------------------------------
# 4. REFERENCE PERCENTILES for What-If candidate search (real distribution)
# ---------------------------------------------------------------------------
SIMULATABLE_FEATURES = [
    "Area", "pH Level", "Organic Matter (%)", "Nitrogen Content (kg/ha)",
    "Potassium Content (kg/ha)", "Soil_Fertility_Index",
    "Fertilizer_Consumption", "Pesticide_Consumption",
    "Annual_Rainfall", "Average_Rainfall", "Rainy_Months_Count",
    "Average_Temperature", "Temperature_Range",
    "Weather_Index", "Climate_Index", "Input_Intensity", "Agricultural_Intensity",
]
model_ready_df = final_df.dropna(subset=FEATURES + [TARGET]).reset_index(drop=True)
top_yield_df = model_ready_df[model_ready_df[TARGET] >= model_ready_df[TARGET].quantile(0.75)]

reference_stats = {}
for feat in SIMULATABLE_FEATURES:
    series = model_ready_df[feat]
    reference_stats[feat] = {
        "p50": float(series.quantile(0.5)),
        "p75": float(series.quantile(0.75)),
        "p90": float(series.quantile(0.9)),
        "top_yield_median": float(top_yield_df[feat].median()) if feat in top_yield_df.columns else float(series.median()),
        "min": float(series.min()),
        "max": float(series.max()),
        "median": float(series.median()),
    }
with open(f"{OUT_DIR}/reference_stats.json", "w") as f:
    json.dump(reference_stats, f, indent=2)
print("Saved reference_stats.json |", len(reference_stats), "features")

# ---------------------------------------------------------------------------
# 5. DATASET OVERVIEW STATS (real numbers, no invented figures)
# ---------------------------------------------------------------------------
dataset_stats = {
    "total_rows_before_dropna": int(len(final_df)),
    "total_rows_model_ready": int(len(model_ready_df)),
    "total_features": int(len(FEATURES)),
    "missing_values_before": int(final_df.isna().sum().sum()),
    "missing_values_after": int(model_ready_df[FEATURES + [TARGET]].isna().sum().sum()),
    "duplicate_rows": int(final_df.duplicated().sum()),
    "target_variable": TARGET,
    "feature_list": FEATURES,
}
with open(f"{OUT_DIR}/dataset_stats.json", "w") as f:
    json.dump(dataset_stats, f, indent=2)
print("Saved dataset_stats.json:", dataset_stats)

# ---------------------------------------------------------------------------
# 6. REAL MODEL EVALUATION METRICS (same split/target-transform as training)
# ---------------------------------------------------------------------------
X = model_ready_df[FEATURES]
y = np.log1p(model_ready_df[TARGET])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = CatBoostRegressor()
model.load_model(f"{OUT_DIR}/best_catboost_model.cbm")

raw_pred = model.predict(X_test)
pred = np.expm1(raw_pred)
actual = np.expm1(y_test)

model_metrics = {
    "model_name": "CatBoost",
    "r2": float(r2_score(actual, pred)),
    "mae": float(mean_absolute_error(actual, pred)),
    "rmse": float(np.sqrt(mean_squared_error(actual, pred))),
    "mse": float(mean_squared_error(actual, pred)),
    "test_set_size": int(len(X_test)),
    "train_set_size": int(len(X_train)),
}
with open(f"{OUT_DIR}/model_metrics.json", "w") as f:
    json.dump(model_metrics, f, indent=2)
print("Saved model_metrics.json:", model_metrics)

# ---------------------------------------------------------------------------
# 7. A SMALL REPRESENTATIVE SAMPLE OF X_test (for SHAP background / dashboard
#    "sample prediction" demo) -- keep this small, not the full dataset.
# ---------------------------------------------------------------------------
sample_df = X_test.sample(n=min(200, len(X_test)), random_state=42)
sample_df.to_csv(f"{OUT_DIR}/x_test_sample.csv", index=False)
print("Saved x_test_sample.csv | rows:", len(sample_df))

print("\nALL REFERENCE DATA BUILT SUCCESSFULLY")
