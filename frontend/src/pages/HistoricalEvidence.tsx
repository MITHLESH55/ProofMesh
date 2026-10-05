import React, { useEffect, useState } from 'react';
import {
  Search,
  BookOpen,
  AlertTriangle,
  History,
  Calendar,
  Info,
  Plus,
  RefreshCw,
} from 'lucide-react';
import { api } from '../services/api';
import { EvidenceSearchResult } from '../types';

export const HistoricalEvidence: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<EvidenceSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  // New Evidence Form
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [evidenceType, setEvidenceType] = useState('PROOF_SUMMARY');

  const defaultOrgId = '00000000-0000-0000-0000-000000000001';

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const res = await api.searchHistoricalEvidence({
        query: query.trim() || 'incident regression authentication memory leak',
        organization_id: defaultOrgId,
        limit: 10,
      });
      setResults(res);
    } catch (err: any) {
      setError(err.message || 'Evidence search failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  const handleCreateEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    try {
      await api.storeHistoricalEvidence({
        organization_id: defaultOrgId,
        title,
        content,
        evidence_type: evidenceType,
        provenance: { source: 'MANUAL_INSPECTION', recorded_by: 'AUDITOR' },
      });
      setShowAddModal(false);
      setTitle('');
      setContent('');
      handleSearch();
    } catch (err: any) {
      alert(`Failed to store evidence: ${err.message}`);
    }
  };

  const typeBadges: Record<string, string> = {
    PROOF_SUMMARY: 'bg-cyan-950/80 text-cyan-300 border-cyan-800',
    INCIDENT: 'bg-rose-950/80 text-rose-300 border-rose-800',
    REGRESSION: 'bg-amber-950/80 text-amber-300 border-amber-800',
    REMEDIATION: 'bg-emerald-950/80 text-emerald-300 border-emerald-800',
    TEST_RATIONALE: 'bg-indigo-950/80 text-indigo-300 border-indigo-800',
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-wider mb-1">
            <BookOpen className="w-3.5 h-3.5" />
            Phase 5 Historical Knowledge &amp; Retrieval
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Historical Evidence Search</h1>
          <p className="text-sm text-slate-400 mt-1">
            Semantic retrieval across historical change proofs, production incidents, regressions, and past remediations.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white rounded-lg shadow-sm shadow-sky-600/30 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Record Evidence
        </button>
      </div>

      {/* Honest Architectural Disclosure Banner */}
      <div className="p-4 bg-slate-900 border border-cyan-800/60 rounded-xl flex items-start gap-3">
        <Info className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-bold text-white uppercase tracking-wider font-mono">
              CURRENT SEARCH ENGINE:
            </span>
            <span className="px-2 py-0.5 bg-cyan-950 text-cyan-300 border border-cyan-800 rounded font-mono font-bold">
              TF-IDF Cosine Similarity (In-Process)
            </span>
          </div>
          <p className="text-slate-400">
            Historical evidence similarity matching is powered by an in-memory, pure-Python TF-IDF term vectorizer and cosine similarity metric. External <code className="text-slate-300 font-mono">pgvector</code> or live neural embeddings are not configured.
          </p>
        </div>
      </div>

      {/* Search Input Bar */}
      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search prior incidents, breaking changes, regressions, or proof rationales..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-sky-500"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2.5 text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white rounded-xl shadow-sm transition-colors flex items-center gap-2"
        >
          {loading ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Search className="w-3.5 h-3.5" />
          )}
          <span>Search</span>
        </button>
      </form>

      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-200 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between text-xs text-slate-400 px-1 font-mono">
          <span>Found {results.length} historical evidence records</span>
          <span>Ranked by TF-IDF Cosine Similarity</span>
        </div>

        {results.length === 0 ? (
          <div className="p-16 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
            <History className="w-8 h-8 text-slate-600 mx-auto mb-3" />
            <h3 className="text-base font-medium text-slate-300">No Matching Historical Records</h3>
            <p className="text-xs text-slate-500 mt-1">
              Try adjusting your search terms or record new incident evidence using the button above.
            </p>
          </div>
        ) : (
          results.map((rec) => {
            const pct = Math.round((rec.similarity_score || 0) * 100);
            return (
              <div
                key={rec.id}
                className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                          typeBadges[rec.evidence_type] || 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        {rec.evidence_type}
                      </span>
                      <h3 className="text-base font-bold text-white">{rec.title}</h3>
                    </div>
                    <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                      <span>ID: {rec.id.slice(0, 8)}…</span>
                      <span>•</span>
                      <span className="flex items-center gap-1 text-slate-500">
                        <Calendar className="w-3.5 h-3.5" />
                        {new Date(rec.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  {/* Similarity Score Metric */}
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-mono text-slate-500 block">
                      TF-IDF Cosine
                    </span>
                    <span className="text-base font-mono font-bold text-cyan-400">
                      {rec.similarity_score?.toFixed(3)}
                    </span>
                    <div className="w-20 h-1.5 bg-slate-800 rounded-full mt-1 overflow-hidden">
                      <div
                        className="h-full bg-cyan-400 rounded-full"
                        style={{ width: `${Math.min(pct * 2, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                  {rec.content}
                </p>

                {rec.provenance && Object.keys(rec.provenance).length > 0 && (
                  <div className="pt-2 border-t border-slate-800 flex items-center gap-2 text-[11px] font-mono text-slate-400">
                    <span className="text-slate-500">Provenance:</span>
                    <span>{JSON.stringify(rec.provenance)}</span>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Record Evidence Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Record Historical Evidence</h3>
            <form onSubmit={handleCreateEvidence} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Memory Leak Incident in Gateway Service"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Evidence Type</label>
                <select
                  value={evidenceType}
                  onChange={(e) => setEvidenceType(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                >
                  <option value="PROOF_SUMMARY">PROOF_SUMMARY</option>
                  <option value="INCIDENT">INCIDENT</option>
                  <option value="REGRESSION">REGRESSION</option>
                  <option value="REMEDIATION">REMEDIATION</option>
                  <option value="TEST_RATIONALE">TEST_RATIONALE</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Content / Evidence Details</label>
                <textarea
                  required
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Detailed root cause, failure behavior, and remediation findings"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500 h-28"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white rounded-lg shadow-sm"
                >
                  Save Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
