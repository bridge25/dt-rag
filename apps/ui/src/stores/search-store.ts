'use client'

import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import {
  SearchState,
  SearchHit,
  SearchFilters,
  SearchFacets,
  SavedSearch,
  SearchMetrics
} from '@/types/search'

interface SearchStoreState extends SearchState {
  // Additional state
  recentQueries: string[]
  savedSearches: SavedSearch[]
  searchHistory: Array<{
    query: string
    timestamp: string
    resultsCount: number
  }>
  metrics: SearchMetrics | null

  // Actions
  setQuery: (query: string) => void
  setResults: (results: SearchHit[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setFilters: (filters: SearchFilters) => void
  setFacets: (facets: SearchFacets) => void
  setTotalResults: (total: number) => void
  setPage: (page: number) => void
  setPageSize: (pageSize: number) => void

  // Search operations
  addToHistory: (query: string, resultsCount: number) => void
  addRecentQuery: (query: string) => void
  clearRecentQueries: () => void

  // Saved searches
  saveSearch: (name: string, description?: string) => void
  deleteSavedSearch: (id: string) => void
  loadSavedSearch: (search: SavedSearch) => void

  // Facet operations
  toggleFacetValue: (facetType: keyof SearchFacets, value: any) => void
  clearAllFilters: () => void

  // Utility functions
  getSelectedFacetValues: (facetType: keyof SearchFacets) => any[]
  hasActiveFilters: () => boolean
  getCurrentSearchParams: () => {
    query: string
    filters: SearchFilters
    page: number
    pageSize: number
  }
}

export const useSearchStore = create<SearchStoreState>()(
  devtools(
    (set, get) => ({
      // Initial state
      query: '',
      results: [],
      loading: false,
      error: null,
      filters: {},
      facets: {
        taxonomy_paths: [],
        sources: [],
        document_types: []
      },
      totalResults: 0,
      page: 1,
      pageSize: 20,
      recentQueries: [],
      savedSearches: [],
      searchHistory: [],
      metrics: null,

      // Basic setters
      setQuery: (query) => set({ query }),
      setResults: (results) => set({ results }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      setFilters: (filters) => set({ filters }),
      setFacets: (facets) => set({ facets }),
      setTotalResults: (totalResults) => set({ totalResults }),
      setPage: (page) => set({ page }),
      setPageSize: (pageSize) => set({ pageSize, page: 1 }), // Reset page when changing page size

      // Search operations
      addToHistory: (query, resultsCount) => {
        const state = get()
        const newEntry = {
          query,
          timestamp: new Date().toISOString(),
          resultsCount
        }

        const filteredHistory = state.searchHistory.filter(
          entry => entry.query !== query
        )

        set({
          searchHistory: [newEntry, ...filteredHistory].slice(0, 50) // Keep last 50 searches
        })
      },

      addRecentQuery: (query) => {
        if (!query.trim()) return

        const state = get()
        const filtered = state.recentQueries.filter(q => q !== query)

        set({
          recentQueries: [query, ...filtered].slice(0, 10) // Keep last 10 queries
        })
      },

      clearRecentQueries: () => set({ recentQueries: [] }),

      // Saved searches
      saveSearch: (name, description) => {
        const state = get()
        const newSearch: SavedSearch = {
          id: `search_${Date.now()}`,
          name,
          query: state.query,
          filters: state.filters,
          created_at: new Date().toISOString(),
          created_by: 'current_user', // TODO: Get from auth context
          description,
          is_public: false
        }

        set({
          savedSearches: [...state.savedSearches, newSearch]
        })
      },

      deleteSavedSearch: (id) => {
        const state = get()
        set({
          savedSearches: state.savedSearches.filter(search => search.id !== id)
        })
      },

      loadSavedSearch: (search) => {
        set({
          query: search.query,
          filters: search.filters,
          page: 1
        })
      },

      // Facet operations
      toggleFacetValue: (facetType, value) => {
        const state = get()
        const facets = { ...state.facets }

        if (facetType === 'taxonomy_paths') {
          facets.taxonomy_paths = facets.taxonomy_paths.map(facet =>
            JSON.stringify(facet.path) === JSON.stringify(value.path)
              ? { ...facet, selected: !facet.selected }
              : facet
          )

          // Update filters
          const selectedPaths = facets.taxonomy_paths
            .filter(f => f.selected)
            .map(f => f.path)

          set({
            facets,
            filters: {
              ...state.filters,
              taxonomy_paths: selectedPaths.length > 0 ? selectedPaths : undefined
            },
            page: 1
          })
        } else if (facetType === 'sources') {
          facets.sources = facets.sources.map(facet =>
            facet.name === value.name
              ? { ...facet, selected: !facet.selected }
              : facet
          )

          const selectedSources = facets.sources
            .filter(f => f.selected)
            .map(f => f.name)

          set({
            facets,
            filters: {
              ...state.filters,
              sources: selectedSources.length > 0 ? selectedSources : undefined
            },
            page: 1
          })
        } else if (facetType === 'document_types') {
          facets.document_types = facets.document_types.map(facet =>
            facet.type === value.type
              ? { ...facet, selected: !facet.selected }
              : facet
          )

          const selectedTypes = facets.document_types
            .filter(f => f.selected)
            .map(f => f.type)

          set({
            facets,
            filters: {
              ...state.filters,
              document_types: selectedTypes.length > 0 ? selectedTypes : undefined
            },
            page: 1
          })
        }
      },

      clearAllFilters: () => {
        const state = get()
        const clearedFacets = {
          taxonomy_paths: state.facets.taxonomy_paths.map(f => ({ ...f, selected: false })),
          sources: state.facets.sources.map(f => ({ ...f, selected: false })),
          document_types: state.facets.document_types.map(f => ({ ...f, selected: false }))
        }

        set({
          filters: {},
          facets: clearedFacets,
          page: 1
        })
      },

      // Utility functions
      getSelectedFacetValues: (facetType) => {
        const state = get()
        const facets = state.facets[facetType]

        if (facetType === 'taxonomy_paths') {
          return facets.filter(f => f.selected).map(f => f.path)
        } else if (facetType === 'sources') {
          return facets.filter(f => f.selected).map(f => f.name)
        } else if (facetType === 'document_types') {
          return facets.filter(f => f.selected).map(f => f.type)
        }

        return []
      },

      hasActiveFilters: () => {
        const state = get()
        return Object.keys(state.filters).some(key => {
          const value = state.filters[key as keyof SearchFilters]
          return value !== undefined && value !== null &&
                 (Array.isArray(value) ? value.length > 0 : true)
        })
      },

      getCurrentSearchParams: () => {
        const state = get()
        return {
          query: state.query,
          filters: state.filters,
          page: state.page,
          pageSize: state.pageSize
        }
      }
    }),
    {
      name: 'search-store'
    }
  )
)