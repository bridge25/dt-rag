"use client"

/**
 * GraphView - ReactFlow-based graph visualization for TaxonomyBuilder
 *
 * @CODE:TAXONOMY-BUILDER-001
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
import { Folder } from "lucide-react"
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
      <div
        className={cn(
          "px-4 py-2 rounded-lg border-2 bg-white dark:bg-gray-800 shadow-md min-w-[120px]",
          "transition-all duration-150",
          isSelected
            ? "border-blue-500 ring-2 ring-blue-200 dark:ring-blue-800"
            : "border-gray-200 dark:border-gray-600 hover:border-blue-300"
        )}
      >
        <Handle type="target" position={Position.Top} className="!bg-gray-400" />

        <div className="flex items-center gap-2">
          <Folder className="w-4 h-4 text-amber-500 flex-shrink-0" />
          <span className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-[100px]">
            {node.name}
          </span>
        </div>

        {documentsCount > 0 && (
          <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {documentsCount} docs
          </div>
        )}

        <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
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
  g.setGraph({ rankdir: "TB", nodesep: 50, ranksep: 80 })

  flowNodes.forEach((node) => {
    g.setNode(node.id, { width: 150, height: 60 })
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
        x: nodeWithPosition.x - 75,
        y: nodeWithPosition.y - 30,
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
        animated: false,
        style: { stroke: "#94a3b8", strokeWidth: 2 },
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
          "flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900",
          className
        )}
      >
        <div className="text-center text-gray-500 dark:text-gray-400">
          <Folder className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>No nodes to visualize</p>
          <p className="text-sm">Add nodes to see the graph view</p>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("h-full w-full", className)}>
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
      >
        <Background color="#e2e8f0" gap={16} />
        <Controls showInteractive={false} />
        <MiniMap
          nodeStrokeWidth={3}
          zoomable
          pannable
          nodeColor={(node) =>
            node.data.isSelected ? "#3b82f6" : "#f59e0b"
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
