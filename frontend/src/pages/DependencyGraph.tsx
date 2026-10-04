import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  GitBranch,
  Zap,
  FileCode2,
  AlertTriangle,
  Shield,
  Activity,
  Search,
  ChevronDown,
  RefreshCw,
  X,
  Info,
  ArrowRight,
  Code2,
  Boxes,
  Network,
} from 'lucide-react';
import { api } from '../services/api';
import type {
  GraphData,
  GraphNode,
  GraphEdge,
  GraphStats,
  ImpactAnalysisResult,
  ImpactedFile,
  Repository,
} from '../types';

// ─── Color Palette ──────────────────────────────────────────────────────────

const NODE_COLORS: Record<string, string> = {
  file: '#6366f1',
  function: '#22d3ee',
  class: '#f59e0b',
  default: '#94a3b8',
};

const LANGUAGE_COLORS: Record<string, string> = {
  python: '#3b82f6',
  javascript: '#fbbf24',
  typescript: '#818cf8',
  java: '#f97316',
  go: '#34d399',
  unknown: '#6b7280',
};

const EDGE_COLORS: Record<string, string> = {
  IMPORTS: '#6366f1',
  DEFINES: '#22d3ee',
  HAS_METHOD: '#f59e0b',
  CALLS: '#ec4899',
  default: '#475569',
};

const RISK_COLORS: Record<string, string> = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#f97316',
  critical: '#ef4444',
};

// ─── Force-Directed Graph (canvas-based) ────────────────────────────────────

interface ForceNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  fx?: number;
  fy?: number;
}

interface ForceEdge extends GraphEdge {
  sourceNode?: ForceNode;
  targetNode?: ForceNode;
}

function useForceGraph(
  nodes: GraphNode[],
  edges: GraphEdge[],
  width: number,
  height: number
) {
  const [forceNodes, setForceNodes] = useState<ForceNode[]>([]);
  const [forceEdges, setForceEdges] = useState<ForceEdge[]>([]);
  const animRef = useRef<number>(0);

  useEffect(() => {
    if (!nodes.length) return;

    // Initialize positions in a circle
    const n = nodes.length;
    const r = Math.min(width, height) * 0.35;
    const cx = width / 2;
    const cy = height / 2;

    const fNodes: ForceNode[] = nodes.map((node, i) => ({
      ...node,
      x: cx + r * Math.cos((2 * Math.PI * i) / n) + (Math.random() - 0.5) * 30,
      y: cy + r * Math.sin((2 * Math.PI * i) / n) + (Math.random() - 0.5) * 30,
      vx: 0,
      vy: 0,
    }));

    const nodeMap = new Map<string, ForceNode>(fNodes.map(n => [n.id, n]));

    const fEdges: ForceEdge[] = edges
      .map(e => ({
        ...e,
        sourceNode: nodeMap.get(e.source),
        targetNode: nodeMap.get(e.target),
      }))
      .filter(e => e.sourceNode && e.targetNode);

    let iteration = 0;
    const MAX_ITER = 300;

    const tick = () => {
      if (iteration >= MAX_ITER) return;
      iteration++;

      const alpha = Math.max(0.01, 1 - iteration / MAX_ITER);

      // Reset forces
      for (const node of fNodes) {
        if (node.fx !== undefined) { node.x = node.fx; node.y = node.fy!; continue; }
        node.vx *= 0.7;
        node.vy *= 0.7;

        // Center gravity
        node.vx += (cx - node.x) * 0.003 * alpha;
        node.vy += (cy - node.y) * 0.003 * alpha;
      }

      // Repulsion between all nodes
      for (let i = 0; i < fNodes.length; i++) {
        for (let j = i + 1; j < fNodes.length; j++) {
          const a = fNodes[i];
          const b = fNodes[j];
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (800 * alpha) / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          if (a.fx === undefined) { a.vx -= fx; a.vy -= fy; }
          if (b.fx === undefined) { b.vx += fx; b.vy += fy; }
        }
      }

      // Attraction along edges
      for (const edge of fEdges) {
        const a = edge.sourceNode!;
        const b = edge.targetNode!;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const targetDist = 120;
        const force = ((dist - targetDist) / dist) * 0.15 * alpha;
        const fx = dx * force;
        const fy = dy * force;
        if (a.fx === undefined) { a.vx += fx; a.vy += fy; }
        if (b.fx === undefined) { b.vx -= fx; b.vy -= fy; }
      }

      // Integrate positions
      for (const node of fNodes) {
        if (node.fx !== undefined) continue;
        node.x = Math.max(40, Math.min(width - 40, node.x + node.vx));
        node.y = Math.max(40, Math.min(height - 40, node.y + node.vy));
      }

      setForceNodes([...fNodes]);
      setForceEdges([...fEdges]);

      if (iteration < MAX_ITER) {
        animRef.current = requestAnimationFrame(tick);
      }
    };

    animRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animRef.current);
  }, [nodes, edges, width, height]);

  return { forceNodes, forceEdges };
}

