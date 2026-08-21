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
import { Switch } from "@/components/ui/switch"
import { ActiveBadge } from "@/components/app/status"
import { getPrimaryApplication, getBackupApplication } from "@/services/api/users"
import { getRoleName } from "@/features/users/get-role-name"
import { functionalTeamLabels } from "@/features/users/constants"
import { applicationOptions, functionalTeamOptionsForApplications } from "@/features/tickets/constants"
import { usePermissions } from "@/lib/auth"
import { useRolesList } from "@/hooks/use-roles-list"
import { usePermissionsList } from "@/hooks/use-permissions-list"
import type { OrganizationalIdentity } from "@/features/users/use-users-admin"
import type { components } from "@/types/api"

type UserResponse = components["schemas"]["UserResponse"]
type Application = components["schemas"]["Application"]
type FunctionalTeam = components["schemas"]["FunctionalTeam"]

/** Sentinel for the "Aucune" option: Radix's Select rejects an empty-string item value, and a
 * user holding no application at all is an ordinary state the admin must be able to set. */
const NO_APPLICATION = "none"

function buildAssignments(
  primary: Application | null,
  backup: Application | null
): OrganizationalIdentity["application_assignments"] {
  const assignments: NonNullable<OrganizationalIdentity["application_assignments"]> = []
  if (primary) assignments.push({ application: primary, assignment_type: "PRIMARY" })
  if (backup) assignments.push({ application: backup, assignment_type: "BACKUP" })
  return assignments
}

interface UserDetailsSheetProps {
  user: UserResponse | null
  onOpenChange: (open: boolean) => void
  onSaveRole: (userId: string, roleId: string) => void | Promise<void>
  onSaveOrganizationalIdentity: (userId: string, identity: OrganizationalIdentity) => void | Promise<void>
  onSavePermissions: (userId: string, toGrant: string[], toRevoke: string[]) => void | Promise<void>
  onToggleActive: (userId: string) => void
}

