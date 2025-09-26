import os
from typing import Literal
from pydantic import BaseModel
from agents import Agent, Runner, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from .guardrails import safety_gate, json_gate, TriageOut
from .gmail_tools import list_messages, get_message, create_draft_new, create_draft_reply


class GmailResult(BaseModel):
    kind: Literal["analysis","draft_created","none"]
    payload: dict


triage_agent = Agent(
    name="GmailTriage",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You triage Gmail messages and produce a deterministic summary, priority, actions, and three reply drafts.
Taxonomy:
- Action Required {{Approval|Info Request|Deliverable|Follow-up}}
- Scheduling {{Meeting Request|Reschedule|Availability}}
- Sales/Finance {{Invoice/Bill|Payment|Pricing|Contract}}
- Recruiting/Career {{Recruiter|Interview|Offer|HR}}
- Operations {{Customer|Vendor|Internal Update}}
- Notifications {{Receipt|System Alert}}
- Personal/Other
- Low-Value/Spam/Phishing
Scoring:
P = base(From:known=20|org=10|else=0) + intent(25|10|0) + time(≤48h=20|≤7d=10|0) + entities(+10 each money/date/attachment ≤20) + thread_depth(≥3=+10) − ambiguity(10) − risk(30).
Urgency: High if P≥80; Medium if 50–79; else Low.
Output TriageOut with fields filled. If risk, do not propose links or payments.""",
    model=os.getenv("MODEL","gpt-4o-mini"),
    tools=[list_messages, get_message, create_draft_new, create_draft_reply],
    input_guardrails=[safety_gate],
    output_guardrails=[json_gate],
    output_type=TriageOut,
)


def run_sync(user_input: str) -> GmailResult:
    """Synchronous helper."""
    out = Runner.run_sync(triage_agent, user_input).final_output
    return GmailResult(kind="analysis", payload=out.model_dump())
