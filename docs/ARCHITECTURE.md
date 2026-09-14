# Architecture: TrustMoss

## High-level flow

```
                              AgentGuard
                                  │
                 ┌────────────────┼────────────────┐
                 ▼                ▼                ▼
              Web App           API             Agent
           React + Vite     FastAPI /query    Python AI
                 │                │                │
                 │                │                ▼
                 │                │        ┌─────────────────┐
                 │                │        │ Stage 1         │
                 │                │        │ Moss Retrieval   │
                 │                │        │                 │
                 │                │        │ Top-k Context   │
                 │                │        │ Relevance Score │
                 │                │        │ Retrieval Time  │
                 │                │        └────────┬────────┘
                 │                │                 │
                 │                │                 ▼
                 │                │        ┌─────────────────┐
                 │                │        │ Stage 2         │
                 │                │        │ Context          │
                 │                │        │ Relevance Check  │
                 │                │        │                 │
                 │                │        │ PASS / WARN      │
                 │                │        └────────┬────────┘
                 │                │                 │
                 │                │                 ▼
                 │                │        ┌─────────────────┐
                 │                │        │ Stage 3         │
                 │                │        │ LLM Generation  │
                 │                │        │                 │
                 │                │        │ Context + Query │
                 │                │        │ → Answer        │
                 │                │        └────────┬────────┘
                 │                │                 │
                 │                │                 ▼
                 │                │        ┌─────────────────┐
                 │                │        │ Stage 4         │
                 │                │        │ Groundedness    │
                 │                │        │ Check            │
                 │                │        │                 │
                 │                │        │ Answer ↔ Context│
                 │                │        │ → Grounding     │
                 │                │        │   Score         │
                 │                │        └────────┬────────┘
                 │                │                 │
                 │                │                 ▼
                 │                │        ┌─────────────────┐
                 │                │        │ Stage 5         │
                 │                │        │ PII / Leak Scan │
                 │                │        │                 │
                 │                │        │ Sensitive Data  │
                 │                │        │ Detection       │
                 │                │        │ → REDACT/BLOCK  │
                 │                │        └────────┬────────┘
                 │                │                 │
                 │                │                 ▼
                 │                │        ┌─────────────────┐
                 │                │        │ Stage 6         │
                 │                │        │ Trust Aggregator │
                 │                │        │                 │
                 │                │        │ Relevance       │
                 │                │        │ Grounding       │
                 │                │        │ Safety          │
                 │                │        │ Latency         │
                 │                │        │        ↓        │
                 │                │        │ PASS / WARN /   │
                 │                │        │ FAIL + Score    │
                 │                │        └────────┬────────┘
                 │                │                 │
                 │                ◄─────────────────┘
                 │                │
                 │                ▼
                 │        Response + Evaluation
                 │        + Trust Score + Trace
                 │                │
                 ◄────────────────┘
                 │
                 ▼
        ┌──────────────────────────┐
        │ AgentGuard Dashboard     │
        │                          │
        │ • AI Response            │
        │ • Trust Badge            │
        │ • Context Sources        │
        │ • Relevance Score        │
        │ • Grounding Score        │
        │ • Safety Status          │
        │ • Retrieval Latency      │
        │ • LLM Latency            │
        │ • Evaluation Trace       │
        └──────────────────────────┘
```


The clean high-level version for your PRD
AgentGuard
│
├── Web
│   └── React + Vite
│
├── API
│   └── FastAPI
│
└── Agent
    ├── Moss Retrieval
    ├── Context Relevance
    ├── LLM Generation
    ├── Groundedness Evaluation
    ├── PII / Leak Detection
    └── Trust Score Aggregation


## Component breakdown

### 1. Moss Retrieval Client
- Wraps Moss API calls
- Input: user query
- Output: list of context chunks, each with a relevance/similarity score, plus retrieval latency
- This is the piece you want to visibly show is fast in your demo, log its latency separately from everything else

### 2. Guardrail Validator (core of the project)
Three independent checks, each returns `{passed: bool, score: float, reason: str}`:

**a. Context Relevance Check**
- Runs right after retrieval, before the LLM call
- Takes Moss's relevance scores for retrieved chunks
- If the top score is below a threshold (e.g. 0.6), flag as low relevance
- Purpose: catch cases where the knowledge base has nothing useful, so you don't let the LLM guess

