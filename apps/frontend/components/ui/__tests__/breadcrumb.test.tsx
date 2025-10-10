import { render, screen } from '@testing-library/react'
import { Breadcrumb } from '../breadcrumb'

describe('Breadcrumb', () => {
  test('renders all items when count is 3 or less', () => {
    const items = [
      { label: 'Home', href: '/' },
      { label: 'Products', href: '/products' },
      { label: 'Laptop', href: '/products/laptop' }
    ]

    render(<Breadcrumb items={items} />)

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Products')).toBeInTheDocument()
    expect(screen.getByText('Laptop')).toBeInTheDocument()
  })

  test('truncates items when count exceeds 3', () => {
    const items = [
      { label: 'Home', href: '/' },
      { label: 'Products', href: '/products' },
      { label: 'Electronics', href: '/products/electronics' },
      { label: 'Computers', href: '/products/electronics/computers' },
      { label: 'Laptop', href: '/products/electronics/computers/laptop' }
    ]

    render(<Breadcrumb items={items} />)

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('...')).toBeInTheDocument()
    expect(screen.getByText('Laptop')).toBeInTheDocument()
    expect(screen.queryByText('Products')).not.toBeInTheDocument()
    expect(screen.queryByText('Electronics')).not.toBeInTheDocument()
  })

  test('last item is bold and not clickable', () => {
    const items = [
      { label: 'Home', href: '/' },
      { label: 'Products', href: '/products' }
    ]

    render(<Breadcrumb items={items} />)

    const lastItem = screen.getByText('Products')
    expect(lastItem).toHaveClass('font-bold')
    expect(lastItem.tagName).not.toBe('A')
  })

  test('renders separators between items', () => {
    const items = [
      { label: 'Home', href: '/' },
      { label: 'Products', href: '/products' }
    ]

    const { container } = render(<Breadcrumb items={items} />)
    const separators = container.querySelectorAll('svg')
    expect(separators.length).toBeGreaterThan(0)
  })

  test('handles single item', () => {
    const items = [
      { label: 'Home', href: '/' }
    ]

    render(<Breadcrumb items={items} />)

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Home')).toHaveClass('font-bold')
  })
})
