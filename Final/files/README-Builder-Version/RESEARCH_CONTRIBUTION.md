# Research Contribution

## Abstract-Style Summary

This work presents an explainable, multilingual, voice-accessible crop
yield decision support system combining a per-crop gradient-boosted
architecture, SHAP-based local explainability, a grounded small-language-
model narrative generation layer, and a two-tier text-to-speech pipeline —
designed and empirically validated for a real, messy government
agricultural dataset spanning 124 crop types with non-standardized
production-reporting units.

## Novelty Claims

### 1. Per-Crop CatBoost Architecture for Unit-Heterogeneous Agricultural Data

Standard crop-yield ML literature typically evaluates a single model per
dataset. This work identifies and empirically demonstrates that pooling
124 crop types into one regression target is not merely a modeling
inconvenience but a fundamental architectural error when those crop types
report yield in incompatible units (tonnes/ha vs. nuts/ha) — root-caused
via direct data inspection (e.g. Coconut, Sugarcane outlier analysis), not
assumed. The per-crop architecture is not a hyperparameter change but a
structural fix: real R² improved from 0.146 (uncleaned pooled model) →
0.313 (cleaned pooled model) → 0.878 (pooled test set across per-crop
architecture), with full per-crop transparency (0.46–0.95 range) rather
than reporting only the flattering pooled headline number.

### 2. SHAP as Grounding Substrate for LLM-Based Explanation

Rather than using an LLM to generate an explanation from raw tabular
input (which risks the model inventing plausible-sounding but
unsubstantiated reasoning), this system uses SHAP's structured,
mathematically-derived factor attributions as the **only** input the SLM
is permitted to see. This converts "explain this prediction" from an
open-ended generation task into a constrained paraphrasing task — a
meaningfully stronger grounding posture than typical "explain this data"
LLM prompting, implemented here via prompt-level constraints (see
`SLM_INTEGRATION.md`) rather than a heavier RAG/tool-use pipeline, as an
explicit, documented engineering trade-off given local-SLM constraints.

### 3. Deterministic Recommendation Engine as an SLM Safety Boundary

The SLM never generates agricultural recommendations itself — it only
paraphrases a fixed, auditable, rule-based recommendation list. This
separation of "what to recommend" (deterministic, reviewable code) from
"how to phrase it" (SLM) is a deliberate safety design for a domain
(agriculture) where a hallucinated recommendation could cause real
financial/crop harm — distinct from generic chatbot-style explanation
systems that don't draw this boundary.

### 4. Multilingual Support as Category-Level Translation, Not String
Substitution

The translation layer translates at the level of *semantic category*
(e.g., "nitrogen deficiency, low severity" as a resolved category+level
pair) rather than translating already-assembled English sentences
word-for-word — this was a deliberate architectural choice (and a real bug
found and fixed during development, where an earlier version wrapped
untranslated English phrases inside translated sentence structure) that
produces linguistically coherent Tamil/Hindi output rather than a
patchwork of translated and untranslated fragments.

### 5. Three-Tier Voice Accessibility with Honest Degradation

Rather than presenting a single "TTS integration," this system implements
and documents two backend providers (gTTS, Coqui) plus a browser-native
fallback, with an explicit, tested failure-handling contract (`503` +
`recommend_frontend_tts` flag) between backend and frontend — designed
around the realistic expectation that not every deployment environment
will have every provider available, rather than assuming a single always-
available cloud TTS service.

## Comparison to Standard SHAP Dashboards

| | Standard SHAP Dashboard | This System |
|---|---|---|
| Explanation format | Bar charts, numeric SHAP values | Natural-language narrative, translated, spoken aloud |
| Audience | Data scientist / technical reviewer | Farmer, including non-literate users |
| Model architecture | Single pooled model (typical) | Per-crop architecture, addressing unit heterogeneity |
| Recommendation source | Often absent, or same model output re-purposed | Separate deterministic engine, SLM only paraphrases |
| Language support | Typically English-only | English, Tamil, Hindi, extensible |
| Accessibility | Requires literacy + numeracy | Voice output requires neither |

## Honest Discussion of Limitations (IEEE-Reviewer Standard)

- **Hallucination is mitigated, not eliminated**: prompt-level grounding
  cannot mathematically guarantee the SLM never over-elaborates beyond
  the given facts. No automated grounding-verification step (e.g.
  comparing SLM output tokens against the input facts) is implemented.
- **Live external-service integrations are unverified**: Ollama,
  IndicTrans2, Google Translate, and gTTS/Coqui TTS network calls were
  written against each provider's documented API but could not be tested
  live in this project's development environment due to sandbox network
  restrictions — a real limitation of this specific development history,
  disclosed rather than glossed over, and something any adopter must
  verify in their own environment before relying on it in production.
- **No k-fold cross-validation**: single 80/20 split per crop; a k-fold
  extension would give more statistically robust per-crop R² estimates,
  particularly for the smaller-sample crops.
- **Pooled R² is a genuinely higher number than most individual crop
  accuracies** for a real statistical reason (variance-denominator
  inflation from pooling across scales), disclosed explicitly rather than
  presented as a single unqualified headline metric.
- **Two crops remain below R²=0.5** (Soyabean, Khesari) even with the
  per-crop architecture — the improvement is real and large, but not
  universal across all 52 modeled crops.

## Future SLM Integration (Forward-Looking)

See `FUTURE_SCOPE.md` for planned extensions: counterfactual explanation
generation, automated grounding verification, larger/fine-tuned local
models for improved Tamil generation quality, and expanded language
coverage beyond the current three.
