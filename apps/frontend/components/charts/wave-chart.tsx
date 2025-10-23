"use client"

import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis } from "recharts"

interface WaveChartProps {
  data?: Array<{ name: string; value: number }>
}

const defaultData = [
  { name: "Su", value: 30 },
  { name: "Mo", value: 45 },
  { name: "Tu", value: 35 },
  { name: "We", value: 60 },
  { name: "Th", value: 40 },
  { name: "Fr", value: 55 },
  { name: "Sa", value: 50 },
]

export function WaveChart({ data = defaultData }: WaveChartProps) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorWave" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#7ECECA" stopOpacity={0.8} />
            <stop offset="95%" stopColor="#7ECECA" stopOpacity={0.1} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="name"
          stroke="#6B7280"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis hide />
        <Area
          type="monotone"
          dataKey="value"
          stroke="#7ECECA"
          strokeWidth={3}
          fillOpacity={1}
          fill="url(#colorWave)"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
