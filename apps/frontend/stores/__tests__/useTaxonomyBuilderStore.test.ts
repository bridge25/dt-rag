/**
 * Tests for TaxonomyBuilder Store
 *
 * @TEST:TAXONOMY-BUILDER-001
 */

import { describe, it, expect, beforeEach } from "vitest"
import { useTaxonomyBuilderStore } from "../useTaxonomyBuilderStore"

// Helper to get fresh state
const getStore = () => useTaxonomyBuilderStore.getState()

describe("useTaxonomyBuilderStore", () => {
  beforeEach(() => {
    // Reset store before each test
    getStore().reset()
  })

  describe("addNode", () => {
    it("should add a root node when no parentId is provided", () => {
      const nodeId = getStore().addNode({
        name: "Root Node",
        description: "Test root node",
        parentId: null,
      })

      const addedNode = getStore().nodes.get(nodeId)
      expect(addedNode).toBeDefined()
      expect(addedNode?.name).toBe("Root Node")
      expect(addedNode?.parentId).toBeNull()
      expect(addedNode?.children).toEqual([])
      expect(getStore().isDirty).toBe(true)
    })

    it("should add a child node and update parent's children array", () => {
      const parentId = getStore().addNode({
        name: "Parent",
        parentId: null,
      })

      const childId = getStore().addNode({
        name: "Child",
        parentId,
      })

      const parent = getStore().nodes.get(parentId)
      const child = getStore().nodes.get(childId)

      expect(parent?.children).toContain(childId)
      expect(child?.parentId).toBe(parentId)
    })

    it("should record action in undo stack", () => {
      getStore().addNode({
        name: "Test Node",
        parentId: null,
      })

      expect(getStore().undoStack.length).toBe(1)
      expect(getStore().undoStack[0].type).toBe("add")
    })
  })

  describe("updateNode", () => {
    it("should update node properties", () => {
      const nodeId = getStore().addNode({
        name: "Original Name",
        parentId: null,
      })

      getStore().updateNode(nodeId, {
        name: "Updated Name",
        description: "New description",
      })

      const updated = getStore().nodes.get(nodeId)
      expect(updated?.name).toBe("Updated Name")
      expect(updated?.description).toBe("New description")
    })

    it("should update metadata.updatedAt", () => {
      const nodeId = getStore().addNode({
        name: "Test",
        parentId: null,
      })

      const originalNode = getStore().nodes.get(nodeId)
      expect(originalNode?.metadata.updatedAt).toBeDefined()
      expect(typeof originalNode?.metadata.updatedAt).toBe("string")

      // Verify updatedAt is a valid ISO date string
      getStore().updateNode(nodeId, { name: "Updated" })

      const updatedNode = getStore().nodes.get(nodeId)
      expect(updatedNode?.metadata.updatedAt).toBeDefined()
      expect(typeof updatedNode?.metadata.updatedAt).toBe("string")
      // Verify it's a parseable date
      expect(new Date(updatedNode?.metadata.updatedAt ?? "").getTime()).toBeGreaterThan(0)
    })
  })

  describe("deleteNode", () => {
    it("should remove a node from the store", () => {
      const nodeId = getStore().addNode({
        name: "To Delete",
        parentId: null,
      })

      expect(getStore().nodes.has(nodeId)).toBe(true)

      getStore().deleteNode(nodeId)

      expect(getStore().nodes.has(nodeId)).toBe(false)
    })

    it("should remove node from parent's children array", () => {
      const parentId = getStore().addNode({
        name: "Parent",
        parentId: null,
      })

      const childId = getStore().addNode({
        name: "Child",
        parentId,
      })

      expect(getStore().nodes.get(parentId)?.children).toContain(childId)

      getStore().deleteNode(childId)

      expect(getStore().nodes.get(parentId)?.children).not.toContain(childId)
    })

    it("should recursively delete all children", () => {
      const parentId = getStore().addNode({ name: "Parent", parentId: null })
      const childId = getStore().addNode({ name: "Child", parentId })
      const grandchildId = getStore().addNode({ name: "Grandchild", parentId: childId })

      getStore().deleteNode(parentId)

      expect(getStore().nodes.has(parentId)).toBe(false)
      expect(getStore().nodes.has(childId)).toBe(false)
      expect(getStore().nodes.has(grandchildId)).toBe(false)
    })
  })

  describe("moveNode", () => {
    it("should move a node to a new parent", () => {
      const parent1 = getStore().addNode({ name: "Parent 1", parentId: null })
      const parent2 = getStore().addNode({ name: "Parent 2", parentId: null })
      const child = getStore().addNode({ name: "Child", parentId: parent1 })

      expect(getStore().nodes.get(parent1)?.children).toContain(child)
      expect(getStore().nodes.get(parent2)?.children).not.toContain(child)

      getStore().moveNode(child, parent2)

      expect(getStore().nodes.get(parent1)?.children).not.toContain(child)
      expect(getStore().nodes.get(parent2)?.children).toContain(child)
      expect(getStore().nodes.get(child)?.parentId).toBe(parent2)
    })

    it("should move a node to root level", () => {
      const parent = getStore().addNode({ name: "Parent", parentId: null })
      const child = getStore().addNode({ name: "Child", parentId: parent })

      getStore().moveNode(child, null)

      expect(getStore().nodes.get(child)?.parentId).toBeNull()
      expect(getStore().nodes.get(parent)?.children).not.toContain(child)
    })

    it("should prevent creating a cycle", () => {
      const parent = getStore().addNode({ name: "Parent", parentId: null })
      const child = getStore().addNode({ name: "Child", parentId: parent })
      const grandchild = getStore().addNode({ name: "Grandchild", parentId: child })

      // Try to move parent under grandchild (would create a cycle)
      getStore().moveNode(parent, grandchild)

      // Should not create cycle - parent should stay at root
      expect(getStore().nodes.get(parent)?.parentId).toBeNull()
    })

    it("should not move node to itself", () => {
      const node = getStore().addNode({ name: "Node", parentId: null })

      getStore().moveNode(node, node)

      expect(getStore().nodes.get(node)?.parentId).toBeNull()
    })
  })

  describe("undo/redo", () => {
    it("should undo add operation", () => {
      const nodeId = getStore().addNode({ name: "Test", parentId: null })
      expect(getStore().nodes.has(nodeId)).toBe(true)

      getStore().undo()
      expect(getStore().nodes.has(nodeId)).toBe(false)
    })

    it("should redo undone operation", () => {
      const nodeId = getStore().addNode({ name: "Test", parentId: null })
      getStore().undo()
      expect(getStore().nodes.has(nodeId)).toBe(false)

      getStore().redo()
      expect(getStore().nodes.has(nodeId)).toBe(true)
    })

    it("should undo delete operation", () => {
      const nodeId = getStore().addNode({ name: "Test", parentId: null })
      getStore().deleteNode(nodeId)
      expect(getStore().nodes.has(nodeId)).toBe(false)

      getStore().undo()
      expect(getStore().nodes.has(nodeId)).toBe(true)
    })

    it("should undo update operation", () => {
      const nodeId = getStore().addNode({ name: "Original", parentId: null })
      getStore().updateNode(nodeId, { name: "Updated" })
      expect(getStore().nodes.get(nodeId)?.name).toBe("Updated")

      getStore().undo()
      expect(getStore().nodes.get(nodeId)?.name).toBe("Original")
    })

    it("canUndo returns correct value", () => {
      expect(getStore().canUndo()).toBe(false)

      getStore().addNode({ name: "Test", parentId: null })
      expect(getStore().canUndo()).toBe(true)

      getStore().undo()
      expect(getStore().canUndo()).toBe(false)
    })

    it("canRedo returns correct value", () => {
      expect(getStore().canRedo()).toBe(false)

      getStore().addNode({ name: "Test", parentId: null })
      expect(getStore().canRedo()).toBe(false)

      getStore().undo()
      expect(getStore().canRedo()).toBe(true)
    })
  })

  describe("selection", () => {
    it("should select a node", () => {
      const nodeId = getStore().addNode({ name: "Test", parentId: null })
      getStore().setSelectedNode(nodeId)

      expect(getStore().selectedNodeId).toBe(nodeId)
    })

    it("should deselect when selecting null", () => {
      const nodeId = getStore().addNode({ name: "Test", parentId: null })
      getStore().setSelectedNode(nodeId)
      getStore().setSelectedNode(null)

      expect(getStore().selectedNodeId).toBeNull()
    })

    it("should clear selection when node is deleted", () => {
      const nodeId = getStore().addNode({ name: "Test", parentId: null })
      getStore().setSelectedNode(nodeId)
      getStore().deleteNode(nodeId)

      expect(getStore().selectedNodeId).toBeNull()
    })
  })

  describe("viewMode", () => {
    it("should toggle view mode", () => {
      expect(getStore().viewMode).toBe("tree")

      getStore().setViewMode("graph")
      expect(getStore().viewMode).toBe("graph")

      getStore().setViewMode("tree")
      expect(getStore().viewMode).toBe("tree")
    })
  })

  describe("reset", () => {
    it("should reset all state to initial values", () => {
      getStore().addNode({ name: "Test", parentId: null })
      getStore().setSelectedNode("some-id")
      getStore().setViewMode("graph")

      getStore().reset()

      expect(getStore().nodes.size).toBe(0)
      expect(getStore().selectedNodeId).toBeNull()
      expect(getStore().viewMode).toBe("tree")
      expect(getStore().isDirty).toBe(false)
      expect(getStore().undoStack).toEqual([])
      expect(getStore().redoStack).toEqual([])
    })
  })
})
