"use client"

import { useMemo, useState } from "react"
import { Lock } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { cn } from "@/lib/utils"
import { buildPermissionGraph } from "@/lib/auth"
import { useRolesList } from "@/hooks/use-roles-list"
import { usePermissionsList } from "@/hooks/use-permissions-list"
import { useUsersList } from "@/hooks/use-users-list"
import { useRolesAdmin } from "@/features/roles/use-roles-admin"

// Static presentational copy — RoleResponse only carries id/name/permission_ids, and role
// management (create/edit) isn't part of this app; roles are seeded, not authored by admins.
// Keyed by the actual seeded role names (see app/scripts/seeding/roles_permissions/roles.py) —
// previously kept English placeholder names ("Support Engineer", ...) that never matched the
// real seeded roles, so two of three roles silently showed no description here.
const roleDescriptions: Record<string, string> = {
  Admin: "Accès complet à la plateforme, y compris l'administration des utilisateurs, des rôles et des permissions.",
  "Ingénieur Support": "Prend en charge la résolution des tickets au quotidien et la contribution aux connaissances.",
  "Chef de projet":
    "Ingénieur support qui pilote une application : il agit sur tous les tickets de son application principale, même ceux qui ne lui sont pas assignés, et gère la base de connaissances.",
  Lecteur: "Consulte les tickets et peut y ajouter des commentaires ou des pièces jointes, sans gérer leur cycle de vie.",
}

function RolesPanel() {
  const { capabilities, togglePermission } = useRolesAdmin()
  const { roles } = useRolesList()
  const { permissions } = usePermissionsList({ enabled: capabilities.readPermissions })
  // Only for the member count, and only when the caller may read every user. Firing this
  // unconditionally is what used to force `user.read_all` onto the whole page's gate.
  const { users } = useUsersList({ enabled: capabilities.countMembers })
  const [activeRoleId, setActiveRoleId] = useState<string | null>(null)
  const [pendingChange, setPendingChange] = useState<
    { permissionId: string; permissionName: string; granted: boolean; cascade: Set<string> } | null
  >(null)

  // The same relation the backend enforces, published on each permission rather than restated.
  const graph = useMemo(() => buildPermissionGraph(permissions), [permissions])
  const permissionsByName = useMemo(
    () => new Map(permissions.map((permission) => [permission.id, permission.name])),
    [permissions]
  )

  const roleId = activeRoleId ?? roles[0]?.id
  const role = roles.find((r) => r.id === roleId)
  if (!role) return null

  const currentRoleId = role.id
  const grantedIds = new Set(role.permission_ids)

  function namesOf(ids: Iterable<string>): string[] {
    return [...ids].map((id) => permissionsByName.get(id) ?? id).sort()
  }

  function requestChange(permissionId: string, permissionName: string, granted: boolean) {
    // Revoking carries away everything in the role that depended on this permission, exactly as
    // the backend's cascade does; granting affects only itself, its prerequisites being required
    // to be present already.
    const cascade = granted ? new Set([permissionId]) : graph.cascadeOf(permissionId, grantedIds)
    setPendingChange({ permissionId, permissionName, granted, cascade })
  }

  function confirmPendingChange() {
    if (!pendingChange) return
    togglePermission(currentRoleId, pendingChange.permissionId, pendingChange.granted)
    setPendingChange(null)
  }

  const memberCounts = Object.fromEntries(
    roles.map((r) => [r.id, users.filter((u) => u.role_id === r.id).length])
  )

  const stats: [string, string][] = [
    ...(capabilities.countMembers
      ? ([["Membres", String(memberCounts[role.id] ?? 0)]] as [string, string][])
      : []),
    ["Permissions", `${role.permission_ids.length} sur ${permissions.length}`],
  ]

  const cascadeExtras = pendingChange
    ? namesOf([...pendingChange.cascade].filter((id) => id !== pendingChange.permissionId))
    : []

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
                  {capabilities.countMembers && (
                    <span className="text-xs tabular text-muted-foreground">
                      {memberCounts[r.id] ?? 0} membres
                    </span>
                  )}
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

        {capabilities.readPermissions && (
          <SectionCard title="Permissions" description="Capacités accordées pour ce rôle" bodyClassName="p-0">
            <ul className="divide-y divide-border">
              {permissions.map((p) => {
                const granted = grantedIds.has(p.id)
                // A role cannot hold a permission without the ones it is built on, so the box
                // stays disabled until they are granted. The backend refuses such a grant
                // outright; this only avoids offering it.
                const missing = granted ? new Set<string>() : graph.missingPrerequisites(p.id, grantedIds)
                const blocked = missing.size > 0
                const editable = granted ? capabilities.revokePermission : capabilities.grantPermission
                return (
                  <li key={p.id} className="flex items-start gap-3 px-5 py-3">
                    <Checkbox
                      id={`role-perm-${p.id}`}
                      checked={granted}
                      disabled={!editable || blocked}
                      className="mt-0.5"
                      onCheckedChange={() => requestChange(p.id, p.name, !granted)}
                    />
                    <div className="min-w-0 flex-1">
                      <Label
                        htmlFor={`role-perm-${p.id}`}
                        className={cn("font-mono text-xs", editable && !blocked && "cursor-pointer")}
                      >
                        {p.name}
                      </Label>
                      {blocked && (
                        <p className="mt-0.5 flex items-start gap-1 text-[11px] leading-snug text-muted-foreground">
                          <Lock className="mt-px size-3 shrink-0" />
                          <span>Nécessite {namesOf(missing).join(", ")}</span>
                        </p>
                      )}
                    </div>
                    <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                      {granted ? "Accordée" : "Non accordée"}
                    </span>
                  </li>
                )
              })}
            </ul>
          </SectionCard>
        )}
      </div>

      <AlertDialog open={pendingChange !== null} onOpenChange={(open) => !open && setPendingChange(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {pendingChange?.granted
                ? "Accorder cette permission ?"
                : cascadeExtras.length > 0
                  ? "Révoquer plusieurs permissions ?"
                  : "Révoquer cette permission ?"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {pendingChange?.granted ? (
                `Accorder la permission « ${pendingChange.permissionName} » au rôle « ${role.name} » ? Tous les membres de ce rôle en bénéficieront immédiatement.`
              ) : cascadeExtras.length > 0 ? (
                <>
                  {`« ${pendingChange?.permissionName} » est requise par ${cascadeExtras.length} autre${cascadeExtras.length > 1 ? "s" : ""} permission${cascadeExtras.length > 1 ? "s" : ""} de ce rôle, qui ${cascadeExtras.length > 1 ? "seront révoquées" : "sera révoquée"} également : `}
                  <span className="font-medium">{cascadeExtras.join(", ")}</span>
                  {". Tous les membres du rôle les perdront immédiatement."}
                </>
              ) : (
                `Révoquer la permission « ${pendingChange?.permissionName} » du rôle « ${role.name} » ? Tous les membres de ce rôle la perdront immédiatement, sauf si elle leur est accordée directement.`
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction onClick={confirmPendingChange}>
              {pendingChange && !pendingChange.granted && cascadeExtras.length > 0
                ? `Révoquer les ${pendingChange.cascade.size}`
                : "Confirmer"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export { RolesPanel }
