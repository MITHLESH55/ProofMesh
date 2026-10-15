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
  Team,
  EnterpriseService,
  EnterpriseGraphData,
  EnterpriseOverview,
  HistoricalEvidence,
  EvidenceSearchResult,
  AgentDefinition,
  AgentTask,
  AgentAction,
  AgentApproval,
  RemediationProposal,
  ChangeProofV3,
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

  // Phase 4 — CI/CD & Runtime Assurance Endpoints

  async getDeployments(params?: { repository_id?: string; change_id?: string; environment?: string; limit?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.repository_id) searchParams.append('repository_id', params.repository_id);
    if (params?.change_id) searchParams.append('change_id', params.change_id);
    if (params?.environment) searchParams.append('environment', params.environment);
    if (params?.limit) searchParams.append('limit', params.limit.toString());

    const qs = searchParams.toString();
    const res = await this.request<any[]>(`/deployments${qs ? `?${qs}` : ''}`);
    return res.data;
  }

  async getDeployment(id: string) {
    const res = await this.request<any>(`/deployments/${id}`);
    return res.data;
  }

  async createDeployment(data: {
    repository_id: string;
    change_id: string;
    analysis_run_id: string;
    commit_sha: string;
    environment?: string;
    status?: string;
  }) {
    const res = await this.request<any>('/deployments', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  async getDeploymentRuntime(id: string) {
    const res = await this.request<any>(`/deployments/${id}/runtime`);
    return res.data;
  }

  async getDeploymentAssurance(id: string) {
    const res = await this.request<any>(`/deployments/${id}/assurance`);
    return res.data;
  }

  async recordObservation(deploymentId: string, data: any) {
    const res = await this.request<any>(`/deployments/${deploymentId}/observations`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  async recordBaseline(deploymentId: string, data: any) {
    const res = await this.request<any>(`/deployments/${deploymentId}/baselines`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  async getRuntimeServices(deploymentId?: string) {
    const query = deploymentId ? `?deployment_id=${encodeURIComponent(deploymentId)}` : '';
    const res = await this.request<any[]>(`/runtime/services${query}`);
    return res.data;
  }

  async getRuntimeMetrics(deploymentId?: string) {
    const query = deploymentId ? `?deployment_id=${encodeURIComponent(deploymentId)}` : '';
    const res = await this.request<any>(`/runtime/metrics${query}`);
    return res.data;
  }

  async getRuntimeFindings(params?: { deployment_id?: string; severity?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.deployment_id) searchParams.append('deployment_id', params.deployment_id);
    if (params?.severity) searchParams.append('severity', params.severity);
    const qs = searchParams.toString();
    const res = await this.request<any[]>(`/runtime/findings${qs ? `?${qs}` : ''}`);
    return res.data;
  }

  async getChangeRuntimeProof(changeId: string, deploymentId?: string) {
    const query = deploymentId ? `?deployment_id=${encodeURIComponent(deploymentId)}` : '';
    const res = await this.request<any>(`/changes/${changeId}/runtime${query}`);
    return res.data;
  }

  async runCICheck(data: { change_id: string; commit_sha?: string; fail_on_warn?: boolean; publish_github_check?: boolean }) {
    const res = await this.request<any>('/ci/check', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  // ─── Phase 5 Enterprise APIs ───

  async getEnterpriseOverview(organizationId?: string): Promise<EnterpriseOverview> {
    const query = organizationId ? `?organization_id=${encodeURIComponent(organizationId)}` : '';
    const res = await this.request<EnterpriseOverview>(`/enterprise/overview${query}`);
    return res.data;
  }

  async getEnterpriseGraph(organizationId: string): Promise<EnterpriseGraphData> {
    const res = await this.request<EnterpriseGraphData>(`/enterprise/graph/${encodeURIComponent(organizationId)}`);
    return res.data;
  }

  async getCrossRepoImpact(organizationId: string, repositoryId: string): Promise<any> {
    const res = await this.request<any>(`/enterprise/graph/${encodeURIComponent(organizationId)}/impact/${encodeURIComponent(repositoryId)}`);
    return res.data;
  }

  async listTeams(organizationId?: string): Promise<Team[]> {
    const query = organizationId ? `?organization_id=${encodeURIComponent(organizationId)}` : '';
    const res = await this.request<Team[]>(`/enterprise/teams${query}`);
    return res.data;
  }

  async createTeam(data: { organization_id: string; name: string; slug: string; description?: string }): Promise<Team> {
    const res = await this.request<Team>('/enterprise/teams', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  async listServices(organizationId?: string, criticality?: string): Promise<EnterpriseService[]> {
    const params = new URLSearchParams();
    if (organizationId) params.append('organization_id', organizationId);
    if (criticality) params.append('criticality', criticality);
    const qs = params.toString();
    const res = await this.request<EnterpriseService[]>(`/enterprise/services${qs ? `?${qs}` : ''}`);
    return res.data;
  }

  async createService(data: { organization_id: string; name: string; criticality?: string; tier?: number; description?: string }): Promise<EnterpriseService> {
    const res = await this.request<EnterpriseService>('/enterprise/services', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  async recordDependency(data: any): Promise<any> {
    const res = await this.request<any>('/enterprise/dependencies', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  async recordIncident(data: any): Promise<any> {
    const res = await this.request<any>('/enterprise/incidents', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  // ─── Historical Evidence APIs ───

  async searchHistoricalEvidence(data: { query: string; organization_id?: string; repository_id?: string; limit?: number }): Promise<EvidenceSearchResult[]> {
    const res = await this.request<EvidenceSearchResult[]>('/enterprise/evidence/search', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  async storeHistoricalEvidence(data: { organization_id: string; title: string; content: string; evidence_type: string; repository_id?: string; provenance?: any }): Promise<HistoricalEvidence> {
    const res = await this.request<HistoricalEvidence>('/enterprise/evidence', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  // ─── Phase 5 Agent Governance APIs ───

  async listAgents(params?: { organization_id?: string; status?: string }): Promise<AgentDefinition[]> {
    const searchParams = new URLSearchParams();
    if (params?.organization_id) searchParams.append('organization_id', params.organization_id);
    if (params?.status) searchParams.append('status', params.status);
    const qs = searchParams.toString();
    const res = await this.request<AgentDefinition[]>(`/agents/${qs ? `?${qs}` : ''}`);
    return res.data;
  }

  async getAgent(agentId: string): Promise<AgentDefinition> {
    const res = await this.request<AgentDefinition>(`/agents/${encodeURIComponent(agentId)}`);
    return res.data;
  }

  async registerAgent(data: { organization_id: string; name: string; agent_type: string; provider?: string; model?: string; version?: string; autonomy_level?: number; capabilities?: string[]; allowed_scopes?: any }): Promise<AgentDefinition> {
    const res = await this.request<AgentDefinition>('/agents/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  async disableAgent(agentId: string): Promise<AgentDefinition> {
    const res = await this.request<AgentDefinition>(`/agents/${encodeURIComponent(agentId)}/disable`, {
      method: 'POST',
    });
    return res.data;
  }

  async checkCapability(agentId: string, capability: string, targetOrgId?: string, targetRepoId?: string): Promise<any> {
    const searchParams = new URLSearchParams();
    searchParams.append('capability', capability);
    if (targetOrgId) searchParams.append('target_organization_id', targetOrgId);
    if (targetRepoId) searchParams.append('target_repository_id', targetRepoId);
    const res = await this.request<any>(`/agents/${encodeURIComponent(agentId)}/check-capability?${searchParams.toString()}`, {
      method: 'POST',
    });
    return res.data;
  }

  // ─── Agent Task APIs ───

  async listAgentTasks(params?: { organization_id?: string; agent_id?: string; change_id?: string; status?: string }): Promise<AgentTask[]> {
    const searchParams = new URLSearchParams();
    if (params?.organization_id) searchParams.append('organization_id', params.organization_id);
    if (params?.agent_id) searchParams.append('agent_id', params.agent_id);
    if (params?.change_id) searchParams.append('change_id', params.change_id);
    if (params?.status) searchParams.append('status', params.status);
    const qs = searchParams.toString();
    const res = await this.request<AgentTask[]>(`/agents/tasks${qs ? `?${qs}` : ''}`);
    return res.data;
  }

  async createAgentTask(data: { organization_id: string; agent_id: string; change_id: string; analysis_run_id: string; task_type?: string; plan?: any }): Promise<AgentTask> {
    const res = await this.request<AgentTask>('/agents/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  async startAgentTask(taskId: string): Promise<AgentTask> {
    const res = await this.request<AgentTask>(`/agents/tasks/${encodeURIComponent(taskId)}/start`, {
      method: 'POST',
    });
    return res.data;
  }

  async getTaskBudget(taskId: string): Promise<any> {
    const res = await this.request<any>(`/agents/tasks/${encodeURIComponent(taskId)}/budget`);
    return res.data;
  }

  async getTaskAudit(taskId: string): Promise<any> {
    const res = await this.request<any>(`/agents/tasks/${encodeURIComponent(taskId)}/audit`);
    return res.data;
  }

  // ─── Agent Action Ledger APIs ───

  async listAgentActions(params?: { task_id?: string; agent_id?: string; organization_id?: string; limit?: number }): Promise<AgentAction[]> {
    const searchParams = new URLSearchParams();
    if (params?.task_id) searchParams.append('task_id', params.task_id);
    if (params?.agent_id) searchParams.append('agent_id', params.agent_id);
    if (params?.organization_id) searchParams.append('organization_id', params.organization_id);
    if (params?.limit) searchParams.append('limit', String(params.limit));
    const qs = searchParams.toString();
    const res = await this.request<AgentAction[]>(`/agents/actions${qs ? `?${qs}` : ''}`);
    return res.data;
  }

  async recordAgentAction(data: any): Promise<AgentAction> {
    const res = await this.request<AgentAction>('/agents/actions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  // ─── Approval Gate APIs ───

  async listPendingApprovals(organizationId?: string): Promise<AgentApproval[]> {
    const query = organizationId ? `?organization_id=${encodeURIComponent(organizationId)}` : '';
    const res = await this.request<AgentApproval[]>(`/agents/approvals/pending${query}`);
    return res.data;
  }

  async requestApproval(data: { organization_id: string; change_id: string; requesting_agent_id: string; requested_action: string; risk_level?: string; affected_resources?: string[]; evidence_summary?: any; task_id?: string }): Promise<AgentApproval> {
    const res = await this.request<AgentApproval>('/agents/approvals', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  async decideApproval(approvalId: string, data: { decision: 'APPROVED' | 'REJECTED'; reason?: string }): Promise<AgentApproval> {
    const res = await this.request<AgentApproval>(`/agents/approvals/${encodeURIComponent(approvalId)}/decide`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  async expireApproval(approvalId: string, reason?: string): Promise<AgentApproval> {
    const query = reason ? `?reason=${encodeURIComponent(reason)}` : '';
    const res = await this.request<AgentApproval>(`/agents/approvals/${encodeURIComponent(approvalId)}/expire${query}`, {
      method: 'POST',
    });
    return res.data;
  }

  // ─── Remediation Proposal APIs ───

  async listRemediations(params?: { organization_id?: string; change_id?: string }): Promise<RemediationProposal[]> {
    const searchParams = new URLSearchParams();
    if (params?.organization_id) searchParams.append('organization_id', params.organization_id);
    if (params?.change_id) searchParams.append('change_id', params.change_id);
    const qs = searchParams.toString();
    const res = await this.request<RemediationProposal[]>(`/agents/remediations${qs ? `?${qs}` : ''}`);
    return res.data;
  }

  async createRemediation(data: { organization_id: string; change_id: string; agent_id: string; title: string; description: string; original_risk_score: number; original_risk_level: string; proposed_diff: string; explanation: string; affected_components?: string[] }): Promise<RemediationProposal> {
    const res = await this.request<RemediationProposal>('/agents/remediations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  }

  // ─── Change Proof v3 APIs ───

  async assembleChangeProofV3(changeId: string, analysisRunId: string): Promise<ChangeProofV3> {
    const res = await this.request<ChangeProofV3>(`/agents/proof-v3/${encodeURIComponent(changeId)}/${encodeURIComponent(analysisRunId)}`, {
      method: 'POST',
    });
    return res.data;
  }

  async getChangeProofV3(changeId: string): Promise<ChangeProofV3> {
    const res = await this.request<ChangeProofV3>(`/agents/proof-v3/${encodeURIComponent(changeId)}`);
    return res.data;
  }
}

export const api = new ApiClient();

