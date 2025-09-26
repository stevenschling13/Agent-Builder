"""SDK shim for the OpenAI Agents SDK."""
try:
    from openai.agents import (
        Agent,
        Runner,
        function_tool,
        input_guardrail,
        output_guardrail,
        GuardrailFunctionOutput,
        RunContextWrapper,
        TResponseInputItem,
        handoff,
    )
    from openai.agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
except Exception:
    from agents import (  # legacy package name fallback
        Agent,
        Runner,
        function_tool,
        input_guardrail,
        output_guardrail,
        GuardrailFunctionOutput,
        RunContextWrapper,
        TResponseInputItem,
        handoff,
    )
    from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
