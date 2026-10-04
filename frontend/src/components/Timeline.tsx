import React from 'react';
import {
  CheckCircle2,
  Clock,
  PlayCircle,
  AlertCircle,
  GitPullRequest,
  Webhook,
  FileCode2,
  Zap,
} from 'lucide-react';
import { AnalysisRun, AuditLog, ChangeStatus } from '../types';

interface TimelineProps {
  changeStatus: ChangeStatus;
  analysisRuns: AnalysisRun[];
  auditHistory: AuditLog[];
}

interface TimelineStep {
  key: string;
  title: string;
  description: string;
  timestamp?: string;
  status: 'completed' | 'active' | 'failed' | 'pending';
  icon: any;
  metadata?: any;
}

export const Timeline: React.FC<TimelineProps> = ({ changeStatus, analysisRuns, auditHistory }) => {
  const latestRun = analysisRuns[0];

  // Helper to find specific audit log
  const findAudit = (actionSubstring: string) =>
    auditHistory.find((l) => l.action.toLowerCase().includes(actionSubstring.toLowerCase()));

  const webhookAudit = findAudit('REPOSITORY_CONNECTED') || findAudit('PR_INGESTED');
  const prAudit = findAudit('PR_INGESTED');
  const changeAudit = findAudit('CHANGE_CREATED');
  const analysisQueuedAudit = findAudit('ANALYSIS_QUEUED');
  const analysisStartedAudit = findAudit('ANALYSIS_STARTED');
  const analysisCompletedAudit = findAudit('ANALYSIS_COMPLETED');
  const analysisFailedAudit = findAudit('ANALYSIS_FAILED');

  const steps: TimelineStep[] = [
    {
      key: 'webhook',
      title: 'Webhook Received',
      description: 'GitHub payload verified and ingested with HMAC-SHA256 signature.',
      timestamp: webhookAudit?.created_at,
      status: 'completed',
      icon: Webhook,
      metadata: webhookAudit?.event_metadata,
    },
    {
      key: 'pr_ingested',
      title: 'PR Ingested',
      description: 'Repository and pull request metadata persisted in database.',
      timestamp: prAudit?.created_at,
      status: 'completed',
      icon: GitPullRequest,
      metadata: prAudit?.event_metadata,
    },
    {
      key: 'change_created',
      title: 'Change Created',
      description: 'Change entity initialized and mapped to commit SHA.',
      timestamp: changeAudit?.created_at,
      status: 'completed',
      icon: FileCode2,
      metadata: changeAudit?.event_metadata,
    },
    {
      key: 'analysis_queued',
      title: 'Analysis Queued',
      description: 'Analysis job dispatched to Redis background worker queue.',
      timestamp: analysisQueuedAudit?.created_at || latestRun?.created_at,
      status: 'completed',
      icon: Clock,
      metadata: analysisQueuedAudit?.event_metadata,
    },
    {
      key: 'worker_started',
      title: 'Worker Started',
      description: latestRun?.worker_id
        ? `Worker (${latestRun.worker_id}) picked up job for execution.`
        : 'Worker picking up job for execution.',
      timestamp: analysisStartedAudit?.created_at || latestRun?.started_at || undefined,
      status:
        changeStatus === 'RUNNING' || changeStatus === 'COMPLETED' || changeStatus === 'FAILED'
          ? 'completed'
          : changeStatus === 'QUEUED'
          ? 'pending'
          : 'pending',
      icon: PlayCircle,
      metadata: analysisStartedAudit?.event_metadata,
    },
    {
      key: 'analysis_result',
      title:
        changeStatus === 'FAILED' || latestRun?.status === 'FAILED'
          ? 'Analysis Failed'
          : changeStatus === 'COMPLETED'
          ? 'Analysis Completed'
          : 'Analysis Ingestion Validation',
      description:
        changeStatus === 'FAILED'
          ? latestRun?.error_message || 'Analysis run encountered an unrecoverable error.'
          : changeStatus === 'COMPLETED'
          ? 'Phase 1 ingestion validation passed successfully.'
          : 'Awaiting completion of Phase 1 ingestion validation.',
      timestamp:
        analysisCompletedAudit?.created_at ||
        analysisFailedAudit?.created_at ||
        latestRun?.completed_at ||
        undefined,
      status:
        changeStatus === 'COMPLETED'
          ? 'completed'
          : changeStatus === 'FAILED'
          ? 'failed'
          : changeStatus === 'RUNNING'
          ? 'active'
          : 'pending',
      icon:
        changeStatus === 'COMPLETED'
          ? CheckCircle2
          : changeStatus === 'FAILED'
          ? AlertCircle
          : changeStatus === 'RUNNING'
          ? Zap
          : Clock,
      metadata: analysisCompletedAudit?.event_metadata || analysisFailedAudit?.event_metadata,
    },
  ];

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {steps.map((step, stepIdx) => {
          const isLast = stepIdx === steps.length - 1;
          const StepIcon = step.icon;

          let badgeColor = 'bg-slate-800 text-slate-400 border-slate-700';
          let lineColor = 'bg-slate-800';

          if (step.status === 'completed') {
            badgeColor = 'bg-emerald-950/80 text-emerald-400 border-emerald-700/60 ring-2 ring-emerald-500/20';
            lineColor = 'bg-emerald-800/40';
          } else if (step.status === 'active') {
            badgeColor = 'bg-sky-950/80 text-sky-400 border-sky-600/60 ring-4 ring-sky-500/20 animate-pulse';
            lineColor = 'bg-sky-800/40';
          } else if (step.status === 'failed') {
            badgeColor = 'bg-rose-950/80 text-rose-400 border-rose-700/60 ring-2 ring-rose-500/20';
            lineColor = 'bg-rose-800/40';
          }

          return (
            <li key={step.key}>
              <div className="relative pb-8">
                {!isLast && (
                  <span
                    className={`absolute left-4 top-4 -ml-px h-full w-0.5 ${lineColor} transition-colors`}
                    aria-hidden="true"
                  />
                )}
                <div className="relative flex items-start space-x-3">
                  <div
                    className={`relative flex h-8 w-8 items-center justify-center rounded-full border shadow-sm ${badgeColor}`}
                  >
                    <StepIcon className="h-4 w-4" aria-hidden="true" />
                  </div>
                  <div className="min-w-0 flex-1 pt-1">
                    <div className="flex justify-between items-center text-sm">
                      <p className="font-semibold text-slate-100">{step.title}</p>
                      {step.timestamp && (
                        <time className="text-xs font-mono text-slate-400">
                          {new Date(step.timestamp).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                          })}
                        </time>
                      )}
                    </div>
                    <p className="mt-0.5 text-xs text-slate-300/80">{step.description}</p>
                    {step.metadata && Object.keys(step.metadata).length > 0 && (
                      <div className="mt-2 p-2 bg-slate-950/60 rounded border border-slate-800 text-[11px] font-mono text-slate-400">
                        {JSON.stringify(step.metadata, null, 2)}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
