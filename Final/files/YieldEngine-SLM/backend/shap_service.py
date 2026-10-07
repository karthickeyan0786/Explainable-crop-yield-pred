"""
shap_service.py
------------------
Responsible ONLY for turning a trained CatBoost model + one feature row into
structured SHAP explanation data. Does not generate any natural-language
text itself -- that is slm_service.py's job. This separation is what makes
the SLM layer "grounded": the SLM only ever receives the exact structured
facts computed here, and is instructed never to introduce information
beyond what's given.

Deterministic, rule-based recommendation actions are still generated here
(unchanged logic) -- the SLM's role is to phrase these naturally and in the
requested language, not invent new recommendations. Recommendation logic
stays deterministic/auditable; the SLM only handles natural-language
presentation of already-vetted facts.
"""
import numpy as np
import pandas as pd

import model_service as ms


def get_shap_explanation(feature_row_full: pd.DataFrame, farm_input: dict, top_n: int = 4) -> dict:
    """
    Returns the grounded, structured explanation payload:
      {
        "predicted_yield": 1.25,
        "positive_factors": [{"feature": "...", "label": "...", "shap_value": 0.12}, ...],
        "negative_factors": [{"feature": "...", "label": "...", "shap_value": -0.18, "context": "..."}, ...],
        "recommendations": [{"issue": "...", "action": "...", "reason": "..."}],
        "model_used": "per_crop" | "fallback_pooled",
      }
    This is exactly the shape the SLM prompt in slm_service.py is built
    from -- nothing else is ever passed to the language model.
    """
    crop = farm_input["crop"]
    model, explainer, feats, is_per_crop = ms._load_model_for_crop(crop)
    row = feature_row_full[feats]

    shap_row = explainer(row)
    shap_vals = shap_row.values[0]
    current_pred = float(np.expm1(model.predict(row))[0])

    contrib_df = pd.DataFrame({"Feature": feats, "Value": row.iloc[0].values, "SHAP": shap_vals})
    contrib_df = contrib_df[~contrib_df["Feature"].isin(ms.DISPLAY_EXCLUDE)]

    negative = contrib_df[contrib_df["SHAP"] < 0].sort_values("SHAP")
    positive = contrib_df[contrib_df["SHAP"] > 0].sort_values("SHAP", ascending=False)

    def dedupe(df, limit):
        seen, rows = set(), []
        for _, r in df.iterrows():
            cat = ms.RECOMMENDATION_CATEGORY.get(r["Feature"], r["Feature"])
            if cat in seen:
                continue
            seen.add(cat)
            rows.append(r)
            if len(rows) >= limit:
                break
        return rows

    top_negative = dedupe(negative, top_n)
    top_positive = dedupe(positive, top_n)

    def factor_context(feat):
        decoded_key = {"Crop_Encoded": "crop", "Season_Encoded": "season",
                       "Soil_Type_Encoded": "soil_type"}.get(feat)
        if decoded_key:
            return f"Current {decoded_key.replace('_', ' ')}: {farm_input[decoded_key]}"
        return None

    positive_factors = []
    for r in top_positive:
        cat = ms.RECOMMENDATION_CATEGORY.get(r["Feature"], r["Feature"])
        positive_factors.append({
            "feature": r["Feature"],
            "label": ms.POSITIVE_PHRASES.get(cat, ms.humanize(r["Feature"])),
            "shap_value": float(r["SHAP"]),
        })

    negative_factors = []
    for r in top_negative:
        negative_factors.append({
            "feature": r["Feature"],
            "label": ms.humanize(r["Feature"]),
            "context": factor_context(r["Feature"]),
            "shap_value": float(r["SHAP"]),
        })

    ref_stats = ms._reference_stats_for(crop)
    simulatable = ms.SIMULATABLE_FEATURES & set(ref_stats.keys())

    recommendations = []
    seen_categories = set()
    for r in top_negative:
        feat = r["Feature"]
        cat = ms.RECOMMENDATION_CATEGORY.get(feat, feat)
        if cat in seen_categories:
            continue
        seen_categories.add(cat)
        entry = ms.RECOMMENDATIONS.get(cat)
        if entry is not None:
            level = ms._level(feat, r["Value"], ref_stats) if feat in simulatable else "low"
            recommendations.append({
                "issue": ms.humanize(feat),
                "action": entry.get(level, entry.get("low")),
                "reason": f"The explainability model identified {ms.humanize(feat).lower()} as a negative contributor.",
            })

    return {
        "predicted_yield": current_pred,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "recommendations": recommendations,
        "top_negative_raw": top_negative,
        "model_used": "per_crop" if is_per_crop else "fallback_pooled",
    }
