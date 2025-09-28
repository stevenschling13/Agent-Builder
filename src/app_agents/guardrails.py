"""Guardrail helpers used by the Gmail triage agent."""

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
    input_guardrail,
    output_guardrail,
)
from pydantic import BaseModel


class MessageOut(BaseModel):
    response: str


@input_guardrail
async def safety_gate(
    ctx: RunContextWrapper[None],
    agent: Agent,
    user_input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Trip on destructive ops or credential sharing."""

    text = user_input if isinstance(user_input, str) else " ".join(
        (i.input_text or "") for i in user_input
    )
    banned = ("delete repo", "share password", "drop database", "wipe data")
    hit = any(k in text.lower() for k in banned)
    return GuardrailFunctionOutput(output_info={"banned_hit": hit}, tripwire_triggered=hit)


@output_guardrail
async def json_gate(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: MessageOut,
) -> GuardrailFunctionOutput:
    """Trip if empty or excessive length."""

    length = len(output.response) if getattr(output, "response", None) else 0
    hit = (length == 0) or (length > 5000)
    return GuardrailFunctionOutput(output_info={"len": length}, tripwire_triggered=hit)
