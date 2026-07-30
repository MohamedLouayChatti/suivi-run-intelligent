import { Download, Plus } from "lucide-react"

import { PageHeader } from "@/components/app/page"
import { Button } from "@/components/ui/button"

interface TicketsHeaderProps {
  onCreateClick: () => void
}

function TicketsHeader({ onCreateClick }: TicketsHeaderProps) {
  return (
    <PageHeader
      title="Tickets"
      description="Gérez les incidents actifs et les affectations."
      actions={
        <>
          <Button variant="outline" size="sm">
            <Download className="size-4" /> Exporter
          </Button>
          <Button size="sm" onClick={onCreateClick}>
            <Plus className="size-4" /> Créer un ticket
          </Button>
        </>
      }
    />
  )
}

export { TicketsHeader }
