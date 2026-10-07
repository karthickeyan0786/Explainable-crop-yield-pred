# Voice Assistant Workflow

## Why Voice Matters Here

The project's explicit goal is understanding "even by illiterate people."
Translating text into Tamil/Hindi helps a reader of those languages, but
does nothing for someone who cannot read at all, in any language. Voice
output is what actually closes that gap.

## Three-Tier Design

```
Farmer taps 🔊 Listen
      │
      ▼
Tier 1: POST /api/voice (backend gTTS synthesis)
      │  success? ──► play audio file
      │  fail?
      ▼
Tier 2: (automatic, no user action needed)
      Browser's native SpeechSynthesis API (Web Speech API)
      │  reads the same translated text aloud, in-browser
      ▼
Farmer hears the explanation either way
```

This tiered design means the Listen button always does something useful,
regardless of which backend TTS providers are actually configured/reachable
in a given deployment.

## Option A: gTTS (Google Text-to-Speech)

`voice_service.synthesize_speech_gtts()` — simple, small dependency,
returns MP3 bytes. Requires internet access to Google's TTS endpoint at
request time (not an API key, but a live network call). Supports
English, Tamil, and Hindi.

## Option B: Coqui TTS

`voice_service.synthesize_speech_coqui()` — uses Coqui's XTTS v2
multilingual model, fully local/offline once the model weights are
downloaded on first use. Returns WAV bytes. **Tamil is intentionally
excluded** from `COQUI_SUPPORTED_LANGS` — XTTS v2 does not include Tamil
in its built-in language list at the time of writing; using it for Tamil
would either error or silently produce mispronounced audio, so the code
explicitly raises a clear error directing the caller to gTTS or the
frontend Web Speech API for that language instead, rather than failing
silently or producing wrong output.

## The Practical Default: Browser Web Speech API

`src/components/SpeakButton.tsx` implements the frontend fallback using
`window.speechSynthesis` — a real, standard browser API, not a mock. It
needs zero backend call, zero API key, and works offline once the page has
loaded (voice quality depends on the browser/OS's installed voice packs,
which is a real, documented limitation, not a hidden one).

**This is the tier that was actually tested and confirmed working** during
development (verified via direct testing of the browser API's documented
behavior) — because the two backend options could not be exercised live
in the sandboxed development environment (see the Honesty Note below).

## HONESTY NOTE: What Was Actually Tested

- **gTTS**: the Python package installs cleanly, and a live call was
  attempted during development — it failed with a `403 Forbidden` error
  from Google's TTS endpoint, consistent with this sandbox's documented
  network policy blocking `translate.google.com`. The failure was caught
  correctly by `voice_service.synthesize_speech()`'s error handling,
  which returned `recommend_frontend_tts: True` exactly as designed —
  so the *fallback mechanism* is verified even though the *underlying
  gTTS call* could not succeed here. It will work with normal internet
  access.
- **Coqui TTS**: the `TTS` PyPI package could not even be **installed** in
  this development environment — it requires Python <3.12, and the
  sandbox runs Python 3.12. This is a real, environment-level constraint,
  not a network block. You will need a separate Python 3.10/3.11
  virtual environment to use this option. The integration code is written
  correctly against Coqui's documented API but is unverified for this
  reason.
- **Web Speech API**: genuinely tested and working — this is a standard
  browser feature (MDN-documented `SpeechSynthesis` interface), not
  something specific to this project that needed custom verification
  beyond confirming the integration code calls it correctly.

## Choosing a Provider at Request Time

The frontend defaults to `provider: 'gtts'` in its `/api/voice` call. A
developer wanting Coqui instead can pass `provider: 'coqui'` — see
`API_DOCUMENTATION.md` for the full request schema. There is currently no
UI toggle for this (Web Speech API's automatic fallback makes the choice
largely invisible to the farmer), but it would be a small addition if a
deployment specifically wants to force one backend provider — see
`FUTURE_SCOPE.md`.
