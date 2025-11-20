// @CODE:HOME-STATS-001:STAT-CARD
interface StatCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  description?: string
}

export function StatCard({ title, value, icon, description }: StatCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        <div className="text-blue-600">{icon}</div>
      </div>
      <p className="text-2xl font-bold text-gray-800 mb-1">{value}</p>
      {description && (
        <p className="text-xs text-gray-500">{description}</p>
      )}
    </div>
  )
}
