"""FastAPI entrypoint for the Gmail triage agent."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from app_agents.gmail_triage import triage_agent
from app_agents.sdk import Runner

load_dotenv()
app = FastAPI(title="OpenAI Gmail Agent")


class RunRequest(BaseModel):
    input: str


@app.post("/run")
async def run(req: RunRequest):
    if not req.input:
        raise HTTPException(400, "input required")
    result = await Runner.run(triage_agent, req.input)
    return {"output": result.final_output}
