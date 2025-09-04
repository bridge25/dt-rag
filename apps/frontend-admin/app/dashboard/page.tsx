import { AppLayout } from '@/components/layout/AppLayout'

export default function DashboardPage() {
  return (
    <AppLayout currentPage="dashboard">
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center py-12">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Admin Dashboard</h1>
            <p className="text-gray-600 mb-8">관리자 대시보드 구현 예정</p>
            <div className="bg-yellow-100 border border-yellow-300 rounded-lg p-4">
              <p className="text-yellow-700">🚧 C-F4 구현 대기중: Admin dashboard with metrics and rollback</p>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}