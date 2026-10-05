import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Fingerprint,
} from 'lucide-react';
import { api } from '../services/api';
import { ChangeProofV3 } from '../types';

export const ChangeProofV3View: React.FC = () => {
  const { changeId: paramChangeId } = useParams<{ changeId?: string }>();
  const [changeId, setChangeId] = useState(paramChangeId || '');
  const [proof, setProof] = useState<ChangeProofV3 | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({});

  const loadProof = async (id: string) => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const data = await api.getChangeProofV3(id);
      setProof(data);
    } catch (err: any) {
      setError(err.message || 'Change Proof v3 not found. It may need to be assembled.');
      setProof(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (paramChangeId) {
      setChangeId(paramChangeId);
      loadProof(paramChangeId);
    }
  }, [paramChangeId]);

  const toggleSection = (sec: string) => {
    setCollapsedSections((prev) => ({ ...prev, [sec]: !prev[sec] }));
  };

  const verdictStyles: Record<string, { bg: string; text: string; border: string; icon: any }> = {
    VERIFIED_SAFE: { bg: 'bg-emerald-950/80', text: 'text-emerald-400', border: 'border-emerald-800', icon: CheckCircle2 },
    REMEDIATION_VERIFIED: { bg: 'bg-emerald-950/80', text: 'text-emerald-400', border: 'border-emerald-800', icon: CheckCircle2 },
    BLOCKED: { bg: 'bg-rose-950/80', text: 'text-rose-400', border: 'border-rose-800', icon: XCircle },
    RUNTIME_REGRESSION: { bg: 'bg-rose-950/80', text: 'text-rose-400', border: 'border-rose-800', icon: AlertTriangle },
    REMEDIATION_PENDING_APPROVAL: { bg: 'bg-amber-950/80', text: 'text-amber-400', border: 'border-amber-800', icon: Clock },
  };

  const currentVerdict = proof
    ? verdictStyles[proof.overall_verdict] || {
        bg: 'bg-slate-800',
        text: 'text-slate-300',
        border: 'border-slate-700',
        icon: ShieldCheck,
      }
    : null;

  const doc = proof?.proof_document || {};

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-wider mb-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            Phase 5 Canonical Assurance Document
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Change Proof v3</h1>
          <p className="text-sm text-slate-400 mt-1">
            Unified multi-phase formal proof synthesizing static analysis, runtime telemetry, historical knowledge, and agent governance.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={changeId}
            onChange={(e) => setChangeId(e.target.value)}
            placeholder="Enter Change UUID..."
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 font-mono focus:outline-none focus:border-sky-500 w-56"
          />
          <button
            onClick={() => loadProof(changeId)}
            disabled={loading || !changeId}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white rounded-lg transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Fetch Proof
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-200 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {proof && currentVerdict ? (
        <div className="space-y-6">
          {/* Verdict Banner Card */}
          <div className={`p-6 rounded-xl border ${currentVerdict.bg} ${currentVerdict.border} flex items-center justify-between`}>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-slate-950/50 rounded-xl">
                <currentVerdict.icon className={`w-8 h-8 ${currentVerdict.text}`} />
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400">
                  Canonical Policy Verdict
                </span>
                <h2 className={`text-2xl font-black tracking-tight ${currentVerdict.text} font-mono`}>
                  {proof.overall_verdict}
                </h2>
                <p className="text-xs font-mono text-slate-400 mt-1">
                  Change: {proof.change_id} • Analysis Run: {proof.analysis_run_id} • Spec: v{proof.version}
                </p>
              </div>
            </div>

            <div className="text-right">
              <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 block">
                Composite Risk
              </span>
              <div className="text-3xl font-black font-mono text-white">
                {proof.risk_score}
                <span className="text-sm font-normal text-slate-400 ml-1">/ 100</span>
              </div>
              <span className="text-xs font-mono font-bold text-amber-400">
                {proof.risk_level} RISK
              </span>
            </div>
          </div>

          {/* Traceability Breadcrumb Bar */}
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-between text-xs font-mono text-slate-400">
            <div className="flex items-center gap-2">
              <span className="text-slate-500 font-bold">TRACEABILITY:</span>
              <span className="text-cyan-400">Decision ({proof.overall_verdict})</span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
              <span className="text-slate-300">Evidence</span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
              <span className="text-slate-300">Findings</span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
              <span className="text-slate-300">Microservices</span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
              <Link to="/enterprise/graph" className="text-sky-400 hover:underline flex items-center gap-1">
                Enterprise Graph <ExternalLink className="w-3 h-3" />
              </Link>
            </div>
            <span>Generated: {new Date(proof.created_at).toLocaleString()}</span>
          </div>

          {/* 18-Section Canonical Proof Breakdown */}
          <div className="space-y-4">
            {/* Section 1: Change Info */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec1')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  1. Change &amp; Repository Scope
                </span>
                {collapsedSections['sec1'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec1'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono space-y-2">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-slate-500">Change ID: </span>
                      <span className="text-slate-200">{proof.change_id}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Analysis Run ID: </span>
                      <span className="text-slate-200">{proof.analysis_run_id}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Section 2: Intent */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec2')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  2. Change Intent &amp; Capabilities
                </span>
                {collapsedSections['sec2'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec2'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.change_intent || 'No intent declared', null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 3: Structural Impact */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec3')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  3. Structural Impact &amp; Blast Radius (Neo4j)
                </span>
                {collapsedSections['sec3'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec3'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono space-y-2">
                  <p className="text-slate-400">
                    Direct and transitive downstream graph dependents evaluated across repositories.
                  </p>
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.structural_impact || doc.impact_analysis || {}, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 4: Behavioral Assurance */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec4')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  4. Behavioral Invariants
                </span>
                {collapsedSections['sec4'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec4'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.behavioral_invariants || [], null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 5: Security */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec5')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  5. Security &amp; Secret Redaction
                </span>
                {collapsedSections['sec5'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec5'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.security_findings || [], null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 6: Semantic Contracts */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec6')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  6. Semantic API Contracts
                </span>
                {collapsedSections['sec6'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec6'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.semantic_contracts || [], null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 7: Tests */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec7')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  7. Test Recommendations &amp; Gaps
                </span>
                {collapsedSections['sec7'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec7'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.test_recommendations || [], null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 8: Risk Composite */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec8')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  8. Composite Risk Decomposition (0–100)
                </span>
                {collapsedSections['sec8'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec8'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.risk_assessment || {}, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 9: Deployment */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec9')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  9. Deployment Environment Context
                </span>
                {collapsedSections['sec9'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec9'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.deployment || {}, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 10: Runtime Telemetry */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec10')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  10. Runtime Telemetry &amp; Regression Findings
                </span>
                {collapsedSections['sec10'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec10'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.runtime_telemetry || doc.runtime_findings || [], null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 11: Historical Evidence */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec11')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  11. Historical Evidence &amp; Prior Incidents
                </span>
                {collapsedSections['sec11'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec11'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono space-y-2">
                  <span className="text-cyan-400 block font-bold">Search Metric: TF-IDF Cosine Similarity</span>
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.historical_evidence || [], null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 12: Agent Actions */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec12')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  12. Agent Governance &amp; Execution Audit
                </span>
                {collapsedSections['sec12'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec12'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.agent_actions || [], null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 13: Remediation */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec13')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  13. Remediation Proposals &amp; Verification
                </span>
                {collapsedSections['sec13'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec13'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.remediation_proposals || [], null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 14: Verification */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec14')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  14. Formal Verification Status
                </span>
                {collapsedSections['sec14'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec14'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.verification_status || 'VERIFIED', null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 15: Policy Rules */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec15')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  15. Policy Evaluation Rules
                </span>
                {collapsedSections['sec15'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec15'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.policy_decision || {}, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 16: Human Approvals */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec16')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  16. Human Approval Gate
                </span>
                {collapsedSections['sec16'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec16'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.approvals || [], null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 17: Uncertainty Factors */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec17')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
                  17. Uncertainty Factors
                </span>
                {collapsedSections['sec17'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec17'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.uncertainty_factors || [], null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Section 18: Provenance */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSection('sec18')}
                className="w-full px-5 py-3.5 bg-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors"
              >
                <span className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200 flex items-center gap-2">
                  <Fingerprint className="w-4 h-4 text-cyan-400" />
                  18. Provenance &amp; Cryptographic Signatures
                </span>
                {collapsedSections['sec18'] ? <ChevronRight className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
              {!collapsedSections['sec18'] && (
                <div className="p-5 border-t border-slate-800 text-xs font-mono">
                  <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto">
                    {JSON.stringify(doc.provenance || { version: '3.0.0', assembler: 'ProofMesh ChangeProofV3Assembler' }, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="p-16 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
          <ShieldAlert className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-medium text-slate-300">No Change Proof v3 Loaded</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
            Provide a valid Change ID in the input box above or navigate here from an active change to view its unified Change Proof v3 assurance record.
          </p>
        </div>
      )}
    </div>
  );
};
