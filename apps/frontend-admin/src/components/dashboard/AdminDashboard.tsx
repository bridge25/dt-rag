'use client'

import React, { useState, useEffect } from 'react'
import { 
  BarChart3, 
  TrendingUp, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Users, 
  Database,
  Cpu,
  HardDrive,
  RefreshCw,
  Download,
  Upload,
  Settings,
  History,
  ArrowUp,
  ArrowDown
} from 'lucide-react'

interface MetricCard {
  title: string
  value: string | number
  change: number
  changeType: 'increase' | 'decrease' | 'neutral'
  icon: React.ComponentType<any>
  color: string
}

interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical'
  uptime: string
  responseTime: number
  errorRate: number
  throughput: number
}

interface RollbackEntry {
  id: string
  timestamp: string
  version: string
  description: string
  initiatedBy: string
  status: 'completed' | 'in-progress' | 'failed'
  affectedServices: string[]
}

// Mock 데이터
const MOCK_METRICS: MetricCard[] = [
  {
    title: '총 분류 요청',
    value: '2,847,293',
    change: 12.5,
    changeType: 'increase',
    icon: BarChart3,
    color: 'blue'
  },
  {
    title: '평균 응답시간',
    value: '245ms',
    change: -8.2,
    changeType: 'decrease',
    icon: Clock,
    color: 'green'
  },
  {
    title: '시스템 가동률',
    value: '99.97%',
    change: 0.12,
    changeType: 'increase',
    icon: Activity,
    color: 'emerald'
  },
  {
    title: '오류율',
    value: '0.03%',
    change: -15.4,
    changeType: 'decrease',
    icon: AlertTriangle,
    color: 'red'
  },
  {
    title: '활성 사용자',
    value: '1,247',
    change: 8.7,
    changeType: 'increase',
    icon: Users,
    color: 'purple'
  },
  {
    title: '처리된 문서',
    value: '45,892',
    change: 23.1,
    changeType: 'increase',
    icon: Database,
    color: 'orange'
  }
]

const MOCK_SYSTEM_HEALTH: SystemHealth = {
  status: 'healthy',
  uptime: '99.97%',
  responseTime: 245,
  errorRate: 0.03,
  throughput: 1847
}

const MOCK_ROLLBACKS: RollbackEntry[] = [
  {
    id: 'rb-001',
    timestamp: '2025-01-15T14:30:00Z',
    version: 'v1.8.0',
    description: 'Emergency rollback due to classification accuracy drop',
    initiatedBy: 'admin@example.com',
    status: 'completed',
    affectedServices: ['taxonomy-service', 'classification-api']
  },
  {
    id: 'rb-002', 
    timestamp: '2025-01-14T09:15:00Z',
    version: 'v1.7.5',
    description: 'Scheduled rollback after failed deployment',
    initiatedBy: 'devops@example.com',
    status: 'completed',
    affectedServices: ['rag-engine', 'document-processor']
  },
  {
    id: 'rb-003',
    timestamp: '2025-01-13T16:45:00Z',
    version: 'v1.7.2',
    description: 'Performance regression rollback',
    initiatedBy: 'system',
    status: 'completed',
    affectedServices: ['search-api']
  }
]

const getMetricColor = (color: string) => {
  const colors = {
    blue: 'text-blue-600 bg-blue-100',
    green: 'text-green-600 bg-green-100',
    emerald: 'text-emerald-600 bg-emerald-100',
    red: 'text-red-600 bg-red-100',
    purple: 'text-purple-600 bg-purple-100',
    orange: 'text-orange-600 bg-orange-100'
  }
  return colors[color as keyof typeof colors] || colors.blue
}

const getChangeColor = (changeType: string) => {
  switch (changeType) {
    case 'increase': return 'text-green-600'
    case 'decrease': return 'text-red-600'
    default: return 'text-gray-600'
  }
}

const getChangeIcon = (changeType: string) => {
  switch (changeType) {
    case 'increase': return ArrowUp
    case 'decrease': return ArrowDown
    default: return null
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'healthy': return 'text-green-600 bg-green-100'
    case 'warning': return 'text-yellow-600 bg-yellow-100'
    case 'critical': return 'text-red-600 bg-red-100'
    default: return 'text-gray-600 bg-gray-100'
  }
}

const getRollbackStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'text-green-700 bg-green-100'
    case 'in-progress': return 'text-yellow-700 bg-yellow-100'
    case 'failed': return 'text-red-700 bg-red-100'
    default: return 'text-gray-700 bg-gray-100'
  }
}

