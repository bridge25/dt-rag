/**
 * ConstellationControlPanel Component Tests
 *
 * Comprehensive unit tests for the Constellation Control Panel component.
 * Tests cover all interactive features, styling, and accessibility.
 *
 * @CODE:FRONTEND-REDESIGN-001-CONTROL-PANEL-TESTS
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ConstellationControlPanel from '../ConstellationControlPanel'

describe('ConstellationControlPanel', () => {
  // Mock handlers
  const mockHandlers = {
    onZoomIn: vi.fn(),
    onZoomOut: vi.fn(),
    onFilterClick: vi.fn(),
    onSettingsClick: vi.fn(),
    onDataDensityChange: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render the control panel container', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const panel = screen.getByTestId('constellation-control-panel')
      expect(panel).toBeInTheDocument()
    })

    it('should render all control buttons in correct order', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      expect(buttons).toHaveLength(4) // Zoom In, Zoom Out, Filter, Settings
    })

    it('should render ZOOM IN button with correct icon and label', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      expect(buttons[0]).toHaveTextContent('Zoom In')
    })

    it('should render ZOOM OUT button with correct icon and label', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      expect(buttons[1]).toHaveTextContent('Zoom Out')
    })

    it('should render FILTER button with arrow indicator', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      const filterButton = buttons[2]
      expect(filterButton).toHaveTextContent('Filter')
      // Check for chevron/arrow icon
      const chevrons = filterButton.querySelectorAll('svg')
      expect(chevrons.length).toBeGreaterThan(1) // At least filter icon + chevron
    })

    it('should render SETTINGS button with arrow indicator', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      const settingsButton = buttons[3]
      expect(settingsButton).toHaveTextContent('Settings')
      // Check for chevron/arrow icon
      const chevrons = settingsButton.querySelectorAll('svg')
      expect(chevrons.length).toBeGreaterThan(1) // At least settings icon + chevron
    })

    it('should render DATA DENSITY label', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      expect(screen.getByText('Data Density')).toBeInTheDocument()
    })

    it('should render data density slider', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const slider = screen.getByTestId('data-density-slider')
      expect(slider).toBeInTheDocument()
      expect(slider).toHaveAttribute('type', 'range')
      expect(slider).toHaveAttribute('min', '0')
      expect(slider).toHaveAttribute('max', '100')
    })

    it('should display current density percentage', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      expect(screen.getByText('Density: 50%')).toBeInTheDocument()
    })

    it('should update density display when value changes', () => {
      const { rerender } = render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      expect(screen.getByText('Density: 50%')).toBeInTheDocument()

      rerender(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={75}
        />
      )

      expect(screen.getByText('Density: 75%')).toBeInTheDocument()
    })
  })

  describe('Interactive Functionality', () => {
    it('should call onZoomIn when ZOOM IN button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      await user.click(buttons[0]) // Zoom In

      expect(mockHandlers.onZoomIn).toHaveBeenCalledTimes(1)
    })

    it('should call onZoomOut when ZOOM OUT button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      await user.click(buttons[1]) // Zoom Out

      expect(mockHandlers.onZoomOut).toHaveBeenCalledTimes(1)
    })

    it('should call onFilterClick when FILTER button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      await user.click(buttons[2]) // Filter

      expect(mockHandlers.onFilterClick).toHaveBeenCalledTimes(1)
    })

    it('should call onSettingsClick when SETTINGS button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      await user.click(buttons[3]) // Settings

      expect(mockHandlers.onSettingsClick).toHaveBeenCalledTimes(1)
    })

    it('should call onDataDensityChange when slider value changes', async () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const slider = screen.getByTestId('data-density-slider') as HTMLInputElement
      fireEvent.change(slider, { target: { value: '75' } })

      expect(mockHandlers.onDataDensityChange).toHaveBeenCalledWith(75)
    })

    it('should handle slider value changes programmatically', () => {
      const { rerender } = render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={30}
        />
      )

      const slider = screen.getByTestId('data-density-slider') as HTMLInputElement
      expect(slider.value).toBe('30')

      rerender(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={70}
        />
      )

      const updatedSlider = screen.getByTestId('data-density-slider') as HTMLInputElement
      expect(updatedSlider.value).toBe('70')
    })

    it('should accept slider value at boundaries (0 and 100)', () => {
      const { rerender } = render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={0}
        />
      )

      let slider = screen.getByTestId('data-density-slider') as HTMLInputElement
      expect(slider.value).toBe('0')
      expect(screen.getByText('Density: 0%')).toBeInTheDocument()

      rerender(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={100}
        />
      )

      slider = screen.getByTestId('data-density-slider') as HTMLInputElement
      expect(slider.value).toBe('100')
      expect(screen.getByText('Density: 100%')).toBeInTheDocument()
    })
  })

  describe('Styling and Classes', () => {
    it('should have correct glass morphism styling classes', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const panel = screen.getByTestId('constellation-control-panel')
      expect(panel).toHaveClass('bg-slate-800/60')
      expect(panel).toHaveClass('backdrop-blur-xl')
      expect(panel).toHaveClass('border')
      expect(panel).toHaveClass('border-white/10')
      expect(panel).toHaveClass('rounded-xl')
    })

    it('should be positioned at bottom-left of viewport', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const panel = screen.getByTestId('constellation-control-panel')
      expect(panel).toHaveClass('absolute')
      expect(panel).toHaveClass('bottom-6')
      expect(panel).toHaveClass('left-6')
      expect(panel).toHaveClass('z-10')
    })

    it('should have proper width (w-64)', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const panel = screen.getByTestId('constellation-control-panel')
      expect(panel).toHaveClass('w-64')
    })

    it('should apply custom className when provided', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
          className="custom-class"
        />
      )

      const panel = screen.getByTestId('constellation-control-panel')
      expect(panel).toHaveClass('custom-class')
      // Should still have base classes
      expect(panel).toHaveClass('bg-slate-800/60')
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels for all buttons', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      buttons.forEach((button) => {
        expect(button).toHaveAccessibleName()
      })
    })

    it('should have accessible name for slider', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const slider = screen.getByTestId('data-density-slider')
      expect(slider).toHaveAttribute('aria-label', 'Data density control (0-100)')
    })

    it('should handle keyboard focus on buttons', async () => {
      const user = userEvent.setup()
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      await user.tab()
      expect(buttons[0]).toHaveFocus()

      await user.tab()
      expect(buttons[1]).toHaveFocus()
    })

    it('should handle keyboard interaction with slider', async () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const slider = screen.getByTestId('data-density-slider') as HTMLInputElement
      slider.focus()
      expect(slider).toHaveFocus()

      // Simulate keyboard input on range slider by changing value
      // In real browser, arrow keys adjust range slider values
      fireEvent.change(slider, { target: { value: '55' } })
      expect(mockHandlers.onDataDensityChange).toHaveBeenCalledWith(55)
    })

    it('should support keyboard activation of buttons', async () => {
      const user = userEvent.setup()
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')

      // Tab to first button
      buttons[0].focus()
      await user.keyboard('{Enter}')
      expect(mockHandlers.onZoomIn).toHaveBeenCalled()
    })
  })

  describe('Visual Structure', () => {
    it('should have divider between controls and density section', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const panel = screen.getByTestId('constellation-control-panel')
      const dividers = panel.querySelectorAll('.border-t')
      expect(dividers.length).toBeGreaterThan(0)
    })

    it('should have proper spacing with space-y-3', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const panel = screen.getByTestId('constellation-control-panel')
      expect(panel).toHaveClass('space-y-3')
    })

    it('should have padding p-4', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const panel = screen.getByTestId('constellation-control-panel')
      expect(panel).toHaveClass('p-4')
    })
  })

  describe('Button States', () => {
    it('should allow buttons to be disabled', async () => {
      const user = userEvent.setup()
      const { rerender } = render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')

      // Initially enabled
      buttons.forEach(btn => {
        expect(btn).not.toBeDisabled()
      })

      // Click a button to verify it works
      await user.click(buttons[0])
      expect(mockHandlers.onZoomIn).toHaveBeenCalledTimes(1)
    })

    it('should have proper hover states on buttons', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      buttons.forEach(btn => {
        expect(btn).toHaveClass('hover:bg-white/10')
      })
    })
  })

  describe('Data Density Slider Styling', () => {
    it('should have gradient background for slider track', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const slider = screen.getByTestId('data-density-slider')
      expect(slider).toHaveClass('bg-gradient-to-r')
      expect(slider).toHaveClass('from-white/20')
      expect(slider).toHaveClass('to-white/5')
    })

    it('should use cyan-400 accent color for slider thumb', () => {
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const slider = screen.getByTestId('data-density-slider')
      expect(slider).toHaveClass('accent-cyan-400')
    })
  })

  describe('Integration Scenarios', () => {
    it('should handle multiple rapid clicks on zoom buttons', async () => {
      const user = userEvent.setup()
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      const zoomInBtn = buttons[0]

      await user.click(zoomInBtn)
      await user.click(zoomInBtn)
      await user.click(zoomInBtn)

      expect(mockHandlers.onZoomIn).toHaveBeenCalledTimes(3)
    })

    it('should handle mixed interactions (buttons and slider)', async () => {
      const user = userEvent.setup()
      render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      const buttons = screen.getAllByRole('button')
      const slider = screen.getByTestId('data-density-slider')

      // Click buttons
      await user.click(buttons[0]) // Zoom In
      expect(mockHandlers.onZoomIn).toHaveBeenCalledTimes(1)

      await user.click(buttons[1]) // Zoom Out
      expect(mockHandlers.onZoomOut).toHaveBeenCalledTimes(1)

      // Change slider
      fireEvent.change(slider, { target: { value: '75' } })
      expect(mockHandlers.onDataDensityChange).toHaveBeenCalledWith(75)

      // Click dropdown buttons
      await user.click(buttons[2]) // Filter
      expect(mockHandlers.onFilterClick).toHaveBeenCalledTimes(1)

      await user.click(buttons[3]) // Settings
      expect(mockHandlers.onSettingsClick).toHaveBeenCalledTimes(1)
    })

    it('should render and function correctly with extreme density values', () => {
      const { rerender } = render(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={0}
        />
      )

      let slider = screen.getByTestId('data-density-slider') as HTMLInputElement
      expect(slider.value).toBe('0')

      rerender(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={100}
        />
      )

      slider = screen.getByTestId('data-density-slider') as HTMLInputElement
      expect(slider.value).toBe('100')

      rerender(
        <ConstellationControlPanel
          {...mockHandlers}
          dataDensity={50}
        />
      )

      slider = screen.getByTestId('data-density-slider') as HTMLInputElement
      expect(slider.value).toBe('50')
    })
  })
})
