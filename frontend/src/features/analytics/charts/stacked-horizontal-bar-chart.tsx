"use client"

import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

interface StackedSegment {
  key: string
  label: string
  color: string
}

interface StackedHorizontalBarChartProps {
  data: Record<string, number | string>[]
  segments: StackedSegment[]
  height?: number
  labelWidth?: number
  /** Key on each row holding a precomputed total, drawn as a direct label past the last segment. */
  totalKey?: string
  valueFormatter?: (value: number) => string
}

function StackedHorizontalBarChart({
  data,
  segments,
  height = 256,
  labelWidth = 100,
  totalKey,
  valueFormatter = (value) => String(value),
}: StackedHorizontalBarChartProps) {
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ left: 0, right: totalKey ? 40 : 16, top: 4, bottom: 4 }}
        >
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
            formatter={(value, name) => [valueFormatter(Number(value)), name]}
            contentStyle={{
              borderRadius: 8,
              border: "1px solid var(--color-border)",
              background: "var(--color-card)",
              fontSize: 12,
            }}
          />
          {segments.map((segment, index) => (
            <Bar
              key={segment.key}
              dataKey={segment.key}
              name={segment.label}
              stackId="stack"
              fill={segment.color}
              maxBarSize={18}
              radius={
                segments.length === 1
                  ? [4, 4, 4, 4]
                  : index === segments.length - 1
                    ? [0, 4, 4, 0]
                    : index === 0
                      ? [4, 0, 0, 4]
                      : 0
              }
            >
              {index === segments.length - 1 && totalKey && (
                <LabelList
                  dataKey={totalKey}
                  position="right"
                  fontSize={12}
                  fill="var(--color-muted-foreground)"
                  formatter={(value) => valueFormatter(Number(value))}
                />
              )}
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export { StackedHorizontalBarChart }
export type { StackedSegment }
