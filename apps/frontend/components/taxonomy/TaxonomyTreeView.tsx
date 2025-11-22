/**
 * TaxonomyTreeView component - optimized for 500+ nodes with performance monitoring
 * Tab navigation order: Search Filter -> Layout Toggle -> Zoom Controls -> Nodes -> Detail Panel
 * Arrow key navigation: integrated with keyboard mode management
 * Keyboard shortcuts: /, +/=, -, L, Home, ?
 *
 * @CODE:FRONTEND-MIGRATION-001
 */

"use client"

import { useCallback, useMemo, useState, useEffect } from "react"
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  type Edge,
  type NodeMouseHandler,
} from "@xyflow/react"
import { useQuery } from "@tanstack/react-query"
import { fetchTaxonomyTree } from "@/lib/api/taxonomy"
import type { TaxonomyNode } from "@/lib/api/types"
import TaxonomyNodeComponent from "./TaxonomyNode"
import TaxonomyEdgeComponent from "./TaxonomyEdge"
import TaxonomyDetailPanel from "./TaxonomyDetailPanel"
import TaxonomySearchFilter from "./TaxonomySearchFilter"
import TaxonomyLayoutToggle from "./TaxonomyLayoutToggle"
import KeyboardShortcutsModal from "./KeyboardShortcutsModal"
import { applyLayout, type LayoutType } from "./taxonomyLayouts"
import { useArrowKeyNavigation } from "@/hooks/useArrowKeyNavigation"
import { useFocusManagement } from "@/hooks/useFocusManagement"
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts"
import { useTaxonomyStore } from "@/stores/useTaxonomyStore"
import type { FlowNode } from "@/lib/utils/findAdjacentNode"
import "@xyflow/react/dist/style.css"

function convertTaxonomyToFlow(
  taxonomyNode: TaxonomyNode
): { nodes: FlowNode[]; edges: Edge[] } {
  const nodes: FlowNode[] = []
  const edges: Edge[] = []

  function traverse(node: TaxonomyNode) {
    nodes.push({
      id: node.id,
      type: "taxonomyNode",
      position: { x: 0, y: 0 }, // Will be calculated by Dagre
      data: {
        taxonomyNode: node,
        isExpanded: true,
      },
    })

    if (node.children) {
      for (const child of node.children) {
        edges.push({
          id: `${node.id}-${child.id}`,
          source: node.id,
          target: child.id,
          type: "taxonomyEdge",
        })
        traverse(child)
      }
    }
  }

  traverse(taxonomyNode)
  return { nodes, edges }
}

const nodeTypes = {
  taxonomyNode: TaxonomyNodeComponent,
}

const edgeTypes = {
  taxonomyEdge: TaxonomyEdgeComponent,
}

