"use client"

import { useState } from "react"
import { Check, Minus } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { cn } from "@/lib/utils"
import { useRolesList } from "@/hooks/use-roles-list"
import { usePermissionsList } from "@/hooks/use-permissions-list"
import { useUsersList } from "@/hooks/use-users-list"

// Static presentational copy — RoleResponse only carries id/name/permission_ids, and role
// management (create/edit) isn't part of this app; roles are seeded, not authored by admins.
const roleDescriptions: Record<string, string> = {
  Admin: "Accès complet à la plateforme, y compris l'administration des utilisateurs, des rôles et des permissions.",
  "Support Engineer": "Prend en charge la résolution des tickets au quotidien et la contribution aux connaissances.",
  "Support Engineer Supervisor": "Supervise les files d'attente, réassigne le travail et consulte les analyses opérationnelles.",
}

function RolesPanel() {
  const { roles } = useRolesList()
  const { permissions } = usePermissionsList()
  const { users } = useUsersList()
  const [activeRoleId, setActiveRoleId] = useState<string | null>(null)

  const roleId = activeRoleId ?? roles[0]?.id
  const role = roles.find((r) => r.id === roleId)
  if (!role) return null

  const memberCounts = Object.fromEntries(
    roles.map((r) => [r.id, users.filter((u) => u.role_ids.includes(r.id)).length])
  )

  const stats: [string, string][] = [
    ["Membres", String(memberCounts[role.id] ?? 0)],
    ["Permissions", `${role.permission_ids.length} sur ${permissions.length}`],
  ]

  return (
    <div className="grid gap-6 xl:grid-cols-[20rem_minmax(0,1fr)]">
      <SectionCard title="Rôles" bodyClassName="p-0">
        <ul className="divide-y divide-border">
          {roles.map((r) => (
            <li key={r.id}>
              <button
                onClick={() => setActiveRoleId(r.id)}
                className={cn(
                  "w-full px-5 py-4 text-left transition-colors hover:bg-surface",
                  role.id === r.id && "bg-primary/5"
                )}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className={cn("text-sm font-medium", role.id === r.id && "text-primary")}>
                    {r.name}
                  </span>
                  <span className="text-xs tabular text-muted-foreground">
                    {memberCounts[r.id] ?? 0} membres
                  </span>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  {roleDescriptions[r.name] ?? ""}
                </p>
              </button>
            </li>
          ))}
        </ul>
      </SectionCard>

      <div className="space-y-6">
        <SectionCard title={role.name} description={roleDescriptions[role.name] ?? ""}>
          <div className="grid gap-4 sm:grid-cols-2">
            {stats.map(([label, value]) => (
              <div key={label} className="rounded-md border border-border bg-surface p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
                <p className="mt-1 text-lg font-semibold tabular">{value}</p>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Permissions" description="Capacités accordées pour ce rôle" bodyClassName="p-0">
          <ul className="divide-y divide-border">
            {permissions.map((p) => {
              const granted = role.permission_ids.includes(p.id)
              return (
                <li key={p.id} className="flex items-center gap-3 px-5 py-3">
                  <span
                    className={cn(
                      "grid size-5 shrink-0 place-items-center rounded border",
                      granted ? "border-primary/30 bg-primary/10 text-primary" : "border-border text-muted-foreground"
                    )}
                  >
                    {granted ? <Check className="size-3" /> : <Minus className="size-3" />}
                  </span>
                  <span className="font-mono text-xs">{p.name}</span>
                  <span className="ml-auto text-xs text-muted-foreground">
                    {granted ? "Accordée" : "Non accordée"}
                  </span>
                </li>
              )
            })}
          </ul>
        </SectionCard>
      </div>
    </div>
  )
}

export { RolesPanel }
