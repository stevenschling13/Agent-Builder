"""Local shim that re-exports the Agents SDK primitives we use.

This keeps imports inside the ``app_agents`` package consistent with
our ``src`` layout while avoiding circular imports.
"""
from agents import Agent, Runner, function_tool, input_guardrail, output_guardrail
from agents import RunContextWrapper, GuardrailFunctionOutput, TResponseInputItem

__all__ = [
    "Agent",
    "Runner",
    "function_tool",
    "input_guardrail",
    "output_guardrail",
    "RunContextWrapper",
    "GuardrailFunctionOutput",
    "TResponseInputItem",
]