// ─── Canvas Graph Renderer ──────────────────────────────────────────────────

interface CanvasGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNode: GraphNode | null;
  onNodeClick: (node: GraphNode) => void;
  width: number;
  height: number;
}

const CanvasGraph: React.FC<CanvasGraphProps> = ({
  nodes,
  edges,
  selectedNode,
  onNodeClick,
  width,
  height,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { forceNodes, forceEdges } = useForceGraph(nodes, edges, width, height);
  const [hovered, setHovered] = useState<ForceNode | null>(null);
  const nodeRadius = 10;

  // Draw on canvas whenever layout changes
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !forceNodes.length) return;
    const ctx = canvas.getContext('2d')!;

    ctx.clearRect(0, 0, width, height);

    // Draw edges
    for (const edge of forceEdges) {
      const src = edge.sourceNode!;
      const tgt = edge.targetNode!;
      if (!src || !tgt) continue;

      const edgeColor = EDGE_COLORS[edge.relationship] || EDGE_COLORS.default;
      ctx.beginPath();
      ctx.moveTo(src.x, src.y);
      ctx.lineTo(tgt.x, tgt.y);
      ctx.strokeStyle = edgeColor + '66'; // semi-transparent
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Arrowhead
      const angle = Math.atan2(tgt.y - src.y, tgt.x - src.x);
      const ax = tgt.x - (nodeRadius + 4) * Math.cos(angle);
      const ay = tgt.y - (nodeRadius + 4) * Math.sin(angle);
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(ax - 8 * Math.cos(angle - 0.4), ay - 8 * Math.sin(angle - 0.4));
      ctx.lineTo(ax - 8 * Math.cos(angle + 0.4), ay - 8 * Math.sin(angle + 0.4));
      ctx.closePath();
      ctx.fillStyle = edgeColor + '88';
      ctx.fill();
    }

    // Draw nodes
    for (const node of forceNodes) {
      const isSelected = selectedNode?.id === node.id;
      const isHovered = hovered?.id === node.id;
      const r = isSelected ? nodeRadius + 4 : isHovered ? nodeRadius + 2 : nodeRadius;

      const baseColor = node.type === 'file'
        ? (LANGUAGE_COLORS[node.language || 'unknown'] || NODE_COLORS.file)
        : NODE_COLORS[node.type] || NODE_COLORS.default;

      // Glow effect for selected
      if (isSelected) {
        ctx.shadowColor = baseColor;
        ctx.shadowBlur = 20;
      } else if (isHovered) {
        ctx.shadowColor = baseColor;
        ctx.shadowBlur = 10;
      } else {
        ctx.shadowBlur = 0;
      }

      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, Math.PI * 2);

      // Gradient fill
      const grad = ctx.createRadialGradient(
        node.x - r * 0.3, node.y - r * 0.3, 0,
        node.x, node.y, r
      );
      grad.addColorStop(0, baseColor + 'ff');
      grad.addColorStop(1, baseColor + '88');
      ctx.fillStyle = grad;
      ctx.fill();

      // Border
      ctx.strokeStyle = isSelected ? '#ffffff' : baseColor + 'cc';
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Label for selected / hovered or if few nodes
      if (isSelected || isHovered || forceNodes.length <= 30) {
        ctx.fillStyle = '#e2e8f0';
        ctx.font = `${isSelected ? 'bold ' : ''}11px Inter, sans-serif`;
        ctx.textAlign = 'center';
        ctx.fillText(
          node.label.length > 18 ? node.label.slice(0, 16) + '…' : node.label,
          node.x,
          node.y + r + 14
        );
      }
    }
  }, [forceNodes, forceEdges, selectedNode, hovered, width, height]);

  const getNodeAt = useCallback(
    (x: number, y: number): ForceNode | null => {
      for (const node of forceNodes) {
        const dx = x - node.x;
        const dy = y - node.y;
        if (Math.sqrt(dx * dx + dy * dy) <= nodeRadius + 4) return node;
      }
      return null;
    },
    [forceNodes]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const rect = canvasRef.current!.getBoundingClientRect();
      const node = getNodeAt(e.clientX - rect.left, e.clientY - rect.top);
      setHovered(node);
      canvasRef.current!.style.cursor = node ? 'pointer' : 'default';
    },
    [getNodeAt]
  );

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const rect = canvasRef.current!.getBoundingClientRect();
      const node = getNodeAt(e.clientX - rect.left, e.clientY - rect.top);
      if (node) onNodeClick(node);
    },
    [getNodeAt, onNodeClick]
  );

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      onMouseMove={handleMouseMove}
      onClick={handleClick}
      className="rounded-xl"
    />
  );
};

