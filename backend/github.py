import base64
import httpx
from fastapi import HTTPException

GITHUB_API = "https://api.github.com"


def _headers(token: str | None) -> dict:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


async def fetch_user_public_repo_count(
    username: str,
    client: httpx.AsyncClient,
    token: str | None = None,
) -> int:
    """Fetch the total number of public repositories for a given user."""
    resp = await client.get(f"{GITHUB_API}/users/{username}", headers=_headers(token))

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail=f"GitHub user '{username}' not found.")
    if resp.status_code in (403, 429):
        raise HTTPException(status_code=429, detail="GitHub API rate limit exceeded.")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="GitHub API error.")

    return resp.json().get("public_repos", 0)


async def fetch_repos_page(
    username: str,
    page: int,
    per_page: int,
    client: httpx.AsyncClient,
    token: str | None = None,
) -> list[dict]:
    """Fetch a single page of public repositories for a user."""
    resp = await client.get(
        f"{GITHUB_API}/users/{username}/repos",
        params={"per_page": per_page, "type": "public", "page": page, "sort": "updated"},
        headers=_headers(token),
    )

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail=f"GitHub user '{username}' not found.")
    if resp.status_code in (403, 429):
        raise HTTPException(status_code=429, detail="GitHub API rate limit exceeded.")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="GitHub API error.")

    return resp.json()


async def fetch_readme(
    owner: str,
    repo: str,
    client: httpx.AsyncClient,
    token: str | None = None,
) -> str | None:
    """Fetch and decode a repo's README, truncated to 3000 chars. Returns None if absent."""
    resp = await client.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/readme",
        headers=_headers(token),
    )

    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        return None

    try:
        content = base64.b64decode(resp.json()["content"]).decode("utf-8", errors="replace")
        return content[:3000] if content.strip() else None
    except Exception:
        return None
