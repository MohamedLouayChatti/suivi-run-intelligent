import { PageHeader, PageBody } from "@/components/app/page"
import { RolesPanel } from "@/features/roles/roles-panel"

export default function RolesPage() {
  return (
    <>
      <PageHeader
        title="Rôles"
        description="Ensembles de permissions appliqués sur la plateforme"
        breadcrumbs={[{ label: "Suivi Run", href: "/" }, { label: "Administration" }, { label: "Rôles" }]}
      />
      <PageBody>
        <RolesPanel />
      </PageBody>
    </>
  )
}
