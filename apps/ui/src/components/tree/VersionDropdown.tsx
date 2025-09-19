'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronDown,
  Check,
  Clock,
  GitBranch,
  AlertTriangle,
  Loader2
} from 'lucide-react'
import { useTaxonomyStore } from '@/stores/taxonomy-store'
import { TaxonomyVersion, VersionDiff } from '@/types/taxonomy'
import { cn } from '@/lib/utils'

interface VersionDropdownProps {
  versions: string[]
  currentVersion: string
  loading?: boolean
  onVersionChange?: (version: string) => void
  showDiff?: boolean
  className?: string
}

// Mock version data - in real app, this would come from API
const versionData: Record<string, TaxonomyVersion> = {
  'latest': {
    version: 'latest',
    status: 'stable',
    description: 'Latest stable version',
    created_at: new Date().toISOString(),
    node_count: 1247,
    document_count: 8934
  },
  '1.8.1': {
    version: '1.8.1',
    status: 'stable',
    description: 'Production stable version',
    created_at: '2025-09-05T00:00:00Z',
    node_count: 1205,
    document_count: 8456
  },
  '1.8.0': {
    version: '1.8.0',
    status: 'deprecated',
    description: 'Previous stable version',
    created_at: '2025-08-15T00:00:00Z',
    node_count: 1156,
    document_count: 7823
  },
  '1.7.9': {
    version: '1.7.9',
    status: 'deprecated',
    description: 'Legacy version',
    created_at: '2025-07-20T00:00:00Z',
    node_count: 1089,
    document_count: 7234
  }
}

