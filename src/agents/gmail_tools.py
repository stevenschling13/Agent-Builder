import os, base64, time, re
from typing import Optional, List, Dict, Any
from email.message import EmailMessage
from agents import function_tool
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = tuple(s.strip() for s in os.getenv("GMAIL_SCOPES","https://www.googleapis.com/auth/gmail.readonly").split(","))


def _gmail_service():
    """OAuth desktop flow using credentials.json; caches token.json."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json","w") as f:
            f.write(creds.to_json())
    return build("gmail","v1", credentials=creds)


@function_tool
async def list_messages(label: str = None, query: str = None, max_results: int = 5) -> List[str]:
    """Return message IDs from the user's mailbox based on label and/or query."""
    service = _gmail_service()
    kwargs = {"userId":"me","maxResults":max_results}
    if label: kwargs["labelIds"] = [label]
    if query: kwargs["q"] = query
    resp = service.users().messages().list(**kwargs).execute()
    return [m["id"] for m in resp.get("messages",[])]


@function_tool
async def get_message(msg_id: str) -> Dict[str, Any]:
    """Fetch a message in 'full' format. Returns headers, snippet, body_text, threadId."""
    service = _gmail_service()
    m = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    headers = {h["name"].lower(): h["value"] for h in m["payload"].get("headers", [])}

    def _walk(payload):
        if payload.get("body",{}).get("data"):
            try: return base64.urlsafe_b64decode(payload["body"]["data"]).decode(errors="ignore")
            except Exception: return ""
        for p in payload.get("parts",[]) or []:
            t = _walk(p)
            if t: return t
        return ""

    body_text = _walk(m["payload"])
    return {"id": m["id"], "threadId": m.get("threadId"), "headers": headers, "snippet": m.get("snippet",""), "body_text": body_text}


def _mime_new(to: str, subject: str, body: str, sender: Optional[str] = None) -> str:
    msg = EmailMessage()
    msg.set_content(body)
    if sender: msg["From"] = sender
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
async def create_draft_new(to: str, subject: str, body: str) -> Dict[str,str]:
    """Create a new draft email."""
    service = _gmail_service()
    raw = _mime_new(to, subject, body)
    draft = service.users().drafts().create(userId="me", body={"message":{"raw": raw}}).execute()
    return {"draft_id": draft["id"], "message_id": draft["message"]["id"]}


@function_tool
async def create_draft_reply(thread_id: str, to: str, subject: str, body: str, in_reply_to: str) -> Dict[str,str]:
    """Create a reply draft in an existing thread. Requires In-Reply-To Message-ID."""
    service = _gmail_service()
    raw = _mime_reply(to, subject, body, in_reply_to=in_reply_to, references=in_reply_to)
    draft = service.users().drafts().create(userId="me", body={"message":{"raw": raw, "threadId": thread_id}}).execute()
    return {"draft_id": draft["id"], "message_id": draft["message"]["id"]}
