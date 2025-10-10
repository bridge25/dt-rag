import { render, screen, fireEvent } from '@testing-library/react'
import { Pagination } from '../pagination'

describe('Pagination', () => {
  test('renders current page and total pages', () => {
    render(<Pagination currentPage={3} totalPages={10} onPageChange={jest.fn()} />)

    expect(screen.getByText('3')).toBeInTheDocument()
  })

  test('calls onPageChange when page button is clicked', () => {
    const onPageChange = jest.fn()
    render(<Pagination currentPage={3} totalPages={10} onPageChange={onPageChange} />)

    const nextPageButton = screen.getByText('4')
    fireEvent.click(nextPageButton)

    expect(onPageChange).toHaveBeenCalledWith(4)
  })

  test('shows first and last page buttons', () => {
    render(<Pagination currentPage={5} totalPages={10} onPageChange={jest.fn()} />)

    expect(screen.getByLabelText('First page')).toBeInTheDocument()
    expect(screen.getByLabelText('Last page')).toBeInTheDocument()
  })

  test('navigates to first page', () => {
    const onPageChange = jest.fn()
    render(<Pagination currentPage={5} totalPages={10} onPageChange={onPageChange} />)

    const firstPageButton = screen.getByLabelText('First page')
    fireEvent.click(firstPageButton)

    expect(onPageChange).toHaveBeenCalledWith(1)
  })

  test('navigates to last page', () => {
    const onPageChange = jest.fn()
    render(<Pagination currentPage={5} totalPages={10} onPageChange={onPageChange} />)

    const lastPageButton = screen.getByLabelText('Last page')
    fireEvent.click(lastPageButton)

    expect(onPageChange).toHaveBeenCalledWith(10)
  })

  test('disables first page button when on first page', () => {
    render(<Pagination currentPage={1} totalPages={10} onPageChange={jest.fn()} />)

    const firstPageButton = screen.getByLabelText('First page')
    expect(firstPageButton).toBeDisabled()
  })

  test('disables last page button when on last page', () => {
    render(<Pagination currentPage={10} totalPages={10} onPageChange={jest.fn()} />)

    const lastPageButton = screen.getByLabelText('Last page')
    expect(lastPageButton).toBeDisabled()
  })

  test('shows current page with ±2 range', () => {
    render(<Pagination currentPage={5} totalPages={10} onPageChange={jest.fn()} />)

    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('6')).toBeInTheDocument()
    expect(screen.getByText('7')).toBeInTheDocument()
  })

  test('highlights current page', () => {
    render(<Pagination currentPage={5} totalPages={10} onPageChange={jest.fn()} />)

    const currentPageButton = screen.getByText('5')
    expect(currentPageButton).toHaveClass('bg-accent-600', 'text-white')
  })
})
