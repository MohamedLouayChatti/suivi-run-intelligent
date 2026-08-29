"use client"

import { useMemo, useState } from "react"
import { Check, Minus, X } from "lucide-react"

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet"
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
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { PermissionGroupList } from "@/components/app/permission-group-list"
import { Switch } from "@/components/ui/switch"
import { ActiveBadge } from "@/components/app/status"
import { getPrimaryApplication, getBackupApplication, getReadOnlyApplications } from "@/services/api/users"
import { getRoleName } from "@/features/users/get-role-name"
import { functionalTeamLabels } from "@/features/users/constants"
import { applicationOptions, functionalTeamOptionsForApplications } from "@/features/tickets/constants"
import { buildPermissionGraph, usePermissions } from "@/lib/auth"
import { useRolesList } from "@/hooks/use-roles-list"
import { usePermissionsList } from "@/hooks/use-permissions-list"
import { describeUserAdminError } from "@/features/users/error-messages"
import { PermissionSaveError } from "@/features/users/use-users-admin"
import type { AdminUser, OrganizationalIdentity, UsersAdminCapabilities } from "@/features/users/use-users-admin"
import type { components } from "@/types/api"

type Application = components["schemas"]["Application"]
type FunctionalTeam = components["schemas"]["FunctionalTeam"]

/** Sentinel for the "Aucune" option: Radix's Select rejects an empty-string item value, and a
 * user holding no application at all is an ordinary state the admin must be able to set. */
const NO_APPLICATION = "none"

function buildAssignments(
  primary: Application | null,
  backup: Application | null,
  readOnly: readonly Application[]
): OrganizationalIdentity["application_assignments"] {
  const assignments: NonNullable<OrganizationalIdentity["application_assignments"]> = []
  if (primary) assignments.push({ application: primary, assignment_type: "PRIMARY" })
  if (backup) assignments.push({ application: backup, assignment_type: "BACKUP" })
  for (const application of readOnly) assignments.push({ application, assignment_type: "READ_ONLY" })
  return assignments
}

function sameApplicationSet(a: ReadonlySet<Application>, b: readonly Application[]): boolean {
  return a.size === b.length && b.every((application) => a.has(application))
}

/**
 * One save can be up to four backend writes, and they are not atomic across each other: the
 * backend has no endpoint that sets staffing, role, permissions and activation together, and
 * they must be sent in this order because each is validated against what the previous one
 * wrote. So a refusal part-way leaves the account in a state that is neither what it was nor
 * what was asked for, and the only honest thing to show is what each write actually did.
 */
type SaveStepStatus = "done" | "failed" | "skipped"

interface SaveStep {
  label: string
  status: SaveStepStatus
  /** The refusal, for a failed step; a note on how far it got, where the write is not atomic. */
  detail?: string
}

/** A write staged by the form, kept with its label so a failure can name what was being written. */
interface StagedWrite {
  label: string
  run: () => Promise<void>
}

/**
 * How far a permission save got before it was refused.
 *
 * The one write here that sends many requests, so the one whose failure leaves a count worth
 * reporting: without it the operator knows the save failed but not whether it left three of
 * five permissions applied.
 */
function permissionProgress(error: PermissionSaveError): string {
  const parts: string[] = []
  if (error.toGrant > 0) parts.push(`${error.granted} accordée${error.granted > 1 ? "s" : ""} sur ${error.toGrant}`)
  if (error.toRevoke > 0) parts.push(`${error.revoked} retirée${error.revoked > 1 ? "s" : ""} sur ${error.toRevoke}`)
  if (error.granted === 0 && error.revoked === 0) return "Aucune permission n'a été modifiée."
  return `Appliqué avant l'échec : ${parts.join(", ")}.`
}

/**
 * What the last save did, write by write.
 *
 * Sits above the footer rather than in a toast: every refusal reachable here is correctable in
 * the form right above it — a missing primary application, an unsatisfied prerequisite — so the
 * message belongs next to the fields that fix it, and has to stay there while they are edited.
 */
