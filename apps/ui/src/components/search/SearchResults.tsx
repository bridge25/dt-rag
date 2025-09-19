'use client'

import React from 'react'
import { motion } from 'framer-motion'
import {
  FileText,
  ExternalLink,
  TrendingUp,
  Clock,
  ChevronRight,
  Copy,
  Download,
  Bookmark
} from 'lucide-react'
import { SearchHit } from '@/types/search'
import { formatPercentage, formatRelativeTime, highlightText, copyToClipboard } from '@/lib/utils'
import { useToast } from '@/providers/ToastProvider'
import { cn } from '@/lib/utils'

interface SearchResultsProps {
  results: SearchHit[]
  loading: boolean
  query: string
  totalResults: number
  onResultSelect?: (hit: SearchHit) => void
}

export function SearchResults({
  results,
  loading,
  query,
  totalResults,
  onResultSelect
}: SearchResultsProps) {
  const { addToast } = useToast()

  const handleCopyText = async (text: string) => {
    try {
      await copyToClipboard(text)
      addToast({
        type: 'success',
        title: 'Copied to clipboard',
        description: 'Text has been copied to your clipboard'
      })
    } catch (error) {
      addToast({
        type: 'error',
        title: 'Copy failed',
        description: 'Failed to copy text to clipboard'
      })
    }
  }

  const handleSaveResult = (hit: SearchHit) => {
    // TODO: Implement save functionality
    addToast({
      type: 'info',
      title: 'Feature coming soon',
      description: 'Save search results functionality will be available soon'
    })
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, index) => (
          <div key={index} className="border rounded-lg p-6 bg-background">
            <div className="animate-pulse space-y-3">
              <div className="h-4 bg-accent rounded w-3/4"></div>
              <div className="h-3 bg-accent rounded w-1/2"></div>
              <div className="space-y-2">
                <div className="h-3 bg-accent rounded"></div>
                <div className="h-3 bg-accent rounded w-5/6"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (results.length === 0 && query) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
        <h3 className="text-lg font-medium text-muted-foreground mb-2">No results found</h3>
        <p className="text-sm text-muted-foreground">
          Try adjusting your search terms or filters to find what you're looking for.
        </p>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
        <h3 className="text-lg font-medium text-muted-foreground mb-2">Start searching</h3>
        <p className="text-sm text-muted-foreground">
          Enter a search query to find relevant documents and content.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Results header */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Showing {results.length} of {totalResults.toLocaleString()} results
        </p>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              // TODO: Implement export functionality
              addToast({
                type: 'info',
                title: 'Feature coming soon',
                description: 'Export results functionality will be available soon'
              })
            }}
            className="flex items-center space-x-1 px-2 py-1 text-xs hover:bg-accent rounded-md"
          >
            <Download className="h-3 w-3" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="space-y-4">
        {results.map((hit, index) => (
          <SearchResultCard
            key={hit.chunk_id}
            hit={hit}
            query={query}
            index={index}
            onSelect={onResultSelect}
            onCopy={handleCopyText}
            onSave={handleSaveResult}
          />
        ))}
      </div>

      {/* Load more */}
      {results.length < totalResults && (
        <div className="text-center py-4">
          <button className="btn btn-outline">
            Load more results
          </button>
        </div>
      )}
    </div>
  )
}

interface SearchResultCardProps {
  hit: SearchHit
  query: string
  index: number
  onSelect?: (hit: SearchHit) => void
  onCopy: (text: string) => void
  onSave: (hit: SearchHit) => void
}

function SearchResultCard({
  hit,
  query,
  index,
  onSelect,
  onCopy,
  onSave
}: SearchResultCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50'
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getSearchTypeIcon = (type?: string) => {
    switch (type) {
      case 'vector':
        return '🧠'
      case 'bm25':
        return '📝'
      case 'hybrid':
        return '🔄'
      default:
        return '🔍'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={cn(
        "border rounded-lg p-6 bg-background hover:shadow-md transition-shadow",
        "cursor-pointer"
      )}
      onClick={() => onSelect?.(hit)}
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-2">
              <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <h3 className="font-medium text-foreground truncate">
                {hit.source?.title || `Document ${hit.chunk_id}`}
              </h3>
              {hit.source?.source_url && (
                <a
                  href={hit.source.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>

            {/* Taxonomy path */}
            {hit.taxonomy_path && (
              <div className="flex items-center space-x-1 text-xs text-muted-foreground mb-2">
                {hit.taxonomy_path.map((segment, idx) => (
                  <React.Fragment key={idx}>
                    <span className="px-1.5 py-0.5 bg-accent rounded text-foreground">
                      {segment}
                    </span>
                    {idx < hit.taxonomy_path!.length - 1 && (
                      <ChevronRight className="h-3 w-3" />
                    )}
                  </React.Fragment>
                ))}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-2 ml-4">
            {/* Score */}
            <div className="flex items-center space-x-1">
              <TrendingUp className="h-3 w-3 text-muted-foreground" />
              <span className={cn(
                "px-2 py-1 rounded text-xs font-medium",
                getScoreColor(hit.score)
              )}>
                {formatPercentage(hit.score)}
              </span>
            </div>

            {/* Search type */}
            <span
              className="text-xs px-2 py-1 bg-accent rounded"
              title={`Search type: ${hit.source?.search_type || 'unknown'}`}
            >
              {getSearchTypeIcon(hit.source?.search_type)}
            </span>
          </div>
        </div>

        {/* Content */}
        {hit.text && (
          <div className="text-sm text-foreground leading-relaxed">
            <p
              dangerouslySetInnerHTML={{
                __html: highlightText(hit.text, query)
              }}
            />
          </div>
        )}

        {/* Highlights */}
        {hit.highlights && hit.highlights.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Highlights
            </h4>
            {hit.highlights.map((highlight, idx) => (
              <div key={idx} className="text-xs bg-accent/50 rounded p-2">
                <span className="font-medium text-muted-foreground">{highlight.field}:</span>
                {highlight.fragments.map((fragment, fragIdx) => (
                  <p
                    key={fragIdx}
                    className="mt-1"
                    dangerouslySetInnerHTML={{
                      __html: highlightText(fragment, query)
                    }}
                  />
                ))}
              </div>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-border">
          <div className="flex items-center space-x-4 text-xs text-muted-foreground">
            <span>ID: {hit.chunk_id}</span>
            {hit.timestamp && (
              <div className="flex items-center space-x-1">
                <Clock className="h-3 w-3" />
                <span>{formatRelativeTime(hit.timestamp)}</span>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-1">
            <button
              onClick={(e) => {
                e.stopPropagation()
                onCopy(hit.text || hit.source?.title || hit.chunk_id)
              }}
              className="p-1 hover:bg-accent rounded"
              title="Copy text"
            >
              <Copy className="h-3 w-3" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onSave(hit)
              }}
              className="p-1 hover:bg-accent rounded"
              title="Save result"
            >
              <Bookmark className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  )
}