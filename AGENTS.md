# Agent Development Guide

## Project purpose

This workspace implements a health-insurance claims processing pipeline using LangGraph, Pydantic, and Groq-assisted extraction. It must never invent missing claim values.

## Source layout

- `claims_agent/agents/`: domain agent implementations and facades.
- `claims_agent/tools/`: external tools such as Groq extraction.
- `claims_agent/factory/`: dependency composition and agent construction.
- `claims_agent/database/`: repositories and persistence adapters.
- `claims_agent/schemas/`: public Pydantic contracts.
- `claims_agent/orchestration/`: LangGraph construction and execution.
- `claims_agent/services/`: application use-case boundaries.
- `claims_agent/api/`: FastAPI app, routes, and HTTP adapters.
- `claims_agent/config/`: environment and runtime settings.
- `tests/`: unit and integration tests.
- `example.py`: demonstration runner for named test cases.

## Change rules

- Keep LLM output separate from deterministic policy and fraud checks.
- Preserve `"UNKNOWN"`, `null`, or empty values for unreadable fields; never infer IDs or medical codes.
- Keep Pydantic schemas strict and backward-compatible when possible.
- Do not expose API keys or raw secret values in logs.
- Deterministic code should have tests before changing the LangGraph routing.
- Database implementations must remain behind repository interfaces.
- HTTP code must call the service layer, not LangGraph internals directly.

## Commands

```bash
source .venv/bin/activate
.venv/bin/python -m pytest -q
.venv/bin/python example.py all
.venv/bin/uvicorn claims_agent.api.app:app --reload --host 0.0.0.0 --port 8000
```

## API test

```bash
curl -X POST http://127.0.0.1:8000/api/claims/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"raw_document_text":"Claim ID: C-1","policy_details":{},"historical_claims":[]}'
```