function SaveOutcomeBanner({ steps }: { steps: SaveStep[] }) {
  const anyDone = steps.some((step) => step.status === "done")
  return (
    <div role="alert" className="mx-4 mb-2 space-y-2 rounded-md border border-destructive/40 bg-destructive/5 p-3">
      <p className="text-sm font-medium text-destructive">
        {anyDone ? "Enregistrement incomplet" : "Enregistrement impossible"}
      </p>
      {anyDone && (
        <p className="text-xs text-muted-foreground">
          Une partie des modifications a été enregistrée. Corrigez ce qui suit et enregistrez à
          nouveau : seules les modifications restantes seront envoyées.
        </p>
      )}
      <ul className="space-y-1.5">
        {steps.map((step) => (
          <li key={step.label} className="flex gap-2 text-xs">
            {step.status === "done" && <Check className="mt-0.5 size-3.5 shrink-0 text-primary" />}
            {step.status === "failed" && <X className="mt-0.5 size-3.5 shrink-0 text-destructive" />}
            {step.status === "skipped" && <Minus className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />}
            <span className={step.status === "skipped" ? "text-muted-foreground" : undefined}>
              <span className="font-medium">{step.label}</span>
              {step.status === "done" && " — enregistré."}
              {step.status === "skipped" && " — non tenté."}
              {step.status === "failed" && ` — ${step.detail}`}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

interface UserDetailsSheetProps {
  user: AdminUser | null
  capabilities: UsersAdminCapabilities
  onOpenChange: (open: boolean) => void
  onSaveRole: (userId: string, roleId: string) => void | Promise<void>
  onSaveOrganizationalIdentity: (userId: string, identity: OrganizationalIdentity) => void | Promise<void>
  onSavePermissions: (userId: string, toGrant: string[], toRevoke: string[]) => void | Promise<void>
  onToggleActive: (userId: string) => void | Promise<void>
}

function UserDetailsSheet({
  user,
  capabilities,
  onOpenChange,
  onSaveRole,
  onSaveOrganizationalIdentity,
  onSavePermissions,
  onToggleActive,
}: UserDetailsSheetProps) {
  // Each list is fetched only when its own permission allows it, so a caller holding some of
  // this page's capabilities and not others never fires a request that can only 403.
  const { roles } = useRolesList({ enabled: capabilities.readRoles })
  const { permissions } = usePermissionsList({ enabled: capabilities.readPermissions })
  const { user: currentUser } = usePermissions()

  const detail = user?.detail ?? null
  const currentRoleId = detail?.role_id ?? roles[0]?.id ?? ""
  const [roleId, setRoleId] = useState(currentRoleId)

  // The same relation the backend enforces, read from the API rather than restated: each
  // permission publishes the ones it cannot be used without.
  const graph = useMemo(() => buildPermissionGraph(permissions), [permissions])

  // What the user effectively holds — role permissions plus direct grants, minus revocations,
  // then narrowed to the part whose prerequisites are actually present. Mirrors
  // `AuthorizationService.combine_permissions`, closure included: a direct grant whose
  // prerequisite nothing supplies is stored but not effective, and showing it ticked would
  // tell the admin the user has something they do not.
  const rolePermissionIds = new Set(roles.find((r) => r.id === detail?.role_id)?.permission_ids ?? [])
  const grantedPermissionIds = new Set(
    [...rolePermissionIds, ...(detail?.direct_permission_ids ?? [])].filter(
      (id) => !(detail?.revoked_permission_ids ?? []).includes(id)
    )
  )
  const effectivePermissionIds = graph.satisfiedSubset(grantedPermissionIds)

  const [checkedPermissionIds, setCheckedPermissionIds] = useState<Set<string>>(effectivePermissionIds)
  const [pendingCascade, setPendingCascade] = useState<{ permissionId: string; cascade: Set<string> } | null>(null)
  const [confirmingRoleChange, setConfirmingRoleChange] = useState(false)
  const [active, setActive] = useState(user?.active ?? true)
  // What the last save did, per write. Null until a save has failed — a save that succeeds
  // closes the sheet, so there is nothing to report.
  const [saveSteps, setSaveSteps] = useState<SaveStep[] | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  const currentPrimary = user ? getPrimaryApplication(user) : null
  const currentBackup = user ? getBackupApplication(user) : null
  const currentReadOnly = user ? getReadOnlyApplications(user) : []
  const [primaryApplication, setPrimaryApplication] = useState<Application | null>(currentPrimary)
  const [backupApplication, setBackupApplication] = useState<Application | null>(currentBackup)
  const [readOnlyApplications, setReadOnlyApplications] = useState<Set<Application>>(new Set(currentReadOnly))
  const [functionalTeam, setFunctionalTeam] = useState<FunctionalTeam>(user?.functional_team ?? "SUPPORT")

  // Read-only applications available to pick: never the one already held as primary or backup —
  // the aggregate refuses the same application under two assignment types, so this only avoids
  // offering a choice that would be rejected on save.
  const readOnlyOptions = applicationOptions.filter(
    (application) => application !== primaryApplication && application !== backupApplication
  )

  function toggleReadOnlyApplication(application: Application, checked: boolean) {
    setReadOnlyApplications((prev) => {
      const next = new Set(prev)
      if (checked) next.add(application)
      else next.delete(application)
      return next
    })
  }

  // The same rule the User aggregate enforces: AERO and VIO have no Paramétrage team, so holding
  // either — as primary or as backup — leaves Support the only answer. Chosen for the admin rather
  // than offered and then refused by the backend, and re-derived on every render so clearing the
  // application reopens the choice.
  const availableFunctionalTeams = functionalTeamOptionsForApplications([primaryApplication, backupApplication])
  const effectiveFunctionalTeam =
    availableFunctionalTeams.length === 1 ? availableFunctionalTeams[0] : functionalTeam

  const isSelf = currentUser?.id === user?.id

  // Every section below asks for the permission that performs it, and for the self-targeting
  // rules `UserAccessPolicy` applies: it refuses set_role, revoke_permission and
  // set_organizational_identity on the actor's own record. The first can strip their own
  // access; the last is refused on different grounds — staffing is a decision made about a
  // person, not one they make for themselves.
  const mayEditStaffing = capabilities.manageOrganization && !isSelf
  const mayEditRole = capabilities.assignRole && capabilities.readRoles && !isSelf
  const mayEditPermissions = capabilities.managePermissions && capabilities.readPermissions && !isSelf
  const mayReadPermissions = capabilities.readAll && capabilities.readPermissions
  const mayToggleActive = user?.active ? capabilities.deactivate && !isSelf : capabilities.activate

  const stagedPrimary = mayEditStaffing ? primaryApplication : currentPrimary
  const selectedRole = roles.find((r) => r.id === roleId)

  // The rule itself is the backend's; the frontend only asks the role whether it applies. Reading
  // `requires_primary_application` off RoleResponse is what keeps a list of staffed role names out
  // of the UI — no business logic here, just the flag the backend publishes.
  const rolePrimaryApplicationMissing =
    selectedRole?.requires_primary_application === true && stagedPrimary === null

  const roleChangeStaged = roleId !== currentRoleId
  const exceptionCount =
    (detail?.direct_permission_ids.length ?? 0) + (detail?.revoked_permission_ids.length ?? 0)

  // A role change replaces the whole permission profile, so the checkboxes show what the new
  // role grants and stop being editable: staging permission edits alongside a role change would
  // show the admin choices the save is about to discard.
  const displayedPermissionIds = roleChangeStaged
    ? graph.satisfiedSubset(new Set(selectedRole?.permission_ids ?? []))
    : checkedPermissionIds

  const permissionsByName = useMemo(
    () => new Map(permissions.map((permission) => [permission.id, permission.name])),
    [permissions]
  )

  function namesOf(ids: Iterable<string>): string[] {
    return [...ids].map((id) => permissionsByName.get(id) ?? id).sort()
  }

  if (!user) return <Sheet open={false} onOpenChange={onOpenChange} />

  function togglePermission(permissionId: string, checked: boolean) {
    if (checked) {
      setCheckedPermissionIds((prev) => new Set(prev).add(permissionId))
      return
    }
    // Unticking takes everything that depended on this permission with it, exactly as the
    // backend's revoke does. More than one means confirming first — dropping ticket.read
    // carries fifteen others, which is not something to discover after the fact.
    const cascade = graph.cascadeOf(permissionId, checkedPermissionIds)
    if (cascade.size > 1) {
      setPendingCascade({ permissionId, cascade })
      return
    }
    setCheckedPermissionIds((prev) => {
      const next = new Set(prev)
      next.delete(permissionId)
      return next
    })
  }

  function applyPendingCascade() {
    if (!pendingCascade) return
    setCheckedPermissionIds((prev) => new Set([...prev].filter((id) => !pendingCascade.cascade.has(id))))
    setPendingCascade(null)
  }

  /**
   * The writes this save will send, in the order the backend requires.
   *
   * Staged as a list first rather than awaited inline, so a refusal on any one of them can be
   * reported against the others: the step that failed is named, the ones already sent are
   * known to have landed, and the ones after it are known not to have been attempted.
   */
  function stagedWrites(target: AdminUser): StagedWrite[] {
    const writes: StagedWrite[] = []

    // Staffing is written before the role, never after: assigning a role that requires a primary
    // application to a user who is only being given one in this same save would otherwise be
    // refused by a backend that has not seen the application yet.
    const assignmentsChanged =
      primaryApplication !== currentPrimary ||
      backupApplication !== currentBackup ||
      !sameApplicationSet(readOnlyApplications, currentReadOnly)
    if (mayEditStaffing && (assignmentsChanged || effectiveFunctionalTeam !== target.functional_team)) {
      writes.push({
        label: "Affectation applicative",
        run: async () => {
          await onSaveOrganizationalIdentity(target.id, {
            functional_team: effectiveFunctionalTeam,
            application_assignments: buildAssignments(primaryApplication, backupApplication, [
              ...readOnlyApplications,
            ]),
          })
        },
      })
    }

    if (mayEditRole && roleChangeStaged) {
      // Setting a role discards every permission exception, so there is nothing left for a
      // permission save to write — and sending one would re-add what the role change removed.
      writes.push({ label: "Rôle", run: async () => void (await onSaveRole(target.id, roleId)) })
    } else if (mayEditPermissions) {
      const toGrant = graph.prerequisitesFirst(
        permissions.filter((p) => checkedPermissionIds.has(p.id) && !effectivePermissionIds.has(p.id)).map((p) => p.id)
      )
      const toRevoke = permissions
        .filter((p) => !checkedPermissionIds.has(p.id) && effectivePermissionIds.has(p.id))
        .map((p) => p.id)
      if (toGrant.length > 0 || toRevoke.length > 0) {
        writes.push({
          label: "Permissions",
          run: async () => void (await onSavePermissions(target.id, toGrant, toRevoke)),
        })
      }
    }

    if (mayToggleActive && active !== target.active) {
      writes.push({
        label: active ? "Activation du compte" : "Désactivation du compte",
        run: async () => void (await onToggleActive(target.id)),
      })
    }

    return writes
  }

  async function persist() {
    if (!user) return
    if (rolePrimaryApplicationMissing) return
    if (isSaving) return

    setIsSaving(true)
    setSaveSteps(null)

    const steps: SaveStep[] = []
    let stopped = false
    try {
      for (const write of stagedWrites(user)) {
        // Everything after a refusal is left unsent. The order is a dependency chain — the
        // role is validated against the staffing this save was to write — so continuing past
        // a failure would send writes whose precondition is known to be missing.
        if (stopped) {
          steps.push({ label: write.label, status: "skipped" })
          continue
        }
        try {
          await write.run()
          steps.push({ label: write.label, status: "done" })
        } catch (error) {
          stopped = true
          steps.push({
            label: write.label,
            status: "failed",
            detail:
              error instanceof PermissionSaveError
                ? `${describeUserAdminError(error.cause)} ${permissionProgress(error)}`
                : describeUserAdminError(error),
          })
        }
      }
    } finally {
      setIsSaving(false)
    }

    // Only a clean save closes the sheet. Leaving it open on failure keeps the staged edits,
    // and every write above re-reads what the user now holds — each of them invalidates the
    // cache whether it succeeded or not — so pressing Enregistrer again re-sends only what
    // did not land.
    if (stopped) setSaveSteps(steps)
    else onOpenChange(false)
  }

  function handleSave() {
    // Only worth confirming when the change actually destroys something: a role change on a
    // user carrying no exceptions takes nothing away that was not already the old role's.
    if (mayEditRole && roleChangeStaged && exceptionCount > 0) {
      setConfirmingRoleChange(true)
      return
    }
    void persist()
  }

  const rows: [string, React.ReactNode][] = [
    ...(capabilities.readAll && capabilities.readRoles
      ? ([["Rôle", getRoleName(detail?.role_id, roles)]] as [string, React.ReactNode][])
      : []),
    [
      "Application",
      [
        currentBackup ? `${currentPrimary} (principal), ${currentBackup} (secours)` : (currentPrimary ?? "—"),
        currentReadOnly.length > 0
          ? `${currentReadOnly.join(", ")} (lecture seule)`
          : null,
      ]
        .filter((part): part is string => part !== null)
        .join(" · "),
    ],
    ["Équipe fonctionnelle", functionalTeamLabels[user.functional_team]],
    [
      "Statut",
      <div key="status" className="flex items-center gap-2">
        <ActiveBadge active={active} />
        {mayToggleActive && (
          <Switch checked={active} onCheckedChange={setActive} aria-label="Activer ou désactiver le compte" />
        )}
      </div>,
    ],
  ]

  const anySectionEditable = mayEditRole || mayEditStaffing || mayEditPermissions || mayToggleActive

  return (
    <>
      <Sheet open={!!user} onOpenChange={(open) => !open && onOpenChange(false)}>
        <SheetContent className="flex w-full flex-col gap-0 sm:max-w-md">
          <SheetHeader>
            <SheetTitle>{user.display_name}</SheetTitle>
            {capabilities.readAll && <SheetDescription>{detail?.email}</SheetDescription>}
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

            {mayEditRole && (
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
                {roleChangeStaged && exceptionCount > 0 && (
                  <p className="text-xs text-destructive">
                    Changer de rôle réinitialise les permissions : les {exceptionCount} exception
                    {exceptionCount > 1 ? "s" : ""} de cet utilisateur seront supprimées et il obtiendra
                    exactement les permissions du rôle « {selectedRole?.name} ».
                  </p>
                )}
              </div>
            )}

            {mayEditStaffing && (
              <div className="space-y-3">
                <div className="space-y-1">
                  <p className="text-sm font-medium">Affectation applicative</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="primary-application">Application principale</Label>
                  <Select
                    value={primaryApplication ?? NO_APPLICATION}
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
                      // An application cannot be both staffed and read-only at once — the aggregate
                      // refuses the same application under two assignment types.
                      if (next !== null && readOnlyApplications.has(next)) {
                        setReadOnlyApplications((prev) => {
                          const nextSet = new Set(prev)
                          nextSet.delete(next)
                          return nextSet
                        })
                      }
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
                    disabled={primaryApplication === null}
                    onValueChange={(value) => {
                      const next = value === NO_APPLICATION ? null : (value as Application)
                      setBackupApplication(next)
                      // Same cardinality rule as primary above: never both staffed and read-only.
                      if (next !== null && readOnlyApplications.has(next)) {
                        setReadOnlyApplications((prev) => {
                          const nextSet = new Set(prev)
                          nextSet.delete(next)
                          return nextSet
                        })
                      }
                    }}
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
                  {primaryApplication === null && (
                    <p className="text-xs text-muted-foreground">
                      Une application de secours nécessite d&apos;abord une application principale.
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="functional-team">Équipe fonctionnelle</Label>
                  <Select
                    value={effectiveFunctionalTeam}
                    disabled={availableFunctionalTeams.length === 1}
                    onValueChange={(value) => setFunctionalTeam(value as FunctionalTeam)}
                  >
                    <SelectTrigger id="functional-team" className="w-full"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {availableFunctionalTeams.map((team) => (
                        <SelectItem key={team} value={team}>{functionalTeamLabels[team]}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {availableFunctionalTeams.length === 1 && (
                    <p className="text-xs text-muted-foreground">
                      AERO et VIO sont assurées par l&apos;équipe SN3 uniquement.
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label>Applications en lecture seule</Label>
                  <p className="text-xs text-muted-foreground">
                    Accès en lecture aux tickets et analyses de ces applications, sans pouvoir en
                    créer ni en gérer.
                  </p>
                  <div className="space-y-2">
                    {readOnlyOptions.map((application) => (
                      <div key={application} className="flex items-center gap-2">
                        <Checkbox
                          id={`read-only-${application}`}
                          checked={readOnlyApplications.has(application)}
                          onCheckedChange={(value) => toggleReadOnlyApplication(application, value === true)}
                        />
                        <Label htmlFor={`read-only-${application}`} className="cursor-pointer font-normal">
                          {application}
                        </Label>
                      </div>
                    ))}
                    {readOnlyOptions.length === 0 && (
                      <p className="text-xs text-muted-foreground">
                        Aucune application disponible : déjà principale ou de secours.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {capabilities.manageOrganization && isSelf && (
              <p className="text-xs text-muted-foreground">
                Vous ne pouvez pas modifier votre propre rôle ni votre propre affectation. Un autre
                administrateur doit s&apos;en charger.
              </p>
            )}

            {mayReadPermissions && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Permissions</p>
                {roleChangeStaged && (
                  <p className="text-xs text-muted-foreground">
                    Permissions du rôle « {selectedRole?.name} », appliquées après enregistrement.
                  </p>
                )}
                <PermissionGroupList
                  permissions={permissions}
                  graph={graph}
                  heldIds={displayedPermissionIds}
                  isEditable={() => mayEditPermissions && !roleChangeStaged}
                  onToggle={(p, checked) => togglePermission(p.id, checked)}
                  renderTrailing={(_p, checked) =>
                    checked ? (
                      <Check className="mt-0.5 size-3.5 shrink-0 text-primary" />
                    ) : (
                      <Minus className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />
                    )
                  }
                  idPrefix="perm"
                  className="rounded-md border border-border"
                />
              </div>
            )}
          </div>
          {saveSteps && <SaveOutcomeBanner steps={saveSteps} />}
          {anySectionEditable && (
            <SheetFooter>
              <Button onClick={handleSave} disabled={rolePrimaryApplicationMissing || isSaving}>
                {isSaving ? "Enregistrement…" : "Enregistrer"}
              </Button>
            </SheetFooter>
          )}
        </SheetContent>
      </Sheet>

      <AlertDialog open={pendingCascade !== null} onOpenChange={(open) => !open && setPendingCascade(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Retirer plusieurs permissions ?</AlertDialogTitle>
            <AlertDialogDescription>
              {`« ${permissionsByName.get(pendingCascade?.permissionId ?? "") ?? ""} » est requise par ${
                (pendingCascade?.cascade.size ?? 1) - 1
              } autre${(pendingCascade?.cascade.size ?? 1) - 1 > 1 ? "s" : ""} permission${
                (pendingCascade?.cascade.size ?? 1) - 1 > 1 ? "s" : ""
              }, qui ${(pendingCascade?.cascade.size ?? 1) - 1 > 1 ? "seront retirées" : "sera retirée"} également : `}
              {namesOf(
                [...(pendingCascade?.cascade ?? [])].filter((id) => id !== pendingCascade?.permissionId)
              ).join(", ")}
              .
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction onClick={applyPendingCascade}>
              Retirer les {pendingCascade?.cascade.size ?? 0}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={confirmingRoleChange} onOpenChange={setConfirmingRoleChange}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Changer le rôle de {user.display_name} ?</AlertDialogTitle>
            <AlertDialogDescription>
              {`Attribuer le rôle « ${selectedRole?.name} » remplace l'intégralité de ses permissions. Les ${exceptionCount} exception${exceptionCount > 1 ? "s" : ""} qui lui ${exceptionCount > 1 ? "ont" : "a"} été accordée${exceptionCount > 1 ? "s" : ""} ou retirée${exceptionCount > 1 ? "s" : ""} individuellement seront supprimées, et il obtiendra exactement les permissions de ce rôle.`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setConfirmingRoleChange(false)
                void persist()
              }}
            >
              Changer le rôle
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

export { UserDetailsSheet }
