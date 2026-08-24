"use client"

import { PageBody, PageHeader } from "@/components/app/page"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BatchImportPanel } from "@/features/knowledge-base/batch-import-panel"
import { RecalculationPanel } from "@/features/knowledge-base/recalculation-panel"
import { RequireRouteAccess, usePermissions } from "@/lib/auth"

/**
 * Administration of the Knowledge Base: loading historical tickets in bulk, and governing the
 * pass that keeps the similarity graph fresh.
 *
 * The three backend permissions are independent, so the gate is "any of them" and each tab then
 * asks for the one its own endpoints require — a caller granted only `knowledge_base.batch_import`
 * reaches the page and sees the import tab alone. Permission-aware UX only: every endpoint behind
 * these tabs enforces its own permission again.
 */
export default function KnowledgeBasePage() {
  const { hasPermission } = usePermissions()

  const canImport = hasPermission("knowledge_base.batch_import")
  const canManageRecalculation = hasPermission("knowledge_base.manage_recalculation")
  const canReadRecalculation = hasPermission("knowledge_base.read_recalculation") || canManageRecalculation

  return (
    <RequireRouteAccess href="/admin/knowledge-base">
      <PageHeader
        title="Base de connaissances"
        description="Import de tickets historiques et entretien du graphe de similarité"
        breadcrumbs={[
          { label: "Suivi Run", href: "/" },
          { label: "Administration" },
          { label: "Base de connaissances" },
        ]}
      />
      <PageBody>
        <Tabs defaultValue={canImport ? "import" : "recalculation"}>
          <TabsList>
            {canImport && <TabsTrigger value="import">Import de tickets</TabsTrigger>}
            {canReadRecalculation && (
              <TabsTrigger value="recalculation">Planification du recalcul</TabsTrigger>
            )}
          </TabsList>

          {canImport && (
            <TabsContent value="import" className="mt-6">
              <BatchImportPanel />
            </TabsContent>
          )}
          {canReadRecalculation && (
            <TabsContent value="recalculation" className="mt-6">
              <RecalculationPanel canManage={canManageRecalculation} />
            </TabsContent>
          )}
        </Tabs>
      </PageBody>
    </RequireRouteAccess>
  )
}
