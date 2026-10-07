"""
build_eda_stats.py
--------------------
Computes REAL exploratory-data-analysis statistics from the actual cleaned
dataset, to replace the fabricated placeholder numbers that were in
EdaView.tsx (hardcoded fake crop stats, fake correlations, a fake "N=6,030"
sample size -- none of which came from the real data).
"""
import json
import numpy as np
import pandas as pd
pd.set_option('future.infer_string', False)
import joblib

RAW_DIR = "/mnt/user-data/uploads"
ART_DIR = "/home/claude/yield-engine/backend/artifacts"

FEATURES = joblib.load(f"{ART_DIR}/model_feature_list.joblib")
TARGET = "Yield"

df = pd.read_csv(f"{RAW_DIR}/Final_Crop_Yield_Dataset.csv")
soil_encoder = joblib.load(f"{ART_DIR}/soil_type_label_encoder.joblib")
if "Soil_Type_Encoded" not in df.columns and "Soil Type" in df.columns:
    df["Soil_Type_Encoded"] = soil_encoder.transform(df["Soil Type"].astype(str))

model_ready_df = df.dropna(subset=FEATURES + [TARGET]).reset_index(drop=True)

# same cleaning rule used for the deployed model
sentinel_mask = model_ready_df["Production"] == 729.0
def crop_far_outlier_mask(group):
    q1, q3 = group.quantile(0.25), group.quantile(0.75)
    iqr = q3 - q1
    return group > (q3 + 3 * iqr)
per_crop_outlier_mask = model_ready_df.groupby("Crop")[TARGET].transform(crop_far_outlier_mask)
cleaned_df = model_ready_df[~(sentinel_mask | per_crop_outlier_mask)].reset_index(drop=True)

print("Cleaned dataset shape:", cleaned_df.shape)

# ---------------------------------------------------------------------------
# 1. Data coverage by state (record count -- NOT a production/area volume)
# ---------------------------------------------------------------------------
# NOTE: Both Production (mixed units across crops, e.g. Coconut in nuts) AND
# Area (known extreme outliers, up to 8.58M "hectares" for single rows --
# see the What-If simulator exclusion in model_service.py) are unreliable to
# SUM across all rows for a state. Record count is the only aggregate here
# that's immune to both problems, so that's what's actually charted -- this
# is honestly labeled as "data coverage," not a production/area claim.
records_by_state = cleaned_df["State_Name"].value_counts()
total_records = records_by_state.sum()
top_states = [
    {"state": state, "record_count": int(cnt), "pct_of_total": float(cnt / total_records * 100)}
    for state, cnt in records_by_state.head(10).items()
]
top3_pct = float(records_by_state.head(3).sum() / total_records * 100)

# ---------------------------------------------------------------------------
# 2. Data coverage among states, chart-ready (top 8 states, for bar chart)
# ---------------------------------------------------------------------------
crop_production_chart = [
    {"state": state, "record_count": int(cnt)} for state, cnt in records_by_state.head(8).items()
]

# ---------------------------------------------------------------------------
# 3. Feature correlation with Yield (real Pearson correlation)
# ---------------------------------------------------------------------------
numeric_features = [
    "Area", "pH Level", "Organic Matter (%)", "Nitrogen Content (kg/ha)",
    "Potassium Content (kg/ha)", "Soil_Fertility_Index", "Fertilizer_Consumption",
    "Pesticide_Consumption", "Annual_Rainfall", "Average_Rainfall", "Rainy_Months_Count",
    "Average_Temperature", "Temperature_Range", "Weather_Index", "Climate_Index",
    "Input_Intensity", "Agricultural_Intensity",
]
correlations = cleaned_df[numeric_features + [TARGET]].corr()[TARGET].drop(TARGET).sort_values(key=abs, ascending=False)
correlation_table = [{"feature": f, "correlation": float(v)} for f, v in correlations.head(8).items()]

# ---------------------------------------------------------------------------
# 4. Area vs Production scatter sample -- restricted to ONE crop (Rice) so
#    the relationship is honestly interpretable. Plotting all 124 crops
#    together would mix incompatible Production units on one axis (same
#    issue as #1 above), making any visual "trend" meaningless.
# ---------------------------------------------------------------------------
rice_df = cleaned_df[cleaned_df["Crop"] == "Rice"]
scatter_sample = rice_df[["Area", "Production"]].sample(n=min(300, len(rice_df)), random_state=42)
scatter_points = [
    {"area": float(a), "production": float(p)}
    for a, p in zip(scatter_sample["Area"], scatter_sample["Production"])
]
scatter_correlation = float(rice_df[["Area", "Production"]].corr().iloc[0, 1])

# ---------------------------------------------------------------------------
# 5. Yield distribution histogram (real bin counts, post-cleaning)
# ---------------------------------------------------------------------------
yield_capped = cleaned_df[TARGET].clip(upper=cleaned_df[TARGET].quantile(0.99))  # for readable bins
counts, bin_edges = np.histogram(yield_capped, bins=12)
yield_histogram = [
    {"bin_start": float(bin_edges[i]), "bin_end": float(bin_edges[i + 1]), "count": int(counts[i])}
    for i in range(len(counts))
]

# ---------------------------------------------------------------------------
# 6. Rainfall histogram (real)
# ---------------------------------------------------------------------------
counts_r, bin_edges_r = np.histogram(cleaned_df["Annual_Rainfall"], bins=12)
rainfall_histogram = [
    {"bin_start": float(bin_edges_r[i]), "bin_end": float(bin_edges_r[i + 1]), "count": int(counts_r[i])}
    for i in range(len(counts_r))
]

eda_stats = {
    "n_rows": int(len(cleaned_df)),
    "n_crops": int(cleaned_df["Crop"].nunique()),
    "n_states": int(cleaned_df["State_Name"].nunique()),
    "top_producing_states": top_states,
    "top3_states_pct_of_total": top3_pct,
    "crop_production_by_state_chart": crop_production_chart,
    "yield_correlations": correlation_table,
    "area_production_scatter_sample": scatter_points,
    "area_production_scatter_crop": "Rice",
    "area_production_scatter_correlation": scatter_correlation,
    "yield_histogram": yield_histogram,
    "rainfall_histogram": rainfall_histogram,
}

with open(f"{ART_DIR}/eda_stats.json", "w") as f:
    json.dump(eda_stats, f, indent=2)

print("Saved eda_stats.json")
print(f"Most-represented state: {top_states[0]['state']} ({top_states[0]['record_count']:,} records, {top_states[0]['pct_of_total']:.1f}%)")
print(f"Top 3 states = {top3_pct:.1f}% of all records")
print(f"Strongest yield correlation: {correlation_table[0]['feature']} (r={correlation_table[0]['correlation']:.3f})")
