export type UserRole = 'ADMIN' | 'ENGINEER' | 'VIEWER';

export type ChangeStatus = 'INGESTED' | 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export type AnalysisStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  memberships?: Array<{
    organization_id: string;
    organization_name: string;
    organization_slug: string;
    role: string;
  }>;
}

export interface Repository {
  id: string;
  organization_id: string;
  github_repository_id: string;
  owner: string;
  name: string;
  full_name: string;
  default_branch: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PullRequest {
  id: string;
  repository_id: string;
  github_pr_id: string;
  number: number;
  title: string;
  description?: string | null;
  author: string;
  head_sha: string;
  base_sha: string;
  state: 'OPEN' | 'CLOSED' | 'MERGED';
  opened_at?: string | null;
  updated_at?: string | null;
  closed_at?: string | null;
  created_at: string;
}

export interface AnalysisRun {
  id: string;
  change_id: string;
  status: AnalysisStatus;
  stage: string;
  worker_id?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  created_at: string;
}

export interface AuditLog {
  id: string;
  organization_id?: string | null;
  actor_user_id?: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  event_metadata?: Record<string, any> | null;
  created_at: string;
}

export interface Change {
  id: string;
  pull_request_id: string;
  commit_sha: string;
  status: ChangeStatus;
  source: string;
  created_at: string;
  updated_at: string;
  pull_request?: PullRequest;
  repository?: Repository;
  latest_analysis_run?: AnalysisRun | null;
}

export interface ChangeDetail extends Change {
  pull_request: PullRequest;
  repository: Repository;
  analysis_runs: AnalysisRun[];
  audit_history: AuditLog[];
}

export interface ApiSuccessResponse<T> {
  data: T;
  request_id: string;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    request_id: string;
    details?: any;
  };
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
}

export interface ReadyStatus {
  status: string;
  dependencies: {
    postgres: string;
    redis: string;
  };
}

// Phase 2 — Graph & Impact Analysis Types

export interface GraphNode {
  id: string;
  label: string;
  type: 'file' | 'function' | 'class';
  path?: string;
  file_path?: string;
  language?: string;
  start_line?: number;
  symbol_count?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: 'IMPORTS' | 'DEFINES' | 'HAS_METHOD' | 'CALLS';
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_files?: number;
}

export interface GraphStats {
  repository_id: string;
  total_files: number;
  total_functions: number;
  total_classes: number;
  total_import_edges: number;
}

export interface ImpactedFile {
  path: string;
  language: string;
  impact_level: 'direct' | 'first' | 'second' | 'transitive';
  impact_chain: string[];
  affected_symbols: string[];
  risk_score: number;
}

export interface RiskSummary {
  overall_risk: 'low' | 'medium' | 'high' | 'critical';
  risk_score: number;
  high_risk_files: number;
  medium_risk_files: number;
  low_risk_files: number;
  blast_radius: number;
}

export interface ImpactAnalysisResult {
  repository_id: string;
  changed_files: string[];
  directly_impacted: ImpactedFile[];
  transitively_impacted: ImpactedFile[];
  total_files_affected: number;
  risk_summary: RiskSummary;
}

export interface IngestFilesResult {
  repository_id: string;
  commit_sha: string;
  files_processed: number;
  total_classes: number;
  total_functions: number;
  total_methods: number;
  total_imports: number;
  total_relationships: number;
  errors: string[];
}

// Phase 3 — AI Assurance & Change Proof Types

export interface ChangeIntent {
  id: string;
  change_id: string;
  analysis_run_id: string;
  objective: string;
  category: string;
  affected_capability: string;
  expected_behavior?: string;
  affected_components: string[];
  confidence: number;
  model_info?: Record<string, any>;
  created_at: string;
}

export interface BehavioralInvariant {
  id: string;
  change_id: string;
  analysis_run_id: string;
  invariant_type: 'DETERMINISTIC' | 'AI_PROPOSED' | 'HISTORICALLY_OBSERVED';
  description: string;
  affected_component: string;
  source: string;
  evidence_refs: string[];
  confidence: number;
  verification_status: 'VERIFIED' | 'VIOLATED' | 'UNVERIFIED';
  created_at: string;
}

export interface SemanticContract {
  id: string;
  change_id: string;
  analysis_run_id: string;
  endpoint_path: string;
  http_method: string;
  contract_type: string;
  classification: 'NO_CHANGE' | 'COMPATIBLE_CHANGE' | 'POTENTIALLY_BREAKING' | 'BREAKING' | 'UNKNOWN';
  evidence_refs: string[];
  details?: Record<string, any>;
  created_at: string;
}

export interface SecurityFinding {
  id: string;
  change_id: string;
  analysis_run_id: string;
  category: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  affected_component: string;
  evidence_refs: string[];
  reasoning: string;
  remediation_suggestion?: string;
  confidence: number;
  created_at: string;
}

export interface TestRecommendation {
  id: string;
  change_id: string;
  analysis_run_id: string;
  target_component: string;
  test_title: string;
  test_code_scaffold?: string;
  reason: string;
  invariant_covered?: string;
  expected_behavior?: string;
  confidence: number;
  created_at: string;
}

export interface ContributingFactor {
  name: string;
  weight: number;
  description: string;
  evidence_ref?: string;
}

export interface RiskAssessment {
  id: string;
  change_id: string;
  analysis_run_id: string;
  overall_risk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  numerical_score: number;
  contributing_factors: ContributingFactor[];
  confidence: number;
  uncertainties: string[];
  created_at: string;
}

export interface EvidenceRecord {
  id: string;
  analysis_run_id: string;
  source_type: string;
  source_reference: string;
  confidence: number;
  explanation: string;
  created_at: string;
}

export interface PolicyDecision {
  id: string;
  change_id: string;
  analysis_run_id: string;
  decision: 'PASS' | 'WARN' | 'BLOCK' | 'INSUFFICIENT_EVIDENCE';
  rules_evaluated: Record<string, any>[];
  blocking_reasons: string[];
  warning_reasons: string[];
  created_at: string;
}

export interface ChangeProof {
  id: string;
  change_id: string;
  analysis_run_id: string;
  decision: 'PASS' | 'WARN' | 'BLOCK' | 'INSUFFICIENT_EVIDENCE';
  risk_level: string;
  summary: Record<string, any>;
  full_proof_artifact: Record<string, any>;
  created_at: string;
}

export interface AssuranceOverview {
  analysis_run_id: string;
  change_id: string;
  status: string;
  intent?: ChangeIntent;
  invariants: BehavioralInvariant[];
  contracts: SemanticContract[];
  security_findings: SecurityFinding[];
  test_recommendations: TestRecommendation[];
  risk?: RiskAssessment;
  evidence: EvidenceRecord[];
  policy_decision?: PolicyDecision;
  proof?: ChangeProof;
}

