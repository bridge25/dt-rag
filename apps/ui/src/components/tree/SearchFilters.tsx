'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { Slider, Label, Checkbox, Input, Button } from '@/components/ui'
import { useTaxonomyStore } from '@/stores/taxonomy-store'
import { SearchFilters as SearchFiltersType } from '@/types/taxonomy'

export function SearchFilters() {
  const { filters, setFilters } = useTaxonomyStore()

  const updateFilter = <K extends keyof SearchFiltersType>(
    key: K,
    value: SearchFiltersType[K]
  ) => {
    setFilters({ ...filters, [key]: value })
  }

  const clearFilters = () => {
    setFilters({})
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-4 p-4 border rounded-lg bg-accent/30"
    >
      <div className="flex items-center justify-between">
        <h3 className="font-medium">Search Filters</h3>
        <Button variant="ghost" size="sm" onClick={clearFilters}>
          Clear All
        </Button>
      </div>

      {/* Confidence Range */}
      <div className="space-y-2">
        <Label>Confidence Range</Label>
        <div className="px-2">
          <Slider
            value={[filters.confidence_min || 0, filters.confidence_max || 1]}
            min={0}
            max={1}
            step={0.01}
            onValueChange={([min, max]) => {
              updateFilter('confidence_min', min)
              updateFilter('confidence_max', max)
            }}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>{((filters.confidence_min || 0) * 100).toFixed(0)}%</span>
            <span>{((filters.confidence_max || 1) * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>

      {/* Document Count */}
      <div className="space-y-2">
        <Label htmlFor="doc-count">Minimum Document Count</Label>
        <Input
          id="doc-count"
          type="number"
          min="0"
          value={filters.document_count_min || ''}
          onChange={(e) => updateFilter('document_count_min', parseInt(e.target.value) || 0)}
          placeholder="0"
        />
      </div>

      {/* Max Depth */}
      <div className="space-y-2">
        <Label htmlFor="max-depth">Maximum Depth</Label>
        <Input
          id="max-depth"
          type="number"
          min="0"
          max="10"
          value={filters.depth_max || ''}
          onChange={(e) => updateFilter('depth_max', parseInt(e.target.value) || undefined)}
          placeholder="No limit"
        />
      </div>

      {/* Has Children */}
      <div className="flex items-center space-x-2">
        <Checkbox
          id="has-children"
          checked={filters.has_children === true}
          onCheckedChange={(checked) => {
            if (checked === true) {
              updateFilter('has_children', true)
            } else if (checked === false) {
              updateFilter('has_children', false)
            } else {
              updateFilter('has_children', undefined)
            }
          }}
        />
        <Label htmlFor="has-children">Only nodes with children</Label>
      </div>
    </motion.div>
  )
}