# Phase-Wise Architecture: AI-Powered Restaurant Recommendation System

**Use case:** Zomato  
**Based on:** [problemstatement.md](./problemstatement.md)

## Overview

The system is built in **eight sequential phases**. Phases 1–5 form the **core recommendation pipeline**; Phases 6–8 wrap that pipeline into a deployable full-stack web application.

| Group | Phases | Focus |
| --- | --- | --- |
| Core pipeline | 1–5 | Data, input, filtering, LLM ranking, display contract |
| Application layer | 6–7 | Backend API and frontend UI |
| Operations | 8 | Streamlit deployment of the full pipeline |

## Phase Overview

```text
Phase 1           Phase 2           Phase 3
Data Ingestion -> User Input    -> Integration Layer
                                       |
                                       v
Phase 5           Phase 4
Output Display <- Recommendation Engine (Groq LLM)
     ^                    ^
     |                    |
Phase 7 (Frontend)   Phase 6 (Backend API)
     |                    |
     +-------- REST ------+
                              |
                    Phase 8 (Streamlit deploy)
```

| Phase | Name | Purpose | Implemented in |
| --- | --- | --- | --- |
| 1 | Data Ingestion | Load and clean restaurant data | `phase1_data_ingestion/` |
| 2 | User Input | Capture and validate search preferences | `phase2_user_input/` |
| 3 | Integration Layer | Filter candidates and build LLM prompt | `phase3_integration_layer/` |
| 4 | Recommendation Engine | Rank restaurants and generate explanations (Groq) | `phase4_recommendation_engine/` |
| 5 | Output Display | Define what the user sees (display contract) | `phase5_output_display/` |
| 6 | Backend API | Expose HTTP endpoints; orchestrate Phases 2–4 | `phase6_backend_api/` |
| 7 | Frontend Web UI | Browser UI for form input and result cards | `phase7_frontend_ui/` |
| 8 | Deployment | Streamlit app that ships the pipeline to users | `phase8_deployment/` |

### Repository layout

```text
Zomato milestone1/
├── phase1_data_ingestion/
├── phase2_user_input/
├── phase3_integration_layer/
├── phase4_recommendation_engine/
├── phase5_output_display/
├── phase6_backend_api/
├── phase7_frontend_ui/
├── phase8_deployment/
├── .env                          # GROQ_API_KEY (server-side only)
└── doc/
    └── architecture.md
```

---

## Phase 1: Data Ingestion

**Goal:** Prepare a clean, usable restaurant dataset for filtering and recommendation.

**Responsibilities**

