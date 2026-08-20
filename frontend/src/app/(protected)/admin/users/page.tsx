"use client"

import { Suspense } from "react"
import { useSearchParams } from "next/navigation"

import { PageHeader, PageBody } from "@/components/app/page"
import { UsersTable } from "@/features/users/users-table"
import { useUsersAdmin } from "@/features/users/use-users-admin"
import { RequirePermission } from "@/lib/auth"

export default function UsersPage() {
  return (
    <Suspense fallback={null}>
      <UsersPageContent />
    </Suspense>
  )
}

function UsersPageContent() {
  const searchParams = useSearchParams()
  const highlightUserId = searchParams.get("highlight")
  const { users, toggleActive, changeRole, savePermissions } = useUsersAdmin()
  const activeCount = users.filter((u) => u.active).length

  return (
    <RequirePermission permissions={["user.read_all", "role.read_all", "permission.read"]}>
      <PageHeader
        title="Utilisateurs"
        description={`${activeCount} actifs sur ${users.length} comptes`}
        breadcrumbs={[{ label: "Suivi Run", href: "/" }, { label: "Administration" }, { label: "Utilisateurs" }]}
      />
      <PageBody>
        <UsersTable
          users={users}
          highlightUserId={highlightUserId}
          onChangeRole={changeRole}
          onToggleActive={(userId) => {
            const user = users.find((u) => u.id === userId)
            if (user) toggleActive(userId, user.active)
          }}
          onSavePermissions={savePermissions}
        />
      </PageBody>
    </RequirePermission>
  )
}
