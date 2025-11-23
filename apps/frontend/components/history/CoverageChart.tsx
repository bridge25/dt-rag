/**
 * Coverage Chart Component
 * Displays a line chart showing coverage trends over time
 *
 * @CODE:FRONTEND-MIGRATION-002:COVERAGE-CHART
 */
"use client"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts"
import type { CoverageHistoryItem } from "@/lib/api/history"

interface CoverageChartProps {
  data: CoverageHistoryItem[]
}

export function CoverageChart({ data }: CoverageChartProps) {
  const chartData = data.map((item) => ({
    date: new Date(item.date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    coverage: parseFloat(item.coverage.toFixed(1)),
  }))

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Coverage Trend</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 12 }}
            label={{ value: "Coverage (%)", angle: -90, position: "insideLeft" }}
          />
          <Tooltip
            formatter={(value: number) => [`${value}%`, "Coverage"]}
            labelStyle={{ color: "#000" }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="coverage"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
            name="Coverage %"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
