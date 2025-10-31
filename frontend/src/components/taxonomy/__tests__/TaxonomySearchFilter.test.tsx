// @TEST:TAXONOMY-VIZ-001-013
// TaxonomySearchFilter component tests

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TaxonomySearchFilter from '../TaxonomySearchFilter'

describe('TaxonomySearchFilter', () => {
  const mockOnSearch = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render search input', () => {
    render(<TaxonomySearchFilter onSearch={mockOnSearch} matchCount={0} />)

    const searchInput = screen.getByLabelText(/search taxonomy nodes/i)
    expect(searchInput).toBeInTheDocument()
    expect(searchInput).toHaveAttribute('placeholder', 'Search taxonomy nodes...')
  })

  it('should call onSearch when typing', async () => {
    const user = userEvent.setup()
    render(<TaxonomySearchFilter onSearch={mockOnSearch} matchCount={0} />)

    const searchInput = screen.getByLabelText(/search taxonomy nodes/i)
    await user.type(searchInput, 'test')

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('test')
    })
  })

  it('should show match count when query is entered', async () => {
    const user = userEvent.setup()
    const { rerender } = render(
      <TaxonomySearchFilter onSearch={mockOnSearch} matchCount={0} />
    )

    const searchInput = screen.getByLabelText(/search taxonomy nodes/i)
    await user.type(searchInput, 'tech')

    // Re-render with match count
    rerender(<TaxonomySearchFilter onSearch={mockOnSearch} matchCount={3} />)

    await waitFor(() => {
      expect(screen.getByText(/found 3 matches/i)).toBeInTheDocument()
    })
  })

  it('should show "no matches" when count is zero', async () => {
    const user = userEvent.setup()
    const { rerender } = render(
      <TaxonomySearchFilter onSearch={mockOnSearch} matchCount={0} />
    )

    const searchInput = screen.getByLabelText(/search taxonomy nodes/i)
    await user.type(searchInput, 'xyz')

    // Re-render with zero matches
    rerender(<TaxonomySearchFilter onSearch={mockOnSearch} matchCount={0} />)

    await waitFor(() => {
      expect(screen.getByText(/no matches found/i)).toBeInTheDocument()
    })
  })

  it('should show clear button when query is entered', async () => {
    const user = userEvent.setup()
    render(<TaxonomySearchFilter onSearch={mockOnSearch} matchCount={0} />)

    const searchInput = screen.getByLabelText(/search taxonomy nodes/i)
    await user.type(searchInput, 'test')

    const clearButton = screen.getByLabelText(/clear search/i)
    expect(clearButton).toBeInTheDocument()
  })

  it('should clear search when clear button is clicked', async () => {
    const user = userEvent.setup()
    render(<TaxonomySearchFilter onSearch={mockOnSearch} matchCount={0} />)

    const searchInput = screen.getByLabelText(/search taxonomy nodes/i)
    await user.type(searchInput, 'test')

    const clearButton = screen.getByLabelText(/clear search/i)
    await user.click(clearButton)

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('')
      expect(searchInput).toHaveValue('')
    })
  })

  it('should show singular "match" for count of 1', async () => {
    const user = userEvent.setup()
    const { rerender } = render(
      <TaxonomySearchFilter onSearch={mockOnSearch} matchCount={0} />
    )

    const searchInput = screen.getByLabelText(/search taxonomy nodes/i)
    await user.type(searchInput, 'root')

    // Re-render with 1 match
    rerender(<TaxonomySearchFilter onSearch={mockOnSearch} matchCount={1} />)

    await waitFor(() => {
      expect(screen.getByText(/found 1 match/i)).toBeInTheDocument()
    })
  })
})
