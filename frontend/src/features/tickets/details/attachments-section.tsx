import { Download, Paperclip } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { Button } from "@/components/ui/button"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]

const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
})

function AttachmentsSection({ ticket }: { ticket: TicketDetail }) {
  return (
    <SectionCard title="Pièces jointes" bodyClassName="p-0">
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
              <Button variant="outline" size="sm" asChild>
                <a href={a.storage_path} download>
                  <Download className="size-4" /> Télécharger
                </a>
              </Button>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  )
}

export { AttachmentsSection }
