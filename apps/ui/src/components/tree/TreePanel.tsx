'use client'

import React, {
  useState,
  useMemo,
  useCallback,
  useRef,
  useEffect,
  KeyboardEvent,
  FocusEvent
} from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronRight,
  ChevronDown,
  Search,
  Filter,
  ExpandAll,
  Minimize2,
  Info,
  AlertTriangle
} from 'lucide-react'
import { useTaxonomyStore } from '@/stores/taxonomy-store'
import { TreeNode } from './TreeNode'
import { VersionDropdown } from './VersionDropdown'
import { SearchFilters as SearchFiltersComponent } from './SearchFilters'
import { TreeMetrics } from './TreeMetrics'
import { cn } from '@/lib/utils'

interface TreePanelProps {
  className?: string
  showVersionDropdown?: boolean
  showMetrics?: boolean
  showFilters?: boolean
  compactMode?: boolean
  maxHeight?: number
}

export function TreePanel({
  className,
  showVersionDropdown = true,
  showMetrics = true,
  showFilters = true,
  compactMode = false,
  maxHeight = 600
}: TreePanelProps) {
  const {
    tree,
    versions,
    currentVersion,
    loading,
    error,
    expandedNodes,
    selectedNode,
    focusedIndex,
    searchQuery,
    filters,
    filteredNodes,
    updateMetrics,
    toggleNode,
    selectNode,
    setFocusedIndex,
    setSearchQuery,
    expandAll,
    collapseAll,
    getNodeById
  } = useTaxonomyStore()

  const [showFiltersPanel, setShowFiltersPanel] = useState(false)
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery)
  const [searchDebounceTimer, setSearchDebounceTimer] = useState<NodeJS.Timeout | null>(null)

  const parentRef = useRef<HTMLDivElement>(null)
  const treeRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Performance monitoring
  const renderStartTime = useRef<number>(0)

  // Virtual scrolling configuration
  const virtualizer = useVirtualizer({
    count: filteredNodes.length,
    getScrollElement: () => parentRef.current,
    estimateSize: useCallback(() => compactMode ? 28 : 36, [compactMode]),
    overscan: 10,
    measureElement: (element) => {
      return element?.getBoundingClientRect().height ?? (compactMode ? 28 : 36)
    }
  })

  // Performance metrics calculation
  useEffect(() => {
    if (renderStartTime.current > 0) {
      const renderTime = performance.now() - renderStartTime.current
      updateMetrics({
        render_time: renderTime,
        virtual_items_count: virtualizer.getVirtualItems().length,
        memory_usage: (performance as any).memory?.usedJSHeapSize || 0,
        fps: 60 // TODO: Implement actual FPS measurement
      })
    }
  }, [filteredNodes, updateMetrics, virtualizer])

  // Track render start time
  useEffect(() => {
    renderStartTime.current = performance.now()
  })

  // Debounced search
  useEffect(() => {
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer)
    }

    const timer = setTimeout(() => {
      setSearchQuery(localSearchQuery)
    }, 300)

    setSearchDebounceTimer(timer)

    return () => {
      if (timer) clearTimeout(timer)
    }
  }, [localSearchQuery, setSearchQuery])

  // Keyboard navigation
  const handleKeyDown = useCallback((event: KeyboardEvent<HTMLDivElement>) => {
    if (!filteredNodes.length) return

    const { key, ctrlKey, metaKey } = event
    const isModifierPressed = ctrlKey || metaKey

    switch (key) {
      case 'ArrowDown':
        event.preventDefault()
        setFocusedIndex(Math.min(focusedIndex + 1, filteredNodes.length - 1))
        break

      case 'ArrowUp':
        event.preventDefault()
        setFocusedIndex(Math.max(focusedIndex - 1, 0))
        break

      case 'ArrowRight':
        event.preventDefault()
        const currentNode = filteredNodes[focusedIndex]
        if (currentNode?.hasChildren && !expandedNodes.has(currentNode.node_id)) {
          toggleNode(currentNode.node_id)
        } else {
          setFocusedIndex(Math.min(focusedIndex + 1, filteredNodes.length - 1))
        }
        break

      case 'ArrowLeft':
        event.preventDefault()
        const focusedNode = filteredNodes[focusedIndex]
        if (focusedNode?.hasChildren && expandedNodes.has(focusedNode.node_id)) {
          toggleNode(focusedNode.node_id)
        } else if (focusedNode?.level > 0) {
          // Navigate to parent
          const parentIndex = filteredNodes.findIndex(node =>
            node.level === focusedNode.level - 1 &&
            node.index < focusedNode.index
          )
          if (parentIndex !== -1) {
            setFocusedIndex(parentIndex)
          }
        }
        break

      case 'Enter':
      case ' ':
        event.preventDefault()
        const activeNode = filteredNodes[focusedIndex]
        if (activeNode) {
          if (activeNode.hasChildren) {
            toggleNode(activeNode.node_id)
          }
          selectNode(activeNode.node_id)
        }
        break

      case 'Home':
        event.preventDefault()
        setFocusedIndex(0)
        break

      case 'End':
        event.preventDefault()
        setFocusedIndex(filteredNodes.length - 1)
        break

      case 'f':
        if (isModifierPressed) {
          event.preventDefault()
          searchInputRef.current?.focus()
        }
        break

      case 'e':
        if (isModifierPressed) {
          event.preventDefault()
          expandAll()
        }
        break

      case 'c':
        if (isModifierPressed) {
          event.preventDefault()
          collapseAll()
        }
        break
    }
  }, [filteredNodes, focusedIndex, expandedNodes, setFocusedIndex, toggleNode, selectNode, expandAll, collapseAll])

  // Auto-scroll to focused item
  useEffect(() => {
    if (focusedIndex >= 0 && focusedIndex < virtualizer.getVirtualItems().length) {
      virtualizer.scrollToIndex(focusedIndex, { align: 'auto' })
    }
  }, [focusedIndex, virtualizer])

  // Focus management
  const handleFocus = useCallback((event: FocusEvent<HTMLDivElement>) => {
    if (!filteredNodes[focusedIndex]) {
      setFocusedIndex(0)
    }
  }, [filteredNodes, focusedIndex, setFocusedIndex])

  const selectedNodeData = selectedNode ? getNodeById(selectedNode) : null

  if (loading) {
    return (
      <div className={cn("flex flex-col", className)}>
        <div className="flex items-center justify-center h-64" role="status" aria-label="Loading taxonomy tree">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <span className="ml-3 text-muted-foreground">Loading taxonomy tree...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn("flex flex-col", className)}>
        <div className="flex items-center justify-center h-64 text-destructive" role="alert">
          <AlertTriangle className="h-6 w-6 mr-2" />
          <span>Error loading taxonomy: {error}</span>
        </div>
      </div>
    )
  }

  if (!tree) {
    return (
      <div className={cn("flex flex-col", className)}>
        <div className="flex items-center justify-center h-64 text-muted-foreground" role="status">
          <Info className="h-6 w-6 mr-2" />
          <span>No taxonomy data available</span>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("flex flex-col bg-background border rounded-lg", className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold">Taxonomy Tree</h2>
          {showVersionDropdown && (
            <VersionDropdown
              versions={versions}
              currentVersion={currentVersion}
              loading={loading}
            />
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={expandAll}
            className="p-2 hover:bg-accent rounded-md"
            title="Expand All (Ctrl+E)"
            aria-label="Expand all nodes"
          >
            <ExpandAll className="h-4 w-4" />
          </button>
          <button
            onClick={collapseAll}
            className="p-2 hover:bg-accent rounded-md"
            title="Collapse All (Ctrl+C)"
            aria-label="Collapse all nodes"
          >
            <Minimize2 className="h-4 w-4" />
          </button>
          {showFilters && (
            <button
              onClick={() => setShowFiltersPanel(!showFiltersPanel)}
              className={cn(
                "p-2 hover:bg-accent rounded-md",
                showFiltersPanel && "bg-accent"
              )}
              title="Toggle Filters"
              aria-label="Toggle search filters"
            >
              <Filter className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Search */}
      <div className="p-4 border-b space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            ref={searchInputRef}
            type="text"
            placeholder="Search taxonomy nodes... (Ctrl+F)"
            value={localSearchQuery}
            onChange={(e) => setLocalSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            aria-label="Search taxonomy nodes"
          />
        </div>

        <AnimatePresence>
          {showFiltersPanel && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <SearchFiltersComponent />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Metrics */}
      {showMetrics && (
        <TreeMetrics
          totalNodes={tree.total_nodes}
          visibleNodes={filteredNodes.length}
          expandedCount={expandedNodes.size}
          selectedNode={selectedNodeData}
        />
      )}

      {/* Tree */}
      <div className="flex-1 overflow-hidden">
        <div
          ref={treeRef}
          className="h-full focus:outline-none focus:ring-2 focus:ring-primary focus:ring-inset"
          role="tree"
          aria-label="Taxonomy tree"
          tabIndex={0}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          style={{ maxHeight }}
        >
          <div ref={parentRef} className="h-full overflow-auto">
            <div
              style={{
                height: `${virtualizer.getTotalSize()}px`,
                width: '100%',
                position: 'relative',
              }}
            >
              {virtualizer.getVirtualItems().map((virtualItem) => {
                const node = filteredNodes[virtualItem.index]
                if (!node) return null

                return (
                  <TreeNode
                    key={node.node_id}
                    node={node}
                    level={node.level}
                    expanded={expandedNodes.has(node.node_id)}
                    hasChildren={node.hasChildren}
                    selected={selectedNode === node.node_id}
                    focused={focusedIndex === virtualItem.index}
                    onToggle={toggleNode}
                    onSelect={selectNode}
                    compactMode={compactMode}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: `${virtualItem.size}px`,
                      transform: `translateY(${virtualItem.start}px)`,
                    }}
                    // Accessibility
                    role="treeitem"
                    ariaExpanded={node.hasChildren ? expandedNodes.has(node.node_id) : undefined}
                    ariaLevel={node.level + 1}
                    ariaSelected={selectedNode === node.node_id}
                    ariaSetSize={filteredNodes.length}
                    ariaPosInSet={virtualItem.index + 1}
                  />
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Selected Node Info */}
      {selectedNodeData && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="border-t p-4 bg-accent/50"
        >
          <div className="space-y-2">
            <h4 className="font-medium text-sm">Selected Node</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Label:</span>
                <p className="font-medium">{selectedNodeData.label}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Confidence:</span>
                <p className="font-medium">{(selectedNodeData.confidence * 100).toFixed(1)}%</p>
              </div>
              <div className="col-span-2">
                <span className="text-muted-foreground">Path:</span>
                <p className="font-medium">{selectedNodeData.canonical_path.join(' → ')}</p>
              </div>
              {selectedNodeData.document_count !== undefined && (
                <div>
                  <span className="text-muted-foreground">Documents:</span>
                  <p className="font-medium">{selectedNodeData.document_count}</p>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* Empty state */}
      {filteredNodes.length === 0 && (searchQuery || Object.keys(filters).length > 0) && (
        <div className="flex items-center justify-center h-32 text-muted-foreground">
          <div className="text-center">
            <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No nodes found matching your search criteria</p>
            <button
              onClick={() => {
                setLocalSearchQuery('')
                setSearchQuery('')
              }}
              className="text-primary hover:underline text-sm mt-1"
            >
              Clear search
            </button>
          </div>
        </div>
      )}
    </div>
  )
}