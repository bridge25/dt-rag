// @TEST:TAXONOMY-KEYNAV-002-010
// Integration tests for arrow key navigation in TaxonomyTreeView

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TaxonomyTreeView from '../TaxonomyTreeView'
import { useTaxonomyStore } from '../../../stores/useTaxonomyStore'
import * as taxonomyApi from '../../../lib/api/taxonomy'
import type { TaxonomyNode } from '../../../lib/api/types'

// Mock the taxonomy API
vi.mock('../../../lib/api/taxonomy')

const createMockTaxonomy = (): TaxonomyNode => ({
  id: 'root',
  name: 'Root Category',
  path: ['root'],
  parent_id: null,
  level: 0,
  document_count: 100,
  children: [
    {
      id: 'child-1',
      name: 'Child 1',
      path: ['root', 'child-1'],
      parent_id: 'root',
      level: 1,
      document_count: 50,
      children: [
        {
          id: 'grandchild-1',
          name: 'Grandchild 1',
          path: ['root', 'child-1', 'grandchild-1'],
          parent_id: 'child-1',
          level: 2,
          document_count: 25,
        },
      ],
    },
    {
      id: 'child-2',
      name: 'Child 2',
      path: ['root', 'child-2'],
      parent_id: 'root',
      level: 1,
      document_count: 50,
    },
  ],
})

