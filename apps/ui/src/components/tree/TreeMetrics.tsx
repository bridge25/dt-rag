'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, Eye, ExpandAll, MousePointer } from 'lucide-react'
import { TaxonomyNode } from '@/types/taxonomy'
import { useTaxonomyStore } from '@/stores/taxonomy-store'
import { formatNumber, formatPercentage } from '@/lib/utils'

interface TreeMetricsProps {
  totalNodes: number
  visibleNodes: number
  expandedCount: number
  selectedNode: TaxonomyNode | null
}

export function TreeMetrics({
  totalNodes,
  visibleNodes,
  expandedCount,
  selectedNode
}: TreeMetricsProps) {
  const { metrics } = useTaxonomyStore()

  const expansionRate = totalNodes > 0 ? expandedCount / totalNodes : 0

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-accent/30 rounded-lg border"
    >
      {/* Total Nodes */}
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
          <TrendingUp className="h-4 w-4 text-blue-600" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Total</p>
          <p className="text-sm font-medium">{formatNumber(totalNodes)}</p>
        </div>
      </div>

      {/* Visible Nodes */}
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
          <Eye className="h-4 w-4 text-green-600" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Visible</p>
          <p className="text-sm font-medium">{formatNumber(visibleNodes)}</p>
        </div>
      </div>

      {/* Expanded Nodes */}
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
          <ExpandAll className="h-4 w-4 text-purple-600" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Expanded</p>
          <p className="text-sm font-medium">{formatNumber(expandedCount)}</p>
        </div>
      </div>

      {/* Performance */}
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
          <MousePointer className="h-4 w-4 text-orange-600" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Render</p>
          <p className="text-sm font-medium">
            {metrics?.render_time ? `${metrics.render_time.toFixed(1)}ms` : 'N/A'}
          </p>
        </div>
      </div>

      {/* Additional Metrics */}
      {metrics && (
        <>
          <div className="md:col-span-2 flex items-center justify-between text-xs text-muted-foreground">
            <span>Expansion Rate:</span>
            <span className="font-medium">{formatPercentage(expansionRate)}</span>
          </div>

          <div className="md:col-span-2 flex items-center justify-between text-xs text-muted-foreground">
            <span>Virtual Items:</span>
            <span className="font-medium">{formatNumber(metrics.virtual_items_count)}</span>
          </div>
        </>
      )}

      {/* Selected Node Info */}
      {selectedNode && (
        <div className="md:col-span-4 pt-2 border-t border-border">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Selected:</span>
            <span className="font-medium truncate ml-2">{selectedNode.label}</span>
          </div>
          <div className="flex items-center justify-between text-xs mt-1">
            <span className="text-muted-foreground">Confidence:</span>
            <span className="font-medium">{formatPercentage(selectedNode.confidence)}</span>
          </div>
        </div>
      )}
    </motion.div>
  )
}