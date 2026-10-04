import React from 'react';
import { CheckCircle2, Clock, PlayCircle, AlertTriangle, XCircle, ShieldCheck } from 'lucide-react';
import { ChangeStatus, AnalysisStatus } from '../types';

interface StatusBadgeProps {
  status: ChangeStatus | AnalysisStatus | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = status.toUpperCase();

  let styles = 'bg-slate-800 text-slate-300 border-slate-700';
  let Icon = Clock;

  switch (normalized) {
    case 'COMPLETED':
      styles = 'bg-emerald-950/70 text-emerald-300 border-emerald-800/60';
      Icon = CheckCircle2;
      break;
    case 'RUNNING':
      styles = 'bg-sky-950/70 text-sky-300 border-sky-800/60 animate-pulse';
      Icon = PlayCircle;
      break;
    case 'QUEUED':
      styles = 'bg-amber-950/70 text-amber-300 border-amber-800/60';
      Icon = Clock;
      break;
    case 'INGESTED':
      styles = 'bg-purple-950/70 text-purple-300 border-purple-800/60';
      Icon = ShieldCheck;
      break;
    case 'FAILED':
      styles = 'bg-rose-950/70 text-rose-300 border-rose-800/60';
      Icon = XCircle;
      break;
    case 'CANCELLED':
      styles = 'bg-slate-900 text-slate-400 border-slate-800';
      Icon = AlertTriangle;
      break;
  }

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs tracking-wider';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono font-medium rounded-full border ${sizeClasses} ${styles}`}
    >
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      {normalized}
    </span>
  );
};
