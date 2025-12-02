/**
 * Constellation Graph Component
 *
 * Main container for taxonomy constellation visualization with:
 * - Radial node layout
 * - Animated energy beam edges
 * - Zoom and pan controls
 * - Node selection and interaction
 *
 * Design Reference: 뉴디자인2.png
 * @CODE:FRONTEND-REDESIGN-001-GRAPH
 */

"use client"

import { useState, useCallback, useRef, useMemo } from "react"
import ConstellationNode from "./ConstellationNode"
import ConstellationEdge from "./ConstellationEdge"
import ConstellationControlPanel from "./ConstellationControlPanel"
import type { TaxonomyNode } from "@/lib/api/types"

interface Position {
  x: number
  y: number
}

interface Edge {
  id: string
  source: string
  target: string
  strength?: number
}

interface ConstellationGraphProps {
  nodes: TaxonomyNode[]
  edges: Edge[]
  onNodeSelect?: (node: TaxonomyNode) => void
  isLoading?: boolean
}

// Calculate radial layout positions
const calculateRadialLayout = (nodes: TaxonomyNode[], centerX: number, centerY: number): Map<string, Position> => {
  const positions = new Map<string, Position>()

  if (nodes.length === 0) {
    return positions
  }

  // Root node in center
  const root = nodes.find(n => n.level === 1)
  if (root) {
    positions.set(root.id, { x: centerX - 40, y: centerY - 40 })
  }

  // Level 2 nodes in first ring
  const level2Nodes = nodes.filter(n => n.level === 2)
  const radius2 = 200
  level2Nodes.forEach((node, index) => {
    const angle = (index / level2Nodes.length) * Math.PI * 2
    positions.set(node.id, {
      x: centerX + Math.cos(angle) * radius2 - 32,
      y: centerY + Math.sin(angle) * radius2 - 32
    })
  })

  // Level 3+ nodes in outer rings
  const level3Plus = nodes.filter(n => n.level >= 3)
  const radius3 = 350
  level3Plus.forEach((node, index) => {
    const angle = (index / level3Plus.length) * Math.PI * 2
    positions.set(node.id, {
      x: centerX + Math.cos(angle) * radius3 - 24,
      y: centerY + Math.sin(angle) * radius3 - 24
    })
  })

  return positions
}

