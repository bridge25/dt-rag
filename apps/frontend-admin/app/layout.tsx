import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Dynamic Taxonomy RAG v1.8.1',
  description: '동적 다단계 분류 시스템 - 트리형 UI와 에이전트 팩토리',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          <header className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center py-4">
                <h1 className="text-xl font-semibold text-gray-900">
                  Dynamic Taxonomy RAG v1.8.1
                </h1>
                <nav className="flex space-x-4">
                  <a href="/" className="text-gray-600 hover:text-gray-900">트리뷰</a>
                  <a href="/agent-factory" className="text-gray-600 hover:text-gray-900">Agent Factory</a>
                  <a href="/chat" className="text-gray-600 hover:text-gray-900">Chat</a>
                  <a href="/admin" className="text-gray-600 hover:text-gray-900">Admin</a>
                </nav>
              </div>
            </div>
          </header>
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}