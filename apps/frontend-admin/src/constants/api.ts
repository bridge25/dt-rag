export const API_ENDPOINTS = {
  // Base URLs
  BASE_URL: process.env.NEXT_PUBLIC_TAXONOMY_API_URL || 'http://localhost:8000',
  
  // Taxonomy endpoints
  TAXONOMY: {
    VERSIONS: '/api/taxonomy/versions',
    TREE: '/api/taxonomy/tree',
    SEARCH: '/api/taxonomy/search'
  },
  
  // Agent Factory endpoints
  AGENT_FACTORY: {
    AGENTS: '/api/agents',
    CREATE: '/api/agents/create',
    TEST: '/api/agents/test'
  },
  
  // Chat endpoints
  CHAT: {
    MESSAGES: '/api/chat/messages',
    SEND: '/api/chat/send',
    CONVERSATION: '/api/chat/conversation',
    HISTORY: '/api/chat/history'
  },
  
  // Dashboard endpoints
  DASHBOARD: {
    METRICS: '/api/dashboard/metrics',
    HEALTH: '/api/dashboard/health',
    METRIC_HISTORY: '/api/dashboard/metrics/history',
    ROLLBACKS: '/api/dashboard/rollbacks',
    ROLLBACK_INITIATE: '/api/dashboard/rollback',
    ROLLBACK_STATUS: '/api/dashboard/rollback/status',
    VERSIONS: '/api/dashboard/versions',
    EXPORT_LOGS: '/api/dashboard/logs/export',
    BACKUP_CREATE: '/api/dashboard/backup',
    ALERT_RULES: '/api/dashboard/alerts',
    CONFIG: '/api/dashboard/config'
  }
} as const

export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
} as const