import axios from "axios";

export interface RepoResult {
  repo_name: string;
  repo_url: string;
  level: "Basic" | "Intermediate" | "Advanced" | "NA";
  summary: string;
  has_readme: boolean;
}

const api = axios.create({
  baseURL: "http://localhost:8000",
});

export const repoService = {
  // Fetch total number of public repos for a GitHub user
  async getRepoCount(username: string): Promise<number> {
    const { data } = await api.get<number>(
      `/user-public-repo-count?username=${encodeURIComponent(username)}`
    );
    return data;
  },

  // Fetch and analyze a single page of repos
  async getAnalyzedRepos(username: string, page: number, perPage: number): Promise<RepoResult[]> {
    const { data } = await api.get<{ results: RepoResult[] }>(
      `/analyze?username=${encodeURIComponent(username)}&page=${page}&per_page=${perPage}`
    );
    return data.results;
  },
};
