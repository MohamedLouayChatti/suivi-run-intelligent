"use client"

import { History } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { formatRelativeTime } from "@/lib/format/relative-time"
import { cn } from "@/lib/utils"
import type { ConversationSummaryResponse } from "@/services/api/chatbot"

interface ConversationsPanelProps {
  conversations: ConversationSummaryResponse[]
  activeConversationId: string | null
  isLoading: boolean
  onSelect: (conversationId: string) => void
}

function ConversationsPanel({ conversations, activeConversationId, isLoading, onSelect }: ConversationsPanelProps) {
  return (
    // Scrolls inside itself for the same reason the chat pane does: this page is a
    // fixed-height workspace, and a long history must not be allowed to stretch it.
    <SectionCard
      title={
        <span className="flex items-center gap-2">
          <History className="size-4 text-muted-foreground" strokeWidth={1.75} />
          Conversations
        </span>
      }
      className="flex min-h-0 flex-1 flex-col"
      bodyClassName="min-h-0 flex-1 overflow-y-auto p-0"
    >
      {isLoading ? (
        <p className="px-5 py-4 text-sm text-muted-foreground">Chargement…</p>
      ) : conversations.length === 0 ? (
        <p className="px-5 py-4 text-sm text-muted-foreground">Aucune conversation pour le moment.</p>
      ) : (
        <ul className="divide-y divide-border">
          {conversations.map((conversation) => (
            <li key={conversation.id}>
              <button
                onClick={() => onSelect(conversation.id)}
                className={cn(
                  "w-full px-5 py-3 text-left transition-colors hover:bg-surface",
                  conversation.id === activeConversationId && "bg-primary/5",
                )}
              >
                <p className="truncate text-sm font-medium">{conversation.title ?? "Nouvelle conversation"}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{formatRelativeTime(conversation.updated_at)}</p>
              </button>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  )
}

export { ConversationsPanel }
