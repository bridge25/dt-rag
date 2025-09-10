'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Send, RotateCcw, Settings, ExternalLink, CheckCircle, AlertTriangle, MessageSquare, User, Bot } from 'lucide-react'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: SourceDocument[]
  accuracy?: number
}

interface SourceDocument {
  id: string
  title: string
  url?: string
  excerpt: string
  relevanceScore: number
  taxonomyPath: string[]
}

// Mock 데이터
const MOCK_SOURCES: SourceDocument[] = [
  {
    id: 'doc-1',
    title: 'Dynamic Taxonomy Architecture Guide',
    url: 'https://docs.example.com/taxonomy-guide',
    excerpt: 'Dynamic taxonomies allow for real-time classification updates based on document content evolution...',
    relevanceScore: 0.94,
    taxonomyPath: ['Root', 'AI', 'Machine Learning', 'Taxonomy']
  },
  {
    id: 'doc-2',
    title: 'RAG Implementation Best Practices',
    excerpt: 'Retrieval-Augmented Generation systems require careful balance between retrieval accuracy and response quality...',
    relevanceScore: 0.87,
    taxonomyPath: ['Root', 'AI', 'RAG Systems']
  },
  {
    id: 'doc-3',
    title: 'Classification Accuracy Metrics',
    excerpt: 'Measuring classification accuracy in dynamic systems requires consideration of temporal drift...',
    relevanceScore: 0.82,
    taxonomyPath: ['Root', 'AI', 'Evaluation']
  }
]

