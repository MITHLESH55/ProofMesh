import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  RefreshCw,
  Bot,
  Info,
  Calendar,
} from 'lucide-react';
import { api } from '../services/api';
import { AgentApproval } from '../types';

export const ApprovalCenter: React.FC = () => {
  const [approvals, setApprovals] = useState<AgentApproval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedApproval, setSelectedApproval] = useState<AgentApproval | null>(null);
  const [decisionType, setDecisionType] = useState<'APPROVED' | 'REJECTED'>('APPROVED');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadApprovals = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listPendingApprovals();
      setApprovals(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load approvals');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApprovals();
  }, []);

  const handleDecide = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApproval) return;
    try {
      setSubmitting(true);
      await api.decideApproval(selectedApproval.id, {
        decision: decisionType,
        reason: reason.trim() || undefined,
      });
      setSelectedApproval(null);
      setReason('');
      loadApprovals();
    } catch (err: any) {
      alert(`Decision failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleExpire = async (approvalId: string) => {
    if (!confirm('Expire this approval request immediately?')) return;
    try {
      await api.expireApproval(approvalId, 'Manually expired by security auditor');
      loadApprovals();
    } catch (err: any) {
      alert(`Failed to expire approval: ${err.message}`);
    }
  };

  const riskColors: Record<string, string> = {
    CRITICAL: 'bg-rose-950/80 text-rose-400 border-rose-800/80',
    HIGH: 'bg-amber-950/80 text-amber-400 border-amber-800/80',
    MEDIUM: 'bg-sky-950/80 text-sky-400 border-sky-800/80',
    LOW: 'bg-slate-800 text-slate-400 border-slate-700',
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-amber-400 uppercase tracking-wider mb-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            Phase 5 Human-in-the-Loop Governance
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Approval Center</h1>
          <p className="text-sm text-slate-400 mt-1">
            Authorize or reject high-risk autonomous agent mutations, remediations, and deployment overrides.
          </p>
        </div>
        <button
          onClick={loadApprovals}
          disabled={loading}
          className="flex items-center gap-2 px-3.5 py-2 text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded-lg transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Governance Policy Notice */}
      <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl flex items-start gap-3">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-400 space-y-1">
          <p className="font-semibold text-slate-200">
            Strict Multi-Tenant &amp; Self-Approval Safeguards Enforced:
          </p>
          <p>
            Autonomous agents cannot approve their own requests under any circumstances. All decisions are
            signed, immutably recorded in the ledger, and time-bounded. Expired requests automatically fail safe.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-200 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Approvals List */}
      {approvals.length === 0 ? (
        <div className="p-16 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
          <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-base font-medium text-slate-300">All Clear — No Pending Approvals</h3>
          <p className="text-xs text-slate-500 mt-1">
            There are currently no high-risk agent operations waiting for human authorization.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {approvals.map((req) => (
            <div
              key={req.id}
              className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-4 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${
                        riskColors[req.risk_level] || riskColors.HIGH
                      }`}
                    >
                      {req.risk_level} RISK
                    </span>
                    <h3 className="text-base font-bold text-white">{req.requested_action}</h3>
                  </div>
                  <div className="flex items-center gap-3 text-xs font-mono text-slate-400 mt-1">
                    <span className="flex items-center gap-1">
                      <Bot className="w-3.5 h-3.5 text-cyan-400" />
                      Agent: {req.requesting_agent_id.slice(0, 8)}…
                    </span>
                    <span>•</span>
                    <span>Change ID: {req.change_id.slice(0, 8)}…</span>
                    <span>•</span>
                    <span className="flex items-center gap-1 text-slate-500">
                      <Calendar className="w-3.5 h-3.5" />
                      {new Date(req.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      setSelectedApproval(req);
                      setDecisionType('APPROVED');
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg shadow-sm transition-colors"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Approve
                  </button>
                  <button
                    onClick={() => {
                      setSelectedApproval(req);
                      setDecisionType('REJECTED');
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white rounded-lg shadow-sm transition-colors"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    Reject
                  </button>
                  <button
                    onClick={() => handleExpire(req.id)}
                    title="Expire Request"
                    className="p-1.5 text-slate-400 hover:text-amber-400 hover:bg-slate-800 rounded transition-colors text-xs"
                  >
                    <Clock className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Affected Resources & Evidence */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-slate-800 text-xs font-mono">
                <div>
                  <span className="text-slate-400 font-semibold block mb-1">
                    Affected Resources:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {(req.affected_resources || []).length > 0 ? (
                      req.affected_resources.map((res, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-slate-950 text-indigo-400 border border-slate-800 rounded text-[11px]"
                        >
                          {res}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-500">None specified</span>
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-slate-400 font-semibold block mb-1">
                    Evidence Summary:
                  </span>
                  <pre className="p-2.5 bg-slate-950 border border-slate-800 rounded text-[11px] text-slate-300 max-h-24 overflow-y-auto">
                    {JSON.stringify(req.evidence_summary || {}, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Decision Modal */}
      {selectedApproval && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              {decisionType === 'APPROVED' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              ) : (
                <XCircle className="w-5 h-5 text-rose-400" />
              )}
              {decisionType === 'APPROVED' ? 'Confirm Approval' : 'Confirm Rejection'}
            </h3>

            <p className="text-xs text-slate-400">
              You are about to{' '}
              <strong className={decisionType === 'APPROVED' ? 'text-emerald-400' : 'text-rose-400'}>
                {decisionType.toLowerCase()}
              </strong>{' '}
              action: &quot;{selectedApproval.requested_action}&quot;.
            </p>

            <form onSubmit={handleDecide} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Reason / Audit Justification
                </label>
                <textarea
                  required={decisionType === 'REJECTED'}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder={
                    decisionType === 'APPROVED'
                      ? 'Optional justification for human audit record'
                      : 'Required explanation for rejection'
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500 h-24"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedApproval(null)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className={`px-4 py-2 text-xs font-semibold text-white rounded-lg shadow-sm transition-colors ${
                    decisionType === 'APPROVED'
                      ? 'bg-emerald-600 hover:bg-emerald-500'
                      : 'bg-rose-600 hover:bg-rose-500'
                  }`}
                >
                  {submitting ? 'Submitting...' : `Submit ${decisionType}`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
