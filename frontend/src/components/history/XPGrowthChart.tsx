// @CODE:FRONTEND-INTEGRATION-001:XP-CHART
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import type { CoverageHistoryItem } from '@/lib/api/history'

interface XPGrowthChartProps {
  data: CoverageHistoryItem[]
}

export function XPGrowthChart({ data }: XPGrowthChartProps) {
  const chartData = data.map((item, index) => {
    const previousXP = index > 0 ? data[index - 1].xp : item.xp
    const xpGain = item.xp - previousXP

    return {
      date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      xpGain: Math.max(0, xpGain),
    }
  })

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">XP Growth</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            label={{ value: 'XP Gained', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip
            formatter={(value: number) => [`${value} XP`, 'Daily Gain']}
            labelStyle={{ color: '#000' }}
          />
          <Legend />
          <Bar
            dataKey="xpGain"
            fill="#8B5CF6"
            radius={[8, 8, 0, 0]}
            name="XP Gained"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
