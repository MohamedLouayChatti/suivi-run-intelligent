"use client"

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

import { SectionCard } from "@/components/app/page"
import { applicationOptions } from "@/features/tickets/constants"
import type { AppMonthlyTrendPoint } from "@/features/analytics/types"

interface MonthlyTrendsProps {
  data: AppMonthlyTrendPoint[]
}

// One line per application — fixed categorical order onto --chart-1..4, same rule as
// the status donut.
const appColor: Record<(typeof applicationOptions)[number], string> = {
  FCI: "var(--color-chart-1)",
  COLORIS: "var(--color-chart-2)",
  AERO: "var(--color-chart-3)",
  VIO: "var(--color-chart-4)",
}

const monthFormatter = new Intl.DateTimeFormat("fr-FR", { month: "short" })

function MonthlyTrends({ data }: MonthlyTrendsProps) {
  return (
    <SectionCard
      title="Tendances mensuelles"
      description="Volume de tickets par application sur 12 mois"
      action={
        <span className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          {applicationOptions.map((app) => (
            <span key={app} className="flex items-center gap-1.5">
              <span className="size-2 rounded-full" style={{ background: appColor[app] }} /> {app}
            </span>
          ))}
        </span>
      }
    >
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ left: -20, right: 8, top: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="month"
              tickFormatter={(value: string) => monthFormatter.format(new Date(value))}
              tickLine={false}
              axisLine={false}
              fontSize={12}
              stroke="var(--color-muted-foreground)"
            />
            <YAxis tickLine={false} axisLine={false} fontSize={12} stroke="var(--color-muted-foreground)" />
            <Tooltip
              labelFormatter={(value) =>
                typeof value === "string" ? monthFormatter.format(new Date(value)) : value
              }
              contentStyle={{
                borderRadius: 8,
                border: "1px solid var(--color-border)",
                background: "var(--color-card)",
                fontSize: 12,
              }}
            />
            {applicationOptions.map((app) => (
              <Line
                key={app}
                type="monotone"
                dataKey={(row: AppMonthlyTrendPoint) => row.counts[app]}
                name={app}
                stroke={appColor[app]}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </SectionCard>
  )
}

export { MonthlyTrends }
