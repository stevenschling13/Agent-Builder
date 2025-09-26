from agents.triage import run_sync

def test_smoke():
    out = run_sync("Summarize this repo starter in 1 sentence.")
    assert hasattr(out, "summary")
