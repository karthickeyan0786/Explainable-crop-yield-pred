# Translation Workflow

## Two Different Translation Needs, Two Different Mechanisms

This system has two distinct kinds of text that need translating, handled
differently:

1. **Fixed phrases** (factor labels, recommendation actions, crop/season
   names) — a known, finite vocabulary. Handled by
   `translations.py`'s dictionaries + `get_translated()`, looked up
   directly by `model_service.py` and `slm_service.py`. Fast, zero
   external dependency, fully tested.
2. **Free-form text** (an SLM narrative that was generated only in
   English, or any other dynamic string needing translation after the
   fact) — handled by `translation_service.py`, which tries IndicTrans2,
   then Google Translate, then returns the text untranslated with a clear
   flag rather than silently failing.

In the current pipeline, `slm_service.py` generates its narrative directly
in the target language (both the Ollama prompt and the template fallback
take `lang` as a parameter), so `translation_service.py` is not on the
critical path today — it exists as the documented, ready-to-use mechanism
requested for translating any other free text this system might need to
handle in the future (e.g. if an LLM without native multilingual
generation quality is substituted for Ollama's small models).

## Provider 1: IndicTrans2 (Primary)

AI4Bharat's IndicTrans2, loaded via HuggingFace `transformers`
(`AutoModelForSeq2SeqLM`, `trust_remote_code=True`). Uses FLORES-200
language codes (`tam_Taml`, `hin_Deva`, `eng_Latn`), input formatted as
`"{src_lang} {tgt_lang} {text}"` per the model's documented convention.
Chosen as primary because it's purpose-built for Indian languages and
performs meaningfully better on agricultural/technical vocabulary than
general-purpose translation models.

**Lazy-loaded**: the model is only loaded into memory on first actual use,
not at server startup — this keeps `uvicorn main:app` startup fast for the
common case where the offline dictionary path (mechanism #1 above) is all
that's actually needed.

## Provider 2: Google Cloud Translate API (Fallback)

Standard REST call to `translation.googleapis.com/language/translate/v2`,
requires `GOOGLE_TRANSLATE_API_KEY` set as an environment variable. Used
only if IndicTrans2 is unavailable (not installed, or its model failed to
load).

## Provider 3: Offline Phrase Dictionary (Always Available)

`translations.py` — English, Tamil, Hindi fully populated for every fixed
phrase the current UI displays (feature labels, recommendation actions by
category+level, positive-factor phrases, season names, and the ~20 most
common crop names as a starter set, easily extended). `get_translated()`
degrades gracefully: missing language → English; missing specific
sub-variant (e.g. a "high" level with no translation) → falls back to the
"low" variant before giving up — mirroring the same degradation the
English-only source dict already relies on, so behavior is consistent
whether or not a translation exists.

## HONESTY NOTE: What Was Actually Tested

This sandbox blocks `huggingface.co` (IndicTrans2's model weight host) and
`translate.googleapis.com` (confirmed via `curl -I` → `403
host_not_allowed` for both), so **neither live provider could be
downloaded or called** during development. Both integrations in
`translation_service.py` follow each provider's official, documented API
exactly and will work with normal internet access in your deployment
environment — but were not verified with a live call here. The offline
dictionary path (mechanism #1, `translations.py`) **is** fully tested and
is what actually powers every translated string in the deployed app today
— confirmed via direct testing that produced genuine, fully-translated
Tamil and Hindi output with zero English leakage (an actual bug was found
and fixed during development where category labels initially leaked
English text into otherwise-translated sentences).

## Adding a New Language

1. Add the language code + display name to `SUPPORTED_LANGUAGES` in
   `translations.py`.
2. Add a new key to every dictionary (`FEATURE_LABELS_I18N`,
   `RECOMMENDATIONS_I18N`, `POSITIVE_PHRASES_I18N`, `SEASON_NAMES_I18N`,
   `CROP_NAMES_I18N`) with the new language's translations.
3. Add the language's BCP-47 tag to `TTS_LANGUAGE_TAGS` (for the frontend
   Web Speech API) and, if using Coqui TTS, to `COQUI_SUPPORTED_LANGS` in
   `voice_service.py` if that language is supported by the XTTS v2 model.
4. Add the option to `LanguageSelector.tsx`'s `LANGUAGE_OPTIONS` array.

No other code changes are required — `get_translated()`'s fallback logic
means a partially-populated new language degrades gracefully to English
for any phrase not yet translated, rather than crashing.