const MOCK_CONVERSATION: ChatMessage[] = [
  {
    id: 'msg-1',
    role: 'user',
    content: 'What are the best practices for implementing dynamic taxonomy systems?',
    timestamp: '2025-01-15T14:30:00Z'
  },
  {
    id: 'msg-2',
    role: 'assistant',
    content: 'Based on the latest documentation, here are the key best practices for implementing dynamic taxonomy systems:\n\n1. **Incremental Updates**: Implement systems that can handle taxonomy changes without full reindexing\n2. **Version Management**: Maintain clear versioning for taxonomy changes\n3. **Confidence Scoring**: Include confidence metrics for all classifications\n4. **Human-in-the-Loop**: Set up review queues for low-confidence classifications\n\nThese approaches ensure system reliability while maintaining flexibility for evolving classification needs.',
    timestamp: '2025-01-15T14:30:15Z',
    sources: MOCK_SOURCES.slice(0, 2),
    accuracy: 0.94
  }
]

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>(MOCK_CONVERSATION)
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showSources, setShowSources] = useState(true)
  const [accuracyThreshold, setAccuracyThreshold] = useState(0.8)
  const [showSettings, setShowSettings] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    // Mock API response
    setTimeout(() => {
      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: 'This is a mock response for demonstration. In a real implementation, this would be connected to your RAG system API.',
        timestamp: new Date().toISOString(),
        sources: MOCK_SOURCES.slice(0, Math.floor(Math.random() * 3) + 1),
        accuracy: 0.85 + Math.random() * 0.1
      }

      setMessages(prev => [...prev, assistantMessage])
      setIsLoading(false)
    }, 1500)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const clearConversation = () => {
    setMessages([])
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      day: '2-digit',
      month: '2-digit'
    })
  }

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 0.9) return 'text-green-600'
    if (accuracy >= 0.8) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getAccuracyIcon = (accuracy: number) => {
    if (accuracy >= accuracyThreshold) return CheckCircle
    return AlertTriangle
  }

  return (
    <div className="flex h-full bg-gray-50">
      {/* 메인 채팅 영역 */}
      <div className="flex-1 flex flex-col">
        {/* 채팅 헤더 */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-lg font-semibold text-gray-900">RAG Chat Interface</h1>
              <p className="text-sm text-gray-600">AI 지원 문서 검색 및 질의응답</p>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">소스 표시:</span>
                <button
                  onClick={() => setShowSources(!showSources)}
                  className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                    showSources
                      ? 'bg-blue-100 text-blue-700 border-blue-300'
                      : 'bg-gray-100 text-gray-600 border-gray-300'
                  }`}
                >
                  {showSources ? 'ON' : 'OFF'}
                </button>
              </div>
              
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
              >
                <Settings className="w-5 h-5" />
              </button>
              
              <button
                onClick={clearConversation}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
              >
                <RotateCcw className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* 메시지 영역 */}
        <div className="flex-1 overflow-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <MessageSquare className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">대화를 시작해보세요</h3>
              <p className="text-gray-600">RAG 시스템에 질문을 입력하여 문서 기반 답변을 받아보세요.</p>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-3xl ${message.role === 'user' ? 'order-2' : 'order-1'}`}>
                  {/* 메시지 헤더 */}
                  <div className={`flex items-center space-x-2 mb-2 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {message.role === 'user' ? (
                      <>
                        <span className="text-sm text-gray-500">{formatTimestamp(message.timestamp)}</span>
                        <User className="w-4 h-4 text-gray-600" />
                        <span className="text-sm font-medium text-gray-700">You</span>
                      </>
                    ) : (
                      <>
                        <Bot className="w-4 h-4 text-blue-600" />
                        <span className="text-sm font-medium text-gray-700">AI Assistant</span>
                        <span className="text-sm text-gray-500">{formatTimestamp(message.timestamp)}</span>
                        {message.accuracy && (
                          <div className="flex items-center space-x-1">
                            {React.createElement(getAccuracyIcon(message.accuracy), {
                              className: `w-4 h-4 ${getAccuracyColor(message.accuracy)}`
                            })}
                            <span className={`text-sm font-medium ${getAccuracyColor(message.accuracy)}`}>
                              {Math.round(message.accuracy * 100)}%
                            </span>
                          </div>
                        )}
                      </>
                    )}
                  </div>

                  {/* 메시지 내용 */}
                  <div className={`p-4 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-200 shadow-sm'
                  }`}>
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    
                    {/* 소스 문서 표시 */}
                    {message.sources && showSources && (
                      <div className="mt-4 pt-4 border-t border-gray-100">
                        <div className="text-sm text-gray-600 mb-3 font-medium">참조 문서:</div>
                        <div className="space-y-2">
                          {message.sources.map((source) => (
                            <div key={source.id} className="p-3 bg-gray-50 rounded border">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <h4 className="font-medium text-gray-900 text-sm">{source.title}</h4>
                                    {source.url && (
                                      <a
                                        href={source.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:text-blue-800"
                                      >
                                        <ExternalLink className="w-3 h-3" />
                                      </a>
                                    )}
                                  </div>
                                  <p className="text-gray-600 text-xs mb-2">{source.excerpt}</p>
                                  <div className="flex items-center justify-between">
                                    <div className="text-xs text-gray-500">
                                      {source.taxonomyPath.join(' > ')}
                                    </div>
                                    <div className="text-xs font-medium text-green-600">
                                      {Math.round(source.relevanceScore * 100)}% 관련성
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="max-w-3xl">
                <div className="flex items-center space-x-2 mb-2">
                  <Bot className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium text-gray-700">AI Assistant</span>
                  <span className="text-sm text-gray-500">생각중...</span>
                </div>
                <div className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span className="text-gray-600">답변을 준비중입니다...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* 입력 영역 */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex items-end space-x-3">
            <div className="flex-1">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="질문을 입력하세요... (Enter로 전송, Shift+Enter로 줄바꿈)"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                rows={1}
                style={{ minHeight: '44px', maxHeight: '120px' }}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 설정 패널 */}
      {showSettings && (
        <div className="w-80 bg-white border-l border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">채팅 설정</h3>
          
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                정확도 임계값
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="range"
                  min="0.5"
                  max="1"
                  step="0.05"
                  value={accuracyThreshold}
                  onChange={(e) => setAccuracyThreshold(parseFloat(e.target.value))}
                  className="flex-1"
                />
                <span className="text-sm text-gray-600 min-w-[3rem]">
                  {Math.round(accuracyThreshold * 100)}%
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                이 값보다 낮은 정확도의 답변에 경고 표시
              </p>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={showSources}
                  onChange={(e) => setShowSources(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">소스 문서 표시</span>
              </label>
            </div>

            <div className="pt-4 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-900 mb-2">통계</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>총 메시지:</span>
                  <span>{messages.length}</span>
                </div>
                <div className="flex justify-between">
                  <span>평균 정확도:</span>
                  <span>
                    {messages.filter(m => m.accuracy).length > 0
                      ? Math.round(
                          messages
                            .filter(m => m.accuracy)
                            .reduce((sum, m) => sum + (m.accuracy || 0), 0) /
                            messages.filter(m => m.accuracy).length * 100
                        ) + '%'
                      : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}