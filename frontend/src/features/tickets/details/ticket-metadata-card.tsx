import { SectionCard } from "@/components/app/page"
import { StatusBadge, PriorityBadge } from "@/components/app/status"
import { Badge } from "@/components/ui/badge"
import { functionalTeamLabels, formatEnumValue } from "@/features/tickets/constants"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]

const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
})
const dateTimeFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
})

function MetadataRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 py-2.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-right text-sm font-medium">{children}</span>
    </div>
  )
}

function TicketMetadataCard({ ticket }: { ticket: TicketDetail }) {
  return (
    <SectionCard title="Informations du ticket" bodyClassName="divide-y divide-border">
      <MetadataRow label="Statut">
        <StatusBadge status={ticket.status} />
      </MetadataRow>
      <MetadataRow label="Priorité">
        <PriorityBadge priority={ticket.priority} />
      </MetadataRow>
      <MetadataRow label="Application">{ticket.application}</MetadataRow>
      <MetadataRow label="Catégorie">{ticket.category}</MetadataRow>
      <MetadataRow label="Équipe fonctionnelle">
        {functionalTeamLabels[ticket.functional_team]}
      </MetadataRow>
      <MetadataRow label="Ingénieur affecté">{ticket.assignee?.display_name ?? "Non affecté"}</MetadataRow>
      <MetadataRow label="Offre">{ticket.offer ? formatEnumValue(ticket.offer) : "—"}</MetadataRow>
      <MetadataRow label="Version">{ticket.version ? formatEnumValue(ticket.version) : "—"}</MetadataRow>
      <MetadataRow label="Point d'attention">
        {ticket.operational_highlight ? <Badge variant="warning">Oui</Badge> : "Non"}
      </MetadataRow>
      <MetadataRow label="Nécessite Jira">
        {ticket.requires_jira ? <Badge variant="info">Oui</Badge> : "Non"}
      </MetadataRow>
      <MetadataRow label="Identifiant Jira">{ticket.jira_id ?? "—"}</MetadataRow>
      <MetadataRow label="Livraison Jira">
        {ticket.jira_delivery_date ? dateFormatter.format(new Date(ticket.jira_delivery_date)) : "—"}
      </MetadataRow>
      <MetadataRow label="Identifiant Oceane">{ticket.oceane_id ?? "—"}</MetadataRow>
      <MetadataRow label="Identifiant Genergy">{ticket.genergy_id ?? "—"}</MetadataRow>
      <MetadataRow label="Application VIO">{ticket.vio_app ?? "—"}</MetadataRow>
      <MetadataRow label="Créé le">{dateTimeFormatter.format(new Date(ticket.created_at))}</MetadataRow>
      <MetadataRow label="Mis à jour le">{dateTimeFormatter.format(new Date(ticket.updated_at))}</MetadataRow>
    </SectionCard>
  )
}

export { TicketMetadataCard }
