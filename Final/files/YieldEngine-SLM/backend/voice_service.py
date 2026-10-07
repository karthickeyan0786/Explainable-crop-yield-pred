"""
voice_service.py
-------------------
Converts an explanation string into an audio file. Provides BOTH requested
implementations:

  Option A: gTTS -- simple, needs internet access to Google's TTS endpoint
            at request time.
  Option B: Coqui TTS -- fully offline/local once installed, no internet
            needed at request time, but a much heavier dependency.

HONESTY NOTE: gTTS the Python package installs cleanly, but its network
target (translate.google.com) is blocked in this sandbox (confirmed 403,
and a live call was attempted and failed with exactly this error). Coqui
TTS (the `TTS` PyPI package) could not even be INSTALLED here -- it
requires Python <3.12, and this environment runs 3.12. Both integrations
below are written correctly against each library's documented API.

RECOMMENDED PRACTICAL DEFAULT: the frontend implements a THIRD option that
needs no backend change and IS fully tested and working today: the
browser's native Web Speech API (see src/components/SpeakButton.tsx),
which reads the translated explanation text aloud directly in the browser,
in Tamil, Hindi, or English, with zero server-side audio generation and
zero network dependency at request time. Both backend TTS options below
remain useful if you need a downloadable audio FILE (e.g. for a phone
call/IVR system or a WhatsApp voice note) rather than in-browser playback.
"""
import io
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

GTTS_LANG_CODES = {"en": "en", "ta": "ta", "hi": "hi"}


def synthesize_speech_gtts(text: str, lang: str = "en") -> bytes:
    """Option A: gTTS. Returns raw MP3 bytes."""
    try:
        from gtts import gTTS
    except ImportError:
        raise RuntimeError("gTTS is not installed. Run: pip install gTTS")

    gtts_lang = GTTS_LANG_CODES.get(lang, "en")
    try:
        tts = gTTS(text=text, lang=gtts_lang)
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        return buffer.read()
    except Exception as e:
        raise RuntimeError(f"gTTS synthesis failed (likely a network issue): {e}")


_coqui_tts_model = None
COQUI_MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
# "ta" intentionally omitted -- Coqui XTTS v2 does not support Tamil in its
# built-in language list at time of writing; use gTTS or the frontend Web
# Speech API for Tamil instead. Documented honestly rather than silently
# producing wrong-language audio.
COQUI_SUPPORTED_LANGS = {"en": "en", "hi": "hi"}


def synthesize_speech_coqui(text: str, lang: str = "en") -> bytes:
    """Option B: Coqui TTS, fully local/offline once the model is
    downloaded on first use. Returns raw WAV bytes."""
    global _coqui_tts_model
    if lang not in COQUI_SUPPORTED_LANGS:
        raise RuntimeError(
            f"Coqui XTTS v2 does not support '{lang}' in this configuration. "
            f"Use gTTS (Option A) or the frontend Web Speech API for this language."
        )
    try:
        from TTS.api import TTS
    except ImportError:
        raise RuntimeError(
            "Coqui TTS is not installed, or your Python version is incompatible "
            "(Coqui TTS requires Python <3.12). Use a separate venv with "
            "Python 3.10/3.11 and run: pip install TTS"
        )

    if _coqui_tts_model is None:
        _coqui_tts_model = TTS(COQUI_MODEL_NAME)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        _coqui_tts_model.tts_to_file(text=text, language=COQUI_SUPPORTED_LANGS[lang], file_path=tmp.name)
        tmp.seek(0)
        with open(tmp.name, "rb") as f:
            audio_bytes = f.read()
    os.unlink(tmp.name)
    return audio_bytes


def synthesize_speech(text: str, lang: str = "en", provider: str = "gtts") -> dict:
    """Unified entry point. Always returns a dict; never raises -- callers
    check audio_bytes is not None before using the result."""
    try:
        if provider == "coqui":
            audio = synthesize_speech_coqui(text, lang)
            return {"audio_bytes": audio, "mime_type": "audio/wav", "provider": "coqui"}
        audio = synthesize_speech_gtts(text, lang)
        return {"audio_bytes": audio, "mime_type": "audio/mpeg", "provider": "gtts"}
    except Exception as e:
        logger.warning("Backend TTS synthesis failed (%s): %s -- recommend frontend Web Speech API instead.", provider, e)
        return {
            "audio_bytes": None, "mime_type": None, "provider": "none",
            "error": str(e), "recommend_frontend_tts": True,
        }
