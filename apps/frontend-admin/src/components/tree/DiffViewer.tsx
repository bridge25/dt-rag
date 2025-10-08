'use client'

import { VersionComparison } from '@/services/taxonomyService'

interface DiffViewerProps {
  comparison: VersionComparison | null
  className?: string
}

export default function DiffViewer({ comparison, className = '' }: DiffViewerProps) {
  if (!comparison) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <p className="text-gray-500 text-center">Select two versions to compare</p>
      </div>
    )
  }

  const { changes, summary } = comparison

  return (
    <div className={`bg-white rounded-lg shadow p-6 space-y-6 ${className}`}>
      <div>
        <h3 className="text-lg font-bold text-gray-900 mb-2">Version Comparison</h3>
        <p className="text-sm text-gray-600">
          {comparison.base_version} → {comparison.target_version}
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="text-center p-3 bg-gray-50 rounded">
          <p className="text-2xl font-bold text-gray-700">{summary.total_changes}</p>
          <p className="text-xs text-gray-500">Total Changes</p>
        </div>
        <div className="text-center p-3 bg-green-50 rounded">
          <p className="text-2xl font-bold text-green-600">{summary.added_count}</p>
          <p className="text-xs text-gray-500">Added</p>
        </div>
        <div className="text-center p-3 bg-red-50 rounded">
          <p className="text-2xl font-bold text-red-600">{summary.removed_count}</p>
          <p className="text-xs text-gray-500">Removed</p>
        </div>
        <div className="text-center p-3 bg-yellow-50 rounded">
          <p className="text-2xl font-bold text-yellow-600">{summary.modified_count}</p>
          <p className="text-xs text-gray-500">Modified</p>
        </div>
      </div>

      {/* Added Nodes */}
      {changes.added.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-green-700 mb-2">✅ Added Nodes</h4>
          <div className="space-y-1">
            {changes.added.map((node) => (
              <div key={node.node_id} className="p-2 bg-green-50 rounded text-sm">
                <span className="font-medium text-green-800">{node.label}</span>
                <span className="text-green-600 text-xs ml-2">
                  {node.canonical_path.join(' → ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Removed Nodes */}
      {changes.removed.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-red-700 mb-2">❌ Removed Nodes</h4>
          <div className="space-y-1">
            {changes.removed.map((node) => (
              <div key={node.node_id} className="p-2 bg-red-50 rounded text-sm">
                <span className="font-medium text-red-800">{node.label}</span>
                <span className="text-red-600 text-xs ml-2">
                  {node.canonical_path.join(' → ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modified Nodes */}
      {changes.modified.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-yellow-700 mb-2">📝 Modified Nodes</h4>
          <div className="space-y-2">
            {changes.modified.map((item) => (
              <div key={item.node_id} className="p-3 bg-yellow-50 rounded">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-yellow-800 text-sm">
                    {item.old.label} → {item.new.label}
                  </span>
                </div>
                <div className="text-xs text-yellow-600">
                  <div className="line-through opacity-60">
                    {item.old.canonical_path.join(' → ')}
                  </div>
                  <div className="mt-1">
                    {item.new.canonical_path.join(' → ')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {summary.total_changes === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500">No changes between these versions</p>
        </div>
      )}
    </div>
  )
}
