"use client"

import { useState } from "react"
import { Download, Paperclip, X } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { usePermissions } from "@/lib/auth"
import { downloadAttachment } from "@/services/api/tickets"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]
type CommentAttachment = TicketDetail["comments"][number]["attachments"][number]

async function handleDownload(attachment: CommentAttachment) {
  const blob = await downloadAttachment(attachment.id)
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = attachment.filename
  link.click()
  URL.revokeObjectURL(url)
}

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
  onAddComment: (content: string, files: File[]) => void
  onDeleteCommentAttachment: (commentId: string, attachmentId: string) => void
}

function CommentsSection({ ticket, isLoading, onAddComment, onDeleteCommentAttachment }: CommentsSectionProps) {
  const [draft, setDraft] = useState("")
  const [files, setFiles] = useState<File[]>([])
  const { user: currentUser, hasPermission, isAdmin, canActOnApplication, isAttachmentUploader } = usePermissions()
  const canComment = hasPermission("comment.create") && (canActOnApplication(ticket.application) || isAdmin)

  function handleSubmit() {
    if (!draft.trim()) return
    onAddComment(draft.trim(), files)
    setDraft("")
    setFiles([])
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
                  {c.attachments.length > 0 && (
                    <ul className="mt-2 space-y-1">
                      {c.attachments.map((a) => (
                        <li key={a.id} className="flex items-center justify-between gap-2 text-xs">
                          <span className="flex min-w-0 items-center gap-1.5 text-muted-foreground">
                            <Paperclip className="size-3.5 shrink-0" />
                            <span className="truncate">{a.filename}</span>
                          </span>
                          <span className="flex shrink-0 items-center gap-1">
                            <Button variant="ghost" size="icon" className="size-6" onClick={() => handleDownload(a)}>
                              <Download className="size-3.5" />
                            </Button>
                            {isAttachmentUploader(a) && (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="size-6"
                                onClick={() => onDeleteCommentAttachment(c.id, a.id)}
                              >
                                <X className="size-3.5" />
                              </Button>
                            )}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}

        {canComment && (
          <div className="flex gap-3 border-t border-border pt-4">
            <Avatar size="sm">
              <AvatarFallback>{initials(currentUser?.displayName ?? "")}</AvatarFallback>
            </Avatar>
            <div className="flex-1 space-y-2">
              <Textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Ajouter un commentaire…"
                rows={2}
              />
              <Input
                type="file"
                multiple
                onChange={(e) => {
                  if (e.target.files) setFiles((prev) => [...prev, ...Array.from(e.target.files ?? [])])
                  e.target.value = ""
                }}
              />
              {files.length > 0 && (
                <ul className="space-y-1">
                  {files.map((file, index) => (
                    <li key={`${file.name}-${index}`} className="flex items-center justify-between gap-2 text-xs">
                      <span className="flex min-w-0 items-center gap-1.5 text-muted-foreground">
                        <Paperclip className="size-3.5 shrink-0" />
                        <span className="truncate">{file.name}</span>
                      </span>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="size-6"
                        onClick={() => setFiles((prev) => prev.filter((_, i) => i !== index))}
                      >
                        <X className="size-3.5" />
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
              <div className="flex justify-end">
                <Button size="sm" onClick={handleSubmit} disabled={!draft.trim()}>
                  Publier
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </SectionCard>
  )
}

export { CommentsSection }
