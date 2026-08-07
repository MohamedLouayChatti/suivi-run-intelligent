"use client"

import { useState } from "react"
import { Download } from "lucide-react"

import { PageHeader, PageBody } from "@/components/app/page"
import { Button } from "@/components/ui/button"
import { AuditLogTable } from "@/features/audit/audit-log-table"
import { AuditRefreshButton } from "@/features/audit/audit-refresh-button"
import { RequirePermission } from "@/lib/auth"
import { exportAuditEntries } from "@/services/api/audit"

export default function AuditPage() {
  const [moduleFilter, setModuleFilter] = useState<"all" | string>("all")
  const [isExporting, setIsExporting] = useState(false)

  async function handleExport() {
    setIsExporting(true)
    try {
      const blob = await exportAuditEntries({ module: moduleFilter })
      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = "journal_audit.csv"
      link.click()
      URL.revokeObjectURL(url)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <RequirePermission admin permission="audit.read">
      <PageHeader
        title="Audit"
        description="Registre immuable des événements métier et administratifs"
        breadcrumbs={[{ label: "Suivi Run", href: "/" }, { label: "Administration" }, { label: "Audit" }]}
        actions={
          <>
            <AuditRefreshButton />
            <Button variant="outline" size="sm" onClick={handleExport} disabled={isExporting}>
              <Download className="size-4" /> {isExporting ? "Export en cours…" : "Exporter le journal"}
            </Button>
          </>
        }
      />
      <PageBody>
        <AuditLogTable moduleFilter={moduleFilter} onModuleFilterChange={setModuleFilter} />
      </PageBody>
    </RequirePermission>
  )
}
