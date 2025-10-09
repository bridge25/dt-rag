import type { Metadata } from 'next'
import { ToastProvider } from '@/contexts/ToastContext'
import '@/app/globals.css'

export const metadata: Metadata = {
  title: 'Dynamic Taxonomy RAG System',
  description: 'Frontend Admin Interface for DT-RAG v1.8.1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>
        <ToastProvider>
          <div className="min-h-screen bg-gray-100">
            <header className="bg-blue-600 text-white p-4">
              <h1 className="text-2xl font-bold">🚀 Dynamic Taxonomy RAG System v1.8.1</h1>
              <p>Frontend Admin Interface - Production Ready</p>
            </header>
            <main className="container mx-auto p-4">
              {children}
            </main>
          </div>
        </ToastProvider>
      </body>
    </html>
  )
}