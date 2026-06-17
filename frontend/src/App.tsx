import { useState } from "react";
import RepoCard from "./components/RepoCard";
import "./App.css";

interface RepoResult {
  repo_name: string;
  repo_url: string;
  level: "Basic" | "Intermediate" | "Advanced" | "NA";
  summary: string;
  has_readme: boolean;
}

export default function App() {
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<RepoResult[] | null>(null);
  const [analyzedUsername, setAnalyzedUsername] = useState(""); //username that was analyzed
  const [filterComplexity, setFilterComplexity] = useState<"all" | "basic" | "intermediate" | "advanced" | "na">("all");

  const filteredResults = results?.filter((r) =>
    filterComplexity === "all" || r.level.toLowerCase() === filterComplexity
  ) ?? [];


  async function handleAnalyze() {
    const trimmed = username.trim();
    if (!trimmed) return;

    setAnalyzedUsername(trimmed);
    setFilterComplexity("all");
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const resp = await fetch(`/analyze?username=${encodeURIComponent(trimmed)}`, { //encode the username to handle special characters
        method: "POST",
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        setError(data.detail ?? `Error ${resp.status}`);
        return;
      }

      const data: RepoResult[] = await resp.json();
      setResults(data);
    } catch {
      setError("Could not reach the server. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleAnalyze();
  }

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
          disabled={loading}
        />
        <button className="button" onClick={handleAnalyze} disabled={loading || !username.trim()}>
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </div>

      {loading && (
        <div className="status-text">Fetching repos and analyzing READMEs…</div>
      )}

      {error && (
        <div className="error-box">{error}</div>
      )}

      {results !== null && results.length === 0 && (
        <div className="status-text">No public repositories found for <strong>{analyzedUsername}</strong>.</div>
      )}

      {results && results.length > 0 && (
        <>
          <div className="results-header">
            <p className="result-count">
              {filteredResults.length} of {results.length} repositor{results.length === 1 ? "y" : "ies"} for <strong>{analyzedUsername}</strong>
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
        </>
      )}
    </div>
  );
}
