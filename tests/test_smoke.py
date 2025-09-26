import os, pytest
from agents.triage import run_sync


@pytest.mark.skipif(os.getenv("CI")=="true", reason="skip network on CI")
def test_smoke():
    out = run_sync("Summarize this starter in 1 sentence.")
    assert hasattr(out, "summary")
