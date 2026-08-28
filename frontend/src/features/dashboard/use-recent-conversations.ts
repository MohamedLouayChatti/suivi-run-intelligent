"use client"

import { useQuery } from "@tanstack/react-query"

import { usePermissions } from "@/lib/auth"
import { listConversations } from "@/services/api/chatbot"

// The dashboard card shows the three most recent; the Chatbot page's own panel is where the whole
// history lives, so asking for more here would only be paid for and thrown away.
const RECENT_CONVERSATIONS_LIMIT = 3

/**
 * The caller's most recent assistant conversations, for the Dashboard's "Reprendre une
 * conversation" card. Every seeded role holds `conversational_assistant.use`, but a direct revoke
 * can take it from one person — so the query is disabled rather than left to 403, the same rule
 * the admin list hooks follow.
 *
 * Shares no query key with the Chatbot page's own `listConversations` call: that one asks for a
 * different page size, and letting the two collide would have whichever mounted first decide how
 * much history the other sees.
 */
function useRecentConversations() {
  const { hasPermission } = usePermissions()
  const canUseAssistant = hasPermission("conversational_assistant.use")

  const query = useQuery({
    queryKey: ["chatbot", "conversations", "recent", RECENT_CONVERSATIONS_LIMIT],
    queryFn: () => listConversations(1, RECENT_CONVERSATIONS_LIMIT),
    enabled: canUseAssistant,
  })

  return {
    conversations: query.data?.items ?? [],
    isLoading: canUseAssistant && query.isPending,
    canUseAssistant,
  }
}

export { useRecentConversations }
