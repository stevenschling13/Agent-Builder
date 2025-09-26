# OpenAI Agents SDK Starter

## What you get
- Python starter using the OpenAI Agents SDK with tools, handoffs, and guardrails.
- CLI and FastAPI server.
- Optional GitHub issue tool.

## Quickstart
```bash
cp .env.sample .env   # add OPENAI_API_KEY, optional GitHub vars
python -m pip install -r requirements.txt
python -m src.app.cli "help"
uvicorn src.app.main:app --reload
curl -s -X POST localhost:8000/run -H "Content-Type: application/json" -d '{"input":"open an issue: onboarding bug"}'
```
