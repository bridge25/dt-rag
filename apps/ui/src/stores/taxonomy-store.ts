'use client'

import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import {
  TaxonomyTree,
  TaxonomyNode,
  TreeViewState,
  SearchFilters,
  PerformanceMetrics
} from '@/types/taxonomy'

interface TaxonomyState extends TreeViewState {
  // Data
  tree: TaxonomyTree | null
  versions: string[]
  currentVersion: string
  loading: boolean
  error: string | null

  // Performance
  metrics: PerformanceMetrics | null

  // Computed values (memoized)
  flattenedNodes: Array<TaxonomyNode & { level: number; hasChildren: boolean; index: number }>
  filteredNodes: Array<TaxonomyNode & { level: number; hasChildren: boolean; index: number }>

  // Actions
  setTree: (tree: TaxonomyTree) => void
  setVersions: (versions: string[]) => void
  setCurrentVersion: (version: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void

  // Tree operations
  toggleNode: (nodeId: string) => void
  selectNode: (nodeId: string) => void
  setFocusedIndex: (index: number) => void
  expandAll: () => void
  collapseAll: () => void
  expandToNode: (nodeId: string) => void

  // Search and filtering
  setSearchQuery: (query: string) => void
  setFilters: (filters: SearchFilters) => void

  // Performance tracking
  updateMetrics: (metrics: Partial<PerformanceMetrics>) => void

  // Utility functions
  getNodeById: (nodeId: string) => TaxonomyNode | null
  getNodePath: (nodeId: string) => TaxonomyNode[]
  getChildNodes: (nodeId: string) => TaxonomyNode[]
  findNodesByQuery: (query: string) => TaxonomyNode[]
}

const createFlattenedNodes = (
  tree: TaxonomyTree | null,
  expandedNodes: Set<string>
): Array<TaxonomyNode & { level: number; hasChildren: boolean; index: number }> => {
  if (!tree) return []

  const nodeMap = new Map<string, TaxonomyNode>()
  const childrenMap = new Map<string, string[]>()

  // Build maps for efficient access
  tree.nodes.forEach(node => {
    nodeMap.set(node.node_id, node)
  })

  tree.edges.forEach(edge => {
    const children = childrenMap.get(edge.parent) || []
    children.push(edge.child)
    childrenMap.set(edge.parent, children)
  })

  // Find root nodes
  const rootNodes = tree.nodes.filter(node =>
    !tree.edges.some(edge => edge.child === node.node_id)
  )

  let globalIndex = 0

  const flattenTree = (nodeId: string, level: number): Array<TaxonomyNode & { level: number; hasChildren: boolean; index: number }> => {
    const node = nodeMap.get(nodeId)
    if (!node) return []

    const children = childrenMap.get(nodeId) || []
    const hasChildren = children.length > 0
    const isExpanded = expandedNodes.has(nodeId)

    const flatNode = {
      ...node,
      level,
      hasChildren,
      index: globalIndex++
    }

    const result = [flatNode]

    if (isExpanded && hasChildren) {
      children.forEach(childId => {
        result.push(...flattenTree(childId, level + 1))
      })
    }

    return result
  }

  return rootNodes.flatMap(node => flattenTree(node.node_id, 0))
}

const filterNodes = (
  nodes: Array<TaxonomyNode & { level: number; hasChildren: boolean; index: number }>,
  searchQuery: string,
  filters: SearchFilters
): Array<TaxonomyNode & { level: number; hasChildren: boolean; index: number }> => {
  let filtered = nodes

  // Text search
  if (searchQuery.trim()) {
    const query = searchQuery.toLowerCase()
    filtered = filtered.filter(node =>
      node.label.toLowerCase().includes(query) ||
      node.canonical_path.some(part => part.toLowerCase().includes(query)) ||
      node.description?.toLowerCase().includes(query)
    )
  }

  // Confidence filter
  if (filters.confidence_min !== undefined) {
    filtered = filtered.filter(node => node.confidence >= filters.confidence_min!)
  }
  if (filters.confidence_max !== undefined) {
    filtered = filtered.filter(node => node.confidence <= filters.confidence_max!)
  }

  // Document count filter
  if (filters.document_count_min !== undefined) {
    filtered = filtered.filter(node =>
      (node.document_count || 0) >= filters.document_count_min!
    )
  }

  // Has children filter
  if (filters.has_children !== undefined) {
    filtered = filtered.filter(node => node.hasChildren === filters.has_children)
  }

  // Depth filter
  if (filters.depth_max !== undefined) {
    filtered = filtered.filter(node => node.level <= filters.depth_max!)
  }

  // Canonical path filter
  if (filters.canonical_in?.length) {
    filtered = filtered.filter(node =>
      filters.canonical_in!.some(path =>
        path.every((segment, index) =>
          node.canonical_path[index]?.toLowerCase() === segment.toLowerCase()
        )
      )
    )
  }

  return filtered
}

export const useTaxonomyStore = create<TaxonomyState>()(
  devtools(
    (set, get) => ({
      // Initial state
      tree: null,
      versions: [],
      currentVersion: 'latest',
      loading: false,
      error: null,
      expandedNodes: new Set(),
      selectedNode: null,
      focusedIndex: 0,
      searchQuery: '',
      filters: {},
      metrics: null,
      flattenedNodes: [],
      filteredNodes: [],

      // Actions
      setTree: (tree) => {
        const state = get()
        const flattenedNodes = createFlattenedNodes(tree, state.expandedNodes)
        const filteredNodes = filterNodes(flattenedNodes, state.searchQuery, state.filters)

        set({
          tree,
          flattenedNodes,
          filteredNodes,
          error: null
        })
      },

      setVersions: (versions) => set({ versions }),
      setCurrentVersion: (currentVersion) => set({ currentVersion }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),

      toggleNode: (nodeId) => {
        const state = get()
        const newExpandedNodes = new Set(state.expandedNodes)

        if (newExpandedNodes.has(nodeId)) {
          newExpandedNodes.delete(nodeId)
        } else {
          newExpandedNodes.add(nodeId)
        }

        const flattenedNodes = createFlattenedNodes(state.tree, newExpandedNodes)
        const filteredNodes = filterNodes(flattenedNodes, state.searchQuery, state.filters)

        set({
          expandedNodes: newExpandedNodes,
          flattenedNodes,
          filteredNodes
        })
      },

      selectNode: (selectedNode) => set({ selectedNode }),
      setFocusedIndex: (focusedIndex) => set({ focusedIndex }),

      expandAll: () => {
        const state = get()
        if (!state.tree) return

        const allNodeIds = new Set(state.tree.nodes.map(node => node.node_id))
        const flattenedNodes = createFlattenedNodes(state.tree, allNodeIds)
        const filteredNodes = filterNodes(flattenedNodes, state.searchQuery, state.filters)

        set({
          expandedNodes: allNodeIds,
          flattenedNodes,
          filteredNodes
        })
      },

      collapseAll: () => {
        const state = get()
        const expandedNodes = new Set<string>()
        const flattenedNodes = createFlattenedNodes(state.tree, expandedNodes)
        const filteredNodes = filterNodes(flattenedNodes, state.searchQuery, state.filters)

        set({
          expandedNodes,
          flattenedNodes,
          filteredNodes
        })
      },

      expandToNode: (nodeId) => {
        const state = get()
        if (!state.tree) return

        const path = get().getNodePath(nodeId)
        const newExpandedNodes = new Set(state.expandedNodes)

        path.forEach(node => {
          newExpandedNodes.add(node.node_id)
        })

        const flattenedNodes = createFlattenedNodes(state.tree, newExpandedNodes)
        const filteredNodes = filterNodes(flattenedNodes, state.searchQuery, state.filters)

        set({
          expandedNodes: newExpandedNodes,
          flattenedNodes,
          filteredNodes
        })
      },

      setSearchQuery: (searchQuery) => {
        const state = get()
        const filteredNodes = filterNodes(state.flattenedNodes, searchQuery, state.filters)

        set({
          searchQuery,
          filteredNodes
        })
      },

      setFilters: (filters) => {
        const state = get()
        const filteredNodes = filterNodes(state.flattenedNodes, state.searchQuery, filters)

        set({
          filters,
          filteredNodes
        })
      },

      updateMetrics: (newMetrics) => {
        const state = get()
        set({
          metrics: {
            ...state.metrics,
            ...newMetrics,
            last_measured: new Date().toISOString()
          } as PerformanceMetrics
        })
      },

      // Utility functions
      getNodeById: (nodeId) => {
        const state = get()
        return state.tree?.nodes.find(node => node.node_id === nodeId) || null
      },

      getNodePath: (nodeId) => {
        const state = get()
        if (!state.tree) return []

        const path: TaxonomyNode[] = []
        const nodeMap = new Map(state.tree.nodes.map(node => [node.node_id, node]))
        const parentMap = new Map<string, string>()

        state.tree.edges.forEach(edge => {
          parentMap.set(edge.child, edge.parent)
        })

        let currentId: string | undefined = nodeId
        while (currentId && nodeMap.has(currentId)) {
          const node = nodeMap.get(currentId)!
          path.unshift(node)
          currentId = parentMap.get(currentId)
        }

        return path
      },

      getChildNodes: (nodeId) => {
        const state = get()
        if (!state.tree) return []

        const childIds = state.tree.edges
          .filter(edge => edge.parent === nodeId)
          .map(edge => edge.child)

        return state.tree.nodes.filter(node => childIds.includes(node.node_id))
      },

      findNodesByQuery: (query) => {
        const state = get()
        if (!state.tree || !query.trim()) return []

        const searchQuery = query.toLowerCase()
        return state.tree.nodes.filter(node =>
          node.label.toLowerCase().includes(searchQuery) ||
          node.canonical_path.some(part => part.toLowerCase().includes(searchQuery)) ||
          node.description?.toLowerCase().includes(searchQuery)
        )
      }
    }),
    {
      name: 'taxonomy-store'
    }
  )
)