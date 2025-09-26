# OpenAI Agents Starter

## Overview
This starter demonstrates core OpenAI Agents SDK primitives including agents, tools, handoffs, guardrails, and sessions. The `Runner.run_sync` helper executes the agent loop end-to-end so you can synchronously evaluate responses in the CLI, HTTP server, or tests.

## Models
The triage agent defaults to the model specified by the `MODEL` environment variable (defaults to `gpt-4o-mini`). Update the `.env.sample` file or runtime environment to target other supported models.

## Guardrails
Input and output guardrails register tripwires via the SDK decorators. `safety_gate` rejects destructive or credential-related prompts, while `json_gate` ensures structured responses are neither empty nor overly long.

## Tools and Handoffs
Function tools decorated with `@function_tool` empower agents with capabilities such as fetching README files or creating GitHub issues. The triage agent can hand off to the specialized GitOps agent whenever issue tracking is needed, enabling delegated workflows.

## GitHub Integration
To enable the `create_github_issue` tool, set `GITHUB_TOKEN` and `GITHUB_DEFAULT_REPO` in your environment. Without a token the tool returns an informative message instead of raising.

## Run the Agent
- CLI: `python -m src.app.cli "open an issue: bug in onboarding flow"`
- API: `uvicorn src.app.main:app --reload` then POST `{ "input": "..." }` to `/run`.

## Tracing and Observability
The Agents SDK ships with tracing, logging, and run configuration hooks. Refer to the SDK documentation for enabling advanced telemetry or external observers in production.

## Safety and Operations
Never hardcode secrets; rely on environment variables or secret managers. Deploy behind a process manager to enforce rate limits and graceful restarts for sustained workloads.
