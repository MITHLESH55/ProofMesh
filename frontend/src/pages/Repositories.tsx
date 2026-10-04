import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FolderGit2, Plus, GitBranch, Shield, ExternalLink } from 'lucide-react';
import { api } from '../services/api';
import { Repository } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { EmptyState } from '../components/EmptyState';

export const Repositories: React.FC = () => {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<any>(null);
  const [modalOpen, setModalOpen] = useState(false);

  // New repo form state
  const [owner, setOwner] = useState('');
  const [name, setName] = useState('');
  const [githubRepoId, setGithubRepoId] = useState('');
  const [defaultBranch, setDefaultBranch] = useState('main');
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<any>(null);

  const fetchRepositories = async () => {
    try {
      setError(null);
      const data = await api.getRepositories();
      setRepositories(data);
    } catch (err: any) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRepositories();
  }, []);

  const handleCreateRepo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!owner || !name || !githubRepoId) return;

    setCreating(true);
    setFormError(null);
    try {
      await api.createRepository({
        github_repository_id: githubRepoId.trim(),
        owner: owner.trim(),
        name: name.trim(),
        default_branch: defaultBranch.trim() || 'main',
      });
      setModalOpen(false);
      setOwner('');
      setName('');
      setGithubRepoId('');
      fetchRepositories();
    } catch (err: any) {
      setFormError(err);
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading connected repositories..." size="lg" />;
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={fetchRepositories} title="Unable to load repositories" />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Connected Repositories</h1>
          <p className="text-xs text-slate-400 mt-1">
            Repositories monitored for Pull Request events and software changes
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center gap-2 px-3.5 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-sm transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          Connect Repository
        </button>
      </div>

      {repositories.length === 0 ? (
        <EmptyState
          icon="repos"
          title="No repositories connected"
          description="Connect a GitHub repository to monitor pull requests and ingest changes."
          actionText="Connect First Repository"
          actionHref="#"
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {repositories.map((repo) => (
            <div
              key={repo.id}
              className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="p-2 bg-slate-950 rounded-lg border border-slate-800 text-sky-400">
                    <FolderGit2 className="w-5 h-5" />
                  </div>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
                    <Shield className="w-3 h-3" />
                    ACTIVE
                  </span>
                </div>

                <h3 className="text-base font-semibold text-white mt-3 truncate">{repo.name}</h3>
                <p className="text-xs text-slate-400 font-mono mt-0.5 truncate">{repo.full_name}</p>
              </div>

              <div className="mt-5 pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center gap-1.5 font-mono">
                  <GitBranch className="w-3.5 h-3.5 text-slate-500" />
                  <span>{repo.default_branch}</span>
                </div>
                <Link
                  to={`/repositories/${repo.id}`}
                  className="inline-flex items-center gap-1 text-sky-400 hover:text-sky-300 font-medium"
                >
                  View Details <ExternalLink className="w-3 h-3" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Connect Repository Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex justify-between items-center pb-4 border-b border-slate-800">
              <h3 className="text-base font-semibold text-white">Connect GitHub Repository</h3>
              <button
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            {formError && (
              <div className="mt-4">
                <ErrorMessage error={formError} onRetry={() => setFormError(null)} title="Connection failed" />
              </div>
            )}

            <form onSubmit={handleCreateRepo} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-1.5">
                  GitHub Repository ID
                </label>
                <input
                  type="text"
                  required
                  value={githubRepoId}
                  onChange={(e) => setGithubRepoId(e.target.value)}
                  placeholder="e.g. 102938475"
                  className="block w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-1.5">
                    Owner / Org
                  </label>
                  <input
                    type="text"
                    required
                    value={owner}
                    onChange={(e) => setOwner(e.target.value)}
                    placeholder="my-org"
                    className="block w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-1.5">
                    Repository Name
                  </label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="backend-service"
                    className="block w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-1.5">
                  Default Branch
                </label>
                <input
                  type="text"
                  value={defaultBranch}
                  onChange={(e) => setDefaultBranch(e.target.value)}
                  placeholder="main"
                  className="block w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:bg-sky-800/50 text-white text-xs font-semibold rounded-lg shadow-sm"
                >
                  {creating ? 'Connecting...' : 'Save & Connect'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
