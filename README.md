# 🍽️ Zomato AI Restaurant Recommendation Engine

An intelligent restaurant recommendation system inspired by Zomato that pairs structured dining data with Large Language Model reasoning. The engine combines multi-criteria filtering with fast Groq LLM inference to deliver transparent, personalized dining suggestions tailored to user tastes and ambience preferences. Built with a resilient hybrid architecture, it ensures instant responses with automatic fallback logic.

---

## 🚀 Key Features

- **Personalized Recommendations:** Curates top restaurants matching location, budget tier (`low`, `medium`, `high`), cuisines, and minimum rating thresholds.
- **Natural-Language Understanding:** Interprets free-form dining vibes and dietary requirements (e.g., *"quiet rooftop dining for an anniversary"*).
- **Deterministic Candidate Filtering:** Pre-screens real-world restaurant data to supply high-relevance candidates to the reasoning layer.
- **Explainable AI Output:** Provides clear, tailored justifications explaining *why* each suggested spot matches the diner's request.
- **Fail-Safe Heuristic Fallback:** Automatically switches to deterministic scoring if API limits or network issues arise, ensuring zero downtime.
- **Dual User Interfaces:** Offers both an interactive standalone Streamlit dashboard and a modern full-stack React web client.

---

## 🏗️ How It Works

```text
User Preferences ➔ Input Validation ➔ Restaurant Filtering ➔ Recommendation Engine ➔ Personalised Results
```

1. **User Preferences:** Diners specify their target city, budget band, cuisine choices, rating filter, and open-ended preferences.
2. **Input Validation:** Validates input parameters, normalizes location aliases, and sanitizes text against prompt injection.
3. **Restaurant Filtering:** Queries the preprocessed Zomato catalog to deterministically filter and rank candidate venues.
4. **Recommendation Engine:** Sends structured candidate data to Groq (`groq/compound-mini`) to reason over trade-offs and draft personalized rationales, backed by a deterministic fallback algorithm.
5. **Personalised Results:** Delivers normalized recommendation cards displaying ratings, cost for two, cuisine tags, and AI-generated explanations.

---

## 🛠️ Tech Stack

- **Interactive Web App:** Streamlit
- **Frontend:** React 18, TypeScript, Vite, Vanilla CSS
- **Backend API:** FastAPI, Uvicorn, Pydantic v2
- **AI / LLM:** Groq Cloud API (`groq/compound-mini`)
- **Data Processing:** Pandas, Hugging Face Datasets (`ManikaSaini/zomato-restaurant-recommendation`)
- **Deployment & DevOps:** Docker, Streamlit Community Cloud

---

## 📁 Project Structure

```text
phase1_data_ingestion/        Dataset ingestion, cleaning, and local caching
phase2_user_input/            Input validation, normalisation, and sanitisation
phase3_integration_layer/     Candidate filtering and dynamic prompt assembly
phase4_recommendation_engine/ LLM reasoning (Groq) and heuristic fallback ranking
phase6_backend_api/           FastAPI REST service and display normaliser
phase7_frontend_ui/           React + TypeScript web interface
phase8_deployment/            Streamlit standalone application
```

---

## 🚀 Run Locally

### 1. Clone and Install

```bash
git clone https://github.com/deeksha-v-hegde/zomato-ai-restaurant-recommendation.git
cd zomato-ai-restaurant-recommendation

# Install dependencies
pip install -r requirements.txt
pip install -r phase8_deployment/requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the root directory (see `.env.example`):

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=groq/compound-mini
```

*(Note: The application also runs in offline fallback mode without an API key.)*

### 3. Launch the Application

Start the Streamlit app:

```bash
streamlit run phase8_deployment/app.py
```

Open `http://localhost:8501` in your browser.

---

## 🌐 Live Demo

- **Live Streamlit App:** [Zomato AI Recommendations · Streamlit](https://zomato-ai-restaurant.streamlit.app/)


---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
