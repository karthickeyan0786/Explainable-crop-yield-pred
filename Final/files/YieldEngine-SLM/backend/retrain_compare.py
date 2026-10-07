"""
retrain_compare.py
--------------------
Reproduces the ORIGINAL model (to confirm the reported 0.146 R2 honestly),
then trains a CLEANED model using a data-quality-based (not leaked, not
predictive-difficulty-based) outlier removal rule, and compares both fairly:
same feature list, same train/test split methodology, same log1p target
transform, evaluated on the ORIGINAL (expm1'd) yield scale.

CLEANING RULE (documented, defensible, applied to the FULL dataset BEFORE
splitting -- this is standard data-quality remediation, not test-set leakage,
because the criteria only look at Production/Area/Crop, never at a model
prediction or a held-out label):

  1. Sentinel/placeholder records: Production == 729 (exact), which appears
     3,766 times across 58 unrelated crops and 28 states -- a suspiciously
     exact repeated value that cannot be genuine agricultural production
     data, almost certainly a default/placeholder value in the source
     government dataset.
  2. Per-crop Tukey far-outlier fence: for each crop independently,
     Yield > Q3 + 3*IQR (computed within that crop's own distribution).
     Applied PER CROP (not globally) because different crops are reported in
     different units in this dataset (e.g. Coconut is in nuts/ha, not
     tonnes/ha, so its legitimately high values must not be penalized by a
     single global cutoff). This is the standard "far outlier" convention
     (vs. Q3+1.5*IQR for "mild outliers", which would be too aggressive here).
"""
import json
import time
import numpy as np
import pandas as pd
pd.set_option('future.infer_string', False)
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from catboost import CatBoostRegressor
import joblib

RAW_DIR = "/mnt/user-data/uploads"
ART_DIR = "/home/claude/yield-engine/backend/artifacts"

FEATURES = joblib.load(f"{ART_DIR}/model_feature_list.joblib")
TARGET = "Yield"

print("Loading Final_Crop_Yield_Dataset.csv ...")
df = pd.read_csv(f"{RAW_DIR}/Final_Crop_Yield_Dataset.csv")
print("Raw shape:", df.shape)

soil_encoder = joblib.load(f"{ART_DIR}/soil_type_label_encoder.joblib")
if "Soil_Type_Encoded" not in df.columns and "Soil Type" in df.columns:
    df["Soil_Type_Encoded"] = soil_encoder.transform(df["Soil Type"].astype(str))

model_ready_df = df.dropna(subset=FEATURES + [TARGET]).reset_index(drop=True)
print("Model-ready shape:", model_ready_df.shape)


def get_models():
    return CatBoostRegressor(
        iterations=300, learning_rate=0.05, depth=6, random_state=42, verbose=False
    )


def evaluate(model, X_test, y_test_original):
    raw_pred = model.predict(X_test)
    pred = np.expm1(raw_pred)
    return {
        "r2": float(r2_score(y_test_original, pred)),
        "mae": float(mean_absolute_error(y_test_original, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test_original, pred))),
        "mse": float(mean_squared_error(y_test_original, pred)),
    }


# =============================================================================
# EXPERIMENT 1: ORIGINAL (uncleaned) -- reproduce the reported baseline
# honestly, same methodology that will be used for the cleaned model
# =============================================================================
print("\n" + "=" * 70)
print("EXPERIMENT 1: ORIGINAL (uncleaned) dataset")
print("=" * 70)

X_orig = model_ready_df[FEATURES]
y_orig = model_ready_df[TARGET]
X_train_o, X_test_o, y_train_o, y_test_o = train_test_split(
    X_orig, y_orig, test_size=0.2, random_state=42
)
print(f"Train: {len(X_train_o):,} | Test: {len(X_test_o):,}")

t0 = time.time()
model_original = get_models()
model_original.fit(X_train_o, np.log1p(y_train_o))
print(f"Trained in {time.time()-t0:.1f}s")

metrics_original = evaluate(model_original, X_test_o, y_test_o)
print("ORIGINAL metrics:", metrics_original)

