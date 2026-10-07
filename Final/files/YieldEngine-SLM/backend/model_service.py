"""
model_service.py
------------------
PER-CROP MODEL ARCHITECTURE (v2)
----------------------------------
The single pooled CatBoost model topped out at R2=0.313 because it was
forced to predict Yield across 124 different crop types reported in
incompatible units (tonnes vs. nuts vs. bales) using one regression target.
That's the actual root cause diagnosed in the previous evaluation report --
not something more outlier-cleaning or hyperparameter tuning could fix.

The fix: one CatBoost model PER crop (for the 52 crops with >=500 rows,
covering 96.6% of the data), each trained only on that crop's own rows, so
it never has to relate Rice's tonnes/ha to Coconut's nuts/ha in the same
regression. A pooled "fallback" model (which DOES keep Crop_Encoded) handles
the remaining ~72 low-sample crops.

Real, held-out-test, no-leakage result: overall pooled R2 = 0.878 (vs. 0.313
for the single global model). Per-crop R2 ranges 0.46 (Khesari) to 0.95
(Tapioca) -- reported in full via /api/model-metrics, not just the headline
number, since the headline pooled R2 is mathematically inflated relative to
individual crop accuracy (pooling across very different yield SCALES makes
R2's denominator -- total variance -- much larger, which is a real property
of R2, not a trick; see backend/README.md for the full explanation).

Still never retrains anything at request time; only ever calls .predict()
on already-trained, already-saved models.
"""
import json
import numpy as np
import pandas as pd
import joblib
import shap
from catboost import CatBoostRegressor
from pathlib import Path

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
PERCROP_DIR = ARTIFACTS_DIR / "percrop_models"

# ---------------------------------------------------------------------------
# LOAD REAL ARTIFACTS ONCE AT STARTUP
# ---------------------------------------------------------------------------
FEATURES = joblib.load(ARTIFACTS_DIR / "model_feature_list.joblib")          # full 23, used by fallback model
PER_CROP_FEATURES = [f for f in FEATURES if f != "Crop_Encoded"]              # 22, used by per-crop models
soil_encoder = joblib.load(ARTIFACTS_DIR / "soil_type_label_encoder.joblib")

with open(ARTIFACTS_DIR / "encoding_maps.json") as f:
    ENCODING_MAPS = json.load(f)
with open(ARTIFACTS_DIR / "decoding_maps.json") as f:
    DECODING_MAPS = json.load(f)
with open(ARTIFACTS_DIR / "state_district_map.json") as f:
    STATE_DISTRICT_MAP = json.load(f)
with open(ARTIFACTS_DIR / "soil_type_options.json") as f:
    SOIL_TYPE_OPTIONS = json.load(f)
with open(ARTIFACTS_DIR / "reference_stats.json") as f:
    GLOBAL_REFERENCE_STATS = json.load(f)          # used for fallback-model crops
with open(ARTIFACTS_DIR / "per_crop_reference_stats.json") as f:
    PER_CROP_REFERENCE_STATS = json.load(f)        # used for the 52 crops with their own model
with open(ARTIFACTS_DIR / "dataset_stats.json") as f:
    DATASET_STATS = json.load(f)
with open(ARTIFACTS_DIR / "per_crop_summary.json") as f:
    PER_CROP_SUMMARY = json.load(f)
with open(ARTIFACTS_DIR / "all_per_crop_results.csv") as f:
    _per_crop_df = pd.read_csv(f)
PER_CROP_METRICS_TABLE = _per_crop_df.to_dict(orient="records")

# model_metrics.json now reports the REAL per-crop-architecture numbers
# (rebuilt by finalize_percrop_artifacts.py -- see that script for how these
# were computed, same held-out-test, no-leakage methodology as before).
with open(ARTIFACTS_DIR / "model_metrics.json") as f:
    MODEL_METRICS = json.load(f)

with open(ARTIFACTS_DIR / "eda_stats.json") as f:
    EDA_STATS = json.load(f)

SEASON_OPTIONS = list(ENCODING_MAPS["Season"].keys())
CROP_OPTIONS = sorted(ENCODING_MAPS["Crop"].keys())
STATE_OPTIONS = sorted(ENCODING_MAPS["State_Name"].keys())

