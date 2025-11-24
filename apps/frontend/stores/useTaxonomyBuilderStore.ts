"use client"

/**
 * Zustand store for Taxonomy Builder state management
 *
 * @CODE:TAXONOMY-BUILDER-001
 */

import { create } from "zustand"
import { immer } from "zustand/middleware/immer"
import { enableMapSet } from "immer"
import type {
  TaxonomyNode,
  TaxonomyAction,
  ViewMode,
  TaxonomyBuilderStore,
} from "@/components/taxonomy-builder/types"

// Enable immer MapSet plugin for Map/Set support
enableMapSet()

const generateId = () => `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

const createAction = (
  type: TaxonomyAction["type"],
  nodeId: string,
  payload: Partial<TaxonomyNode> | null,
  previousState: Partial<TaxonomyNode> | null
): TaxonomyAction => ({
  type,
  nodeId,
  payload,
  previousState,
  timestamp: Date.now(),
})

const detectCycle = (
  nodes: Map<string, TaxonomyNode>,
  nodeId: string,
  newParentId: string | null
): boolean => {
  if (newParentId === null) return false
  if (newParentId === nodeId) return true

  let currentId: string | null = newParentId
  const visited = new Set<string>()

  while (currentId !== null) {
    if (visited.has(currentId)) return true
    if (currentId === nodeId) return true
    visited.add(currentId)

    const current = nodes.get(currentId)
    currentId = current?.parentId ?? null
  }

  return false
}

export const useTaxonomyBuilderStore = create<TaxonomyBuilderStore>()(
  immer((set, get) => ({
    // Initial state
    nodes: new Map(),
    selectedNodeId: null,
    viewMode: "tree" as ViewMode,
    undoStack: [],
    redoStack: [],
    isDirty: false,
    isLoading: false,
    isSaving: false,
    lastSavedAt: null,
    error: null,

    // Node operations
    addNode: (nodeData) => {
      const id = generateId()
      const now = new Date().toISOString()

      const newNode: TaxonomyNode = {
        id,
        name: nodeData.name,
        description: nodeData.description,
        parentId: nodeData.parentId,
        children: [],
        metadata: {
          documentsCount: 0,
          createdAt: now,
          updatedAt: now,
          createdBy: "current_user",
        },
      }

      set((state) => {
        state.nodes.set(id, newNode)

        // Update parent's children array
        if (nodeData.parentId) {
          const parent = state.nodes.get(nodeData.parentId)
          if (parent) {
            parent.children.push(id)
          }
        }

        state.undoStack.push(createAction("add", id, newNode, null))
        state.redoStack = []
        state.isDirty = true
        state.selectedNodeId = id
      })

      return id
    },

    updateNode: (id, updates) => {
      const currentNode = get().nodes.get(id)
      if (!currentNode) return

      set((state) => {
        const node = state.nodes.get(id)
        if (!node) return

        const previousState = { ...node }
        Object.assign(node, updates, {
          metadata: {
            ...node.metadata,
            updatedAt: new Date().toISOString(),
          },
        })

        state.undoStack.push(createAction("update", id, updates, previousState))
        state.redoStack = []
        state.isDirty = true
      })
    },

    deleteNode: (id) => {
      const currentNode = get().nodes.get(id)
      if (!currentNode) return

      set((state) => {
        const node = state.nodes.get(id)
        if (!node) return

        // Recursively collect all descendant IDs
        const collectDescendants = (nodeId: string): string[] => {
          const n = state.nodes.get(nodeId)
          if (!n) return []
          const descendants: string[] = []
          for (const childId of n.children) {
            descendants.push(childId, ...collectDescendants(childId))
          }
          return descendants
        }

        const descendants = collectDescendants(id)
        const allToDelete = [id, ...descendants]

        // Store previous state for undo
        const previousState = { ...node }

        // Remove from parent's children
        if (node.parentId) {
          const parent = state.nodes.get(node.parentId)
          if (parent) {
            parent.children = parent.children.filter((cid) => cid !== id)
          }
        }

        // Delete node and all descendants
        for (const nodeId of allToDelete) {
          state.nodes.delete(nodeId)
        }

        state.undoStack.push(createAction("delete", id, null, previousState))
        state.redoStack = []
        state.isDirty = true

        if (state.selectedNodeId === id || allToDelete.includes(state.selectedNodeId ?? "")) {
          state.selectedNodeId = null
        }
      })
    },

    moveNode: (id, newParentId) => {
      const currentNode = get().nodes.get(id)
      if (!currentNode) return

      // Check for cycles
      if (detectCycle(get().nodes, id, newParentId)) {
        set((state) => {
          state.error = "Cannot move node: this would create a circular reference"
        })
        return
      }

      set((state) => {
        const node = state.nodes.get(id)
        if (!node) return

        const previousState = { parentId: node.parentId }

        // Remove from old parent
        if (node.parentId) {
          const oldParent = state.nodes.get(node.parentId)
          if (oldParent) {
            oldParent.children = oldParent.children.filter((cid) => cid !== id)
          }
        }

        // Add to new parent
        if (newParentId) {
          const newParent = state.nodes.get(newParentId)
          if (newParent) {
            newParent.children.push(id)
          }
        }

        node.parentId = newParentId
        node.metadata.updatedAt = new Date().toISOString()

        state.undoStack.push(
          createAction("move", id, { parentId: newParentId }, previousState)
        )
        state.redoStack = []
        state.isDirty = true
      })
    },

    // Selection
    setSelectedNode: (id) => {
      set((state) => {
        state.selectedNodeId = id
      })
    },

    // View
    setViewMode: (mode) => {
      set((state) => {
        state.viewMode = mode
      })
    },

    // Undo/Redo
    undo: () => {
      const { undoStack } = get()
      if (undoStack.length === 0) return

      set((state) => {
        const action = state.undoStack.pop()
        if (!action) return

        switch (action.type) {
          case "add":
            // Undo add = delete
            state.nodes.delete(action.nodeId)
            if (action.payload?.parentId) {
              const parent = state.nodes.get(action.payload.parentId)
              if (parent) {
                parent.children = parent.children.filter((id) => id !== action.nodeId)
              }
            }
            break

          case "update":
            // Undo update = restore previous
            if (action.previousState) {
              const node = state.nodes.get(action.nodeId)
              if (node) {
                Object.assign(node, action.previousState)
              }
            }
            break

          case "delete":
            // Undo delete = restore (simplified - full restore would need to store children)
            if (action.previousState) {
              state.nodes.set(action.nodeId, action.previousState as TaxonomyNode)
            }
            break

          case "move":
            // Undo move = move back
            if (action.previousState) {
              const node = state.nodes.get(action.nodeId)
              if (node) {
                // Remove from current parent
                if (node.parentId) {
                  const currentParent = state.nodes.get(node.parentId)
                  if (currentParent) {
                    currentParent.children = currentParent.children.filter(
                      (id) => id !== action.nodeId
                    )
                  }
                }
                // Add to previous parent
                const prevParentId = action.previousState.parentId as string | null
                if (prevParentId) {
                  const prevParent = state.nodes.get(prevParentId)
                  if (prevParent) {
                    prevParent.children.push(action.nodeId)
                  }
                }
                node.parentId = prevParentId ?? null
              }
            }
            break
        }

        state.redoStack.push(action)
        state.isDirty = true
      })
    },

    redo: () => {
      const { redoStack } = get()
      if (redoStack.length === 0) return

      set((state) => {
        const action = state.redoStack.pop()
        if (!action) return

        switch (action.type) {
          case "add":
            if (action.payload) {
              state.nodes.set(action.nodeId, action.payload as TaxonomyNode)
              if (action.payload.parentId) {
                const parent = state.nodes.get(action.payload.parentId)
                if (parent) {
                  parent.children.push(action.nodeId)
                }
              }
            }
            break

          case "update":
            if (action.payload) {
              const node = state.nodes.get(action.nodeId)
              if (node) {
                Object.assign(node, action.payload)
              }
            }
            break

          case "delete":
            state.nodes.delete(action.nodeId)
            break

          case "move":
            if (action.payload) {
              const node = state.nodes.get(action.nodeId)
              if (node) {
                const newParentId = action.payload.parentId as string | null
                // Move to new parent (simplified)
                node.parentId = newParentId
              }
            }
            break
        }

        state.undoStack.push(action)
        state.isDirty = true
      })
    },

    canUndo: () => get().undoStack.length > 0,
    canRedo: () => get().redoStack.length > 0,

    // Persistence
    save: async () => {
      set((state) => {
        state.isSaving = true
        state.error = null
      })

      try {
        // API call would go here
        await new Promise((resolve) => setTimeout(resolve, 500))

        set((state) => {
          state.isDirty = false
          state.isSaving = false
          state.lastSavedAt = new Date()
        })
      } catch (error) {
        set((state) => {
          state.isSaving = false
          state.error = error instanceof Error ? error.message : "Failed to save"
        })
      }
    },

    loadTaxonomy: async (taxonomyId: string) => {
      set((state) => {
        state.isLoading = true
        state.error = null
      })

      try {
        // API call would go here
        await new Promise((resolve) => setTimeout(resolve, 500))

        // Mock data for now
        const mockNodes = new Map<string, TaxonomyNode>()
        const rootId = "root_1"
        mockNodes.set(rootId, {
          id: rootId,
          name: "Root Category",
          description: "The root of the taxonomy",
          parentId: null,
          children: [],
          metadata: {
            documentsCount: 0,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            createdBy: "system",
          },
        })

        set((state) => {
          state.nodes = mockNodes
          state.isLoading = false
          state.isDirty = false
        })
      } catch (error) {
        set((state) => {
          state.isLoading = false
          state.error = error instanceof Error ? error.message : "Failed to load taxonomy"
        })
      }
    },

    reset: () => {
      set((state) => {
        state.nodes = new Map()
        state.selectedNodeId = null
        state.viewMode = "tree"
        state.undoStack = []
        state.redoStack = []
        state.isDirty = false
        state.error = null
      })
    },

    // State
    setError: (error) => {
      set((state) => {
        state.error = error
      })
    },

    setLoading: (loading) => {
      set((state) => {
        state.isLoading = loading
      })
    },
  }))
)
