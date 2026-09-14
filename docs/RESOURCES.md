# Project Resources & Context

This file is the single source of truth for external docs, SDKs, and decisions on this project. Refer to this file instead of asking the user to repeat links.

## Track
Agent Reliability, Security & Evaluation — YC Fall 2026 x Moss: Zero Latency Builder Sprint

## Core dependency: Moss
- Docs: https://docs.moss.dev/docs
- Getting Started: https://docs.moss.dev/docs/start/what-is-moss
- GitHub: https://github.com/usemoss/moss
- SDK (JS/TS): https://docs.moss.dev/docs/reference/js/api
- CLI: https://docs.moss.dev/docs/integrations/moss-cli
- Website: https://www.moss.dev/
- Offline-First Search: https://docs.moss.dev/docs/build/offline-first-search?utm_source=hidevshackathon&utm_medium=resources&utm_campaign=zero_latency_builder_sprint

## Key decisions
- Moss's official SDK is JavaScript/TypeScript. If backend is Python, either:
  a) call Moss via its REST API directly (check docs for REST endpoints), or
  b) switch backend to Node.js/Express to use the SDK natively
- Not using: Moss Offline-First Search (that's for a different track), LiveKit/Voice AI resources (different track, not relevant here)

## Project docs
- PRD: ./PRD.md
- Architecture: ./ARCHITECTURE.md

## Instruction to agent
Always check this file first before asking the user for links, SDK details, or track scope. If something here is unclear or missing, ask once and then update this file with the answer so it doesn't need to be asked again.
