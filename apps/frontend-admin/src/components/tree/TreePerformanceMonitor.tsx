'use client'

import React, { useState, useEffect } from 'react'
import { useMemoryMonitor, usePerformanceMetrics } from '@/hooks/useTreeOptimization'

interface TreePerformanceMonitorProps {
  nodeCount: number
  visibleNodeCount: number
  isVisible?: boolean
}

export function TreePerformanceMonitor({
  nodeCount,
  visibleNodeCount,
  isVisible = false
}: TreePerformanceMonitorProps) {
  const memory = useMemoryMonitor()
  const { metrics } = usePerformanceMetrics()
  const [fps, setFps] = useState(60)

  // FPS 모니터링
  useEffect(() => {
    let frameCount = 0
    let lastTime = performance.now()

    const measureFPS = () => {
      const currentTime = performance.now()
      frameCount++

      if (currentTime - lastTime >= 1000) {
        setFps(frameCount)
        frameCount = 0
        lastTime = currentTime
      }

      requestAnimationFrame(measureFPS)
    }

    const animationId = requestAnimationFrame(measureFPS)
    return () => cancelAnimationFrame(animationId)
  }, [])

  // 성능 상태 계산
  const getPerformanceStatus = () => {
    const avgRenderTime = metrics.averageRenderTime
    const memoryUsage = memory.current / (1024 * 1024) // MB로 변환

    if (avgRenderTime < 16 && fps >= 55 && memoryUsage < 100) {
      return { status: 'excellent', color: 'text-green-600', bg: 'bg-green-50' }
    } else if (avgRenderTime < 50 && fps >= 45 && memoryUsage < 200) {
      return { status: 'good', color: 'text-blue-600', bg: 'bg-blue-50' }
    } else if (avgRenderTime < 100 && fps >= 30 && memoryUsage < 500) {
      return { status: 'fair', color: 'text-yellow-600', bg: 'bg-yellow-50' }
    } else {
      return { status: 'poor', color: 'text-red-600', bg: 'bg-red-50' }
    }
  }

  const performanceStatus = getPerformanceStatus()

  if (!isVisible) return null

  return (
    <div className={`p-4 rounded-lg border ${performanceStatus.bg} ${performanceStatus.color}`}>
      <h3 className="text-sm font-semibold mb-3">성능 모니터링</h3>

      <div className="grid grid-cols-2 gap-4 text-xs">
        {/* 렌더링 성능 */}
        <div>
          <h4 className="font-medium mb-2">렌더링</h4>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span>FPS:</span>
              <span className={fps >= 55 ? 'text-green-600' : fps >= 30 ? 'text-yellow-600' : 'text-red-600'}>
                {fps}
              </span>
            </div>
            <div className="flex justify-between">
              <span>평균 렌더 시간:</span>
              <span className={metrics.averageRenderTime < 16 ? 'text-green-600' : 'text-yellow-600'}>
                {metrics.averageRenderTime.toFixed(1)}ms
              </span>
            </div>
            <div className="flex justify-between">
              <span>렌더 카운트:</span>
              <span>{metrics.renderCount}</span>
            </div>
          </div>
        </div>

        {/* 메모리 사용량 */}
        <div>
          <h4 className="font-medium mb-2">메모리</h4>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span>현재:</span>
              <span className={(memory.current / 1024 / 1024) < 100 ? 'text-green-600' : 'text-yellow-600'}>
                {(memory.current / 1024 / 1024).toFixed(1)}MB
              </span>
            </div>
            <div className="flex justify-between">
              <span>최대:</span>
              <span>{(memory.peak / 1024 / 1024).toFixed(1)}MB</span>
            </div>
            <div className="flex justify-between">
              <span>노드 당:</span>
              <span>{nodeCount > 0 ? ((memory.current / nodeCount) / 1024).toFixed(1) + 'KB' : '0KB'}</span>
            </div>
          </div>
        </div>

        {/* 데이터 통계 */}
        <div>
          <h4 className="font-medium mb-2">데이터</h4>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span>총 노드:</span>
              <span>{nodeCount.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span>표시 중:</span>
              <span>{visibleNodeCount.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span>가상화 비율:</span>
              <span>{nodeCount > 0 ? ((1 - visibleNodeCount / nodeCount) * 100).toFixed(1) + '%' : '0%'}</span>
            </div>
          </div>
        </div>

        {/* 성능 상태 */}
        <div>
          <h4 className="font-medium mb-2">상태</h4>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span>전체 성능:</span>
              <span className={`font-semibold ${performanceStatus.color}`}>
                {performanceStatus.status.toUpperCase()}
              </span>
            </div>
            <div className="text-xs text-gray-600 mt-2">
              {performanceStatus.status === 'excellent' && '🚀 최적 성능'}
              {performanceStatus.status === 'good' && '✅ 양호한 성능'}
              {performanceStatus.status === 'fair' && '⚠️ 보통 성능'}
              {performanceStatus.status === 'poor' && '🐌 성능 개선 필요'}
            </div>
          </div>
        </div>
      </div>

      {/* 성능 팁 */}
      {performanceStatus.status !== 'excellent' && (
        <div className="mt-4 p-2 bg-white bg-opacity-50 rounded text-xs">
          <p className="font-medium">성능 개선 팁:</p>
          <ul className="mt-1 space-y-1 text-gray-700">
            {metrics.averageRenderTime > 50 && (
              <li>• 많은 노드를 한 번에 확장하지 마세요</li>
            )}
            {fps < 30 && (
              <li>• 스크롤 속도를 줄여보세요</li>
            )}
            {(memory.current / 1024 / 1024) > 500 && (
              <li>• 브라우저를 새로고침하여 메모리를 정리하세요</li>
            )}
          </ul>
        </div>
      )}
    </div>
  )
}