# OpenAI Gmail Agent

Deterministic Gmail triage + reply assistant using the OpenAI Agents SDK. Produces a structured summary, priority score, actions, and three reply drafts. CLI + FastAPI. **Drafts only**; never sends mail.

## Agent-mode Gmail credentials (headless)
Use env-provided credentials to avoid an interactive browser in hosted or agent environments.

1) Create a Google OAuth **Desktop App** client. Download `credentials.json`.
2) Generate `token.json` once using any environment where interactive OAuth is OK:
```bash
python - <<'PY'
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json
scopes = ["https://www.googleapis.com/auth/gmail.readonly","https://www.googleapis.com/auth/gmail.compose"]
flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes)
creds = flow.run_local_server(port=0)
open("token.json","w").write(creds.to_json())
print("token.json written")
PY
Base64 both files and place values in .env:
# linux
export GMAIL_CLIENT_SECRET_JSON_B64=$(base64 -w0 credentials.json)
export GMAIL_TOKEN_JSON_B64=$(base64 -w0 token.json)
# macOS
export GMAIL_CLIENT_SECRET_JSON_B64=$(base64 credentials.json | tr -d '\n')
export GMAIL_TOKEN_JSON_B64=$(base64 token.json | tr -d '\n')
Set HEADLESS_OAUTH=true in .env. The agent first tries env creds, then token.json, and only falls back to interactive OAuth if HEADLESS_OAUTH is not true.
Quickstart
cp .env.sample .env
python -m pip install -r requirements.txt
python -m src.app.cli "Help"         # CLI
uvicorn src.app.main:app --reload    # API
curl -s -X POST localhost:8000/run -H "Content-Type: application/json" \
  -d '{"input":"List 3 unread via list_messages, summarize and propose replies."}'
Notes
Scopes configurable via GMAIL_SCOPES.
token.json and credentials.json are gitignored.
Optional GitHub App secrets are supported if you later add GitHub tools.
