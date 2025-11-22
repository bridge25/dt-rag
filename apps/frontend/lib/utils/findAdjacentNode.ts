/**
 * Spatial navigation algorithm using Euclidean distance with tree hierarchy support
 *
 * @CODE:FRONTEND-MIGRATION-001
 */

import type { Node } from "@xyflow/react"
import type { TaxonomyNode } from "@/lib/api/types"
import type { LayoutType } from "@/components/taxonomy/taxonomyLayouts"

/**
 * Direction for navigation
 */
export type Direction = "up" | "down" | "left" | "right"

/**
 * Extended FlowNode type with taxonomy data
 */
export interface FlowNode extends Node {
  data: {
    taxonomyNode: TaxonomyNode
    isExpanded: boolean
  }
}

/**
 * Calculate Euclidean distance between two points
 */
function calculateDistance(x1: number, y1: number, x2: number, y2: number): number {
  const dx = x2 - x1
  const dy = y2 - y1
  return Math.sqrt(dx * dx + dy * dy)
}

/**
 * Get first child node from taxonomy hierarchy
 */
function getFirstChild(sourceNode: FlowNode, nodes: FlowNode[]): string | null {
  const children = sourceNode.data.taxonomyNode.children
  if (!children || children.length === 0) {
    return null
  }

  const firstChildId = children[0].id
  const childNode = nodes.find((node) => node.id === firstChildId)
  return childNode ? childNode.id : null
}

/**
 * Get next sibling node from taxonomy hierarchy
 */
function getNextSibling(sourceNode: FlowNode, nodes: FlowNode[]): string | null {
  const parentId = sourceNode.data.taxonomyNode.parent_id
  if (!parentId) {
    return null
  }

  const parentNode = nodes.find((node) => node.id === parentId)
  if (!parentNode) {
    return null
  }

  const siblings = parentNode.data.taxonomyNode.children || []
  const currentIndex = siblings.findIndex((child) => child.id === sourceNode.id)

  if (currentIndex === -1 || currentIndex === siblings.length - 1) {
    return null
  }

  return siblings[currentIndex + 1].id
}

/**
 * Get previous sibling node from taxonomy hierarchy
 */
function getPreviousSibling(sourceNode: FlowNode, nodes: FlowNode[]): string | null {
  const parentId = sourceNode.data.taxonomyNode.parent_id
  if (!parentId) {
    return null
  }

  const parentNode = nodes.find((node) => node.id === parentId)
  if (!parentNode) {
    return null
  }

  const siblings = parentNode.data.taxonomyNode.children || []
  const currentIndex = siblings.findIndex((child) => child.id === sourceNode.id)

  if (currentIndex <= 0) {
    return null
  }

  return siblings[currentIndex - 1].id
}

/**
 * Get parent node from taxonomy hierarchy
 */
function getParent(sourceNode: FlowNode, nodes: FlowNode[]): string | null {
  const parentId = sourceNode.data.taxonomyNode.parent_id
  if (!parentId) {
    return null
  }

  const parentNode = nodes.find((node) => node.id === parentId)
  return parentNode ? parentNode.id : null
}

/**
 * Get siblings at same level for left/right navigation
 */
function getSiblingsInDirection(
  sourceNode: FlowNode,
  nodes: FlowNode[],
  direction: "left" | "right"
): FlowNode[] {
  const parentId = sourceNode.data.taxonomyNode.parent_id
  if (!parentId) {
    return []
  }

  const parentNode = nodes.find((node) => node.id === parentId)
  if (!parentNode) {
    return []
  }

  const siblings = parentNode.data.taxonomyNode.children || []
  const siblingNodes = siblings
    .map((sibling) => nodes.find((node) => node.id === sibling.id))
    .filter((node): node is FlowNode => node !== undefined && node.id !== sourceNode.id)

  // Filter by direction based on x position
  if (direction === "right") {
    return siblingNodes.filter((node) => node.position.x > sourceNode.position.x)
  } else {
    return siblingNodes.filter((node) => node.position.x < sourceNode.position.x)
  }
}

/**
 * Find the closest node from a list of candidates
 */
function findClosestNode(sourceNode: FlowNode, candidates: FlowNode[]): string | null {
  if (candidates.length === 0) {
    return null
  }

  const sourceX = sourceNode.position.x
  const sourceY = sourceNode.position.y

  let minDistance = Infinity
  let closestNode: FlowNode | null = null

  for (const candidate of candidates) {
    const distance = calculateDistance(
      sourceX,
      sourceY,
      candidate.position.x,
      candidate.position.y
    )

    if (distance < minDistance) {
      minDistance = distance
      closestNode = candidate
    }
  }

  return closestNode ? closestNode.id : null
}

/**
 * Find adjacent node in the specified direction using spatial algorithm and tree hierarchy
 *
 * Algorithm:
 * 1. Try hierarchy-based navigation first (parent, child, sibling)
 * 2. If no hierarchy match, fallback to spatial algorithm
 * 3. Filter candidate nodes based on direction
 * 4. Calculate Euclidean distance to each candidate
 * 5. Return the node with minimum distance, or null if no candidates exist
 *
 * @param sourceNodeId - ID of the current focused node
 * @param direction - Direction to navigate (up, down, left, right)
 * @param nodes - Array of all flow nodes
 * @param layout - Current layout type (tree or radial) - reserved for future use
 * @returns ID of adjacent node, or null if none found
 */
export function findAdjacentNode(
  sourceNodeId: string,
  direction: Direction,
  nodes: FlowNode[],
  layout: LayoutType
): string | null {
  // Reserved for future layout-specific navigation optimization
  void layout

  // Find source node
  const sourceNode = nodes.find((node) => node.id === sourceNodeId)
  if (!sourceNode) {
    return null
  }

  // Try hierarchy-based navigation first
  let hierarchyTarget: string | null = null

  switch (direction) {
    case "down":
      // Priority: First child > Next sibling > Spatial
      hierarchyTarget = getFirstChild(sourceNode, nodes)
      if (!hierarchyTarget) {
        hierarchyTarget = getNextSibling(sourceNode, nodes)
      }
      break

    case "up":
      // Priority: Previous sibling > Parent > Spatial
      hierarchyTarget = getPreviousSibling(sourceNode, nodes)
      if (!hierarchyTarget) {
        hierarchyTarget = getParent(sourceNode, nodes)
      }
      break

    case "right":
    case "left": {
      // Priority: Sibling at same level > Spatial
      const siblings = getSiblingsInDirection(sourceNode, nodes, direction)
      if (siblings.length > 0) {
        // Find closest sibling by distance
        hierarchyTarget = findClosestNode(sourceNode, siblings)
      }
      break
    }
  }

  // If hierarchy navigation succeeded, return it
  if (hierarchyTarget) {
    return hierarchyTarget
  }

  // Fallback to spatial algorithm
  const sourceX = sourceNode.position.x
  const sourceY = sourceNode.position.y

  // Filter candidate nodes based on direction
  let candidates: FlowNode[] = []

  switch (direction) {
    case "right":
      candidates = nodes.filter((node) => node.position.x > sourceX && node.id !== sourceNodeId)
      break
    case "left":
      candidates = nodes.filter((node) => node.position.x < sourceX && node.id !== sourceNodeId)
      break
    case "down":
      candidates = nodes.filter((node) => node.position.y > sourceY && node.id !== sourceNodeId)
      break
    case "up":
      candidates = nodes.filter((node) => node.position.y < sourceY && node.id !== sourceNodeId)
      break
  }

  if (candidates.length === 0) {
    return null
  }

  return findClosestNode(sourceNode, candidates)
}
