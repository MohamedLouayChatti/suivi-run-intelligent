"use client"

import { useState } from "react"

import { PageHeader, PageBody } from "@/components/app/page"
import { UsersTable } from "@/features/users/users-table"
import { mockUsers, type MockUser } from "@/features/users/mock-data"

export default function UsersPage() {
  const [users, setUsers] = useState<MockUser[]>(mockUsers)
  const activeCount = users.filter((u) => u.active).length

  function handleChangeRole(userId: string, roleId: string) {
    setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, role_ids: [roleId] } : u)))
  }

  function handleToggleActive(userId: string) {
    setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, active: !u.active } : u)))
  }

  return (
    <>
      <PageHeader
        title="Utilisateurs"
        description={`${activeCount} actifs sur ${users.length} comptes`}
        breadcrumbs={[{ label: "Suivi Run", href: "/" }, { label: "Administration" }, { label: "Utilisateurs" }]}
      />
      <PageBody>
        <UsersTable users={users} onChangeRole={handleChangeRole} onToggleActive={handleToggleActive} />
      </PageBody>
    </>
  )
}
