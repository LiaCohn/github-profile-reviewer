import axios from "axios";

export interface RepoResult {
  repo_name: string;
  repo_url: string;
  level: "Basic" | "Intermediate" | "Advanced" | "NA";
  summary: string;
  has_readme: boolean;
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

function resolveErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    return err.response?.data?.detail ?? `Error ${err.response?.status}`;
  }
  return fallback;
}

export const repoService = {
  async getRepoCount(username: string): Promise<number> {
    try {
      const { data } = await api.get<number>("/user-public-repo-count", {
        params: { username },
      });
      return data;
    } catch (err) {
      throw new Error(resolveErrorMessage(err, "Failed to fetch repository count."));
    }
  },

  async getAnalyzedRepos(username: string, page: number, perPage: number): Promise<RepoResult[]> {
    try {
      const { data } = await api.get<RepoResult[]>("/analyze", {
        params: { username, page, per_page: perPage },
      });
      return data;
    } catch (err) {
      throw new Error(resolveErrorMessage(err, "Could not reach the server. Is the backend running?"));
    }
  },
};
