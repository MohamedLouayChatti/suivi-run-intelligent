import { SectionCard } from "@/components/app/page"
import { statusConfig, priorityConfig } from "@/components/app/status"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]
type HistoryEntry = components["schemas"]["TicketHistoryEntryResponse"]

const dateTimeFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
})

function historyEntryLabel(entry: HistoryEntry): string {
  switch (entry.event_type) {
    case "CREATED":
      return "Ticket créé"
    case "STATUS_CHANGED":
      return entry.from_status && entry.to_status
        ? `Statut changé : ${statusConfig[entry.from_status].label} → ${statusConfig[entry.to_status].label}`
        : "Statut changé"
    case "PRIORITY_CHANGED":
      return entry.from_priority && entry.to_priority
        ? `Priorité changée : ${priorityConfig[entry.from_priority].label} → ${priorityConfig[entry.to_priority].label}`
        : "Priorité changée"
    case "REASSIGNED":
      return `Réaffecté à ${entry.assignee?.display_name ?? "un utilisateur inconnu"}`
    case "TRANSFERRED":
      return `Transféré vers ${entry.transferred_to ?? "une autre file"}`
    case "ARCHIVED":
      return "Ticket archivé"
    case "RESTORED":
      return "Ticket restauré"
    default:
      return entry.event_type
  }
}

function ActivityTimeline({ ticket }: { ticket: TicketDetail }) {
  const events = ticket.history

  return (
    <SectionCard title="Historique du ticket" description="Événements du cycle de vie">
      {events.length === 0 ? (
        <p className="text-sm text-muted-foreground">Aucun événement pour le moment.</p>
      ) : (
        <ol className="space-y-0">
          {events.map((event, i) => (
            <li key={event.id} className="relative flex gap-3">
              <div className="flex flex-col items-center">
                <span className="mt-1 size-2 shrink-0 rounded-full bg-primary" />
                {i < events.length - 1 && <span className="w-px flex-1 bg-border" />}
              </div>
              <div className="pb-4">
                <p className="text-sm font-medium">{historyEntryLabel(event)}</p>
                <p className="text-xs text-muted-foreground">
                  {dateTimeFormatter.format(new Date(event.occurred_at))}
                </p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </SectionCard>
  )
}

export { ActivityTimeline }
