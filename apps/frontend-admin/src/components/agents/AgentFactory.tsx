'use client'

import React, { useState, useEffect } from 'react'
import { Play, Save, FileText, Settings, AlertCircle, CheckCircle, Clock, Eye } from 'lucide-react'

interface AgentManifest {
  id: string
  name: string
  description: string
  version: string
  author: string
  category: 'classification' | 'search' | 'analysis' | 'custom'
  status: 'draft' | 'testing' | 'active' | 'deprecated'
  config: {
    model: string
    temperature: number
    maxTokens: number
    systemPrompt: string
    tools: string[]
  }
  testResults?: {
    accuracy: number
    latency: number
    lastTested: string
    sampleCount: number
  }
  createdAt: string
  updatedAt: string
}

// Mock 데이터
const MOCK_AGENTS: AgentManifest[] = [
  {
    id: 'agent-1',
    name: 'Taxonomy Classifier v1.2',
    description: 'High-accuracy document classification agent for taxonomy assignment',
    version: '1.2.0',
    author: 'Team A',
    category: 'classification',
    status: 'active',
    config: {
      model: 'gpt-4-turbo-preview',
      temperature: 0.1,
      maxTokens: 1000,
      systemPrompt: 'You are an expert taxonomy classifier. Analyze the given text and assign the most appropriate taxonomy path.',
      tools: ['text-splitter', 'embedding-search', 'confidence-scorer']
    },
    testResults: {
      accuracy: 0.94,
      latency: 1200,
      lastTested: '2025-01-15T10:30:00Z',
      sampleCount: 500
    },
    createdAt: '2025-01-10T09:00:00Z',
    updatedAt: '2025-01-15T11:00:00Z'
  },
  {
    id: 'agent-2',
    name: 'RAG Search Engine v2.1',
    description: 'Advanced search agent with semantic understanding',
    version: '2.1.0',
    author: 'Team B',
    category: 'search',
    status: 'testing',
    config: {
      model: 'gpt-4',
      temperature: 0.3,
      maxTokens: 2000,
      systemPrompt: 'You are a search expert. Find the most relevant documents based on user queries.',
      tools: ['vector-search', 'reranker', 'result-formatter']
    },
    testResults: {
      accuracy: 0.87,
      latency: 800,
      lastTested: '2025-01-14T15:20:00Z',
      sampleCount: 200
    },
    createdAt: '2025-01-12T14:00:00Z',
    updatedAt: '2025-01-14T16:00:00Z'
  },
  {
    id: 'agent-3',
    name: 'Document Analyzer v1.0',
    description: 'Comprehensive document analysis and metadata extraction',
    version: '1.0.0',
    author: 'Team C',
    category: 'analysis',
    status: 'draft',
    config: {
      model: 'gpt-3.5-turbo',
      temperature: 0.2,
      maxTokens: 1500,
      systemPrompt: 'Analyze documents and extract key metadata, themes, and structure.',
      tools: ['text-parser', 'entity-extractor', 'sentiment-analyzer']
    },
    createdAt: '2025-01-16T08:00:00Z',
    updatedAt: '2025-01-16T08:00:00Z'
  }
]

const STATUS_COLORS = {
  draft: { bg: 'bg-gray-100', text: 'text-gray-700', icon: FileText },
  testing: { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: Clock },
  active: { bg: 'bg-green-100', text: 'text-green-700', icon: CheckCircle },
  deprecated: { bg: 'bg-red-100', text: 'text-red-700', icon: AlertCircle }
}

const CATEGORY_COLORS = {
  classification: 'bg-blue-100 text-blue-700',
  search: 'bg-purple-100 text-purple-700',
  analysis: 'bg-orange-100 text-orange-700',
  custom: 'bg-gray-100 text-gray-700'
}

