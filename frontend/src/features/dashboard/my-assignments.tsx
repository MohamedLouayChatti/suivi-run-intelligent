"use client"

import Link from "next/link"

import { SectionCard } from "@/components/app/page"
import { StatusBadge, PriorityBadge } from "@/components/app/status"
import { Button } from "@/components/ui/button"
import { usePermissions } from "@/lib/auth"
import type { components } from "@/types/api"

type TicketSummary = components["schemas"]["TicketSummaryResponse"]

interface MyAssignmentsProps {
  tickets: TicketSummary[]
}

function MyAssignments({ tickets }: MyAssignmentsProps) {
  const { canAccessRoute } = usePermissions()
  const active = tickets
    .filter((t) => t.status === "OPEN" || t.status === "IN_PROGRESS")
    .slice(0, 3)

  return (
    <SectionCard
      className="xl:col-span-2"
      title="Mes tickets actifs"
      description="Tickets qui vous sont affectés, en cours ou à démarrer"
      bodyClassName="p-0"
      action={
        canAccessRoute("/tickets") ? (
          <Button variant="ghost" size="sm" asChild>
            <Link href="/tickets">Voir tout</Link>
          </Button>
        ) : undefined
      }
    >
      {active.length === 0 ? (
        <p className="px-5 py-6 text-sm text-muted-foreground">
          Aucun ticket actif pour le moment.
        </p>
      ) : (
        <ul className="divide-y divide-border">
          {active.map((t) => (
            <li
              key={t.id}
              className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 px-5 py-3.5"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-muted-foreground">
                    {t.id.slice(0, 8)}
                  </span>
                  <PriorityBadge priority={t.priority} />
                  <StatusBadge status={t.status} />
                </div>
                <p className="mt-1 truncate text-sm font-medium">{t.title}</p>
                <p className="mt-0.5 truncate text-xs text-muted-foreground">
                  {t.application}
                </p>
              </div>
              <Button size="sm" variant="outline" asChild>
                <Link href={`/tickets/${t.id}`}>
                  {t.status === "IN_PROGRESS" ? "Reprendre" : "Démarrer"}
                </Link>
              </Button>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  )
}

export { MyAssignments }
