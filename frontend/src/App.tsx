import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import RepoCard from "./components/RepoCard";
import { repoService, RepoResult } from "./services/api";
import "./App.css";

const PER_PAGE = 10;

export default function App() {
  const [username, setUsername] = useState("");
  const [analyzedUsername, setAnalyzedUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<RepoResult[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [filterComplexity, setFilterComplexity] = useState<"all" | "basic" | "intermediate" | "advanced" | "na">("all");

  const sentinelRef = useRef<HTMLDivElement | null>(null);

  // Client-side filtering based on selected complexity level
  const filteredResults = results.filter((r) =>
    filterComplexity === "all" || r.level.toLowerCase() === filterComplexity
  );

  // Fetches a specific page batch of repositories and analyzes them
  const fetchPage = useCallback(async (user: string, pageNum: number, currentTotal?: number) => {
    setLoading(true);
    try {
      const reposBatch = await repoService.getAnalyzedRepos(user, pageNum, PER_PAGE);

      // Clear list on page 1 for a new search, otherwise append results to the end
      setResults((prev) => (pageNum === 1 ? reposBatch : [...prev, ...reposBatch]));
      setPage(pageNum);

      // Determine if there are more repositories left to load
      // Use the newly fetched total for page 1, fallback to existing state for subsequent pages
      const effectiveTotal = currentTotal !== undefined ? currentTotal : total;
      setHasMore((pageNum * PER_PAGE) < effectiveTotal);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? `Error ${err.response?.status}`);
      } else {
        setError("Could not reach the server. Is the backend running?");
      }
    } finally {
      setLoading(false);
    }
  }, [total]);

  // Main trigger function when user clicks the Analyze button
  async function handleAnalyze() {
    const trimmed = username.trim();
    if (!trimmed) return;

    setAnalyzedUsername(trimmed);
    setFilterComplexity("all");
    setError(null);
    setResults([]);
    setTotal(0); // Critical reset so old counts don't linger in the UI during loading
    setHasMore(false);
    setLoading(true);

    try {
      // Step 1: Call the dedicated endpoint to fetch the total repo count exactly once
      const totalCount = await repoService.getRepoCount(trimmed);
      setTotal(totalCount);

      // Stop execution early if the user exists but has 0 public repositories
      if (totalCount === 0) {
        setHasMore(false);
        setLoading(false);
        return;
      }

      // Step 2: Trigger the first page load and feed it the fresh total count
      await fetchPage(trimmed, 1, totalCount);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? "Failed to fetch repository count.");
      } else {
        setError("Could not reach the server. Is the backend running?");
      }
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleAnalyze();
  }

  // IntersectionObserver — fires when the sentinel div scrolls into view
  useEffect(() => {
    if (!sentinelRef.current || !hasMore || loading) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          fetchPage(analyzedUsername, page + 1);
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [hasMore, loading, page, analyzedUsername, fetchPage]);

  return (
    <div className="page">
      <header className="header">
        <h1 className="title">GitHub Repo Analyzer</h1>
        <p className="subtitle">Enter a GitHub username to analyze their public repositories.</p>
      </header>

      <div className="search-row">
        <input
          className="input"
          type="text"
          placeholder="GitHub username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading && results.length === 0}
        />
        <button className="button" onClick={handleAnalyze} disabled={loading || !username.trim()}>
          {loading && results.length === 0 ? "Analyzing…" : "Analyze"}
        </button>
      </div>

      {loading && results.length === 0 && (
        <div className="status-text">Fetching repos and analyzing READMEs…</div>
      )}

      {error && (
        <div className="error-box">{error}</div>
      )}

      {!loading && results.length === 0 && analyzedUsername && !error && (
        <div className="status-text">No public repositories found for <strong>{analyzedUsername}</strong>.</div>
      )}

      {results.length > 0 && (
        <>
          <div className="results-header">
            <p className="result-count">
              Showing {results.length} of {total} repositor{total === 1 ? "y" : "ies"} for <strong>{analyzedUsername}</strong>
            </p>
            <div className="filter-bar">
              {(["all", "basic", "intermediate", "advanced", "na"] as const).map((f) => (
                <button
                  key={f}
                  className={`filter-btn${filterComplexity === f ? " active" : ""}`}
                  onClick={() => setFilterComplexity(f)}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="grid">
            {filteredResults.map((r) => (
              <RepoCard key={r.repo_name} {...r} />
            ))}
          </div>

          {/* Sentinel — IntersectionObserver watches this to trigger next page load */}
          <div ref={sentinelRef} className="sentinel" />

          {loading && (
            <div className="status-text" style={{ textAlign: "center" }}>Loading more…</div>
          )}

          {!hasMore && !loading && (
            <div className="status-text" style={{ textAlign: "center" }}>All {total} repositories loaded.</div>
          )}
        </>
      )}
    </div>
  );
}
