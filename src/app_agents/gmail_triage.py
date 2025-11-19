"""Gmail triage agent wired to the OpenAI Agents SDK."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, Field

from agents import Agent, Runner
from agents.run import RunResult
from app_agents.gmail_tools import (
    create_draft_new,
    create_draft_reply,
    get_message,
    list_messages,
)


class GmailTriagePayload(BaseModel):
    """Structured output from the Gmail triage agent."""

    summary: str = Field(..., description="One-paragraph summary of the email thread.")
    priority: int = Field(..., ge=1, le=5, description="1 (low) to 5 (urgent) priority score.")
    actions: List[str] = Field(default_factory=list, description="Next steps for the user.")
    drafts: List[str] = Field(default_factory=list, description="Reply drafts to choose from.")


triage_agent = Agent(
    name="Gmail Triage",
    instructions=(
        "You triage Gmail threads. Provide a concise summary, priority 1 (low) to 5 "
        "(urgent), a short action list, and 3 brief reply drafts. Use the Gmail tools "
        "when the user asks to fetch context or create drafts. Keep responses clear and "
        "deterministic."
    ),
    model=os.getenv("MODEL", "gpt-4o-mini"),
    tools=[list_messages, get_message, create_draft_new, create_draft_reply],
    output_type=GmailTriagePayload,
)


@dataclass
class TriageResponse:
    """Wrapper exposing a dict payload for easy assertions."""

    payload: dict
    run_result: Optional[RunResult]


def _offline_payload(user_input: str) -> dict:
    """Deterministic fallback when no API key is configured."""

    return {
        "summary": f"Offline triage placeholder for: {user_input}",
        "priority": 1,
        "actions": ["Set OPENAI_API_KEY to enable live Gmail triage."],
        "drafts": ["Thanks for reaching out. I'll follow up shortly."],
    }


async def run(user_input: str) -> TriageResponse:
    if not os.getenv("OPENAI_API_KEY"):
        return TriageResponse(payload=_offline_payload(user_input), run_result=None)

    result = await Runner.run(triage_agent, user_input)
    payload = (
        result.final_output.model_dump()
        if hasattr(result.final_output, "model_dump")
        else result.final_output
    )
    return TriageResponse(payload=payload, run_result=result)


def run_sync(user_input: str) -> TriageResponse:
    if not os.getenv("OPENAI_API_KEY"):
        return TriageResponse(payload=_offline_payload(user_input), run_result=None)

    result = Runner.run_sync(triage_agent, user_input)
    payload = (
        result.final_output.model_dump()
        if hasattr(result.final_output, "model_dump")
        else result.final_output
    )
    return TriageResponse(payload=payload, run_result=result)
