import { useState, useCallback, useRef, useEffect } from 'react'
import { chatService, ChatMessage, ChatRequest, SourceDocument } from '@/services/chat.service'

interface UseChatOptions {
  initialMessages?: ChatMessage[]
  conversationId?: string
  mockMode?: boolean
}

interface UseChatReturn {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
  sendMessage: (content: string, options?: { includeSource?: boolean, accuracyThreshold?: number }) => Promise<void>
  clearMessages: () => void
  retryLastMessage: () => Promise<void>
  conversationId: string | null
}

// Mock 소스 문서
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

// Mock 응답 생성
const generateMockResponse = (userMessage: string): string => {
  const responses = [
    `Based on your question about "${userMessage.slice(0, 20)}...", I can provide detailed insights from the available documentation. This response demonstrates the RAG system's ability to provide contextual information.`,
    `Here's what I found regarding your query. The system has analyzed multiple sources and provides this comprehensive answer with supporting documentation references.`,
    `Thank you for your question. I've searched through the available knowledge base and can offer the following analysis with relevant source materials.`,
    `Your inquiry about the dynamic taxonomy system touches on several important concepts. Let me explain based on the current documentation and best practices.`
  ]
  return responses[Math.floor(Math.random() * responses.length)]
}

export function useChat(options: UseChatOptions = {}): UseChatReturn {
  const { initialMessages = [], conversationId: initialConversationId, mockMode = true } = options
  
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(initialConversationId || null)
  
  const lastUserMessageRef = useRef<string>('')

  const sendMessage = useCallback(async (
    content: string, 
    options: { includeSource?: boolean, accuracyThreshold?: number } = {}
  ) => {
    if (!content.trim()) return

    const { includeSource = true, accuracyThreshold = 0.8 } = options
    lastUserMessageRef.current = content

    // 사용자 메시지 추가
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    try {
      if (mockMode) {
        // Mock 응답 생성
        await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1500))
        
        const assistantMessage: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          role: 'assistant',
          content: generateMockResponse(content),
          timestamp: new Date().toISOString(),
          sources: includeSource ? MOCK_SOURCES.slice(0, Math.floor(Math.random() * 3) + 1) : undefined,
          accuracy: 0.75 + Math.random() * 0.2
        }

        setMessages(prev => [...prev, assistantMessage])
        
        // Mock conversation ID 생성
        if (!conversationId) {
          setConversationId(`conv-${Date.now()}`)
        }
      } else {
        // 실제 API 호출
        const request: ChatRequest = {
          message: content,
          conversation_id: conversationId || undefined,
          include_sources: includeSource,
          accuracy_threshold: accuracyThreshold
        }

        const response = await chatService.sendMessage(request)
        
        setMessages(prev => [...prev, response.message])
        setConversationId(response.conversation_id)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다'
      setError(errorMessage)
      
      // 오류 메시지 표시
      const errorResponseMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `죄송합니다. 오류가 발생했습니다: ${errorMessage}`,
        timestamp: new Date().toISOString(),
        accuracy: 0
      }
      
      setMessages(prev => [...prev, errorResponseMessage])
    } finally {
      setIsLoading(false)
    }
  }, [conversationId, mockMode])

  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
    if (conversationId && !mockMode) {
      chatService.clearConversation(conversationId).catch(console.error)
    }
    setConversationId(null)
  }, [conversationId, mockMode])

  const retryLastMessage = useCallback(async () => {
    if (lastUserMessageRef.current) {
      // 마지막 어시스턴트 메시지 제거 후 재시도
      setMessages(prev => {
        const lastUserIndex = prev.findLastIndex(msg => msg.role === 'user')
        if (lastUserIndex !== -1) {
          return prev.slice(0, lastUserIndex + 1)
        }
        return prev
      })
      
      await sendMessage(lastUserMessageRef.current)
    }
  }, [sendMessage])

  // 컴포넌트 언마운트시 정리
  useEffect(() => {
    return () => {
      setIsLoading(false)
      setError(null)
    }
  }, [])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    retryLastMessage,
    conversationId
  }
}