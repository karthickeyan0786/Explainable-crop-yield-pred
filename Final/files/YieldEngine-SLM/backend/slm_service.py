"""
slm_service.py
-----------------
Converts the structured, grounded SHAP payload from shap_service.py into a
natural-language explanation using a Small Language Model.

GROUNDING STRATEGY (anti-hallucination):
The SLM is given ONLY the structured facts computed by shap_service.py and
is explicitly instructed to explain ONLY those facts -- never invent
numbers, crops, weather data, or recommendations not present in the input.
This is "prompt-level grounding": strong mitigation, not an absolute
guarantee (see IEEE novelty doc for honest discussion of this limitation).

PROVIDERS (in priority order):
  1. Ollama (local SLM: Phi-3 Mini / Gemma 2B / TinyLlama) -- PRIMARY, per
     your requirement to avoid cloud APIs. Requires Ollama installed and a
     model pulled (`ollama pull phi3:mini`) in YOUR deployment environment.
  2. Template-based deterministic fallback -- ALWAYS available, zero
     external dependencies, fully tested in this repo.

HONESTY NOTE: This sandbox's network policy blocks ollama.com entirely
(confirmed via curl -I -> 403 host_not_allowed), so Ollama could not be
installed or tested live here. The integration code follows the official
`ollama` Python client's documented API and will work once you run
`ollama serve` + `ollama pull phi3:mini` in your own environment. The
template fallback path IS fully tested.
"""
import logging
import os

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi3:mini")

_ollama_client = None


def _get_ollama_client():
    global _ollama_client
    if _ollama_client is not None:
        return _ollama_client
    try:
        import ollama
        client = ollama.Client(host=OLLAMA_HOST)
        client.list()
        _ollama_client = client
        return _ollama_client
    except Exception as e:
        logger.info("Ollama not reachable (%s) -- using template fallback.", e)
        return None


def _build_grounded_prompt(shap_payload: dict, farm_input: dict, lang_name: str) -> str:
    positive = "; ".join(f["label"] for f in shap_payload["positive_factors"]) or "none identified"
    negative = "; ".join(f["label"] for f in shap_payload["negative_factors"]) or "none identified"
    actions = "; ".join(r["action"] for r in shap_payload["recommendations"]) or "none needed"

    return f"""You are explaining an AI crop yield prediction to a farmer, in {lang_name}.

STRICT GROUNDING RULES:
- Use ONLY the facts given below. Do not add any crop, weather, price, or
  yield information that is not explicitly listed here.
- Do not invent new recommendations. Only rephrase the ones given.
- Do not mention percentages, dates, or numbers not given below.
- Do not mention "SHAP", "the model", "AI", or any technical/ML terms.

FACTS (grounding data -- do not go beyond this):
Crop: {farm_input.get('crop')}
Season: {farm_input.get('season')}
Predicted yield: {shap_payload['predicted_yield']:.2f} tonnes per hectare
Helping factors: {positive}
Limiting factors: {negative}
Recommended actions: {actions}

TASK: Write a short (4-6 sentence), warm, simple, spoken-style explanation
in {lang_name} using ONLY the facts above. No bullet points, no headings.
Speak directly to the farmer. End with one encouraging sentence."""


