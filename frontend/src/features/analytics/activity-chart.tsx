"use client"

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

import { SectionCard } from "@/components/app/page"
import type { TimeRange } from "@/features/analytics/constants"
import type { ActivityPoint } from "@/features/analytics/types"

interface ActivityChartProps {
  data: ActivityPoint[]
  timeRange: TimeRange
}

const dayFormatter = new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "2-digit" })
const monthFormatter = new Intl.DateTimeFormat("fr-FR", { month: "short" })

// Operational Activity — the most visually prominent chart on the page (hero, full
// width, taller than the other charts). Same gradient-area pattern as the Dashboard's
// IncidentTrendChart, scaled up.
function ActivityChart({ data, timeRange }: ActivityChartProps) {
  // Matches the backend's bucketing scheme (bucket_scheme in time_range.py): daily
  // buckets for 30D/3M read better as day/month, the coarser 6M/1Y buckets as month only.
  const useDayLabel = timeRange === "30D" || timeRange === "3M"
  const formatBucket = (value: string) => {
    const date = new Date(value)
    return useDayLabel ? dayFormatter.format(date) : monthFormatter.format(date)
  }

  return (
    <SectionCard
      title="Activité opérationnelle"
      description="Tickets créés vs résolus sur la période sélectionnée"
      action={
        <span className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-primary" /> Créés
          </span>
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-muted-foreground/50" /> Résolus
          </span>
        </span>
      }
    >
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ left: -20, right: 8, top: 8 }}>
            <defs>
              <linearGradient id="analytics-activity-created" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.25} />
                <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="bucket_start"
              tickFormatter={formatBucket}
              tickLine={false}
              axisLine={false}
              fontSize={12}
              stroke="var(--color-muted-foreground)"
              minTickGap={24}
            />
            <YAxis tickLine={false} axisLine={false} fontSize={12} stroke="var(--color-muted-foreground)" />
            <Tooltip
              labelFormatter={(value) => (typeof value === "string" ? formatBucket(value) : value)}
              contentStyle={{
                borderRadius: 8,
                border: "1px solid var(--color-border)",
                background: "var(--color-card)",
                fontSize: 12,
              }}
            />
            <Area
              type="monotone"
              dataKey="created"
              name="Créés"
              stroke="var(--color-primary)"
              fill="url(#analytics-activity-created)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="resolved"
              name="Résolus"
              stroke="var(--color-muted-foreground)"
              fill="transparent"
              strokeWidth={1.5}
              strokeDasharray="4 3"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </SectionCard>
  )
}

export { ActivityChart }
