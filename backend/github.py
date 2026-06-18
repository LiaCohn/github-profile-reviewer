import base64
import httpx
from fastapi import HTTPException

GITHUB_API = "https://api.github.com"

def _headers(token: str | None) -> dict:
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

async def fetch_user_public_repo_count(username: str, token: str | None = None) -> int:
    """Fetch the total number of public repositories for a specific user"""
    url = f"{GITHUB_API}/users/{username}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=_headers(token))
        
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail=f"GitHub user '{username}' not found.")
        if resp.status_code in (403, 429):
            raise HTTPException(status_code=429, detail="GitHub API rate limit exceeded.")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="GitHub API error.")
            
        data = resp.json()
        return data.get("public_repos", 0)

async def fetch_repos_page(
    username: str,
    page: int,
    per_page: int,
    token: str | None = None,
) -> list[dict]:
    """Fetch a specific page of public repositories for a user, along with the total number of public repositories"""
    # total = await fetch_user_public_repo_count(username, token)
    
    # if total == 0:
    #     return [], 0

    # Fetch the specific page of public repositories for the user
    url = f"{GITHUB_API}/users/{username}/repos?per_page={per_page}&type=public&page={page}"
    
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=_headers(token))
        
        if resp.status_code in (403, 429):
            raise HTTPException(status_code=429, detail="GitHub API rate limit exceeded.")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="GitHub API error.")
            
        repos_slice = resp.json()
        return repos_slice

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