CROPS_WITH_OWN_MODEL = set(PER_CROP_SUMMARY.get("crops_at_or_above_r2_0.8", [])) | {
    r["crop"] for r in PER_CROP_METRICS_TABLE
}

# ---------------------------------------------------------------------------
# LAZY-LOADED MODEL REGISTRY (loaded on first use, cached after) -- 53 models
# is cheap enough to eager-load, but lazy keeps startup fast and memory only
# used for crops actually requested.
# ---------------------------------------------------------------------------
_model_cache: dict[str, CatBoostRegressor] = {}
_explainer_cache: dict[str, "shap.TreeExplainer"] = {}


def _safe_filename(crop: str) -> str:
    return crop.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")


def _load_model_for_crop(crop: str):
    """Returns (model, explainer, feature_list, is_per_crop_model)."""
    per_crop_path = PERCROP_DIR / f"catboost_{_safe_filename(crop)}.cbm"
    cache_key = crop if per_crop_path.exists() else "__fallback__"

    if cache_key in _model_cache:
        m = _model_cache[cache_key]
        feats = PER_CROP_FEATURES if cache_key != "__fallback__" else FEATURES
        return m, _explainer_cache[cache_key], feats, cache_key != "__fallback__"

    if per_crop_path.exists():
        m = CatBoostRegressor()
        m.load_model(str(per_crop_path))
        feats = PER_CROP_FEATURES
        is_per_crop = True
    else:
        m = CatBoostRegressor()
        m.load_model(str(PERCROP_DIR / "catboost_fallback.cbm"))
        feats = FEATURES
        is_per_crop = False

    explainer = shap.TreeExplainer(m)
    _model_cache[cache_key] = m
    _explainer_cache[cache_key] = explainer
    return m, explainer, feats, is_per_crop


# ---------------------------------------------------------------------------
# HUMAN-READABLE LABELS
# ---------------------------------------------------------------------------
FEATURE_LABELS = {
    "Area": "Land utilization",
    "Season_Encoded": "Sowing season",
    "Crop_Encoded": "Crop suitability",
    "pH Level": "Soil pH balance",
    "Organic Matter (%)": "Soil organic matter",
    "Nitrogen Content (kg/ha)": "Nitrogen availability",
    "Potassium Content (kg/ha)": "Potassium availability",
    "Soil_Fertility_Index": "Soil fertility",
    "Soil_Type_Encoded": "Soil type suitability",
    "Fertilizer_Consumption": "Fertilizer usage",
    "Pesticide_Consumption": "Pesticide usage",
    "Annual_Rainfall": "Rainfall",
    "Average_Rainfall": "Rainfall",
    "Rainy_Months_Count": "Rainfall",
    "Average_Temperature": "Temperature",
    "Temperature_Range": "Temperature stability",
    "Weather_Index": "Weather favourability",
    "Climate_Index": "Climate suitability",
    "Input_Intensity": "Input intensity",
    "Agricultural_Intensity": "Farming intensity",
}

DISPLAY_EXCLUDE = {"Crop_Year", "State_Name_Encoded", "District_Name_Encoded"}

SIMULATABLE_FEATURES = set(GLOBAL_REFERENCE_STATS.keys()) - {"Area"}

RECOMMENDATION_CATEGORY = {
    "Annual_Rainfall": "rainfall", "Average_Rainfall": "rainfall", "Rainy_Months_Count": "rainfall",
    "Nitrogen Content (kg/ha)": "nitrogen", "Potassium Content (kg/ha)": "potassium",
    "Organic Matter (%)": "organic_matter", "Soil_Fertility_Index": "soil_fertility", "pH Level": "soil_ph",
    "Fertilizer_Consumption": "fertilizer", "Pesticide_Consumption": "pesticide",
    "Average_Temperature": "temperature", "Temperature_Range": "temperature",
    "Weather_Index": "weather", "Climate_Index": "climate",
    "Input_Intensity": "input_intensity", "Agricultural_Intensity": "farming_intensity",
    "Crop_Encoded": "crop_choice", "Season_Encoded": "season_choice",
    "Area": "land_utilization", "Soil_Type_Encoded": "soil_type",
}

