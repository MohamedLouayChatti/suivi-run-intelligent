import { Download } from "lucide-react"

import { PageHeader } from "@/components/app/page"
import { Button } from "@/components/ui/button"

interface HistoryHeaderProps {
  onExport: () => void
  isExporting: boolean
}

function HistoryHeader({ onExport, isExporting }: HistoryHeaderProps) {
  return (
    <PageHeader
      title="Historique des tickets"
      description="Parcourez les incidents clôturés et les interventions passées."
      actions={
        <Button variant="outline" size="sm" onClick={onExport} disabled={isExporting}>
          <Download className="size-4" /> {isExporting ? "Export en cours…" : "Exporter"}
        </Button>
      }
    />
  )
}

export { HistoryHeader }
