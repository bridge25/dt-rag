import { AppLayout } from '@/components/layout/AppLayout'

export default function ChatPage() {
  return (
    <AppLayout currentPage="chat">
      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Chat UI</h1>
            <p className="text-gray-600 mb-8">채팅 인터페이스 구현 예정</p>
            <div className="bg-yellow-100 border border-yellow-300 rounded-lg p-4">
              <p className="text-yellow-700">🚧 C-F3 구현 대기중: Chat UI with sources and accuracy toggle</p>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}