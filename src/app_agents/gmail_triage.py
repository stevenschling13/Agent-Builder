"""Deterministic Gmail triage assistant.

The goal is to provide a predictable, test-friendly response shape even
when no API keys are configured. The module produces a structured
payload with a concise summary, a priority score, a short list of
actions, and three lightweight reply drafts.
"""
from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, Field

# Import Gmail tools so downstream callers can wire them into an LLM-backed
# Agent if desired. We don't call them inside the deterministic fallback to
# keep tests self contained.
from . import gmail_tools  # noqa: F401


class Draft(BaseModel):
    """Simple email draft representation used in the payload."""

    subject: str
    body: str
    to: Optional[str] = None


class GmailTriagePayload(BaseModel):
    """Structured output expected by downstream automation."""

    summary: str = Field(..., description="Concise 1–3 sentence overview of the request")
    priority_score: int = Field(..., ge=1, le=5, description="1=low, 5=urgent")
    actions: List[str] = Field(default_factory=list, description="Ordered task list")
    drafts: List[Draft] = Field(default_factory=list, description="Draft replies")
    reasoning: Optional[str] = Field(None, description="Lightweight rationale used for debugging")


@dataclass
class GmailTriageResult:
    """Wrapper matching the ``result.payload`` access pattern used in tests."""

    payload: dict
    structured: GmailTriagePayload


_KEYWORDS_PRIORITY = {
    "urgent": 5,
    "asap": 5,
    "immediately": 5,
    "today": 4,
    "schedule": 3,
    "meeting": 3,
    "follow up": 3,
    "question": 2,
}


def _priority(text: str) -> int:
    lowered = text.lower()
    score = 1
    for kw, val in _KEYWORDS_PRIORITY.items():
        if kw in lowered:
            score = max(score, val)
    return score


def _summarize(text: str) -> str:
    cleaned = " ".join(text.split()) or "General request"
    return textwrap.shorten(cleaned, width=220, placeholder="…")


def _actions(text: str) -> List[str]:
    lowered = text.lower()
    acts: List[str] = []
    if any(w in lowered for w in ["schedule", "meeting", "call"]):
        acts.append("Propose times and confirm the meeting context.")
    if any(w in lowered for w in ["question", "clarify", "details"]):
        acts.append("Answer the question and ask for any missing details.")
    if any(w in lowered for w in ["follow", "update", "status"]):
        acts.append("Provide a brief status update with next steps.")
    if not acts:
        acts.append("Acknowledge the email and provide a concise next step.")
    return acts[:3]


def _drafts(summary: str, actions: List[str], priority: int) -> List[Draft]:
    tone = "quick" if priority >= 4 else "thoughtful"
    next_step = actions[0] if actions else "Provide a helpful reply."
    base_subject = "Re: " + textwrap.shorten(summary, width=60, placeholder="…")

    drafts = [
        Draft(subject=base_subject, body=f"Thanks for the note—{summary} I'll {next_step.lower()}", to=None),
        Draft(
            subject=base_subject,
            body=(
                "Hi there,\n\n" + summary + "\n\n" +
                f"Proposed next step: {next_step} This is a {tone} check-in."
            ),
            to=None,
        ),
        Draft(
            subject=base_subject,
            body=(
                "Appreciate the context. I captured the request as: " + summary +
                "\nLet me know if you'd like me to adjust the plan or timing."
            ),
            to=None,
        ),
    ]
    return drafts


def run_sync(user_input: str) -> GmailTriageResult:
    """Deterministic triage helper used by the smoke test.

    We avoid external network calls to keep the workflow reliable in
    constrained environments. The returned object mirrors the ``payload``
    shape the rest of the application expects so it can be swapped with
    an LLM-backed agent later.
    """

    summary = _summarize(user_input)
    priority_score = _priority(user_input)
    actions = _actions(user_input)
    drafts = _drafts(summary, actions, priority_score)
    payload_model = GmailTriagePayload(
        summary=summary,
        priority_score=priority_score,
        actions=actions,
        drafts=drafts,
        reasoning=f"priority={priority_score} via keyword heuristic",
    )
    return GmailTriageResult(payload=payload_model.model_dump(), structured=payload_model)
