import Link from "next/link"
import { MessageSquareText } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { Button } from "@/components/ui/button"

interface ContinueConversationsProps {
  conversations: { id: string; title: string; relativeTime: string }[]
}

function ContinueConversations({ conversations }: ContinueConversationsProps) {
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
      <ul className="divide-y divide-border">
        {conversations.map((c) => (
          <li key={c.id}>
            <Link
              href="/chatbot"
              className="flex items-center gap-3 px-5 py-3 transition-colors hover:bg-surface"
            >
              <MessageSquareText className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
              <span className="min-w-0 flex-1 truncate text-sm">{c.title}</span>
              <span className="shrink-0 text-xs text-muted-foreground">{c.relativeTime}</span>
            </Link>
          </li>
        ))}
      </ul>
    </SectionCard>
  )
}

export { ContinueConversations }
