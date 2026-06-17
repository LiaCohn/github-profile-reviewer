import base64
import httpx
from fastapi import HTTPException

GITHUB_API = "https://api.github.com"


def _headers(token: str | None) -> dict:
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


async def fetch_repos(username: str, token: str | None = None) -> list[dict]:
    repos: list[dict] = []
    page = 1
    async with httpx.AsyncClient(timeout=15) as client:
        while True:
            url = f"{GITHUB_API}/users/{username}/repos?per_page=100&type=public&page={page}"
            resp = await client.get(url, headers=_headers(token))

            if page == 1 and resp.status_code == 404:
                raise HTTPException(status_code=404, detail=f"GitHub user '{username}' not found.")
            if resp.status_code in (403, 429):
                raise HTTPException(status_code=429, detail="GitHub API rate limit exceeded.")
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="GitHub API error.")

            batch = resp.json()
            if not batch:
                break
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1

    return repos


async def fetch_readme(owner: str, repo: str, token: str | None = None) -> str | None:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/readme"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=_headers(token))

    if resp.status_code == 404:
        return None
    if resp.status_code not in (200,):
        return None

    data = resp.json()
    try:
        content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return content[:3000] if content.strip() else None
    except Exception:
        return None
