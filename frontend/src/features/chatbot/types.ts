import type { components } from "@/types/api"

type MessageRole = components["schemas"]["MessageRole"]

/**
 * One chat bubble — mirrors the backend's MessageResponse (id/role/content), plus the optimistic
 * bubbles the UI synthesizes locally before the server round trip completes: the user's just-sent
 * message, and the empty assistant placeholder that fills in as message_delta events arrive.
 */
interface ChatMessage {
  id: string
  role: MessageRole
  content: string
}

const suggestedPrompts: string[] = [
  "Résumer les incidents Sev2 ouverts des 30 derniers jours",
  "Quel runbook couvre le renouvellement des certificats TLS ?",
  "Afficher les tickets similaires à SR-4821",
  "Expliquer la politique SLA pour les tickets de priorité critique",
]

export { suggestedPrompts }
export type { ChatMessage, MessageRole }
