"use client"

import {
  AreaChart,
  Area,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts"

import { SectionCard } from "@/components/app/page"

interface IncidentTrendChartProps {
  data: { date: string; created: number; resolved: number }[]
}

function IncidentTrendChart({ data }: IncidentTrendChartProps) {
  return (
    <SectionCard
      className="xl:col-span-2"
      title="Tendance des incidents"
      description="Créés vs résolus — 30 derniers jours"
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
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ left: -20, right: 8, top: 8 }}>
            <defs>
              <linearGradient id="incident-trend-created" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.25} />
                <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              fontSize={12}
              stroke="var(--color-muted-foreground)"
              tickFormatter={(value: string) =>
                new Date(value).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" })
              }
              minTickGap={24}
            />
            <YAxis tickLine={false} axisLine={false} fontSize={12} stroke="var(--color-muted-foreground)" />
            <Tooltip
              labelFormatter={(value) =>
                typeof value === "string"
                  ? new Date(value).toLocaleDateString("fr-FR", { day: "numeric", month: "long" })
                  : value
              }
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
              fill="url(#incident-trend-created)"
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

export { IncidentTrendChart }
