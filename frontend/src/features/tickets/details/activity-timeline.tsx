import { SectionCard } from "@/components/app/page"
import { buildActivityTimeline } from "@/features/tickets/details/mock-activity"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]

const dateTimeFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
})

function ActivityTimeline({ ticket }: { ticket: TicketDetail }) {
  const events = buildActivityTimeline(ticket)

  return (
    <SectionCard title="Historique du ticket" description="Événements du cycle de vie">
      <ol className="space-y-0">
        {events.map((event, i) => (
          <li key={event.id} className="relative flex gap-3">
            <div className="flex flex-col items-center">
              <span className="mt-1 size-2 shrink-0 rounded-full bg-primary" />
              {i < events.length - 1 && <span className="w-px flex-1 bg-border" />}
            </div>
            <div className="pb-4">
              <p className="text-sm font-medium">{event.label}</p>
              <p className="text-xs text-muted-foreground">
                {dateTimeFormatter.format(new Date(event.timestamp))}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </SectionCard>
  )
}

export { ActivityTimeline }
