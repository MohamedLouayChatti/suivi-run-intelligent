import { Download } from "lucide-react"

import { PageHeader, PageBody } from "@/components/app/page"
import { Button } from "@/components/ui/button"
import { AuditLogTable } from "@/features/audit/audit-log-table"
import { RequirePermission } from "@/lib/auth"

export default function AuditPage() {
  return (
    <RequirePermission admin permission="audit.read">
      <PageHeader
        title="Audit"
        description="Registre immuable des événements métier et administratifs"
        breadcrumbs={[{ label: "Suivi Run", href: "/" }, { label: "Administration" }, { label: "Audit" }]}
        actions={
          <Button variant="outline" size="sm" disabled>
            <Download className="size-4" /> Exporter le journal
          </Button>
        }
      />
      <PageBody>
        <AuditLogTable />
      </PageBody>
    </RequirePermission>
  )
}
