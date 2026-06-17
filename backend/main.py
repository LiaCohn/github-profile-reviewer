import asyncio
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from github import fetch_readme, fetch_repos
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


sem = asyncio.Semaphore(5) #limit the number of concurrent requests to 5


@app.post("/analyze")
async def analyze(username: str = Query(..., min_length=1)):
    repos = await fetch_repos(username, GITHUB_TOKEN)

    if not repos:
        return []

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
    return list(results)
