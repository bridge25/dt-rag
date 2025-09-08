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
  ArrowDown,
  Bot,
  Play,
  Pause,
  Square,
  Monitor,
  Zap,
  Shield,
  Globe
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
  version: string
  timestamp: string
  description: string
  status: 'success' | 'failed' | 'pending'
}

interface AgentInfo {
  id: string
  name: string
  status: 'active' | 'inactive' | 'error'
  type: string
  createdAt: string
  lastActivity: string
  tasksCompleted: number
  performance: number
  description: string
  version: string
}

interface SystemStatusInfo {
  component: string
  status: 'healthy' | 'warning' | 'critical'
  lastChecked: string
  details: string
  metrics?: {
    cpu?: number
    memory?: number
    responseTime?: number
    errorRate?: number
  }
}

const MOCK_METRICS: MetricCard[] = [
  {
    title: '총 질의',
    value: '24,832',
    change: 12.5,
    changeType: 'increase',
    icon: BarChart3,
    color: 'blue'
  },
  {
    title: '정확도',
    value: '94.2%',
    change: 2.1,
    changeType: 'increase',
    icon: TrendingUp,
    color: 'green'
  },
  {
    title: '응답 시간',
    value: '1.2s',
    change: -8.3,
    changeType: 'decrease',
    icon: Activity,
    color: 'yellow'
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

const MOCK_AGENTS: AgentInfo[] = [
  {
    id: 'agent-001',
    name: 'Classification Agent Alpha',
    status: 'active',
    type: 'Classification',
    createdAt: '2024-01-15T10:00:00Z',
    lastActivity: '2024-01-20T14:30:00Z',
    tasksCompleted: 1247,
    performance: 94.2,
    description: '문서 분류 및 태그 생성을 담당하는 에이전트',
    version: '1.2.3'
  },
  {
    id: 'agent-002',
    name: 'Extraction Agent Beta',
    status: 'active',
    type: 'Extraction',
    createdAt: '2024-01-10T09:15:00Z',
    lastActivity: '2024-01-20T14:25:00Z',
    tasksCompleted: 832,
    performance: 91.8,
    description: '핵심 정보 추출 및 요약 생성 에이전트',
    version: '1.1.0'
  },
  {
    id: 'agent-003',
    name: 'RAG Agent Gamma',
    status: 'inactive',
    type: 'RAG',
    createdAt: '2024-01-20T11:00:00Z',
    lastActivity: '2024-01-20T12:00:00Z',
    tasksCompleted: 156,
    performance: 87.5,
    description: '검색 증강 생성 및 답변 생성 에이전트',
    version: '1.0.5'
  },
  {
    id: 'agent-004',
    name: 'Monitoring Agent Delta',
    status: 'error',
    type: 'Monitoring',
    createdAt: '2024-01-18T08:30:00Z',
    lastActivity: '2024-01-20T10:15:00Z',
    tasksCompleted: 45,
    performance: 65.3,
    description: '시스템 모니터링 및 알림 관리 에이전트',
    version: '0.9.8'
  }
]

const MOCK_SYSTEM_STATUS: SystemStatusInfo[] = [
  {
    component: 'API Gateway',
    status: 'healthy',
    lastChecked: '2024-01-20T14:30:00Z',
    details: 'All endpoints responding normally',
    metrics: {
      cpu: 12,
      memory: 45,
      responseTime: 125,
      errorRate: 0.1
    }
  },
  {
    component: 'Vector Database',
    status: 'warning',
    lastChecked: '2024-01-20T14:28:00Z',
    details: 'High memory usage detected',
    metrics: {
      cpu: 34,
      memory: 87,
      responseTime: 340,
      errorRate: 0.5
    }
  },
  {
    component: 'ML Model Service',
    status: 'healthy',
    lastChecked: '2024-01-20T14:29:00Z',
    details: 'Models performing within expected parameters',
    metrics: {
      cpu: 67,
      memory: 72,
      responseTime: 450,
      errorRate: 0.2
    }
  },
  {
    component: 'Cache Layer',
    status: 'critical',
    lastChecked: '2024-01-20T14:25:00Z',
    details: 'Multiple cache misses and connection timeouts',
    metrics: {
      cpu: 89,
      memory: 95,
      responseTime: 1200,
      errorRate: 5.2
    }
  }
]

const MOCK_ROLLBACKS: RollbackEntry[] = [
  {
    id: 'rb-001',
    version: 'v1.2.3',
    timestamp: '2024-01-20T10:30:00Z',
    description: '분류 모델 정확도 개선',
    status: 'success'
  },
  {
    id: 'rb-002',
    version: 'v1.2.2',
    timestamp: '2024-01-19T15:45:00Z',
    description: 'API 응답 시간 최적화',
    status: 'success'
  },
  {
    id: 'rb-003',
    version: 'v1.2.1',
    timestamp: '2024-01-18T09:20:00Z',
    description: '벡터 인덱스 구조 개선',
    status: 'failed'
  }
]

const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleString('ko-KR')
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'healthy': return 'bg-green-100 text-green-800'
    case 'warning': return 'bg-yellow-100 text-yellow-800'
    case 'critical': return 'bg-red-100 text-red-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

const getPerformanceColor = (performance: number) => {
  if (performance >= 90) return 'text-green-600'
  if (performance >= 70) return 'text-yellow-600'
  return 'text-red-600'
}

export function AdminDashboard() {
  const [metrics, setMetrics] = useState<MetricCard[]>(MOCK_METRICS)
  const [systemHealth, setSystemHealth] = useState<SystemHealth>(MOCK_SYSTEM_HEALTH)
  const [rollbacks, setRollbacks] = useState<RollbackEntry[]>(MOCK_ROLLBACKS)
  const [agents, setAgents] = useState<AgentInfo[]>(MOCK_AGENTS)
  const [systemStatus, setSystemStatus] = useState<SystemStatusInfo[]>(MOCK_SYSTEM_STATUS)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h')
  const [activeTab, setActiveTab] = useState<'metrics' | 'agents' | 'system'>('metrics')

  const refreshData = async () => {
    setIsRefreshing(true)
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsRefreshing(false)
  }

  const getChangeIcon = (changeType: string) => {
    switch (changeType) {
      case 'increase':
        return <ArrowUp className="w-3 h-3 text-green-600" />
      case 'decrease':
        return <ArrowDown className="w-3 h-3 text-red-600" />
      default:
        return null
    }
  }

  const getChangeColor = (changeType: string) => {
    switch (changeType) {
      case 'increase':
        return 'text-green-600'
      case 'decrease':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const handleAgentControl = async (agentId: string, action: 'start' | 'stop' | 'restart') => {
    setAgents(prev => prev.map(agent => {
      if (agent.id === agentId) {
        let newStatus: 'active' | 'inactive' | 'error' = agent.status
        if (action === 'start') newStatus = 'active'
        if (action === 'stop') newStatus = 'inactive'
        if (action === 'restart') newStatus = 'active'
        
        return {
          ...agent,
          status: newStatus,
          lastActivity: new Date().toISOString()
        }
      }
      return agent
    }))
  }

  const handleDeleteAgent = async (agentId: string) => {
    if (confirm('정말로 이 에이전트를 삭제하시겠습니까?')) {
      setAgents(prev => prev.filter(agent => agent.id !== agentId))
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
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
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>새로고침</span>
          </button>
        </div>
      </div>

      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('metrics')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'metrics'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            시스템 메트릭
          </button>
          <button
            onClick={() => setActiveTab('agents')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'agents'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            에이전트 관리
          </button>
          <button
            onClick={() => setActiveTab('system')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'system'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            시스템 상태
          </button>
        </nav>
      </div>

      {activeTab === 'metrics' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            {metrics.map((metric, index) => {
              const IconComponent = metric.icon
              return (
                <div key={index} className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className={`p-2 rounded-md bg-${metric.color}-100`}>
                        <IconComponent className={`w-6 h-6 text-${metric.color}-600`} />
                      </div>
                    </div>
                    <div className={`flex items-center space-x-1 ${getChangeColor(metric.changeType)}`}>
                      {getChangeIcon(metric.changeType)}
                      <span className="text-sm font-medium">{Math.abs(metric.change)}%</span>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="text-2xl font-bold text-gray-900">{metric.value}</div>
                    <div className="text-sm text-gray-600 mt-1">{metric.title}</div>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">시스템 상태</h2>
              <div className={`flex items-center space-x-2 ${
                systemHealth.status === 'healthy' ? 'text-green-600' :
                systemHealth.status === 'warning' ? 'text-yellow-600' : 'text-red-600'
              }`}>
                <div className={`w-3 h-3 rounded-full ${
                  systemHealth.status === 'healthy' ? 'bg-green-500' :
                  systemHealth.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                }`}></div>
                <span className="font-medium">
                  {systemHealth.status === 'healthy' ? '정상' :
                   systemHealth.status === 'warning' ? '경고' : '심각'}
                </span>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{systemHealth.uptime}</div>
                <div className="text-sm text-gray-600">가동률</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{systemHealth.responseTime}ms</div>
                <div className="text-sm text-gray-600">응답 시간</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{systemHealth.errorRate}%</div>
                <div className="text-sm text-gray-600">오류율</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{systemHealth.throughput}</div>
                <div className="text-sm text-gray-600">처리량/초</div>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">롤백 이력</h2>
              <button className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-800">
                <History className="w-4 h-4" />
                <span>전체 이력</span>
              </button>
            </div>
            
            <div className="space-y-3">
              {rollbacks.map((rollback) => (
                <div key={rollback.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      rollback.status === 'success' ? 'bg-green-500' :
                      rollback.status === 'failed' ? 'bg-red-500' : 'bg-yellow-500'
                    }`}></div>
                    <div>
                      <div className="font-medium text-gray-900">{rollback.version}</div>
                      <div className="text-sm text-gray-600">{rollback.description}</div>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatTimestamp(rollback.timestamp)}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-200">
              <button className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700">
                <Download className="w-4 h-4" />
                <span>이전 버전으로 롤백</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'agents' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 rounded-md bg-blue-100">
                  <Bot className="w-6 h-6 text-blue-600" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-2xl font-bold text-gray-900">{agents.length}</div>
                <div className="text-sm text-gray-600 mt-1">총 에이전트</div>
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 rounded-md bg-green-100">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-2xl font-bold text-gray-900">
                  {agents.filter(a => a.status === 'active').length}
                </div>
                <div className="text-sm text-gray-600 mt-1">활성 에이전트</div>
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 rounded-md bg-yellow-100">
                  <Clock className="w-6 h-6 text-yellow-600" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-2xl font-bold text-gray-900">
                  {agents.filter(a => a.status === 'inactive').length}
                </div>
                <div className="text-sm text-gray-600 mt-1">비활성 에이전트</div>
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 rounded-md bg-red-100">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-2xl font-bold text-gray-900">
                  {agents.filter(a => a.status === 'error').length}
                </div>
                <div className="text-sm text-gray-600 mt-1">오류 에이전트</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">에이전트 목록</h2>
                <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                  <Bot className="w-4 h-4" />
                  <span>새 에이전트 생성</span>
                </button>
              </div>
            </div>
            
            <div className="p-6">
              <div className="grid gap-6">
                {agents.map((agent) => (
                  <div key={agent.id} className="border border-gray-200 rounded-lg p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-4">
                        <div className={`w-4 h-4 rounded-full ${
                          agent.status === 'active' ? 'bg-green-500' :
                          agent.status === 'inactive' ? 'bg-yellow-500' : 'bg-red-500'
                        }`}></div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                          <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                            <span>타입: {agent.type}</span>
                            <span>버전: {agent.version}</span>
                            <span>생성일: {formatTimestamp(agent.createdAt)}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleAgentControl(agent.id, 'start')}
                          className="p-2 text-green-600 hover:bg-green-100 rounded-md"
                          title="시작"
                        >
                          <Play className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleAgentControl(agent.id, 'stop')}
                          className="p-2 text-red-600 hover:bg-red-100 rounded-md"
                          title="정지"
                        >
                          <Pause className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleAgentControl(agent.id, 'restart')}
                          className="p-2 text-blue-600 hover:bg-blue-100 rounded-md"
                          title="재시작"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteAgent(agent.id)}
                          className="p-2 text-red-600 hover:bg-red-100 rounded-md"
                          title="삭제"
                        >
                          <Square className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    
                    <p className="text-gray-700 mb-4">{agent.description}</p>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-lg font-semibold text-gray-900">{agent.tasksCompleted}</div>
                        <div className="text-sm text-gray-600">완료 작업</div>
                      </div>
                      <div className="text-center">
                        <div className={`text-lg font-semibold ${getPerformanceColor(agent.performance)}`}>
                          {agent.performance}%
                        </div>
                        <div className="text-sm text-gray-600">성능</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-semibold text-gray-900">
                          {formatTimestamp(agent.lastActivity)}
                        </div>
                        <div className="text-sm text-gray-600">마지막 활동</div>
                      </div>
                      <div className="text-center">
                        <span className={`px-3 py-1 text-sm rounded-full font-medium ${
                          agent.status === 'active' ? 'bg-green-100 text-green-800' :
                          agent.status === 'inactive' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {agent.status === 'active' ? '활성' :
                           agent.status === 'inactive' ? '비활성' : '오류'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'system' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 rounded-md bg-green-100">
                  <Monitor className="w-6 h-6 text-green-600" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-2xl font-bold text-gray-900">
                  {systemStatus.filter(s => s.status === 'healthy').length}
                </div>
                <div className="text-sm text-gray-600 mt-1">정상 컴포넌트</div>
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 rounded-md bg-yellow-100">
                  <AlertTriangle className="w-6 h-6 text-yellow-600" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-2xl font-bold text-gray-900">
                  {systemStatus.filter(s => s.status === 'warning').length}
                </div>
                <div className="text-sm text-gray-600 mt-1">경고 컴포넌트</div>
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 rounded-md bg-red-100">
                  <Zap className="w-6 h-6 text-red-600" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-2xl font-bold text-gray-900">
                  {systemStatus.filter(s => s.status === 'critical').length}
                </div>
                <div className="text-sm text-gray-600 mt-1">심각 컴포넌트</div>
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="p-2 rounded-md bg-blue-100">
                  <Shield className="w-6 h-6 text-blue-600" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-2xl font-bold text-gray-900">{systemStatus.length}</div>
                <div className="text-sm text-gray-600 mt-1">총 컴포넌트</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">시스템 컴포넌트 상태</h2>
            </div>
            
            <div className="p-6">
              <div className="grid gap-4">
                {systemStatus.map((component, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className={`w-3 h-3 rounded-full ${
                          component.status === 'healthy' ? 'bg-green-500' :
                          component.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                        }`}></div>
                        <h3 className="font-medium text-gray-900">{component.component}</h3>
                        <span className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(component.status)}`}>
                          {component.status === 'healthy' ? '정상' :
                           component.status === 'warning' ? '경고' : '심각'}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {formatTimestamp(component.lastChecked)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{component.details}</p>
                    {component.metrics && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <div className="text-sm font-medium text-gray-900">{component.metrics.cpu}%</div>
                          <div className="text-xs text-gray-600">CPU</div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm font-medium text-gray-900">{component.metrics.memory}%</div>
                          <div className="text-xs text-gray-600">Memory</div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm font-medium text-gray-900">{component.metrics.responseTime}ms</div>
                          <div className="text-xs text-gray-600">Response</div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm font-medium text-gray-900">{component.metrics.errorRate}%</div>
                          <div className="text-xs text-gray-600">Error Rate</div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}