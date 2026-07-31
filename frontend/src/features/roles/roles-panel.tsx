"use client"

import { useState } from "react"
import { Check, Minus } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { cn } from "@/lib/utils"
import { mockPermissions, mockRoles } from "@/features/roles/mock-data"
import { mockUsers } from "@/features/users/mock-data"

function RolesPanel() {
  const [activeRoleId, setActiveRoleId] = useState(mockRoles[0].id)
  const role = mockRoles.find((r) => r.id === activeRoleId)!

  const memberCounts = Object.fromEntries(
    mockRoles.map((r) => [r.id, mockUsers.filter((u) => u.role_ids.includes(r.id)).length])
  )

  const stats: [string, string][] = [
    ["Membres", String(memberCounts[role.id])],
    ["Permissions", `${role.permission_ids.length} sur ${mockPermissions.length}`],
    ["Dernière modification", role.last_modified_label],
  ]

  return (
    <div className="grid gap-6 xl:grid-cols-[20rem_minmax(0,1fr)]">
      <SectionCard title="Rôles" bodyClassName="p-0">
        <ul className="divide-y divide-border">
          {mockRoles.map((r) => (
            <li key={r.id}>
              <button
                onClick={() => setActiveRoleId(r.id)}
                className={cn(
                  "w-full px-5 py-4 text-left transition-colors hover:bg-surface",
                  activeRoleId === r.id && "bg-primary/5"
                )}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className={cn("text-sm font-medium", activeRoleId === r.id && "text-primary")}>
                    {r.name}
                  </span>
                  <span className="text-xs tabular text-muted-foreground">
                    {memberCounts[r.id]} membres
                  </span>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{r.description}</p>
              </button>
            </li>
          ))}
        </ul>
      </SectionCard>

      <div className="space-y-6">
        <SectionCard title={role.name} description={role.description}>
          <div className="grid gap-4 sm:grid-cols-3">
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
            {mockPermissions.map((p) => {
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
