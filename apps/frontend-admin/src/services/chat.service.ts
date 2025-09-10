import { apiClient } from './api-client'
import { API_ENDPOINTS } from '@/constants/api'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: SourceDocument[]
  accuracy?: number
}

export interface SourceDocument {
  id: string
  title: string
  url?: string
  excerpt: string
  relevanceScore: number
  taxonomyPath: string[]
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  include_sources?: boolean
  accuracy_threshold?: number
}

export interface ChatResponse {
  message: ChatMessage
  conversation_id: string
  processing_time_ms: number
}

class ChatService {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await apiClient.post<ChatResponse>(
        API_ENDPOINTS.CHAT.SEND,
        request
      )
      return response.data
    } catch (error) {
      console.error('Failed to send chat message:', error)
      throw error
    }
  }

  async getConversation(conversationId: string): Promise<ChatMessage[]> {
    try {
      const response = await apiClient.get<ChatMessage[]>(
        `${API_ENDPOINTS.CHAT.CONVERSATION}/${conversationId}`
      )
      return response.data
    } catch (error) {
      console.error('Failed to get conversation:', error)
      throw error
    }
  }

  async clearConversation(conversationId: string): Promise<void> {
    try {
      await apiClient.delete(
        `${API_ENDPOINTS.CHAT.CONVERSATION}/${conversationId}`
      )
    } catch (error) {
      console.error('Failed to clear conversation:', error)
      throw error
    }
  }

  async getConversationHistory(): Promise<{ id: string, title: string, lastMessage: string, timestamp: string }[]> {
    try {
      const response = await apiClient.get<any[]>(
        API_ENDPOINTS.CHAT.HISTORY
      )
      return response.data
    } catch (error) {
      console.error('Failed to get conversation history:', error)
      throw error
    }
  }
}

export const chatService = new ChatService()