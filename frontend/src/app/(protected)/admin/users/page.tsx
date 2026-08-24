"use client"

import { Suspense } from "react"
import { useSearchParams } from "next/navigation"

import { PageHeader, PageBody } from "@/components/app/page"
import { UsersTable } from "@/features/users/users-table"
import { useUsersAdmin } from "@/features/users/use-users-admin"
import { RequireRouteAccess } from "@/lib/auth"

export default function UsersPage() {
  return (
    <Suspense fallback={null}>
      <UsersPageContent />
    </Suspense>
  )
}

/**
 * Administration of user accounts. Gated by the route's own declared requirement — any one of
 * the capabilities the page offers — rather than by a conjunction of every permission its
 * queries touch. That conjunction only ever admitted people holding all three of
 * `user.read_all`, `role.read_all` and `permission.read`, which is a role check written in
 * permission vocabulary: granting somebody `user.activate` gave them a sidebar entry leading
 * to an Access Denied screen.
 *
 * What each caller sees is decided below this point, by the table and the details sheet, from
 * the permission each column and action actually needs.
 */
function UsersPageContent() {
  const searchParams = useSearchParams()
  const highlightUserId = searchParams.get("highlight")
  const { users, capabilities, toggleActive, changeRole, saveOrganizationalIdentity, savePermissions } =
    useUsersAdmin()
  const activeCount = users.filter((u) => u.active).length

  return (
    <RequireRouteAccess href="/admin/users">
      <PageHeader
        title="Utilisateurs"
        description={`${activeCount} actifs sur ${users.length} comptes`}
        breadcrumbs={[{ label: "Suivi Run", href: "/" }, { label: "Administration" }, { label: "Utilisateurs" }]}
      />
      <PageBody>
        <UsersTable
          users={users}
          capabilities={capabilities}
          highlightUserId={highlightUserId}
          onChangeRole={changeRole}
          onSaveOrganizationalIdentity={saveOrganizationalIdentity}
          onToggleActive={(userId) => {
            const user = users.find((u) => u.id === userId)
            if (user) toggleActive(userId, user.active)
          }}
          onSavePermissions={savePermissions}
        />
      </PageBody>
    </RequireRouteAccess>
  )
}
