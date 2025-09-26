"""Command-line interface for the Gmail triage agent."""
import sys

from dotenv import load_dotenv

from app_agents.gmail_triage import triage_agent
from app_agents.sdk import Runner


def main() -> None:
    load_dotenv()
    prompt = " ".join(sys.argv[1:]) or "Help"
    result = Runner.run_sync(triage_agent, prompt)
    print(result.final_output)


if __name__ == "__main__":
    main()
