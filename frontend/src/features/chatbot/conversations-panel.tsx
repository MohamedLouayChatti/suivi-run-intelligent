import { History } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { mockConversations } from "@/features/chatbot/mock-data"
import { cn } from "@/lib/utils"

function ConversationsPanel() {
  return (
    <SectionCard
      title={
        <span className="flex items-center gap-2">
          <History className="size-4 text-muted-foreground" strokeWidth={1.75} />
          Conversations
        </span>
      }
      bodyClassName="p-0"
    >
      <ul className="divide-y divide-border">
        {mockConversations.map((conversation, i) => (
          <li key={conversation.id}>
            <button
              className={cn(
                "w-full px-5 py-3 text-left transition-colors hover:bg-surface",
                i === 0 && "bg-primary/5"
              )}
            >
              <p className="truncate text-sm font-medium">{conversation.title}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{conversation.relativeTime}</p>
            </button>
          </li>
        ))}
      </ul>
    </SectionCard>
  )
}

export { ConversationsPanel }
