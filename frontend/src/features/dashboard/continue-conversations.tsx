import Link from "next/link"
import { MessageSquareText } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { Button } from "@/components/ui/button"
import { conversationHref } from "@/features/chatbot/conversation-link"
import { formatRelativeTime } from "@/lib/format/relative-time"
import type { ConversationSummaryResponse } from "@/services/api/chatbot"

interface ContinueConversationsProps {
  conversations: ConversationSummaryResponse[]
  isLoading: boolean
}

function ContinueConversations({ conversations, isLoading }: ContinueConversationsProps) {
  return (
    <SectionCard
      title="Reprendre une conversation"
      action={
        <Button variant="ghost" size="sm" asChild>
          <Link href="/chatbot">Ouvrir</Link>
        </Button>
      }
      bodyClassName="p-0"
    >
      {isLoading ? (
        <p className="px-5 py-4 text-sm text-muted-foreground">Chargement…</p>
      ) : conversations.length === 0 ? (
        <p className="px-5 py-4 text-sm text-muted-foreground">Aucune conversation pour le moment.</p>
      ) : (
        <ul className="divide-y divide-border">
          {conversations.map((conversation) => (
            <li key={conversation.id}>
              {/* Each item resumes its own conversation rather than opening a blank assistant —
                  which is the whole of what this card offers over the sidebar's Chatbot link. */}
              <Link
                href={conversationHref(conversation.id)}
                className="flex items-center gap-3 px-5 py-3 transition-colors hover:bg-surface"
              >
                <MessageSquareText className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
                <span className="min-w-0 flex-1 truncate text-sm">
                  {conversation.title ?? "Nouvelle conversation"}
                </span>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {formatRelativeTime(conversation.updated_at)}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  )
}

export { ContinueConversations }
