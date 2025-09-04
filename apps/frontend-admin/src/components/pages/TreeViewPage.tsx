'use client'

import React, { useState, useEffect } from 'react'
import { TreeView } from '@/components/tree/TreeView'
import { taxonomyService } from '@/services/taxonomy.service'
import type { TaxonomyTree } from '@/types/common'

// Mock 데이터 (A팀 API 준비 전까지 사용) - 이미지 참조 구조
const MOCK_VERSIONS = ['Version 4', 'Version 3', 'Version 2']

const MOCK_TREE: TaxonomyTree = {
  version: 'Version 4',
  total_nodes: 7,
  total_documents: 0,
  nodes: [
    // Root 노드
    {
      node_id: 'root',
      label: 'Root',
      canonical_path: ['Root'],
      version: 'Version 4',
      confidence: 1.0,
      document_count: undefined
    },
    // Node 1, 2, 3
    {
      node_id: 'node1',
      label: 'Node 1',
      canonical_path: ['Root', 'Node 1'],
      version: 'Version 4',
      confidence: 1.0,
      document_count: undefined
    },
    {
      node_id: 'node2',
      label: 'Node 2',
      canonical_path: ['Root', 'Node 2'],
      version: 'Version 4',
      confidence: 1.0,
      document_count: undefined
    },
    {
      node_id: 'node3',
      label: 'Node 3',
      canonical_path: ['Root', 'Node 3'],
      version: 'Version 4',
      confidence: 1.0,
      document_count: undefined
    },
    // Node 1 하위: AI, RAG
    {
      node_id: 'ai',
      label: 'AI',
      canonical_path: ['Root', 'Node 1', 'AI'],
      version: 'Version 4',
      confidence: 1.0,
      document_count: undefined
    },
    {
      node_id: 'rag',
      label: 'RAG',
      canonical_path: ['Root', 'Node 1', 'RAG'],
      version: 'Version 4',
      confidence: 1.0,
      document_count: undefined
    },
    // Node 2 하위: Taxonomy, A3C
    {
      node_id: 'taxonomy',
      label: 'Taxonomy',
      canonical_path: ['Root', 'Node 2', 'Taxonomy'],
      version: 'Version 4',
      confidence: 1.0,
      document_count: undefined
    },
    {
      node_id: 'a3c',
      label: 'A3C',
      canonical_path: ['Root', 'Node 2', 'A3C'],
      version: 'Version 4',
      confidence: 1.0,
      document_count: undefined
    }
  ],
  edges: [
    // Root -> Node 1, 2, 3
    { parent: 'root', child: 'node1', version: 'Version 4' },
    { parent: 'root', child: 'node2', version: 'Version 4' },
    { parent: 'root', child: 'node3', version: 'Version 4' },
    // Node 1 -> AI, RAG
    { parent: 'node1', child: 'ai', version: 'Version 4' },
    { parent: 'node1', child: 'rag', version: 'Version 4' },
    // Node 2 -> Taxonomy, A3C
    { parent: 'node2', child: 'taxonomy', version: 'Version 4' },
    { parent: 'node2', child: 'a3c', version: 'Version 4' }
  ]
}

export function TreeViewPage() {
  const [tree, setTree] = useState<TaxonomyTree | null>(null)
  const [versions, setVersions] = useState<string[]>([])
  const [currentVersion, setCurrentVersion] = useState<string>('Version 4')
  const [loading, setLoading] = useState(false)

  // Mock 모드 확인
  const isMockMode = process.env.NEXT_PUBLIC_MOCK_MODE === 'true'

  useEffect(() => {
    loadVersions()
  }, [])

  useEffect(() => {
    if (currentVersion) {
      loadTree(currentVersion)
    }
  }, [currentVersion])

  const loadVersions = async () => {
    try {
      if (isMockMode) {
        setVersions(MOCK_VERSIONS)
        return
      }
      
      const versionList = await taxonomyService.getVersions()
      setVersions(versionList)
    } catch (error) {
      console.error('버전 목록 로딩 실패:', error)
      // Fallback to mock data
      setVersions(MOCK_VERSIONS)
    }
  }

  const loadTree = async (version: string) => {
    setLoading(true)
    try {
      if (isMockMode) {
        // Mock 데이터에 지연 시뮬레이션
        await new Promise(resolve => setTimeout(resolve, 500))
        setTree({ ...MOCK_TREE, version })
        return
      }
      
      const treeData = await taxonomyService.getTree(version)
      setTree(treeData)
    } catch (error) {
      console.error('트리 데이터 로딩 실패:', error)
      // Fallback to mock data
      setTree({ ...MOCK_TREE, version })
    } finally {
      setLoading(false)
    }
  }

  const handleVersionChange = (version: string) => {
    setCurrentVersion(version)
  }

  return (
    <div className="flex h-screen bg-white">
      {/* 왼쪽 사이드바 - TreeView */}
      <div className="w-80 bg-gray-100 border-r border-gray-200 flex flex-col">
        {/* 사이드바 헤더 */}
        <div className="p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-gray-700 uppercase tracking-wide">
              STORYBOOK
            </h2>
            <button className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
          
          {/* Filter 입력 */}
          <div className="relative">
            <input
              type="text"
              placeholder="Filter"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            />
          </div>
        </div>

        {/* 트리뷰 */}
        <div className="flex-1 overflow-hidden">
          <TreeView
            tree={tree}
            versions={versions}
            currentVersion={currentVersion}
            onVersionChange={handleVersionChange}
            loading={loading}
            sidebarMode={true}
          />
        </div>
      </div>

      {/* 오른쪽 컨텐츠 영역 */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {/* 상단 탭 영역 */}
        <div className="bg-white border-b border-gray-200 px-6 py-3 shadow-sm">
          <div className="flex items-center space-x-1 text-sm">
            <span className="px-3 py-1.5 bg-gray-100 text-gray-800 rounded font-medium">revlon test</span>
            <span className="text-gray-400 mx-1">›</span>
            <span className="px-2 py-1 text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded cursor-pointer transition-colors">revlon</span>
            <span className="text-gray-400 mx-1">›</span>
            <span className="px-2 py-1 text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded cursor-pointer transition-colors">revlon-lipstick</span>
            <span className="text-gray-400 mx-1">›</span>
            <span className="px-2 py-1 text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded cursor-pointer transition-colors">revlon-mascara</span>
            <div className="ml-6 flex items-center space-x-1">
              <span className="text-gray-400 mx-1">›</span>
              <span className="px-2 py-1 text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded cursor-pointer transition-colors">revlon-eye-pencil</span>
              <span className="text-gray-400 mx-1">›</span>
              <span className="px-2 py-1 text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded cursor-pointer transition-colors">revlon-eye-pencilcil</span>
            </div>
            <div className="ml-6 flex items-center space-x-1">
              <span className="text-gray-400 mx-1">›</span>
              <span className="px-2 py-1 text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded cursor-pointer transition-colors">revlon2</span>
              <span className="text-gray-400 mx-1">›</span>
              <span className="px-2 py-1 text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded cursor-pointer transition-colors">revlon-lipstick2</span>
            </div>
          </div>
        </div>

        {/* 메인 컨텐츠 */}
        <div className="flex-1 p-6">
          <div className="h-full bg-white rounded-lg shadow-sm border border-gray-200 flex items-center justify-center">
            <p className="text-gray-500">TreeView 컨텐츠 영역</p>
          </div>
        </div>
      </div>
    </div>
  )
}