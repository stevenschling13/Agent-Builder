import os
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from agents import Runner
from agents.triage import triage_agent

load_dotenv()
app = FastAPI(title="Agents SDK Starter")


class RunRequest(BaseModel):
    input: str


@app.post("/run")
async def run(req: RunRequest) -> Dict[str, Any]:
    if not req.input:
        raise HTTPException(400, "input required")
    # Use async API per SDK guidance; do not call run_sync inside async context.
    result = await Runner.run(triage_agent, req.input)
    return {"output": result.final_output}