**b. Groundedness Check**
- Runs after the LLM generates an answer
- Embed the answer and embed the retrieved context (use a fast embedding model)
- Compute cosine similarity between them
- If similarity is low, the LLM likely drifted or hallucinated beyond what was retrieved
- Purpose: this is your main "reliability" story, prove the answer is actually grounded in retrieved data, not made up

**c. PII / Leak Scan**
- Simple regex-based scan on the final answer text
- Patterns: email, phone number, credit card-like numbers, API key patterns, SSN-like patterns
- If matched, flag and optionally redact before returning
- Purpose: security angle, catch accidental leaks before they reach the user

### 3. Latency Tracer
- Wrap each stage (Moss retrieval, relevance check, LLM call, groundedness check, PII scan) with a timer
- Store per-query: `{stage: name, duration_ms: X}` for all 5 stages
- Return this array alongside the response so the frontend can render a simple timeline bar
- This is what makes Moss's speed visible and provable, not just claimed

### 4. Trust Score Aggregator
- Simple weighted logic, not a model:
  - All 3 checks pass → **PASS** (green)
  - 1 check fails/warns → **WARN** (yellow)
  - 2+ checks fail, or PII leak detected → **FAIL** (red, response withheld or redacted)
- Returns the score plus a short human-readable reason ("Answer didn't closely match retrieved context")

### 5. Backend API (FastAPI)
- `POST /query` — main endpoint, runs the full pipeline, returns answer + trust data + latency trace
- `GET /history` — returns session's past queries and their trust results (for the demo history panel)

### 6. Frontend (simple chat UI)
- Chat input + message list
- Each agent response shows: answer text, trust badge (color + label), expandable "why" section, latency trace mini-bar
- Sidebar or bottom panel: session history list

## Data flow for a single query (concrete example)

1. User sends: "What's our refund policy for digital products?"
2. Backend calls Moss → gets 3 chunks about refund policy, top score 0.89, latency 8ms
3. Relevance check: 0.89 > 0.6 threshold → PASS
4. LLM generates answer using those 3 chunks as context, latency 650ms
5. Groundedness check: embed answer vs embed context → similarity 0.82 → PASS
6. PII scan: no matches → PASS
7. Trust Aggregator: all 3 pass → **PASS**, green badge
8. Response returned with full latency trace: Moss 8ms, LLM 650ms, checks ~40ms combined
9. Frontend renders answer + green badge + timeline showing Moss as the fast step

## Tech choices and reasoning
- **FastAPI**: fast to build with, async support fits well with calling Moss + LLM concurrently where possible
- **Moss**: retrieval backbone, the whole point of the sprint
- **Embeddings for groundedness**: use a lightweight/fast embedding model (don't add a slow model here, it defeats the purpose of proving speed)
- **Regex for PII**: intentionally simple and fast, not an ML classifier, this is a 7-day sprint, not a production security product
- **Frontend**: keep minimal, a clean single-page chat interface is enough, don't spend time on a full design system

## Suggested repo structure

```
trustmoss/
├── backend/
  |      |──.venv/
│   ├── main.py                 # FastAPI app, /query and /history routes
│   ├── moss_client.py          # Moss API wrapper
│   ├── guardrails/
│   │   ├── relevance.py
│   │   ├── groundedness.py
│   │   └── pii_scan.py
│   ├── trust_score.py          # aggregator logic
│   ├── tracer.py                # latency timing utility
│   └── requirements.txt
├── frontend/
│   ├── index.html / App.jsx
│   ├── components/
│   │   ├── ChatWindow
│   │   ├── TrustBadge
│   │   ├── LatencyTrace
│   │   └── HistoryPanel
│   └── package.json
├── PRD.md
├── ARCHITECTURE.md
└── README.md
```

## Notes for building in for You
- Build backend stages in isolation first (test `/query` with curl/Postman before touching frontend)
- Get Moss retrieval + LLM call working end-to-end before adding any guardrail logic, that's your fallback demo if guardrails run out of time
- Add guardrails one at a time, test each independently
- Keep thresholds as config variables (not hardcoded) so you can tune them live if a demo query doesn't behave as expected
