"""Gmail API tools supporting headless env-based OAuth with interactive fallback."""
import os, base64, json
from typing import Optional, List, Dict, Any
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from agents import function_tool

def _scopes() -> list[str]:
    raw = os.getenv("GMAIL_SCOPES","https://www.googleapis.com/auth/gmail.readonly")
    return [s.strip() for s in raw.split(",") if s.strip()]

def _creds_from_env(scopes: list[str]) -> Optional[Credentials]:
    tok_b64 = os.getenv("GMAIL_TOKEN_JSON_B64","").strip()
    if not tok_b64:
        return None
    data = json.loads(base64.b64decode(tok_b64).decode())
    return Credentials.from_authorized_user_info(data, scopes=scopes)

def _client_cfg_from_env() -> Optional[dict]:
    cli_b64 = os.getenv("GMAIL_CLIENT_SECRET_JSON_B64","").strip()
    if not cli_b64:
        return None
    return json.loads(base64.b64decode(cli_b64).decode())

def _gmail_service():
    """Resolve credentials in priority: env token -> token.json -> interactive (unless HEADLESS_OAUTH=true)."""
    scopes = _scopes()
    # 1) Env token
    creds = _creds_from_env(scopes)
    if creds:
        if not creds.valid and creds.refresh_token:
            creds.refresh(Request())
        if creds.valid:
            return build("gmail","v1", credentials=creds)

    # 2) token.json file
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", scopes)
        if not creds.valid and creds.refresh_token:
            creds.refresh(Request())
        return build("gmail","v1", credentials=creds)

    # 3) Interactive fallback if allowed
    if os.getenv("HEADLESS_OAUTH","").lower() == "true":
        raise RuntimeError("HEADLESS_OAUTH=true but no GMAIL_TOKEN_JSON_B64 or token.json available")
    client_cfg = _client_cfg_from_env()
    if client_cfg:
        flow = InstalledAppFlow.from_client_config(client_cfg, scopes)
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes)
    creds = flow.run_local_server(port=0)
    try:
        with open("token.json","w") as f:
            f.write(creds.to_json())
    except Exception:
        pass
    return build("gmail","v1", credentials=creds)

def _mime_new(to: str, subject: str, body: str, sender: Optional[str] = None) -> str:
    msg = EmailMessage()
    msg.set_content(body)
    if sender:
        msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()

def _mime_reply(to: str, subject: str, body: str, in_reply_to: str, references: str) -> str:
    msg = EmailMessage()
    msg.set_content(body)
    msg["To"] = to
    msg["Subject"] = subject
    msg["In-Reply-To"] = in_reply_to
    msg["References"] = references
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()

@function_tool
async def list_messages(label: str = None, query: str = None, max_results: int = 5) -> List[str]:
    """Return message IDs from the user's mailbox based on label and/or query."""
    service = _gmail_service()
    kwargs: Dict[str, Any] = {"userId": "me", "maxResults": max_results}
    if label:
        kwargs["labelIds"] = [label]
    if query:
        kwargs["q"] = query
    resp = service.users().messages().list(**kwargs).execute()
    return [m["id"] for m in resp.get("messages", [])]

@function_tool
async def get_message(msg_id: str) -> Dict[str, Any]:
    """Fetch a message in 'full' format. Returns headers, snippet, body_text, threadId."""
    service = _gmail_service()
    m = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    headers = {h["name"].lower(): h["value"] for h in m["payload"].get("headers", [])}

    def _walk(payload):
        if payload.get("body", {}).get("data"):
            try:
                return base64.urlsafe_b64decode(payload["body"]["data"]).decode(errors="ignore")
            except Exception:
                return ""
        for p in payload.get("parts", []) or []:
            text = _walk(p)
            if text:
                return text
        return ""

    body_text = _walk(m["payload"])
    return {
        "id": m["id"],
        "threadId": m.get("threadId"),
        "headers": headers,
        "snippet": m.get("snippet", ""),
        "body_text": body_text,
    }

@function_tool
async def create_draft_new(to: str, subject: str, body: str) -> Dict[str, str]:
    """Create a new draft email."""
    service = _gmail_service()
    raw = _mime_new(to, subject, body)
    draft = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )
    return {"draft_id": draft["id"], "message_id": draft["message"]["id"]}

@function_tool
async def create_draft_reply(
    thread_id: str,
    to: str,
    subject: str,
    body: str,
    in_reply_to: str,
) -> Dict[str, str]:
    """Create a reply draft in an existing thread. Requires In-Reply-To Message-ID."""
    service = _gmail_service()
    raw = _mime_reply(to, subject, body, in_reply_to=in_reply_to, references=in_reply_to)
    draft = (
        service.users()
        .drafts()
        .create(
            userId="me",
            body={"message": {"raw": raw, "threadId": thread_id}},
        )
        .execute()
    )
    return {"draft_id": draft["id"], "message_id": draft["message"]["id"]}
