/**
 * Dashboard layout component
 * Ethereal Glass themed layout with space background
 * (Migrated from Vite frontend pattern per frontend-design-master-plan.md)
 *
 * @CODE:FRONTEND-001
 * @CODE:FRONTEND-REDESIGN-001
 */

import type { ReactNode } from "react"

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-dark-navy space-background">
      {/* Space background ensures consistent Ethereal Glass aesthetic */}
      {children}
    </div>
  )
}
