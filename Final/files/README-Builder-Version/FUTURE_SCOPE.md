# Future Scope

## Counterfactual Explanations

Extend beyond "what factors contributed" to "what is the minimal change
that would flip this prediction from below-average to above-average
yield" — a more formally-grounded counterfactual framing than the current
What-If Simulation's percentile-candidate search, potentially using
established counterfactual-explanation libraries (e.g. DiCE) adapted to
work with the per-crop CatBoost models.

## SLM Integration Improvements

- **Automated grounding verification**: a lightweight check (e.g. does
  the SLM output mention any crop, number, or factor not present in the
  input payload?) run after generation, to catch and discard/regenerate
  responses that drift from the grounding facts — turning "prompt-level
  grounding" into "prompt-level + verified grounding."
- **Fine-tuned local models**: Phi-3 Mini/Gemma 2B's out-of-the-box Tamil
  generation quality is a known weak point for small models; a
  LoRA-finetuned variant on agricultural Tamil text could meaningfully
  improve this without needing a larger (slower, more resource-hungry)
  base model.
- **Live benchmarking**: latency/quality benchmarking of the actual Ollama
  integration in a real (non-sandboxed) environment, which this
  project's development history could not perform.

## Farmer Chatbot

Extend the one-shot "predict → explain" flow into a multi-turn
conversational interface where a farmer can ask follow-up questions
("what if I plant next month instead?") in natural language, routed to
the appropriate structured tool (What-If Simulation, a different crop's
prediction, etc.) rather than free-form LLM generation — preserving the
grounding discipline established in the current architecture.

## Multilingual Support

Extend beyond Tamil/Hindi to other major Indian languages (Telugu,
Kannada, Marathi, Bengali, etc.) using the same category-keyed translation
architecture documented in `TRANSLATION_WORKFLOW.md` — no code changes
needed beyond populating new dictionary entries and adding BCP-47 tags.

## Satellite Imagery Integration

Incorporate NDVI/vegetation-index features derived from satellite imagery
(e.g. Sentinel-2) as additional model inputs, which the original Phase 1
dataset report identified as a meaningful feature gap in the current
government-sourced dataset (which has no remote-sensing features at all).

## Weather Forecasting Integration

Replace or supplement the current climatological-normal weather features
(long-term monthly averages, not year-specific — a documented limitation
carried through every phase of this project) with real forecast data at
prediction time, enabling genuinely forward-looking (not just historical-
pattern-based) yield predictions.

## Mobile Deployment

- A dedicated mobile app (React Native or a PWA wrapper around the
  existing React frontend) would better serve farmers primarily using
  smartphones, with offline-first design (cached model predictions,
  on-device Web Speech API) more critical than on desktop.
- Investigate on-device model inference (e.g. exporting the per-crop
  CatBoost models to ONNX) for fully offline prediction in low-
  connectivity rural areas, removing the backend dependency entirely for
  the core prediction flow.

## Production Monitoring

Add structured logging of prediction requests (with appropriate privacy
handling) to enable monitoring of: which crops/regions are most queried,
how often the live Ollama/translation/TTS paths are actually used vs.
falling back, and real-world model performance drift over time as new
government data becomes available.
