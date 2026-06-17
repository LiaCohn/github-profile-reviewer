# GitHub Repo Analyzer

Analyze any GitHub user's public repositories using Groq (Llama 3.3 70B). Each repo is assessed as Basic, Intermediate, Advanced, or NA based on its README.

## Assumptions & Limitations

- **All public repos fetched** — GitHub's API returns up to 100 repos per page; the backend paginates automatically to fetch all pages.
- **README truncation** — README content is truncated to 3,000 characters before being sent to the AI to keep costs and latency low.
- **Public repos only** — private repositories are never fetched or analyzed.
- **No caching** — every analysis request hits the GitHub and Groq APIs fresh. Re-analyzing the same user makes new API calls.
- **NA for missing READMEs** — repos without a README cannot be assessed and receive an NA badge.

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with your API keys:
```
GROQ_API_KEY=your_groq_key_here
GITHUB_TOKEN=your_github_token_here  # optional, raises rate limit from 60 to 5000 req/hr
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).  
Get a GitHub token (no scopes needed) at [github.com/settings/tokens](https://github.com/settings/tokens).

Run the backend:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

## Usage

1. Open `http://localhost:5173` in your browser.
2. Enter a GitHub username and click **Analyze**.
3. Wait while repos and READMEs are fetched and analyzed.
4. Browse the result cards — each shows the repo name (linked), a level badge, and a short AI-generated summary.

## Levels

| Badge | Meaning |
|-------|---------|
| **Basic** | Beginner-friendly project, simple structure |
| **Intermediate** | Moderate complexity, some experience required |
| **Advanced** | High complexity, advanced concepts |
| **NA** | No README available — could not assess |

## API

### `POST /analyze?username={github_username}`

Returns a list of analyzed repositories (up to 100):

```json
[
  {
    "repo_name": "my-project",
    "repo_url": "https://github.com/user/my-project",
    "level": "Intermediate",
    "summary": "This project demonstrates solid use of async patterns...",
    "has_readme": true
  }
]
```

**Error responses:**
- `404` — GitHub user not found
- `429` — GitHub API rate limit exceeded
- `502` — GitHub API unavailable

## Future Improvements

- **Streaming results** — use Server-Sent Events to stream each repo's analysis back to the frontend as it completes, so cards appear one by one instead of all at once after a long wait
- **Lazy-loaded pagination** — fetch all repo metadata upfront, display 10 at a time, and trigger AI analysis for the next batch only when the user scrolls near the bottom (infinite scroll)
- **Result caching** — cache analysis results per username/repo so repeat lookups don't re-call the AI API
- **Fork filtering** — optionally skip forked repositories since they rarely have original READMEs worth analyzing
- **Sort options** — allow sorting results by level, name, or last updated date
