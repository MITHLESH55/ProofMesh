import React, { useEffect, useState } from 'react';
import {
  Wrench,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Plus,
  FileCode,
  ArrowRight,
} from 'lucide-react';
import { api } from '../services/api';
import { RemediationProposal } from '../types';

export const RemediationCenter: React.FC = () => {
  const [proposals, setProposals] = useState<RemediationProposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedProposal, setSelectedProposal] = useState<RemediationProposal | null>(null);

  // Form states
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [changeId, setChangeId] = useState('');
  const [agentId] = useState('');
  const [origRiskScore, setOrigRiskScore] = useState(85);
  const [origRiskLevel] = useState('HIGH');
  const [proposedDiff, setProposedDiff] = useState('--- a/service.py\n+++ b/service.py\n@@ -10,3 +10,3 @@\n-    timeout = None\n+    timeout = 30.0');
  const [explanation, setExplanation] = useState('Added explicit timeout parameter to prevent socket exhaustion.');

  const loadProposals = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listRemediations();
      setProposals(data);
      if (data.length > 0 && !selectedProposal) {
        setSelectedProposal(data[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load remediation proposals');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProposals();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !changeId.trim()) return;
    try {
      const defaultOrgId = '00000000-0000-0000-0000-000000000001';
      const defaultAgentId = agentId.trim() || '00000000-0000-0000-0000-000000000002';
      const created = await api.createRemediation({
        organization_id: defaultOrgId,
        change_id: changeId.trim(),
        agent_id: defaultAgentId,
        title,
        description,
        original_risk_score: Number(origRiskScore),
        original_risk_level: origRiskLevel,
        proposed_diff: proposedDiff,
        explanation,
        affected_components: ['service.py'],
      });
      setShowCreateModal(false);
      setTitle('');
      setDescription('');
      loadProposals();
      setSelectedProposal(created);
    } catch (err: any) {
      alert(`Failed to create remediation: ${err.message}`);
    }
  };

  const statusBadges: Record<string, { label: string; color: string }> = {
    VERIFIED_SAFER: { label: 'Verified Safer', color: 'bg-emerald-950 text-emerald-300 border-emerald-800' },
    PENDING: { label: 'Pending Verification', color: 'bg-amber-950 text-amber-300 border-amber-800' },
    REJECTED_REGRESSION: { label: 'Rejected Regression', color: 'bg-rose-950 text-rose-300 border-rose-800' },
    FAILED_VERIFICATION: { label: 'Failed Verification', color: 'bg-slate-800 text-slate-300 border-slate-700' },
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-wider mb-1">
            <Wrench className="w-3.5 h-3.5" />
            Phase 5 Autonomous Remediation
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Remediation Center</h1>
          <p className="text-sm text-slate-400 mt-1">
            Governed automated patch proposals with verified before/after risk quantification and rollback recipes.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadProposals}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white rounded-lg shadow-sm shadow-sky-600/30 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Propose Remediation
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-200 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Proposal List + Selected Proposal Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: List of proposals */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 px-1">
            Remediation Proposals ({proposals.length})
          </h3>
          {proposals.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-500">
              No remediation proposals found.
            </div>
          ) : (
            <div className="space-y-2 max-h-[620px] overflow-y-auto pr-1">
              {proposals.map((p) => {
                const badge = statusBadges[p.verification_status] || statusBadges.PENDING;
                const isSelected = selectedProposal?.id === p.id;

                return (
                  <button
                    key={p.id}
                    onClick={() => setSelectedProposal(p)}
                    className={`w-full text-left p-3.5 rounded-lg border transition-all ${
                      isSelected
                        ? 'bg-sky-950/40 border-sky-500/60 text-white'
                        : 'bg-slate-950/60 border-slate-800/80 text-slate-300 hover:bg-slate-800/50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold truncate max-w-[150px]">
                        {p.title}
                      </span>
                      <span
                        className={`text-[9px] font-mono px-1.5 py-0.2 rounded border ${badge.color}`}
                      >
                        {badge.label}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mt-2">
                      <span className="text-rose-400">Before: {p.original_risk_score}</span>
                      <ArrowRight className="w-3 h-3 text-slate-500" />
                      <span className="text-emerald-400">After: {p.verified_risk_score}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right column: Selected Proposal Breakdown */}
        <div className="lg:col-span-2 space-y-6">
          {selectedProposal ? (
            <>
              {/* Header Box */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-white">{selectedProposal.title}</h2>
                    <p className="text-xs font-mono text-slate-400 mt-0.5">
                      Change ID: {selectedProposal.change_id} • Agent: {selectedProposal.agent_id}
                    </p>
                  </div>
                  <span
                    className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${
                      statusBadges[selectedProposal.verification_status]?.color ||
                      'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {selectedProposal.verification_status}
                  </span>
                </div>

                <p className="text-xs text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-800">
                  {selectedProposal.explanation || selectedProposal.description}
                </p>

                {/* Risk Comparison Bar */}
                <div className="grid grid-cols-2 gap-4 pt-3 border-t border-slate-800">
                  <div className="p-4 bg-rose-950/20 border border-rose-800/40 rounded-xl">
                    <div className="flex items-center justify-between text-xs text-rose-300 mb-1">
                      <span>Original Risk Baseline</span>
                      <ShieldAlert className="w-4 h-4 text-rose-400" />
                    </div>
                    <div className="text-2xl font-bold font-mono text-rose-400">
                      {selectedProposal.original_risk_score}
                      <span className="text-xs font-normal text-rose-300 ml-2">
                        ({selectedProposal.original_risk_level})
                      </span>
                    </div>
                  </div>

                  <div className="p-4 bg-emerald-950/20 border border-emerald-800/40 rounded-xl">
                    <div className="flex items-center justify-between text-xs text-emerald-300 mb-1">
                      <span>Verified Post-Patch Risk</span>
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    </div>
                    <div className="text-2xl font-bold font-mono text-emerald-400">
                      {selectedProposal.verified_risk_score}
                      <span className="text-xs font-normal text-emerald-300 ml-2">
                        ({selectedProposal.verified_risk_level})
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Proposed Code Patch Diff */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileCode className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                      Proposed Code Patch Diff
                    </h3>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400">
                    Affected: {(selectedProposal.affected_components || []).join(', ') || 'N/A'}
                  </span>
                </div>

                <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs overflow-x-auto max-h-72">
                  {selectedProposal.proposed_diff.split('\n').map((line, idx) => {
                    const isAdd = line.startsWith('+') && !line.startsWith('+++');
                    const isDel = line.startsWith('-') && !line.startsWith('---');
                    const isHeader = line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++');

                    return (
                      <div
                        key={idx}
                        className={`${
                          isAdd
                            ? 'text-emerald-400 bg-emerald-950/40 px-1'
                            : isDel
                            ? 'text-rose-400 bg-rose-950/40 px-1'
                            : isHeader
                            ? 'text-cyan-400 font-bold'
                            : 'text-slate-400'
                        }`}
                      >
                        {line || ' '}
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          ) : (
            <div className="p-16 text-center text-slate-500 text-sm bg-slate-900/40 border border-slate-800 rounded-xl">
              Select a remediation proposal to inspect before/after verified risk metrics and code patches.
            </div>
          )}
        </div>
      </div>

      {/* Create Proposal Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-bold text-white">Propose Autonomous Remediation</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Add Request Timeout Parameter"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Target Change ID</label>
                  <input
                    type="text"
                    required
                    value={changeId}
                    onChange={(e) => setChangeId(e.target.value)}
                    placeholder="UUID of target change"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Original Risk Score</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={origRiskScore}
                    onChange={(e) => setOrigRiskScore(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Explanation &amp; Rationale</label>
                <textarea
                  value={explanation}
                  onChange={(e) => setExplanation(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500 h-16"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Unified Code Patch (Diff)</label>
                <textarea
                  value={proposedDiff}
                  onChange={(e) => setProposedDiff(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-100 focus:outline-none focus:border-sky-500 h-28"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white rounded-lg shadow-sm"
                >
                  Submit &amp; Verify Risk
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
