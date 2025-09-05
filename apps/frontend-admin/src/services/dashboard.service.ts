import { apiClient } from './api-client'
import { API_ENDPOINTS } from '@/constants/api'

export interface MetricData {
  timestamp: string
  value: number
}

export interface SystemMetrics {
  totalRequests: number
  averageResponseTime: number
  uptime: number
  errorRate: number
  activeUsers: number
  processedDocuments: number
  requestsChange: number
  responseTimeChange: number
  uptimeChange: number
  errorRateChange: number
  usersChange: number
  documentsChange: number
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical'
  uptime: string
  responseTime: number
  errorRate: number
  throughput: number
  lastUpdated: string
}

export interface RollbackEntry {
  id: string
  timestamp: string
  version: string
  description: string
  initiatedBy: string
  status: 'completed' | 'in-progress' | 'failed'
  affectedServices: string[]
  rollbackDuration?: number
}

export interface RollbackRequest {
  targetVersion: string
  reason: string
  affectedServices?: string[]
  skipValidation?: boolean
}

export interface AlertRule {
  id: string
  name: string
  condition: string
  threshold: number
  enabled: boolean
  severity: 'low' | 'medium' | 'high' | 'critical'
}

class DashboardService {
  async getSystemMetrics(timeRange: string = '24h'): Promise<SystemMetrics> {
    try {
      const response = await apiClient.get<SystemMetrics>(
        `${API_ENDPOINTS.DASHBOARD.METRICS}?range=${timeRange}`
      )
      return response.data
    } catch (error) {
      console.error('Failed to fetch system metrics:', error)
      throw error
    }
  }

  async getSystemHealth(): Promise<SystemHealth> {
    try {
      const response = await apiClient.get<SystemHealth>(
        API_ENDPOINTS.DASHBOARD.HEALTH
      )
      return response.data
    } catch (error) {
      console.error('Failed to fetch system health:', error)
      throw error
    }
  }

  async getMetricHistory(
    metric: string, 
    timeRange: string = '24h'
  ): Promise<MetricData[]> {
    try {
      const response = await apiClient.get<MetricData[]>(
        `${API_ENDPOINTS.DASHBOARD.METRIC_HISTORY}/${metric}?range=${timeRange}`
      )
      return response.data
    } catch (error) {
      console.error(`Failed to fetch ${metric} history:`, error)
      throw error
    }
  }

  async getRollbackHistory(): Promise<RollbackEntry[]> {
    try {
      const response = await apiClient.get<RollbackEntry[]>(
        API_ENDPOINTS.DASHBOARD.ROLLBACKS
      )
      return response.data
    } catch (error) {
      console.error('Failed to fetch rollback history:', error)
      throw error
    }
  }

  async initiateRollback(request: RollbackRequest): Promise<RollbackEntry> {
    try {
      const response = await apiClient.post<RollbackEntry>(
        API_ENDPOINTS.DASHBOARD.ROLLBACK_INITIATE,
        request
      )
      return response.data
    } catch (error) {
      console.error('Failed to initiate rollback:', error)
      throw error
    }
  }

  async getRollbackStatus(rollbackId: string): Promise<RollbackEntry> {
    try {
      const response = await apiClient.get<RollbackEntry>(
        `${API_ENDPOINTS.DASHBOARD.ROLLBACK_STATUS}/${rollbackId}`
      )
      return response.data
    } catch (error) {
      console.error('Failed to get rollback status:', error)
      throw error
    }
  }

  async getAvailableVersions(): Promise<string[]> {
    try {
      const response = await apiClient.get<string[]>(
        API_ENDPOINTS.DASHBOARD.VERSIONS
      )
      return response.data
    } catch (error) {
      console.error('Failed to fetch available versions:', error)
      throw error
    }
  }

  async exportLogs(
    startDate: string, 
    endDate: string, 
    logLevel?: string
  ): Promise<Blob> {
    try {
      const params = {
        start: startDate,
        end: endDate,
        ...(logLevel && { level: logLevel })
      }
      
      const response = await fetch(
        `${API_ENDPOINTS.BASE_URL}${API_ENDPOINTS.DASHBOARD.EXPORT_LOGS}?${new URLSearchParams(params)}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
          }
        }
      )
      
      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`)
      }
      
      return await response.blob()
    } catch (error) {
      console.error('Failed to export logs:', error)
      throw error
    }
  }

  async createBackup(): Promise<{ id: string, status: string }> {
    try {
      const response = await apiClient.post<{ id: string, status: string }>(
        API_ENDPOINTS.DASHBOARD.BACKUP_CREATE
      )
      return response.data
    } catch (error) {
      console.error('Failed to create backup:', error)
      throw error
    }
  }

  async getAlertRules(): Promise<AlertRule[]> {
    try {
      const response = await apiClient.get<AlertRule[]>(
        API_ENDPOINTS.DASHBOARD.ALERT_RULES
      )
      return response.data
    } catch (error) {
      console.error('Failed to fetch alert rules:', error)
      throw error
    }
  }

  async updateAlertRule(ruleId: string, rule: Partial<AlertRule>): Promise<AlertRule> {
    try {
      const response = await apiClient.put<AlertRule>(
        `${API_ENDPOINTS.DASHBOARD.ALERT_RULES}/${ruleId}`,
        rule
      )
      return response.data
    } catch (error) {
      console.error('Failed to update alert rule:', error)
      throw error
    }
  }

  async getSystemConfiguration(): Promise<Record<string, any>> {
    try {
      const response = await apiClient.get<Record<string, any>>(
        API_ENDPOINTS.DASHBOARD.CONFIG
      )
      return response.data
    } catch (error) {
      console.error('Failed to fetch system configuration:', error)
      throw error
    }
  }

  async updateSystemConfiguration(config: Record<string, any>): Promise<void> {
    try {
      await apiClient.put(API_ENDPOINTS.DASHBOARD.CONFIG, config)
    } catch (error) {
      console.error('Failed to update system configuration:', error)
      throw error
    }
  }
}

export const dashboardService = new DashboardService()