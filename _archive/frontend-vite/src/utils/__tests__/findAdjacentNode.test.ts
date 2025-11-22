/**
 * Test file
 *
 * @CODE:FRONTEND-001
 * @TEST:FRONTEND-001
 */
import { describe, it, expect } from 'vitest'
import { findAdjacentNode, type Direction } from '../findAdjacentNode'
import type { FlowNode } from '../../hooks/useArrowKeyNavigation'
import type { TaxonomyNode } from '../../lib/api/types'

const createMockNode = (
  id: string,
  x: number,
  y: number,
  parentId: string | null = null,
  children: TaxonomyNode[] = []
): FlowNode => ({
  id,
  type: 'taxonomyNode',
  position: { x, y },
  data: {
    taxonomyNode: {
      id,
      name: `Node ${id}`,
      path: [`node-${id}`],
      parent_id: parentId,
      children,
      level: 0,
      document_count: 0,
    },
    isExpanded: true,
  },
})

describe('findAdjacentNode - Spatial Algorithm', () => {
  describe('ArrowRight navigation', () => {
    it('should find nearest node to the right', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 0, 0),
        createMockNode('2', 100, 0),
        createMockNode('3', 200, 0),
      ]

      const result = findAdjacentNode('1', 'right', nodes, 'tree')

      expect(result).toBe('2')
    })

    it('should find nearest node to the right among multiple candidates', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 0, 0),
        createMockNode('2', 150, 0),
        createMockNode('3', 100, 50), // Diagonal but closer
        createMockNode('4', 80, 10), // Very close
      ]

      const result = findAdjacentNode('1', 'right', nodes, 'tree')

      // Node 4 at (80, 10) is closest: sqrt(80^2 + 10^2) = ~80.6
      expect(result).toBe('4')
    })

    it('should return null when no node exists to the right', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 100, 0),
        createMockNode('2', 50, 0),
      ]

      const result = findAdjacentNode('1', 'right', nodes, 'tree')

      expect(result).toBeNull()
    })
  })

  describe('ArrowLeft navigation', () => {
    it('should find nearest node to the left', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 200, 0),
        createMockNode('2', 100, 0),
        createMockNode('3', 0, 0),
      ]

      const result = findAdjacentNode('1', 'left', nodes, 'tree')

      expect(result).toBe('2')
    })

    it('should find nearest node to the left among multiple candidates', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 200, 100),
        createMockNode('2', 100, 100),
        createMockNode('3', 50, 50),
        createMockNode('4', 150, 90), // Closest
      ]

      const result = findAdjacentNode('1', 'left', nodes, 'tree')

      // Node 4 at (150, 90) is closest: sqrt(50^2 + 10^2) = ~51
      expect(result).toBe('4')
    })

    it('should return null when no node exists to the left', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 0, 0),
        createMockNode('2', 100, 0),
      ]

      const result = findAdjacentNode('1', 'left', nodes, 'tree')

      expect(result).toBeNull()
    })
  })

  describe('ArrowDown navigation', () => {
    it('should find nearest node below', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 0, 0),
        createMockNode('2', 0, 100),
        createMockNode('3', 0, 200),
      ]

      const result = findAdjacentNode('1', 'down', nodes, 'tree')

      expect(result).toBe('2')
    })

    it('should find nearest node below among multiple candidates', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 100, 100),
        createMockNode('2', 100, 200),
        createMockNode('3', 150, 180), // Closer
        createMockNode('4', 50, 190),
      ]

      const result = findAdjacentNode('1', 'down', nodes, 'tree')

      // Node 3 at (150, 180) is closest: sqrt(50^2 + 80^2) = ~94.3
      expect(result).toBe('3')
    })

    it('should return null when no node exists below', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 0, 100),
        createMockNode('2', 0, 50),
      ]

      const result = findAdjacentNode('1', 'down', nodes, 'tree')

      expect(result).toBeNull()
    })
  })

  describe('ArrowUp navigation', () => {
    it('should find nearest node above', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 0, 200),
        createMockNode('2', 0, 100),
        createMockNode('3', 0, 0),
      ]

      const result = findAdjacentNode('1', 'up', nodes, 'tree')

      expect(result).toBe('2')
    })

    it('should find nearest node above among multiple candidates', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 100, 200),
        createMockNode('2', 100, 100),
        createMockNode('3', 120, 150), // Closer
        createMockNode('4', 50, 120),
      ]

      const result = findAdjacentNode('1', 'up', nodes, 'tree')

      // Node 3 at (120, 150) is closest: sqrt(20^2 + 50^2) = ~53.9
      expect(result).toBe('3')
    })

    it('should return null when no node exists above', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 0, 0),
        createMockNode('2', 0, 50),
      ]

      const result = findAdjacentNode('1', 'up', nodes, 'tree')

      expect(result).toBeNull()
    })
  })

  describe('Layout support', () => {
    it('should work with Tree layout', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 0, 0),
        createMockNode('2', 100, 0),
      ]

      const result = findAdjacentNode('1', 'right', nodes, 'tree')

      expect(result).toBe('2')
    })

    it('should work with Radial layout', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 0, 0),
        createMockNode('2', 100, 0),
      ]

      const result = findAdjacentNode('1', 'right', nodes, 'radial')

      expect(result).toBe('2')
    })
  })

  describe('Edge cases', () => {
    it('should return null when source node does not exist', () => {
      const nodes: FlowNode[] = [createMockNode('1', 0, 0)]

      const result = findAdjacentNode('non-existent', 'right', nodes, 'tree')

      expect(result).toBeNull()
    })

    it('should not return the source node itself', () => {
      const nodes: FlowNode[] = [createMockNode('1', 0, 0)]

      const result = findAdjacentNode('1', 'right', nodes, 'tree')

      expect(result).toBeNull()
    })

    it('should handle nodes at the same position', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 100, 100),
        createMockNode('2', 100, 100), // Same position
        createMockNode('3', 200, 100),
      ]

      const result = findAdjacentNode('1', 'right', nodes, 'tree')

      // Should find node 3, not node 2 at same position
      expect(result).toBe('3')
    })
  })
})

