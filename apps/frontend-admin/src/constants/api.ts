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
  }
} as const

export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
} as const