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
  "Recherche les tickets ouverts liés à une erreur API",
  "Quels incidents sont similaires au ticket à analyser ?",
  "Quel est mon bilan d'activité récent ?",
  "Quels sont les indicateurs de mon équipe ?",
]

export { suggestedPrompts }
export type { ChatMessage, MessageRole }
