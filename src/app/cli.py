import os, sys
from dotenv import load_dotenv
from agents import Runner
from project_agents.triage import triage_agent


def main():
    load_dotenv()
    prompt = " ".join(sys.argv[1:]) or "help"
    result = Runner.run_sync(triage_agent, prompt)
    print(result.final_output)


if __name__ == "__main__":
    main()
