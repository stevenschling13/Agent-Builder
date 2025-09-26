from pydantic import BaseModel
from agents import (
    Agent, Runner,
    GuardrailFunctionOutput,
    RunContextWrapper, TResponseInputItem,
    input_guardrail, output_guardrail,
)


class MessageOut(BaseModel):
    response: str


@input_guardrail
async def safety_gate(ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]) -> GuardrailFunctionOutput:
    """Trip if user requests destructive ops or credentials."""
    text = input if isinstance(input, str) else " ".join([i.input_text or "" for i in input])  # tolerate list inputs
    banned = ("delete repo", "share password", "drop database")
    trip = any(k in text.lower() for k in banned)
    return GuardrailFunctionOutput(output_info={"banned_hit": trip}, tripwire_triggered=trip)


@output_guardrail
async def json_gate(ctx: RunContextWrapper[None], agent: Agent, output: MessageOut) -> GuardrailFunctionOutput:
    """Trip if response is empty or overlong."""
    trip = (not output.response) or (len(output.response) > 5000)
    return GuardrailFunctionOutput(output_info={"len": len(output.response) if output.response else 0}, tripwire_triggered=trip)
