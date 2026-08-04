import { useRef } from "react"
import { Download, Paperclip, Plus, X } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { Button } from "@/components/ui/button"
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
}

function AttachmentsSection({ ticket, onUploadAttachment, onDeleteAttachment }: AttachmentsSectionProps) {
  const { hasPermission, isTicketAssignee, isAttachmentUploader } = usePermissions()
  const fileInputRef = useRef<HTMLInputElement>(null)
  // Mirrors AttachmentAccessPolicy's "create" rule (app/modules/ticket_management/application/
  // security/attachment_access_policy.py): only the ticket assignee may attach files directly to
  // the ticket — no admin override there, so none here either.
  const canAttach = hasPermission("attachment.create") && isTicketAssignee(ticket)

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
                Array.from(e.target.files ?? []).forEach(onUploadAttachment)
                e.target.value = ""
              }}
            />
            <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()}>
              <Plus className="size-4" /> Attacher
            </Button>
          </>
        )
      }
    >
      {ticket.attachments.length === 0 ? (
        <p className="px-5 py-6 text-sm text-muted-foreground">Aucune pièce jointe.</p>
      ) : (
        <ul className="divide-y divide-border">
          {ticket.attachments.map((a) => (
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
                  <Button variant="ghost" size="icon" onClick={() => onDeleteAttachment(a.id)}>
                    <X className="size-4" />
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  )
}

export { AttachmentsSection }