describe('findAdjacentNode - Tree Hierarchy Navigation', () => {
  describe('ArrowDown with hierarchy', () => {
    it('should navigate to first child with ArrowDown', () => {
      const child1: TaxonomyNode = {
        id: '2',
        name: 'Child 1',
        path: ['parent', 'child1'],
        parent_id: '1',
        level: 1,
      }
      const child2: TaxonomyNode = {
        id: '3',
        name: 'Child 2',
        path: ['parent', 'child2'],
        parent_id: '1',
        level: 1,
      }

      const nodes: FlowNode[] = [
        createMockNode('1', 100, 0, null, [child1, child2]),
        createMockNode('2', 50, 100, '1'),
        createMockNode('3', 150, 100, '1'),
        createMockNode('4', 200, 0, null), // Spatial candidate
      ]

      const result = findAdjacentNode('1', 'down', nodes, 'tree')

      // Should prefer first child over spatial nearest
      expect(result).toBe('2')
    })

    it('should navigate to next sibling when no children exist', () => {
      const sibling: TaxonomyNode = {
        id: '3',
        name: 'Sibling',
        path: ['parent', 'sibling'],
        parent_id: 'parent',
        level: 1,
      }

      const nodes: FlowNode[] = [
        createMockNode('parent', 100, 0, null, [
          {
            id: '2',
            name: 'Node 2',
            path: ['parent', 'node2'],
            parent_id: 'parent',
            level: 1,
          },
          sibling,
        ]),
        createMockNode('2', 100, 100, 'parent', []),
        createMockNode('3', 100, 100, 'parent'),
      ]

      const result = findAdjacentNode('2', 'down', nodes, 'tree')

      // Should navigate to next sibling
      expect(result).toBe('3')
    })

    it('should fallback to spatial when no hierarchy match for down', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 100, 0, null, []),
        createMockNode('2', 100, 100, null),
      ]

      const result = findAdjacentNode('1', 'down', nodes, 'tree')

      // Should use spatial algorithm
      expect(result).toBe('2')
    })
  })

  describe('ArrowUp with hierarchy', () => {
    it('should navigate to parent with ArrowUp', () => {
      const parent: TaxonomyNode = {
        id: '1',
        name: 'Parent',
        path: ['parent'],
        parent_id: null,
        level: 0,
        children: [
          {
            id: '2',
            name: 'Child',
            path: ['parent', 'child'],
            parent_id: '1',
            level: 1,
          },
        ],
      }

      const nodes: FlowNode[] = [
        createMockNode('1', 100, 0, null, parent.children),
        createMockNode('2', 100, 100, '1'),
        createMockNode('3', 80, 50, null), // Spatial candidate closer
      ]

      const result = findAdjacentNode('2', 'up', nodes, 'tree')

      // Should prefer parent over spatial nearest
      expect(result).toBe('1')
    })

    it('should navigate to previous sibling with ArrowUp', () => {
      const nodes: FlowNode[] = [
        createMockNode('parent', 100, 0, null),
        createMockNode('2', 100, 100, 'parent'),
        createMockNode('3', 100, 150, 'parent'),
      ]

      const result = findAdjacentNode('3', 'up', nodes, 'tree')

      // Should navigate to previous sibling
      expect(result).toBe('2')
    })

    it('should fallback to spatial when no hierarchy match for up', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 100, 100, null),
        createMockNode('2', 100, 0, null),
      ]

      const result = findAdjacentNode('1', 'up', nodes, 'tree')

      // Should use spatial algorithm
      expect(result).toBe('2')
    })
  })

  describe('ArrowLeft/Right with hierarchy', () => {
    it('should navigate to next sibling with ArrowRight', () => {
      const nodes: FlowNode[] = [
        createMockNode('parent', 0, 0, null),
        createMockNode('1', 100, 100, 'parent'),
        createMockNode('2', 200, 100, 'parent'),
        createMockNode('3', 150, 120, null), // Spatial candidate closer
      ]

      const result = findAdjacentNode('1', 'right', nodes, 'tree')

      // Should prefer sibling at same level
      expect(result).toBe('2')
    })

    it('should navigate to previous sibling with ArrowLeft', () => {
      const nodes: FlowNode[] = [
        createMockNode('parent', 300, 0, null),
        createMockNode('1', 100, 100, 'parent'),
        createMockNode('2', 200, 100, 'parent'),
        createMockNode('3', 150, 90, null), // Spatial candidate closer
      ]

      const result = findAdjacentNode('2', 'left', nodes, 'tree')

      // Should prefer sibling at same level
      expect(result).toBe('1')
    })

    it('should fallback to spatial when no sibling exists', () => {
      const nodes: FlowNode[] = [
        createMockNode('1', 100, 100, 'parent'),
        createMockNode('2', 200, 100, 'other-parent'),
      ]

      const result = findAdjacentNode('1', 'right', nodes, 'tree')

      // Should use spatial algorithm since nodes have different parents
      expect(result).toBe('2')
    })
  })
})
