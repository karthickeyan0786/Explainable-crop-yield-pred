# Project Diagrams

## 1. System Architecture

```mermaid
flowchart TD
    A[Farmer - React Frontend] -->|HTTP fetch| B[FastAPI Backend - main.py]
    B --> C[model_service.py]
    B --> D[shap_service.py]
    B --> E[slm_service.py]
    B --> F[translation_service.py]
    B --> G[voice_service.py]
    C -->|per-crop CatBoost| H[(backend/artifacts/)]
    D --> C
    E --> D
    E -->|Ollama| I[Local SLM: Phi-3/Gemma/TinyLlama]
    E -->|fallback| J[Offline Template + translations.py]
    F -->|IndicTrans2/Google| K[External Translation Providers]
    G -->|gTTS/Coqui| L[TTS Providers]
    A -->|fallback| M[Browser Web Speech API]
```

## 2. Prediction Pipeline

```mermaid
flowchart LR
    A[Farmer Input] --> B[Pydantic Validation]
    B --> C[build_feature_row]
    C --> D{Crop has own model?}
    D -->|Yes, 52 crops| E[Per-Crop CatBoost]
    D -->|No| F[Pooled Fallback Model]
    E --> G[expm1 predicted yield]
    F --> G
```

## 3. Explainability Pipeline

```mermaid
flowchart LR
    A[Feature Row + Model] --> B[shap.TreeExplainer]
    B --> C[Raw SHAP values, all features]
    C --> D[Filter DISPLAY_EXCLUDE]
    D --> E[Sort positive / negative]
    E --> F[Dedupe by agronomic category]
    F --> G[Structured Grounding Payload]
```

## 4. Decision Support Pipeline

```mermaid
flowchart LR
    A[Negative SHAP Factor] --> B[RECOMMENDATION_CATEGORY lookup]
    B --> C["_level: low or high vs crop median"]
    C --> D[RECOMMENDATIONS lookup]
    D --> E["issue / action / reason"]
```

## 5. SLM + Multilingual Explanation Pipeline

```mermaid
flowchart TD
    A[Grounding Payload] --> B{Ollama reachable?}
    B -->|Yes| C[Grounded Prompt in target language]
    C --> D[Ollama chat call]
    D --> E[Explanation Text]
    B -->|No| F[Template Fallback]
    F --> G["get_translated per category+level"]
    G --> E
```

## 6. Voice Assistant Pipeline

```mermaid
flowchart TD
    A[Listen Button Tapped] --> B[POST /api/voice - gTTS]
    B --> C{Success?}
    C -->|Yes| D[Play audio file]
    C -->|No, 503| E[Browser Web Speech API]
    E --> D
```

## 7. What-If Simulation Pipeline

```mermaid
flowchart TD
    A[Baseline Prediction + SHAP Factors] --> B[For each simulatable negative factor]
    B --> C[get_candidates: real crop percentiles]
    C --> D[find_best_value: try each through real model]
    D --> E{Improves prediction?}
    E -->|Yes| F[Apply change, record before/after]
    E -->|No| G[Leave unchanged]
    F --> H[Re-predict improved_row]
    G --> H
    H --> I[current_yield, improved_yield, % improvement, changed_parameters]
```

## 8. Frontend-Backend Communication

```mermaid
sequenceDiagram
    participant U as Farmer
    participant F as React Frontend
    participant B as FastAPI Backend
    U->>F: Fill prediction form
    F->>B: POST /api/predict
    B-->>F: yield + SHAP factors + recommendations
    F->>B: POST /api/explain (lang=ta)
    B-->>F: Tamil narrative
    F->>B: POST /api/what-if
    B-->>F: current/improved yield
    U->>F: Tap Listen
    F->>B: POST /api/voice
    alt TTS succeeds
        B-->>F: audio bytes
    else TTS fails
        B-->>F: 503 recommend_frontend_tts
        F->>F: Web Speech API fallback
    end
```

## 9. Model Training Workflow

```mermaid
flowchart TD
    A[5 Government CSVs] --> B[Merge]
    B --> C[Clean: sentinel + per-crop Tukey outliers]
    C --> D[240,457 model-ready rows]
    D --> E{Crop has >=500 rows?}
    E -->|Yes, 52 crops| F[Per-crop 80/20 split + CatBoost]
    E -->|No, ~72 crops pooled| G[Pooled 80/20 split + CatBoost]
    F --> H[53 trained models + real held-out metrics]
    G --> H
    H --> I[backend/artifacts/]
```
