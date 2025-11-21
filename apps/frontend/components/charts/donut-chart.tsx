/**
 * Donut chart component
 *
 * @CODE:MONITORING-001
 */

"use client"

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"

interface DonutChartProps {
  data?: Array<{ name: string; value: number; color: string }>
  centerValue?: string
}

const defaultData = [
  { name: "Documents", value: 68, color: "#6FA989" },
  { name: "Images", value: 55, color: "#5F5AB4" },
  { name: "Videos", value: 62, color: "#F59E0B" },
  { name: "Free", value: 315, color: "#1F2937" },
]

export function DonutChart({ data = defaultData, centerValue = "37%" }: DonutChartProps) {
  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <p className="text-3xl font-bold">{centerValue}</p>
          <p className="text-xs text-muted-foreground">Used</p>
        </div>
      </div>
    </div>
  )
}