RECOMMENDATIONS = {
    "nitrogen":          {"low": "Apply nitrogen fertilizer in split doses"},
    "potassium":         {"low": "Apply potash fertilizer to boost potassium levels"},
    "organic_matter":    {"low": "Add compost or farmyard manure"},
    "soil_fertility":    {"low": "Improve fertility using crop rotation and green manure"},
    "soil_ph":           {"low": "Apply agricultural lime to raise soil pH",
                           "high": "Apply gypsum or organic matter to lower soil pH"},
    "fertilizer":        {"low": "Apply fertilizer according to soil test recommendations"},
    "pesticide":         {"low": "Apply need-based pesticide protection to control losses",
                           "high": "Reduce pesticide use and adopt integrated pest management"},
    "rainfall":          {"low": "Use supplemental irrigation during dry periods"},
    "temperature":       {"low": "Use row covers or greenhouses to retain warmth",
                           "high": "Use mulching and shade nets to reduce heat stress"},
    "weather":           {"low": "Adjust sowing schedule using weather forecasts"},
    "climate":           {"low": "Choose climate-resilient crop varieties"},
    "input_intensity":   {"low": "Increase balanced use of fertilizer, water, and inputs"},
    "farming_intensity": {"low": "Adopt improved agronomic practices to raise farming intensity"},
    "land_utilization":  {"low": "Optimize field spacing and land utilization"},
    "soil_type":         {"low": "Adapt farming practices to your soil type"},
    "crop_choice":       {"low": "Select a crop suitable for local climate and soil"},
    "season_choice":     {"low": "Adjust sowing period according to rainfall pattern"},
}

POSITIVE_PHRASES = {
    "fertilizer": "Good fertilizer usage", "pesticide": "Balanced pesticide usage",
    "rainfall": "Suitable rainfall", "soil_ph": "Healthy soil pH",
    "organic_matter": "Healthy soil organic matter", "nitrogen": "Balanced nitrogen availability",
    "potassium": "Balanced nutrient availability", "soil_fertility": "Healthy soil fertility",
    "temperature": "Suitable temperature", "weather": "Favourable weather",
    "climate": "Favourable climate conditions", "input_intensity": "Good input management",
    "farming_intensity": "Balanced input intensity", "crop_choice": "Good crop selection",
    "season_choice": "Optimal sowing season", "land_utilization": "Efficient land utilization",
    "soil_type": "Suitable soil type",
}


def humanize(feature_name: str) -> str:
    return FEATURE_LABELS.get(
        feature_name, feature_name.replace("_", " ").replace("Encoded", "").strip().capitalize()
    )


# ---------------------------------------------------------------------------
# FEATURE ENGINEERING (same formulas as before -- unchanged by the per-crop
# architecture, only WHICH model consumes the row changes)
# ---------------------------------------------------------------------------
def build_feature_row(farm_input: dict) -> pd.DataFrame:
    row = {}
    row["Crop_Year"] = farm_input["crop_year"]
    row["Area"] = farm_input["area"]
    row["Season_Encoded"] = ENCODING_MAPS["Season"][farm_input["season"]]
    row["Crop_Encoded"] = ENCODING_MAPS["Crop"][farm_input["crop"]]
    row["State_Name_Encoded"] = ENCODING_MAPS["State_Name"][farm_input["state"]]
    row["District_Name_Encoded"] = ENCODING_MAPS["District_Name"][farm_input["district"]]
    row["pH Level"] = farm_input["ph_level"]
    row["Organic Matter (%)"] = farm_input["organic_matter"]
    row["Nitrogen Content (kg/ha)"] = farm_input["nitrogen"]
    row["Potassium Content (kg/ha)"] = farm_input["potassium"]
    row["Soil_Fertility_Index"] = (farm_input["nitrogen"] + farm_input["potassium"]) / 2
    row["Soil_Type_Encoded"] = int(soil_encoder.transform([farm_input["soil_type"]])[0])
    row["Fertilizer_Consumption"] = farm_input["fertilizer_consumption"]
    row["Pesticide_Consumption"] = farm_input["pesticide_consumption"]
    row["Annual_Rainfall"] = farm_input["annual_rainfall"]
    row["Average_Rainfall"] = farm_input["average_rainfall"]
    row["Rainy_Months_Count"] = farm_input["rainy_months_count"]
    row["Average_Temperature"] = farm_input["average_temperature"]
    row["Temperature_Range"] = farm_input["temperature_range"]

    temp_range_safe = row["Temperature_Range"] if row["Temperature_Range"] != 0 else np.nan
    row["Weather_Index"] = (row["Average_Temperature"] * row["Annual_Rainfall"]) / 100
    row["Climate_Index"] = (row["Annual_Rainfall"] / temp_range_safe) if temp_range_safe else 0.0
    row["Input_Intensity"] = row["Fertilizer_Consumption"] + row["Pesticide_Consumption"]
    row["Agricultural_Intensity"] = row["Input_Intensity"] * row["Soil_Fertility_Index"]

    full_row = pd.DataFrame([row])[FEATURES]
    return full_row


