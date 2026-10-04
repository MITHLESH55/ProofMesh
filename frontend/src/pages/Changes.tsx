import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { RefreshCw, ExternalLink, Search } from 'lucide-react';
import { api } from '../services/api';
import { Change, Repository } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { EmptyState } from '../components/EmptyState';

const STATUS_FILTERS = ['ALL', 'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED'];

export const Changes: React.FC = () => {
  const [changes, setChanges] = useState<Change[]>([]);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedRepoId, setSelectedRepoId] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<any>(null);

  const fetchChanges = async () => {
    try {
      setError(null);
      const [changesData, reposData] = await Promise.all([
        api.getChanges({
          status: selectedStatus,
          repository_id: selectedRepoId || undefined,
        }),
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
    fetchChanges();
  }, [selectedStatus, selectedRepoId]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchChanges();
  };

  // Client-side search filtering by PR title or commit
  const filteredChanges = changes.filter((c) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    const titleMatch = c.pull_request?.title.toLowerCase().includes(term);
    const commitMatch = c.commit_sha.toLowerCase().includes(term);
    const prNumMatch = c.pull_request?.number.toString().includes(term);
    return titleMatch || commitMatch || prNumMatch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Software Changes</h1>
          <p className="text-xs text-slate-400 mt-1">
            Track ingested pull requests, commit changes, and background analysis runs
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg transition-colors cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-sky-400' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
        {/* Status Tabs */}
        <div className="flex flex-wrap gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          {STATUS_FILTERS.map((status) => (
            <button
              key={status}
              onClick={() => setSelectedStatus(status)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                selectedStatus === status
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {/* Repository & Search Filters */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Filter by title / commit..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
          </div>

          <select
            value={selectedRepoId}
            onChange={(e) => setSelectedRepoId(e.target.value)}
            className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Repositories</option>
            {repositories.map((r) => (
              <option key={r.id} value={r.id}>
                {r.full_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Content */}
      {loading ? (
        <LoadingSpinner label="Fetching ingested changes..." size="lg" />
      ) : error ? (
        <ErrorMessage error={error} onRetry={fetchChanges} title="Unable to load changes" />
      ) : filteredChanges.length === 0 ? (
        <EmptyState
          icon="changes"
          title="No changes match your criteria"
          description={
            changes.length === 0
              ? 'No GitHub Pull Request events have been received yet.'
              : 'Try clearing status or search filters.'
          }
        />
      ) : (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4 font-medium">PR #</th>
                  <th className="py-3.5 px-4 font-medium">Title</th>
                  <th className="py-3.5 px-4 font-medium">Repository</th>
                  <th className="py-3.5 px-4 font-medium">Commit SHA</th>
                  <th className="py-3.5 px-4 font-medium">Status</th>
                  <th className="py-3.5 px-4 font-medium">Created</th>
                  <th className="py-3.5 px-4 font-medium">Updated</th>
                  <th className="py-3.5 px-4 font-medium text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredChanges.map((change) => (
                  <tr key={change.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-semibold text-sky-400 text-xs">
                      #{change.pull_request?.number || '?'}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-100 max-w-xs truncate">
                      {change.pull_request?.title || 'Untitled change'}
                    </td>
                    <td className="py-3.5 px-4 text-xs font-mono text-slate-400">
                      {change.repository?.full_name || 'unknown'}
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
                    <td className="py-3.5 px-4 text-xs font-mono text-slate-400">
                      {new Date(change.updated_at).toLocaleString([], {
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
                        Inspect <ExternalLink className="w-3 h-3" />
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
  );
};
