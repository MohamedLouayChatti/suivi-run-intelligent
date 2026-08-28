import type { components } from "@/types/api"

type MessageRole = components["schemas"]["MessageRole"]

/**
 * One chat bubble — mirrors the backend's MessageResponse (id/role/content), plus the optimistic
 * bubbles the UI synthesizes locally before the server round trip completes: the user's just-sent
 * message, and the empty assistant placeholder that fills in as message_delta events arrive.
 *
 * `failed` marks a run the assistant never answered. It is not a role of its own because it is not
 * something the assistant said: the backend stores no message for a failed run and returns it
 * separately, and the transcript renders it in place so the question it followed does not appear
 * to have been ignored.
 */
interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  failed?: boolean
}

export type { ChatMessage, MessageRole }
