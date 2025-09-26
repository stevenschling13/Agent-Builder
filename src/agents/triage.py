import os
from typing import Literal
from pydantic import BaseModel
from agents import Agent, Runner, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from .guardrails import safety_gate, json_gate
from .github_tools import create_github_issue, get_repo_readme


class Outcome(BaseModel):
    kind: Literal["answer","issue_created","unknown"]
    summary: str
    actions: list[str] = []


# Specialized GitOps agent that focuses on issues
gitops_agent = Agent(
    name="GitOps",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You help create concise GitHub issues. When asked to open an issue, call the create_github_issue tool with:
- repo: from context env GITHUB_DEFAULT_REPO unless user specifies owner/repo
- title: 6–10 words, imperative
- body: short context, acceptance criteria checklist.
Return the created issue URL in your final text.""",
    model=os.getenv("MODEL","gpt-4o-mini"),
    tools=[create_github_issue],
)


# Primary triage agent
triage_agent = Agent(
    name="Triage",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are a deterministic assistant for planning and light GitOps. 
Use tools when necessary. Prefer answering directly. 
If the user asks to open an issue or track work, HANDOFF to GitOps.
When asked about a repo, use get_repo_readme.
Output must be a one-paragraph summary of up to 120 words.""",
    model=os.getenv("MODEL","gpt-4o-mini"),
    tools=[get_repo_readme],
    handoffs=[handoff(gitops_agent)],        # enable delegation to GitOps
    input_guardrails=[safety_gate],
    output_guardrails=[json_gate],
    output_type=Outcome,                      # enforce structured final output
)


def run_sync(user_input: str) -> Outcome:
    """Run the triage agent and return the structured Outcome."""
    result = Runner.run_sync(triage_agent, user_input)
    return result.final_output
