# Phase 8: Streamlit deployment

Single-app deployment of the Zomato recommendation pipeline. The Streamlit UI calls the same Phase 6 `RecommendationService` in-process (Phases 2 → 3 → 4 → 5). FastAPI and the React UI are not required to run this app.

## Prerequisites

- Python 3.10+
- Phase 1 cache at `phase1_data_ingestion/data/cache/restaurants_clean.json`
- Project-root `.env` with `GROQ_API_KEY` (optional; fallback ranking is used without it)

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

## Install

From the repository root:

```powershell
pip install -r phase8_deployment/requirements.txt
pip install -r phase1_data_ingestion/requirements.txt
pip install -r phase4_recommendation_engine/requirements.txt
```

## Run locally

From the repository root:

```powershell
python -m phase8_deployment
```

Or:

```powershell
streamlit run phase8_deployment/app.py --server.port 8501
```

Open http://127.0.0.1:8501

## Environment

| Variable | Description |
| --- | --- |
| `GROQ_API_KEY` | Groq API key for LLM ranking |
| `GROQ_MODEL` | Optional model override |
| `PHASE1_STORE_PATH` | Override path to `restaurants_clean.json` |

## Tests

```powershell
python -m unittest phase8_deployment.tests.test_pipeline
```
