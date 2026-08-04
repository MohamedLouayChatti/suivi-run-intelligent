import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]
type UserSummary = components["schemas"]["UserSummaryResponse"]

// Placeholder engineers used for the Assignee filter and the Create Ticket "Assignee" field.
// Replace with a real services/api/users.ts call once it exists — consumers only depend on
// UserSummaryResponse[], so swapping the source is a one-line change.
const mockUsers: UserSummary[] = [
  { id: "00000000-0000-0000-0000-000000000001", display_name: "Camille Martin" },
  { id: "00000000-0000-0000-0000-000000000002", display_name: "Yanis Belkacem" },
  { id: "00000000-0000-0000-0000-000000000003", display_name: "Sarah Nasri" },
  { id: "00000000-0000-0000-0000-000000000004", display_name: "Karim Haddad" },
  { id: "00000000-0000-0000-0000-000000000005", display_name: "Julie Perrot" },
]

const currentUserId = "00000000-0000-0000-0000-000000000001"

function findUser(id: string): UserSummary {
  return mockUsers.find((u) => u.id === id) ?? mockUsers[0]
}

function isoAgo(hours: number): string {
  return new Date(Date.now() - hours * 60 * 60 * 1000).toISOString()
}

let ticketSeq = 0

function makeTicket(overrides: Partial<TicketDetail> & Pick<TicketDetail, "title" | "application" | "status" | "priority" | "assignee">): TicketDetail {
  ticketSeq += 1
  const createdHoursAgo = overrides.created_at ? undefined : 24 + ticketSeq * 7
  return {
    // The first 8 characters are what the UI displays (truncated id in tables/breadcrumbs),
    // so the sequence must live there rather than in a shared, always-identical suffix.
    id: `${String(ticketSeq).padStart(8, "0")}-c2b2-c2b2-c2b2-c2b2c2b2c2b2`,
    description: "Description détaillée à compléter.",
    category: "Bug",
    functional_team: "SUPPORT",
    operational_highlight: false,
    transferred_to: null,
    created_at: createdHoursAgo ? isoAgo(createdHoursAgo) : isoAgo(24),
    updated_at: isoAgo(2),
    archived_at: null,
    resolved_at: null,
    closed_at: null,
    genergy_id: null,
    oceane_id: null,
    jira_id: null,
    jira_delivery_date: null,
    requires_jira: false,
    offer: null,
    version: null,
    element: null,
    vio_app: null,
    resolution_notes: null,
    comments: [],
    attachments: [],
    history: [],
    ...overrides,
  }
}

const me = findUser(currentUserId)