// ─── Risk Badge ──────────────────────────────────────────────────────────────

const RiskBadge: React.FC<{ level: string }> = ({ level }) => {
  const color = RISK_COLORS[level] || '#6b7280';
  return (
    <span
      className="px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider"
      style={{ background: color + '22', color, border: `1px solid ${color}55` }}
    >
      {level}
    </span>
  );
};

// ─── Impact Level Badge ───────────────────────────────────────────────────────

const ImpactBadge: React.FC<{ level: string }> = ({ level }) => {
  const colors: Record<string, string> = {
    direct: '#ef4444',
    first: '#f97316',
    second: '#f59e0b',
    transitive: '#6b7280',
  };
  const c = colors[level] || '#6b7280';
  return (
    <span
      className="px-2 py-0.5 rounded text-xs font-semibold"
      style={{ background: c + '22', color: c }}
    >
      {level}
    </span>
  );
};

// ─── Main Page ───────────────────────────────────────────────────────────────

export const DependencyGraph: React.FC = () => {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<string>('');
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [graphStats, setGraphStats] = useState<GraphStats | null>(null);
  const [impactResult, setImpactResult] = useState<ImpactAnalysisResult | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [impactLoading, setImpactLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'graph' | 'impact' | 'ingest'>('graph');
  const [impactFiles, setImpactFiles] = useState('');
  const [ingestContent, setIngestContent] = useState('');
  const [ingestPath, setIngestPath] = useState('');
  const [ingestSha, setIngestSha] = useState('');
  const [ingestLoading, setIngestLoading] = useState(false);
  const [ingestResult, setIngestResult] = useState<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 520 });

  // Resize canvas to container
  useEffect(() => {
    const obs = new ResizeObserver(entries => {
      for (const entry of entries) {
        setCanvasSize({
          width: Math.floor(entry.contentRect.width),
          height: 520,
        });
      }
    });
    if (containerRef.current) obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  // Load repositories
  useEffect(() => {
    api
      .getRepositories()
      .then(repos => {
        setRepositories(repos);
        if (repos.length > 0) setSelectedRepo(repos[0].id);
      })
      .catch(() => {});
  }, []);

  const loadGraph = useCallback(async () => {
    if (!selectedRepo) return;
    setLoading(true);
    setError(null);
    setGraphData(null);
    setGraphStats(null);
    try {
      const [graph, stats] = await Promise.all([
        api.getRepositoryGraph(selectedRepo, 200),
        api.getGraphStats(selectedRepo),
      ]);
      setGraphData(graph);
      setGraphStats(stats);
    } catch (e: any) {
      setError(e.message || 'Failed to load graph data');
    } finally {
      setLoading(false);
    }
  }, [selectedRepo]);

  useEffect(() => {
    if (selectedRepo && activeTab === 'graph') loadGraph();
  }, [selectedRepo, activeTab]);

  const runImpact = async () => {
    if (!selectedRepo || !impactFiles.trim()) return;
    const files = impactFiles
      .split('\n')
      .map(f => f.trim())
      .filter(Boolean);
    setImpactLoading(true);
    setImpactResult(null);
    setError(null);
    try {
      const result = await api.runImpactAnalysis(selectedRepo, files);
      setImpactResult(result);
    } catch (e: any) {
      setError(e.message || 'Impact analysis failed');
    } finally {
      setImpactLoading(false);
    }
  };

  const runIngest = async () => {
    if (!selectedRepo || !ingestPath.trim() || !ingestContent.trim()) return;
    setIngestLoading(true);
    setIngestResult(null);
    setError(null);
    try {
      const sha = ingestSha.trim() || 'manual-ingest-' + Date.now().toString(16);
      const result = await api.ingestFiles(selectedRepo, sha, [
        { path: ingestPath.trim(), content: ingestContent },
      ]);
      setIngestResult(result);
    } catch (e: any) {
      setError(e.message || 'Ingestion failed');
    } finally {
      setIngestLoading(false);
    }
  };

  const totalNodes = graphData?.nodes.length || 0;
  const totalEdges = graphData?.edges.length || 0;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Network className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">Dependency Graph</h1>
          </div>
          <p className="text-gray-400 text-sm ml-13">
            Code intelligence — visualize structure, trace impact, explore dependencies
          </p>
        </div>

        {/* Repo Selector */}
        <div className="relative">
          <select
            value={selectedRepo}
            onChange={e => setSelectedRepo(e.target.value)}
            className="appearance-none bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 pr-10 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 min-w-[200px] cursor-pointer"
          >
            <option value="">Select repository…</option>
            {repositories.map(r => (
              <option key={r.id} value={r.id}>{r.full_name}</option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>
      </div>

      {/* Stats Row */}
      {graphStats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Files', value: graphStats.total_files, icon: FileCode2, color: '#6366f1' },
            { label: 'Functions', value: graphStats.total_functions, icon: Code2, color: '#22d3ee' },
            { label: 'Classes', value: graphStats.total_classes, icon: Boxes, color: '#f59e0b' },
            { label: 'Import Edges', value: graphStats.total_import_edges, icon: GitBranch, color: '#ec4899' },
          ].map(stat => (
            <div
              key={stat.label}
              className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center gap-3"
            >
              <div
                className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                style={{ background: stat.color + '22' }}
              >
                <stat.icon className="w-4 h-4" style={{ color: stat.color }} />
              </div>
              <div>
                <div className="text-xl font-bold text-white">{stat.value.toLocaleString()}</div>
                <div className="text-xs text-gray-500">{stat.label}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1 w-fit">
        {([
          { id: 'graph', label: 'Graph View', icon: Network },
          { id: 'impact', label: 'Impact Analysis', icon: Zap },
          { id: 'ingest', label: 'Ingest Files', icon: Activity },
        ] as const).map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeTab === tab.id
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/25'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-red-300 font-medium">Error</p>
            <p className="text-sm text-red-400 mt-0.5">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-200">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ── Graph Tab ── */}
      {activeTab === 'graph' && (
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
          {/* Canvas */}
          <div className="xl:col-span-3 bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Network className="w-4 h-4" />
                <span>{totalNodes} nodes · {totalEdges} edges</span>
              </div>
              <button
                onClick={loadGraph}
                disabled={loading}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
            <div ref={containerRef} className="w-full relative">
              {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 z-10 rounded-b-2xl">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                    <p className="text-sm text-gray-400">Building graph…</p>
                  </div>
                </div>
              )}
              {!loading && !graphData?.nodes.length && (
                <div className="flex flex-col items-center justify-center h-[520px] gap-4 text-center px-8">
                  <div className="w-16 h-16 rounded-2xl bg-gray-800 flex items-center justify-center">
                    <Network className="w-8 h-8 text-gray-600" />
                  </div>
                  <div>
                    <p className="text-gray-400 font-medium mb-1">No graph data yet</p>
                    <p className="text-gray-600 text-sm">
                      Use the <span className="text-indigo-400">Ingest Files</span> tab to parse source files into the graph, or wait for a webhook to trigger analysis.
                    </p>
                  </div>
                </div>
              )}
              {graphData && graphData.nodes.length > 0 && (
                <CanvasGraph
                  nodes={graphData.nodes}
                  edges={graphData.edges}
                  selectedNode={selectedNode}
                  onNodeClick={setSelectedNode}
                  width={canvasSize.width}
                  height={canvasSize.height}
                />
              )}
            </div>

            {/* Legend */}
            <div className="flex flex-wrap items-center gap-x-5 gap-y-2 px-4 py-3 border-t border-gray-800 text-xs text-gray-500">
              <span className="font-medium text-gray-400">Languages:</span>
              {Object.entries(LANGUAGE_COLORS).slice(0, 5).map(([lang, color]) => (
                <span key={lang} className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                  {lang}
                </span>
              ))}
              <span className="font-medium text-gray-400 ml-2">Edges:</span>
              {Object.entries(EDGE_COLORS).slice(0, 3).map(([rel, color]) => (
                <span key={rel} className="flex items-center gap-1.5">
                  <span className="w-4 h-0.5" style={{ background: color }} />
                  {rel}
                </span>
              ))}
            </div>
          </div>

          {/* Node Inspector */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4 space-y-4">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-indigo-400" />
              <h3 className="text-sm font-semibold text-gray-200">Node Inspector</h3>
            </div>
            {selectedNode ? (
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-semibold text-white break-all">{selectedNode.label}</p>
                  <button
                    onClick={() => setSelectedNode(null)}
                    className="text-gray-500 hover:text-gray-300 flex-shrink-0"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="space-y-2">
                  {[
                    { label: 'Type', value: selectedNode.type },
                    { label: 'Language', value: selectedNode.language || '—' },
                    { label: 'Path', value: selectedNode.path || selectedNode.file_path || '—' },
                    { label: 'Line', value: selectedNode.start_line?.toString() || '—' },
                    { label: 'Symbols', value: selectedNode.symbol_count?.toString() || '—' },
                  ].map(item => (
                    <div key={item.label}>
                      <p className="text-xs text-gray-500 mb-0.5">{item.label}</p>
                      <p className="text-xs text-gray-300 break-all font-mono">{item.value}</p>
                    </div>
                  ))}
                </div>

                <div
                  className="w-full h-1.5 rounded-full mt-2"
                  style={{
                    background: selectedNode.type === 'file'
                      ? LANGUAGE_COLORS[selectedNode.language || 'unknown'] || NODE_COLORS.file
                      : NODE_COLORS[selectedNode.type] || NODE_COLORS.default,
                  }}
                />
              </div>
            ) : (
              <div className="text-center py-8">
                <Search className="w-8 h-8 text-gray-700 mx-auto mb-2" />
                <p className="text-xs text-gray-500">Click any node to inspect it</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Impact Analysis Tab ── */}
      {activeTab === 'impact' && (
        <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
          {/* Input */}
          <div className="xl:col-span-2 bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-yellow-400" />
              <h3 className="text-sm font-semibold text-gray-200">Changed Files</h3>
            </div>
            <p className="text-xs text-gray-500">
              Enter one file path per line. ProofMesh will trace all impacted dependents.
            </p>
            <textarea
              value={impactFiles}
              onChange={e => setImpactFiles(e.target.value)}
              placeholder={'app/core/config.py\napp/services/auth/service.py\nfrontend/src/services/api.ts'}
              rows={8}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-200 font-mono placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
            <button
              onClick={runImpact}
              disabled={impactLoading || !selectedRepo || !impactFiles.trim()}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-sm font-semibold hover:from-indigo-500 hover:to-purple-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2"
            >
              {impactLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Analyzing…
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  Run Impact Analysis
                </>
              )}
            </button>
          </div>

          {/* Results */}
          <div className="xl:col-span-3 bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
            {!impactResult ? (
              <div className="flex flex-col items-center justify-center h-80 gap-3 text-center px-8">
                <div className="w-14 h-14 rounded-2xl bg-gray-800 flex items-center justify-center">
                  <Zap className="w-7 h-7 text-gray-600" />
                </div>
                <p className="text-gray-500 text-sm">
                  Enter changed files and run the analysis to see impact results.
                </p>
              </div>
            ) : (
              <div className="overflow-auto max-h-[600px]">
                {/* Risk Header */}
                <div
                  className="p-5 border-b border-gray-800"
                  style={{
                    background: `linear-gradient(135deg, ${RISK_COLORS[impactResult.risk_summary.overall_risk]}11 0%, transparent 100%)`,
                  }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Shield className="w-5 h-5" style={{ color: RISK_COLORS[impactResult.risk_summary.overall_risk] }} />
                      <span className="font-semibold text-white">Risk Assessment</span>
                    </div>
                    <RiskBadge level={impactResult.risk_summary.overall_risk} />
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { label: 'Blast Radius', value: impactResult.risk_summary.blast_radius },
                      { label: 'Directly Affected', value: impactResult.directly_impacted.length },
                      { label: 'Transitively Affected', value: impactResult.transitively_impacted.length },
                    ].map(m => (
                      <div key={m.label} className="bg-gray-800/60 rounded-xl p-3 text-center">
                        <div className="text-2xl font-bold text-white">{m.value}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{m.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Risk bar */}
                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>Risk Score</span>
                      <span>{(impactResult.risk_summary.risk_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{
                          width: `${impactResult.risk_summary.risk_score * 100}%`,
                          background: RISK_COLORS[impactResult.risk_summary.overall_risk],
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Directly Impacted */}
                {impactResult.directly_impacted.length > 0 && (
                  <div className="p-4 border-b border-gray-800">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                      Directly Impacted ({impactResult.directly_impacted.length})
                    </p>
                    <div className="space-y-2">
                      {impactResult.directly_impacted.map((f, i) => (
                        <ImpactFileRow key={i} file={f} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Transitively Impacted */}
                {impactResult.transitively_impacted.length > 0 && (
                  <div className="p-4">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                      Transitively Impacted ({impactResult.transitively_impacted.length})
                    </p>
                    <div className="space-y-2">
                      {impactResult.transitively_impacted.map((f, i) => (
                        <ImpactFileRow key={i} file={f} />
                      ))}
                    </div>
                  </div>
                )}

                {impactResult.directly_impacted.length === 0 &&
                  impactResult.transitively_impacted.length === 0 && (
                    <div className="p-8 text-center">
                      <Shield className="w-8 h-8 text-green-500 mx-auto mb-2" />
                      <p className="text-green-400 font-medium">No dependent files found</p>
                      <p className="text-gray-500 text-sm mt-1">
                        The changed files appear to be leaf nodes with no reverse dependencies in the graph.
                      </p>
                    </div>
                  )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Ingest Tab ── */}
      {activeTab === 'ingest' && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-semibold text-gray-200">Ingest Source File</h3>
            </div>
            <p className="text-xs text-gray-500">
              Paste a source file to parse and add to the graph. This builds the dependency index for impact analysis.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">File Path</label>
                <input
                  value={ingestPath}
                  onChange={e => setIngestPath(e.target.value)}
                  placeholder="app/core/config.py"
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 text-sm font-mono text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Commit SHA (optional)</label>
                <input
                  value={ingestSha}
                  onChange={e => setIngestSha(e.target.value)}
                  placeholder="abc1234"
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 text-sm font-mono text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">File Content</label>
                <textarea
                  value={ingestContent}
                  onChange={e => setIngestContent(e.target.value)}
                  placeholder={'import os\nimport redis\nfrom app.core.config import settings\n\nclass MyService:\n    def run(self):\n        pass'}
                  rows={10}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-200 font-mono placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
                />
              </div>
            </div>

            <button
              onClick={runIngest}
              disabled={ingestLoading || !selectedRepo || !ingestPath.trim() || !ingestContent.trim()}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white text-sm font-semibold hover:from-emerald-500 hover:to-teal-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2"
            >
              {ingestLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Ingesting…
                </>
              ) : (
                <>
                  <Activity className="w-4 h-4" />
                  Parse & Ingest File
                </>
              )}
            </button>
          </div>

          {/* Ingest Result */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            {!ingestResult ? (
              <div className="flex flex-col items-center justify-center h-full min-h-[300px] gap-3 text-center">
                <div className="w-14 h-14 rounded-2xl bg-gray-800 flex items-center justify-center">
                  <Code2 className="w-7 h-7 text-gray-600" />
                </div>
                <p className="text-gray-500 text-sm">Ingestion results will appear here</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <p className="text-sm font-semibold text-emerald-400">Ingestion Successful</p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: 'Files Processed', value: ingestResult.files_processed },
                    { label: 'Classes', value: ingestResult.total_classes },
                    { label: 'Functions', value: ingestResult.total_functions },
                    { label: 'Methods', value: ingestResult.total_methods },
                    { label: 'Import Edges', value: ingestResult.total_imports },
                    { label: 'Graph Relationships', value: ingestResult.total_relationships },
                  ].map(m => (
                    <div key={m.label} className="bg-gray-800 rounded-xl p-3">
                      <div className="text-xl font-bold text-white">{m.value}</div>
                      <div className="text-xs text-gray-500">{m.label}</div>
                    </div>
                  ))}
                </div>

                {ingestResult.errors?.length > 0 && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3">
                    <p className="text-xs text-red-400 font-medium mb-1">Errors</p>
                    {ingestResult.errors.map((err: string, i: number) => (
                      <p key={i} className="text-xs text-red-300 font-mono">{err}</p>
                    ))}
                  </div>
                )}

                <button
                  onClick={() => { setActiveTab('graph'); loadGraph(); }}
                  className="flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  <ArrowRight className="w-4 h-4" />
                  View updated graph
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Impact File Row Component ────────────────────────────────────────────────

const ImpactFileRow: React.FC<{ file: ImpactedFile }> = ({ file }) => {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-3 hover:bg-gray-800 transition-colors text-left"
      >
        <div className="flex-1 min-w-0">
          <p className="text-xs font-mono text-gray-300 truncate">{file.path}</p>
          <p className="text-xs text-gray-600 mt-0.5">{file.language}</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <ImpactBadge level={file.impact_level} />
          <div className="text-xs text-gray-500 w-10 text-right">
            {(file.risk_score * 100).toFixed(0)}%
          </div>
        </div>
      </button>

      {expanded && (file.impact_chain.length > 0 || file.affected_symbols.length > 0) && (
        <div className="px-3 pb-3 border-t border-gray-700/50 pt-2 space-y-2">
          {file.impact_chain.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-1">Impact chain</p>
              <div className="flex flex-wrap gap-1">
                {file.impact_chain.map((c, i) => (
                  <span key={i} className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded font-mono">
                    {c.split('/').pop()}
                  </span>
                ))}
              </div>
            </div>
          )}
          {file.affected_symbols.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-1">Affected symbols</p>
              <div className="flex flex-wrap gap-1">
                {file.affected_symbols.slice(0, 6).map((s, i) => (
                  <span key={i} className="text-xs bg-indigo-500/10 text-indigo-300 px-2 py-0.5 rounded font-mono">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
