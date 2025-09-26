from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from agents import Runner
from agents.gmail_triage import triage_agent

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