def predict_yield_for_crop(crop: str, feature_row_full: pd.DataFrame) -> float:
    model, _, feats, _ = _load_model_for_crop(crop)
    row = feature_row_full[feats]
    raw_pred = model.predict(row)
    return float(np.expm1(raw_pred)[0])


def _reference_stats_for(crop: str) -> dict:
    return PER_CROP_REFERENCE_STATS.get(crop, GLOBAL_REFERENCE_STATS)


def _level(feature: str, value: float, ref_stats: dict) -> str:
    median = ref_stats.get(feature, {}).get("median")
    if median is None:
        return "low"
    return "low" if value <= median else "high"


def get_candidates(feature: str, current_value: float, ref_stats: dict) -> list:
    stats = ref_stats.get(feature)
    if not stats:
        return []
    raw = [stats["p50"], stats["p75"], stats["p90"], stats["top_yield_median"]]
    seen, candidates = set(), []
    for c in raw:
        c = round(float(c), 6)
        if c in seen or np.isclose(c, current_value, rtol=1e-3):
            continue
        seen.add(c)
        candidates.append(c)
    return candidates


def find_best_value(model, feature: str, base_row: pd.DataFrame, candidates: list):
    if not candidates:
        return float(base_row.iloc[0][feature]), False
    trial = base_row.copy()
    best_val = float(base_row.iloc[0][feature])
    best_raw_pred = model.predict(base_row)[0]
    improved = False
    for cand in candidates:
        trial.at[trial.index[0], feature] = cand
        raw_pred = model.predict(trial)[0]
        if raw_pred > best_raw_pred:
            best_raw_pred, best_val = raw_pred, cand
            improved = True
    return best_val, improved


def what_if_simulation(feature_row_full: pd.DataFrame, farm_input: dict, top_n: int = 4) -> dict:
    import shap_service  # lazy import avoids circular dependency
    crop = farm_input["crop"]
    model, explainer, feats, is_per_crop = _load_model_for_crop(crop)
    row = feature_row_full[feats]
    ref_stats = _reference_stats_for(crop)

    explanation = shap_service.get_shap_explanation(feature_row_full, farm_input, top_n=top_n)
    current_pred = explanation["predicted_yield"]

    improved_row = row.copy()
    changes = []
    simulatable = SIMULATABLE_FEATURES & set(ref_stats.keys()) & set(feats)
    for r in explanation["top_negative_raw"]:
        feat, val = r["Feature"], r["Value"]
        if feat in simulatable:
            candidates = get_candidates(feat, val, ref_stats)
            best_val, improved = find_best_value(model, feat, improved_row, candidates)
            if improved:
                improved_row.at[improved_row.index[0], feat] = best_val
                changes.append({
                    "feature": feat, "label": humanize(feat),
                    "before": float(val), "after": float(best_val),
                })

    improved_pred = float(np.expm1(model.predict(improved_row))[0])
    pct_change = ((improved_pred - current_pred) / current_pred * 100) if current_pred != 0 else 0.0

    return {
        "current_yield": current_pred,
        "improved_yield": improved_pred,
        "percentage_improvement": pct_change,
        "changed_parameters": changes,
    }
