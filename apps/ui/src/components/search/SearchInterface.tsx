'use client'

import React, { useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  Filter,
  X,
  Clock,
  BookOpen,
  TrendingUp,
  Download,
  Share,
  Bookmark,
  ChevronDown,
  ChevronUp,
  ExternalLink
} from 'lucide-react'
import { useSearchStore } from '@/stores/search-store'
import { SearchHit, SearchFilters, SavedSearch } from '@/types/search'
import { SearchResults } from './SearchResults'
import { SearchFiltersPanel } from './SearchFiltersPanel'
import { SavedSearches } from './SavedSearches'
import { cn } from '@/lib/utils'

interface SearchInterfaceProps {
  className?: string
  onResultSelect?: (hit: SearchHit) => void
  autoFocus?: boolean
  showFilters?: boolean
  showSavedSearches?: boolean
}

export function SearchInterface({
  className,
  onResultSelect,
  autoFocus = false,
  showFilters = true,
  showSavedSearches = true
}: SearchInterfaceProps) {
  const {
    query,
    results,
    loading,
    error,
    filters,
    facets,
    totalResults,
    page,
    pageSize,
    recentQueries,
    savedSearches,
    setQuery,
    setResults,
    setLoading,
    setError,
    addRecentQuery,
    hasActiveFilters,
    clearAllFilters
  } = useSearchStore()

  const [localQuery, setLocalQuery] = useState(query)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [showFiltersPanel, setShowFiltersPanel] = useState(false)
  const [showSavedSearchesPanel, setShowSavedSearchesPanel] = useState(false)
  const [searchDebounceTimer, setSearchDebounceTimer] = useState<NodeJS.Timeout | null>(null)

  const searchInputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  // Auto-focus search input
  useEffect(() => {
    if (autoFocus && searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }, [autoFocus])

  // Debounced search
  useEffect(() => {
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer)
    }

    if (localQuery.trim()) {
      const timer = setTimeout(() => {
        performSearch(localQuery)
      }, 300)
      setSearchDebounceTimer(timer)
    } else {
      setQuery('')
      setResults([])
    }

    return () => {
      if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
    }
  }, [localQuery])

  // Click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const performSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) return

    setLoading(true)
    setError(null)
    setQuery(searchQuery)

    try {
      // Mock API call - replace with actual search API
      await new Promise(resolve => setTimeout(resolve, 500))

      const mockResults: SearchHit[] = [
        {
          chunk_id: 'chunk_001',
          score: 0.95,
          text: 'This is a sample search result about taxonomy and classification systems...',
          taxonomy_path: ['AI', 'Machine Learning', 'Classification'],
          source: {
            title: 'Introduction to AI Classification',
            source_url: 'https://example.com/ai-classification',
            search_type: 'hybrid'
          }
        },
        {
          chunk_id: 'chunk_002',
          score: 0.87,
          text: 'Another relevant result discussing hierarchical taxonomies and their applications...',
          taxonomy_path: ['AI', 'Taxonomy', 'Hierarchical'],
          source: {
            title: 'Hierarchical Taxonomy Systems',
            source_url: 'https://example.com/hierarchical-tax',
            search_type: 'vector'
          }
        }
      ]

      setResults(mockResults)
      addRecentQuery(searchQuery)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setLoading(false)
    }
  }, [setLoading, setError, setQuery, setResults, addRecentQuery])

  const handleSearchSubmit = useCallback((event: React.FormEvent) => {
    event.preventDefault()
    if (localQuery.trim()) {
      performSearch(localQuery)
      setShowSuggestions(false)
    }
  }, [localQuery, performSearch])

  const handleSuggestionSelect = useCallback((suggestion: string) => {
    setLocalQuery(suggestion)
    setShowSuggestions(false)
    performSearch(suggestion)
  }, [performSearch])

  const handleSavedSearchSelect = useCallback((savedSearch: SavedSearch) => {
    setLocalQuery(savedSearch.query)
    performSearch(savedSearch.query)
    setShowSavedSearchesPanel(false)
  }, [performSearch])

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      setShowSuggestions(false)
      searchInputRef.current?.blur()
    }
  }, [])

  const getSuggestions = () => {
    if (!localQuery.trim()) return recentQueries.slice(0, 5)

    return recentQueries
      .filter(q => q.toLowerCase().includes(localQuery.toLowerCase()))
      .slice(0, 5)
  }

  return (
    <div className={cn("flex flex-col space-y-4", className)}>
      {/* Search Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold">Document Search</h1>
          {totalResults > 0 && (
            <span className="text-muted-foreground">
              {totalResults.toLocaleString()} results
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {showSavedSearches && (
            <button
              onClick={() => setShowSavedSearchesPanel(!showSavedSearchesPanel)}
              className={cn(
                "flex items-center space-x-2 px-3 py-2 rounded-md border",
                "hover:bg-accent transition-colors",
                showSavedSearchesPanel && "bg-accent"
              )}
            >
              <Bookmark className="h-4 w-4" />
              <span className="text-sm">Saved</span>
            </button>
          )}

          {showFilters && (
            <button
              onClick={() => setShowFiltersPanel(!showFiltersPanel)}
              className={cn(
                "flex items-center space-x-2 px-3 py-2 rounded-md border",
                "hover:bg-accent transition-colors",
                (showFiltersPanel || hasActiveFilters()) && "bg-accent"
              )}
            >
              <Filter className="h-4 w-4" />
              <span className="text-sm">Filters</span>
              {hasActiveFilters() && (
                <span className="bg-primary text-primary-foreground text-xs px-1.5 py-0.5 rounded">
                  {Object.keys(filters).length}
                </span>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Search Form */}
      <div className="relative" ref={suggestionsRef}>
        <form onSubmit={handleSearchSubmit} className="relative">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search documents and taxonomy..."
              value={localQuery}
              onChange={(e) => setLocalQuery(e.target.value)}
              onFocus={() => setShowSuggestions(true)}
              onKeyDown={handleKeyDown}
              className={cn(
                "w-full pl-12 pr-12 py-3 text-lg border rounded-lg",
                "focus:outline-none focus:ring-2 focus:ring-primary",
                "placeholder:text-muted-foreground"
              )}
              aria-label="Search documents"
              autoComplete="off"
            />
            {localQuery && (
              <button
                type="button"
                onClick={() => {
                  setLocalQuery('')
                  setQuery('')
                  setResults([])
                }}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 p-1 hover:bg-accent rounded"
                aria-label="Clear search"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {loading && (
            <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
            </div>
          )}
        </form>

        {/* Search Suggestions */}
        <AnimatePresence>
          {showSuggestions && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute top-full mt-2 w-full bg-background border rounded-lg shadow-lg z-50"
            >
              {getSuggestions().length > 0 ? (
                <div className="p-2">
                  <div className="flex items-center space-x-2 px-3 py-2 text-sm text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    <span>Recent searches</span>
                  </div>
                  {getSuggestions().map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionSelect(suggestion)}
                      className="w-full text-left px-3 py-2 hover:bg-accent rounded-md transition-colors"
                    >
                      <span className="text-sm">{suggestion}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-muted-foreground">
                  <Search className="h-6 w-6 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No recent searches</p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Active Filters */}
      {hasActiveFilters() && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="flex items-center space-x-2 p-3 bg-accent/50 rounded-lg"
        >
          <span className="text-sm font-medium">Active filters:</span>
          <div className="flex-1 flex items-center space-x-2">
            {/* Show active filter tags */}
            {Object.entries(filters).map(([key, value]) => (
              <span
                key={key}
                className="px-2 py-1 bg-primary text-primary-foreground text-xs rounded"
              >
                {key}: {Array.isArray(value) ? value.length : '1'} selected
              </span>
            ))}
          </div>
          <button
            onClick={clearAllFilters}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Clear all
          </button>
        </motion.div>
      )}

      {/* Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Panel */}
        <AnimatePresence>
          {showFiltersPanel && (
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="lg:col-span-1"
            >
              <SearchFiltersPanel />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <div className={cn(
          "transition-all duration-300",
          showFiltersPanel ? "lg:col-span-3" : "lg:col-span-4"
        )}>
          {/* Error State */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg"
            >
              <div className="flex items-center space-x-2 text-destructive">
                <X className="h-5 w-5" />
                <span className="font-medium">Search Error</span>
              </div>
              <p className="text-sm mt-1">{error}</p>
            </motion.div>
          )}

          {/* Results */}
          {!error && (
            <SearchResults
              results={results}
              loading={loading}
              query={query}
              totalResults={totalResults}
              onResultSelect={onResultSelect}
            />
          )}
        </div>
      </div>

      {/* Saved Searches Panel */}
      <AnimatePresence>
        {showSavedSearchesPanel && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
          >
            <SavedSearches
              savedSearches={savedSearches}
              onSearchSelect={handleSavedSearchSelect}
              onClose={() => setShowSavedSearchesPanel(false)}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}