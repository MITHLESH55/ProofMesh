import React, { useEffect, useState } from 'react';
import {
  Layers,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  AlertTriangle,
  Activity,
  Info,
} from 'lucide-react';
import { api } from '../services/api';
import { EnterpriseGraphData, EnterpriseGraphNode } from '../types';

export const EnterpriseGraph: React.FC = () => {
  const [graphData, setGraphData] = useState<EnterpriseGraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<EnterpriseGraphNode | null>(null);
  const [selectedImpact, setSelectedImpact] = useState<any | null>(null);
  const [impactLoading, setImpactLoading] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [filterType, setFilterType] = useState<string>('ALL');

  const defaultOrgId = '00000000-0000-0000-0000-000000000001';

  const loadGraph = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getEnterpriseGraph(defaultOrgId);
      setGraphData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch enterprise graph');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, []);

  const handleNodeClick = async (node: EnterpriseGraphNode) => {
    setSelectedNode(node);
    if (node.type === 'REPOSITORY') {
      try {
        setImpactLoading(true);
        const impact = await api.getCrossRepoImpact(defaultOrgId, node.id);
        setSelectedImpact(impact);
      } catch {
        setSelectedImpact(null);
      } finally {
        setImpactLoading(false);
      }
    } else {
      setSelectedImpact(null);
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const getNodeColor = (type: string, criticality?: string | null) => {
    if (criticality === 'CRITICAL') return { bg: '#881337', stroke: '#f43f5e', text: '#ffe4e6' };
    if (criticality === 'HIGH') return { bg: '#78350f', stroke: '#f59e0b', text: '#fef3c7' };
    switch (type) {
      case 'ORGANIZATION':
        return { bg: '#083344', stroke: '#06b6d4', text: '#cffafe' };
      case 'TEAM':
        return { bg: '#1e1b4b', stroke: '#6366f1', text: '#e0e7ff' };
      case 'REPOSITORY':
        return { bg: '#064e3b', stroke: '#10b981', text: '#d1fae5' };
      case 'SERVICE':
        return { bg: '#312e81', stroke: '#818cf8', text: '#e0e7ff' };
      default:
        return { bg: '#1e293b', stroke: '#64748b', text: '#f1f5f9' };
    }
  };

  // Node position calculation in circular/hierarchical layout
  const filteredNodes = graphData?.nodes.filter(
    (n) => filterType === 'ALL' || n.type === filterType
  ) || [];

  const nodePositions = React.useMemo(() => {
    const map = new Map<string, { x: number; y: number }>();
    if (!graphData) return map;

    const orgNodes = graphData.nodes.filter((n) => n.type === 'ORGANIZATION');
    const teamNodes = graphData.nodes.filter((n) => n.type === 'TEAM');
    const repoNodes = graphData.nodes.filter((n) => n.type === 'REPOSITORY');
    const serviceNodes = graphData.nodes.filter((n) => n.type === 'SERVICE');
    const otherNodes = graphData.nodes.filter(
      (n) => !['ORGANIZATION', 'TEAM', 'REPOSITORY', 'SERVICE'].includes(n.type)
    );

    // Place Org in center top
    orgNodes.forEach((n, idx) => {
      map.set(n.id, { x: 450 + idx * 200, y: 80 });
    });

    // Teams on second row
    teamNodes.forEach((n, idx) => {
      const spacing = 700 / (teamNodes.length + 1);
      map.set(n.id, { x: 150 + (idx + 1) * spacing, y: 220 });
    });

    // Repositories on third row
    repoNodes.forEach((n, idx) => {
      const spacing = 800 / (repoNodes.length + 1);
      map.set(n.id, { x: 100 + (idx + 1) * spacing, y: 380 });
    });

    // Services on fourth row
    serviceNodes.forEach((n, idx) => {
      const spacing = 800 / (serviceNodes.length + 1);
      map.set(n.id, { x: 100 + (idx + 1) * spacing, y: 540 });
    });

    // Others at bottom
    otherNodes.forEach((n, idx) => {
      map.set(n.id, { x: 150 + idx * 150, y: 680 });
    });

    return map;
  }, [graphData]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-wider mb-1">
            <Layers className="w-3.5 h-3.5" />
            Enterprise Architecture Graph
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Cross-Repository Topology</h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time interactive dependency mapping across organizations, teams, repositories, and critical services.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 text-slate-200 rounded-lg focus:outline-none"
          >
            <option value="ALL">All Entity Types</option>
            <option value="ORGANIZATION">Organizations</option>
            <option value="TEAM">Teams</option>
            <option value="REPOSITORY">Repositories</option>
            <option value="SERVICE">Services</option>
          </select>
          <button
            onClick={loadGraph}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-200 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Graph Viewport + Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Canvas Area */}
        <div className="lg:col-span-3 bg-slate-950 border border-slate-800 rounded-xl overflow-hidden relative h-[650px] select-none">
          {/* Controls Overlay */}
          <div className="absolute top-4 right-4 z-10 flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 rounded-lg p-1.5 backdrop-blur">
            <button
              onClick={() => setZoom((z) => Math.min(z + 0.2, 2.5))}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={() => setZoom((z) => Math.max(z - 0.2, 0.4))}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              onClick={() => {
                setZoom(1);
                setPan({ x: 0, y: 0 });
              }}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
              title="Reset View"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
            <span className="text-[11px] font-mono text-slate-400 px-2">
              {Math.round(zoom * 100)}%
            </span>
          </div>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 z-10 flex flex-wrap gap-3 bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono backdrop-blur">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-slate-300">Org</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-400" />
              <span className="text-slate-300">Team</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
              <span className="text-slate-300">Repo</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
              <span className="text-slate-300">Service</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
              <span className="text-rose-300">Critical</span>
            </div>
          </div>

          {/* SVG Canvas */}
          <svg
            className="w-full h-full cursor-grab active:cursor-grabbing"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
          >
            <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
              <defs>
                <marker
                  id="arrow"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
                </marker>
                <marker
                  id="arrow-impact"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" />
                </marker>
              </defs>

              {/* Render Edges */}
              {graphData?.edges.map((edge, idx) => {
                const sourcePos = nodePositions.get(edge.source);
                const targetPos = nodePositions.get(edge.target);
                if (!sourcePos || !targetPos) return null;

                const isImpactEdge =
                  selectedImpact &&
                  (selectedImpact.impacted_repositories?.includes(edge.target) ||
                    edge.source === selectedNode?.id);

                return (
                  <line
                    key={`edge-${idx}`}
                    x1={sourcePos.x}
                    y1={sourcePos.y}
                    x2={targetPos.x}
                    y2={targetPos.y}
                    stroke={isImpactEdge ? '#ef4444' : '#334155'}
                    strokeWidth={isImpactEdge ? 2.5 : 1.5}
                    strokeDasharray={edge.type === 'DEPENDS_ON' ? '4 2' : undefined}
                    markerEnd={isImpactEdge ? 'url(#arrow-impact)' : 'url(#arrow)'}
                  />
                );
              })}

              {/* Render Nodes */}
              {filteredNodes.map((node) => {
                const pos = nodePositions.get(node.id) || { x: 300, y: 300 };
                const colors = getNodeColor(node.type, node.criticality);
                const isSelected = selectedNode?.id === node.id;
                const isImpacted =
                  selectedImpact?.impacted_repositories?.includes(node.id);

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    onClick={() => handleNodeClick(node)}
                    className="cursor-pointer transition-transform hover:scale-105"
                  >
                    <circle
                      r={node.type === 'ORGANIZATION' ? 32 : 24}
                      fill={colors.bg}
                      stroke={
                        isSelected
                          ? '#38bdf8'
                          : isImpacted
                          ? '#ef4444'
                          : colors.stroke
                      }
                      strokeWidth={isSelected || isImpacted ? 3 : 1.5}
                      className="filter drop-shadow"
                    />
                    <text
                      y={4}
                      textAnchor="middle"
                      fill={colors.text}
                      fontSize={node.type === 'ORGANIZATION' ? 12 : 10}
                      fontFamily="monospace"
                      fontWeight="bold"
                      pointerEvents="none"
                    >
                      {node.label.length > 10 ? `${node.label.slice(0, 9)}…` : node.label}
                    </text>
                    <text
                      y={node.type === 'ORGANIZATION' ? 48 : 38}
                      textAnchor="middle"
                      fill="#94a3b8"
                      fontSize={9}
                      fontFamily="monospace"
                      pointerEvents="none"
                    >
                      {node.type}
                    </text>
                  </g>
                );
              })}
            </g>
          </svg>
        </div>

        {/* Inspector Sidebar */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-6">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <Info className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold text-white">Entity Inspector</h2>
          </div>

          {selectedNode ? (
            <div className="space-y-4">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
                  Selected Entity
                </span>
                <h3 className="text-base font-bold text-white mt-0.5">{selectedNode.label}</h3>
                <div className="flex items-center gap-2 mt-1.5">
                  <span className="text-xs font-mono px-2 py-0.5 bg-slate-800 text-cyan-400 rounded border border-slate-700">
                    {selectedNode.type}
                  </span>
                  {selectedNode.criticality && (
                    <span className="text-xs font-mono font-bold px-2 py-0.5 bg-rose-950 text-rose-400 rounded border border-rose-800">
                      {selectedNode.criticality}
                    </span>
                  )}
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-800">
                <span className="text-xs font-medium text-slate-400">Metadata</span>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs font-mono space-y-1.5">
                  <div>
                    <span className="text-slate-500">ID: </span>
                    <span className="text-slate-300 break-all">{selectedNode.id}</span>
                  </div>
                  {Object.entries(selectedNode.metadata || {}).map(([k, v]) => (
                    <div key={k}>
                      <span className="text-slate-500">{k}: </span>
                      <span className="text-slate-300">{String(v)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cross-Repo Blast Radius Section */}
              {selectedNode.type === 'REPOSITORY' && (
                <div className="space-y-3 pt-3 border-t border-slate-800">
                  <div className="flex items-center gap-2 text-rose-400">
                    <Activity className="w-4 h-4" />
                    <span className="text-xs font-bold uppercase tracking-wider">
                      Cross-Repo Blast Radius
                    </span>
                  </div>

                  {impactLoading ? (
                    <div className="flex items-center gap-2 text-xs text-slate-400 py-3">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                      Computing blast radius...
                    </div>
                  ) : selectedImpact ? (
                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Impacted Repositories:</span>
                        <span className="font-mono font-bold text-rose-400">
                          {selectedImpact.impacted_repositories?.length ?? 0}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Impacted Services:</span>
                        <span className="font-mono font-bold text-amber-400">
                          {selectedImpact.impacted_services?.length ?? 0}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Max Dependency Depth:</span>
                        <span className="font-mono text-cyan-400">
                          {selectedImpact.max_depth ?? 1} hops
                        </span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500">No cross-repo impact detected.</p>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500 text-xs">
              Click any node in the graph to inspect relationships, criticality tier, and cross-repo blast radius.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
