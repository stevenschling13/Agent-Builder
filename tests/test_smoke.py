import os, pytest
from agents.gmail_triage import run_sync


@pytest.mark.skipif(os.getenv("CI")=="true", reason="skip network on CI")
def test_smoke():
    out = run_sync("Classify and propose replies for a generic scheduling email.")
    assert "summary" in out.payload
