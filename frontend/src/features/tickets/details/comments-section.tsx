"use client"

import { useState } from "react"
import { Check, Download, Paperclip, Pencil, Trash2, X } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
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
  onEditComment: (commentId: string, content: string) => void
  onDeleteComment: (commentId: string) => void
  onDeleteCommentAttachment: (commentId: string, attachmentId: string) => void
  attachmentError: string | null
}

function CommentsSection({
  ticket,
  isLoading,
  onAddComment,
  onEditComment,
  onDeleteComment,
  onDeleteCommentAttachment,
  attachmentError,
}: CommentsSectionProps) {
  const [draft, setDraft] = useState("")
  const [files, setFiles] = useState<File[]>([])
  const [editingCommentId, setEditingCommentId] = useState<string | null>(null)
  const [editDraft, setEditDraft] = useState("")
  const [deletingCommentId, setDeletingCommentId] = useState<string | null>(null)
  const {
    user: currentUser,
    hasPermission,
    canActOnApplication,
    isAttachmentUploader,
    isCommentAuthor,
  } = usePermissions()

  // Mirrors AttachmentAccessPolicy's "delete": the uploader's own attachment, and the permission
  // that performs the deletion. Only the first was checked, so a role without `attachment.delete`
  // was still offered a button whose request the backend refuses.
  function canDeleteAttachment(attachment: Parameters<typeof isAttachmentUploader>[0]) {
    return hasPermission("attachment.delete") && isAttachmentUploader(attachment)
  }
  // Mirrors CommentAccessPolicy's "update"/"delete" rules, which admit the author alone — no
  // breadth override, unlike reading. Paired with the permission that performs each, since
  // holding one of the two without the other is an ordinary state.
  function canEditComment(comment: Parameters<typeof isCommentAuthor>[0]) {
    return hasPermission("comment.update") && isCommentAuthor(comment)
  }
  function mayDeleteComment(comment: Parameters<typeof isCommentAuthor>[0]) {
    return hasPermission("comment.delete") && isCommentAuthor(comment)
  }
  // Mirrors CommentAccessPolicy's "create" rule: assigned to the ticket's application, or
  // holding the cross-application breadth permission.
  const canComment =
    hasPermission("comment.create") &&
    (canActOnApplication(ticket.application) || hasPermission("ticket.read_any_application"))
  // Newest first — the backend returns comments in creation order. Deleted ones are dropped:
  // deletion is soft, so the API keeps returning them with a `deleted_at`, and rendering those
  // would make a deletion look like it had not happened. Nothing filtered them before because
  // there was no way to delete a comment from the UI at all.
  const comments = [...ticket.comments]
    .filter((c) => c.deleted_at === null)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

  function beginEdit(commentId: string, content: string) {
    setEditingCommentId(commentId)
    setEditDraft(content)
  }

  function submitEdit(commentId: string) {
    const content = editDraft.trim()
    if (content) onEditComment(commentId, content)
    setEditingCommentId(null)
  }

  function handleSubmit() {
    if (!draft.trim()) return
    onAddComment(draft.trim(), files)
    setDraft("")
    setFiles([])
  }

  return (
    <SectionCard title="Commentaires" description="Échanges autour de ce ticket">
      <div className="space-y-4">
        {attachmentError && <p className="text-sm text-destructive">{attachmentError}</p>}
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        ) : comments.length === 0 ? (
          <p className="text-sm text-muted-foreground">Aucun commentaire pour le moment.</p>
        ) : (
          <ul className="space-y-4">
            {comments.map((c) => {
              const activeAttachments = c.attachments.filter((a) => a.deleted_at === null)
              return (
                <li key={c.id} className="flex gap-3">
                  <Avatar size="sm">
                    <AvatarImage src={c.author?.avatar_url ?? undefined} alt={c.author?.display_name ?? ""} />
                    <AvatarFallback>{initials(c.author?.display_name ?? "?")}</AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1 rounded-lg bg-muted/50 px-3 py-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium">
                        {c.author?.display_name ?? "Utilisateur inconnu"}
                      </span>
                      <span className="flex shrink-0 items-center gap-1">
                        <span className="text-xs text-muted-foreground">
                          {dateTimeFormatter.format(new Date(c.created_at))}
                          {c.edited_at !== null && " · modifié"}
                        </span>
                        {editingCommentId !== c.id && canEditComment(c) && (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-6"
                            aria-label="Modifier le commentaire"
                            onClick={() => beginEdit(c.id, c.content)}
                          >
                            <Pencil className="size-3.5" />
                          </Button>
                        )}
                        {editingCommentId !== c.id && mayDeleteComment(c) && (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-6 text-destructive hover:text-destructive"
                            aria-label="Supprimer le commentaire"
                            onClick={() => setDeletingCommentId(c.id)}
                          >
                            <Trash2 className="size-3.5" />
                          </Button>
                        )}
                      </span>
                    </div>
                    {editingCommentId === c.id ? (
                      <div className="mt-2 space-y-2">
                        <Textarea
                          value={editDraft}
                          onChange={(e) => setEditDraft(e.target.value)}
                          rows={3}
                          aria-label="Modifier le commentaire"
                        />
                        <div className="flex justify-end gap-2">
                          <Button variant="ghost" size="sm" onClick={() => setEditingCommentId(null)}>
                            Annuler
                          </Button>
                          <Button size="sm" disabled={!editDraft.trim()} onClick={() => submitEdit(c.id)}>
                            <Check className="size-3.5" /> Enregistrer
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <p className="mt-1 text-sm whitespace-pre-wrap">{c.content}</p>
                    )}
                    {activeAttachments.length > 0 && (
                      <ul className="mt-2 space-y-1">
                        {activeAttachments.map((a) => (
                          <li key={a.id} className="flex items-center justify-between gap-2 text-xs">
                            <span className="flex min-w-0 items-center gap-1.5 text-muted-foreground">
                              <Paperclip className="size-3.5 shrink-0" />
                              <span className="truncate">{a.filename}</span>
                            </span>
                            <span className="flex shrink-0 items-center gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="size-6"
                                onClick={() => handleDownload(a)}
                              >
                                <Download className="size-3.5" />
                              </Button>
                              {canDeleteAttachment(a) && (
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
              )
            })}
          </ul>
        )}

        {canComment && (
          <div className="flex gap-3 border-t border-border pt-4">
            <Avatar size="sm">
              <AvatarImage src={currentUser?.avatarUrl ?? undefined} alt={currentUser?.displayName ?? ""} />
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
                  const selected = Array.from(e.target.files ?? [])
                  e.target.value = ""
                  if (selected.length > 0) setFiles((prev) => [...prev, ...selected])
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
      <AlertDialog
        open={deletingCommentId !== null}
        onOpenChange={(open) => !open && setDeletingCommentId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Supprimer ce commentaire ?</AlertDialogTitle>
            <AlertDialogDescription>
              Le commentaire ne sera plus visible dans le fil de discussion de ce ticket. Ses pièces
              jointes restent conservées.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deletingCommentId) onDeleteComment(deletingCommentId)
                setDeletingCommentId(null)
              }}
            >
              Supprimer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </SectionCard>
  )
}

export { CommentsSection }
