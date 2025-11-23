/**
 * Dashboard layout component
 * Simplified layout - pages handle their own layout structure
 * (Migrated from Vite frontend pattern per frontend-design-master-plan.md)
 *
 * @CODE:FRONTEND-001
 * @CODE:FRONTEND-MIGRATION-001
 */

import type { ReactNode } from "react";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {children}
    </div>
  );
}