export default function TaxonomyTreeView() {
  const [selectedNode, setSelectedNode] = useState<TaxonomyNode | null>(null)
  const [showPerformanceWarning, setShowPerformanceWarning] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [currentLayout, setCurrentLayout] = useState<LayoutType>("tree")
  const [showHelpModal, setShowHelpModal] = useState(false)

  // Focus management hooks
  const { focusedNodeId, setFocus } = useFocusManagement()
  const keyboardMode = useTaxonomyStore((state) => state.keyboardMode)

  // ReactFlow zoom controls
  const { zoomIn, zoomOut } = useReactFlow()

  const {
    data: taxonomyData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["taxonomy", "tree"],
    queryFn: () => fetchTaxonomyTree(),
    staleTime: 5 * 60 * 1000,
    retry: 3,
  })

  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!taxonomyData) {
      return { nodes: [], edges: [] }
    }

    const startTime = performance.now()
    const { nodes, edges } = convertTaxonomyToFlow(taxonomyData)
    // eslint-disable-next-line
    const layoutedNodes = applyLayout(nodes as any, edges, currentLayout)
    const endTime = performance.now()

    // Log performance metrics for large graphs
    if (nodes.length > 100) {
      console.log(
        `[TaxonomyTreeView] Processed ${nodes.length} nodes with ${currentLayout} layout in ${Math.round(endTime - startTime)}ms`
      )
    }

    // Show warning for very large graphs
    if (nodes.length > 500) {
      setShowPerformanceWarning(true)
    }

    return { nodes: layoutedNodes as FlowNode[], edges }
  }, [taxonomyData, currentLayout])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)

  // Arrow key navigation - only enabled in navigation mode
  useArrowKeyNavigation(
    keyboardMode === "navigation" ? (nodes as FlowNode[]) : [],
    currentLayout
  )

  // Monitor node count
  useEffect(() => {
    if (nodes.length > 500) {
      console.warn(
        `[TaxonomyTreeView] Rendering ${nodes.length} nodes - performance may be impacted`
      )
    }
  }, [nodes.length])

  // Search and highlight logic
  const matchCount = useMemo(() => {
    if (!searchQuery) return 0
    const query = searchQuery.toLowerCase()
    return nodes.filter((node) => {
      const flowNode = node as FlowNode
      return flowNode.data.taxonomyNode.name.toLowerCase().includes(query)
    }).length
  }, [nodes, searchQuery])

  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query)
  }, [])

  const handleLayoutChange = useCallback((newLayout: LayoutType) => {
    setCurrentLayout(newLayout)
  }, [])

  // Keyboard shortcut handlers
  const handleZoomIn = useCallback(() => zoomIn(), [zoomIn])
  const handleZoomOut = useCallback(() => zoomOut(), [zoomOut])
  const handleToggleLayout = useCallback(() => {
    const newLayout = currentLayout === "tree" ? "radial" : "tree"
    setCurrentLayout(newLayout)
  }, [currentLayout])
  const handleShowHelp = useCallback(() => setShowHelpModal(true), [])
  const handleCloseHelp = useCallback(() => setShowHelpModal(false), [])

  // Get root node ID for Home shortcut
  const rootNodeId = useMemo(() => {
    const rootNode = nodes.find((node) => {
      const taxonomyNode = (node as FlowNode).data.taxonomyNode
      return !taxonomyNode.parent_id || taxonomyNode.level === 0
    })
    return rootNode?.id
  }, [nodes])

  // Initialize keyboard shortcuts
  useKeyboardShortcuts({
    onZoomIn: handleZoomIn,
    onZoomOut: handleZoomOut,
    onToggleLayout: handleToggleLayout,
    onShowHelp: handleShowHelp,
    rootNodeId,
  })

  // Update node styles based on search
  useEffect(() => {
    if (!searchQuery) {
      // Reset all nodes to default style
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          style: undefined,
        }))
      )
      return
    }

    const query = searchQuery.toLowerCase()
    setNodes((nds) =>
      nds.map((node) => {
        const flowNode = node as FlowNode
        const isMatch = flowNode.data.taxonomyNode.name.toLowerCase().includes(query)
        return {
          ...node,
          style: isMatch
            ? {
                backgroundColor: "#fef3c7", // yellow-100
                border: "2px solid #f59e0b", // yellow-500
              }
            : {
                opacity: 0.3,
              },
        }
      })
    )
  }, [searchQuery, setNodes])

  // Programmatically focus node when focusedNodeId changes
  useEffect(() => {
    if (focusedNodeId) {
      // Use data-id attribute to find the node in the DOM
      const nodeElement = document.querySelector(
        `[data-id="${focusedNodeId}"] div[role="button"]`
      ) as HTMLDivElement

      if (nodeElement) {
        nodeElement.focus()
      }
    }
  }, [focusedNodeId])

  const onNodeClick: NodeMouseHandler = useCallback(
    (_, node) => {
      const flowNode = node as FlowNode
      setSelectedNode(flowNode.data.taxonomyNode)
      setFocus(flowNode.id)
    },
    [setFocus]
  )

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  const handleCloseDetailPanel = useCallback(() => {
    setSelectedNode(null)
  }, [])

  const onInit = useCallback(() => {
    // React Flow initialization callback
  }, [])

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-gray-500">Loading taxonomy tree...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-red-500">Error loading taxonomy: {error.message}</p>
      </div>
    )
  }

  return (
    <div className="relative h-full w-full">
      {/* Search Filter */}
      <TaxonomySearchFilter onSearch={handleSearch} matchCount={matchCount} />

      {/* Layout Toggle */}
      <TaxonomyLayoutToggle
        currentLayout={currentLayout}
        onLayoutChange={handleLayoutChange}
      />

      {/* Performance Warning Banner */}
      {showPerformanceWarning && (
        <div className="absolute left-1/2 top-4 z-20 -translate-x-1/2 transform">
          <div className="flex items-center gap-2 rounded-lg border border-yellow-300 bg-yellow-50 px-4 py-2 shadow-lg">
            <svg
              className="h-5 w-5 text-yellow-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <p className="text-sm text-yellow-800">
              Large taxonomy ({nodes.length} nodes) - zoom and pan performance may be affected
            </p>
            <button
              onClick={() => setShowPerformanceWarning(false)}
              className="ml-2 text-yellow-600 hover:text-yellow-800"
              aria-label="Dismiss warning"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      )}

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        onInit={onInit}
        fitView
        minZoom={0.1}
        maxZoom={2}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
      >
        <Background />
        <Controls />
        <MiniMap nodeStrokeWidth={3} zoomable pannable />
      </ReactFlow>
      <TaxonomyDetailPanel node={selectedNode} onClose={handleCloseDetailPanel} />
      <KeyboardShortcutsModal isOpen={showHelpModal} onClose={handleCloseHelp} />
    </div>
  )
}
