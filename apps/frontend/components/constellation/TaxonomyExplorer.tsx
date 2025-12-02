/**
 * Taxonomy Explorer Component
 *
 * Full-page interface for exploring taxonomy constellation with:
 * - Main constellation visualization
 * - Detailed sidebar with selected node information
 * - Breadcrumb navigation
 * - Search and filtering
 *
 * Design Reference: 뉴디자인2.png
 * @CODE:FRONTEND-REDESIGN-001-EXPLORER
 */

"use client"

import { useState, useCallback, useMemo, useEffect } from "react"
import ConstellationGraph from "./ConstellationGraph"
import { X, ChevronRight } from "lucide-react"
import type { TaxonomyNode } from "@/lib/api/types"

interface TaxonomyExplorerProps {
  taxonomy: TaxonomyNode[]
  onClose?: () => void
}

interface Edge {
  id: string
  source: string
  target: string
  strength?: number
}

// Build edges from parent-child relationships
const buildEdgesFromTaxonomy = (nodes: TaxonomyNode[]): Edge[] => {
  const edges: Edge[] = []
  const usedIds = new Set<string>()

  const processNode = (node: TaxonomyNode) => {
    if (node.children && node.children.length > 0) {
      node.children.forEach((child, index) => {
        const edgeId = `edge-${node.id}-${child.id}-${index}`
        if (!usedIds.has(edgeId)) {
          usedIds.add(edgeId)
          edges.push({
            id: edgeId,
            source: node.id,
            target: child.id,
            strength: 0.8
          })
        }

        // Recursively process children
        if (child.children) {
          processNode(child as TaxonomyNode)
        }
      })
    }
  }

  nodes.forEach(processNode)

  return edges
}

// Flatten nested taxonomy into flat array
const flattenTaxonomy = (nodes: TaxonomyNode[]): TaxonomyNode[] => {
  const result: TaxonomyNode[] = []

  const process = (node: TaxonomyNode) => {
    result.push(node)
    if (node.children) {
      node.children.forEach(child => process(child as TaxonomyNode))
    }
  }

  nodes.forEach(process)
  return result
}

