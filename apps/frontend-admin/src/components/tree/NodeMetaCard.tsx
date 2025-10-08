'use client'

import { TaxonomyNode } from '@/services/taxonomyService'

interface NodeMetaCardProps {
  node: TaxonomyNode | null
  className?: string
}

export default function NodeMetaCard({ node, className = '' }: NodeMetaCardProps) {
  if (!node) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <p className="text-gray-500 text-center">Select a node to view details</p>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 space-y-4 ${className}`}>
      <div>
        <h3 className="text-lg font-bold text-gray-900 mb-2">{node.label}</h3>
        <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
          {node.version}
        </span>
      </div>

      <div className="space-y-2">
        <div>
          <label className="text-sm font-medium text-gray-600">Node ID:</label>
          <p className="text-sm text-gray-800 font-mono break-all">{node.node_id}</p>
        </div>

        <div>
          <label className="text-sm font-medium text-gray-600">Canonical Path:</label>
          <div className="flex items-center space-x-1 mt-1">
            {node.canonical_path.map((part, idx) => (
              <span key={idx} className="flex items-center">
                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                  {part}
                </span>
                {idx < node.canonical_path.length - 1 && (
                  <span className="text-gray-400 mx-1">→</span>
                )}
              </span>
            ))}
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-gray-600">Depth:</label>
          <p className="text-sm text-gray-800">{node.canonical_path.length}</p>
        </div>
      </div>

      <div className="pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Note: Document count and confidence data will be available in Phase 4.2
        </p>
      </div>
    </div>
  )
}
