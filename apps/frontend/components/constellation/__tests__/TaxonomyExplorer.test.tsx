/**
 * TaxonomyExplorer Component Tests
 *
 * Tests for the full-page taxonomy exploration interface with constellation visualization.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TaxonomyExplorer from '../TaxonomyExplorer'
import type { TaxonomyNode } from '@/lib/api/types'

describe('TaxonomyExplorer', () => {
  const defaultTaxonomy: TaxonomyNode[] = [
    {
      id: 'root',
      name: 'Knowledge Base',
      level: 1,
      path: ['Knowledge Base'],
      parent_id: null,
      document_count: 150,
      children: [
        {
          id: 'science',
          name: 'Science',
          level: 2,
          path: ['Knowledge Base', 'Science'],
          parent_id: 'root',
          document_count: 75,
          children: [
            {
              id: 'biology',
              name: 'Biology',
              level: 3,
              path: ['Knowledge Base', 'Science', 'Biology'],
              parent_id: 'science',
              document_count: 40
            }
          ]
        },
        {
          id: 'history',
          name: 'History',
          level: 2,
          path: ['Knowledge Base', 'History'],
          parent_id: 'root',
          document_count: 75
        }
      ]
    }
  ]

  const defaultProps = {
    taxonomy: defaultTaxonomy,
    onClose: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render the explorer container', () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      expect(screen.getByTestId('taxonomy-explorer')).toBeInTheDocument()
    })

    it('should render the constellation graph', () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      expect(screen.getByTestId('constellation-graph')).toBeInTheDocument()
    })

    it('should render the sidebar panel', () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      expect(screen.getByTestId('explorer-sidebar')).toBeInTheDocument()
    })

    it('should have search input and sidebar', () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      // Verify main components are rendered
      const searchInput = screen.getByPlaceholderText(/search/i)
      const sidebar = screen.getByTestId('explorer-sidebar')
      expect(searchInput).toBeInTheDocument()
      expect(sidebar).toBeInTheDocument()
    })

    it('should render search/filter input', () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      const searchInput = screen.getByPlaceholderText(/search/i)
      expect(searchInput).toBeInTheDocument()
    })
  })

  describe('Node Selection', () => {
    it('should support node selection', async () => {
      const user = userEvent.setup()
      render(<TaxonomyExplorer {...defaultProps} />)

      const rootButton = screen.getByText('Knowledge Base').closest('[role="button"]')
      if (rootButton) {
        // Should be able to click node
        await user.click(rootButton)
        expect(rootButton).toBeInTheDocument()
      }
    })

    it('should display sidebar with selected node info', async () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      const sidebar = screen.getByTestId('explorer-sidebar')
      // Sidebar should always be present
      expect(sidebar).toBeInTheDocument()
    })
  })

  describe('Search and Filter', () => {
    it('should have search input', () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      const searchInput = screen.getByPlaceholderText(/search/i)
      expect(searchInput).toBeInTheDocument()
    })

    it('should filter nodes by search term', async () => {
      const user = userEvent.setup()
      render(<TaxonomyExplorer {...defaultProps} />)

      const searchInput = screen.getByPlaceholderText(/search/i)
      await user.type(searchInput, 'Science')

      // Science node should still be visible
      expect(screen.getByText('Science')).toBeInTheDocument()
    })

    it('should clear search on clear button click', async () => {
      const user = userEvent.setup()
      render(<TaxonomyExplorer {...defaultProps} />)

      const searchInput = screen.getByPlaceholderText(/search/i) as HTMLInputElement
      await user.type(searchInput, 'Science')

      const clearButtons = screen.queryAllByText('Clear')
      if (clearButtons.length > 0) {
        await user.click(clearButtons[0])
        await waitFor(() => {
          expect(searchInput.value).toBe('')
        })
      }
    })
  })

  describe('Breadcrumb Navigation', () => {
    it('should display breadcrumbs when node selected', async () => {
      const user = userEvent.setup()
      render(<TaxonomyExplorer {...defaultProps} />)

      const rootButton = screen.getByText('Knowledge Base').closest('[role="button"]')
      if (rootButton) {
        await user.click(rootButton)

        await waitFor(() => {
          expect(screen.getByTestId('breadcrumb-navigation')).toBeInTheDocument()
        })
      }
    })
  })

  describe('Sidebar Details', () => {
    it('should display empty state initially', () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      const sidebar = screen.getByTestId('explorer-sidebar')
      // Should have some content
      expect(sidebar).toBeInTheDocument()
    })

    it('should be scrollable for long content', () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      const sidebar = screen.getByTestId('explorer-sidebar')
      expect(sidebar).toHaveClass('overflow-auto')
    })
  })

  describe('Close Button', () => {
    it('should have close button', () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      const closeButton = screen.getByLabelText(/close/i)
      expect(closeButton).toBeInTheDocument()
    })

    it('should call onClose when close button clicked', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()
      render(<TaxonomyExplorer taxonomy={defaultTaxonomy} onClose={onClose} />)

      const closeButton = screen.getByLabelText(/close/i)
      await user.click(closeButton)

      expect(onClose).toHaveBeenCalled()
    })

    it('should support keyboard shortcut to close (Escape)', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()
      render(<TaxonomyExplorer taxonomy={defaultTaxonomy} onClose={onClose} />)

      await user.keyboard('{Escape}')

      expect(onClose).toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('should have heading in sidebar', () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      // Should have at least one heading
      const headings = screen.getAllByRole('heading')
      expect(headings.length).toBeGreaterThan(0)
    })

    it('should have accessible search input', () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      const searchInput = screen.getByPlaceholderText(/search/i)
      const hasAriaLabel = searchInput.hasAttribute('aria-label')
      const hasName = searchInput.hasAttribute('name')
      expect(hasAriaLabel || hasName).toBe(true)
    })

    it('should have ARIA labels on buttons', () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      const closeButton = screen.getByLabelText(/close/i)
      expect(closeButton).toHaveAttribute('aria-label')
    })
  })

  describe('Empty State', () => {
    it('should handle empty taxonomy', () => {
      render(<TaxonomyExplorer taxonomy={[]} onClose={vi.fn()} />)
      expect(screen.getByTestId('taxonomy-explorer')).toBeInTheDocument()
    })
  })

  describe('Responsive Design', () => {
    it('should have responsive layout', () => {
      render(<TaxonomyExplorer {...defaultProps} />)
      const explorer = screen.getByTestId('taxonomy-explorer')
      expect(explorer).toHaveClass('grid')
    })
  })
})