export default function TaxonomyExplorer({ taxonomy, onClose }: TaxonomyExplorerProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose?.()
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [onClose])

  // Flatten taxonomy for graph
  const flatNodes = useMemo(() => flattenTaxonomy(taxonomy), [taxonomy])

  // Filter nodes based on search term
  const filteredNodes = useMemo(() => {
    if (!searchTerm) {
      return flatNodes
    }

    const term = searchTerm.toLowerCase()
    return flatNodes.filter(
      node =>
        node.name.toLowerCase().includes(term) ||
        node.path.some(p => p.toLowerCase().includes(term))
    )
  }, [flatNodes, searchTerm])

  // Build edges from taxonomy
  const edges = useMemo(() => buildEdgesFromTaxonomy(filteredNodes), [filteredNodes])

  // Get selected node data
  const selectedNode = useMemo(
    () => flatNodes.find(n => n.id === selectedNodeId),
    [selectedNodeId, flatNodes]
  )

  // Build breadcrumb path
  const breadcrumbs = useMemo(() => {
    if (!selectedNode) return []
    return selectedNode.path.map(name => ({
      label: name,
      node: flatNodes.find(n => n.name === name)
    }))
  }, [selectedNode, flatNodes])

  // Handle node selection
  const handleNodeSelect = useCallback((node: TaxonomyNode) => {
    setSelectedNodeId(node.id)
  }, [])

  // Handle breadcrumb click
  const handleBreadcrumbClick = useCallback(
    (nodeId: string | undefined) => {
      if (nodeId) {
        setSelectedNodeId(nodeId)
      }
    },
    []
  )

  // Handle search clear
  const handleClearSearch = useCallback(() => {
    setSearchTerm("")
  }, [])

  return (
    <div
      data-testid="taxonomy-explorer"
      className="fixed inset-0 z-50 grid grid-cols-1 lg:grid-cols-3 gap-4 p-4 bg-black/80 backdrop-blur-sm"
    >
      {/* Main Graph Section */}
      <div className="lg:col-span-2 h-full">
        <div className="relative h-full rounded-2xl overflow-hidden border border-white/10">
          <ConstellationGraph
            nodes={filteredNodes}
            edges={edges}
            onNodeSelect={handleNodeSelect}
          />

          {/* Search Bar - Overlay on top */}
          <div className="absolute top-6 left-6 right-6 z-20 flex gap-2">
            <input
              type="text"
              placeholder="Search taxonomy..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="flex-1 px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-cyan-400 transition-all"
              aria-label="Search taxonomy nodes"
            />
            {searchTerm && (
              <button
                aria-label="Clear search"
                onClick={handleClearSearch}
                className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Sidebar Section */}
      <div
        data-testid="explorer-sidebar"
        className="h-full flex flex-col rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <h2 className="text-lg font-semibold text-white">Node Details</h2>
          <button
            aria-label="Close explorer"
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors text-cyan-300"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {selectedNode ? (
            <div className="space-y-6">
              {/* Breadcrumb */}
              <div
                data-testid="breadcrumb-navigation"
                className="flex flex-wrap items-center gap-2 text-sm"
              >
                {breadcrumbs.map((crumb, index) => (
                  <div key={index} className="flex items-center gap-2">
                    {index > 0 && <ChevronRight size={16} className="text-white/30" />}
                    {crumb.node ? (
                      <button
                        onClick={() => handleBreadcrumbClick(crumb.node?.id)}
                        className="text-cyan-400 hover:text-cyan-300 transition-colors truncate"
                      >
                        {crumb.label}
                      </button>
                    ) : (
                      <span className="text-white/60">{crumb.label}</span>
                    )}
                  </div>
                ))}
              </div>

              {/* Node Name */}
              <div>
                <div className="text-xs text-cyan-300 uppercase tracking-wider mb-1">
                  Selected Node
                </div>
                <h3 className="text-2xl font-bold text-white">{selectedNode.name}</h3>
              </div>

              {/* Basic Info */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-white/60">Level:</span>
                  <span className="text-white font-semibold">{selectedNode.level}</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-white/60">Documents:</span>
                  <span className="text-white font-semibold">{selectedNode.document_count ?? 0}</span>
                </div>

                {selectedNode.children && selectedNode.children.length > 0 && (
                  <div className="flex justify-between items-center">
                    <span className="text-white/60">Subcategories:</span>
                    <span className="text-white font-semibold">{selectedNode.children.length}</span>
                  </div>
                )}
              </div>

              {/* Children List */}
              {selectedNode.children && selectedNode.children.length > 0 && (
                <div>
                  <div className="text-xs text-cyan-300 uppercase tracking-wider mb-3">
                    Child Categories
                  </div>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {selectedNode.children.map((child: any) => (
                      <button
                        key={child.id}
                        onClick={() => handleBreadcrumbClick(child.id)}
                        className="block w-full text-left px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                      >
                        <div className="text-sm font-medium text-white truncate">
                          {child.name}
                        </div>
                        <div className="text-xs text-white/50">
                          {child.document_count ?? 0} documents
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Metadata */}
              {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
                <div>
                  <div className="text-xs text-cyan-300 uppercase tracking-wider mb-3">
                    Metadata
                  </div>
                  <div className="space-y-2">
                    {Object.entries(selectedNode.metadata).map(([key, value]) => (
                      <div key={key} className="text-sm">
                        <div className="text-white/60 capitalize">{key}:</div>
                        <div className="text-white break-words">
                          {typeof value === "string" ? value : JSON.stringify(value)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-center">
              <div>
                <div className="text-lg text-cyan-300 mb-2">Select a Node</div>
                <div className="text-sm text-white/50">Click on a node in the constellation to view details</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Close on background click */}
      <div
        className="fixed inset-0 -z-10"
        onClick={onClose}
        role="presentation"
      />
    </div>
  )
}
