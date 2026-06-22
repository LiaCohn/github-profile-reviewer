import asyncio
import logging
import os
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from github import fetch_readme, fetch_repos_page, fetch_user_public_repo_count
from analyzer import analyze_readme, configure

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable is not set.")
if not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_TOKEN environment variable is not set.")


# --- Pydantic models ---

class RepoResult(BaseModel):
    repo_name: str
    repo_url: str
    level: str
    summary: str
    has_readme: bool


# --- App lifecycle ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure(GROQ_API_KEY)
    app.state.http_client = httpx.AsyncClient(timeout=15)
    app.state.sem = asyncio.Semaphore(5)
    yield
    await app.state.http_client.aclose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Helpers ---

async def process_repo(repo: dict, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> RepoResult:
    async with sem:
        readme = await fetch_readme(repo["owner"]["login"], repo["name"], client, GITHUB_TOKEN)
        assessment = await analyze_readme(readme)
    return RepoResult(
        repo_name=repo["name"],
        repo_url=repo["html_url"],
        level=assessment["level"],
        summary=assessment["summary"],
        has_readme=readme is not None,
    )


# --- Routes ---

@app.get("/user-public-repo-count")
async def user_public_repo_count(
    username: str = Query(..., min_length=1),
):
    return await fetch_user_public_repo_count(username, app.state.http_client, GITHUB_TOKEN)


@app.get("/analyze", response_model=list[RepoResult])
async def analyze(
    username: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
):
    repos = await fetch_repos_page(username, page, per_page, app.state.http_client, GITHUB_TOKEN)

    if not repos:
        return []

    results = await asyncio.gather(
        *[process_repo(r, app.state.http_client, app.state.sem) for r in repos]
    )
    return list(results)
