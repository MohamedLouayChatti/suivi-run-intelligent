import { useRef, useState } from "react"
import { Download, Paperclip, Plus, X } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { Button, buttonVariants } from "@/components/ui/button"
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
type Attachment = TicketDetail["attachments"][number]

const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
})

async function handleDownload(attachment: Attachment) {
  const blob = await downloadAttachment(attachment.id)
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = attachment.filename
  link.click()
  URL.revokeObjectURL(url)
}

interface AttachmentsSectionProps {
  ticket: TicketDetail
  onUploadAttachment: (file: File) => void
  onDeleteAttachment: (attachmentId: string) => void
  error: string | null
}

function AttachmentsSection({ ticket, onUploadAttachment, onDeleteAttachment, error }: AttachmentsSectionProps) {
  const { hasPermission, isTicketAssignee, isAttachmentUploader } = usePermissions()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [pendingFiles, setPendingFiles] = useState<File[] | null>(null)
  const [pendingDelete, setPendingDelete] = useState<Attachment | null>(null)
  // Mirrors AttachmentAccessPolicy's "create" rule (app/modules/ticket_management/application/
  // security/attachment_access_policy.py): only the ticket assignee may attach files directly to
  // the ticket — no admin override there, so none here either.
  const canAttach = hasPermission("attachment.create") && isTicketAssignee(ticket)
  // Soft-deleted attachments (deleted_at set) are kept in the response for audit purposes but must
  // never appear as if they were still live — the UI should mirror the deletion, not the raw list.
  const activeAttachments = ticket.attachments.filter((a) => a.deleted_at === null)

  function confirmUpload() {
    pendingFiles?.forEach(onUploadAttachment)
    setPendingFiles(null)
  }

  function confirmDelete() {
    if (pendingDelete) onDeleteAttachment(pendingDelete.id)
    setPendingDelete(null)
  }

  return (
    <SectionCard
      title="Pièces jointes"
      bodyClassName="p-0"
      action={
        canAttach && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => {
                const selected = Array.from(e.target.files ?? [])
                e.target.value = ""
                if (selected.length > 0) setPendingFiles(selected)
              }}
            />
            <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()}>
              <Plus className="size-4" /> Attacher
            </Button>
          </>
        )
      }
    >
      {error && <p className="border-b border-border px-5 py-3 text-sm text-destructive">{error}</p>}
      {activeAttachments.length === 0 ? (
        <p className="px-5 py-6 text-sm text-muted-foreground">Aucune pièce jointe.</p>
      ) : (
        <ul className="divide-y divide-border">
          {activeAttachments.map((a) => (
            <li key={a.id} className="flex items-center justify-between gap-4 px-5 py-3">
              <div className="flex min-w-0 items-center gap-2">
                <Paperclip className="size-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{a.filename}</p>
                  <p className="truncate text-xs text-muted-foreground">
                    Ajouté par {a.uploader?.display_name ?? "Utilisateur inconnu"} ·{" "}
                    {dateFormatter.format(new Date(a.uploaded_at))}
                  </p>
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => handleDownload(a)}>
                  <Download className="size-4" /> Télécharger
                </Button>
                {isAttachmentUploader(a) && (
                  <Button variant="ghost" size="icon" onClick={() => setPendingDelete(a)}>
                    <X className="size-4" />
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <AlertDialog open={pendingFiles !== null} onOpenChange={(open) => !open && setPendingFiles(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Êtes-vous sûr ?</AlertDialogTitle>
            <AlertDialogDescription>
              {pendingFiles?.length === 1
                ? `Attacher le fichier « ${pendingFiles[0].name} » à ce ticket ?`
                : `Attacher ces ${pendingFiles?.length ?? 0} fichiers à ce ticket ? ${pendingFiles
                    ?.map((f) => f.name)
                    .join(", ")}`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction onClick={confirmUpload}>Confirmer</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={pendingDelete !== null} onOpenChange={(open) => !open && setPendingDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Êtes-vous sûr ?</AlertDialogTitle>
            <AlertDialogDescription>
              Supprimer la pièce jointe « {pendingDelete?.filename} » ? Cette action est irréversible.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction className={buttonVariants({ variant: "destructive" })} onClick={confirmDelete}>
              Confirmer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </SectionCard>
  )
}

export { AttachmentsSection }
