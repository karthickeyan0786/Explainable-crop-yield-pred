# Yield Engine — AI Crop Yield Prediction & Explainable Decision Support

Full-stack application: React/TypeScript frontend (this AI Studio export,
modified) + Python FastAPI backend (`/backend`) wired to your real, already-
trained CatBoost model. No predictions are hardcoded in the frontend — every
number comes from a live API call to `/backend`.

## Architecture

```
React Dashboard (this folder)
       |
       | HTTP (fetch), see src/services/api.ts
       ↓
FastAPI Backend (/backend)
       |
       ├── model_service.py: feature engineering, CatBoost .predict(),
       |                      SHAP explanation, what-if simulation
       ↓
best_catboost_model.cbm  (your real trained model — never retrained)
```

## Run it

**1. Start the backend first** (see `backend/README.md` for details):
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**2. Start the frontend:**
```bash
npm install
cp .env.example .env.local   # already points at http://localhost:8000
npm run dev
```

Open the printed local URL. Go to **Prediction**, fill in the form, click
**Predict Yield** — this calls your real backend and real model.

## What changed from the original AI Studio export

- **Removed "Model Comparison" entirely** (nav item, page, route, type) — you
  only use one production model (CatBoost), so a multi-model comparison page
  didn't reflect reality and has been dropped per your request.
- **Removed `src/data.ts`** — it contained a fake `calculateYield()` function
  (a hand-tuned scoring formula, not your model) and a fabricated
  `MODEL_METRICS` array listing models (XGBoost, LightGBM, a "Deep Agronomic
  Neural Net") that were never actually trained. Both violated "do not
  invent model results."
- **New `src/services/api.ts`** — real fetch calls to the FastAPI backend.
  `PredictionView`, `DashboardView`, `ExplainableAiView`,
  `DecisionSupportView`, `WhatIfSimulationView`, and `DatasetView` were all
  rewritten to consume this instead of local fake logic.
- **`PredictionView`** now has the exact grouped form you specified (Crop
  Info / Soil / Agricultural Inputs / Climate & Weather), with dropdowns
  populated from the real training data (not a hardcoded list), and derived
  fields (Soil Fertility Index, Input Intensity) shown as computed read-only
  previews rather than editable — they're mathematically defined from other
  inputs, so letting a user type an inconsistent value would feed the model
  bad data.
- **`server.ts`** simplified to only serve the frontend — it previously also
  ran a fake `/api/predict` route with a hand-written scoring formula plus
  optional Gemini calls; that's all removed since real predictions now go to
  FastAPI.
- **`DatasetView`** rewritten from a fake 10-row "add your own record" table
  into real dataset statistics + preprocessing pipeline, pulled from
  `/api/dataset-info`.

## Verified before delivery

- Backend: `/health`, `/api/options`, `/api/dataset-info`,
  `/api/model-metrics`, `/api/predict`, `/api/what-if` all tested against
  the real model with `curl`.
- Frontend: `npx tsc --noEmit` — zero errors. `npx vite build` — succeeds.
- Found and fixed two real bugs while testing: (1) negative SHAP factors
  were returning the raw feature value instead of the actual SHAP number,
  (2) the What-If simulator's Area search produced a nonsensical
  "expand to 27,100 hectares" suggestion due to outlier rows in the training
  data — both fixed, see `backend/README.md` for details.

## ⚠️ Important finding — read `backend/README.md`

The real CatBoost R² on this dataset is **0.146**, not the ~0.75–0.88 you
may be expecting from earlier runs. Root cause and full explanation is in
`backend/README.md` — I did not retrain or filter data to hide this, per
your "do not retrain" instruction. The dashboard shows the honest number.

## What's NOT done (given the scope of this request)

- **EDA page** (`src/components/EdaView.tsx`) was left as-is — it still
  shows illustrative chart placeholders rather than live charts generated
  from your actual data. Wiring real EDA charts (e.g. via a `/api/eda`
  endpoint returning chart data, rendered with a charting library) is a
  reasonable next step but wasn't completed here.
- No deployment configuration (Docker, hosting) was set up — only local dev
  instructions above.
- The backend's CORS is wide open (`allow_origins=["*"]`) for local
  development — tighten this before any real deployment.

## Folder structure

```
.
├── backend/                    # FastAPI backend (Python)
│   ├── main.py                 # API routes
│   ├── model_service.py        # model logic (feature eng, predict, SHAP, what-if)
│   ├── build_reference_data.py # one-time script that built artifacts/ (already run)
│   ├── requirements.txt
│   ├── README.md               # backend-specific docs + the R² finding
│   └── artifacts/              # your real model + encoders + small reference JSON
├── src/
│   ├── components/              # all page components, updated to call the API
│   ├── services/api.ts          # NEW: the only place that talks to the backend
│   └── types.ts                 # rewritten to match the real 23-feature model
├── server.ts                    # simplified: serves frontend only
└── .env.example                 # VITE_API_BASE_URL config
```
