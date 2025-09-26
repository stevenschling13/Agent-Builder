# OpenAI Gmail Agent

Deterministic Gmail triage + reply assistant using the OpenAI Agents SDK. Produces a structured summary, priority score, actions, and three reply drafts. Provides a CLI and a FastAPI endpoint. Drafts only; never sends mail.

## Quickstart
```bash
cp .env.sample .env
python -m pip install -r requirements.txt
# place your Google OAuth client as credentials.json in repo root
python -m src.app.cli "Help"         # basic run
uvicorn src.app.main:app --reload    # API mode
curl -s -X POST localhost:8000/run -H "Content-Type: application/json" \
  -d '{"input":"List 3 unread via list_messages, summarize and propose replies."}'
```
OAuth
First tool use triggers a browser OAuth; token.json is cached. Adjust scopes via GMAIL_SCOPES in .env.
Safety
Guardrails reject destructive instructions. Gmail tools create drafts only.
