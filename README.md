# OpenAI Gmail Agent
## Modes
- Tool mode: Agent uses Gmail tools to list messages by label or query, fetch a message, and create drafts (new or reply).
- Paste mode: Provide raw content via `/run` input.
## Gmail auth
- Place `credentials.json` in repo root (OAuth client). First run creates `token.json`. Scopes from `GMAIL_SCOPES`. For drafts you need `gmail.compose` or `gmail.modify`.
## Quickstart
```bash
cp .env.sample .env
python -m pip install -r requirements.txt
# first-run OAuth will open a browser to consent
python -m src.app.cli "List 3 unread in INBOX using list_messages and then summarize each."
uvicorn src.app.main:app --reload
curl -s -X POST localhost:8000/run -H "Content-Type: application/json" \
  -d '{"input":"Fetch latest unread with list_messages, then for msg <ID> propose three replies and create a draft reply to the sender."}'
```
