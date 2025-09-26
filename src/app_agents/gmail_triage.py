"""Definition of the Gmail triage agent and supporting sync wrapper."""
import os
from typing import Literal

from pydantic import BaseModel

from .gmail_tools import create_draft_new, create_draft_reply, get_message, list_messages
from .guardrails import TriageOut, json_gate, safety_gate
from .sdk import Agent, RECOMMENDED_PROMPT_PREFIX, Runner


class GmailResult(BaseModel):
    kind: Literal["analysis", "draft_created", "none"]
    payload: dict


gmail_model = os.getenv("MODEL", "gpt-4o-mini")

triage_agent = Agent(
    name="GmailTriage",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You triage Gmail messages and produce a deterministic summary, priority, actions, and three reply drafts.
Taxonomy:
Action Required {{Approval|Info Request|Deliverable|Follow-up}}
Scheduling {{Meeting Request|Reschedule|Availability}}
Sales/Finance {{Invoice/Bill|Payment|Pricing|Contract}}
Recruiting/Career {{Recruiter|Interview|Offer|HR}}
Operations {{Customer|Vendor|Internal Update}}
Notifications {{Receipt|System Alert}}
Personal/Other
Low-Value/Spam/Phishing
Scoring:
P = base(From:known=20|org=10|else=0) + intent(25|10|0) + time(≤48h=20|≤7d=10|0) + entities(+10 each money/date/attachment ≤20) + thread_depth(≥3=+10) − ambiguity(10) − risk(30).
Urgency: High if P≥80; Medium if 50–79; else Low.
Output TriageOut with fields filled. If risk, do not propose links or payments.""",
    model=gmail_model,
    tools=[list_messages, get_message, create_draft_new, create_draft_reply],
    input_guardrails=[safety_gate],
    output_guardrails=[json_gate],
    output_type=TriageOut,
)


def run_sync(user_input: str) -> GmailResult:
    out = Runner.run_sync(triage_agent, user_input).final_output
    return GmailResult(kind="analysis", payload=out.model_dump())
