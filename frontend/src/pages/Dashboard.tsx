import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FolderGit2,
  GitPullRequest,
  Clock,
  PlayCircle,
  CheckCircle2,
  AlertOctagon,
  RefreshCw,
  ArrowUpRight,
  ExternalLink,
} from 'lucide-react';
import { api } from '../services/api';
import { Change, Repository } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { EmptyState } from '../components/EmptyState';

export const Dashboard: React.FC = () => {
  const [changes, setChanges] = useState<Change[]>([]);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<any>(null);

  const fetchData = async () => {
    try {
      setError(null);
      const [changesData, reposData] = await Promise.all([
        api.getChanges({ limit: 10 }),
        api.getRepositories(),
      ]);
      setChanges(changesData);
      setRepositories(reposData);
    } catch (err: any) {
      setError(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Periodic refresh
    const interval = setInterval(() => {
      fetchData();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  // Metrics computation from real backend data
  const totalRepos = repositories.length;
  const queuedCount = changes.filter((c) => c.status === 'QUEUED').length;
  const runningCount = changes.filter((c) => c.status === 'RUNNING').length;
  const completedCount = changes.filter((c) => c.status === 'COMPLETED').length;
  const failedCount = changes.filter((c) => c.status === 'FAILED').length;
  const openChangesCount = changes.filter((c) => c.pull_request?.state === 'OPEN').length;

  if (loading) {
    return <LoadingSpinner label="Loading dashboard metrics and ingestion pipeline..." size="lg" />;
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-bold text-white">System Dashboard</h1>
          <button
            onClick={handleManualRefresh}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry
          </button>
        </div>
        <ErrorMessage error={error} onRetry={fetchData} title="Unable to load dashboard data" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page Title & Refresh */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Software Change Dashboard</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time ingestion and analysis pipeline status
          </p>
        </div>
        <button
          onClick={handleManualRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg transition-colors cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-sky-400' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh Pipeline'}
        </button>
      </div>

      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-slate-900/70 border border-slate-800/90 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Repositories</span>
            <FolderGit2 className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{totalRepos}</div>
          <span className="text-[11px] text-slate-500">Connected</span>
        </div>

        <div className="bg-slate-900/70 border border-slate-800/90 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Open Changes</span>
            <GitPullRequest className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-sky-300 font-mono">{openChangesCount}</div>
          <span className="text-[11px] text-slate-500">Active Pull Requests</span>
        </div>

        <div className="bg-slate-900/70 border border-slate-800/90 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Queued</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-300 font-mono">{queuedCount}</div>
          <span className="text-[11px] text-slate-500">In Job Queue</span>
        </div>

        <div className="bg-slate-900/70 border border-slate-800/90 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Running</span>
            <PlayCircle className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-sky-300 font-mono">{runningCount}</div>
          <span className="text-[11px] text-slate-500">Worker executing</span>
        </div>

        <div className="bg-slate-900/70 border border-slate-800/90 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Completed</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-300 font-mono">{completedCount}</div>
          <span className="text-[11px] text-slate-500">Validated</span>
        </div>

        <div className="bg-slate-900/70 border border-slate-800/90 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Failed</span>
            <AlertOctagon className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400 font-mono">{failedCount}</div>
          <span className="text-[11px] text-slate-500">Requires Attention</span>
        </div>
      </div>

      {/* Recent Ingested Changes Table */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-base font-semibold text-white">Recent Ingested Changes</h2>
          <Link
            to="/changes"
            className="text-xs font-medium text-sky-400 hover:text-sky-300 flex items-center gap-1"
          >
            View all changes <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {changes.length === 0 ? (
          <EmptyState
            icon="changes"
            title="No changes yet"
            description="Connect a repository or open a Pull Request on GitHub to begin ingestion."
            actionText="Connect Repository"
            actionHref="/repositories"
          />
        ) : (
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950/60 text-xs font-mono uppercase text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-3.5 px-4 font-medium">Pull Request</th>
                    <th className="py-3.5 px-4 font-medium">Repository</th>
                    <th className="py-3.5 px-4 font-medium">Commit SHA</th>
                    <th className="py-3.5 px-4 font-medium">Status</th>
                    <th className="py-3.5 px-4 font-medium">Created</th>
                    <th className="py-3.5 px-4 font-medium text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {changes.map((change) => (
                    <tr key={change.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-semibold text-sky-400">
                            #{change.pull_request?.number || '?'}
                          </span>
                          <span className="text-slate-100 font-medium truncate max-w-xs">
                            {change.pull_request?.title || 'Untitled change'}
                          </span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="text-xs font-mono text-slate-400">
                          {change.repository?.full_name || 'unknown'}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <code className="text-xs bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                          {change.commit_sha.substring(0, 7)}
                        </code>
                      </td>
                      <td className="py-3.5 px-4">
                        <StatusBadge status={change.status} size="sm" />
                      </td>
                      <td className="py-3.5 px-4 text-xs font-mono text-slate-400">
                        {new Date(change.created_at).toLocaleString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <Link
                          to={`/changes/${change.id}`}
                          className="inline-flex items-center gap-1 text-xs font-medium text-sky-400 hover:text-sky-300 hover:underline"
                        >
                          Details <ExternalLink className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
