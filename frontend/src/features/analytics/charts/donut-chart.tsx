"use client"

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts"

interface DonutDatum {
  label: string
  value: number
  color: string
}

interface DonutChartProps {
  data: DonutDatum[]
  size?: number
  centerLabel?: React.ReactNode
  valueFormatter?: (value: number) => string
}

// Parts-of-whole, identity encoded: color follows the entity (never repainted by
// filters), legend always present with values so identity never rests on color alone.
function DonutChart({ data, size = 176, centerLabel, valueFormatter = (v) => String(v) }: DonutChartProps) {
  return (
    <div className="flex flex-wrap items-center gap-6">
      <div className="relative shrink-0" style={{ height: size, width: size }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="label"
              innerRadius="62%"
              outerRadius="100%"
              paddingAngle={2}
              stroke="var(--color-card)"
              strokeWidth={2}
            >
              {data.map((d) => (
                <Cell key={d.label} fill={d.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value, name) => [valueFormatter(Number(value)), name]}
              contentStyle={{
                borderRadius: 8,
                border: "1px solid var(--color-border)",
                background: "var(--color-card)",
                fontSize: 12,
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        {centerLabel && (
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            {centerLabel}
          </div>
        )}
      </div>
      <div className="flex min-w-[160px] flex-1 flex-col gap-2.5">
        {data.map((d) => (
          <div key={d.label} className="flex items-center justify-between gap-4 text-sm">
            <span className="flex items-center gap-2 text-muted-foreground">
              <span className="size-2 shrink-0 rounded-full" style={{ background: d.color }} />
              {d.label}
            </span>
            <span className="font-medium tabular-nums">{valueFormatter(d.value)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export { DonutChart }
export type { DonutDatum }
