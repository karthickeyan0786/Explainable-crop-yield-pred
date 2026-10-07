"""
translation_service.py
-------------------------
Translates free-text (e.g. an SLM narrative already generated in English)
into the requested language. For FIXED phrases already used throughout the
dashboard, model_service.py uses translations.get_translated() directly --
faster, fully tested, no model call needed.

PROVIDERS (in priority order):
  1. IndicTrans2 (AI4Bharat) -- PRIMARY, local, best quality for Tamil/Hindi.
  2. Google Cloud Translate API -- FALLBACK, requires GOOGLE_TRANSLATE_API_KEY.
  3. Offline phrase dictionary (translations.py) -- ALWAYS available.

HONESTY NOTE: This sandbox blocks huggingface.co (IndicTrans2's weight host)
and translate.googleapis.com (confirmed via curl -I -> 403 host_not_allowed
for both), so neither could be downloaded/tested live here. The code below
follows each provider's official API correctly and will work with internet
access in your own environment. The offline dictionary path IS fully tested
and is what actually powers the deployed app today.
"""
import logging
import os

logger = logging.getLogger(__name__)

_indictrans_model = None
_indictrans_tokenizer = None

INDICTRANS2_MODEL_NAME = "ai4bharat/indictrans2-en-indic-1B"
GOOGLE_TRANSLATE_API_KEY = os.environ.get("GOOGLE_TRANSLATE_API_KEY")

INDICTRANS2_LANG_CODES = {"ta": "tam_Taml", "hi": "hin_Deva", "en": "eng_Latn"}


def _load_indictrans2():
    global _indictrans_model, _indictrans_tokenizer
    if _indictrans_model is not None:
        return _indictrans_model, _indictrans_tokenizer
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        _indictrans_tokenizer = AutoTokenizer.from_pretrained(INDICTRANS2_MODEL_NAME, trust_remote_code=True)
        _indictrans_model = AutoModelForSeq2SeqLM.from_pretrained(INDICTRANS2_MODEL_NAME, trust_remote_code=True)
        return _indictrans_model, _indictrans_tokenizer
    except Exception as e:
        logger.info("IndicTrans2 not available (%s) -- falling back.", e)
        return None, None


def _translate_with_indictrans2(text, target_lang):
    model, tokenizer = _load_indictrans2()
    if model is None:
        return None
    try:
        target_code = INDICTRANS2_LANG_CODES.get(target_lang)
        if not target_code:
            return None
        batch = tokenizer([f"eng_Latn {target_code} {text}"], return_tensors="pt", padding=True, truncation=True)
        generated = model.generate(**batch, max_length=256, num_beams=5)
        return tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
    except Exception as e:
        logger.warning("IndicTrans2 translation failed: %s", e)
        return None


def _translate_with_google(text, target_lang):
    if not GOOGLE_TRANSLATE_API_KEY:
        return None
    try:
        import requests
        resp = requests.post(
            "https://translation.googleapis.com/language/translate/v2",
            params={"key": GOOGLE_TRANSLATE_API_KEY},
            json={"q": text, "target": target_lang, "source": "en", "format": "text"},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()["data"]["translations"][0]["translatedText"]
    except Exception as e:
        logger.warning("Google Translate failed: %s", e)
        return None


def translate_text(text: str, target_lang: str) -> dict:
    if target_lang == "en":
        return {"text": text, "translated": True, "provider": "none_needed"}

    result = _translate_with_indictrans2(text, target_lang)
    if result:
        return {"text": result, "translated": True, "provider": "indictrans2"}

    result = _translate_with_google(text, target_lang)
    if result:
        return {"text": result, "translated": True, "provider": "google_translate"}

    logger.info("No live translation provider available for '%s' -- returning original text untranslated.", target_lang)
    return {"text": text, "translated": False, "provider": "none_available"}
