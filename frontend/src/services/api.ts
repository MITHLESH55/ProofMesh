import {
  ApiSuccessResponse,
  Change,
  ChangeDetail,
  GraphData,
  GraphStats,
  HealthStatus,
  ImpactAnalysisResult,
  IngestFilesResult,
  ReadyStatus,
  Repository,
  User,
} from '../types';

const API_BASE = '/api/v1';

export class ApiError extends Error {
  code: string;
  requestId: string;
  status: number;
  details?: any;

  constructor(message: string, code: string, requestId: string, status: number, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.requestId = requestId;
    this.status = status;
    this.details = details;
  }
}

class ApiClient {
  private getToken(): string | null {
    return localStorage.getItem('proofmesh_token');
  }

  public setToken(token: string): void {
    localStorage.setItem('proofmesh_token', token);
  }

  public clearToken(): void {
    localStorage.removeItem('proofmesh_token');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiSuccessResponse<T>> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorDetail = data?.error;
      const code = errorDetail?.code || 'API_ERROR';
      const message = errorDetail?.message || response.statusText || 'An unexpected error occurred';
      const requestId = errorDetail?.request_id || response.headers.get('X-Request-ID') || 'unknown';
      throw new ApiError(message, code, requestId, response.status, errorDetail?.details);
    }

    return data as ApiSuccessResponse<T>;
  }

  // Auth Endpoints
  async login(email: string, password: string) {
    const res = await this.request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(res.data.access_token);
    return res.data;
  }

  async register(email: string, password: string, full_name: string, organization_name?: string) {
    const res = await this.request<{ access_token: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name, organization_name }),
    });
    this.setToken(res.data.access_token);
    return res.data;
  }

  async getMe() {
    const res = await this.request<User>('/auth/me');
    return res.data;
  }

  logout() {
    this.clearToken();
  }

  // Repositories Endpoints
  async getRepositories(organizationId?: string) {
    const query = organizationId ? `?organization_id=${encodeURIComponent(organizationId)}` : '';
    const res = await this.request<Repository[]>(`/repositories${query}`);
    return res.data;
  }

  async getRepository(id: string) {
    const res = await this.request<Repository>(`/repositories/${id}`);
    return res.data;
  }

  async createRepository(data: { github_repository_id: string; owner: string; name: string; default_branch?: string }) {
    const res = await this.request<Repository>('/repositories', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  // Changes Endpoints
  async getChanges(params?: { repository_id?: string; status?: string; limit?: number; offset?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.repository_id) searchParams.append('repository_id', params.repository_id);
    if (params?.status && params.status !== 'ALL') searchParams.append('status', params.status);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());

    const qs = searchParams.toString();
    const res = await this.request<Change[]>(`/changes${qs ? `?${qs}` : ''}`);
    return res.data;
  }

  async getChangeById(id: string) {
    const res = await this.request<ChangeDetail>(`/changes/${id}`);
    return res.data;
  }

  async getChangeStatus(id: string) {
    const res = await this.request<{ change_id: string; status: string; updated_at: string }>(`/changes/${id}/status`);
    return res.data;
  }

  async reanalyzeChange(id: string, reason?: string) {
    const res = await this.request<ChangeDetail>(`/changes/${id}/reanalyze`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
    return res.data;
  }

  // Health
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    return (await res.json()) as HealthStatus;
  }

  async getReady() {
    const res = await fetch(`${API_BASE}/ready`);
    return (await res.json()) as ReadyStatus;
  }

  // Phase 2 — Graph & Impact Analysis

  async getRepositoryGraph(repositoryId: string, limit = 200) {
    const res = await this.request<GraphData>(
      `/graph/repository/${repositoryId}?limit=${limit}`
    );
    return res.data;
  }

  async getFileGraph(repositoryId: string, filePath: string, depth = 2) {
    const encoded = encodeURIComponent(filePath);
    const res = await this.request<GraphData>(
      `/graph/file/${repositoryId}?file_path=${encoded}&depth=${depth}`
    );
    return res.data;
  }

  async getGraphStats(repositoryId: string) {
    const res = await this.request<GraphStats>(`/graph/stats/${repositoryId}`);
    return res.data;
  }

  async runImpactAnalysis(
    repositoryId: string,
    changedFiles: string[],
    maxDepth = 4
  ) {
    const res = await this.request<ImpactAnalysisResult>(
      `/graph/impact/${repositoryId}`,
      {
        method: 'POST',
        body: JSON.stringify({ changed_files: changedFiles, max_depth: maxDepth }),
      }
    );
    return res.data;
  }

  async ingestFiles(
    repositoryId: string,
    commitSha: string,
    files: Array<{ path: string; content: string }>
  ) {
    const res = await this.request<IngestFilesResult>('/graph/ingest', {
      method: 'POST',
      body: JSON.stringify({
        repository_id: repositoryId,
        commit_sha: commitSha,
        files,
      }),
    });
    return res.data;
  }

  async getGraphHealth() {
    const res = await this.request<{ status: string; uri: string }>('/graph/health');
    return res.data;
  }

  // Phase 3 — AI Assurance & Change Proof

  async getAssuranceOverview(analysisRunId: string) {
    const res = await this.request<any>(`/assurance/${analysisRunId}`);
    return res.data;
  }

  async runAssuranceAnalysis(changeId: string) {
    const res = await this.request<any>(`/assurance/analyze/${changeId}`, {
      method: 'POST',
    });
    return res.data;
  }

  async getChangeProof(analysisRunId: string) {
    const res = await this.request<any>(`/assurance/${analysisRunId}/proof`);
    return res.data;
  }

  async reevaluateDecision(analysisRunId: string, policyOverrides?: Record<string, any>) {
    const res = await this.request<any>(`/assurance/${analysisRunId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ policy_overrides: policyOverrides || {} }),
    });
    return res.data;
  }
}

export const api = new ApiClient();
