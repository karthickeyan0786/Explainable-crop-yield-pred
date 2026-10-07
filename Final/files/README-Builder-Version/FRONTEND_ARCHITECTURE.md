# Frontend Architecture

## React Architecture

TypeScript + React (Vite build), single-page application with in-memory
tab-based navigation (no URL routing library — `NavTab` state in `App.tsx`
controls which page component renders). This was the existing AI
Studio-exported app's structure, preserved rather than rewritten, per
"reuse current code wherever possible."

## Components

| Component | Purpose |
|---|---|
| `Sidebar.tsx` | Navigation between the 7 pages |
| `Header.tsx` | Page title + theme toggle |
| `DashboardView.tsx` | Overview: hero prediction, Farmer Assistant panel, Explainable AI, Decision Support, What-If preview |
| `PredictionView.tsx` | Grouped input form (Crop Info / Soil / Inputs / Climate) + language selector |
| `ExplainableAiView.tsx` | Detailed SHAP factor bars |
| `DecisionSupportView.tsx` | Full recommendation cards (Problem/Action/Reason) |
| `WhatIfSimulationView.tsx` | Dedicated what-if exploration page |
| `EdaView.tsx` | Real dataset statistics and charts |
| `DatasetView.tsx` | Dataset overview + model metrics + preprocessing pipeline |
| `farmer-assistant/PredictionCard.tsx` | Headline predicted yield |
| `farmer-assistant/ExplanationCard.tsx` | SLM narrative, "Why is my yield low?" |
| `farmer-assistant/RecommendationsCard.tsx` | Action list, "What should I do?" |
| `farmer-assistant/VoiceAssistantCard.tsx` | Language selector + Listen button, combined |
| `LanguageSelector.tsx` | Reusable en/ta/hi dropdown |
| `SpeakButton.tsx` | Two-tier TTS (backend `/api/voice` → browser Web Speech API fallback) |

## Pages / Routing

No client-side router library — `App.tsx` holds `currentTab: NavTab` state
and conditionally renders the matching view component. Simple and
sufficient for a single-screen dashboard app with no deep-linkable URLs
required.

## State Management

Lifted to `App.tsx`: `farmInput: FarmInput` (the current form state,
including the selected `lang`) and `prediction: PredictionResult | null`
are held at the top level and passed down as props, so every page reads
consistent, shared state rather than re-fetching independently. Local
component state (`useState`) is used within each view for
page-specific concerns (e.g. `DashboardView`'s SLM explanation, what-if
preview, and model metrics are all fetched and held locally since they're
only relevant to that page).

## API Integration

`src/services/api.ts` is the **only** file that calls `fetch()` — every
component imports the typed `api` object rather than constructing requests
itself. This keeps the request/response contract in one place and makes
`types.ts` the single source of truth for what shape of data the frontend
expects from each endpoint.

## Dashboard Rendering

`DashboardView.tsx` fetches `/api/model-metrics` once on mount, and
`/api/what-if` + `/api/explain` each time `prediction` changes (i.e. after
a new prediction is made) — this keeps the Farmer Assistant panel's
Explanation Card and the What-If preview automatically in sync with
whatever the farmer most recently predicted, without a manual refresh
step.

## Accessibility Design (Low-Literacy Support)

This is the primary design constraint driving several frontend choices
beyond the obvious language selector:
- Derived/computed fields (Soil Fertility Index, Input Intensity) are
  shown as read-only previews rather than free-text entry, reducing the
  chance of a confusing invalid-input error for a less technically
  fluent user.
- The Farmer Assistant panel's cards use short titles phrased as direct
  questions ("Why is my yield low?", "What should I do?") rather than
  technical section headers.
- The Voice Assistant is placed prominently, not buried in a settings
  menu — voice output is treated as a first-class feature, not an
  accessibility afterthought.
