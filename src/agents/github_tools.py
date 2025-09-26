import os, httpx
from agents import function_tool


@function_tool
async def create_github_issue(repo: str, title: str, body: str = "") -> str:
    """Create a GitHub issue in owner/repo. Requires env GITHUB_TOKEN. Returns 'STATUS URL'."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "missing GITHUB_TOKEN"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            f"https://api.github.com/repos/{repo}/issues",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            json={"title": title, "body": body},
        )
        j = r.json() if r.content else {}
        return f"{r.status_code} {j.get('html_url','')}"


@function_tool
async def get_repo_readme(repo: str) -> str:
    """Fetch README.md from the repo main branch via raw.githubusercontent.com."""
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"https://raw.githubusercontent.com/{repo}/main/README.md")
        return r.text if r.status_code == 200 else f"error {r.status_code}"
