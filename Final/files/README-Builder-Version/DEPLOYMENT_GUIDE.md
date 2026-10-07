# Deployment Guide

## Prerequisites

- Python 3.10–3.12 for the core backend (Ollama/gTTS/IndicTrans2 paths);
  a **separate** Python 3.10/3.11 environment specifically if you want the
  Coqui TTS option, since it's incompatible with 3.12.
- Node.js 18+ for the frontend build.
- (Optional) Ollama installed, with a model pulled: `ollama pull phi3:mini`.
- (Optional) `GOOGLE_TRANSLATE_API_KEY` environment variable if you want
  the Google Translate fallback active.

## Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Frontend Setup

```bash
npm install
cp .env.example .env.local
# edit .env.local: VITE_API_BASE_URL=https://your-backend-host:8000
```

## Local Development

```bash
# Terminal 1 — backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
npm run dev
```

## Enabling the Local SLM (Optional but Recommended)

```bash
ollama serve                 # in its own terminal
ollama pull phi3:mini        # or gemma:2b, tinyllama
```
Verify: `curl http://localhost:8000/health` should show
`"slm_ollama_reachable": true`. Without this step, the app functions
normally using the tested offline template fallback.

## Enabling Coqui TTS (Optional)

```bash
python3.11 -m venv venv-coqui
source venv-coqui/bin/activate
pip install TTS
# Run voice_service's Coqui path from within this environment, or deploy
# it as a separate microservice if your main backend runs Python 3.12+.
```

## Production Build

```bash
npm run build        # outputs to dist/
```
Serve `dist/` via your preferred static host (or `server.ts`'s Express
static-serving path — see that file's docstring).

## Environment Variables

| Variable | Purpose | Required? |
|---|---|---|
| `VITE_API_BASE_URL` (frontend) | Backend base URL | Yes |
| `OLLAMA_HOST` (backend) | Ollama server address, default `http://localhost:11434` | No |
| `OLLAMA_MODEL` (backend) | Model name, default `phi3:mini` | No |
| `GOOGLE_TRANSLATE_API_KEY` (backend) | Enables the Google Translate fallback | No |

## Production Hardening Checklist

- [ ] Tighten `main.py`'s CORS `allow_origins=["*"]` to your actual
      frontend domain.
- [ ] Put the backend behind HTTPS (a reverse proxy like nginx/Caddy is
      sufficient).
- [ ] Decide whether to log farmer predictions for monitoring — currently
      nothing is persisted (see `DATABASE_AND_DATAFLOW.md`); add logging
      deliberately if you need it, with appropriate privacy handling.
- [ ] Benchmark live Ollama/gTTS/IndicTrans2 latency in your actual
      deployment environment — none of these were exercised live during
      development due to sandbox network restrictions (see each service's
      "Honesty Note").
- [ ] If deploying Coqui TTS, run it in its own Python 3.10/3.11
      environment or container, separate from the main FastAPI backend.

## Rollback / Compatibility Note

Every new endpoint (`/api/explain`, `/api/voice`, `/api/languages`) is
additive — `/api/predict`, `/api/what-if`, `/api/options`,
`/api/dataset-info`, `/api/model-metrics`, `/api/eda`, and `/health` all
preserve their exact pre-existing response shapes, so this deployment is
backward-compatible with any frontend already built against the earlier
API version.
