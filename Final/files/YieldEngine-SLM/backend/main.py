"""
main.py
--------
FastAPI backend for the Yield Engine dashboard.

ARCHITECTURE:
  Farmer Input -> model_service (feature engineering + per-crop CatBoost)
               -> shap_service (grounded, structured SHAP explanation)
               -> slm_service (natural-language explanation, any language)
               -> translation_service (translates free text when needed)
               -> voice_service (text -> speech, optional backend audio file)
               -> React Dashboard

Existing endpoints (/health, /api/options, /api/dataset-info,
/api/model-metrics, /api/predict, /api/what-if, /api/eda) are UNCHANGED in
response shape -- the live dashboard already depends on them, so they are
preserved rather than rewritten. /api/predict's internal implementation now
calls shap_service.get_shap_explanation() instead of the old
model_service.explain_and_recommend() (moved there during the service-layer
split), but the response shape to the frontend is identical.

NEW endpoints for the SLM/multilingual/voice layer:
  POST /api/explain    -- grounded SLM explanation in the requested language
  POST /api/voice        -- text-to-speech audio file (gTTS or Coqui)
  GET  /api/languages    -- supported language list

Run with:
    uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import model_service as ms
import shap_service
import slm_service
import translation_service
import voice_service
from translations import SUPPORTED_LANGUAGES

app = FastAPI(title="Yield Engine API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class FarmInput(BaseModel):
    state: str
    district: str
    crop: str
    season: str
    crop_year: int = Field(ge=1997, le=2035)
    area: float = Field(gt=0)
    soil_type: str
    ph_level: float = Field(ge=0, le=14)
    organic_matter: float = Field(ge=0)
    nitrogen: float = Field(ge=0)
    potassium: float = Field(ge=0)
    fertilizer_consumption: float = Field(ge=0)
    pesticide_consumption: float = Field(ge=0)
    annual_rainfall: float = Field(ge=0)
    average_rainfall: float = Field(ge=0)
    rainy_months_count: float = Field(ge=0, le=12)
    average_temperature: float
    temperature_range: float = Field(ge=0)
    lang: str = Field(default="en", description="Language code: en, ta, or hi")


class VoiceRequest(BaseModel):
    text: str
    lang: str = Field(default="en")
    provider: str = Field(default="gtts", description="'gtts' or 'coqui'")


@app.get("/health")
def health():
    try:
        _, _, _, _ = ms._load_model_for_crop("Rice")
        model_loaded = True
    except Exception:
        model_loaded = False
    return {
        "status": "ok" if model_loaded else "degraded",
        "model": ms.MODEL_METRICS.get("model_name", "CatBoost"),
        "architecture": ms.MODEL_METRICS.get("architecture", "single model"),
        "model_loaded": model_loaded,
        "n_crop_specific_models": ms.MODEL_METRICS.get("n_crop_specific_models"),
        "feature_count": len(ms.FEATURES),
        "slm_ollama_reachable": slm_service._get_ollama_client() is not None,
    }


@app.get("/api/options")
def get_options():
    return {
        "states": ms.STATE_OPTIONS,
        "state_district_map": ms.STATE_DISTRICT_MAP,
        "crops": ms.CROP_OPTIONS,
        "seasons": ms.SEASON_OPTIONS,
        "soil_types": ms.SOIL_TYPE_OPTIONS,
    }


@app.get("/api/dataset-info")
def dataset_info():
    return ms.DATASET_STATS


@app.get("/api/model-metrics")
def model_metrics():
    return ms.MODEL_METRICS


@app.get("/api/languages")
def languages():
    return {"supported_languages": SUPPORTED_LANGUAGES}


@app.post("/api/predict")
def predict(farm_input: FarmInput):
    try:
        payload = farm_input.model_dump()
        payload.pop("lang", None)
        feature_row = ms.build_feature_row(payload)
        result = shap_service.get_shap_explanation(feature_row, payload)
        result.pop("top_negative_raw", None)
        return result
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Unrecognized value: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/explain")
def explain(farm_input: FarmInput):
    """Pipeline: features -> SHAP (grounding facts) -> SLM (natural
    language, in `lang`). Returns {"language": "...", "explanation": "..."}
    plus source/model metadata for UI transparency."""
    try:
        payload = farm_input.model_dump()
        lang = payload.pop("lang", "en")
        feature_row = ms.build_feature_row(payload)
        shap_payload = shap_service.get_shap_explanation(feature_row, payload)
        shap_payload.pop("top_negative_raw", None)
        result = slm_service.generate_explanation(shap_payload, payload, lang=lang)
        return {
            "language": result["language_name"],
            "explanation": result["explanation"],
            "source": result["source"],
            "model": result["model"],
        }
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Unrecognized value: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice")
def voice(request: VoiceRequest):
    """Returns a raw audio file. If backend TTS fails for any reason,
    returns 503 with recommend_frontend_tts=True so the frontend can fall
    back to the browser's Web Speech API instead of a hard error."""
    result = voice_service.synthesize_speech(request.text, lang=request.lang, provider=request.provider)
    if result["audio_bytes"] is None:
        raise HTTPException(
            status_code=503,
            detail={"error": result.get("error", "TTS synthesis unavailable"), "recommend_frontend_tts": True},
        )
    return Response(content=result["audio_bytes"], media_type=result["mime_type"])


@app.post("/api/what-if")
def what_if(farm_input: FarmInput):
    try:
        payload = farm_input.model_dump()
        payload.pop("lang", None)
        feature_row = ms.build_feature_row(payload)
        return ms.what_if_simulation(feature_row, payload)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Unrecognized value: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/eda")
def eda_stats():
    return ms.EDA_STATS