export function AdminDashboard() {
  const [metrics, setMetrics] = useState<MetricCard[]>(MOCK_METRICS)
  const [systemHealth, setSystemHealth] = useState<SystemHealth>(MOCK_SYSTEM_HEALTH)
  const [rollbacks, setRollbacks] = useState<RollbackEntry[]>(MOCK_ROLLBACKS)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h')

  const refreshData = async () => {
    setIsRefreshing(true)
    // Mock refresh delay
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsRefreshing(false)
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleRollback = async (version: string) => {
    if (confirm(`Are you sure you want to rollback to ${version}?`)) {
      // Mock rollback process
      const newRollback: RollbackEntry = {
        id: `rb-${Date.now()}`,
        timestamp: new Date().toISOString(),
        version: version,
        description: `Manual rollback to ${version}`,
        initiatedBy: 'current-user@example.com',
        status: 'in-progress',
        affectedServices: ['all-services']
      }
      
      setRollbacks(prev => [newRollback, ...prev])
      
      // Simulate completion after 3 seconds
      setTimeout(() => {
        setRollbacks(prev => 
          prev.map(rb => 
            rb.id === newRollback.id 
              ? { ...rb, status: 'completed' as const }
              : rb
          )
        )
      }, 3000)
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* 대시보드 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600">시스템 메트릭 및 관리 도구</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1h">지난 1시간</option>
            <option value="24h">지난 24시간</option>
            <option value="7d">지난 7일</option>
            <option value="30d">지난 30일</option>
          </select>
          
          <button
            onClick={refreshData}
            disabled={isRefreshing}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>새로고침</span>
          </button>
        </div>
      </div>

      {/* 시스템 상태 카드 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">시스템 상태</h2>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(systemHealth.status)}`}>
            {systemHealth.status === 'healthy' ? '정상' : 
             systemHealth.status === 'warning' ? '경고' : '심각'}
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{systemHealth.uptime}</div>
            <div className="text-sm text-gray-600">가동률</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{systemHealth.responseTime}ms</div>
            <div className="text-sm text-gray-600">응답시간</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{systemHealth.errorRate}%</div>
            <div className="text-sm text-gray-600">오류율</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{systemHealth.throughput.toLocaleString()}</div>
            <div className="text-sm text-gray-600">처리량/분</div>
          </div>
        </div>
      </div>

      {/* 메트릭 카드 그리드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {metrics.map((metric, index) => {
          const IconComponent = metric.icon
          const ChangeIcon = getChangeIcon(metric.changeType)
          
          return (
            <div key={index} className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">{metric.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
                  <div className={`flex items-center mt-2 ${getChangeColor(metric.changeType)}`}>
                    {ChangeIcon && <ChangeIcon className="w-4 h-4 mr-1" />}
                    <span className="text-sm font-medium">
                      {Math.abs(metric.change)}%
                    </span>
                    <span className="text-sm text-gray-500 ml-1">vs 이전 기간</span>
                  </div>
                </div>
                <div className={`p-3 rounded-lg ${getMetricColor(metric.color)}`}>
                  <IconComponent className="w-6 h-6" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* 롤백 관리 섹션 */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">롤백 관리</h2>
              <p className="text-sm text-gray-600">시스템 버전 관리 및 롤백 기록</p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => handleRollback('v1.7.5')}
                className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors flex items-center space-x-2"
              >
                <History className="w-4 h-4" />
                <span>이전 버전으로 롤백</span>
              </button>
              <button className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors flex items-center space-x-2">
                <Download className="w-4 h-4" />
                <span>로그 내보내기</span>
              </button>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="space-y-4">
            {rollbacks.map((rollback) => (
              <div key={rollback.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="font-medium text-gray-900">
                        롤백 to {rollback.version}
                      </h3>
                      <span className={`px-2 py-1 text-xs rounded-full font-medium ${getRollbackStatusColor(rollback.status)}`}>
                        {rollback.status === 'completed' ? '완료' : 
                         rollback.status === 'in-progress' ? '진행중' : '실패'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{rollback.description}</p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <div className="flex items-center space-x-4">
                        <span>실행자: {rollback.initiatedBy}</span>
                        <span>시간: {formatTimestamp(rollback.timestamp)}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span>영향받은 서비스:</span>
                        <div className="flex space-x-1">
                          {rollback.affectedServices.map((service, idx) => (
                            <span key={idx} className="px-2 py-1 bg-gray-100 rounded text-xs">
                              {service}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 퀵 액션 패널 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <button className="p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 text-blue-600 rounded-lg">
              <Settings className="w-5 h-5" />
            </div>
            <div className="text-left">
              <div className="font-medium text-gray-900">시스템 설정</div>
              <div className="text-sm text-gray-600">구성 및 파라미터 관리</div>
            </div>
          </div>
        </button>
        
        <button className="p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 text-green-600 rounded-lg">
              <Download className="w-5 h-5" />
            </div>
            <div className="text-left">
              <div className="font-medium text-gray-900">백업 생성</div>
              <div className="text-sm text-gray-600">시스템 데이터 백업</div>
            </div>
          </div>
        </button>
        
        <button className="p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 text-purple-600 rounded-lg">
              <Cpu className="w-5 h-5" />
            </div>
            <div className="text-left">
              <div className="font-medium text-gray-900">성능 모니터링</div>
              <div className="text-sm text-gray-600">실시간 성능 지표</div>
            </div>
          </div>
        </button>
        
        <button className="p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-100 text-orange-600 rounded-lg">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div className="text-left">
              <div className="font-medium text-gray-900">알림 관리</div>
              <div className="text-sm text-gray-600">시스템 알림 설정</div>
            </div>
          </div>
        </button>
      </div>
    </div>
  )
}