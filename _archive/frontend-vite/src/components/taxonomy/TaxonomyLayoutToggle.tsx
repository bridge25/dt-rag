/**
 * Layout toggle button - switch between tree (Dagre) and radial (D3 Force) layouts
 * Accessibility: aria-hidden for decorative SVGs, WCAG 2.1 AA compliant
 * Tab order: Second interactive element after Search Filter
 * Focus indicators: Blue ring (focus:ring-2) with offset (focus:ring-offset-2)
 *
 * @CODE:TAXONOMY-VIZ-001
 */

import type { LayoutType } from './taxonomyLayouts'

interface TaxonomyLayoutToggleProps {
  currentLayout: LayoutType
  onLayoutChange: (layout: LayoutType) => void
}

export default function TaxonomyLayoutToggle({
  currentLayout,
  onLayoutChange,
}: TaxonomyLayoutToggleProps) {
  const handleToggle = () => {
    const newLayout: LayoutType = currentLayout === 'tree' ? 'radial' : 'tree'
    onLayoutChange(newLayout)
  }

  return (
    <div className="absolute left-1/2 top-4 z-10 -translate-x-1/2 transform">
      <button
        onClick={handleToggle}
        className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-md transition-all hover:bg-gray-50 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        aria-label={`Switch to ${currentLayout === 'tree' ? 'radial' : 'tree'} layout`}
      >
        {currentLayout === 'tree' ? (
          <>
            <svg
              className="h-5 w-5 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"
              />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <span>Switch to Radial Layout</span>
          </>
        ) : (
          <>
            <svg
              className="h-5 w-5 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 2v20M5 9l7-7 7 7M5 15l7 7 7-7"
              />
            </svg>
            <span>Switch to Tree Layout</span>
          </>
        )}
      </button>
    </div>
  )
}
