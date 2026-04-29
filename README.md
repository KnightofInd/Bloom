# Bloom — Lifecycle-Aware Recommendations for Baby & Maternity

Calm, caring recommendations for every stage of pregnancy and postpartum recovery. Bloom maps free-text needs to a controlled vocabulary, retrieves top products using embeddings and FAISS, and explains results with an LLM-backed narrative. It also supports lifecycle-based recommendations using last menstrual period (LMP) dates to infer trimester and augment needs. The system is built as a modular pipeline with a FastAPI service and a lightweight web UI.

## 📖 Overview
Bloom is an AI-powered recommendation system for baby and maternity ecommerce. It combines controlled vocabulary mapping with semantic retrieval to deliver consistent, relevant product suggestions. The pipeline is designed for reliability: it has lexical and numpy fallbacks, lazy-loaded heavy dependencies, and deterministic explanations when LLMs are unavailable. A lifecycle workflow augments user queries with trimester-specific needs to keep recommendations stage-appropriate.

## 🧠 Problem & Solution
**Problem:** Free-form user needs in maternity ecommerce are ambiguous, and product catalogs are large and noisy. This leads to low-quality search results, inconsistent recommendations, and weak personalization for pregnancy stages.

**Solution:** Bloom extracts structured needs from user input, anchors them to a controlled vocabulary, retrieves products via embeddings + FAISS (with fallbacks), and adds context-aware explanations. When an LMP date is provided, Bloom infers the trimester and augments needs with lifecycle-specific items to keep results aligned with the user’s stage.

## 🏗️ Architecture
Bloom is organized into small modules with a thin orchestration layer:

- **core.py**: data loading, embedding/index utilities, lifecycle computation, context inference, filters, and normalization.
- **extraction.py**: controlled-vocabulary mapping, heuristics, Gemini-based extraction, and lifecycle augmentation prompt.
- **retrieval.py**: retrieval backends (FAISS, numpy cosine, lexical overlap) with context-aware re-ranking.
- **explain.py**: Gemini or fallback explanation generation.
- **pipeline.py**: orchestration of extraction → retrieval → filtering → explanation with lifecycle augmentation support.
- **recommend_api.py**: FastAPI endpoints for standard and lifecycle recommendations; serves the UI.
- **ui/**: HTML/CSS/JS frontend for search and lifecycle flows.

Data flow:
1) Ingest products and embeddings (build if missing).
2) Extract needs (vocab/heuristic/Gemini).
3) Optionally augment needs based on lifecycle stage.
4) Retrieve candidates with FAISS (fallbacks: numpy, lexical).
5) Filter and re-rank with context.
6) Generate explanation (Gemini or local fallback).

## ⚙️ Tech Stack
**Frontend**
- HTML, CSS, Vanilla JS

**Backend**
- FastAPI
- Uvicorn

**AI/ML**
- SentenceTransformers (`all-MiniLM-L6-v2`)
- FAISS (IndexFlatL2)
- Gemini API (generateContent)

**Data**
- JSON product catalog
- NumPy embeddings

**Tools**
- Python 3.10+

## ✨ Features
- Controlled vocabulary mapping of free-text needs
- Lifecycle recommendations from LMP date (trimester inference)
- FAISS semantic retrieval with numpy and lexical fallbacks
- Context-aware filtering and re-ranking
- LLM-generated explanations with safe local fallback
- FastAPI service + lightweight UI

## 🔄 Workflow / How It Works
1. User submits a query (and optional LMP date).
2. Lifecycle stage is inferred from LMP (first/second/third trimester or postpartum).
3. Needs are extracted from the query and augmented with lifecycle needs.
4. Embedding-based retrieval returns candidate products.
5. Products are filtered by rating/price and re-ranked using context.
6. The system generates a concise explanation and returns results.

## 🧪 Example Use Case
A user enters: “I am 7 months pregnant and have back pain.”
- Bloom infers third trimester and augments needs with support items.
- It retrieves top-rated maternity care products, prioritizing support belts and pregnancy pillows.
- The UI returns a ranked list with a short explanation tailored to late pregnancy.

## 📦 Installation & Setup
```bash
# Create and activate a virtual environment
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Set your Gemini API key (optional but recommended):
```bash
# Windows
setx GEMINI_API_KEY "YOUR_KEY"
# macOS/Linux
export GEMINI_API_KEY="YOUR_KEY"
```

Run the API and UI:
```bash
python -m uvicorn recommend_api:app --host 127.0.0.1 --port 8000
```
Open: http://127.0.0.1:8000

## 🚀 Future Improvements
- Add caching for embeddings and LLM outputs
- Add automated tests for extraction and lifecycle logic
- Introduce ranking metrics and offline evaluation
- Expand lifecycle logic for postpartum stages
- Add Docker image and production deployment templates

## 🤝 Contribution
- Fork the repo and create a feature branch
- Keep changes modular (core/extraction/retrieval/explain/pipeline)
- Add or update tests when modifying logic
- Open a PR with a clear description of changes

## 📄 License
MIT

---

## One-paragraph Summary
Bloom is an AI-powered lifecycle-aware recommendation system for maternity and baby care. It translates a user’s free-text needs into structured intents, augments them with pregnancy stage (via LMP), and retrieves relevant products with contextual explanations. The system ensures stage-appropriate recommendations, reduces ambiguity in search, and improves personalization for expecting and new mothers.

## Prototype Access
- GitHub Repo: https://github.com/KnightofInd
- Demo Video (Loom-style): https://drive.google.com/file/d/15WSOrb7y1fk64ym0gkIMGRAIE8Em2ClA/view

## Discovery
**Persona**
A 28-year-old pregnant woman (first pregnancy), navigating products for health, comfort, and baby preparation.

**Observations while exploring Mumzworld**
- Free-text search leads to inconsistent and noisy results
- No lifecycle-awareness (trimester-specific needs ignored)
- Overwhelming product catalog without contextual reasoning
- Weak personalization beyond basic filtering

**Chosen Problem**
Lack of context-aware, lifecycle-based product recommendations.

**Why this problem**
- High-impact: directly affects purchase decisions
- Repeated across user journeys
- Cannot be solved with static UX improvements alone

## Why AI
A traditional system (filters, categories) fails because:
- User intent is ambiguous ("back pain", "baby prep", etc.)
- Needs evolve dynamically across pregnancy stages
- Context must be inferred, not explicitly selected

AI enables:
- Semantic understanding of user queries
- Lifecycle inference (trimester awareness)
- Context-aware ranking and explanations

Without AI, this becomes rigid and rule-based. With AI, it becomes adaptive and personalized.

## Working Prototype
**System Built:** Bloom

**Core pipeline**
- User input (query + optional LMP)
- Lifecycle inference (trimester/postpartum)
- Need extraction (controlled vocabulary + LLM fallback)
- Retrieval (FAISS + embedding similarity)
- Context-aware filtering & re-ranking
- Explanation generation (LLM or fallback)

**Key capabilities**
- Free-text → structured needs
- Lifecycle-aware augmentation
- Semantic retrieval over product catalog
- Explainable recommendations

**Modular architecture**
- Extraction layer
- Retrieval layer
- Explanation layer
- FastAPI backend + lightweight UI

## Show Your Work
**Tools used**
- Gemini API → extraction + explanations
- SentenceTransformers → embeddings
- FAISS → vector search
- FastAPI → backend
- HTML/CSS/JS → UI

**Timeline log (approx.)**
- 0–1 hr → Problem discovery + framing
- 1–2 hr → Architecture + pipeline design
- 2–4 hr → Core implementation (extraction + retrieval)
- 4–5 hr → UI + explanation layer + testing

**Prompts that mattered**
- Need extraction prompt (structured vocabulary mapping)
- Lifecycle augmentation prompt (trimester-aware needs)
- Explanation generation prompt (concise + grounded output)

**Refinement focused on**
- Reducing hallucination
- Forcing structured outputs
- Improving clarity of explanations

**Dead ends**
- Pure keyword search → low relevance
- Over-reliance on LLM → inconsistent outputs
- No lifecycle modeling → generic recommendations

**Cuts from scope**
- Multilingual (EN/AR) support
- Real-time evaluation dashboard
- Advanced ranking metrics

**Reflection**
- Lifecycle awareness drastically improves relevance
- Hybrid systems (AI + rules) outperform pure LLM setups
- Retrieval quality matters more than generation quality

## Measurement
**Leading indicator (Week 1)**
Click-through rate on recommended products.

**Experiment plan**
- Run A/B test (5% users with Bloom vs baseline)
- Success = higher CTR + lower search abandonment
- Failure = no improvement or irrelevant recommendations

## AI Usage Note
Used Gemini API for structured extraction and explanations, SentenceTransformers + FAISS for semantic retrieval, and ChatGPT/Cursor for iterative development and debugging. AI assisted in prompt design, pipeline structuring, and refinement of outputs.

## Time Log
- Discovery: 1 hr
- Design: 1 hr
- Implementation: 2 hrs
- Testing + UI: 1 hr
- Total: ~5 hrs