// Placeholder tickets covering "my active", "team active", and completed (History-only)
// statuses. Replace with a real services/api/tickets.ts call once it exists — consumers
// only depend on TicketSummaryResponse[] / TicketDetailResponse, so swapping the source
// is a one-line change.
const mockTickets: TicketDetail[] = [
  makeTicket({
    title: "Rejeu du batch de règlement bloqué en file de reprise",
    application: "FCI",
    status: "IN_PROGRESS",
    priority: "P1",
    assignee: me,
    category: "Anomalie applicatif",
    operational_highlight: true,
    created_at: isoAgo(5),
    updated_at: isoAgo(1),
    description:
      "Le batch de règlement quotidien reste bloqué en file de reprise depuis ce matin 6h. Aucun règlement n'a été émis depuis. Impact direct sur les échéances clients du jour.",
    genergy_id: "GEN-88213",
    jira_id: "FCI-4021",
    requires_jira: true,
    jira_delivery_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
    comments: [
      {
        id: "cm-1",
        author: me,
        content: "Reprise du batch relancée manuellement, en observation.",
        created_at: isoAgo(1),
        attachments: [],
        edited_at: null,
        deleted_at: null,
      },
    ],
    attachments: [
      {
        id: "at-1",
        filename: "logs-batch-reglement.log",
        content_type: "text/plain",
        storage_path: "/attachments/logs-batch-reglement.log",
        uploader: me,
        uploaded_at: isoAgo(4),
        deleted_at: null,
      },
    ],
  }),
  makeTicket({
    title: "Rapport de rapprochement : lignes de fin de journée manquantes",
    application: "COLORIS",
    status: "OPEN",
    priority: "P2",
    assignee: me,
    category: "Bug",
    created_at: isoAgo(3),
    updated_at: isoAgo(3),
    description:
      "Le rapport de rapprochement du 29/07 ne contient pas les lignes générées après 22h. À vérifier côté export nocturne.",
  }),
  makeTicket({
    title: "Emails de réinitialisation de mot de passe retardés",
    application: "VIO",
    status: "OPEN",
    priority: "P3",
    assignee: me,
    category: "Assistance client",
    created_at: isoAgo(8),
    updated_at: isoAgo(8),
    vio_app: "VIGIE",
    description: "Plusieurs utilisateurs signalent un délai de plus de 30 minutes pour recevoir l'email de réinitialisation.",
  }),
  makeTicket({
    title: "Export du grand livre tronqué pour les gros comptes",
    application: "FCI",
    status: "RESOLVED",
    priority: "P2",
    assignee: me,
    category: "Bug",
    created_at: isoAgo(30),
    updated_at: isoAgo(2),
    resolved_at: isoAgo(2),
    resolution_notes: "Correctif appliqué sur la pagination de l'export ; les comptes de plus de 10k lignes sont désormais complets.",
    description: "L'export du grand livre s'arrête à 10 000 lignes pour les comptes à fort volume, provoquant des écarts de clôture.",
  }),
  makeTicket({
    title: "Habilitation manquante suite à changement d'équipe",
    application: "VIO",
    status: "IN_PROGRESS",
    priority: "P4",
    assignee: me,
    category: "Habilitation",
    created_at: isoAgo(12),
    updated_at: isoAgo(6),
    vio_app: "SAGIC",
    description: "Un utilisateur transféré vers l'équipe Support n'a plus accès aux dossiers VIO depuis son changement d'équipe.",
  }),
  makeTicket({
    title: "Volume de tickets Identity Service au-dessus de la normale",
    application: "COLORIS",
    status: "TRANSFERRED",
    priority: "P3",
    assignee: me,
    category: "Hors périmètre",
    transferred_to: "Support COLORIS",
    created_at: isoAgo(70),
    updated_at: isoAgo(40),
    description: "Pic anormal de création de tickets liés à l'Identity Service, hors périmètre de l'équipe Support FCI.",
  }),
  makeTicket({
    title: "Renouvellement du certificat TLS bloqué en pré-production",
    application: "AERO",
    status: "CLOSED",
    priority: "P1",
    assignee: me,
    category: "Opération de service",
    created_at: isoAgo(50),
    updated_at: isoAgo(20),
    closed_at: isoAgo(20),
    description: "Le renouvellement automatique du certificat TLS a échoué sur l'environnement de pré-production.",
  }),

  // Team tickets — assigned to colleagues.
  makeTicket({
    title: "Connexion impossible sur le portail partenaire",
    application: "VIO",
    status: "OPEN",
    priority: "P1",
    assignee: findUser("00000000-0000-0000-0000-000000000002"),
    category: "Anomalie applicatif",
    operational_highlight: true,
    element: "Connexion impossible",
    vio_app: "FOP",
    created_at: isoAgo(2),
    updated_at: isoAgo(1),
    description: "Les partenaires ne peuvent plus se connecter au portail FOP depuis 9h ce matin, erreur 502 systématique.",
  }),
  makeTicket({
    title: "Doublons de règlement détectés sur le batch nocturne",
    application: "FCI",
    status: "IN_PROGRESS",
    priority: "P2",
    assignee: findUser("00000000-0000-0000-0000-000000000003"),
    category: "Anomalie applicatif",
    created_at: isoAgo(15),
    updated_at: isoAgo(4),
    description: "Certains règlements apparaissent en double sur le batch de la nuit dernière, à investiguer avant réémission.",
  }),
  makeTicket({
    title: "Données de facturation absentes pour trois comptes",
    application: "COLORIS",
    status: "OPEN",
    priority: "P2",
    assignee: findUser("00000000-0000-0000-0000-000000000003"),
    category: "Synchronisation des données",
    created_at: isoAgo(9),
    updated_at: isoAgo(9),
    description: "Trois comptes n'ont pas reçu leurs données de facturation lors de la dernière synchronisation.",
  }),
  makeTicket({
    title: "Demande d'assistance : export manuel non conforme",
    application: "AERO",
    status: "OPEN",
    priority: "P4",
    assignee: findUser("00000000-0000-0000-0000-000000000004"),
    category: "Assistance client",
    created_at: isoAgo(20),
    updated_at: isoAgo(18),
    description: "Le client signale que le format de l'export manuel ne correspond plus au gabarit attendu.",
  }),
  makeTicket({
    title: "Message d'erreur inattendu à la validation d'un dossier",
    application: "VIO",
    status: "IN_PROGRESS",
    priority: "P3",
    assignee: findUser("00000000-0000-0000-0000-000000000004"),
    category: "Bug",
    element: "Message d'erreur ou résultat inattendu",
    vio_app: "PARC",
    created_at: isoAgo(6),
    updated_at: isoAgo(2),
    description: "Une erreur générique apparaît à la validation de certains dossiers PARC sans plus de détail.",
  }),
  makeTicket({
    title: "Anomalie applicatif sur le module de reporting",
    application: "FCI",
    status: "RESOLVED",
    priority: "P3",
    assignee: findUser("00000000-0000-0000-0000-000000000005"),
    category: "Anomalie applicatif",
    created_at: isoAgo(40),
    updated_at: isoAgo(3),
    resolved_at: isoAgo(3),
    resolution_notes: "Requête de reporting corrigée, redéploiement effectué en production.",
    description: "Le module de reporting affichait des totaux erronés pour les rapports hebdomadaires.",
  }),
  makeTicket({
    title: "Bon usage : procédure de clôture non respectée",
    application: "COLORIS",
    status: "RESOLVED",
    priority: "P4",
    assignee: findUser("00000000-0000-0000-0000-000000000005"),
    category: "Bon usage",
    created_at: isoAgo(60),
    updated_at: isoAgo(10),
    resolved_at: isoAgo(10),
    resolution_notes: "Rappel de procédure envoyé à l'équipe concernée.",
    description: "La procédure de clôture mensuelle n'a pas été suivie correctement par l'équipe partenaire.",
  }),
  makeTicket({
    title: "Manque d'information sur un dossier VIO",
    application: "VIO",
    status: "OPEN",
    priority: "P3",
    assignee: findUser("00000000-0000-0000-0000-000000000002"),
    category: "Manque d'information",
    vio_app: "VIGIE",
    created_at: isoAgo(11),
    updated_at: isoAgo(11),
    description: "Le dossier ne contient pas les pièces nécessaires à son traitement, en attente de complément.",
  }),
  makeTicket({
    title: "Transfert vers l'équipe Habilitation",
    application: "VIO",
    status: "TRANSFERRED",
    priority: "P4",
    assignee: findUser("00000000-0000-0000-0000-000000000002"),
    category: "Habilitation",
    transferred_to: "Habilitation",
    created_at: isoAgo(80),
    updated_at: isoAgo(55),
    description: "Demande de droits ne relevant pas du périmètre Support, transférée à l'équipe Habilitation.",
  }),
  makeTicket({
    title: "Anomalie clôturée sur le connecteur AERO",
    application: "AERO",
    status: "CLOSED",
    priority: "P2",
    assignee: findUser("00000000-0000-0000-0000-000000000003"),
    category: "Bug",
    created_at: isoAgo(90),
    updated_at: isoAgo(65),
    closed_at: isoAgo(65),
    description: "Connecteur AERO instable, correctif déployé et vérifié sur deux cycles complets.",
  }),
]

function getTicketById(id: string): TicketDetail | undefined {
  return mockTickets.find((t) => t.id === id)
}

export { mockUsers, mockTickets, currentUserId, getTicketById, findUser }
