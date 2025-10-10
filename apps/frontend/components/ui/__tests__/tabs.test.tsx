import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { Tabs, TabList, Tab, TabPanel } from '../tabs'

describe('Tabs', () => {
  const TabsExample = () => (
    <Tabs defaultValue="tab1">
      <TabList>
        <Tab value="tab1">Tab 1</Tab>
        <Tab value="tab2">Tab 2</Tab>
        <Tab value="tab3">Tab 3</Tab>
      </TabList>
      <TabPanel value="tab1">
        <p>Content 1</p>
      </TabPanel>
      <TabPanel value="tab2">
        <p>Content 2</p>
      </TabPanel>
      <TabPanel value="tab3">
        <p>Content 3</p>
      </TabPanel>
    </Tabs>
  )

  test('renders all tabs', () => {
    render(<TabsExample />)
    expect(screen.getByText('Tab 1')).toBeInTheDocument()
    expect(screen.getByText('Tab 2')).toBeInTheDocument()
    expect(screen.getByText('Tab 3')).toBeInTheDocument()
  })

  test('shows default tab content', () => {
    render(<TabsExample />)
    expect(screen.getByText('Content 1')).toBeInTheDocument()
    expect(screen.queryByText('Content 2')).not.toBeInTheDocument()
  })

  test('switches tab content on click', () => {
    render(<TabsExample />)

    const tab2 = screen.getByText('Tab 2')
    fireEvent.click(tab2)

    expect(screen.getByText('Content 2')).toBeInTheDocument()
    expect(screen.queryByText('Content 1')).not.toBeInTheDocument()
  })

  test('highlights active tab', () => {
    render(<TabsExample />)

    const tab1 = screen.getByText('Tab 1')
    expect(tab1).toHaveClass('border-accent-600', 'text-accent-600')

    const tab2 = screen.getByText('Tab 2')
    fireEvent.click(tab2)

    expect(tab2).toHaveClass('border-accent-600', 'text-accent-600')
    expect(tab1).not.toHaveClass('border-accent-600')
  })

  test('has accessible attributes', () => {
    render(<TabsExample />)

    const tab1 = screen.getByText('Tab 1')
    expect(tab1).toHaveAttribute('role', 'tab')
    expect(tab1).toHaveAttribute('aria-selected', 'true')

    const tab2 = screen.getByText('Tab 2')
    expect(tab2).toHaveAttribute('aria-selected', 'false')
  })
})

describe('Tabs with controlled value', () => {
  test('uses controlled value', () => {
    const ControlledTabs = () => {
      const [value, setValue] = React.useState('tab2')

      return (
        <Tabs value={value} onValueChange={setValue}>
          <TabList>
            <Tab value="tab1">Tab 1</Tab>
            <Tab value="tab2">Tab 2</Tab>
          </TabList>
          <TabPanel value="tab1">Content 1</TabPanel>
          <TabPanel value="tab2">Content 2</TabPanel>
        </Tabs>
      )
    }

    render(<ControlledTabs />)
    expect(screen.getByText('Content 2')).toBeInTheDocument()
  })
})
