import { Download } from "lucide-react"

import { PageHeader } from "@/components/app/page"
import { Button } from "@/components/ui/button"

function HistoryHeader() {
  return (
    <PageHeader
      title="Historique des tickets"
      description="Parcourez les incidents clôturés et les interventions passées."
      actions={
        <Button variant="outline" size="sm">
          <Download className="size-4" /> Exporter
        </Button>
      }
    />
  )
}

export { HistoryHeader }
