import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  GitCommit,
  FolderGit2,
  RotateCw,
  User,
  Info,
  Layers,
  Terminal,
  Clock,
} from 'lucide-react';
import { api } from '../services/api';
import { ChangeDetail as IChangeDetail } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Timeline } from '../components/Timeline';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';

export const ChangeDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [change, setChange] = useState<IChangeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [error, setError] = useState<any>(null);

  const fetchChangeDetail = async () => {
    if (!id) return;
    try {
      setError(null);
      const data = await api.getChangeById(id);
      setChange(data);
    } catch (err: any) {
      setError(err);
    } finally {
      setLoading(false);
      setReanalyzing(false);
    }
  };

  useEffect(() => {
    fetchChangeDetail();

    // Auto-poll while change is QUEUED or RUNNING
    const interval = setInterval(() => {
      if (change?.status === 'QUEUED' || change?.status === 'RUNNING') {
        fetchChangeDetail();
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [id, change?.status]);

  const handleReanalyze = async () => {
    if (!id) return;
    setReanalyzing(true);
    try {
      await api.reanalyzeChange(id, 'User requested reanalysis from web dashboard');
      await fetchChangeDetail();
    } catch (err: any) {
      setError(err);
      setReanalyzing(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading change lifecycle and analysis history..." size="lg" />;
  }

  if (error || !change) {
    return (
      <div className="space-y-4">
        <Link to="/changes" className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200">
          <ArrowLeft className="w-4 h-4" /> Back to Changes
        </Link>
        <ErrorMessage error={error} onRetry={fetchChangeDetail} title="Change not found" />
      </div>
    );
  }

  const { pull_request: pr, repository: repo, analysis_runs: runs, audit_history: audits } = change;

  return (
    <div className="space-y-8">
      {/* Back link */}
      <Link to="/changes" className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Changes
      </Link>

      {/* Main Header Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm font-bold text-sky-400">
                PR #{pr.number}
              </span>
              <h1 className="text-xl font-bold text-white">{pr.title}</h1>
              <StatusBadge status={change.status} />
            </div>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 pt-1">
              <span className="flex items-center gap-1">
                <FolderGit2 className="w-3.5 h-3.5 text-slate-500" />
                {repo.full_name}
              </span>
              <span className="flex items-center gap-1">
                <User className="w-3.5 h-3.5 text-slate-500" />
                {pr.author}
              </span>
              <span className="flex items-center gap-1 font-mono">
                <GitCommit className="w-3.5 h-3.5 text-slate-500" />
                {change.commit_sha}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleReanalyze}
              disabled={reanalyzing || change.status === 'RUNNING'}
              className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-all cursor-pointer"
            >
              <RotateCw className={`w-3.5 h-3.5 ${reanalyzing ? 'animate-spin text-sky-400' : ''}`} />
              {reanalyzing ? 'Dispatching...' : 'Reanalyze Change'}
            </button>
          </div>
        </div>

        {/* PR Description if present */}
        {pr.description && (
          <div className="p-4 bg-slate-950/60 rounded-lg border border-slate-800/80 text-xs text-slate-300">
            <p className="font-mono text-[11px] text-slate-500 uppercase mb-1">Pull Request Description</p>
            <p className="whitespace-pre-wrap">{pr.description}</p>
          </div>
        )}

        {/* Honest Phase 1 Scope Callout */}
        <div className="p-4 bg-sky-950/30 border border-sky-900/60 rounded-lg flex items-start gap-3 text-xs text-sky-200">
          <Info className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-sky-300">Phase 1 Ingestion Validation Active</span>
            <p className="mt-0.5 text-slate-300">
              The ingestion worker validates the Pull Request event, verifies HMAC payload authenticity, confirms commit SHA integrity, and maintains the asynchronous job lifecycle.
              <span className="block text-slate-400 text-[11px] mt-1 font-mono">
                * Note: Deep semantic AST analysis, dependency graph, and risk scoring are scheduled for future phases.
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Timeline & Analysis Runs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Analysis Lifecycle Timeline */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6">
            <h2 className="text-base font-semibold text-white mb-6 flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-400" />
              Analysis Execution Timeline
            </h2>
            <Timeline
              changeStatus={change.status}
              analysisRuns={runs}
              auditHistory={audits}
            />
          </div>

          {/* Analysis Runs History */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6">
            <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-sky-400" />
              Analysis Runs History ({runs.length})
            </h2>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/60 font-mono uppercase text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Run ID</th>
                    <th className="py-2.5 px-3">Stage</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Worker</th>
                    <th className="py-2.5 px-3">Started</th>
                    <th className="py-2.5 px-3">Completed</th>
                    <th className="py-2.5 px-3 text-right">Proof</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {runs.map((run) => (
                    <tr key={run.id} className="hover:bg-slate-800/40">
                      <td className="py-2.5 px-3 text-slate-400">{run.id.substring(0, 8)}...</td>
                      <td className="py-2.5 px-3 text-slate-200">{run.stage}</td>
                      <td className="py-2.5 px-3">
                        <StatusBadge status={run.status} size="sm" />
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">{run.worker_id || '—'}</td>
                      <td className="py-2.5 px-3 text-slate-400">
                        {run.started_at ? new Date(run.started_at).toLocaleTimeString() : '—'}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">
                        {run.completed_at ? new Date(run.completed_at).toLocaleTimeString() : '—'}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <Link
                          to={`/assurance/${run.id}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 border border-indigo-500/20 rounded text-xs transition-colors"
                        >
                          View Proof &rarr;
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Col: Change Metadata & Audit Stream */}
        <div className="space-y-6">
          {/* Metadata Card */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-semibold text-white">Change Information</h3>
            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-500 uppercase tracking-wider block font-mono text-[10px]">
                  Commit Head
                </span>
                <span className="font-mono text-slate-200 break-all">{pr.head_sha}</span>
              </div>
              <div>
                <span className="text-slate-500 uppercase tracking-wider block font-mono text-[10px]">
                  Commit Base
                </span>
                <span className="font-mono text-slate-200 break-all">{pr.base_sha}</span>
              </div>
              <div>
                <span className="text-slate-500 uppercase tracking-wider block font-mono text-[10px]">
                  Ingestion Source
                </span>
                <span className="text-slate-200 font-mono">{change.source}</span>
              </div>
              <div>
                <span className="text-slate-500 uppercase tracking-wider block font-mono text-[10px]">
                  Ingested Timestamp
                </span>
                <span className="text-slate-200">{new Date(change.created_at).toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Audit Logs Stream */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-slate-400" />
              Audit Stream ({audits.length})
            </h3>
            <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
              {audits.map((log) => (
                <div key={log.id} className="p-2.5 bg-slate-950/70 rounded border border-slate-800 text-xs">
                  <div className="flex justify-between items-center text-[11px] font-mono text-slate-400">
                    <span className="text-sky-400 font-semibold">{log.action}</span>
                    <span>{new Date(log.created_at).toLocaleTimeString()}</span>
                  </div>
                  {log.event_metadata && Object.keys(log.event_metadata).length > 0 && (
                    <p className="mt-1 font-mono text-[10px] text-slate-400 truncate">
                      {JSON.stringify(log.event_metadata)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
