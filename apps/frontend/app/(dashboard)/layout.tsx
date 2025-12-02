/**
 * Dashboard layout component
 * Ethereal Glass themed layout with space background and sidebar navigation
 * (Migrated from Vite frontend pattern per frontend-design-master-plan.md)
 *
 * @CODE:FRONTEND-001
 * @CODE:FRONTEND-REDESIGN-001
 */

import type { ReactNode } from "react"
import { Sidebar } from "@/components/layout/Sidebar"

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen bg-dark-navy space-background">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}