export function AgentFactory() {
  const [agents, setAgents] = useState<AgentManifest[]>(MOCK_AGENTS)
  const [selectedAgent, setSelectedAgent] = useState<AgentManifest | null>(null)
  const [showManifest, setShowManifest] = useState(false)
  const [filter, setFilter] = useState<string>('all')
  const [isCreating, setIsCreating] = useState(false)

  const filteredAgents = agents.filter(agent => 
    filter === 'all' || agent.category === filter || agent.status === filter
  )

  const handleCreateAgent = () => {
    setIsCreating(true)
    // TODO: Implement agent creation modal
  }

  const handleTestAgent = async (agentId: string) => {
    // TODO: Implement agent testing
    console.log('Testing agent:', agentId)
  }

  const handleDeployAgent = async (agentId: string) => {
    // TODO: Implement agent deployment
    console.log('Deploying agent:', agentId)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Agent Factory</h1>
          <p className="text-gray-600">AI 에이전트 생성, 테스트 및 배포 관리</p>
        </div>
        <button
          onClick={handleCreateAgent}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-2"
        >
          <Settings className="w-4 h-4" />
          <span>새 에이전트 생성</span>
        </button>
      </div>

      {/* 필터 */}
      <div className="flex items-center space-x-4 mb-6">
        <span className="text-sm font-medium text-gray-700">필터:</span>
        <div className="flex space-x-2">
          {[
            { value: 'all', label: '전체' },
            { value: 'classification', label: '분류' },
            { value: 'search', label: '검색' },
            { value: 'analysis', label: '분석' },
            { value: 'active', label: '활성' },
            { value: 'testing', label: '테스트중' }
          ].map(option => (
            <button
              key={option.value}
              onClick={() => setFilter(option.value)}
              className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
                filter === option.value
                  ? 'bg-blue-100 text-blue-700 border-blue-300'
                  : 'bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 왼쪽: 에이전트 목록 */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">에이전트 목록</h2>
          
          <div className="space-y-3">
            {filteredAgents.map(agent => {
              const StatusIcon = STATUS_COLORS[agent.status].icon
              
              return (
                <div
                  key={agent.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-all ${
                    selectedAgent?.id === agent.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                  onClick={() => setSelectedAgent(agent)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="font-medium text-gray-900">{agent.name}</h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${CATEGORY_COLORS[agent.category]}`}>
                          {agent.category}
                        </span>
                        <div className={`flex items-center space-x-1 px-2 py-1 text-xs rounded-full ${STATUS_COLORS[agent.status].bg} ${STATUS_COLORS[agent.status].text}`}>
                          <StatusIcon className="w-3 h-3" />
                          <span>{agent.status}</span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 mb-3">{agent.description}</p>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span>v{agent.version}</span>
                          <span>{agent.author}</span>
                          <span>업데이트: {formatDate(agent.updatedAt)}</span>
                        </div>
                        
                        {agent.testResults && (
                          <div className="flex items-center space-x-3 text-xs">
                            <span className="text-green-600">
                              정확도: {(agent.testResults.accuracy * 100).toFixed(1)}%
                            </span>
                            <span className="text-blue-600">
                              응답시간: {agent.testResults.latency}ms
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-end space-x-2 mt-3 pt-3 border-t border-gray-100">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedAgent(agent)
                        setShowManifest(true)
                      }}
                      className="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors flex items-center space-x-1"
                    >
                      <Eye className="w-3 h-3" />
                      <span>Manifest</span>
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleTestAgent(agent.id)
                      }}
                      className="px-3 py-1.5 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 transition-colors flex items-center space-x-1"
                    >
                      <Play className="w-3 h-3" />
                      <span>테스트</span>
                    </button>
                    
                    {agent.status === 'testing' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeployAgent(agent.id)
                        }}
                        className="px-3 py-1.5 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors flex items-center space-x-1"
                      >
                        <Save className="w-3 h-3" />
                        <span>배포</span>
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* 오른쪽: 에이전트 상세 정보 */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">에이전트 상세</h2>
          
          {selectedAgent ? (
            <div className="space-y-4">
              <div>
                <h3 className="font-medium text-gray-900 mb-1">{selectedAgent.name}</h3>
                <p className="text-sm text-gray-600">{selectedAgent.description}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">버전:</span>
                  <span className="ml-2 font-mono">{selectedAgent.version}</span>
                </div>
                <div>
                  <span className="text-gray-500">작성자:</span>
                  <span className="ml-2">{selectedAgent.author}</span>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900 mb-2">설정</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">모델:</span>
                    <span className="font-mono">{selectedAgent.config.model}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Temperature:</span>
                    <span className="font-mono">{selectedAgent.config.temperature}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Max Tokens:</span>
                    <span className="font-mono">{selectedAgent.config.maxTokens}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900 mb-2">도구</h4>
                <div className="flex flex-wrap gap-1">
                  {selectedAgent.config.tools.map(tool => (
                    <span key={tool} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
              
              {selectedAgent.testResults && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">테스트 결과</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">정확도:</span>
                      <span className="text-green-600 font-semibold">
                        {(selectedAgent.testResults.accuracy * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">평균 응답시간:</span>
                      <span className="text-blue-600">{selectedAgent.testResults.latency}ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">샘플 수:</span>
                      <span>{selectedAgent.testResults.sampleCount}개</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">마지막 테스트:</span>
                      <span className="text-xs">{formatDate(selectedAgent.testResults.lastTested)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <Settings className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>에이전트를 선택해주세요</p>
            </div>
          )}
        </div>
      </div>

      {/* Manifest 미리보기 모달 */}
      {showManifest && selectedAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Agent Manifest: {selectedAgent.name}</h3>
              <button
                onClick={() => setShowManifest(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto font-mono">
{JSON.stringify(selectedAgent, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}