export function VersionDropdown({
  versions,
  currentVersion,
  loading = false,
  onVersionChange,
  showDiff = true,
  className
}: VersionDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [showDiffModal, setShowDiffModal] = useState(false)
  const [compareVersion, setCompareVersion] = useState<string | null>(null)
  const { setCurrentVersion } = useTaxonomyStore()

  const handleVersionSelect = (version: string) => {
    setCurrentVersion(version)
    onVersionChange?.(version)
    setIsOpen(false)
  }

  const handleCompareVersions = (fromVersion: string, toVersion: string) => {
    setCompareVersion(fromVersion)
    setShowDiffModal(true)
  }

  const getStatusIcon = (status: TaxonomyVersion['status']) => {
    switch (status) {
      case 'stable':
        return <Check className="h-3 w-3 text-green-600" />
      case 'beta':
        return <Clock className="h-3 w-3 text-yellow-600" />
      case 'deprecated':
        return <AlertTriangle className="h-3 w-3 text-red-600" />
      default:
        return <GitBranch className="h-3 w-3 text-gray-600" />
    }
  }

  const getStatusColor = (status: TaxonomyVersion['status']) => {
    switch (status) {
      case 'stable':
        return 'text-green-600 bg-green-50'
      case 'beta':
        return 'text-yellow-600 bg-yellow-50'
      case 'deprecated':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const currentVersionData = versionData[currentVersion]

  return (
    <div className={cn("relative", className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={loading}
        className={cn(
          "flex items-center space-x-2 px-3 py-2 bg-background border rounded-md",
          "hover:bg-accent transition-colors",
          "focus:outline-none focus:ring-2 focus:ring-primary",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          isOpen && "ring-2 ring-primary"
        )}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={`Current version: ${currentVersion}`}
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          getStatusIcon(currentVersionData?.status || 'stable')
        )}
        <span className="font-medium text-sm">{currentVersion}</span>
        <ChevronDown className={cn(
          "h-4 w-4 transition-transform",
          isOpen && "rotate-180"
        )} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Overlay */}
            <div
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* Dropdown */}
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full mt-2 right-0 z-50 min-w-80 bg-background border rounded-lg shadow-lg"
              role="listbox"
              aria-label="Version selection"
            >
              <div className="p-2 border-b">
                <h3 className="font-medium text-sm text-foreground">Taxonomy Versions</h3>
                <p className="text-xs text-muted-foreground">Select a version to view</p>
              </div>

              <div className="max-h-80 overflow-y-auto">
                {versions.map((version) => {
                  const versionInfo = versionData[version]
                  const isSelected = version === currentVersion

                  return (
                    <div
                      key={version}
                      className={cn(
                        "flex items-center justify-between p-3 hover:bg-accent cursor-pointer",
                        "border-b border-border last:border-b-0",
                        isSelected && "bg-primary/5"
                      )}
                      onClick={() => handleVersionSelect(version)}
                      role="option"
                      aria-selected={isSelected}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          {getStatusIcon(versionInfo?.status || 'stable')}
                          <span className={cn(
                            "font-medium text-sm",
                            isSelected ? "text-primary" : "text-foreground"
                          )}>
                            {version}
                          </span>
                          {isSelected && (
                            <Check className="h-4 w-4 text-primary" />
                          )}
                        </div>

                        {versionInfo && (
                          <>
                            <p className="text-xs text-muted-foreground mb-2">
                              {versionInfo.description}
                            </p>
                            <div className="flex items-center space-x-3 text-xs text-muted-foreground">
                              <span>{formatDate(versionInfo.created_at)}</span>
                              {versionInfo.node_count && (
                                <span>{versionInfo.node_count.toLocaleString()} nodes</span>
                              )}
                              {versionInfo.document_count && (
                                <span>{versionInfo.document_count.toLocaleString()} docs</span>
                              )}
                            </div>
                          </>
                        )}
                      </div>

                      <div className="flex items-center space-x-2">
                        {versionInfo && (
                          <span className={cn(
                            "px-2 py-1 rounded text-xs font-medium",
                            getStatusColor(versionInfo.status)
                          )}>
                            {versionInfo.status}
                          </span>
                        )}

                        {showDiff && version !== currentVersion && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleCompareVersions(version, currentVersion)
                            }}
                            className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
                            aria-label={`Compare ${version} with ${currentVersion}`}
                          >
                            <GitBranch className="h-3 w-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>

              {versions.length === 0 && (
                <div className="p-4 text-center text-muted-foreground">
                  <GitBranch className="h-6 w-6 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No versions available</p>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Version Diff Modal */}
      <AnimatePresence>
        {showDiffModal && compareVersion && (
          <VersionDiffModal
            fromVersion={compareVersion}
            toVersion={currentVersion}
            onClose={() => setShowDiffModal(false)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

interface VersionDiffModalProps {
  fromVersion: string
  toVersion: string
  onClose: () => void
}

function VersionDiffModal({ fromVersion, toVersion, onClose }: VersionDiffModalProps) {
  // Mock diff data - in real app, this would come from API
  const mockDiff: VersionDiff = {
    version_from: fromVersion,
    version_to: toVersion,
    summary: {
      added: 42,
      removed: 8,
      modified: 23,
      moved: 5
    },
    changes: [
      {
        type: 'added',
        node_id: 'ai_new_001',
        path: ['AI', 'Machine Learning', 'Deep Learning'],
        new_value: 'Deep Learning',
        description: 'Added new deep learning taxonomy branch'
      },
      {
        type: 'modified',
        node_id: 'ai_ml_001',
        path: ['AI', 'ML'],
        old_value: 'Machine Learning',
        new_value: 'ML/AI',
        description: 'Updated node label for clarity'
      },
      {
        type: 'removed',
        node_id: 'ai_old_001',
        path: ['AI', 'Legacy'],
        old_value: 'Legacy AI',
        description: 'Removed deprecated taxonomy branch'
      }
    ]
  }

  const getChangeColor = (type: VersionDiff['changes'][0]['type']) => {
    switch (type) {
      case 'added':
        return 'text-green-600 bg-green-50'
      case 'removed':
        return 'text-red-600 bg-red-50'
      case 'modified':
        return 'text-blue-600 bg-blue-50'
      case 'moved':
        return 'text-purple-600 bg-purple-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/50 z-50" onClick={onClose} />

      {/* Modal */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <div className="bg-background border rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
          {/* Header */}
          <div className="p-6 border-b">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">Version Comparison</h2>
                <p className="text-sm text-muted-foreground">
                  {fromVersion} → {toVersion}
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-accent rounded-md"
                aria-label="Close diff modal"
              >
                ×
              </button>
            </div>

            {/* Summary */}
            <div className="mt-4 grid grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{mockDiff.summary.added}</div>
                <div className="text-xs text-muted-foreground">Added</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{mockDiff.summary.removed}</div>
                <div className="text-xs text-muted-foreground">Removed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{mockDiff.summary.modified}</div>
                <div className="text-xs text-muted-foreground">Modified</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{mockDiff.summary.moved}</div>
                <div className="text-xs text-muted-foreground">Moved</div>
              </div>
            </div>
          </div>

          {/* Changes */}
          <div className="p-6 overflow-y-auto max-h-96">
            <div className="space-y-3">
              {mockDiff.changes.map((change, index) => (
                <div
                  key={index}
                  className="border rounded-lg p-4"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className={cn(
                        "px-2 py-1 rounded text-xs font-medium capitalize",
                        getChangeColor(change.type)
                      )}>
                        {change.type}
                      </span>
                      <span className="text-sm text-muted-foreground">
                        {change.path.join(' → ')}
                      </span>
                    </div>
                  </div>

                  <p className="text-sm text-muted-foreground mb-2">
                    {change.description}
                  </p>

                  <div className="space-y-1 text-sm">
                    {change.old_value && (
                      <div className="flex items-center space-x-2">
                        <span className="text-red-600">-</span>
                        <span className="bg-red-50 text-red-900 px-2 py-1 rounded">
                          {change.old_value}
                        </span>
                      </div>
                    )}
                    {change.new_value && (
                      <div className="flex items-center space-x-2">
                        <span className="text-green-600">+</span>
                        <span className="bg-green-50 text-green-900 px-2 py-1 rounded">
                          {change.new_value}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </>
  )
}