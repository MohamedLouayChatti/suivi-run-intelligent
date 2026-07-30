"use client"

import { useState } from "react"

import { SectionCard } from "@/components/app/page"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { currentUserId, findUser } from "@/features/tickets/mock-data"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]
type Comment = components["schemas"]["CommentResponse"]

const dateTimeFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
})

function initials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase()
}

interface CommentsSectionProps {
  ticket: TicketDetail
  isLoading: boolean
  onAddComment: (comment: Comment) => void
}

function CommentsSection({ ticket, isLoading, onAddComment }: CommentsSectionProps) {
  const [draft, setDraft] = useState("")
  const currentUser = findUser(currentUserId)

  function handleSubmit() {
    if (!draft.trim()) return
    onAddComment({
      id: crypto.randomUUID(),
      author: currentUser,
      content: draft.trim(),
      created_at: new Date().toISOString(),
      attachments: [],
      edited_at: null,
      deleted_at: null,
    })
    setDraft("")
  }

  return (
    <SectionCard title="Commentaires" description="Échanges autour de ce ticket">
      <div className="space-y-4">
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        ) : ticket.comments.length === 0 ? (
          <p className="text-sm text-muted-foreground">Aucun commentaire pour le moment.</p>
        ) : (
          <ul className="space-y-4">
            {ticket.comments.map((c) => (
              <li key={c.id} className="flex gap-3">
                <Avatar size="sm">
                  <AvatarFallback>{initials(c.author?.display_name ?? "?")}</AvatarFallback>
                </Avatar>
                <div className="min-w-0 flex-1 rounded-lg bg-muted/50 px-3 py-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium">
                      {c.author?.display_name ?? "Utilisateur inconnu"}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {dateTimeFormatter.format(new Date(c.created_at))}
                    </span>
                  </div>
                  <p className="mt-1 text-sm whitespace-pre-wrap">{c.content}</p>
                </div>
              </li>
            ))}
          </ul>
        )}

        <div className="flex gap-3 border-t border-border pt-4">
          <Avatar size="sm">
            <AvatarFallback>{initials(currentUser.display_name)}</AvatarFallback>
          </Avatar>
          <div className="flex-1 space-y-2">
            <Textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Ajouter un commentaire…"
              rows={2}
            />
            <div className="flex justify-end">
              <Button size="sm" onClick={handleSubmit} disabled={!draft.trim()}>
                Publier
              </Button>
            </div>
          </div>
        </div>
      </div>
    </SectionCard>
  )
}

export { CommentsSection }
