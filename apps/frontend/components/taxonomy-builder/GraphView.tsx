"use client"

/**
 * GraphView - ReactFlow-based graph visualization for TaxonomyBuilder
 * Constellation Explorer Aesthetic
 *
 * @CODE:TAXONOMY-BUILDER-002
 */

import { useCallback, useMemo, useEffect } from "react"
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
  type Edge,
  type Node,
  type NodeMouseHandler,
  Handle,
  Position,
} from "@xyflow/react"
import { memo } from "react"
import { cn } from "@/lib/utils"
import { Folder, Database, Globe, FileText, Sparkles } from "lucide-react"
import dagre from "dagre"
import type { TaxonomyNode } from "./types"
import "@xyflow/react/dist/style.css"

// Custom node component for the graph view
interface BuilderNodeData extends Record<string, unknown> {
  node: TaxonomyNode
  isSelected: boolean
  documentsCount: number
}

const BuilderNodeComponent = memo<{ data: BuilderNodeData; id: string }>(
  function BuilderNodeComponent({ data }) {
    const { node, isSelected, documentsCount } = data

    return (
      <div className="relative group">
        {/* Glow Effect */}
        <div
          className={cn(
            "absolute inset-0 rounded-full blur-xl transition-all duration-500",
            isSelected
              ? "bg-blue-500/40 scale-150"
              : "bg-blue-500/0 group-hover:bg-blue-500/20 scale-125"
          )}
        />

        {/* Node Body */}
        <div
          className={cn(
            "relative flex flex-col items-center justify-center w-24 h-24 rounded-full border-2 transition-all duration-300 backdrop-blur-md",
            isSelected
              ? "bg-blue-900/40 border-blue-400 shadow-[0_0_20px_rgba(59,130,246,0.5)] scale-110"
              : "bg-black/40 border-white/10 hover:border-blue-400/50 hover:bg-blue-900/20"
          )}
        >
          <Handle
            type="target"
            position={Position.Top}
            className="!bg-blue-400 !w-2 !h-2 !border-none"
          />

          {/* Icon */}
          <div className={cn(
            "mb-2 transition-colors duration-300",
            isSelected ? "text-blue-200" : "text-blue-400/70 group-hover:text-blue-300"
          )}>
            {documentsCount > 10 ? (
              <Database className="w-6 h-6" />
            ) : (
              <Folder className="w-6 h-6" />
            )}
          </div>

          {/* Label */}
          <span className={cn(
            "text-xs font-medium text-center px-2 truncate w-full transition-colors duration-300",
            isSelected ? "text-white" : "text-white/70 group-hover:text-white"
          )}>
            {node.name}
          </span>

          {/* Badge */}
          {documentsCount > 0 && (
            <div className={cn(
              "absolute -top-2 -right-2 px-2 py-0.5 rounded-full text-[10px] font-bold border transition-all duration-300",
              isSelected
                ? "bg-blue-500 text-white border-blue-400 shadow-lg"
                : "bg-blue-900/50 text-blue-200 border-blue-500/30"
            )}>
              {documentsCount}
            </div>
          )}

          <Handle
            type="source"
            position={Position.Bottom}
            className="!bg-blue-400 !w-2 !h-2 !border-none"
          />
        </div>

        {/* Orbit Ring (Decorative) */}
        {isSelected && (
          <div className="absolute inset-0 -m-1 rounded-full border border-blue-500/30 animate-spin-slow pointer-events-none" />
        )}
      </div>
    )
  }
)

const nodeTypes = {
  builderNode: BuilderNodeComponent,
}

interface GraphViewProps {
  nodes: Map<string, TaxonomyNode>
  selectedNodeId: string | null
  onSelectNode: (id: string | null) => void
  className?: string
}

// Apply Dagre layout for hierarchical tree
function applyDagreLayout(
  flowNodes: Node[],
  flowEdges: Edge[]
): Node[] {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: "TB", nodesep: 100, ranksep: 120 })

  flowNodes.forEach((node) => {
    g.setNode(node.id, { width: 120, height: 120 })
  })

  flowEdges.forEach((edge) => {
    g.setEdge(edge.source, edge.target)
  })

  dagre.layout(g)

  return flowNodes.map((node) => {
    const nodeWithPosition = g.node(node.id)
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 60,
        y: nodeWithPosition.y - 60,
      },
    }
  })
}