function UserDetailsSheet({ user, onOpenChange, onSaveRole, onSaveOrganizationalIdentity, onSavePermissions, onToggleActive }: UserDetailsSheetProps) {
  const { roles } = useRolesList()
  const { permissions } = usePermissionsList()
  const { user: currentUser, hasPermission } = usePermissions()
  const currentRoleId = user?.role_id ?? roles[0]?.id ?? ""
  const [roleId, setRoleId] = useState(currentRoleId)

  // A permission is effectively granted if it comes from the user's role or was
  // granted directly, unless it was explicitly revoked — mirrors AuthorizationService.resolve_permissions.
  const rolePermissionIds = new Set(roles.find((r) => r.id === user?.role_id)?.permission_ids ?? [])
  const effectivePermissionIds = new Set(
    [...rolePermissionIds, ...(user?.direct_permission_ids ?? [])].filter(
      (id) => !(user?.revoked_permission_ids ?? []).includes(id)
    )
  )
  const [checkedPermissionIds, setCheckedPermissionIds] = useState<Set<string>>(effectivePermissionIds)
  const [active, setActive] = useState(user?.active ?? true)

  const currentPrimary = user ? getPrimaryApplication(user) : null
  const currentBackup = user ? getBackupApplication(user) : null
  const [primaryApplication, setPrimaryApplication] = useState<Application | null>(currentPrimary)
  const [backupApplication, setBackupApplication] = useState<Application | null>(currentBackup)
  const [functionalTeam, setFunctionalTeam] = useState<FunctionalTeam>(user?.functional_team ?? "SUPPORT")

  // The same rule the User aggregate enforces: AERO and VIO have no Paramétrage team, so holding
  // either — as primary or as backup — leaves Support the only answer. Chosen for the admin rather
  // than offered and then refused by the backend, and re-derived on every render so clearing the
  // application reopens the choice.
  const availableFunctionalTeams = functionalTeamOptionsForApplications([primaryApplication, backupApplication])
  const effectiveFunctionalTeam =
    availableFunctionalTeams.length === 1 ? availableFunctionalTeams[0] : functionalTeam

  // Permission-aware UX only, mirroring the backend: `user.manage_organization` gates the section
  // at all, and UserAccessPolicy refuses it on the actor's own record — staffing is a decision made
  // about a person, not one they make for themselves.
  const mayManageOrganization = hasPermission("user.manage_organization")
  const isSelf = currentUser?.id === user?.id

  // What the user would hold once this sheet is saved. An admin who cannot edit staffing leaves it
  // exactly as stored, so the check below reads the same value either way.
  const mayEditStaffing = mayManageOrganization && !isSelf
  const stagedPrimary = mayEditStaffing ? primaryApplication : currentPrimary
  const selectedRole = roles.find((r) => r.id === roleId)

  // The rule itself is the backend's; the frontend only asks the role whether it applies. Reading
  // `requires_primary_application` off RoleResponse is what keeps a list of staffed role names out
  // of the UI — no business logic here, just the flag the backend publishes.
  const rolePrimaryApplicationMissing =
    selectedRole?.requires_primary_application === true && stagedPrimary === null

  if (!user) return <Sheet open={false} onOpenChange={onOpenChange} />

  function togglePermission(permissionId: string, checked: boolean) {
    setCheckedPermissionIds((prev) => {
      const next = new Set(prev)
      if (checked) next.add(permissionId)
      else next.delete(permissionId)
      return next
    })
  }

  async function handleSave() {
    if (!user) return
    if (rolePrimaryApplicationMissing) return

    // Staffing is written before the role, never after: assigning a role that requires a primary
    // application to a user who is only being given one in this same save would otherwise be
    // refused by a backend that has not seen the application yet.
    const assignmentsChanged = primaryApplication !== currentPrimary || backupApplication !== currentBackup
    if (mayEditStaffing && (assignmentsChanged || effectiveFunctionalTeam !== user.functional_team)) {
      await onSaveOrganizationalIdentity(user.id, {
        functional_team: effectiveFunctionalTeam,
        application_assignments: buildAssignments(primaryApplication, backupApplication),
      })
    }

    if (roleId !== currentRoleId) await onSaveRole(user.id, roleId)

    const toGrant = permissions.filter((p) => checkedPermissionIds.has(p.id) && !effectivePermissionIds.has(p.id)).map((p) => p.id)
    const toRevoke = permissions.filter((p) => !checkedPermissionIds.has(p.id) && effectivePermissionIds.has(p.id)).map((p) => p.id)
    if (toGrant.length > 0 || toRevoke.length > 0) onSavePermissions(user.id, toGrant, toRevoke)

    if (active !== user.active) onToggleActive(user.id)

    onOpenChange(false)
  }

  const rows: [string, React.ReactNode][] = [
    ["Rôle", getRoleName(user, roles)],
    [
      "Application",
      currentBackup ? `${currentPrimary} (principal), ${currentBackup} (secours)` : (currentPrimary ?? "—"),
    ],
    ["Équipe fonctionnelle", functionalTeamLabels[user.functional_team]],
    [
      "Statut",
      <div key="status" className="flex items-center gap-2">
        <ActiveBadge active={active} />
        <Switch checked={active} onCheckedChange={setActive} aria-label="Activer ou désactiver le compte" />
      </div>,
    ],
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
            {rolePrimaryApplicationMissing && (
              <p className="text-xs text-destructive">
                {mayEditStaffing
                  ? `Le rôle « ${selectedRole?.name} » nécessite une application principale. Renseignez-la ci-dessous.`
                  : `Le rôle « ${selectedRole?.name} » nécessite une application principale, que cet utilisateur n'a pas.`}
              </p>
            )}
          </div>
          {mayManageOrganization && (
            <div className="space-y-3">
              <div className="space-y-1">
                <p className="text-sm font-medium">Affectation applicative</p>
                {isSelf && (
                  <p className="text-xs text-muted-foreground">
                    Vous ne pouvez pas modifier votre propre affectation. Un autre administrateur doit
                    s&apos;en charger.
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="primary-application">Application principale</Label>
                <Select
                  value={primaryApplication ?? NO_APPLICATION}
                  disabled={isSelf}
                  onValueChange={(value) => {
                    const next = value === NO_APPLICATION ? null : (value as Application)
                    setPrimaryApplication(next)
                    // One application per user, never both roles on the same one — the same pair the
                    // aggregate refuses as a duplicate assignment.
                    if (next !== null && next === backupApplication) setBackupApplication(null)
                    // A backup supplements an application of one's own, so it cannot outlive the
                    // primary. Cleared visibly here rather than left to be refused on save, the same
                    // way the AERO/VIO team rule is resolved for the admin instead of rejected.
                    if (next === null) setBackupApplication(null)
                  }}
                >
                  <SelectTrigger id="primary-application" className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NO_APPLICATION}>Aucune</SelectItem>
                    {applicationOptions.map((application) => (
                      <SelectItem key={application} value={application}>{application}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="backup-application">Application de secours</Label>
                <Select
                  value={backupApplication ?? NO_APPLICATION}
                  disabled={isSelf || primaryApplication === null}
                  onValueChange={(value) =>
                    setBackupApplication(value === NO_APPLICATION ? null : (value as Application))
                  }
                >
                  <SelectTrigger id="backup-application" className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NO_APPLICATION}>Aucune</SelectItem>
                    {applicationOptions
                      .filter((application) => application !== primaryApplication)
                      .map((application) => (
                        <SelectItem key={application} value={application}>{application}</SelectItem>
                      ))}
                  </SelectContent>
                </Select>
                {primaryApplication === null && !isSelf && (
                  <p className="text-xs text-muted-foreground">
                    Une application de secours nécessite d&apos;abord une application principale.
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="functional-team">Équipe fonctionnelle</Label>
                <Select
                  value={effectiveFunctionalTeam}
                  disabled={isSelf || availableFunctionalTeams.length === 1}
                  onValueChange={(value) => setFunctionalTeam(value as FunctionalTeam)}
                >
                  <SelectTrigger id="functional-team" className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {availableFunctionalTeams.map((team) => (
                      <SelectItem key={team} value={team}>{functionalTeamLabels[team]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {availableFunctionalTeams.length === 1 && !isSelf && (
                  <p className="text-xs text-muted-foreground">
                    AERO et VIO sont assurées par l&apos;équipe Support uniquement.
                  </p>
                )}
              </div>
            </div>
          )}
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
          <Button className="flex-1" onClick={handleSave} disabled={rolePrimaryApplicationMissing}>Enregistrer</Button>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annuler</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

export { UserDetailsSheet }
