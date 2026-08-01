"use client"

import { PageHeader, PageBody } from "@/components/app/page"
import { UsersTable } from "@/features/users/users-table"
import { useUsersAdmin } from "@/features/users/use-users-admin"

export default function UsersPage() {
  const { users, toggleActive, changeRole } = useUsersAdmin()
  const activeCount = users.filter((u) => u.active).length

  return (
    <>
      <PageHeader
        title="Utilisateurs"
        description={`${activeCount} actifs sur ${users.length} comptes`}
        breadcrumbs={[{ label: "Suivi Run", href: "/" }, { label: "Administration" }, { label: "Utilisateurs" }]}
      />
      <PageBody>
        <UsersTable
          users={users}
          onChangeRole={(userId, roleId) => {
            const user = users.find((u) => u.id === userId)
            if (user) changeRole(userId, roleId, user.role_ids)
          }}
          onToggleActive={(userId) => {
            const user = users.find((u) => u.id === userId)
            if (user) toggleActive(userId, user.active)
          }}
        />
      </PageBody>
    </>
  )
}
