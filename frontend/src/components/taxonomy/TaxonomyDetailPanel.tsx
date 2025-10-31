// @CODE:TAXONOMY-VIZ-001-007
// Taxonomy Detail Panel - displays selected node information

import { type TaxonomyNode } from '../../lib/api/types'

interface TaxonomyDetailPanelProps {
  node: TaxonomyNode | null
  onClose: () => void
}

export default function TaxonomyDetailPanel({
  node,
  onClose,
}: TaxonomyDetailPanelProps) {
  if (!node) return null

  return (
    <div
      data-testid="detail-panel"
      className="absolute right-0 top-0 z-10 h-full w-80 border-l border-gray-200 bg-white shadow-lg"
    >
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <h3 className="text-lg font-semibold text-gray-900">Node Details</h3>
          <button
            onClick={onClose}
            aria-label="Close detail panel"
            className="rounded-lg p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          <div className="space-y-4">
            {/* Node Name */}
            <div>
              <label className="text-xs font-medium uppercase text-gray-500">
                Name
              </label>
              <p className="mt-1 text-sm text-gray-900">{node.name}</p>
            </div>

            {/* Level */}
            <div>
              <label className="text-xs font-medium uppercase text-gray-500">
                Level
              </label>
              <p className="mt-1 text-sm text-gray-900">Level {node.level}</p>
            </div>

            {/* Path */}
            <div>
              <label className="text-xs font-medium uppercase text-gray-500">
                Path
              </label>
              <div className="mt-1 flex flex-wrap gap-1">
                {node.path.map((segment, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-1 text-sm text-gray-700"
                  >
                    {segment}
                    {index < node.path.length - 1 && (
                      <svg
                        className="h-3 w-3 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    )}
                  </span>
                ))}
              </div>
            </div>

            {/* Document Count */}
            <div>
              <label className="text-xs font-medium uppercase text-gray-500">
                Documents
              </label>
              <p className="mt-1 text-sm text-gray-900">
                {node.document_count ?? 0} documents
              </p>
            </div>

            {/* Children Count */}
            {node.children && node.children.length > 0 && (
              <div>
                <label className="text-xs font-medium uppercase text-gray-500">
                  Subcategories
                </label>
                <p className="mt-1 text-sm text-gray-900">
                  {node.children.length} subcategories
                </p>
              </div>
            )}

            {/* Metadata */}
            {node.metadata && Object.keys(node.metadata).length > 0 && (
              <div>
                <label className="text-xs font-medium uppercase text-gray-500">
                  Metadata
                </label>
                <div className="mt-1 space-y-1">
                  {Object.entries(node.metadata).map(([key, value]) => (
                    <div key={key} className="text-sm">
                      <span className="font-medium text-gray-700">{key}:</span>{' '}
                      <span className="text-gray-600">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
