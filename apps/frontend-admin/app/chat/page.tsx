import { AppLayout } from '@/components/layout/AppLayout'
import { ChatInterface } from '@/components/chat/ChatInterface'

export default function ChatPage() {
  return (
    <AppLayout currentPage="chat">
      <ChatInterface />
    </AppLayout>
  )
}