def _template_fallback(shap_payload: dict, farm_input: dict, lang: str) -> str:
    """Deterministic, fully offline, fully tested narrative. Translates
    every factor label and recommendation action via translations.py's
    category-keyed dictionaries so the output is genuinely in the target
    language, not English content wrapped in local sentence structure."""
    from translations import (
        CROP_NAMES_I18N, SEASON_NAMES_I18N, FEATURE_LABELS_I18N,
        POSITIVE_PHRASES_I18N, RECOMMENDATIONS_I18N, get_translated,
    )
    import model_service as ms

    yield_val = shap_payload["predicted_yield"]
    crop = get_translated(CROP_NAMES_I18N, farm_input.get("crop", ""), lang)
    season = get_translated(SEASON_NAMES_I18N, farm_input.get("season", ""), lang)

    def translate_positive(f):
        cat = ms.RECOMMENDATION_CATEGORY.get(f["feature"], f["feature"])
        return get_translated(POSITIVE_PHRASES_I18N, cat, lang)

    def translate_negative(f):
        return get_translated(FEATURE_LABELS_I18N, f["feature"], lang)

    def translate_action(r):
        for cat, entry in ms.RECOMMENDATIONS.items():
            if r["action"] in entry.values():
                level = "high" if r["action"] == entry.get("high") else "low"
                return get_translated(RECOMMENDATIONS_I18N, cat, lang, sub_key=level)
        return r["action"]

    positive_labels = [translate_positive(f) for f in shap_payload["positive_factors"]]
    negative_labels = [translate_negative(f) for f in shap_payload["negative_factors"]]
    actions = [translate_action(r) for r in shap_payload["recommendations"]]

    templates = {
        "en": {
            "intro": f"For your {crop} field in the {season} season, the expected yield is about {yield_val:.2f} tonnes per hectare.",
            "positive_lead": "This is helped by: " + ", ".join(positive_labels) + ".",
            "negative_lead": "This is being held back by: " + ", ".join(negative_labels) + ".",
            "actions_lead": "To improve this, you could: " + "; ".join(actions) + ".",
            "closing": "Even small changes to these factors can meaningfully raise your yield.",
        },
        "ta": {
            "intro": f"உங்கள் {season} பருவ {crop} பயிருக்கு, எதிர்பார்க்கப்படும் மகசூல் ஏறத்தாழ ஹெக்டேருக்கு {yield_val:.2f} டன்கள்.",
            "positive_lead": "இதற்கு உதவுவது: " + ", ".join(positive_labels) + ".",
            "negative_lead": "இதைத் தடுப்பது: " + ", ".join(negative_labels) + ".",
            "actions_lead": "இதை மேம்படுத்த, நீங்கள் இதைச் செய்யலாம்: " + "; ".join(actions) + ".",
            "closing": "இந்த காரணிகளில் சிறிய மாற்றங்கள் கூட உங்கள் மகசூலை கணிசமாக அதிகரிக்கும்.",
        },
        "hi": {
            "intro": f"आपके {season} मौसम के {crop} खेत के लिए, अनुमानित उपज लगभग {yield_val:.2f} टन प्रति हेक्टेयर है।",
            "positive_lead": "इसमें मदद कर रहा है: " + ", ".join(positive_labels) + "।",
            "negative_lead": "इसे रोक रहा है: " + ", ".join(negative_labels) + "।",
            "actions_lead": "इसे सुधारने के लिए, आप यह कर सकते हैं: " + "; ".join(actions) + "।",
            "closing": "इन कारकों में छोटे बदलाव भी आपकी उपज को उल्लेखनीय रूप से बढ़ा सकते हैं।",
        },
    }
    t = templates.get(lang, templates["en"])
    parts = [t["intro"]]
    if positive_labels:
        parts.append(t["positive_lead"])
    if negative_labels:
        parts.append(t["negative_lead"])
    if actions:
        parts.append(t["actions_lead"])
    parts.append(t["closing"])
    return " ".join(parts)


def generate_explanation(shap_payload: dict, farm_input: dict, lang: str = "en") -> dict:
    """Grounded SLM explanation. `shap_payload` must be the output of
    shap_service.get_shap_explanation() -- this function never computes its
    own facts, only phrases the ones it's given."""
    from translations import SUPPORTED_LANGUAGES
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"
    lang_name = SUPPORTED_LANGUAGES[lang]

    client = _get_ollama_client()
    explanation_text = None
    source = "template_fallback"
    model_used = "template"

    if client is not None:
        try:
            prompt = _build_grounded_prompt(shap_payload, farm_input, lang_name)
            response = client.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3},
            )
            explanation_text = response["message"]["content"].strip()
            source = "ollama"
            model_used = OLLAMA_MODEL
        except Exception as e:
            logger.warning("Ollama call failed, using template fallback: %s", e)
            explanation_text = None

    if not explanation_text:
        explanation_text = _template_fallback(shap_payload, farm_input, lang)
        source = "template_fallback"
        model_used = "template"

    return {
        "language": lang,
        "language_name": lang_name,
        "explanation": explanation_text,
        "source": source,
        "model": model_used,
    }
