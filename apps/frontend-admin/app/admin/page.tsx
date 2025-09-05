import { AppLayout } from '@/components/layout/AppLayout'
import { AdminDashboard } from '@/components/dashboard/AdminDashboard'

export default function AdminPage() {
  return (
    <AppLayout currentPage="dashboard">
      <AdminDashboard />
    </AppLayout>
  )
}