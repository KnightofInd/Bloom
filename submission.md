# Bloom - AI Lifecycle-Aware Recommendations for Mothers

## Summary
Bloom is an AI-powered recommendation system designed for maternity and baby-care e-commerce. It transforms ambiguous free-text queries into structured needs, augments them with pregnancy lifecycle context (via LMP), and retrieves relevant products with clear, grounded explanations. The system improves personalization, reduces search friction, and ensures stage-appropriate recommendations for expecting and new mothers.

## Track
Track B - AI-Native Product Intern

## Prototype Access
- GitHub Repository: https://github.com/KnightofInd/Bloom
- Demo Walkthrough (Video): https://drive.google.com/file/d/15WSOrb7y1fk64ym0gkIMGRAIE8Em2ClA/view

## 1. Discovery
**Persona**

A 28-year-old first-time pregnant woman navigating maternity and baby-care products. She is unsure what she needs at each stage and relies heavily on search and recommendations.

**Observed Problems**
- Free-text search returns inconsistent and noisy results
- No lifecycle awareness (trimester-specific needs ignored)
- Overwhelming product catalog without prioritization
- Lack of contextual explanations for recommendations

**Chosen Problem**

Lack of lifecycle-aware, context-driven product recommendations

**Why This Problem**
- Directly impacts purchase decisions
- Repeated across multiple user journeys
- Cannot be solved effectively with static filters or UX tweaks
- High leverage for improving user experience and conversion

## 2. Why AI
This problem fundamentally requires understanding and inference, not just filtering.

**Traditional Systems Fail Because**
- User intent is ambiguous ("back pain", "baby essentials")
- Needs evolve dynamically across pregnancy stages
- Context must be inferred, not explicitly selected

**AI Enables**
- Semantic understanding of user intent
- Lifecycle inference (trimester-based needs)
- Context-aware ranking of products
- Natural-language explanations

Without AI -> rigid, rule-based system.
With AI -> adaptive, personalized experience.

## 3. Working Prototype
**System Overview**

Bloom is built as a modular AI pipeline:

- User Input
  - Free-text query
  - Optional LMP (Last Menstrual Period)
- Lifecycle Inference
  - Determines trimester or postpartum stage
- Need Extraction
  - Controlled vocabulary mapping
  - LLM-assisted fallback
- Retrieval
  - Embedding-based search (FAISS)
  - Fallbacks: cosine similarity + lexical matching
- Filtering and Ranking
  - Context-aware re-ranking
  - Product quality filtering
- Explanation Layer
  - AI-generated reasoning
  - Deterministic fallback if needed

**Key Features**
- Free-text -> structured intent mapping
- Lifecycle-aware recommendations
- Semantic retrieval over product catalog
- Explainable outputs
- Robust fallback mechanisms

**Architecture**
- Backend: FastAPI
- AI/ML: SentenceTransformers + FAISS + Gemini API
- Frontend: HTML, CSS, JS
- Data: JSON + embeddings

## 4. Show Your Work
**Tools Used**
- Gemini API -> extraction + explanations
- SentenceTransformers -> embeddings
- FAISS -> semantic retrieval
- FastAPI -> backend APIs
- ChatGPT / Cursor -> development assistance

**Timeline (approx. 5 hours)**
- 0-1 hr -> Problem discovery + framing
- 1-2 hr -> Architecture design
- 2-4 hr -> Core pipeline implementation
- 4-5 hr -> UI + testing + refinement

**Prompts That Mattered**
- Structured need extraction prompt
- Lifecycle augmentation prompt
- Explanation generation prompt

**Key Improvements**
- Reduced hallucination
- Enforced structured outputs
- Improved explanation clarity

**Dead Ends**
- Keyword-based retrieval -> poor relevance
- Over-reliance on LLM -> inconsistent results
- No lifecycle modeling -> generic outputs

**Cuts From Scope**
- Multilingual support (EN/AR)
- Advanced ranking metrics
- Evaluation dashboard

**Reflection**
- Lifecycle context dramatically improves relevance
- Hybrid systems (AI + deterministic logic) are more reliable
- Retrieval quality is more critical than generation quality

## 5. Measurement
**Primary Metric (Week 1)**

Click-Through Rate (CTR) on recommended products

**Experiment Plan**
Run 5% A/B test:
- Control -> existing search
- Variant -> Bloom recommendations

**Success Criteria**
- Higher CTR
- Reduced search abandonment
- Increased engagement

**Failure Indicators**
- No CTR improvement
- Irrelevant recommendations
- High drop-off after recommendation

## 6. AI Usage Note
Used Gemini API for extraction and explanation generation, SentenceTransformers + FAISS for retrieval, and AI-assisted tools (ChatGPT/Cursor) for pipeline design, prompt engineering, and iterative debugging.

## 7. Time Log
- Discovery: 1 hr
- Design: 1 hr
- Implementation: 2 hrs
- Testing/UI: 1 hr
- Total: ~5 hrs

## 8. Tradeoffs
**Why This Problem**

Chosen for high user impact and alignment with Mumzworld's core experience.

**Model and Architecture Choices**
- Embeddings + FAISS -> fast and scalable retrieval
- LLM -> only where reasoning is required
- Fallback systems -> ensure reliability

**Handling Uncertainty**
- Controlled vocabulary mapping
- Fallback retrieval methods
- Deterministic explanations when LLM unavailable

**Known Limitations**
- No multilingual support
- Limited evaluation dataset
- No real-time personalization feedback loop

**Next Steps**
- Add Arabic + English multilingual support
- Introduce evaluation metrics and dashboards
- Improve ranking with user interaction data

## 9. How to Run (Optional)
```bash
git clone https://github.com/KnightofInd
cd bloom

python -m venv .venv
source .venv/bin/activate  # or Windows equivalent

pip install -r requirements.txt

python -m uvicorn recommend_api:app --host 127.0.0.1 --port 8000
```

Open: http://127.0.0.1:8000
