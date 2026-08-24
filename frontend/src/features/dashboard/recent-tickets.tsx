"use client"

import Link from "next/link"

import { SectionCard } from "@/components/app/page"
import { StatusBadge } from "@/components/app/status"
import { Button } from "@/components/ui/button"
import { usePermissions } from "@/lib/auth"
import type { components } from "@/types/api"

type TicketSummary = components["schemas"]["TicketSummaryResponse"]

const relativeTimeFormatter = new Intl.RelativeTimeFormat("fr-FR", { numeric: "auto" })

function formatRelativeCompletion(isoDate: string): string {
  const diffMs = new Date(isoDate).getTime() - Date.now()
  const diffHours = Math.round(diffMs / (1000 * 60 * 60))
  if (Math.abs(diffHours) < 24) return relativeTimeFormatter.format(diffHours, "hour")
  const diffDays = Math.round(diffHours / 24)
  return relativeTimeFormatter.format(diffDays, "day")
}

interface RecentTicketsProps {
  tickets: TicketSummary[]
}

function RecentTickets({ tickets }: RecentTicketsProps) {
  const { canAccessRoute } = usePermissions()
  const completed = tickets
    .filter((t) => t.status === "CLOSED" || t.status === "TRANSFERRED")
    .slice(0, 5)

  return (
    <SectionCard
      title="Tickets récents"
      description="Travail complété récemment"
      bodyClassName="p-0"
    >
      <ul className="divide-y divide-border">
        {completed.map((t) => (
          <li key={t.id}>
            <Link
              href={`/tickets/${t.id}`}
              className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 px-5 py-3 transition-colors hover:bg-surface"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-muted-foreground">
                    {t.id.slice(0, 8)}
                  </span>
                  <StatusBadge status={t.status} />
                </div>
                <p className="mt-1 truncate text-sm font-medium">{t.title}</p>
              </div>
              <span className="shrink-0 text-xs text-muted-foreground">
                {formatRelativeCompletion(t.updated_at)}
              </span>
            </Link>
          </li>
        ))}
      </ul>
      {canAccessRoute("/history") && (
        <div className="border-t border-border px-5 py-3">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/history">Voir l&apos;historique</Link>
          </Button>
        </div>
      )}
    </SectionCard>
  )
}

export { RecentTickets }
