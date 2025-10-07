'use client'

import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { API_CONFIG, getApiHeaders } from '@/constants/api'
import {
  ApiStatus,
  AnswerResult,
  ApiStatusSchema,
  AnswerResultSchema,
  ClassifyResponse,
  ClassifyResponseSchema,
  SearchResponse,
  SearchResponseSchema
} from '@/types/schemas'
import { useToast } from '@/contexts/ToastContext'
import { getErrorMessage, isAbortError } from '@/lib/errorHandler'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { useDebounce } from '@/hooks/useDebounce'

interface SearchResult {
  id: string
  title: string
  content: string
  score: number
  source: string
}

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('artificial intelligence')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [answerResult, setAnswerResult] = useState<AnswerResult | null>(null)
  const [generateAnswer, setGenerateAnswer] = useState(false)
  const [answerMode, setAnswerMode] = useState('answer')
  const [classifyText, setClassifyText] = useState('This is a technical documentation about machine learning algorithms.')
  const [classifyResults, setClassifyResults] = useState<ClassifyResponse | null>(null)
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const { showToast } = useToast()
  const searchAbortControllerRef = useRef<AbortController>()
  const classifyAbortControllerRef = useRef<AbortController>()

  const debouncedSearchQuery = useDebounce(searchQuery, 300)
  const debouncedClassifyText = useDebounce(classifyText, 500)

  const checkApiStatus = useCallback(async (signal?: AbortSignal) => {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL.replace('/api/v1', '')}/health`, { signal })
      if (signal?.aborted) return
      const data = await response.json()
      setApiStatus(data)
      showToast('API 연결 성공', 'success')
    } catch (error: any) {
      if (isAbortError(error)) return
      const message = getErrorMessage(error)
      showToast(`API 연결 실패: ${message}`, 'error')
      console.error('API 연결 실패:', error)
    }
  }, [showToast])

  const handleSearch = useCallback(async () => {
    if (!debouncedSearchQuery.trim()) return

    if (searchAbortControllerRef.current) {
      searchAbortControllerRef.current.abort()
    }
    const controller = new AbortController()
    searchAbortControllerRef.current = controller

    setLoading(true)
    setAnswerResult(null)

    try {
      if (generateAnswer) {
        const response = await fetch(`${API_CONFIG.BASE_URL.replace('/api/v1', '')}/answer`, {
          method: 'POST',
          headers: getApiHeaders(),
          body: JSON.stringify({
            q: debouncedSearchQuery,
            mode: answerMode,
            final_topk: 5
          }),
          signal: controller.signal
        })

        const data = await response.json()
        setAnswerResult(data)

        const formattedResults = (data.sources || []).map((source: any, index: number) => ({
          id: source.chunk_id || `source-${index}`,
          title: source.source?.title || 'Untitled',
          content: source.text || '',
          score: source.score || 0,
          source: source.source?.url || 'N/A'
        }))
        setSearchResults(formattedResults)
      } else {
        const response = await fetch(`${API_CONFIG.BASE_URL.replace('/api/v1', '')}/search`, {
          method: 'POST',
          headers: getApiHeaders(),
          body: JSON.stringify({
            q: debouncedSearchQuery,
            final_topk: 5
          }),
          signal: controller.signal
        })

        const data = await response.json()
        const formattedResults = (data.hits || []).map((hit: any) => ({
          id: hit.chunk_id,
          title: hit.source?.title || 'Untitled',
          content: hit.text || '',
          score: hit.score,
          source: hit.source?.url || 'N/A'
        }))
        setSearchResults(formattedResults)
      }
    } catch (error) {
      if (isAbortError(error)) return
      const message = getErrorMessage(error)
      showToast(`검색 실패: ${message}`, 'error')
      console.error('검색 실패:', error)
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false)
      }
    }
  }, [debouncedSearchQuery, generateAnswer, answerMode, showToast])

  const handleClassify = useCallback(async () => {
    if (!debouncedClassifyText.trim()) return

    if (classifyAbortControllerRef.current) {
      classifyAbortControllerRef.current.abort()
    }
    const controller = new AbortController()
    classifyAbortControllerRef.current = controller

    setLoading(true)
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/classify`, {
        method: 'POST',
        headers: getApiHeaders(),
        body: JSON.stringify({
          text: debouncedClassifyText,
          confidence_threshold: 0.7
        }),
        signal: controller.signal
      })

      const rawData = await response.json()
      const validatedData = ClassifyResponseSchema.parse(rawData)
      setClassifyResults(validatedData)
      showToast('분류 완료', 'success')
    } catch (error) {
      if (isAbortError(error)) return
      const message = getErrorMessage(error)
      showToast(`분류 실패: ${message}`, 'error')
      console.error('분류 실패:', error)
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false)
      }
    }
  }, [debouncedClassifyText, showToast])

  useEffect(() => {
    const controller = new AbortController()
    checkApiStatus(controller.signal)

    return () => {
      controller.abort()
    }
  }, [checkApiStatus])

  return (
    <div className="space-y-6">
      {/* API 상태 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">🔗 백엔드 API 연결 상태</h2>
        {apiStatus ? (
          <div className="text-green-600">
            ✅ 연결됨 - 상태: {apiStatus.status}, 버전: {apiStatus.version}
            <br />
            백엔드 주소: http://localhost:8001
          </div>
        ) : (
          <div className="text-red-600">
            ❌ API 서버에 연결할 수 없습니다
          </div>
        )}
        <button
          onClick={() => checkApiStatus()}
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          상태 새로고침
        </button>
      </div>

      {/* 네비게이션 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">📱 기능 메뉴</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 border rounded text-center">
            <h3 className="font-bold">🏠 Dashboard</h3>
            <p className="text-sm text-gray-600">메인 대시보드</p>
          </div>
          <div className="p-4 border rounded text-center">
            <h3 className="font-bold">👤 Admin</h3>
            <p className="text-sm text-gray-600">관리자 페이지</p>
          </div>
          <div className="p-4 border rounded text-center">
            <h3 className="font-bold">🤖 Agents</h3>
            <p className="text-sm text-gray-600">AI 에이전트</p>
          </div>
          <div className="p-4 border rounded text-center">
            <h3 className="font-bold">💬 Chat</h3>
            <p className="text-sm text-gray-600">채팅 인터페이스</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 검색 섹션 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">🔍 하이브리드 검색</h2>
          <p className="text-gray-600 mb-4">BM25 + Vector Search 통합</p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                검색어
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="검색하고 싶은 내용을 입력하세요"
              />
            </div>

            {/* AI 답변 생성 옵션 */}
            <div className="border rounded-lg p-4 bg-gradient-to-r from-purple-50 to-blue-50">
              <div className="flex items-center justify-between mb-3">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={generateAnswer}
                    onChange={(e) => setGenerateAnswer(e.target.checked)}
                    className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                  />
                  <span className="text-sm font-semibold text-purple-900">
                    🤖 AI 답변 생성 (Gemini 2.5 Flash)
                  </span>
                </label>
              </div>

              {generateAnswer && (
                <div className="mt-2">
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    생성 모드
                  </label>
                  <select
                    value={answerMode}
                    onChange={(e) => setAnswerMode(e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="answer">📝 완전한 답변 (Answer)</option>
                    <option value="summary">📋 요약 (Summary)</option>
                    <option value="keypoints">🔑 핵심 요점 (Key Points)</option>
                  </select>
                </div>
              )}
            </div>

            <button
              onClick={handleSearch}
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              {loading && <LoadingSpinner size="sm" />}
              <span>{loading ? '검색 중...' : generateAnswer ? '🤖 AI 답변 생성' : '🔍 검색 실행'}</span>
            </button>

            {/* AI 답변 결과 */}
            {answerResult && (
              <div className="mt-4 border-2 border-purple-300 rounded-lg p-4 bg-gradient-to-r from-purple-50 to-blue-50">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-bold text-purple-900">🤖 AI 답변</h3>
                  <div className="flex items-center space-x-2 text-xs text-gray-600">
                    <span>⚡ {answerResult.total_time.toFixed(2)}s</span>
                    <span>|</span>
                    <span>🌐 {answerResult.language === 'ko' ? '한국어' : '영어'}</span>
                    <span>|</span>
                    <span>📚 {answerResult.source_count}개 문서</span>
                  </div>
                </div>
                <div className="bg-white rounded p-4 shadow-sm">
                  <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">
                    {answerResult.answer}
                  </p>
                </div>
                <div className="mt-2 text-xs text-gray-500">
                  모델: {answerResult.model} | 모드: {answerResult.mode} | 검색: {answerResult.search_time.toFixed(2)}s, 생성: {answerResult.generation_time.toFixed(2)}s
                </div>
              </div>
            )}

            {/* 검색 결과 */}
            {searchResults.length > 0 && (
              <div className="mt-4 max-h-64 overflow-y-auto">
                <h3 className="font-bold text-green-600 mb-2">
                  {generateAnswer ? '📚 참조 문서' : '검색 결과'} ({searchResults.length}개)
                </h3>
                {searchResults.map((result, index) => (
                  <div key={result.id} className="border-t pt-2 mt-2">
                    <h4 className="font-semibold">{result.title}</h4>
                    <p className="text-sm text-gray-600 truncate">{result.content}</p>
                    <small className="text-xs text-gray-400">
                      점수: {result.score.toFixed(2)} | 출처: {result.source}
                    </small>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 분류 섹션 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">📊 문서 분류</h2>
          <p className="text-gray-600 mb-4">ML 기반 자동 문서 분류</p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                분류할 텍스트
              </label>
              <textarea
                value={classifyText}
                onChange={(e) => setClassifyText(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="분류하고 싶은 문서 내용을 입력하세요"
              />
            </div>

            <button
              onClick={handleClassify}
              disabled={loading}
              className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              {loading && <LoadingSpinner size="sm" />}
              <span>{loading ? '분류 중...' : '📊 분류 실행'}</span>
            </button>

            {/* 분류 결과 */}
            {classifyResults && (
              <div className="mt-4 max-h-64 overflow-y-auto">
                <h3 className="font-bold text-green-600 mb-2">
                  분류 결과 ({classifyResults.classifications.length}개)
                </h3>
                {classifyResults.classifications.map((cls, index) => (
                  <div key={index} className="border-t pt-2 mt-2">
                    <h4 className="font-semibold">{cls.taxonomy_path.join(' > ')}</h4>
                    <p className="text-sm">신뢰도: {(cls.confidence * 100).toFixed(1)}%</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 추가 기능들 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <h3 className="text-lg font-bold mb-2">🗂️ 분류체계</h3>
          <p className="text-sm text-gray-600 mb-4">계층적 분류 구조 확인</p>
          <button
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
            onClick={() => window.open('http://localhost:8001/api/v1/taxonomy', '_blank')}
          >
            분류체계 보기
          </button>
        </div>

        <div className="bg-white rounded-lg shadow p-6 text-center">
          <h3 className="text-lg font-bold mb-2">📈 모니터링</h3>
          <p className="text-sm text-gray-600 mb-4">실시간 시스템 상태</p>
          <button
            className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
            onClick={() => window.open('http://localhost:8001/api/v1/monitoring/health', '_blank')}
          >
            상태 확인
          </button>
        </div>

        <div className="bg-white rounded-lg shadow p-6 text-center">
          <h3 className="text-lg font-bold mb-2">📖 API 문서</h3>
          <p className="text-sm text-gray-600 mb-4">Interactive Swagger UI</p>
          <button
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
            onClick={() => window.open('http://localhost:8001/docs', '_blank')}
          >
            문서 열기
          </button>
        </div>
      </div>
    </div>
  )
}