import { Plus } from "lucide-react"

import { PageHeader } from "@/components/app/page"
import { Button } from "@/components/ui/button"

interface TicketsHeaderProps {
  canCreate: boolean
  onCreateClick: () => void
}

function TicketsHeader({ canCreate, onCreateClick }: TicketsHeaderProps) {
  return (
    <PageHeader
      title="Tickets"
      description="Gérez les incidents actifs et les affectations."
      actions={
        canCreate && (
          <Button size="sm" onClick={onCreateClick}>
            <Plus className="size-4" /> Créer un ticket
          </Button>
        )
      }
    />
  )
}

export { TicketsHeader }
