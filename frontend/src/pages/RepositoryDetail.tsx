import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { FolderGit2, ArrowLeft, GitBranch, ShieldCheck, ExternalLink } from 'lucide-react';
import { api } from '../services/api';
import { Change, Repository } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { EmptyState } from '../components/EmptyState';

export const RepositoryDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [repository, setRepository] = useState<Repository | null>(null);
  const [changes, setChanges] = useState<Change[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<any>(null);

  const fetchData = async () => {
    if (!id) return;
    try {
      setError(null);
      const [repoData, changesData] = await Promise.all([
        api.getRepository(id),
        api.getChanges({ repository_id: id }),
      ]);
      setRepository(repoData);
      setChanges(changesData);
    } catch (err: any) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  if (loading) {
    return <LoadingSpinner label="Loading repository details and changes..." size="lg" />;
  }

  if (error || !repository) {
    return (
      <div className="space-y-4">
        <Link to="/repositories" className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200">
          <ArrowLeft className="w-4 h-4" /> Back to Repositories
        </Link>
        <ErrorMessage error={error} onRetry={fetchData} title="Repository not found" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link to="/repositories" className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Repositories
      </Link>

      {/* Repo Header Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-sky-400">
              <FolderGit2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-bold text-white">{repository.name}</h1>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
                  <ShieldCheck className="w-3.5 h-3.5" /> ACTIVE
                </span>
              </div>
              <p className="text-xs font-mono text-slate-400 mt-1">{repository.full_name}</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-4 text-xs font-mono text-slate-400">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-950 rounded-lg border border-slate-800">
              <GitBranch className="w-3.5 h-3.5 text-slate-400" />
              <span>Branch: {repository.default_branch}</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-950 rounded-lg border border-slate-800">
              <span>GitHub ID: {repository.github_repository_id}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Associated Changes */}
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-white">Ingested Pull Requests & Changes</h2>

        {changes.length === 0 ? (
          <EmptyState
            icon="changes"
            title="No changes for this repository"
            description="Open a Pull Request on this repository in GitHub to trigger automatic ingestion."
          />
        ) : (
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950/60 text-xs font-mono uppercase text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-3.5 px-4 font-medium">PR #</th>
                    <th className="py-3.5 px-4 font-medium">Title</th>
                    <th className="py-3.5 px-4 font-medium">Commit</th>
                    <th className="py-3.5 px-4 font-medium">Status</th>
                    <th className="py-3.5 px-4 font-medium">Ingested At</th>
                    <th className="py-3.5 px-4 font-medium text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {changes.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-semibold text-sky-400 text-xs">
                        #{c.pull_request?.number || '?'}
                      </td>
                      <td className="py-3.5 px-4 font-medium text-slate-100">
                        {c.pull_request?.title || 'Untitled change'}
                      </td>
                      <td className="py-3.5 px-4">
                        <code className="text-xs bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                          {c.commit_sha.substring(0, 7)}
                        </code>
                      </td>
                      <td className="py-3.5 px-4">
                        <StatusBadge status={c.status} size="sm" />
                      </td>
                      <td className="py-3.5 px-4 text-xs font-mono text-slate-400">
                        {new Date(c.created_at).toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <Link
                          to={`/changes/${c.id}`}
                          className="inline-flex items-center gap-1 text-xs font-medium text-sky-400 hover:text-sky-300 hover:underline"
                        >
                          View <ExternalLink className="w-3 h-3" />
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
