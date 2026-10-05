import React, { useEffect, useState } from 'react';
import {
  Building2,
  Users,
  Server,
  GitBranch,
  AlertTriangle,
  Bot,
  Shield,
  Layers,
  RefreshCw,
  Plus,
  ArrowRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { EnterpriseOverview as EnterpriseOverviewType, Team, EnterpriseService } from '../types';

export const EnterpriseOverview: React.FC = () => {
  const [overview, setOverview] = useState<EnterpriseOverviewType | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [services, setServices] = useState<EnterpriseService[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTeamModal, setShowTeamModal] = useState(false);
  const [showServiceModal, setShowServiceModal] = useState(false);

  // Form states
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamSlug, setNewTeamSlug] = useState('');
  const [newTeamDesc, setNewTeamDesc] = useState('');
  const [newServiceName, setNewServiceName] = useState('');
  const [newServiceCrit, setNewServiceCrit] = useState('MEDIUM');
  const [newServiceTier, setNewServiceTier] = useState(2);
  const [newServiceDesc, setNewServiceDesc] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [overviewData, teamsData, servicesData] = await Promise.all([
        api.getEnterpriseOverview().catch(() => null),
        api.listTeams().catch(() => []),
        api.listServices().catch(() => []),
      ]);
      setOverview(overviewData);
      setTeams(teamsData);
      setServices(servicesData);
    } catch (err: any) {
      setError(err.message || 'Failed to load enterprise data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTeamName.trim() || !newTeamSlug.trim()) return;
    try {
      // Use default org if available or placeholder
      const orgId = teams[0]?.organization_id || '00000000-0000-0000-0000-000000000001';
      await api.createTeam({
        organization_id: orgId,
        name: newTeamName,
        slug: newTeamSlug,
        description: newTeamDesc,
      });
      setShowTeamModal(false);
      setNewTeamName('');
      setNewTeamSlug('');
      setNewTeamDesc('');
      loadData();
    } catch (err: any) {
      alert(`Failed to create team: ${err.message}`);
    }
  };

  const handleCreateService = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newServiceName.trim()) return;
    try {
      const orgId = services[0]?.organization_id || teams[0]?.organization_id || '00000000-0000-0000-0000-000000000001';
      await api.createService({
        organization_id: orgId,
        name: newServiceName,
        criticality: newServiceCrit,
        tier: Number(newServiceTier),
        description: newServiceDesc,
      });
      setShowServiceModal(false);
      setNewServiceName('');
      setNewServiceDesc('');
      loadData();
    } catch (err: any) {
      alert(`Failed to create service: ${err.message}`);
    }
  };

  const criticalityColors: Record<string, string> = {
    CRITICAL: 'bg-rose-500/20 text-rose-400 border-rose-500/40',
    HIGH: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
    MEDIUM: 'bg-sky-500/20 text-sky-400 border-sky-500/40',
    LOW: 'bg-slate-500/20 text-slate-400 border-slate-500/40',
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-wider mb-1">
            <Building2 className="w-3.5 h-3.5" />
            Phase 5 Enterprise Scale
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Enterprise Overview</h1>
          <p className="text-sm text-slate-400 mt-1">
            Hierarchical organizational visibility, cross-repository topologies, and microservice assurance metrics.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <Link
            to="/enterprise/graph"
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white rounded-lg shadow-sm shadow-sky-600/30 transition-colors"
          >
            <Layers className="w-3.5 h-3.5" />
            Enterprise Graph
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-200 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-5 bg-slate-900/80 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>Organizations & Teams</span>
            <Building2 className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {overview?.total_organizations ?? 1}
            <span className="text-slate-500 text-base font-normal ml-1">orgs</span> / {overview?.total_teams ?? teams.length}
            <span className="text-slate-500 text-base font-normal ml-1">teams</span>
          </div>
        </div>

        <div className="p-5 bg-slate-900/80 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>Microservices & Tier 1</span>
            <Server className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {overview?.total_services ?? services.length}
            <span className="text-slate-500 text-base font-normal ml-1">services</span> / {overview?.critical_services_count ?? services.filter(s => s.criticality === 'CRITICAL').length}
            <span className="text-rose-400 text-xs font-normal ml-1">crit</span>
          </div>
        </div>

        <div className="p-5 bg-slate-900/80 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>Cross-Repo Dependencies</span>
            <GitBranch className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {overview?.total_cross_repo_deps ?? 0}
            <span className="text-slate-500 text-sm font-normal ml-1">links</span>
          </div>
        </div>

        <div className="p-5 bg-slate-900/80 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>Active Agents & Incidents</span>
            <Bot className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {overview?.active_agents_count ?? 0}
            <span className="text-slate-500 text-base font-normal ml-1">agents</span> / {overview?.active_incidents_count ?? 0}
            <span className="text-amber-400 text-xs font-normal ml-1">incidents</span>
          </div>
        </div>
      </div>

      {/* Main Content Grid: Teams & Services */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Teams Section */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-cyan-400" />
              <h2 className="text-base font-semibold text-white">Engineering Teams</h2>
            </div>
            <button
              onClick={() => setShowTeamModal(true)}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 rounded-md transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Team
            </button>
          </div>

          {teams.length === 0 ? (
            <div className="p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-lg text-sm">
              No engineering teams registered yet. Click &quot;Add Team&quot; to define team boundaries.
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
              {teams.map((team) => (
                <div
                  key={team.id}
                  className="p-3.5 bg-slate-950/70 border border-slate-800/80 rounded-lg flex items-center justify-between hover:border-slate-700 transition-colors"
                >
                  <div>
                    <h3 className="text-sm font-semibold text-slate-200">{team.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs font-mono text-cyan-400 bg-cyan-950/50 px-1.5 py-0.5 rounded border border-cyan-900/60">
                        @{team.slug}
                      </span>
                      {team.description && (
                        <span className="text-xs text-slate-400 truncate max-w-xs">{team.description}</span>
                      )}
                    </div>
                  </div>
                  <span className="text-[11px] font-mono text-slate-500">
                    {new Date(team.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Services Section */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-indigo-400" />
              <h2 className="text-base font-semibold text-white">Registered Microservices</h2>
            </div>
            <button
              onClick={() => setShowServiceModal(true)}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 rounded-md transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Service
            </button>
          </div>

          {services.length === 0 ? (
            <div className="p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-lg text-sm">
              No services registered yet. Click &quot;Add Service&quot; to define critical service tiers.
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
              {services.map((svc) => (
                <div
                  key={svc.id}
                  className="p-3.5 bg-slate-950/70 border border-slate-800/80 rounded-lg flex items-center justify-between hover:border-slate-700 transition-colors"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-slate-200 truncate">{svc.name}</h3>
                      <span
                        className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                          criticalityColors[svc.criticality] || criticalityColors.MEDIUM
                        }`}
                      >
                        {svc.criticality}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">
                        Tier {svc.tier}
                      </span>
                    </div>
                    {svc.description && (
                      <p className="text-xs text-slate-400 mt-1 truncate">{svc.description}</p>
                    )}
                  </div>
                  <Link
                    to={`/enterprise/graph`}
                    className="p-1.5 text-slate-400 hover:text-cyan-300 hover:bg-slate-800 rounded transition-colors"
                    title="View in Enterprise Graph"
                  >
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to="/agents"
          className="p-5 bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 rounded-xl hover:border-sky-500/50 transition-all group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 rounded-lg bg-sky-950/80 border border-sky-800/60 text-sky-400">
              <Bot className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-sky-400 transition-colors" />
          </div>
          <h3 className="text-sm font-semibold text-white group-hover:text-sky-300">Agent Center</h3>
          <p className="text-xs text-slate-400 mt-1">
            Governed autonomous agents, autonomy levels 1–5, and execution budget policies.
          </p>
        </Link>

        <Link
          to="/approvals"
          className="p-5 bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 rounded-xl hover:border-amber-500/50 transition-all group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 rounded-lg bg-amber-950/80 border border-amber-800/60 text-amber-400">
              <Shield className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-amber-400 transition-colors" />
          </div>
          <h3 className="text-sm font-semibold text-white group-hover:text-amber-300">Approval Center</h3>
          <p className="text-xs text-slate-400 mt-1">
            Human-in-the-loop gates for high-risk agent mutations and remediation plans.
          </p>
        </Link>

        <Link
          to="/evidence"
          className="p-5 bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 rounded-xl hover:border-indigo-500/50 transition-all group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 rounded-lg bg-indigo-950/80 border border-indigo-800/60 text-indigo-400">
              <Layers className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 transition-colors" />
          </div>
          <h3 className="text-sm font-semibold text-white group-hover:text-indigo-300">Historical Evidence</h3>
          <p className="text-xs text-slate-400 mt-1">
            TF-IDF cosine similarity search over prior change proofs and incidents.
          </p>
        </Link>
      </div>

      {/* Create Team Modal */}
      {showTeamModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-white">Create Engineering Team</h3>
            <form onSubmit={handleCreateTeam} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Team Name</label>
                <input
                  type="text"
                  required
                  value={newTeamName}
                  onChange={(e) => setNewTeamName(e.target.value)}
                  placeholder="e.g. Core Platform"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Team Slug</label>
                <input
                  type="text"
                  required
                  value={newTeamSlug}
                  onChange={(e) => setNewTeamSlug(e.target.value)}
                  placeholder="e.g. core-platform"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
                <textarea
                  value={newTeamDesc}
                  onChange={(e) => setNewTeamDesc(e.target.value)}
                  placeholder="Responsibilities and ownership domain"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-sky-500 h-20"
                />
              </div>
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowTeamModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white rounded-lg"
                >
                  Save Team
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Service Modal */}
      {showServiceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-white">Register Microservice</h3>
            <form onSubmit={handleCreateService} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Service Name</label>
                <input
                  type="text"
                  required
                  value={newServiceName}
                  onChange={(e) => setNewServiceName(e.target.value)}
                  placeholder="e.g. auth-service"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Criticality</label>
                  <select
                    value={newServiceCrit}
                    onChange={(e) => setNewServiceCrit(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Architecture Tier</label>
                  <input
                    type="number"
                    min="1"
                    max="4"
                    value={newServiceTier}
                    onChange={(e) => setNewServiceTier(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
                <textarea
                  value={newServiceDesc}
                  onChange={(e) => setNewServiceDesc(e.target.value)}
                  placeholder="Service domain, SLA expectations, and dependencies"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500 h-20"
                />
              </div>
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowServiceModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg"
                >
                  Register Service
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
