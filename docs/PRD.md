# PRD: TrustMoss — Real-Time Trust Layer for AI Agents

## Track
Agent Reliability, Security & Evaluation (YC Fall 2026 x Moss: Zero Latency Builder Sprint)

## One-liner
A runtime guardrail layer that sits between an AI agent's retrieval step and its response, using Moss for fast context validation, and gives every answer a live trust score before it reaches the user.

## Problem
AI agents hallucinate, leak sensitive info, or answer confidently using irrelevant context, and most teams find out only after something goes wrong in production. There's no fast, real-time way to check "is this answer actually grounded in what we retrieved" before it reaches the user.

## Target user
Teams shipping customer-facing AI agents (support bots, internal knowledge assistants) who need to catch bad answers before they go out, not after.

## Why Moss matters here
Guardrails only work if they're fast enough not to break the user experience. Moss's low-latency retrieval lets us:
- Pull the original context back for comparison in near real time
- Run relevance checks against the knowledge base without adding noticeable delay
- Trace latency at each hop (retrieval, validation, LLM call) live

## Scope (MVP — 7 days)

**In scope:**
- One agent: a support/knowledge Q&A bot over a sample knowledge base
- Moss-powered retrieval as the knowledge source
- Three guardrail checks, run automatically on every query:
  1. **Context relevance check** — does the retrieved context actually match the query (score threshold before it's sent to the LLM)
  2. **Groundedness check** — does the LLM's answer actually reflect the retrieved context, or did it drift/hallucinate (simple overlap/similarity scoring between answer and context)
  3. **PII/leak check** — basic regex + pattern scan on the output before it's returned
- A live dashboard showing: query, latency breakdown per stage, trust score (pass/warn/fail), and why

**Out of scope (don't build this in 7 days):**
- Multi-agent orchestration
- Fine-tuned evaluation models (use simple, fast heuristics/embeddings, not a whole eval pipeline)
- User auth / multi-tenant support
- Voice or multimodal input

## User flow
1. User asks a question in the chat UI
2. Agent retrieves context from Moss
3. Guardrail validates the context is relevant before passing it to the LLM
4. LLM generates an answer
5. Guardrail checks the answer against the context and scans for leaks
6. Response is shown to the user along with a trust badge (green/yellow/red) and a "why" tooltip
7. Every step's latency is logged and shown on a live trace panel

## Core features (MVP)
1. Chat interface (simple, single page)
2. Moss retrieval integration
3. Guardrail validator module (3 checks above)
4. Real-time latency trace (per-hop timing, shown as a small bar/timeline per query)
5. Trust score badge + explanation on every response
6. Session log / history panel (so judges can scroll back through past queries during the demo)

## Success metrics (how you'll know it's working for the demo)
- Every query shows a visible trust score within ~1–2 seconds
- At least one demo query intentionally shows a "fail" or "warn" (e.g., ask something outside the knowledge base) so judges see the guardrail actually catching something
- Latency trace clearly shows Moss retrieval as the fast step (this is the point — prove Moss is fast, not the LLM call)

## Tech stack
- Backend: FastAPI (Python)
- Retrieval: Moss API
- LLM: any fast provider (Groq, OpenAI gpt-4o-mini, or similar — pick for speed)
- Embeddings for groundedness check: sentence-transformers or a fast embedding API
- Frontend: simple React or plain HTML/JS chat UI (don't over-build this)
- Deployment: Vercel (frontend) + Render/Railway (backend), or a single combined deploy if simpler

## Deliverables (per sprint rules)
- Architecture diagram (see ARCHITECTURE.md)
- This PRD
- GitHub repo (public)
- Deployed live link
- 2–3 min video demo showing: a normal query passing, a bad/off-topic query getting flagged, and the latency trace

## Day-by-day plan
- **Day 1:** Set up repo, FastAPI skeleton, Moss API access working, basic chat endpoint returning raw answers (no guardrails yet)
- **Day 2:** Build the knowledge base + get retrieval working end-to-end (query → Moss → context → LLM → answer)
- **Day 3:** Build guardrail check #1 (context relevance) and #2 (groundedness)
- **Day 4:** Build guardrail check #3 (PII/leak scan) + trust score logic combining all three
- **Day 5:** Build latency tracing (timestamp each stage, store per-query) + basic frontend chat UI
- **Day 6:** Build the trust badge UI + latency trace panel + session history panel, connect frontend to backend fully
- **Day 7:** Deploy, polish UI, write PRD/architecture docs (this), record demo video, submit

## Demo script (for the video)
1. Ask a normal question → show fast response + green trust badge + latency trace (highlight Moss's speed)
2. Ask an off-topic/unrelated question → show it get flagged (yellow/red badge) with the reason shown
3. Scroll the session history to show multiple queries logged
4. Briefly point at the architecture diagram and explain where Moss sits in the pipeline
