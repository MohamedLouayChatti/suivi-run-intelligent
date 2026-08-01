"use client"

import { useState } from "react"

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ActiveBadge } from "@/components/app/status"
import { getPrimaryApplication, getBackupApplication } from "@/services/api/users"
import { getRoleName } from "@/features/users/get-role-name"
import { functionalTeamLabels } from "@/features/users/constants"
import { useRolesList } from "@/hooks/use-roles-list"
import type { components } from "@/types/api"

type UserResponse = components["schemas"]["UserResponse"]

interface UserDetailsSheetProps {
  user: UserResponse | null
  onOpenChange: (open: boolean) => void
  onSaveRole: (userId: string, roleId: string) => void
}

function UserDetailsSheet({ user, onOpenChange, onSaveRole }: UserDetailsSheetProps) {
  const { roles } = useRolesList()
  const currentRoleId = user?.role_ids[0] ?? roles[0]?.id ?? ""
  const [roleId, setRoleId] = useState(currentRoleId)

  if (!user) return <Sheet open={false} onOpenChange={onOpenChange} />

  const primaryApplication = getPrimaryApplication(user)
  const backupApplication = getBackupApplication(user)

  function handleSave() {
    if (!user) return
    onSaveRole(user.id, roleId)
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
      <SheetContent className="w-full sm:max-w-md">
        <SheetHeader>
          <SheetTitle>{user.display_name}</SheetTitle>
          <SheetDescription>{user.email}</SheetDescription>
        </SheetHeader>
        <div className="space-y-6 px-4">
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
        </div>
        <SheetFooter className="flex-row">
          <Button className="flex-1" onClick={handleSave}>Enregistrer</Button>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annuler</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

export { UserDetailsSheet }
