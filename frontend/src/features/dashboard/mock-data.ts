import type { components } from "@/types/api"

type TicketSummary = components["schemas"]["TicketSummaryResponse"]

const currentAssignee = { id: "00000000-0000-0000-0000-000000000001", display_name: "Camille Martin" }

function isoAgo(hours: number): string {
  return new Date(Date.now() - hours * 60 * 60 * 1000).toISOString()
}

// Placeholder tickets assigned to the current engineer, covering every status.
// Replace with a real services/api/tickets.ts call once the endpoint exists — consumers
// only depend on TicketSummaryResponse[], so swapping the source is a one-line change.
const mockAssignedTickets: TicketSummary[] = [
  {
    id: "b1a1b1a1-0000-0000-0000-000000000001",
    title: "Rejeu du batch de règlement bloqué en file de reprise",
    application: "FCI",
    status: "IN_PROGRESS",
    priority: "P1",
    assignee: currentAssignee,
    category: "Anomalie applicatif",
    functional_team: "SUPPORT",
    operational_highlight: true,
    transferred_to: null,
    created_at: isoAgo(5),
    updated_at: isoAgo(1),
    archived_at: null,
  },
  {
    id: "b1a1b1a1-0000-0000-0000-000000000002",
    title: "Rapport de rapprochement : lignes de fin de journée manquantes",
    application: "COLORIS",
    status: "OPEN",
    priority: "P2",
    assignee: currentAssignee,
    category: "Bug",
    functional_team: "SUPPORT",
    operational_highlight: false,
    transferred_to: null,
    created_at: isoAgo(3),
    updated_at: isoAgo(3),
    archived_at: null,
  },
  {
    id: "b1a1b1a1-0000-0000-0000-000000000003",
    title: "Emails de réinitialisation de mot de passe retardés",
    application: "VIO",
    status: "OPEN",
    priority: "P3",
    assignee: currentAssignee,
    category: "Assistance client",
    functional_team: "SUPPORT",
    operational_highlight: false,
    transferred_to: null,
    created_at: isoAgo(8),
    updated_at: isoAgo(8),
    archived_at: null,
  },
  {
    id: "b1a1b1a1-0000-0000-0000-000000000004",
    title: "Export du grand livre tronqué pour les gros comptes",
    application: "FCI",
    status: "RESOLVED",
    priority: "P2",
    assignee: currentAssignee,
    category: "Bug",
    functional_team: "SUPPORT",
    operational_highlight: false,
    transferred_to: null,
    created_at: isoAgo(30),
    updated_at: isoAgo(2),
    archived_at: null,
  },
  {
    id: "b1a1b1a1-0000-0000-0000-000000000005",
    title: "Renouvellement du certificat TLS bloqué en pré-production",
    application: "AERO",
    status: "CLOSED",
    priority: "P1",
    assignee: currentAssignee,
    category: "Opération de service",
    functional_team: "SUPPORT",
    operational_highlight: false,
    transferred_to: null,
    created_at: isoAgo(50),
    updated_at: isoAgo(20),
    archived_at: null,
  },
  {
    id: "b1a1b1a1-0000-0000-0000-000000000006",
    title: "Volume de tickets Identity Service au-dessus de la normale",
    application: "COLORIS",
    status: "TRANSFERRED",
    priority: "P3",
    assignee: currentAssignee,
    category: "Hors périmètre",
    functional_team: "SUPPORT",
    operational_highlight: false,
    transferred_to: "Support COLORIS",
    created_at: isoAgo(70),
    updated_at: isoAgo(40),
    archived_at: null,
  },
]

// No /analytics endpoint exists yet — mocked and isolated here for a later one-file swap.
function buildMockTrend(days: number) {
  const points: { date: string; created: number; resolved: number }[] = []
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000)
    const base = 3 + Math.round(2 * Math.sin(i / 4))
    points.push({
      date: date.toISOString().slice(0, 10),
      created: Math.max(0, base + (i % 5 === 0 ? 2 : 0)),
      resolved: Math.max(0, base - (i % 7 === 0 ? 1 : 0)),
    })
  }
  return points
}

const mockTrend = buildMockTrend(30)

const mockConversations = [
  { id: "conv-1", title: "Procédure de lag des consumers Kafka", relativeTime: "il y a 18 min" },
  { id: "conv-2", title: "Comment rejouer la dead-letter queue", relativeTime: "il y a 2 h" },
  { id: "conv-3", title: "Politique SLA pour les incidents Sev2", relativeTime: "hier" },
]

const mockKpis = {
  activeAssignments: mockAssignedTickets.filter(
    (t) => t.status === "OPEN" || t.status === "IN_PROGRESS"
  ).length,
  resolvedThisWeek: 5,
  createdThisWeek: 7,
  avgResolutionMinutes: 375,
}

export { mockAssignedTickets, mockTrend, mockConversations, mockKpis }
