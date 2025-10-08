'use client'

import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import TreePanel from '@/components/tree/TreePanel'
import VersionDropdown from '@/components/tree/VersionDropdown'
import NodeMetaCard from '@/components/tree/NodeMetaCard'
import { LoadingOverlay } from '@/components/ui/LoadingSpinner'
import { taxonomyService, TaxonomyNode, TaxonomyVersion } from '@/services/taxonomyService'
import { useToast } from '@/contexts/ToastContext'
import { getErrorMessage, isAbortError } from '@/lib/errorHandler'

export default function TaxonomyPage() {
  const [versions, setVersions] = useState<TaxonomyVersion[]>([])
  const [currentVersion, setCurrentVersion] = useState<string>('1.0.0')
  const [nodes, setNodes] = useState<TaxonomyNode[]>([])
  const [selectedNode, setSelectedNode] = useState<TaxonomyNode | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [initialLoadComplete, setInitialLoadComplete] = useState(false)
  const abortControllerRef = useRef<AbortController>()
  const { showToast } = useToast()

  useEffect(() => {
    const controller = new AbortController()
    abortControllerRef.current = controller

    const loadInitialData = async () => {
      try {
        const data = await taxonomyService.getVersions()
        if (controller.signal.aborted) return

        setVersions(data.versions)

        if (data.versions.length > 0) {
          const firstVersion = data.versions[0].version
          setCurrentVersion(firstVersion)

          const tree = await taxonomyService.getTree(firstVersion)
          if (controller.signal.aborted) return

          setNodes(tree.nodes)
        }

        setInitialLoadComplete(true)
      } catch (err: any) {
        if (isAbortError(err)) return
        const message = getErrorMessage(err)
        setError(message)
        showToast(`데이터 로드 실패: ${message}`, 'error')
        console.error(err)
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    loadInitialData()

    return () => {
      controller.abort()
    }
  }, [])

  useEffect(() => {
    if (!initialLoadComplete) return

    if (currentVersion) {
      const controller = new AbortController()
      abortControllerRef.current = controller
      loadTree(currentVersion, controller.signal)

      return () => {
        controller.abort()
      }
    }
  }, [currentVersion, initialLoadComplete])

  const loadTree = useCallback(async (version: string, signal?: AbortSignal) => {
    setLoading(true)
    setError(null)
    try {
      const tree = await taxonomyService.getTree(version)
      if (signal?.aborted) return
      setNodes(tree.nodes)
      showToast(`버전 ${version} 로드 완료`, 'success')
    } catch (err: any) {
      if (isAbortError(err)) return
      const message = getErrorMessage(err)
      setError(message)
      showToast(`트리 로드 실패: ${message}`, 'error')
      console.error(err)
    } finally {
      if (!signal?.aborted) {
        setLoading(false)
      }
    }
  }, [showToast])

  const maxDepth = useMemo(() => {
    if (nodes.length === 0) return 0
    return Math.max(...nodes.map(n => n.canonical_path.length))
  }, [nodes])

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            🗂️ Taxonomy Tree Viewer
          </h1>
          <p className="text-gray-600 mb-4">
            Hierarchical taxonomy management and visualization
          </p>

          {/* Version Selector */}
          <VersionDropdown
            versions={versions}
            currentVersion={currentVersion}
            onVersionChange={setCurrentVersion}
          />
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">❌ {error}</p>
          </div>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tree Panel */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">
                Taxonomy Tree
              </h2>

              {loading ? (
                <LoadingOverlay message="Loading taxonomy tree..." />
              ) : (
                <TreePanel
                  nodes={nodes}
                  onNodeSelect={setSelectedNode}
                />
              )}
            </div>
          </div>

          {/* Node Details */}
          <div className="lg:col-span-1">
            <h2 className="text-lg font-bold text-gray-900 mb-4">
              Node Details
            </h2>
            <NodeMetaCard node={selectedNode} />
          </div>
        </div>

        {/* Statistics */}
        {!loading && nodes.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Statistics</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded">
                <p className="text-2xl font-bold text-blue-600">{nodes.length}</p>
                <p className="text-sm text-gray-600">Total Nodes</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded">
                <p className="text-2xl font-bold text-green-600">{currentVersion}</p>
                <p className="text-sm text-gray-600">Version</p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded">
                <p className="text-2xl font-bold text-purple-600">
                  {maxDepth}
                </p>
                <p className="text-sm text-gray-600">Max Depth</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