- Load the Zomato dataset from Hugging Face:  
  [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
- Preprocess and normalize records
- Extract fields: restaurant name, location, cuisine, cost, rating, and related attributes

**Input**

- Raw Hugging Face dataset

**Output**

- Structured restaurant records ready for filtering (`restaurants_clean.json`)

**Architecture focus**

```text
Hugging Face Dataset --> Loader --> Preprocessor --> Clean Restaurant Store
```

---

## Phase 2: User Input

**Goal:** Collect preferences that drive filtering and LLM ranking.

**Responsibilities**

- Capture required and optional preferences from the user
- Validate input before it reaches the integration layer

**Preferences**

| Preference | Examples |
| --- | --- |
| Location | Delhi, Bangalore |
| Budget | Low, medium, high |
| Cuisine | Italian, Chinese |
| Minimum rating | e.g., 4.0+ |
| Additional preferences | Family-friendly, quick service |

**Input**

- Raw preference fields (from CLI, API, or UI form)

**Output**

- `ValidatedPreferences` object passed to Phase 3

**Architecture focus**

```text
Raw Input --> Validator --> Validated Preference Object
```

---

## Phase 3: Integration Layer

**Goal:** Bridge structured data and the LLM by filtering candidates and building a strong prompt.

**Responsibilities**

- Filter restaurant records using Phase 2 preferences
- Prepare a shortlist of relevant restaurants
- Design and assemble an LLM prompt that includes:
  - user preferences
  - candidate restaurant details
  - ranking and explanation instructions

**Input**

- Clean restaurant store (Phase 1)
- Validated preferences (Phase 2)

**Output**

- Filtered candidate list
- Final LLM prompt

**Architecture focus**

```text
Preferences + Restaurant Store
            |
            v
     Filter & Shortlist
            |
            v
     Prompt Builder --> LLM Prompt
```

---

## Phase 4: Recommendation Engine

**Goal:** Use an LLM to rank restaurants and explain why each option fits.

**Responsibilities**

- Send the Phase 3 prompt to **Groq** (`llama-3.3-70b-versatile` by default)
- Rank restaurants by fit to user preferences
- Generate a short explanation for each recommendation
- Optionally summarize the overall set of choices
- Fall back to deterministic ranking if Groq is unavailable

**Input**

- LLM prompt with preferences and candidates (Phase 3)

**Output**

- Ranked recommendations with explanations (and optional summary)

**Architecture focus**

```text
LLM Prompt --> Groq LLM Service --> Ranked Results + Explanations
                      |
                      +--> Fallback ranker (on API/parse failure)
```

---

## Phase 5: Output Display

**Goal:** Define the display contract — what the user sees after ranking completes.

**Responsibilities**

- Specify fields shown for each recommendation
- Normalize Phase 4 output into a stable view model for the UI
- Handle missing fields gracefully (`N/A`, hide optional fields)
- Truncate long names and explanations for layout safety
- Escape unsafe content in LLM explanations before render

**Displayed fields**

| Field | Source |
| --- | --- |
| Rank | Phase 4 |
| Restaurant name | Phase 4 / candidate |
| Cuisine | Phase 4 / candidate |
| Rating | Phase 4 / candidate |
| Estimated cost | Phase 4 / candidate |
| AI-generated explanation | Phase 4 |
| Fallback badge | Phase 4 `used_fallback` |

**Input**

- `Phase4Result` (ranked recommendations + summary + warnings)

**Output**

- `DisplayPayload` — normalized list of recommendation cards + summary + UI state hints (`results` / `no_match` / `fallback`)

**Architecture focus**

```text
Phase4Result --> Display Normalizer --> DisplayPayload --> Phase 7 UI
```

**Folder structure**

```text
phase5_output_display/
├── models.py           # DisplayPayload, DisplayCard
├── normalizer.py       # Phase4Result -> DisplayPayload
├── pipeline.py         # run_phase5()
└── tests/
```

---

## Phase 6: Backend API

**Goal:** Expose a REST API that orchestrates the pipeline and returns JSON for the frontend.

**Responsibilities**

- Load Phase 1 clean store on startup
- Accept preference payloads over HTTP
- Run Phase 2 validation → Phase 3 filtering → Phase 4 Groq ranking → Phase 5 display normalization
- Expose catalog endpoints for location/cuisine dropdowns
- Keep `GROQ_API_KEY` server-side only
- Enable CORS for the Phase 7 frontend origin

**Stack**

- **FastAPI** — HTTP API + OpenAPI docs
- **Uvicorn** — ASGI server
- **Phases 1–5** — imported as Python packages

**Input**

- HTTP requests (JSON preference form, catalog queries)

**Output**

- JSON responses consumed by Phase 7

**Architecture focus**

```text
HTTP Request --> Router --> RecommendationService
                                |
                    Phase 2 --> Phase 3 --> Phase 4 --> Phase 5
                                |
                                v
                          JSON Response
```

**Folder structure**

```text
phase6_backend_api/
├── app/
│   ├── main.py                  # FastAPI entrypoint
│   ├── config.py                # CORS, paths, env
│   ├── api/routes/
│   │   ├── health.py            # GET /health, GET /ready
│   │   ├── catalog.py           # GET /catalog/locations, /catalog/cuisines
│   │   └── recommend.py         # POST /recommend
│   ├── schemas/                 # Pydantic request/response models
│   └── services/
│       └── recommendation_service.py
└── requirements.txt
```

### API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness check |
| `GET` | `/ready` | Readiness — store loaded, Groq key present |
| `GET` | `/catalog/locations` | Known locations from Phase 1 store |
| `GET` | `/catalog/cuisines` | Known cuisines from Phase 1 store |
| `POST` | `/recommend` | Full pipeline; returns Phase 5 display payload |

### `POST /recommend` contract

**Request**

```json
{
  "location": "Bellandur",
  "budget": "high",
  "cuisine": "North Indian",
  "min_rating": 4.0,
  "additional_preferences": "budget around 2000 for two people",
  "cuisine_match_mode": "or"
}
```

**Success (`200`)**

```json
{
  "state": "results",
  "preferences": {
    "location": "Bellandur",
    "location_key": "bellandur",
    "budget": "high",
    "cuisines": ["North Indian"],
    "min_rating": 4.0
  },
  "recommendations": [
    {
      "rank": 1,
      "name": "MoMo Cafe - Courtyard by Marriott",
      "cuisines": "Asian, North Indian, South Indian, Momos",
      "rating": "4.1/5",
      "cost": "₹2000 for two",
      "explanation": "Exact budget match with strong rating.",
      "source": "llm"
    }
  ],
  "summary": "Top picks for Bellandur.",
  "used_fallback": false,
  "warnings": []
}
```

**No match (`200`, `state: "no_match"`)**

```json
{
  "state": "no_match",
  "recommendations": [],
  "no_match_message": "No restaurants match your preferences.",
  "refine_hints": ["Try lowering minimum rating."]
}
```

**Validation error (`422`)**

```json
{
  "detail": [
    { "field": "budget", "message": "Invalid budget 'premium'. Allowed: high, low, medium." }
  ]
}
```

### Configuration

| Variable | Description |
| --- | --- |
| `GROQ_API_KEY` | Groq API key (required for LLM ranking) |
| `GROQ_MODEL` | Optional model override |
| `CORS_ORIGINS` | Allowed frontend origins (e.g. `http://localhost:5173`) |
| `PHASE1_STORE_PATH` | Override path to `restaurants_clean.json` |

---

## Phase 7: Frontend Web UI

**Goal:** Deliver the Zomato-style recommendation experience in the browser.

**Responsibilities**

- Render the preference form (Phase 2 fields)
- Fetch catalog data from Phase 6 for dropdowns/autocomplete
- Submit searches to `POST /recommend`
- Show loading state while Groq ranking runs
- Render Phase 5 recommendation cards
- Show empty state with refine hints when `state: "no_match"`
- Show fallback banner when `used_fallback: true`
- Disable duplicate submits while a request is in flight

**Stack**

- **React 18** — component UI
- **Vite** — dev server and build
- **TypeScript** — typed API client

**Input**

- User interactions (form submit)
- JSON from Phase 6 `/recommend` and `/catalog/*`

**Output**

- User-facing web application (browser)

**Architecture focus**

```text
User --> PreferenceForm --> POST /recommend (Phase 6)
                                |
User <-- RecommendationList <--- DisplayPayload JSON
```

**Folder structure**

```text
phase7_frontend_ui/
├── src/
│   ├── api/client.ts
│   ├── components/
│   │   ├── PreferenceForm.tsx
│   │   ├── RecommendationCard.tsx
│   │   ├── RecommendationList.tsx
│   │   ├── LoadingState.tsx
│   │   ├── EmptyState.tsx
│   │   └── FallbackBanner.tsx
│   ├── pages/Home.tsx
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

### UI components

| Component | Maps to | Responsibility |
| --- | --- | --- |
| `PreferenceForm` | Phase 2 | Location, budget, cuisine, min rating, notes |
| `RecommendationList` | Phase 5 | Ordered list of top-N cards |
| `RecommendationCard` | Phase 5 | Name, cuisine, rating, cost, explanation |
| `LoadingState` | Phase 7 | Spinner while Phase 6/4 runs |
| `EmptyState` | Phase 5 | No-match message + refine hints |
| `FallbackBanner` | Phase 4/5 | AI-unavailable notice |

### UI state flow

```text
idle --> submitting --> results
                   \-> no_match
                   \-> error
```

### Configuration

| Variable | Description |
| --- | --- |
| `VITE_API_BASE_URL` | Phase 6 backend URL (default `http://localhost:8000`) |

---

## Phase 8: Deployment (Streamlit)

**Goal:** Ship the recommendation pipeline as a single Streamlit app that users can run locally or host on Streamlit Community Cloud.

**Responsibilities**

- Provide a browser UI for Phase 2 preferences and Phase 5 recommendation cards
- Call Phase 6 `RecommendationService` in-process (no separate API server required)
- Load the Phase 1 clean store once at startup
- Keep `GROQ_API_KEY` server-side (`.env` or Streamlit secrets)
- Document install, run, and environment checklist

**Stack**

- **Streamlit** — UI and process host
- **Phase 6 `RecommendationService`** — orchestrates Phases 2–5
- **Phase 1 JSON cache** — restaurant store
- **Groq** — LLM ranking (with Phase 4 fallback)

**Input**

- User preferences from the Streamlit form
- Phase 1 clean store
- `.env` with `GROQ_API_KEY`

**Output**

- Running Streamlit application at `http://127.0.0.1:8501`

**Architecture focus**

```text
User browser --> Streamlit (phase8_deployment/app.py)
                        |
                        v
              RecommendationService (Phase 6)
                        |
          Phase 2 --> Phase 3 --> Phase 4 --> Phase 5
                        |
              Phase 1 JSON cache + Groq API
```

**Folder structure**

```text
phase8_deployment/
├── app.py                   # Streamlit UI
├── pipeline.py              # Runtime loader + search wrapper
├── config.py                # Store path and app title
├── __main__.py              # python -m phase8_deployment
├── requirements.txt
├── .streamlit/config.toml   # Zomato-red theme
└── README.md
```

### Local development

```text
python -m phase8_deployment
```

The React (Phase 7) + FastAPI (Phase 6) stack remains available as an alternative:

```text
Terminal 1:  python -m phase6_backend_api --reload
Terminal 2:  npm run dev   (Phase 7 on :5173)
```

### Configuration

| Variable | Description |
| --- | --- |
| `GROQ_API_KEY` | Groq API key (required for LLM ranking) |
| `GROQ_MODEL` | Optional model override |
| `PHASE1_STORE_PATH` | Override path to `restaurants_clean.json` |

### Production topology

| Component | Local Streamlit | Notes |
| --- | --- | --- |
| UI + pipeline | Streamlit `:8501` | Single process; no nginx required |
| Phase 1 data | Local JSON cache | Must exist before launch |
| Secrets | `.env` at project root | Never commit the key |

---

## End-to-End Flow (All Phases)

```text
1.  [Phase 1]  Ingest & cache clean Zomato data
2.  [Phase 8]  User fills preference form in Streamlit
3.  [Phase 6]  RecommendationService receives the request in-process
4.  [Phase 2]  Validates preferences
5.  [Phase 3]  Filters candidates & builds LLM prompt
6.  [Phase 4]  Groq ranks & explains
7.  [Phase 5]  Normalizes output for display
8.  [Phase 8]  Renders recommendation cards in Streamlit
```

## Design Rules Across Phases

- **Phase independence:** Each phase can be built and tested on its own
- **Filter before LLM:** Phase 3 reduces noise so Phase 4 reasons over relevant options only
- **Explainability:** Phase 4 must return reasons; Phase 5 and 7 must surface them
- **Clear contracts:** Every phase defines input and output so later phases stay stable
- **Secrets stay server-side:** `GROQ_API_KEY` lives in project-root `.env` (or Streamlit secrets) — never in the browser
- **Thin API, fat phases:** Phase 6 delegates to Phases 2–5; Phase 8 reuses that service instead of duplicating pipeline logic
- **UI is display + input:** Phase 7 and Phase 8 send preferences and render the display contract; no filtering or LLM calls in the UI
- **Graceful degradation:** Phase 4 fallback flows through Phase 5 and the UI with a visible banner
