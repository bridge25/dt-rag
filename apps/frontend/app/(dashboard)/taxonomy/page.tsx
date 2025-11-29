/**
 * Taxonomy browser page - React Flow 기반 Constellation Explorer
 *
 * 뉴디자인2.png 스펙 완벽 구현:
 * - React Flow (@xyflow/react) 엔진 사용
 * - 마우스 휠 줌인/아웃
 * - 캔버스 드래그 팬
 * - 노드 드래그 가능
 * - 애니메이션 연결선
 * - 좌측 하단 컨트롤 패널 (React Flow 함수 연결)
 *
 * @CODE:FRONTEND-REDESIGN-001-TAXONOMY-PAGE
 */

"use client";

import { useCallback, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ReactFlow,
  Background,
  Panel,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  useReactFlow,
  ReactFlowProvider,
  MarkerType,
  type NodeMouseHandler,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import dagre from "dagre";
import { Network, Loader2, Sparkles, ZoomIn, ZoomOut, Filter, Settings, ChevronRight, Upload, Bot, X } from "lucide-react";
import { ImportKnowledgeModal } from "@/components/taxonomy/ImportKnowledgeModal";
import { TaxonomyVersionPanel } from "@/components/taxonomy/TaxonomyVersionPanel";
import { AgentCreationModal } from "@/components/taxonomy/AgentCreationModal";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n/context";

import { getTaxonomyTree } from "@/lib/api";
import { TaxonomyGraphNode, TaxonomyNodeData } from "@/components/taxonomy/TaxonomyGraphNode";

// Node Types Configuration (type assertion for React Flow compatibility)
const nodeTypes = {
  taxonomyNode: TaxonomyGraphNode,
} as const;

// Mock taxonomy data for demo
const MOCK_TAXONOMY_DATA = [
  {
    id: "root-1",
    name: "Technology",
    level: 1,
    document_count: 156,
    children: [
      {
        id: "tech-ai",
        name: "Artificial Intelligence",
        level: 2,
        document_count: 45,
        children: [
          { id: "ai-ml", name: "Machine Learning", level: 3, document_count: 23 },
          { id: "ai-nlp", name: "NLP", level: 3, document_count: 12 },
          { id: "ai-cv", name: "Computer Vision", level: 3, document_count: 10 },
        ],
      },
      {
        id: "tech-web",
        name: "Web Development",
        level: 2,
        document_count: 67,
        children: [
          { id: "web-frontend", name: "Frontend", level: 3, document_count: 34 },
          { id: "web-backend", name: "Backend", level: 3, document_count: 33 },
        ],
      },
      {
        id: "tech-cloud",
        name: "Cloud Computing",
        level: 2,
        document_count: 44,
        children: [
          { id: "cloud-aws", name: "AWS", level: 3, document_count: 18 },
          { id: "cloud-gcp", name: "GCP", level: 3, document_count: 14 },
          { id: "cloud-azure", name: "Azure", level: 3, document_count: 12 },
        ],
      },
    ],
  },
  {
    id: "root-2",
    name: "Business",
    level: 1,
    document_count: 89,
    children: [
      { id: "biz-strategy", name: "Strategy", level: 2, document_count: 32 },
      { id: "biz-marketing", name: "Marketing", level: 2, document_count: 28 },
      { id: "biz-finance", name: "Finance", level: 2, document_count: 29 },
    ],
  },
];

// Layout Calculation using Dagre
const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: "TB", nodesep: 120, ranksep: 180 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 100, height: 100 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 50,
        y: nodeWithPosition.y - 50,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

// Transform API data to React Flow elements
const transformDataToGraph = (data: any[]) => {
  const nodes: Node<TaxonomyNodeData>[] = [];
  const edges: Edge[] = [];

  const traverse = (item: any, parentId: string | null = null) => {
    const nodeId = item.id;
    const nodeType = item.level === 1 ? "root" : item.children?.length ? "category" : "item";

    nodes.push({
      id: nodeId,
      type: "taxonomyNode",
      data: {
        label: item.name,
        type: nodeType,
        count: item.document_count,
        documentCount: item.document_count,
        connectionCount: Math.floor(Math.random() * 150) + 10,
      },
      position: { x: 0, y: 0 },
    });

    if (parentId) {
      edges.push({
        id: `e${parentId}-${nodeId}`,
        source: parentId,
        target: nodeId,
        // Gemini Guide: smoothstep 곡선 + 밝은 시안색
        type: "smoothstep",
        animated: true,
        style: {
          stroke: "rgba(0, 247, 255, 0.6)",
          strokeWidth: 2,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: "rgba(0, 247, 255, 0.8)",
        },
      });
    }

    if (item.children) {
      item.children.forEach((child: any) => traverse(child, nodeId));
    }
  };

  data.forEach((root) => traverse(root));

  return getLayoutedElements(nodes, edges);
};

// Control Panel Component (React Flow 함수 연결)
function TaxonomyControlPanel() {
  const { t } = useTranslation();
  const { zoomIn, zoomOut, fitView } = useReactFlow();
  const [dataDensity, setDataDensity] = useState(50);

  return (
    <div
      className={cn(
        "w-64 p-4 space-y-2",
        "bg-slate-800/70 backdrop-blur-xl",
        "border border-white/10 rounded-xl",
        "shadow-2xl shadow-black/50"
      )}
    >
      {/* Zoom In */}
      <button
        onClick={() => zoomIn({ duration: 300 })}
        className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-xs font-medium text-gray-200 uppercase tracking-wider hover:bg-white/10 transition-colors"
      >
        <ZoomIn size={18} className="opacity-80" />
        <span className="flex-1 text-left">{t("taxonomy.zoomIn")}</span>
      </button>

      {/* Zoom Out */}
      <button
        onClick={() => zoomOut({ duration: 300 })}
        className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-xs font-medium text-gray-200 uppercase tracking-wider hover:bg-white/10 transition-colors"
      >
        <ZoomOut size={18} className="opacity-80" />
        <span className="flex-1 text-left">{t("taxonomy.zoomOut")}</span>
      </button>

      {/* Filter */}
      <button
        className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-xs font-medium text-gray-200 uppercase tracking-wider hover:bg-white/10 transition-colors"
      >
        <Filter size={18} className="opacity-80" />
        <span className="flex-1 text-left">{t("common.filter")}</span>
        <ChevronRight size={14} className="opacity-60" />
      </button>

      {/* Settings */}
      <button
        className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-xs font-medium text-gray-200 uppercase tracking-wider hover:bg-white/10 transition-colors"
      >
        <Settings size={18} className="opacity-80" />
        <span className="flex-1 text-left">{t("common.settings")}</span>
        <ChevronRight size={14} className="opacity-60" />
      </button>

      {/* Divider */}
      <div className="border-t border-white/10 my-2" />

      {/* Data Density Slider */}
      <div className="space-y-2 pt-1">
        <label className="block text-xs font-medium text-gray-300 uppercase tracking-wider">
          {t("taxonomy.dataDensity")}
        </label>
        <input
          type="range"
          min="0"
          max="100"
          value={dataDensity}
          onChange={(e) => setDataDensity(Number(e.target.value))}
          className={cn(
            "w-full h-1.5 rounded-full accent-cyan-400",
            "appearance-none bg-gradient-to-r from-white/20 to-white/5",
            "[&::-webkit-slider-thumb]:appearance-none",
            "[&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3",
            "[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-cyan-400",
            "[&::-webkit-slider-thumb]:cursor-pointer",
            // Gemini Guide: slider thumb 네온 글로우
            "[&::-webkit-slider-thumb]:shadow-[0_0_5px_rgba(0,247,255,0.7)]"
          )}
        />
        <div className="text-xs text-gray-400">{t("taxonomy.density")}: {dataDensity}%</div>
      </div>

      {/* Fit View Button */}
      <button
        onClick={() => fitView({ duration: 500, padding: 0.2 })}
        className="w-full mt-2 px-3 py-2 rounded-lg text-xs font-medium text-cyan-400 uppercase tracking-wider hover:bg-cyan-400/10 border border-cyan-400/30 transition-colors"
      >
        {t("taxonomy.fitToView")}
      </button>
    </div>
  );
}

// Main Taxonomy Flow Component
interface TaxonomyFlowProps {
  initialNodes: Node[];
  initialEdges: Edge[];
  onNodeSelect?: (nodeId: string | null, nodePath: string[]) => void;
  selectedNodeId?: string | null;
}

function TaxonomyFlow({ initialNodes, initialEdges, onNodeSelect, selectedNodeId }: TaxonomyFlowProps) {
  const [nodes, _setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Build path from root to target node using edges
  const buildPathToNode = useCallback((targetId: string): string[] => {
    const path: string[] = [];
    const nodeMap = new Map(initialNodes.map(n => [n.id, n]));

    // Build parent map from edges
    const parentMap = new Map<string, string>();
    initialEdges.forEach(edge => {
      parentMap.set(edge.target, edge.source);
    });

    // Traverse from target to root
    let currentId: string | undefined = targetId;
    while (currentId) {
      const node = nodeMap.get(currentId);
      if (node) {
        path.unshift((node.data as TaxonomyNodeData).label);
      }
      currentId = parentMap.get(currentId);
    }

    return path;
  }, [initialNodes, initialEdges]);

  // Handle node click for selection
  const onNodeClick: NodeMouseHandler = useCallback((event, node) => {
    if (selectedNodeId === node.id) {
      // Deselect if clicking the same node
      onNodeSelect?.(null, []);
    } else {
      // Select new node and build path
      const path = buildPathToNode(node.id);
      onNodeSelect?.(node.id, path);
    }
  }, [selectedNodeId, onNodeSelect, buildPathToNode]);

  // Update node selection state
  const nodesWithSelection = useMemo(() => {
    return nodes.map(node => ({
      ...node,
      selected: node.id === selectedNodeId,
    }));
  }, [nodes, selectedNodeId]);

  return (
    <ReactFlow
      nodes={nodesWithSelection}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      onNodeClick={onNodeClick}
      nodeTypes={nodeTypes as any}
      fitView
      minZoom={0.1}
      maxZoom={2}
      defaultEdgeOptions={{
        // Gemini Guide: smoothstep 곡선 + 네온 시안
        type: "smoothstep",
        animated: true,
        style: { stroke: "rgba(0, 247, 255, 0.6)", strokeWidth: 2 },
      }}
      proOptions={{ hideAttribution: true }}
      className="bg-transparent"
    >
      {/* Space Background - Gemini Guide: 그리드 매우 은은하게 또는 제거 */}
      <Background
        color="rgba(255, 255, 255, 0.01)"
        gap={50}
        size={0.5}
      />

      {/* Control Panel - Bottom Left - Gemini Guide: z-20 */}
      <Panel position="bottom-left" className="m-6 z-20">
        <TaxonomyControlPanel />
      </Panel>
    </ReactFlow>
  );
}

// Page Component
export default function TaxonomyPage() {
  const { t } = useTranslation();
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showAgentModal, setShowAgentModal] = useState(false);
  const [currentVersion, setCurrentVersion] = useState("1.8.1");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNodePath, setSelectedNodePath] = useState<string[]>([]);

  // Handle taxonomy version rollback
  const handleRollback = useCallback(async (version: string) => {
    // TODO: Call API to rollback taxonomy version
    console.log("Rolling back to version:", version);
    setCurrentVersion(version);
    // Trigger refetch of taxonomy data with the rolled back version
  }, []);

  // Handle node selection
  const handleNodeSelect = useCallback((nodeId: string | null, nodePath: string[]) => {
    setSelectedNodeId(nodeId);
    setSelectedNodePath(nodePath);
  }, []);

  // Handle agent creation
  const handleCreateAgent = useCallback(async (agent: {
    name: string;
    taxonomy_scope: string[];
    rarity: string;
    avatar: string;
  }) => {
    console.log("Creating agent:", agent);
    // TODO: Call API to create agent
    // After creation, navigate to agents page or show success toast
    setShowAgentModal(false);
    setSelectedNodeId(null);
    setSelectedNodePath([]);
  }, []);

  const { data, isLoading } = useQuery({
    queryKey: ["taxonomy"],
    queryFn: () => getTaxonomyTree("1.8.1"),
  });

  // Use mock data if API returns empty or fails
  const taxonomyData = useMemo(() => {
    if (data && Array.isArray(data) && data.length > 0) {
      return data;
    }
    return MOCK_TAXONOMY_DATA;
  }, [data]);

  // Transform data to React Flow elements
  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => transformDataToGraph(taxonomyData),
    [taxonomyData]
  );

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="absolute inset-0 bg-cyan-400/20 rounded-full blur-xl animate-pulse" />
            <Loader2 className="h-12 w-12 animate-spin text-cyan-400 relative z-10" />
          </div>
          <p className="text-gray-400 animate-pulse">{t("taxonomy.loadingMessage")}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-4rem)] w-full flex overflow-hidden bg-[#050a15]">
      {/* Main Content Area */}
      <div className="flex-1 relative overflow-hidden">
        {/* Space Nebula Background - 뉴디자인2 스타일 */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {/* Deep space base gradient */}
          <div className="absolute inset-0 bg-gradient-to-b from-[#0a0f1a] via-[#0d1425] to-[#050a15]" />

          {/* Purple nebula - top right */}
          <div
            className="absolute -top-20 -right-20 w-[600px] h-[600px] rounded-full opacity-30 blur-3xl"
            style={{ background: "radial-gradient(circle, rgba(139,92,246,0.4) 0%, rgba(139,92,246,0.1) 50%, transparent 70%)" }}
          />

          {/* Cyan nebula - bottom left */}
          <div
            className="absolute -bottom-40 -left-20 w-[500px] h-[500px] rounded-full opacity-25 blur-3xl"
            style={{ background: "radial-gradient(circle, rgba(0,247,255,0.3) 0%, rgba(0,247,255,0.1) 50%, transparent 70%)" }}
          />

          {/* Pink/magenta nebula - center */}
          <div
            className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[800px] h-[400px] rounded-full opacity-15 blur-3xl"
            style={{ background: "radial-gradient(ellipse, rgba(236,72,153,0.3) 0%, rgba(168,85,247,0.1) 50%, transparent 70%)" }}
          />

          {/* Stars layer - tiny dots */}
          <div className="absolute inset-0 opacity-60"
            style={{
              backgroundImage: `
                radial-gradient(1px 1px at 20px 30px, white, transparent),
                radial-gradient(1px 1px at 40px 70px, rgba(255,255,255,0.8), transparent),
                radial-gradient(1px 1px at 50px 160px, rgba(255,255,255,0.6), transparent),
                radial-gradient(1px 1px at 90px 40px, white, transparent),
                radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.7), transparent),
                radial-gradient(1.5px 1.5px at 160px 120px, rgba(0,247,255,0.9), transparent),
                radial-gradient(1px 1px at 200px 150px, white, transparent),
                radial-gradient(1.5px 1.5px at 250px 50px, rgba(139,92,246,0.9), transparent),
                radial-gradient(1px 1px at 300px 100px, rgba(255,255,255,0.8), transparent),
                radial-gradient(1px 1px at 350px 200px, white, transparent)
              `,
              backgroundSize: "400px 300px",
            }}
          />
        </div>

        {/* Header Overlay */}
        <div className="absolute top-6 left-8 right-8 z-20 flex items-start justify-between pointer-events-none">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-slate-800/60 backdrop-blur-xl border border-white/10">
              {/* Gemini Guide: 아이콘 네온 글로우 */}
              <Network className="h-6 w-6 text-cyan-400 drop-shadow-[0_0_8px_rgba(0,247,255,0.7)]" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                {/* Gemini Guide: 아이콘 네온 글로우 */}
                <Sparkles className="w-5 h-5 text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.7)]" />
                {t("taxonomy.title")}
              </h1>
              <p className="text-sm text-gray-400">
                {t("taxonomy.subtitle")} • {initialNodes.length} {t("taxonomy.nodes")} • v{currentVersion}
              </p>
            </div>
          </div>
        </div>

        {/* React Flow Graph */}
        <ReactFlowProvider>
          <TaxonomyFlow
            initialNodes={initialNodes}
            initialEdges={initialEdges}
            selectedNodeId={selectedNodeId}
            onNodeSelect={handleNodeSelect}
          />
        </ReactFlowProvider>

        {/* Ambient glow effect */}
        <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_center,transparent_0%,rgba(11,17,33,0.6)_100%)]" />

        {/* Selected Node Indicator & Create Agent Button - Bottom Right */}
        <div className="absolute bottom-8 right-8 z-30 flex flex-col items-end gap-3">
          {/* Selection Indicator */}
          {selectedNodeId && selectedNodePath.length > 0 && (
            <div
              className={cn(
                "flex items-center gap-3 px-4 py-3",
                "bg-slate-800/90 backdrop-blur-xl",
                "border border-cyan-400/30 rounded-xl",
                "shadow-lg shadow-cyan-500/20",
                "animate-in fade-in slide-in-from-bottom-2 duration-200"
              )}
            >
              <div className="flex-1">
                <div className="text-xs text-cyan-400 font-medium uppercase tracking-wider mb-1">
                  {t("taxonomy.nodeSelected")}
                </div>
                <div className="text-sm text-white font-medium">
                  /{selectedNodePath.join("/")}
                </div>
              </div>
              <button
                onClick={() => handleNodeSelect(null, [])}
                className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
              >
                <X className="w-4 h-4 text-white/60" />
              </button>
            </div>
          )}

          {/* FAB Buttons Row */}
          <div className="flex items-center gap-3">
            {/* Create Agent Button - Only visible when node selected */}
            {selectedNodeId && (
              <button
                onClick={() => setShowAgentModal(true)}
                className={cn(
                  "flex items-center gap-2 px-5 py-3",
                  "bg-gradient-to-r from-purple-500 to-pink-500",
                  "text-white font-semibold text-sm",
                  "rounded-full shadow-lg",
                  "transition-all duration-300 ease-out",
                  "hover:scale-105 hover:shadow-[0_0_25px_rgba(168,85,247,0.5)]",
                  "active:scale-95",
                  "animate-in fade-in slide-in-from-bottom-2 duration-200"
                )}
              >
                <Bot className="w-5 h-5" />
                {t("taxonomy.createAgent")}
              </button>
            )}

            {/* Import Knowledge Button */}
            <button
              onClick={() => setShowUploadModal(true)}
              className={cn(
                "flex items-center gap-2 px-5 py-3",
                "bg-gradient-to-r from-cyan-500 to-purple-500",
                "text-white font-semibold text-sm",
                "rounded-full shadow-lg",
                "transition-all duration-300 ease-out",
                "hover:scale-105 hover:shadow-[0_0_25px_rgba(0,247,255,0.5)]",
                "active:scale-95"
              )}
            >
              <Upload className="w-5 h-5" />
              {t("taxonomy.importKnowledge")}
            </button>
          </div>
        </div>
      </div>

      {/* Version History Side Panel */}
      <TaxonomyVersionPanel
        currentVersion={currentVersion}
        onVersionChange={(version) => {
          setCurrentVersion(version);
          // TODO: Trigger taxonomy data refetch with selected version
        }}
        onRollback={handleRollback}
        className="h-full"
      />

      {/* Import Knowledge Modal */}
      <ImportKnowledgeModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUploadComplete={(results) => {
          console.log("Upload completed:", results);
          // TODO: Trigger taxonomy refresh after upload
        }}
      />

      {/* Agent Creation Modal */}
      <AgentCreationModal
        isOpen={showAgentModal}
        onClose={() => setShowAgentModal(false)}
        taxonomyPath={selectedNodePath}
        onCreateAgent={handleCreateAgent}
      />
    </div>
  );
}
