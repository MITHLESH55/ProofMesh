import React, { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import {
  Terminal,
  Play,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Coins,
  Cpu,
  RefreshCw,
  Shield,
  FileText,
  Layers,
  ChevronRight,
} from 'lucide-react';
import { api } from '../services/api';
import { AgentTask, AgentAction } from '../types';

export const AgentTaskDetail: React.FC = () => {
  const { taskId } = useParams<{ taskId?: string }>();
  const [searchParams] = useSearchParams();
  const agentIdParam = searchParams.get('agent_id');

  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [selectedTask, setSelectedTask] = useState<AgentTask | null>(null);
  const [actions, setActions] = useState<AgentAction[]>([]);
  const [budgetInfo, setBudgetInfo] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const loadTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const taskList = await api.listAgentTasks({
        agent_id: agentIdParam || undefined,
      });
      setTasks(taskList);

      let current: AgentTask | null = null;
      if (taskId) {
        current = taskList.find((t) => t.id === taskId) || null;
      }
      if (!current && taskList.length > 0) {
        current = taskList[0];
      }
      setSelectedTask(current);

      if (current) {
        await loadTaskDetails(current.id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  const loadTaskDetails = async (id: string) => {
    try {
      const [actList, budget] = await Promise.all([
        api.listAgentActions({ task_id: id }).catch(() => []),
        api.getTaskBudget(id).catch(() => null),
      ]);
      setActions(actList);
      setBudgetInfo(budget);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    loadTasks();
  }, [taskId, agentIdParam]);

  const handleSelectTask = (t: AgentTask) => {
    setSelectedTask(t);
    loadTaskDetails(t.id);
  };

  const handleStartTask = async () => {
    if (!selectedTask) return;
    try {
      setStarting(true);
      const updated = await api.startAgentTask(selectedTask.id);
      setSelectedTask(updated);
      loadTaskDetails(updated.id);
    } catch (err: any) {
      alert(`Failed to start task: ${err.message}`);
    } finally {
      setStarting(false);
    }
  };

  const statusColors: Record<string, string> = {
    COMPLETED: 'bg-emerald-950/80 text-emerald-400 border-emerald-800/60',
    RUNNING: 'bg-sky-950/80 text-sky-400 border-sky-800/60',
    PENDING: 'bg-amber-950/80 text-amber-400 border-amber-800/60',
    FAILED: 'bg-rose-950/80 text-rose-400 border-rose-800/60',
    BLOCKED: 'bg-purple-950/80 text-purple-400 border-purple-800/60',
  };

  const stages = [
    { key: 'TASK', label: '1. Task Ingestion' },
    { key: 'PLAN', label: '2. Plan Synthesis' },
    { key: 'ACTIONS', label: '3. Governed Actions' },
    { key: 'EVIDENCE', label: '4. Evidence Gathering' },
    { key: 'VERIFICATION', label: '5. Verification' },
    { key: 'POLICY', label: '6. Policy Check' },
    { key: 'OUTCOME', label: '7. Final Decision' },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-wider mb-1">
            <Terminal className="w-3.5 h-3.5" />
            Phase 5 Agent Orchestrator
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Agent Task Execution & Action Ledger</h1>
          <p className="text-sm text-slate-400 mt-1">
            End-to-end task progression, plan inspection, resource budgets, and cryptographic audit records.
          </p>
        </div>
        <button
          onClick={loadTasks}
          disabled={loading}
          className="flex items-center gap-2 px-3.5 py-2 text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded-lg transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-200 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Task Selector List & Task Detail View */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Task List Selector */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 px-1">
            Orchestrated Tasks ({tasks.length})
          </h3>
          {tasks.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-500">
              No tasks found.
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {tasks.map((t) => (
                <button
                  key={t.id}
                  onClick={() => handleSelectTask(t)}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${
                    selectedTask?.id === t.id
                      ? 'bg-sky-950/40 border-sky-500/60 text-white'
                      : 'bg-slate-950/60 border-slate-800/80 text-slate-300 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-semibold truncate max-w-[130px]">
                      {t.task_type}
                    </span>
                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                        statusColors[t.status] || 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {t.status}
                    </span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-500 mt-1 truncate">
                    ID: {t.id.slice(0, 8)}…
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Task Detail Pane */}
        <div className="lg:col-span-3 space-y-6">
          {selectedTask ? (
            <>
              {/* Task Header & Budget Bar */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-bold text-white">{selectedTask.task_type}</h2>
                      <span
                        className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${
                          statusColors[selectedTask.status] || 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {selectedTask.status}
                      </span>
                    </div>
                    <p className="text-xs font-mono text-slate-400 mt-1">
                      Task ID: {selectedTask.id} • Agent: {selectedTask.agent_id} • Initiator: {selectedTask.initiator_type}
                    </p>
                  </div>

                  {selectedTask.status === 'PENDING' && (
                    <button
                      onClick={handleStartTask}
                      disabled={starting}
                      className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg shadow-sm transition-colors"
                    >
                      <Play className="w-3.5 h-3.5" />
                      {starting ? 'Starting...' : 'Start Execution'}
                    </button>
                  )}
                </div>

                {/* KPI Metrics */}
                <div className="grid grid-cols-4 gap-3 pt-3 border-t border-slate-800">
                  <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Clock className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Steps</span>
                    </div>
                    <div className="text-lg font-mono font-bold text-white mt-1">
                      {selectedTask.step_count} <span className="text-xs text-slate-500">steps</span>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Tokens</span>
                    </div>
                    <div className="text-lg font-mono font-bold text-white mt-1">
                      {selectedTask.token_count}
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Coins className="w-3.5 h-3.5 text-amber-400" />
                      <span>Cost Estimate</span>
                    </div>
                    <div className="text-lg font-mono font-bold text-white mt-1">
                      ${selectedTask.cost_estimate.toFixed(4)}
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Shield className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Budget Status</span>
                    </div>
                    <div className="text-xs font-mono font-bold text-emerald-400 mt-2">
                      {budgetInfo?.within_budget !== false ? 'WITHIN LIMITS' : 'BUDGET EXCEEDED'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Visual Execution Flow Pipeline */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Execution Pipeline Progression
                </span>
                <div className="flex flex-wrap items-center gap-2 pt-2">
                  {stages.map((stage, idx) => {
                    const isCompleted = selectedTask.status === 'COMPLETED';
                    const isRunning = selectedTask.status === 'RUNNING';

                    return (
                      <React.Fragment key={stage.key}>
                        <div
                          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-mono font-medium ${
                            isCompleted
                              ? 'bg-emerald-950/60 border-emerald-800/60 text-emerald-300'
                              : isRunning
                              ? 'bg-sky-950/60 border-sky-800/60 text-sky-300'
                              : 'bg-slate-950 border-slate-800 text-slate-500'
                          }`}
                        >
                          {isCompleted ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <div className="w-2 h-2 rounded-full bg-slate-600" />
                          )}
                          <span>{stage.label}</span>
                        </div>
                        {idx < stages.length - 1 && (
                          <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
                        )}
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>

              {/* Plan & Result Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-2">
                  <div className="flex items-center gap-2 text-cyan-400">
                    <FileText className="w-4 h-4" />
                    <h3 className="text-xs font-bold uppercase tracking-wider">Generated Plan</h3>
                  </div>
                  <pre className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 max-h-48 overflow-y-auto">
                    {JSON.stringify(selectedTask.plan || {}, null, 2)}
                  </pre>
                </div>

                <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-2">
                  <div className="flex items-center gap-2 text-indigo-400">
                    <Layers className="w-4 h-4" />
                    <h3 className="text-xs font-bold uppercase tracking-wider">Execution Result</h3>
                  </div>
                  <pre className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 max-h-48 overflow-y-auto">
                    {JSON.stringify(selectedTask.result || {}, null, 2)}
                  </pre>
                </div>
              </div>

              {/* Action Audit Ledger Table */}
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-sm font-semibold text-white">Immutable Action Ledger</h3>
                  </div>
                  <span className="text-xs font-mono text-slate-500">
                    {actions.length} recorded actions
                  </span>
                </div>

                {actions.length === 0 ? (
                  <div className="p-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
                    No actions recorded for this task in the ledger yet.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-mono">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400">
                          <th className="py-2.5 px-3">Action Type</th>
                          <th className="py-2.5 px-3">Tool / Capability</th>
                          <th className="py-2.5 px-3">Policy Gate</th>
                          <th className="py-2.5 px-3">Status</th>
                          <th className="py-2.5 px-3">Timestamp</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {actions.map((act) => (
                          <tr key={act.id} className="hover:bg-slate-800/30">
                            <td className="py-2.5 px-3 font-semibold text-slate-200">
                              {act.action_type}
                            </td>
                            <td className="py-2.5 px-3 text-cyan-400">
                              {act.tool_name || act.requested_capability}
                            </td>
                            <td className="py-2.5 px-3">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  act.policy_decision === 'ALLOWED'
                                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                                    : 'bg-rose-950 text-rose-400 border border-rose-800'
                                }`}
                              >
                                {act.policy_decision}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-slate-300">{act.status}</td>
                            <td className="py-2.5 px-3 text-slate-500">
                              {new Date(act.created_at).toLocaleTimeString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="p-16 text-center text-slate-500 text-sm bg-slate-900/40 border border-slate-800 rounded-xl">
              Select a task from the left sidebar to inspect execution steps, budgets, and action logs.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