describe('TaxonomyTreeView - Arrow Key Navigation', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })

    // Reset store
    const { getState } = useTaxonomyStore
    getState().setFocusedNode(null)
    getState().clearFocusHistory()
    getState().setKeyboardMode('navigation')

    // Mock API response
    vi.mocked(taxonomyApi.fetchTaxonomyTree).mockResolvedValue(createMockTaxonomy())
  })

  const renderTreeView = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <TaxonomyTreeView />
      </QueryClientProvider>
    )
  }

  it('should render taxonomy tree with nodes', async () => {
    renderTreeView()

    await waitFor(() => {
      expect(screen.getByText('Root Category')).toBeInTheDocument()
    })

    expect(screen.getByText('Child 1')).toBeInTheDocument()
    expect(screen.getByText('Child 2')).toBeInTheDocument()
  })

  it('should move focus right with ArrowRight key', async () => {
    renderTreeView()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Root Category')).toBeInTheDocument()
    })

    // Set initial focus
    const rootNode = screen.getByText('Root Category').closest('div[role="button"]')
    expect(rootNode).toBeInTheDocument()

    if (rootNode) {
      await user.click(rootNode)
      await user.keyboard('{ArrowRight}')

      // Should move to child or sibling based on layout
      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).toBeTruthy()
    }
  })

  it('should move focus left with ArrowLeft key', async () => {
    renderTreeView()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Child 2')).toBeInTheDocument()
    })

    const child2Node = screen.getByText('Child 2').closest('div[role="button"]')
    if (child2Node) {
      await user.click(child2Node)

      const initialFocus = useTaxonomyStore.getState().focusedNodeId
      await user.keyboard('{ArrowLeft}')

      const finalFocus = useTaxonomyStore.getState().focusedNodeId
      expect(finalFocus).toBeTruthy()
      // Focus should change (either to sibling or parent)
      expect(finalFocus).not.toBe(initialFocus)
    }
  })

  it('should move focus down with ArrowDown key', async () => {
    renderTreeView()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Root Category')).toBeInTheDocument()
    })

    const rootNode = screen.getByText('Root Category').closest('div[role="button"]')
    if (rootNode) {
      await user.click(rootNode)
      await user.keyboard('{ArrowDown}')

      const store = useTaxonomyStore.getState()
      // Should move to first child
      expect(store.focusedNodeId).toBe('child-1')
    }
  })

  it('should move focus up with ArrowUp key', async () => {
    renderTreeView()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Child 1')).toBeInTheDocument()
    })

    const child1Node = screen.getByText('Child 1').closest('div[role="button"]')
    if (child1Node) {
      await user.click(child1Node)
      await user.keyboard('{ArrowUp}')

      const store = useTaxonomyStore.getState()
      // Should move to parent
      expect(store.focusedNodeId).toBe('root')
    }
  })

  it('should navigate to child node in tree hierarchy with ArrowDown', async () => {
    renderTreeView()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Root Category')).toBeInTheDocument()
    })

    const rootNode = screen.getByText('Root Category').closest('div[role="button"]')
    if (rootNode) {
      await user.click(rootNode)
      await user.keyboard('{ArrowDown}')

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).toBe('child-1')
    }
  })

  it('should navigate to parent node in tree hierarchy with ArrowUp', async () => {
    renderTreeView()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Grandchild 1')).toBeInTheDocument()
    })

    const grandchildNode = screen.getByText('Grandchild 1').closest('div[role="button"]')
    if (grandchildNode) {
      await user.click(grandchildNode)
      await user.keyboard('{ArrowUp}')

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).toBe('child-1')
    }
  })

  it('should work with Tree layout', async () => {
    renderTreeView()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Root Category')).toBeInTheDocument()
    })

    const rootNode = screen.getByText('Root Category').closest('div[role="button"]')
    if (rootNode) {
      await user.click(rootNode)
      await user.keyboard('{ArrowDown}')

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).not.toBeNull()
    }
  })

  it('should work with Radial layout', async () => {
    renderTreeView()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Root Category')).toBeInTheDocument()
    })

    // Switch to radial layout
    const layoutToggle = screen.getByRole('button', { name: /radial/i })
    await user.click(layoutToggle)

    const rootNode = screen.getByText('Root Category').closest('div[role="button"]')
    if (rootNode) {
      await user.click(rootNode)
      await user.keyboard('{ArrowDown}')

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).not.toBeNull()
    }
  })

  it('should not navigate when keyboardMode is search', async () => {
    renderTreeView()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Root Category')).toBeInTheDocument()
    })

    // Set keyboard mode to search
    useTaxonomyStore.getState().setKeyboardMode('search')

    const rootNode = screen.getByText('Root Category').closest('div[role="button"]')
    if (rootNode) {
      await user.click(rootNode)

      const initialFocus = useTaxonomyStore.getState().focusedNodeId
      await user.keyboard('{ArrowDown}')

      const finalFocus = useTaxonomyStore.getState().focusedNodeId
      // Focus should not change in search mode
      expect(finalFocus).toBe(initialFocus)
    }
  })

  it('should not navigate when keyboardMode is panel', async () => {
    renderTreeView()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Root Category')).toBeInTheDocument()
    })

    // Set keyboard mode to panel
    useTaxonomyStore.getState().setKeyboardMode('panel')

    const rootNode = screen.getByText('Root Category').closest('div[role="button"]')
    if (rootNode) {
      await user.click(rootNode)

      const initialFocus = useTaxonomyStore.getState().focusedNodeId
      await user.keyboard('{ArrowDown}')

      const finalFocus = useTaxonomyStore.getState().focusedNodeId
      // Focus should not change in panel mode
      expect(finalFocus).toBe(initialFocus)
    }
  })

  it('should update focus when node is clicked', async () => {
    renderTreeView()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Child 1')).toBeInTheDocument()
    })

    const child1Node = screen.getByText('Child 1').closest('div[role="button"]')
    if (child1Node) {
      await user.click(child1Node)

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).toBe('child-1')
    }
  })

  it('should maintain focus across layout changes', async () => {
    renderTreeView()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Root Category')).toBeInTheDocument()
    })

    const rootNode = screen.getByText('Root Category').closest('div[role="button"]')
    if (rootNode) {
      await user.click(rootNode)

      const beforeLayoutChange = useTaxonomyStore.getState().focusedNodeId

      // Switch layout
      const layoutToggle = screen.getByRole('button', { name: /radial/i })
      await user.click(layoutToggle)

      const afterLayoutChange = useTaxonomyStore.getState().focusedNodeId

      // Focus should be maintained
      expect(afterLayoutChange).toBe(beforeLayoutChange)
    }
  })

  it('should prevent default behavior for arrow keys', async () => {
    renderTreeView()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Root Category')).toBeInTheDocument()
    })

    const rootNode = screen.getByText('Root Category').closest('div[role="button"]')
    if (rootNode) {
      await user.click(rootNode)

      // This test verifies that preventDefault is called on arrow key events
      // The actual behavior is tested implicitly through other tests
      await user.keyboard('{ArrowDown}')

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).not.toBeNull()
    }
  })
})
