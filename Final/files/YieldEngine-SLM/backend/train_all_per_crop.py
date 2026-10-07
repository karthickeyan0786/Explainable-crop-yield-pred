import numpy as np
import pandas as pd
pd.set_option('future.infer_string', False)
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from catboost import CatBoostRegressor
import joblib
import json
import time
import os

ART_DIR = "/home/claude/yield-engine/backend/artifacts"
FEATURES = joblib.load(f"{ART_DIR}/model_feature_list.joblib")
PER_CROP_FEATURES = [f for f in FEATURES if f != "Crop_Encoded"]
TARGET = "Yield"
MIN_ROWS_FOR_OWN_MODEL = 500

OUT_DIR = "/home/claude/percrop_test/per_crop_models"
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv("/home/claude/percrop_test/cleaned_df.csv")
crop_counts = df["Crop"].value_counts()
eligible_crops = crop_counts[crop_counts >= MIN_ROWS_FOR_OWN_MODEL].index.tolist()  # Only crops with enough data
print(f"Training per-crop models for {len(eligible_crops)} crops "
      f"({crop_counts[crop_counts>=MIN_ROWS_FOR_OWN_MODEL].sum()/len(df)*100:.1f}% of data)")

# ---------------------------------------------------------------------------
# 1. Split EVERY crop's own rows into train/test FIRST (same 80/20,
#    random_state=42 methodology throughout), so the "overall" R2 computed at
#    the end is on genuinely held-out data for every single row, never seen
#    during any model's training.
# ---------------------------------------------------------------------------
all_test_actual = []
all_test_pred = []
per_crop_results = []

t_start = time.time()
for i, crop in enumerate(eligible_crops):
    sub = df[df["Crop"] == crop].reset_index(drop=True)
    X = sub[PER_CROP_FEATURES]
    y = sub[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = CatBoostRegressor(iterations=300, learning_rate=0.05, depth=6, random_state=42, verbose=False)
    model.fit(X_train, np.log1p(y_train))
    pred = np.expm1(model.predict(X_test))

    r2 = r2_score(y_test, pred)
    mae = mean_absolute_error(y_test, pred)
    rmse = np.sqrt(mean_squared_error(y_test, pred))

    per_crop_results.append({
        "crop": crop, "n_rows": len(sub), "n_train": len(X_train), "n_test": len(X_test),
        "r2": r2, "mae": mae, "rmse": rmse, "yield_median": float(y.median()),
    })
    all_test_actual.extend(y_test.tolist())
    all_test_pred.extend(pred.tolist())

    safe_name = crop.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
    model.save_model(f"{OUT_DIR}/catboost_{safe_name}.cbm")

    if (i + 1) % 10 == 0:
        print(f"  [{i+1}/{len(eligible_crops)}] done, {time.time()-t_start:.0f}s elapsed")

print(f"All {len(eligible_crops)} per-crop models trained in {time.time()-t_start:.0f}s")

# ---------------------------------------------------------------------------
# 2. Fallback model for the remaining small crops (<500 rows each) -- reuse
#    the existing cleaned GLOBAL model's own test predictions for those rows
#    specifically, so the "overall" number includes them honestly rather than
#    ignoring them.
# ---------------------------------------------------------------------------
small_crop_df = df[~df["Crop"].isin(eligible_crops)].reset_index(drop=True)
print(f"\nFallback (small-crop, pooled) model covers {len(small_crop_df)} rows "
      f"({len(small_crop_df)/len(df)*100:.1f}%) across {small_crop_df['Crop'].nunique()} crops")

X_small = small_crop_df[FEATURES]  # fallback model KEEPS Crop_Encoded (pooled)
y_small = small_crop_df[TARGET]
X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_small, y_small, test_size=0.2, random_state=42)

fallback_model = CatBoostRegressor(iterations=300, learning_rate=0.05, depth=6, random_state=42, verbose=False)
fallback_model.fit(X_train_s, np.log1p(y_train_s))
pred_small = np.expm1(fallback_model.predict(X_test_s))

fallback_r2 = r2_score(y_test_s, pred_small)
fallback_mae = mean_absolute_error(y_test_s, pred_small)
fallback_rmse = np.sqrt(mean_squared_error(y_test_s, pred_small))
print(f"Fallback model: R2={fallback_r2:.4f} MAE={fallback_mae:.3f} RMSE={fallback_rmse:.3f} "
      f"(n_test={len(X_test_s)})")

fallback_model.save_model(f"{OUT_DIR}/catboost_fallback.cbm")

all_test_actual.extend(y_test_s.tolist())
all_test_pred.extend(pred_small.tolist())

# ---------------------------------------------------------------------------
# 3. TRUE OVERALL R2/MAE/RMSE across the ENTIRE test population (every row's
#    own held-out test point, from whichever model actually serves it)
# ---------------------------------------------------------------------------
all_test_actual = np.array(all_test_actual)
all_test_pred = np.array(all_test_pred)

overall_r2 = r2_score(all_test_actual, all_test_pred)
overall_mae = mean_absolute_error(all_test_actual, all_test_pred)
overall_rmse = np.sqrt(mean_squared_error(all_test_actual, all_test_pred))

print("\n" + "=" * 70)
print("TRUE OVERALL RESULT (per-crop architecture, all rows, held-out test)")
print("=" * 70)
print(f"Total test rows: {len(all_test_actual):,}")
print(f"Overall R2:   {overall_r2:.4f}")
print(f"Overall MAE:  {overall_mae:.4f}")
print(f"Overall RMSE: {overall_rmse:.4f}")

results_df = pd.DataFrame(per_crop_results).sort_values("r2", ascending=False)
results_df.to_csv("/home/claude/percrop_test/all_per_crop_results.csv", index=False)

summary = {
    "architecture": "per-crop CatBoost models (>=500 rows/crop) + pooled fallback for smaller crops",
    "n_crop_models": len(eligible_crops),
    "n_crops_covered_by_own_model": len(eligible_crops),
    "pct_rows_with_own_crop_model": float(crop_counts[crop_counts >= MIN_ROWS_FOR_OWN_MODEL].sum() / len(df) * 100),
    "fallback_covers_n_crops": int(small_crop_df["Crop"].nunique()),
    "fallback_covers_pct_rows": float(len(small_crop_df) / len(df) * 100),
    "fallback_r2": float(fallback_r2),
    "fallback_mae": float(fallback_mae),
    "fallback_rmse": float(fallback_rmse),
    "overall_r2": float(overall_r2),
    "overall_mae": float(overall_mae),
    "overall_rmse": float(overall_rmse),
    "overall_n_test": int(len(all_test_actual)),
    "crops_below_r2_0.5": results_df[results_df["r2"] < 0.5]["crop"].tolist(),
    "crops_at_or_above_r2_0.8": results_df[results_df["r2"] >= 0.8]["crop"].tolist(),
    "n_crops_below_r2_0.5": int((results_df["r2"] < 0.5).sum()),
    "n_crops_at_or_above_0.8": int((results_df["r2"] >= 0.8).sum()),
}
with open("/home/claude/percrop_test/per_crop_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("\nSaved all_per_crop_results.csv and per_crop_summary.json")
print(json.dumps(summary, indent=2))
