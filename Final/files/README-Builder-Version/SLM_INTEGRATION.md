# SLM Integration

## Why a Small Language Model, Not Just Templates

Raw SHAP output ("Nitrogen +0.42, Rainfall +0.28, Temperature -0.35") is
precise but unreadable to a non-technical farmer. A fixed template can
produce readable sentences, but reads mechanically and can't naturally
adapt phrasing to context. An SLM bridges this: natural, warm,
conversational language, generated from the exact same underlying facts.

## Model Choice: Local SLM via Ollama, Not Cloud APIs

Per requirement, this integration uses **Ollama** (Phi-3 Mini / Gemma 2B /
TinyLlama), not OpenAI or other cloud LLM APIs. Rationale:
- **Privacy**: farmer input (location, crop, financial-adjacent data like
  fertilizer spend) never leaves the deployment environment.
- **Cost**: no per-request API billing at scale (this is a
  farmer-facing tool, potentially high request volume).
- **Offline capability**: rural deployment environments may have
  unreliable internet; a local model keeps the core explanation feature
  working without it.

## Grounding Strategy (Anti-Hallucination)

The SLM is **never given open-ended context** — it receives exactly one
thing: the structured JSON payload from `shap_service.get_shap_explanation()`
(predicted yield, positive/negative factor labels, recommendation
actions), embedded in a prompt with explicit rules:

```
STRICT GROUNDING RULES:
- Use ONLY the facts given below. Do not add any crop, weather, price, or
  yield information that is not explicitly listed here.
- Do not invent new recommendations. Only rephrase the ones given.
- Do not mention percentages, dates, or numbers not given below.
- Do not mention "SHAP", "the model", "AI", or any technical/ML terms.
```

This is **prompt-level grounding**: the model has no tool access, no
retrieval, no ability to query the training data or the internet. It
literally cannot introduce a fact it wasn't given, though it could in
principle still over-elaborate on a given fact in a way that sounds more
confident/specific than warranted — a known, honestly-acknowledged
limitation of prompt-only grounding (see "Limitations" below), not a
solved problem.

## Low Temperature for Reduced Creativity

`options={"temperature": 0.3}` in the Ollama call — a lower temperature
biases the model toward more literal, less creative/elaborative output,
which is desirable for a grounded explanation task (we want faithful
paraphrasing, not creative writing).

## Fallback: Fully Offline, Fully Tested Template

If Ollama is unreachable (`_get_ollama_client()` returns `None` — checked
via a cheap `client.list()` call at first use, cached after), the exact
same structured facts are assembled into a natural sentence using
`translations.py`'s category-keyed phrase dictionaries. This path is
**100% deterministic and was fully tested during development** (unlike the
live Ollama path — see the Honesty Note below): every recommendation
action and factor label is individually translated via
`get_translated()`, not just wrapped in local sentence structure around
English text (an actual bug found and fixed during development — see
`git blame`/development history for the exact fix).

## Prompt Engineering Choices

- **Language specified explicitly in the prompt** (`in {lang_name}`), not
  inferred — avoids the model defaulting to English regardless of the
  request.
- **"Speak directly to the farmer"** instruction — produces second-person,
  conversational phrasing rather than a third-person report.
- **4-6 sentence length constraint** — long enough to cover positive
  factors, negative factors, and recommendations, short enough to remain
  listenable as a single audio clip via the Voice Assistant.
- **No bullet points/headings instruction** — the output must work as a
  flowing spoken narrative (fed directly to TTS), not a visual document.

## HONESTY NOTE: What Was Actually Tested

This project's development sandbox blocks `ollama.com` and `ollama.ai`
entirely at the network level (confirmed via `curl -I https://ollama.com`
returning `403 host_not_allowed`), so **Ollama itself could not be
installed, and no live model call was ever made** during development. The
integration code in `slm_service.py` follows the official `ollama` Python
client's documented API exactly (`ollama.Client(host=...)`,
`client.chat(model=..., messages=...)`) and will work correctly once you
run `ollama serve` and `ollama pull phi3:mini` in an environment with
normal internet access — but this specific path is unverified by direct
testing in this repository's development history. The offline template
fallback path (`_template_fallback()`) **is** fully tested and is what
currently powers every explanation the deployed app produces.

## Limitations

- Prompt-level grounding is a strong mitigation, not an absolute
  guarantee against hallucination — a sufficiently unusual input
  combination could still produce an SLM response that over-elaborates
  beyond the literal given facts. No automated fact-checking of the SLM's
  output against the grounding payload is implemented (see
  `FUTURE_SCOPE.md` for the recommended extension).
- Small local models (Phi-3 Mini, Gemma 2B, TinyLlama) have weaker
  multilingual generation quality than larger cloud models, particularly
  for Tamil — this is a real trade-off of the "local, not cloud API"
  requirement, and is exactly why the offline template fallback exists as
  a reliable backstop rather than an afterthought.
- No per-request cost/latency benchmarking of the live Ollama path exists,
  since it was never run — plan to benchmark this yourself before
  production deployment.
