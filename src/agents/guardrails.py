from pydantic import BaseModel
from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, TResponseInputItem, input_guardrail, output_guardrail


class TriageOut(BaseModel):
    category: str
    subcategory: str | None = None
    priority: int
    urgency: str
    summary: str
    actions: list[str] = []
    reply_quick: str
    reply_professional: str
    reply_detailed: str
    json_payload: dict
    confidence: float


@input_guardrail
async def safety_gate(ctx: RunContextWrapper[None], agent: Agent, user_input: str | list[TResponseInputItem]) -> GuardrailFunctionOutput:
    text = user_input if isinstance(user_input, str) else " ".join([(i.input_text or "") for i in user_input])
    banned = ("share password","wire funds","send credentials","delete repo","drop database")
    hit = any(k in text.lower() for k in banned)
    return GuardrailFunctionOutput(output_info={"banned": hit}, tripwire_triggered=hit)


@output_guardrail
async def json_gate(ctx: RunContextWrapper[None], agent: Agent, output: TriageOut) -> GuardrailFunctionOutput:
    ok = bool(getattr(output, "summary", "")) and 0 <= getattr(output, "confidence", 0) <= 1
    return GuardrailFunctionOutput(output_info={"ok": ok}, tripwire_triggered=(not ok))
