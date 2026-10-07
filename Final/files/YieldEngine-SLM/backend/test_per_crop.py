import numpy as np
import pandas as pd
pd.set_option('future.infer_string', False)
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from catboost import CatBoostRegressor
import joblib
import time

ART_DIR = "/home/claude/yield-engine/backend/artifacts"
FEATURES = joblib.load(f"{ART_DIR}/model_feature_list.joblib")
# Crop_Encoded is meaningless within a single-crop model (constant column) --
# drop it for per-crop models, same as you'd do for any dataset with a
# zero-variance feature.
PER_CROP_FEATURES = [f for f in FEATURES if f != "Crop_Encoded"]
TARGET = "Yield"

df = pd.read_csv("/home/claude/percrop_test/cleaned_df.csv")

TOP_CROPS = ["Rice", "Maize", "Wheat", "Sugarcane", "Potato", "Onion", "Groundnut"]

results = []
for crop in TOP_CROPS:
    sub = df[df["Crop"] == crop].reset_index(drop=True)
    X = sub[PER_CROP_FEATURES]
    y = sub[TARGET]
    if len(sub) < 200:
        continue
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    t0 = time.time()
    model = CatBoostRegressor(iterations=300, learning_rate=0.05, depth=6, random_state=42, verbose=False)
    model.fit(X_train, np.log1p(y_train))
    pred = np.expm1(model.predict(X_test))

    r2 = r2_score(y_test, pred)
    mae = mean_absolute_error(y_test, pred)
    rmse = np.sqrt(mean_squared_error(y_test, pred))

    results.append({
        "crop": crop, "n_rows": len(sub), "n_train": len(X_train), "n_test": len(X_test),
        "r2": r2, "mae": mae, "rmse": rmse,
        "yield_median": float(y.median()), "yield_std": float(y.std()),
        "train_time_s": time.time() - t0,
    })
    print(f"{crop:15s} | n={len(sub):6d} | R2={r2:.4f} | MAE={mae:.3f} | RMSE={rmse:.3f} | "
          f"median_yield={y.median():.2f} | std={y.std():.2f} | {time.time()-t0:.1f}s")

results_df = pd.DataFrame(results)
results_df.to_csv("/home/claude/percrop_test/per_crop_results.csv", index=False)
print("\nSaved per_crop_results.csv")
print("\nMean R2 across tested crops:", results_df["r2"].mean())
