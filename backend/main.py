import asyncio
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from github import fetch_readme, fetch_repos_page
from analyzer import analyze_readme, configure

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable is not set.")

configure(GROQ_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sem = asyncio.Semaphore(5)


@app.get("/analyze")
async def analyze(
    username: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
):
    repos, total = await fetch_repos_page(username, page, per_page, GITHUB_TOKEN)

    if not repos:
        return {"results": [], "total": total, "page": page, "per_page": per_page}

    async def process(repo: dict) -> dict:
        async with sem:
            readme = await fetch_readme(repo["owner"]["login"], repo["name"], GITHUB_TOKEN)
            assessment = await analyze_readme(readme)
        return {
            "repo_name": repo["name"],
            "repo_url": repo["html_url"],
            "level": assessment["level"],
            "summary": assessment["summary"],
            "has_readme": readme is not None,
        }

    results = await asyncio.gather(*[process(r) for r in repos])
    return {"results": list(results), "total": total, "page": page, "per_page": per_page}
