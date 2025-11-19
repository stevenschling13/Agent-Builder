import os
from typing import Literal
from pydantic import BaseModel
from agents import Agent, Runner, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from .guardrails import safety_gate, json_gate, MessageOut
from .github_tools import create_github_issue, get_repo_readme


class Outcome(BaseModel):
    kind: Literal["answer","issue_created","unknown"]
    summary: str
    actions: list[str] = []


gitops_agent = Agent(
    name="GitOps",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You help create concise GitHub issues. When asked to open an issue, call create_github_issue with:
- repo: from env GITHUB_DEFAULT_REPO unless user specifies owner/repo
- title: 6–10 words, imperative
- body: short context + acceptance criteria checklist.
Return the created issue URL in your final text.""",
    model=os.getenv("MODEL","gpt-4o-mini"),
    tools=[create_github_issue],
)


triage_agent = Agent(
    name="Triage",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are a deterministic planner and light GitOps assistant.
Prefer direct answers. When asked to open an issue, HANDOFF to GitOps.
Use get_repo_readme when the user asks about a repo.
Respond with one paragraph <=120 words.""",
    model=os.getenv("MODEL","gpt-4o-mini"),
    tools=[get_repo_readme],
    handoffs=[handoff(gitops_agent)],
    input_guardrails=[safety_gate],
    output_guardrails=[json_gate],
    output_type=Outcome,
)


def run_sync(user_input: str) -> Outcome:
    """Synchronous helper for CLI contexts."""
    return Runner.run_sync(triage_agent, user_input).final_output