// Convert TaxonomyNode Map to ReactFlow nodes and edges
function convertToFlow(
  nodes: Map<string, TaxonomyNode>,
  selectedNodeId: string | null
): { flowNodes: Node[]; flowEdges: Edge[] } {
  const flowNodes: Node[] = []
  const flowEdges: Edge[] = []

  nodes.forEach((node) => {
    flowNodes.push({
      id: node.id,
      type: "builderNode",
      position: node.position ?? { x: 0, y: 0 },
      data: {
        node,
        isSelected: node.id === selectedNodeId,
        documentsCount: node.metadata.documentsCount,
      } as BuilderNodeData,
    })

    // Create edges to children
    node.children.forEach((childId) => {
      flowEdges.push({
        id: `${node.id}-${childId}`,
        source: node.id,
        target: childId,
        type: "smoothstep",
        animated: true,
        style: {
          stroke: node.id === selectedNodeId ? "#60a5fa" : "#1e40af",
          strokeWidth: node.id === selectedNodeId ? 2 : 1,
          opacity: 0.6
        },
      })
    })
  })

  return { flowNodes, flowEdges }
}

function GraphViewInner({
  nodes,
  selectedNodeId,
  onSelectNode,
  className,
}: GraphViewProps) {
  const { flowNodes: initialNodes, flowEdges: initialEdges } = useMemo(() => {
    const { flowNodes, flowEdges } = convertToFlow(nodes, selectedNodeId)
    const layoutedNodes = applyDagreLayout(flowNodes, flowEdges)
    return { flowNodes: layoutedNodes, flowEdges }
  }, [nodes, selectedNodeId])

  const [flowNodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [flowEdges, , onEdgesChange] = useEdgesState(initialEdges)

  // Update nodes when data changes
  useEffect(() => {
    const { flowNodes, flowEdges } = convertToFlow(nodes, selectedNodeId)
    const layoutedNodes = applyDagreLayout(flowNodes, flowEdges)
    setNodes(layoutedNodes)
  }, [nodes, selectedNodeId, setNodes])

  const onNodeClick: NodeMouseHandler = useCallback(
    (_, node) => {
      onSelectNode(node.id)
    },
    [onSelectNode]
  )

  const onPaneClick = useCallback(() => {
    onSelectNode(null)
  }, [onSelectNode])

  if (nodes.size === 0) {
    return (
      <div
        className={cn(
          "flex items-center justify-center h-full bg-[#0B1120]",
          className
        )}
      >
        <div className="text-center text-white/30">
          <div className="relative mx-auto mb-4 w-16 h-16">
            <div className="absolute inset-0 bg-blue-500/20 blur-xl rounded-full animate-pulse" />
            <Sparkles className="relative w-16 h-16 text-blue-400/50" />
          </div>
          <p className="text-lg font-medium text-white/60">Constellation Empty</p>
          <p className="text-sm">Add nodes to begin mapping</p>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("h-full w-full bg-[#0B1120]", className)}>
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
        proOptions={{ hideAttribution: true }}
        className="bg-[#0B1120]"
      >
        <Background
          color="#1e293b"
          gap={32}
          size={2}
          className="bg-[#0B1120]"
        />
        <Controls
          showInteractive={false}
          className="!bg-white/5 !border-white/10 !fill-white/60 [&>button]:!border-b-white/10 hover:[&>button]:!bg-white/10"
        />
        <MiniMap
          nodeStrokeWidth={3}
          zoomable
          pannable
          className="!bg-white/5 !border-white/10 rounded-lg overflow-hidden"
          maskColor="rgba(11, 17, 32, 0.8)"
          nodeColor={(node) =>
            node.data.isSelected ? "#60a5fa" : "#1e3a8a"
          }
        />
      </ReactFlow>
    </div>
  )
}

// Wrap with ReactFlowProvider
export const GraphView = memo<GraphViewProps>(function GraphView(props) {
  return (
    <ReactFlowProvider>
      <GraphViewInner {...props} />
    </ReactFlowProvider>
  )
})