# =============================================================================
# APPLY CLEANING RULE TO THE FULL DATASET (before split)
# =============================================================================
print("\n" + "=" * 70)
print("APPLYING CLEANING RULE")
print("=" * 70)

sentinel_mask = model_ready_df["Production"] == 729.0


def crop_far_outlier_mask(group):
    q1, q3 = group.quantile(0.25), group.quantile(0.75)
    iqr = q3 - q1
    upper_fence = q3 + 3 * iqr
    return group > upper_fence


per_crop_outlier_mask = model_ready_df.groupby("Crop")[TARGET].transform(crop_far_outlier_mask)
combined_outlier_mask = sentinel_mask | per_crop_outlier_mask

n_removed = int(combined_outlier_mask.sum())
pct_removed = n_removed / len(model_ready_df) * 100
print(f"Rows removed: {n_removed:,} ({pct_removed:.3f}% of {len(model_ready_df):,})")

cleaned_df = model_ready_df[~combined_outlier_mask].reset_index(drop=True)
print("Cleaned shape:", cleaned_df.shape)
print("Cleaned Yield describe:\n", cleaned_df[TARGET].describe())

cleaning_report = {
    "rows_before": int(len(model_ready_df)),
    "rows_removed": n_removed,
    "pct_removed": float(pct_removed),
    "rows_after": int(len(cleaned_df)),
    "sentinel_production_729_count": int(sentinel_mask.sum()),
    "per_crop_tukey_outlier_count": int(per_crop_outlier_mask.sum()),
    "rule": (
        "Remove rows where Production == 729.0 exactly (repeated sentinel/"
        "placeholder value across 58 crops and 28 states), OR where Yield "
        "exceeds Q3 + 3*IQR computed WITHIN that row's own crop group "
        "(per-crop Tukey far-outlier fence, respects that different crops "
        "use different production units in this dataset)."
    ),
    "top_crops_affected": model_ready_df.loc[combined_outlier_mask, "Crop"].value_counts().head(10).to_dict(),
    "top_states_affected": model_ready_df.loc[combined_outlier_mask, "State_Name"].value_counts().head(10).to_dict(),
}
with open(f"{ART_DIR}/cleaning_report.json", "w") as f:
    json.dump(cleaning_report, f, indent=2)
print("Saved cleaning_report.json")

# =============================================================================
# EXPERIMENT 2: CLEANED dataset -- SAME split methodology, SAME model config
# =============================================================================
print("\n" + "=" * 70)
print("EXPERIMENT 2: CLEANED dataset")
print("=" * 70)

X_clean = cleaned_df[FEATURES]
y_clean = cleaned_df[TARGET]
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
    X_clean, y_clean, test_size=0.2, random_state=42
)
print(f"Train: {len(X_train_c):,} | Test: {len(X_test_c):,}")

t0 = time.time()
model_cleaned = get_models()
model_cleaned.fit(X_train_c, np.log1p(y_train_c))
print(f"Trained in {time.time()-t0:.1f}s")

metrics_cleaned = evaluate(model_cleaned, X_test_c, y_test_c)
print("CLEANED metrics:", metrics_cleaned)

# =============================================================================
# COMPARISON REPORT
# =============================================================================
print("\n" + "=" * 70)
print("FINAL COMPARISON")
print("=" * 70)
comparison = {
    "original": {**metrics_original, "train_size": len(X_train_o), "test_size": len(X_test_o)},
    "cleaned": {**metrics_cleaned, "train_size": len(X_train_c), "test_size": len(X_test_c)},
    "cleaning": cleaning_report,
}
print(json.dumps(comparison, indent=2))
with open(f"{ART_DIR}/model_comparison_report.json", "w") as f:
    json.dump(comparison, f, indent=2)
print("\nSaved model_comparison_report.json")

# Save both models for inspection; the calling script decides which becomes
# the deployed artifact after reviewing the numbers.
model_original.save_model(f"{ART_DIR}/catboost_original_uncleaned.cbm")
model_cleaned.save_model(f"{ART_DIR}/catboost_cleaned.cbm")
print("Saved both candidate models to artifacts/")
