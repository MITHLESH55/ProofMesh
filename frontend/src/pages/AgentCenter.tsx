import React, { useEffect, useState } from 'react';
import {
  Bot,
  Shield,
  Plus,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Lock,
  Key,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { AgentDefinition } from '../types';

export const AgentCenter: React.FC = () => {
  const [agents, setAgents] = useState<AgentDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [testingAgent, setTestingAgent] = useState<AgentDefinition | null>(null);
  const [testCapability, setTestCapability] = useState('READ_REPOSITORY');
  const [testOrgId, setTestOrgId] = useState('');
  const [testResult, setTestResult] = useState<any | null>(null);

  // New Agent Form
  const [name, setName] = useState('');
  const [agentType, setAgentType] = useState('REVIEW_AGENT');
  const [provider, setProvider] = useState('mock');
  const [model, setModel] = useState('gemini-1.5-pro');
  const [version] = useState('1.0.0');
  const [autonomyLevel, setAutonomyLevel] = useState(1);

  const loadAgents = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listAgents();
      setAgents(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load agents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const handleRegisterAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      const defaultOrgId = agents[0]?.organization_id || '00000000-0000-0000-0000-000000000001';
      await api.registerAgent({
        organization_id: defaultOrgId,
        name,
        agent_type: agentType,
        provider,
        model,
        version,
        autonomy_level: Number(autonomyLevel),
      });
      setShowRegisterModal(false);
      setName('');
      loadAgents();
    } catch (err: any) {
      alert(`Registration failed: ${err.message}`);
    }
  };

  const handleDisable = async (agentId: string) => {
    if (!confirm('Are you sure you want to disable this agent? It will immediately revoke all capabilities.')) return;
    try {
      await api.disableAgent(agentId);
      loadAgents();
    } catch (err: any) {
      alert(`Failed to disable agent: ${err.message}`);
    }
  };

  const handleCheckCapability = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testingAgent) return;
    try {
      const res = await api.checkCapability(
        testingAgent.id,
        testCapability,
        testOrgId.trim() || undefined
      );
      setTestResult(res);
    } catch (err: any) {
      setTestResult({ authorized: false, reason: err.message });
    }
  };

  const autonomyBadges: Record<number, { label: string; color: string }> = {
    1: { label: 'Level 1: Read-Only Assistant', color: 'bg-slate-800 text-slate-300 border-slate-700' },
    2: { label: 'Level 2: Advisory / Recommender', color: 'bg-cyan-950 text-cyan-300 border-cyan-800' },
    3: { label: 'Level 3: Governed Proposer', color: 'bg-indigo-950 text-indigo-300 border-indigo-800' },
    4: { label: 'Level 4: Supervised Executor', color: 'bg-amber-950 text-amber-300 border-amber-800' },
    5: { label: 'Level 5: Autonomous with Escalation', color: 'bg-rose-950 text-rose-300 border-rose-800' },
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-wider mb-1">
            <Shield className="w-3.5 h-3.5" />
            Phase 5 Agent Governance & Security
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Agent Governance Center</h1>
          <p className="text-sm text-slate-400 mt-1">
            Identity registry, 5-tier autonomy controls, capability scopes, and execution budget boundaries.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadAgents}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowRegisterModal(true)}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white rounded-lg shadow-sm shadow-sky-600/30 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Register Agent
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-200 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Agents Grid */}
      {agents.length === 0 ? (
        <div className="p-12 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
          <Bot className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-medium text-slate-300">No AI Agents Registered</h3>
          <p className="text-xs text-slate-500 mt-1">
            Click &quot;Register Agent&quot; above to create a governed autonomous agent with bounded capabilities.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {agents.map((agent) => {
            const badge = autonomyBadges[agent.autonomy_level] || autonomyBadges[1];
            const isActive = agent.status === 'ACTIVE';

            return (
              <div
                key={agent.id}
                className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 space-y-4 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2.5 rounded-lg border ${
                        isActive
                          ? 'bg-sky-950/80 border-sky-800/60 text-sky-400'
                          : 'bg-slate-800/80 border-slate-700 text-slate-500'
                      }`}
                    >
                      <Bot className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-white">{agent.name}</h3>
                        <span
                          className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                            isActive
                              ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800/60'
                              : 'bg-rose-950/80 text-rose-400 border-rose-800/60'
                          }`}
                        >
                          {agent.status}
                        </span>
                      </div>
                      <p className="text-xs font-mono text-slate-400 mt-0.5">
                        {agent.agent_type} • v{agent.version}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        setTestingAgent(agent);
                        setTestResult(null);
                      }}
                      title="Test Capability Authorization"
                      className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-xs transition-colors"
                    >
                      <Key className="w-3.5 h-3.5" />
                    </button>
                    {isActive ? (
                      <button
                        onClick={() => handleDisable(agent.id)}
                        title="Disable Agent"
                        className="p-1.5 bg-slate-800 hover:bg-rose-950 hover:text-rose-400 text-slate-400 rounded border border-slate-700 text-xs transition-colors"
                      >
                        <Lock className="w-3.5 h-3.5" />
                      </button>
                    ) : (
                      <span className="p-1.5 text-slate-600">
                        <Lock className="w-3.5 h-3.5" />
                      </span>
                    )}
                  </div>
                </div>

                {/* Autonomy Level Badge */}
                <div>
                  <span
                    className={`inline-block text-[11px] font-mono px-2 py-0.5 rounded border ${badge.color}`}
                  >
                    {badge.label}
                  </span>
                </div>

                {/* Capabilities list */}
                <div className="space-y-1.5">
                  <span className="text-xs font-medium text-slate-400">Granted Capabilities:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {(agent.capabilities || []).map((cap) => (
                      <span
                        key={cap}
                        className="text-[10px] font-mono bg-slate-950 text-cyan-400 border border-slate-800 px-2 py-0.5 rounded"
                      >
                        {cap}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Meta details footer */}
                <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500 font-mono">
                  <span>
                    Provider: <strong className="text-slate-300">{agent.provider}</strong> ({agent.model})
                  </span>
                  <Link
                    to={`/agents/tasks?agent_id=${agent.id}`}
                    className="flex items-center gap-1 text-sky-400 hover:text-sky-300"
                  >
                    <span>View Tasks</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Capability Test Drawer / Modal */}
      {testingAgent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-cyan-400" />
                <h3 className="text-base font-bold text-white">
                  Capability & Tenant Authorization Check
                </h3>
              </div>
              <button
                onClick={() => setTestingAgent(null)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Simulate an authorization evaluation against the Agent Governance Service for{' '}
              <strong className="text-white">{testingAgent.name}</strong>.
            </p>

            <form onSubmit={handleCheckCapability} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Capability to Validate
                </label>
                <select
                  value={testCapability}
                  onChange={(e) => setTestCapability(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                >
                  <option value="READ_REPOSITORY">READ_REPOSITORY (Level 1+)</option>
                  <option value="READ_GRAPH">READ_GRAPH (Level 1+)</option>
                  <option value="ANALYZE_DIFF">ANALYZE_DIFF (Level 1+)</option>
                  <option value="GENERATE_ASSURANCE">GENERATE_ASSURANCE (Level 2+)</option>
                  <option value="PROPOSE_REMEDIATION">PROPOSE_REMEDIATION (Level 3+)</option>
                  <option value="EXECUTE_TOOL">EXECUTE_TOOL (Level 4+)</option>
                  <option value="AUTO_APPROVE">AUTO_APPROVE (Level 5+)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Target Organization ID (Tenant Isolation Test)
                </label>
                <input
                  type="text"
                  value={testOrgId}
                  onChange={(e) => setTestOrgId(e.target.value)}
                  placeholder="Optional foreign organization ID to test tenant rejection"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white rounded-lg"
                >
                  Evaluate Authorization
                </button>
              </div>
            </form>

            {testResult && (
              <div
                className={`p-3.5 rounded-lg border text-xs font-mono space-y-1 ${
                  testResult.authorized
                    ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-300'
                    : 'bg-rose-950/40 border-rose-800/80 text-rose-300'
                }`}
              >
                <div className="flex items-center gap-2 font-bold">
                  {testResult.authorized ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span>AUTHORIZATION GRANTED</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4 text-rose-400" />
                      <span>AUTHORIZATION DENIED</span>
                    </>
                  )}
                </div>
                {testResult.reason && <div>Reason: {testResult.reason}</div>}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Register Modal */}
      {showRegisterModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-white">Register AI Agent</h3>
            <form onSubmit={handleRegisterAgent} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Agent Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. CodeReviewBot"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Agent Type</label>
                  <select
                    value={agentType}
                    onChange={(e) => setAgentType(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                  >
                    <option value="REVIEW_AGENT">REVIEW_AGENT</option>
                    <option value="TEST_AGENT">TEST_AGENT</option>
                    <option value="SECURITY_AGENT">SECURITY_AGENT</option>
                    <option value="ARCHITECTURE_AGENT">ARCHITECTURE_AGENT</option>
                    <option value="REMEDIATION_AGENT">REMEDIATION_AGENT</option>
                    <option value="ORCHESTRATOR_AGENT">ORCHESTRATOR_AGENT</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Autonomy Level (1-5)
                  </label>
                  <select
                    value={autonomyLevel}
                    onChange={(e) => setAutonomyLevel(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                  >
                    <option value={1}>Level 1: Read-Only</option>
                    <option value={2}>Level 2: Advisory</option>
                    <option value={3}>Level 3: Proposer</option>
                    <option value={4}>Level 4: Supervised</option>
                    <option value={5}>Level 5: Autonomous</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Provider</label>
                  <input
                    type="text"
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Model</label>
                  <input
                    type="text"
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white rounded-lg"
                >
                  Register Agent
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
