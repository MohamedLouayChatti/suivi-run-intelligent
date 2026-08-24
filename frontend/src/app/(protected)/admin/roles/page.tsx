import { PageHeader, PageBody } from "@/components/app/page"
import { RolesPanel } from "@/features/roles/roles-panel"
import { RequireRouteAccess } from "@/lib/auth"

export default function RolesPage() {
  return (
    <RequireRouteAccess href="/admin/roles">
      <PageHeader
        title="Rôles"
        description="Ensembles de permissions appliqués sur la plateforme"
        breadcrumbs={[{ label: "Suivi Run", href: "/" }, { label: "Administration" }, { label: "Rôles" }]}
      />
      <PageBody>
        <RolesPanel />
      </PageBody>
    </RequireRouteAccess>
  )
}
