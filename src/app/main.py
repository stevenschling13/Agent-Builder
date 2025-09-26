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
def run(req: RunRequest) -> Dict[str, Any]:
    if not req.input:
        raise HTTPException(400, "input required")
    result = Runner.run_sync(triage_agent, req.input)
    return {"output": result.final_output}
