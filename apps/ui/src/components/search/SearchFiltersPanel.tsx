'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { X, Filter, RotateCcw } from 'lucide-react'
import { useSearchStore } from '@/stores/search-store'
import { Button, Input, Label, Checkbox } from '@/components/ui'

export function SearchFiltersPanel() {
  const {
    filters,
    facets,
    setFilters,
    toggleFacetValue,
    clearAllFilters,
    hasActiveFilters
  } = useSearchStore()

  const updateFilter = (key: string, value: any) => {
    setFilters({ ...filters, [key]: value })
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="space-y-6 p-4 border rounded-lg bg-background"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4" />
          <h3 className="font-medium">Filters</h3>
        </div>
        {hasActiveFilters() && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearAllFilters}
            className="h-8 px-2"
          >
            <RotateCcw className="h-3 w-3 mr-1" />
            Clear
          </Button>
        )}
      </div>

      {/* Taxonomy Paths */}
      {facets.taxonomy_paths.length > 0 && (
        <div className="space-y-3">
          <Label className="text-sm font-medium">Taxonomy Paths</Label>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {facets.taxonomy_paths.map((facet, index) => (
              <div key={index} className="flex items-center space-x-2">
                <Checkbox
                  id={`taxonomy-${index}`}
                  checked={facet.selected}
                  onCheckedChange={() => toggleFacetValue('taxonomy_paths', facet)}
                />
                <Label
                  htmlFor={`taxonomy-${index}`}
                  className="text-xs flex-1 cursor-pointer"
                >
                  {facet.path.join(' → ')} ({facet.count})
                </Label>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sources */}
      {facets.sources.length > 0 && (
        <div className="space-y-3">
          <Label className="text-sm font-medium">Sources</Label>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {facets.sources.map((facet, index) => (
              <div key={index} className="flex items-center space-x-2">
                <Checkbox
                  id={`source-${index}`}
                  checked={facet.selected}
                  onCheckedChange={() => toggleFacetValue('sources', facet)}
                />
                <Label
                  htmlFor={`source-${index}`}
                  className="text-xs flex-1 cursor-pointer"
                >
                  {facet.name} ({facet.count})
                </Label>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Document Types */}
      {facets.document_types.length > 0 && (
        <div className="space-y-3">
          <Label className="text-sm font-medium">Document Types</Label>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {facets.document_types.map((facet, index) => (
              <div key={index} className="flex items-center space-x-2">
                <Checkbox
                  id={`type-${index}`}
                  checked={facet.selected}
                  onCheckedChange={() => toggleFacetValue('document_types', facet)}
                />
                <Label
                  htmlFor={`type-${index}`}
                  className="text-xs flex-1 cursor-pointer"
                >
                  {facet.type} ({facet.count})
                </Label>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Confidence Range */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Confidence Range</Label>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label htmlFor="confidence-min" className="text-xs">Min</Label>
            <Input
              id="confidence-min"
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={filters.confidence_min || ''}
              onChange={(e) => updateFilter('confidence_min', parseFloat(e.target.value) || undefined)}
              placeholder="0.0"
              className="h-8"
            />
          </div>
          <div>
            <Label htmlFor="confidence-max" className="text-xs">Max</Label>
            <Input
              id="confidence-max"
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={filters.confidence_max || ''}
              onChange={(e) => updateFilter('confidence_max', parseFloat(e.target.value) || undefined)}
              placeholder="1.0"
              className="h-8"
            />
          </div>
        </div>
      </div>

      {/* Date Range */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Date Range</Label>
        <div className="grid grid-cols-1 gap-2">
          <div>
            <Label htmlFor="date-from" className="text-xs">From</Label>
            <Input
              id="date-from"
              type="date"
              value={filters.date_from || ''}
              onChange={(e) => updateFilter('date_from', e.target.value || undefined)}
              className="h-8"
            />
          </div>
          <div>
            <Label htmlFor="date-to" className="text-xs">To</Label>
            <Input
              id="date-to"
              type="date"
              value={filters.date_to || ''}
              onChange={(e) => updateFilter('date_to', e.target.value || undefined)}
              className="h-8"
            />
          </div>
        </div>
      </div>

      {/* Active Filters Summary */}
      {hasActiveFilters() && (
        <div className="pt-3 border-t border-border">
          <p className="text-xs text-muted-foreground mb-2">Active filters:</p>
          <div className="flex flex-wrap gap-1">
            {Object.entries(filters).map(([key, value]) => {
              if (value === undefined || value === null) return null

              let displayValue = value
              if (Array.isArray(value)) {
                displayValue = `${value.length} selected`
              } else if (typeof value === 'number') {
                displayValue = value.toString()
              }

              return (
                <span
                  key={key}
                  className="inline-flex items-center px-2 py-1 bg-primary/10 text-primary text-xs rounded"
                >
                  {key}: {displayValue}
                  <button
                    onClick={() => updateFilter(key, undefined)}
                    className="ml-1 hover:bg-primary/20 rounded"
                  >
                    <X className="h-2 w-2" />
                  </button>
                </span>
              )
            })}
          </div>
        </div>
      )}
    </motion.div>
  )
}