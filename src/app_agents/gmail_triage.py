"""Compatibility wrapper for legacy ``app_agents.gmail_triage`` imports."""

import os
from types import SimpleNamespace

from agents import Runner

from .triage import Outcome, triage_agent

__all__ = ["Outcome", "run_sync", "triage_agent"]


def _fallback_payload() -> dict[str, object]:
    return {
        "summary": "OpenAI API key not configured; returning offline stub.",
        "actions": [],
    }


def run_sync(user_input: str):
    """Run the triage agent synchronously with an offline fallback."""

    if not os.getenv("OPENAI_API_KEY"):
        return SimpleNamespace(payload=_fallback_payload())

    result = Runner.run_sync(triage_agent, user_input)
    # `RunResult` exposes ``final_output`` as the structured payload.
    payload = (
        result.final_output.model_dump()
        if hasattr(result.final_output, "model_dump")
        else result.final_output
    )
    return SimpleNamespace(payload=payload)
