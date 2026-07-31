"use client"

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

interface VerticalBarDatum {
  label: string
  value: number
}

interface VerticalBarChartProps {
  data: VerticalBarDatum[]
  height?: number
  barColor?: string
  seriesName?: string
  valueFormatter?: (value: number) => string
}

function VerticalBarChart({
  data,
  height = 256,
  barColor = "var(--color-primary)",
  seriesName = "Valeur",
  valueFormatter = (value) => String(value),
}: VerticalBarChartProps) {
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: -20, right: 8, top: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            fontSize={12}
            stroke="var(--color-muted-foreground)"
          />
          <YAxis tickLine={false} axisLine={false} fontSize={12} stroke="var(--color-muted-foreground)" />
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
          <Bar dataKey="value" name={seriesName} fill={barColor} radius={[4, 4, 0, 0]} maxBarSize={40} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export { VerticalBarChart }
export type { VerticalBarDatum }
