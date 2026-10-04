import React from 'react';
import { GitPullRequest, FolderGit2, Inbox } from 'lucide-react';
import { Link } from 'react-router-dom';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  actionHref?: string;
  icon?: 'changes' | 'repos' | 'default';
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No records found',
  description = 'There are no records matching your current criteria.',
  actionText,
  actionHref,
  icon = 'default',
}) => {
  let IconComponent = Inbox;
  if (icon === 'changes') IconComponent = GitPullRequest;
  if (icon === 'repos') IconComponent = FolderGit2;

  return (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-slate-900/40 border border-slate-800/80 rounded-xl">
      <div className="p-4 bg-slate-800/60 rounded-2xl text-slate-400 mb-4 border border-slate-700/50">
        <IconComponent className="w-8 h-8 text-sky-400" />
      </div>
      <h3 className="text-base font-semibold text-slate-200">{title}</h3>
      <p className="mt-1.5 text-sm text-slate-400 max-w-sm">{description}</p>
      {actionText && actionHref && (
        <Link
          to={actionHref}
          className="mt-5 inline-flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-sm transition-all"
        >
          {actionText}
        </Link>
      )}
    </div>
  );
};
