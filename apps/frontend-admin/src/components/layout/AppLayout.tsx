'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ChevronRight, Home, Settings, TestTube, BarChart3, MessageSquare } from 'lucide-react'

interface AppLayoutProps {
  children: React.ReactNode
  currentPage: string
}

const navigationItems = [
  { id: 'tree', label: 'Tree View', icon: Home, path: '/' },
  { id: 'agents', label: 'Agent Factory', icon: Settings, path: '/agents' },
  { id: 'chat', label: 'Chat UI', icon: MessageSquare, path: '/chat' },
  { id: 'dashboard', label: 'Admin Dashboard', icon: BarChart3, path: '/dashboard' },
  { id: 'testing', label: 'Testing', icon: TestTube, path: '/testing' },
]

export function AppLayout({ children, currentPage }: AppLayoutProps) {
  const router = useRouter()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const currentItem = navigationItems.find(item => item.id === currentPage)

  return (
    <div className="flex h-screen bg-white">
      {/* 왼쪽 사이드바 - Navigation */}
      <div className={`${sidebarCollapsed ? 'w-16' : 'w-64'} bg-gray-100 border-r border-gray-200 flex flex-col transition-all duration-200`}>
        {/* 사이드바 헤더 */}
        <div className="p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between">
            {!sidebarCollapsed && (
              <h2 className="text-sm font-bold text-gray-700 uppercase tracking-wide">
                Dynamic RAG Admin
              </h2>
            )}
            <button 
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
            >
              <ChevronRight className={`w-4 h-4 transition-transform ${sidebarCollapsed ? 'rotate-0' : 'rotate-180'}`} />
            </button>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 p-3 space-y-1">
          {navigationItems.map((item) => {
            const Icon = item.icon
            const isActive = item.id === currentPage
            
            return (
              <button
                key={item.id}
                onClick={() => router.push(item.path)}
                className={`
                  w-full flex items-center px-3 py-2 text-sm rounded-md transition-colors
                  ${isActive 
                    ? 'bg-blue-100 text-blue-700 font-medium border-l-2 border-l-blue-500' 
                    : 'text-gray-700 hover:bg-gray-200'
                  }
                `}
                title={sidebarCollapsed ? item.label : ''}
              >
                <Icon className={`w-4 h-4 ${sidebarCollapsed ? 'mx-auto' : 'mr-3'}`} />
                {!sidebarCollapsed && (
                  <span className="truncate">{item.label}</span>
                )}
              </button>
            )
          })}
        </nav>

        {/* 사이드바 푸터 */}
        <div className="p-3 border-t border-gray-200 bg-gray-50">
          {!sidebarCollapsed && (
            <div className="text-xs text-gray-500 text-center">
              v1.8.1 • C팀 Frontend
            </div>
          )}
        </div>
      </div>

      {/* 오른쪽 컨텐츠 영역 */}
      <div className="flex-1 flex flex-col">
        {/* 상단 헤더 */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
          <div className="flex items-center space-x-2 text-sm">
            <Home className="w-4 h-4 text-gray-400" />
            <ChevronRight className="w-3 h-3 text-gray-400" />
            {currentItem && (
              <>
                <currentItem.icon className="w-4 h-4 text-gray-600" />
                <span className="text-gray-800 font-medium">{currentItem.label}</span>
              </>
            )}
          </div>
        </div>

        {/* 메인 컨텐츠 */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}