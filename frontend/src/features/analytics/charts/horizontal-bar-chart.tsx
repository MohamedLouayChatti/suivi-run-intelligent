"use client"

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

interface HorizontalBarDatum {
  label: string
  value: number
}

interface HorizontalBarChartProps {
  data: HorizontalBarDatum[]
  height?: number
  barColor?: string
  seriesName?: string
  valueFormatter?: (value: number) => string
  labelWidth?: number
}

// Single-series ranked bars: magnitude only, one hue — shared by every "top N" /
// comparison widget on the Analytics page (category, priority, per-app, per-engineer…).
function HorizontalBarChart({
  data,
  height = 256,
  barColor = "var(--color-primary)",
  seriesName = "Valeur",
  valueFormatter = (value) => String(value),
  labelWidth = 140,
}: HorizontalBarChartProps) {
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 0, right: 24, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
          <XAxis
            type="number"
            tickLine={false}
            axisLine={false}
            fontSize={12}
            stroke="var(--color-muted-foreground)"
          />
          <YAxis
            type="category"
            dataKey="label"
            tickLine={false}
            axisLine={false}
            fontSize={12}
            stroke="var(--color-muted-foreground)"
            width={labelWidth}
          />
          <Tooltip
            cursor={{ fill: "var(--color-muted)" }}
            formatter={(value) => [valueFormatter(Number(value)), seriesName]}
            contentStyle={{
              borderRadius: 8,
              border: "1px solid var(--color-border)",
              background: "var(--color-card)",
              fontSize: 12,
            }}
          />
          <Bar
            dataKey="value"
            name={seriesName}
            fill={barColor}
            radius={[0, 4, 4, 0]}
            maxBarSize={18}
            background={{ fill: "var(--color-muted)", radius: 4 }}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export { HorizontalBarChart }
export type { HorizontalBarDatum }
