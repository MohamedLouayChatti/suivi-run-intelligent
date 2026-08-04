"use client"

import { useState } from "react"
import { Check, Minus } from "lucide-react"

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ActiveBadge } from "@/components/app/status"
import { getPrimaryApplication, getBackupApplication } from "@/services/api/users"
import { getRoleName } from "@/features/users/get-role-name"
import { functionalTeamLabels } from "@/features/users/constants"
import { useRolesList } from "@/hooks/use-roles-list"
import { usePermissionsList } from "@/hooks/use-permissions-list"
import type { components } from "@/types/api"

type UserResponse = components["schemas"]["UserResponse"]

interface UserDetailsSheetProps {
  user: UserResponse | null
  onOpenChange: (open: boolean) => void
  onSaveRole: (userId: string, roleId: string) => void
  onSavePermissions: (userId: string, toGrant: string[], toRevoke: string[]) => void
}

function UserDetailsSheet({ user, onOpenChange, onSaveRole, onSavePermissions }: UserDetailsSheetProps) {
  const { roles } = useRolesList()
  const { permissions } = usePermissionsList()
  const currentRoleId = user?.role_ids[0] ?? roles[0]?.id ?? ""
  const [roleId, setRoleId] = useState(currentRoleId)

  // A permission is effectively granted if it comes from one of the user's roles or was
  // granted directly, unless it was explicitly revoked — mirrors AuthorizationService.resolve_permissions.
  const rolePermissionIds = new Set(
    (user?.role_ids ?? []).flatMap((rid) => roles.find((r) => r.id === rid)?.permission_ids ?? [])
  )
  const effectivePermissionIds = new Set(
    [...rolePermissionIds, ...(user?.direct_permission_ids ?? [])].filter(
      (id) => !(user?.revoked_permission_ids ?? []).includes(id)
    )
  )
  const [checkedPermissionIds, setCheckedPermissionIds] = useState<Set<string>>(effectivePermissionIds)

  if (!user) return <Sheet open={false} onOpenChange={onOpenChange} />

  const primaryApplication = getPrimaryApplication(user)
  const backupApplication = getBackupApplication(user)

  function togglePermission(permissionId: string, checked: boolean) {
    setCheckedPermissionIds((prev) => {
      const next = new Set(prev)
      if (checked) next.add(permissionId)
      else next.delete(permissionId)
      return next
    })
  }

  function handleSave() {
    if (!user) return
    if (roleId !== currentRoleId) onSaveRole(user.id, roleId)

    const toGrant = permissions.filter((p) => checkedPermissionIds.has(p.id) && !effectivePermissionIds.has(p.id)).map((p) => p.id)
    const toRevoke = permissions.filter((p) => !checkedPermissionIds.has(p.id) && effectivePermissionIds.has(p.id)).map((p) => p.id)
    if (toGrant.length > 0 || toRevoke.length > 0) onSavePermissions(user.id, toGrant, toRevoke)

    onOpenChange(false)
  }

  const rows: [string, React.ReactNode][] = [
    ["Rôle", getRoleName(user, roles)],
    [
      "Application",
      backupApplication ? `${primaryApplication} (principal), ${backupApplication} (secours)` : (primaryApplication ?? "—"),
    ],
    ["Équipe fonctionnelle", functionalTeamLabels[user.functional_team]],
    ["Statut", <ActiveBadge key="status" active={user.active} />],
  ]

  return (
    <Sheet open={!!user} onOpenChange={(open) => !open && onOpenChange(false)}>
      <SheetContent className="flex w-full flex-col gap-0 sm:max-w-md">
        <SheetHeader>
          <SheetTitle>{user.display_name}</SheetTitle>
          <SheetDescription>{user.email}</SheetDescription>
        </SheetHeader>
        <div className="flex-1 space-y-6 overflow-y-auto px-4">
          <dl className="space-y-4 text-sm">
            {rows.map(([label, value]) => (
              <div key={label} className="flex items-center justify-between gap-3 border-b border-border pb-3">
                <dt className="text-muted-foreground">{label}</dt>
                <dd className="font-medium">{value}</dd>
              </div>
            ))}
          </dl>
          <div className="space-y-2">
            <p className="text-sm font-medium">Attribuer un rôle</p>
            <Select value={roleId} onValueChange={setRoleId}>
              <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                {roles.map((r) => (
                  <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <p className="text-sm font-medium">Permissions</p>
            <ul className="divide-y divide-border rounded-md border border-border">
              {permissions.map((p) => {
                const checked = checkedPermissionIds.has(p.id)
                return (
                  <li key={p.id} className="flex items-center gap-3 px-3 py-2">
                    <Checkbox
                      id={`perm-${p.id}`}
                      checked={checked}
                      onCheckedChange={(value) => togglePermission(p.id, value === true)}
                    />
                    <Label htmlFor={`perm-${p.id}`} className="flex-1 cursor-pointer font-mono text-xs">
                      {p.name}
                    </Label>
                    {checked ? (
                      <Check className="size-3.5 text-primary" />
                    ) : (
                      <Minus className="size-3.5 text-muted-foreground" />
                    )}
                  </li>
                )
              })}
            </ul>
          </div>
        </div>
        <SheetFooter className="flex-row border-t border-border">
          <Button className="flex-1" onClick={handleSave}>Enregistrer</Button>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annuler</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

export { UserDetailsSheet }
