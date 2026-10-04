import React, { useEffect, useState } from 'react';
import { Shield, Webhook, Server, Database, Copy, Check } from 'lucide-react';
import { api } from '../services/api';
import { User, ReadyStatus } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const Settings: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [readyStatus, setReadyStatus] = useState<ReadyStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [copiedWebhook, setCopiedWebhook] = useState(false);

  useEffect(() => {
    Promise.all([api.getMe(), api.getReady()])
      .then(([userData, readyData]) => {
        setUser(userData);
        setReadyStatus(readyData);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const webhookUrl = `${window.location.origin}/api/v1/webhooks/github`;

  const handleCopyWebhook = () => {
    navigator.clipboard.writeText(webhookUrl);
    setCopiedWebhook(true);
    setTimeout(() => setCopiedWebhook(false), 2000);
  };

  if (loading) {
    return <LoadingSpinner label="Loading workspace configuration..." size="lg" />;
  }

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Workspace Settings</h1>
        <p className="text-xs text-slate-400 mt-1">
          Manage GitHub webhook integrations, organization details, and system connectivity
        </p>
      </div>

      {/* GitHub Webhook Setup Guide */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 space-y-5">
        <div className="flex items-center gap-3 pb-3 border-b border-slate-800">
          <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-sky-400">
            <Webhook className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">GitHub Webhook Integration</h2>
            <p className="text-xs text-slate-400">Configure GitHub repository or organization webhooks</p>
          </div>
        </div>

        <div className="space-y-4 text-xs text-slate-300">
          <div>
            <label className="block text-[11px] font-mono uppercase text-slate-400 mb-1.5">
              Payload URL
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={webhookUrl}
                className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 font-mono text-slate-200 select-all"
              />
              <button
                onClick={handleCopyWebhook}
                className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 flex items-center gap-1.5 transition-colors"
              >
                {copiedWebhook ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedWebhook ? 'Copied' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80">
              <span className="font-mono text-slate-400 block text-[11px] uppercase mb-1">Content Type</span>
              <span className="font-mono text-slate-200">application/json</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80">
              <span className="font-mono text-slate-400 block text-[11px] uppercase mb-1">Secret</span>
              <span className="font-mono text-slate-200">Configured in GITHUB_WEBHOOK_SECRET</span>
            </div>
          </div>

          <div>
            <span className="font-mono text-slate-400 block text-[11px] uppercase mb-1.5">
              Supported Events (Phase 1)
            </span>
            <div className="flex flex-wrap gap-2">
              <span className="px-2.5 py-1 bg-slate-950 border border-slate-800 rounded font-mono text-[11px] text-sky-300">
                pull_request.opened
              </span>
              <span className="px-2.5 py-1 bg-slate-950 border border-slate-800 rounded font-mono text-[11px] text-sky-300">
                pull_request.synchronize
              </span>
              <span className="px-2.5 py-1 bg-slate-950 border border-slate-800 rounded font-mono text-[11px] text-sky-300">
                pull_request.reopened
              </span>
              <span className="px-2.5 py-1 bg-slate-950 border border-slate-800 rounded font-mono text-[11px] text-sky-300">
                pull_request.closed
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* System Infrastructure & Readiness */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 space-y-5">
        <div className="flex items-center gap-3 pb-3 border-b border-slate-800">
          <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-sky-400">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">System Diagnostics & Infrastructure</h2>
            <p className="text-xs text-slate-400">Core service dependencies health check</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Database className="w-4 h-4 text-slate-400" />
              <div>
                <p className="font-semibold text-slate-200">PostgreSQL Database</p>
                <p className="text-slate-500 font-mono text-[11px]">Relational Persistence</p>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded font-mono text-[11px] bg-emerald-950 text-emerald-400 border border-emerald-800">
              {readyStatus?.dependencies?.postgres || 'CONNECTED'}
            </span>
          </div>

          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Server className="w-4 h-4 text-slate-400" />
              <div>
                <p className="font-semibold text-slate-200">Redis Queue & Worker</p>
                <p className="text-slate-500 font-mono text-[11px]">Asynchronous Ingestion</p>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded font-mono text-[11px] bg-emerald-950 text-emerald-400 border border-emerald-800">
              {readyStatus?.dependencies?.redis || 'CONNECTED'}
            </span>
          </div>
        </div>
      </div>

      {/* User & Organization Details */}
      {user && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-3 pb-3 border-b border-slate-800">
            <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-sky-400">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Account & RBAC Role</h2>
              <p className="text-xs text-slate-400">Your profile and organization memberships</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-500 block font-mono text-[10px] uppercase mb-1">User Name</span>
              <span className="font-semibold text-slate-200">{user.full_name}</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-500 block font-mono text-[10px] uppercase mb-1">Email</span>
              <span className="font-mono text-slate-200">{user.email}</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-500 block font-mono text-[10px] uppercase mb-1">RBAC Role</span>
              <span className="font-mono text-sky-400 font-bold">{user.role}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
