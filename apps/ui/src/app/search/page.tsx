'use client'

import React from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { SearchInterface } from '@/components/search/SearchInterface'
import { SearchHit } from '@/types/search'

export default function SearchPage() {
  const handleResultSelect = (hit: SearchHit) => {
    console.log('Selected search result:', hit)
    // TODO: Implement result selection behavior (open document, show details, etc.)
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Document Search</h1>
            <p className="text-muted-foreground">
              Search through classified documents using advanced hybrid search with BM25 and vector similarity.
            </p>
          </div>
        </div>

        <SearchInterface
          onResultSelect={handleResultSelect}
          autoFocus={true}
          showFilters={true}
          showSavedSearches={true}
        />
      </div>
    </AppLayout>
  )
}