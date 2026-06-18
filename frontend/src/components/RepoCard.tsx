import "./RepoCard.css";
import { RepoResult } from "../services/api";

type RepoCardProps = RepoResult;

const LEVEL_COLORS: Record<string, string> = {
  Basic: "#22c55e",
  Intermediate: "#f97316",
  Advanced: "#ef4444",
  NA: "#9e9d9b",
};

export default function RepoCard({ repo_name, repo_url, level, summary, has_readme }: RepoCardProps) {
  return (
    <div className="card">
      <div className="card-header">
        <a href={repo_url} target="_blank" rel="noopener noreferrer" className="repo-name">
          {repo_name}
        </a>
        <span
          className="badge"
          style={{ backgroundColor: LEVEL_COLORS[level] ?? "#6b7280" }}
        >
          {level}
        </span>
      </div>
      <p className="summary">{summary}</p>
      {!has_readme && (
        <p className="no-readme">No README</p>
      )}
    </div>
  );
}
