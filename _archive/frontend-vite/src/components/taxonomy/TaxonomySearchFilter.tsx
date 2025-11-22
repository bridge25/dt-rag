/**
 * Taxonomy Search Filter - search and highlight nodes by name
 * Accessibility: aria-live for match count, focus ring for clear button, WCAG 2.1 AA compliant
 * Tab order: First interactive element in TaxonomyTreeView
 * Focus indicators: Blue ring (focus:ring-1) and border (focus:border-blue-500)
 *
 * @CODE:TAXONOMY-VIZ-001
 */

import { useState, useCallback } from 'react'

interface TaxonomySearchFilterProps {
  onSearch: (query: string) => void
  matchCount: number
}

export default function TaxonomySearchFilter({
  onSearch,
  matchCount,
}: TaxonomySearchFilterProps) {
  const [query, setQuery] = useState('')

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value
      setQuery(value)
      onSearch(value)
    },
    [onSearch]
  )

  const handleClear = useCallback(() => {
    setQuery('')
    onSearch('')
  }, [onSearch])

  return (
    <div
      data-testid="search-filter"
      className="absolute left-4 top-4 z-10 w-80"
    >
      <div className="flex flex-col gap-2 rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
        {/* Search Input */}
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={handleChange}
            placeholder="Search taxonomy nodes..."
            aria-label="Search taxonomy nodes"
            className="w-full rounded-md border border-gray-300 px-3 py-2 pr-20 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          {query && (
            <button
              onClick={handleClear}
              aria-label="Clear search"
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>

        {/* Match Count */}
        {query && (
          <div
            className="text-xs text-gray-600"
            role="status"
            aria-live="polite"
            aria-atomic="true"
          >
            {matchCount === 0 ? (
              <span className="text-red-600">No matches found</span>
            ) : (
              <span>
                Found {matchCount} {matchCount === 1 ? 'match' : 'matches'}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