export default function ConstellationGraph({
  nodes,
  edges,
  onNodeSelect,
  isLoading = false
}: ConstellationGraphProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isPanning, setIsPanning] = useState(false)
  const [panStart, setPanStart] = useState({ x: 0, y: 0 })
  const [dataDensity, setDataDensity] = useState(50)

  const containerRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  // Calculate container dimensions
  const containerWidth = 1000
  const containerHeight = 800
  const centerX = containerWidth / 2
  const centerY = containerHeight / 2

  // Calculate node positions
  const nodePositions = useMemo(
    () => calculateRadialLayout(nodes, centerX, centerY),
    [nodes, centerX, centerY]
  )

  // Get selected node data
  const selectedNode = useMemo(
    () => nodes.find(n => n.id === selectedNodeId),
    [selectedNodeId, nodes]
  )

  // Handle node selection
  const handleNodeSelect = useCallback(
    (node: TaxonomyNode) => {
      setSelectedNodeId(node.id)
      onNodeSelect?.(node)
    },
    [onNodeSelect]
  )

  // Handle node hover
  const handleNodeHover = useCallback(
    (isHovered: boolean, node: TaxonomyNode) => {
      if (isHovered) {
        setHoveredNodeId(node.id)
      } else if (hoveredNodeId === node.id) {
        setHoveredNodeId(null)
      }
    },
    [hoveredNodeId]
  )

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    setZoom(prev => Math.min(prev * 1.2, 3))
  }, [])

  const handleZoomOut = useCallback(() => {
    setZoom(prev => Math.max(prev / 1.2, 0.2))
  }, [])

  // Reset view - prefixed with underscore since not currently used but kept for future
  const _handleResetView = useCallback(() => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
    setSelectedNodeId(null)
    setHoveredNodeId(null)
  }, [])

  // Filter and Settings handlers (for future implementation)
  const handleFilterClick = useCallback(() => {
    // TODO: Implement filter modal/drawer
    console.log("Filter clicked - density:", dataDensity)
  }, [dataDensity])

  const handleSettingsClick = useCallback(() => {
    // TODO: Implement settings modal/drawer
    console.log("Settings clicked")
  }, [])

  // Pan controls
  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (e.button === 0) {
      // Left mouse button only
      setIsPanning(true)
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
    }
  }, [pan])

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (isPanning) {
      setPan({
        x: e.clientX - panStart.x,
        y: e.clientY - panStart.y
      })
    }
  }, [isPanning, panStart])

  const handleMouseUp = useCallback(() => {
    setIsPanning(false)
  }, [])

  // Wheel scroll to zoom
  const handleWheel = useCallback((e: React.WheelEvent<HTMLDivElement>) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    setZoom(prev => Math.min(Math.max(prev * delta, 0.2), 3))
  }, [])

  // Edge visibility based on selection
  const getEdgeActive = useCallback(
    (edge: Edge): boolean => {
      if (!selectedNodeId) return true
      return edge.source === selectedNodeId || edge.target === selectedNodeId
    },
    [selectedNodeId]
  )

  // Edge styles - prefixed with underscore since not currently used
  const _edgeStyles = isLoading
    ? "opacity-50 pointer-events-none"
    : ""

  const transform = `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`

  return (
    <div
      data-testid="constellation-graph"
      ref={containerRef}
      className="space-background relative w-full h-full overflow-hidden rounded-2xl border border-white/10"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
      style={{ cursor: isPanning ? "grabbing" : "grab" }}
    >
      {/* Loading State */}
      {isLoading && (
        <div className="absolute inset-0 z-20 flex items-center justify-center backdrop-blur-sm">
          <div className="text-cyan-300 animate-pulse">Loading constellation...</div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && nodes.length === 0 && (
        <div className="absolute inset-0 z-20 flex items-center justify-center">
          <div className="text-center">
            <div className="text-lg text-cyan-300 mb-2">No taxonomy data</div>
            <div className="text-sm text-cyan-400/60">Create or load a taxonomy to begin</div>
          </div>
        </div>
      )}

      {/* Graph Content Container */}
      <div
        data-testid="constellation-graph-content"
        ref={contentRef}
        className="absolute inset-0"
        style={{
          transform: transform,
          transformOrigin: "0 0",
          transition: selectedNodeId ? "none" : "transform 0.3s ease"
        }}
      >
        {/* SVG Layer for Edges */}
        <svg
          className="absolute inset-0 pointer-events-none"
          width={containerWidth}
          height={containerHeight}
          viewBox={`0 0 ${containerWidth} ${containerHeight}`}
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Render edges */}
          {edges.map(edge => {
            const sourcePos = nodePositions.get(edge.source)
            const targetPos = nodePositions.get(edge.target)

            if (!sourcePos || !targetPos) return null

            return (
              <ConstellationEdge
                key={edge.id}
                source={sourcePos}
                target={targetPos}
                isActive={getEdgeActive(edge)}
                strength={edge.strength}
                edgeId={edge.id}
              />
            )
          })}
        </svg>

        {/* Node Layer */}
        <div className="absolute inset-0 pointer-events-none">
          {nodes.map(node => {
            const position = nodePositions.get(node.id)
            if (!position) return null

            return (
              <div key={node.id} className="pointer-events-auto">
                <ConstellationNode
                  node={node}
                  position={position}
                  isSelected={selectedNodeId === node.id}
                  isHovered={hoveredNodeId === node.id}
                  onClick={handleNodeSelect}
                  onHover={handleNodeHover}
                />
              </div>
            )
          })}
        </div>
      </div>

      {/* Constellation Control Panel - Bottom Left */}
      <ConstellationControlPanel
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onFilterClick={handleFilterClick}
        onSettingsClick={handleSettingsClick}
        dataDensity={dataDensity}
        onDataDensityChange={setDataDensity}
      />

      {/* Info Panel - Shows Selected Node Details */}
      {selectedNode && (
        <div className="absolute top-6 left-6 z-10 backdrop-blur-md bg-white/5 rounded-xl border border-cyan-400/20 p-4 max-w-sm">
          <div className="text-xs text-cyan-300 mb-2">SELECTED NODE</div>
          <div className="text-lg font-semibold text-cyan-100 mb-2">{selectedNode.name}</div>
          <div className="text-sm text-cyan-400/70 space-y-1">
            <div>Level: {selectedNode.level}</div>
            <div>Documents: {selectedNode.document_count ?? 0}</div>
            {selectedNode.children && selectedNode.children.length > 0 && (
              <div>Children: {selectedNode.children.length}</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
