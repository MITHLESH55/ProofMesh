import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Server,
  Zap,
  Clock,
  ShieldCheck,
  FileCheck,
  TrendingUp,
  BarChart2,
  Terminal,
  Layers,
} from 'lucide-react';
import { api } from '../services/api';
import {
  Deployment,
  RuntimeFinding,
  RuntimeMetricsSummary,
  PredictionVsObservedReport,
  ExtendedChangeProof,
  CIAssuranceCheck,
} from '../types';

export const RuntimeAssurance: React.FC = () => {
  const [searchParams] = useSearchParams();
  const changeIdParam = searchParams.get('change_id') || '';

  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [selectedDeployment, setSelectedDeployment] = useState<Deployment | null>(null);
  const [metricsSummary, setMetricsSummary] = useState<RuntimeMetricsSummary | null>(null);
  const [findings, setFindings] = useState<RuntimeFinding[]>([]);
  const [predictionReport, setPredictionReport] = useState<PredictionVsObservedReport | null>(null);
  const [extendedProof, setExtendedProof] = useState<ExtendedChangeProof | null>(null);
  const [ciCheckResult, setCiCheckResult] = useState<CIAssuranceCheck | null>(null);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'predictions' | 'findings' | 'ci_gate' | 'proof'>('overview');
  const [simulating, setSimulating] = useState(false);

  const loadData = async () => {
    try {
      setRefreshing(true);
      const deps = await api.getDeployments(changeIdParam ? { change_id: changeIdParam } : undefined);
      setDeployments(deps);

      let currentDep = selectedDeployment;
      if (!currentDep && deps.length > 0) {
        currentDep = deps[0];
        setSelectedDeployment(deps[0]);
      }


      const metrics = await api.getRuntimeMetrics(currentDep ? currentDep.id : undefined);
      setMetricsSummary(metrics);

      if (currentDep) {
        const assuranceData = await api.getDeploymentAssurance(currentDep.id);
        if (assuranceData) {
          setFindings(assuranceData.findings || []);
          setPredictionReport(assuranceData.prediction_vs_observed || null);
        }

        if (currentDep.change_id) {
          const proof = await api.getChangeRuntimeProof(currentDep.change_id, currentDep.id);
          setExtendedProof(proof);
        }
      }
    } catch (err) {
      console.error('Failed to load runtime assurance data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(), 8000);
    return () => clearInterval(interval);
  }, [selectedDeployment?.id]);

  const handleSimulateTelemetry = async (scenario: 'healthy' | 'regression') => {
    if (!selectedDeployment) return;
    setSimulating(true);
    try {
      if (scenario === 'healthy') {
        // Record healthy baseline and observation
        await api.recordBaseline(selectedDeployment.id, {
          service_name: 'auth-service',
          endpoint: '/api/v1/auth/login',
          request_rate: 45.0,
          error_rate: 0.4,
          p50_latency_ms: 32.0,
          p95_latency_ms: 85.0,
          p99_latency_ms: 140.0,
        });

        await api.recordObservation(selectedDeployment.id, {
          service_name: 'auth-service',
          endpoint: '/api/v1/auth/login',
          request_count: 500,
          error_count: 2,
          error_rate: 0.4,
          p50_latency_ms: 34.0,
          p95_latency_ms: 88.0,
          p99_latency_ms: 145.0,
          status_2xx_count: 498,
          status_4xx_count: 2,
          status_5xx_count: 0,
        });

        await api.recordObservation(selectedDeployment.id, {
          service_name: 'user-service',
          endpoint: '/api/v1/users/me',
          request_count: 350,
          error_count: 1,
          error_rate: 0.28,
          p50_latency_ms: 22.0,
          p95_latency_ms: 60.0,
          p99_latency_ms: 110.0,
          status_2xx_count: 349,
          status_4xx_count: 1,
          status_5xx_count: 0,
        });
      } else {
        // Record regression scenario
        await api.recordBaseline(selectedDeployment.id, {
          service_name: 'auth-service',
          endpoint: '/api/v1/auth/authorize',
          request_rate: 50.0,
          error_rate: 0.5,
          p50_latency_ms: 40.0,
          p95_latency_ms: 110.0,
          p99_latency_ms: 200.0,
        });

        await api.recordObservation(selectedDeployment.id, {
          service_name: 'auth-service',
          endpoint: '/api/v1/auth/authorize',
          request_count: 620,
          error_count: 48,
          error_rate: 7.74,
          p50_latency_ms: 140.0,
          p95_latency_ms: 485.0,
          p99_latency_ms: 920.0,
          status_2xx_count: 572,
          status_4xx_count: 12,
          status_5xx_count: 36,
        });
      }

      await loadData();
    } catch (e) {
      console.error('Simulation error:', e);
    } finally {
      setSimulating(false);
    }
  };

  const handleRunCiCheck = async () => {
    if (!selectedDeployment) return;
    try {
      const res = await api.runCICheck({
        change_id: selectedDeployment.change_id,
        commit_sha: selectedDeployment.commit_sha,
        fail_on_warn: false,
        publish_github_check: true,
      });
      setCiCheckResult(res);
      setActiveTab('ci_gate');
    } catch (e) {
      console.error('CI check error:', e);
    }
  };

  if (loading && deployments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
        <p className="text-sm text-slate-400 font-mono">Loading runtime telemetry & assurance models...</p>
      </div>
    );
  }


  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">

        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-lg shadow-cyan-500/5">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
                Runtime Assurance & Observability
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-mono font-medium border border-cyan-500/30">
                  Phase 4
                </span>
              </h1>
              <p className="text-sm text-slate-400 mt-0.5">
                Pre-deployment policy gates & live post-deployment telemetry verification
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => loadData()}
            disabled={refreshing}
            className="flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-slate-300 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 rounded-lg transition-all"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-cyan-400' : ''}`} />
            Refresh Telemetry
          </button>
          <button
            onClick={handleRunCiCheck}
            className="flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/20 rounded-lg transition-all"
          >
            <Terminal className="w-4 h-4" />
            Run CI Gate Check
          </button>
        </div>
      </div>

      {/* Deployment Selector & Telemetry Simulator Bar */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Server className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Deployment:</span>
          {deployments.length > 0 ? (
            <select
              value={selectedDeployment?.id || ''}
              onChange={(e) => {
                const dep = deployments.find((d) => d.id === e.target.value);
                if (dep) setSelectedDeployment(dep);
              }}
              className="bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-1.5 focus:ring-1 focus:ring-cyan-500"
            >
              {deployments.map((d) => (
                <option key={d.id} value={d.id}>
                  [{d.environment.toUpperCase()}] {d.commit_sha.slice(0, 8)} - {d.status} ({new Date(d.deployed_at).toLocaleTimeString()})
                </option>
              ))}
            </select>
          ) : (
            <span className="text-sm text-slate-500 italic">No deployments found</span>
          )}
        </div>

        {selectedDeployment && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 mr-1">Inject Mock Telemetry:</span>
            <button
              onClick={() => handleSimulateTelemetry('healthy')}
              disabled={simulating}
              className="px-3 py-1 text-xs font-medium text-emerald-300 bg-emerald-950/60 hover:bg-emerald-900/60 border border-emerald-700/50 rounded-md transition-all"
            >
              + Healthy Traffic
            </button>
            <button
              onClick={() => handleSimulateTelemetry('regression')}
              disabled={simulating}
              className="px-3 py-1 text-xs font-medium text-rose-300 bg-rose-950/60 hover:bg-rose-900/60 border border-rose-700/50 rounded-md transition-all"
            >
              + Error Regression
            </button>
          </div>
        )}
      </div>

      {/* Metrics KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>TOTAL OBSERVED REQUESTS</span>
            <Zap className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">
            {metricsSummary ? metricsSummary.total_requests.toLocaleString() : '0'}
          </div>
          <p className="text-xs text-slate-500 mt-1">Live telemetry sample window</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>AGGREGATE ERROR RATE</span>
            <TrendingUp className="w-4 h-4 text-amber-400" />
          </div>
          <div
            className={`text-2xl font-bold ${
              metricsSummary && metricsSummary.overall_error_rate > 2.0 ? 'text-rose-400' : 'text-emerald-400'
            }`}
          >
            {metricsSummary ? `${metricsSummary.overall_error_rate.toFixed(2)}%` : '0.00%'}
          </div>
          <p className="text-xs text-slate-500 mt-1">Threshold: &lt; 2.0%</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>AVG P95 LATENCY</span>
            <Clock className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">
            {metricsSummary ? `${metricsSummary.avg_p95_latency_ms.toFixed(1)} ms` : '0.0 ms'}
          </div>
          <p className="text-xs text-slate-500 mt-1">SLA limit: 350 ms</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>RUNTIME VERDICT</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-bold">
            {extendedProof?.runtime_decision === 'RUNTIME_VERIFIED' && (
              <span className="text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-5 h-5" /> VERIFIED
              </span>
            )}
            {extendedProof?.runtime_decision === 'RUNTIME_REGRESSION' && (
              <span className="text-rose-400 flex items-center gap-1.5">
                <XCircle className="w-5 h-5" /> REGRESSION
              </span>
            )}
            {extendedProof?.runtime_decision === 'RUNTIME_WARNING' && (
              <span className="text-amber-400 flex items-center gap-1.5">
                <AlertTriangle className="w-5 h-5" /> WARNING
              </span>
            )}
            {(!extendedProof || extendedProof.runtime_decision === 'INSUFFICIENT_RUNTIME_EVIDENCE') && (
              <span className="text-slate-400 text-sm">NO TELEMETRY</span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">Phase 4 deterministic decision</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-800 flex gap-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'overview'
              ? 'border-cyan-500 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          Service Health & Telemetry
        </button>

        <button
          onClick={() => setActiveTab('predictions')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'predictions'
              ? 'border-cyan-500 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="w-4 h-4" />
          Predicted vs Actual Traffic
        </button>

        <button
          onClick={() => setActiveTab('findings')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'findings'
              ? 'border-cyan-500 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          Runtime Regression Findings ({findings.length})
        </button>

        <button
          onClick={() => setActiveTab('ci_gate')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'ci_gate'
              ? 'border-cyan-500 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Terminal className="w-4 h-4" />
          CI/CD Gate & GitHub Check
        </button>

        <button
          onClick={() => setActiveTab('proof')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'proof'
              ? 'border-cyan-500 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileCheck className="w-4 h-4" />
          Extended Change Proof
        </button>
      </div>

      {/* Tab 1: Service Health & Telemetry */}
      {activeTab === 'overview' && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
          <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <Server className="w-4 h-4 text-cyan-400" />
            Monitored Microservices in Staging / Runtime
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Service</th>
                  <th className="py-3 px-4">Health Status</th>
                  <th className="py-3 px-4">Requests Observed</th>
                  <th className="py-3 px-4">Error Rate</th>
                  <th className="py-3 px-4">p95 Latency</th>
                  <th className="py-3 px-4">Last Seen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {metricsSummary && metricsSummary.services.length > 0 ? (
                  metricsSummary.services.map((s, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-semibold text-slate-100 font-sans">{s.service_name}</td>
                      <td className="py-3 px-4 font-sans">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            s.status === 'HEALTHY'
                              ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/50'
                              : s.status === 'DEGRADED'
                              ? 'bg-amber-950 text-amber-300 border border-amber-800/50'
                              : 'bg-rose-950 text-rose-300 border border-rose-800/50'
                          }`}
                        >
                          {s.status}
                        </span>
                      </td>
                      <td className="py-3 px-4">{s.request_rate.toLocaleString()}</td>
                      <td className="py-3 px-4">
                        <span className={s.error_rate > 2.0 ? 'text-rose-400 font-bold' : 'text-emerald-400'}>
                          {s.error_rate}%
                        </span>
                      </td>
                      <td className="py-3 px-4">{s.p95_latency_ms} ms</td>
                      <td className="py-3 px-4 text-slate-400">
                        {s.last_seen ? new Date(s.last_seen).toLocaleTimeString() : 'N/A'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500 font-sans text-sm">
                      No runtime telemetry recorded yet. Click "+ Healthy Traffic" or "+ Error Regression" above to inject test traffic.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Predicted vs Actual Traffic */}
      {activeTab === 'predictions' && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              Phase 2 Graph Predictions vs Live Telemetry Correlation
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Verifies if services predicted statically to be in the change blast radius actually experienced runtime load.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Service</th>
                  <th className="py-3 px-4">Graph Predicted Impact</th>
                  <th className="py-3 px-4">Observed Traffic</th>
                  <th className="py-3 px-4">Observed Error Rate</th>
                  <th className="py-3 px-4">Correlation Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs font-mono">
                {predictionReport && predictionReport.components.length > 0 ? (
                  predictionReport.components.map((c, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-sans font-semibold text-slate-100">{c.service_name}</td>
                      <td className="py-3 px-4 font-sans">
                        {c.predicted_impacted ? (
                          <span className="text-amber-400 font-medium">YES (In Blast Radius)</span>
                        ) : (
                          <span className="text-slate-500">NO</span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-sans">
                        {c.observed_traffic ? (
                          <span className="text-emerald-400 font-medium">ACTIVE TRAFFIC</span>
                        ) : (
                          <span className="text-slate-500">NO TRAFFIC</span>
                        )}
                      </td>
                      <td className="py-3 px-4">{c.observed_error_rate}%</td>
                      <td className="py-3 px-4 font-sans">
                        <span
                          className={`px-2.5 py-0.5 rounded text-xs font-bold ${
                            c.status === 'MATCH'
                              ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/40'
                              : c.status === 'REGRESSION'
                              ? 'bg-rose-950 text-rose-300 border border-rose-800/40'
                              : 'bg-amber-950 text-amber-300 border border-amber-800/40'
                          }`}
                        >
                          {c.status}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500 font-sans text-sm">
                      No prediction-versus-observation comparison generated yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Runtime Regression Findings */}
      {activeTab === 'findings' && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
          <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Deterministic Runtime Findings & Regressions
          </h2>

          <div className="space-y-3">
            {findings.length > 0 ? (
              findings.map((f) => (
                <div
                  key={f.id}
                  className={`p-4 rounded-xl border ${
                    f.severity === 'CRITICAL'
                      ? 'bg-rose-950/20 border-rose-800/60 text-rose-200'
                      : f.severity === 'HIGH'
                      ? 'bg-amber-950/20 border-amber-800/60 text-amber-200'
                      : 'bg-slate-900/80 border-slate-800 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs font-bold px-2 py-0.5 rounded uppercase ${
                          f.severity === 'CRITICAL'
                            ? 'bg-rose-600 text-white'
                            : f.severity === 'HIGH'
                            ? 'bg-amber-600 text-white'
                            : 'bg-slate-700 text-slate-200'
                        }`}
                      >
                        {f.finding_type}
                      </span>
                      <span className="text-sm font-semibold text-slate-100">
                        {f.service_name} &bull; {f.endpoint_or_metric}
                      </span>
                    </div>
                    <span className="text-xs text-slate-400 font-mono">
                      Confidence: {(f.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  <p className="text-sm text-slate-300 font-sans leading-relaxed">{f.evidence}</p>

                  <div className="mt-3 pt-2 border-t border-slate-800/50 flex flex-wrap gap-4 text-xs font-mono text-slate-400">
                    <span>Baseline: {f.baseline_value !== null ? `${f.baseline_value}` : 'N/A'}</span>
                    <span>Observed: {f.observed_value !== null ? `${f.observed_value}` : 'N/A'}</span>
                    <span>Threshold: {f.threshold_value !== null ? `${f.threshold_value}` : 'N/A'}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-slate-500 text-sm">
                No runtime regression findings detected. Telemetry is healthy.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 4: CI/CD Gate & GitHub Check */}
      {activeTab === 'ci_gate' && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-indigo-400" />
              ProofMesh Machine-Readable CI Gate Evaluation
            </h2>

            {ciCheckResult ? (
              <div className="space-y-4 font-mono text-xs">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
                    <div className="text-slate-500 mb-1 font-sans">GATE DECISION</div>
                    <div
                      className={`text-lg font-bold ${
                        ciCheckResult.gate_decision === 'PASS'
                          ? 'text-emerald-400'
                          : ciCheckResult.gate_decision === 'WARN'
                          ? 'text-amber-400'
                          : 'text-rose-400'
                      }`}
                    >
                      {ciCheckResult.gate_decision}
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
                    <div className="text-slate-500 mb-1 font-sans">PROCESS EXIT CODE</div>
                    <div className="text-lg font-bold text-slate-100">{ciCheckResult.exit_code}</div>
                  </div>

                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
                    <div className="text-slate-500 mb-1 font-sans">RISK LEVEL</div>
                    <div className="text-lg font-bold text-slate-100">{ciCheckResult.risk_level}</div>
                  </div>

                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
                    <div className="text-slate-500 mb-1 font-sans">GITHUB CHECK RUN</div>
                    <div className="text-xs text-indigo-400 font-semibold truncate">
                      {ciCheckResult.github_check_id || 'LOCAL_RUN'}
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
                  <div className="text-slate-400 font-sans font-semibold mb-2">
                    GitHub PR Status / Check Run Markdown Payload:
                  </div>
                  <pre className="text-slate-300 font-mono text-xs whitespace-pre-wrap bg-slate-900/90 p-3 rounded border border-slate-800">
                    {ciCheckResult.policy_summary.markdown_summary}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500">
                Click "Run CI Gate Check" at the top right to simulate GitHub Actions pipeline evaluation.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 5: Extended Change Proof */}
      {activeTab === 'proof' && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-semibold text-slate-100 font-sans flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-emerald-400" />
                Extended Change Proof Artifact (v2.0.0-phase4)
              </h2>
              <p className="text-xs text-slate-400 font-sans mt-0.5">
                Complete cryptographically auditable chain linking PR, Impact, Assurance, CI Gate, and Post-Deployment Telemetry.
              </p>
            </div>
            {extendedProof && (
              <span className="px-3 py-1 rounded bg-emerald-950 border border-emerald-700/50 text-emerald-300 font-sans font-bold">
                {extendedProof.final_combined_verdict}
              </span>
            )}
          </div>

          {extendedProof ? (
            <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-slate-300 overflow-x-auto max-h-[500px]">
              {JSON.stringify(extendedProof.auditable_record, null, 2)}
            </pre>
          ) : (
            <div className="text-center py-8 text-slate-500 font-sans">
              No Extended Change Proof available for active deployment.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
