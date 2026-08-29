"use client"

import { useState } from "react"
import { Search, MoreHorizontal } from "lucide-react"

import { cn } from "@/lib/utils"
import { SectionCard } from "@/components/app/page"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ActiveBadge } from "@/components/app/status"
import { getPrimaryApplication } from "@/services/api/users"
import { getRoleName } from "@/features/users/get-role-name"
import { functionalTeamLabels } from "@/features/users/constants"
import { UserDetailsSheet } from "@/features/users/user-details-sheet"
import { describeUserAdminError } from "@/features/users/error-messages"
import { toast } from "@/hooks/use-toast"
import { usePermissions } from "@/lib/auth"
import { useRolesList } from "@/hooks/use-roles-list"
import type { AdminUser, OrganizationalIdentity, UsersAdminCapabilities } from "@/features/users/use-users-admin"

function initials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase()
}

interface UsersTableProps {
  users: AdminUser[]
  capabilities: UsersAdminCapabilities
  highlightUserId?: string | null
  onChangeRole: (userId: string, roleId: string) => void | Promise<void>
  onSaveOrganizationalIdentity: (userId: string, identity: OrganizationalIdentity) => void | Promise<void>
  onToggleActive: (userId: string) => void | Promise<void>
  onSavePermissions: (userId: string, toGrant: string[], toRevoke: string[]) => void | Promise<void>
}

function UsersTable({
  users,
  capabilities,
  highlightUserId,
  onChangeRole,
  onSaveOrganizationalIdentity,
  onToggleActive,
  onSavePermissions,
}: UsersTableProps) {
  // Only fetched when the caller may read every role. Without it the role column and the role
  // filter simply do not render, rather than the page refusing to open.
  const { roles } = useRolesList({ enabled: capabilities.readRoles })
  const { user: currentUser } = usePermissions()
  const [query, setQuery] = useState("")
  const [roleId, setRoleId] = useState("all")
  const [manualSelectedUserId, setManualSelectedUserId] = useState<string | null>(null)
  const [highlightDismissed, setHighlightDismissed] = useState(false)

  // Deep-linked from a "new user registered" notification (?highlight=<id>) — open that
  // user's details sheet once the list has loaded far enough to contain them. Derived
  // (not effect-driven) so it naturally re-evaluates as `users` arrives; `highlightDismissed`
  // stops it from reopening once the admin has closed the sheet.
  const isHighlightActive = !highlightDismissed && !!highlightUserId && users.some((u) => u.id === highlightUserId)
  const selectedUserId = manualSelectedUserId ?? (isHighlightActive ? highlightUserId : null)

  function closeSheet() {
    setManualSelectedUserId(null)
    if (isHighlightActive) setHighlightDismissed(true)
  }

  // Both follow the projection rather than being blanked per row: a directory read carries no
  // email and no role id at all, so there is nothing to put in either column.
  const showIdentityColumns = capabilities.readAll
  const showRoleColumn = capabilities.readAll && capabilities.readRoles

  // Whether opening a user is worth offering — the sheet holds nothing for a caller who may
  // neither read their details nor change anything about them.
  const canOpenDetails =
    capabilities.readAll ||
    capabilities.assignRole ||
    capabilities.manageOrganization ||
    capabilities.managePermissions

  function activationLabel(user: AdminUser): string | null {
    if (user.active) return capabilities.deactivate ? "Désactiver" : null
    return capabilities.activate ? "Activer" : null
  }

  // A toast here, where the sheet reports the same failure inline: this row action has no form
  // to correct and nothing staged to preserve, so there is nowhere to anchor a message. What
  // both share is that a refusal is now shown at all — this call used to be made and dropped.
  function handleToggleActive(user: AdminUser) {
    void Promise.resolve(onToggleActive(user.id)).catch((error: unknown) => {
      toast({
        variant: "destructive",
        title: user.active ? "Désactivation impossible" : "Activation impossible",
        description: describeUserAdminError(error),
      })
    })
  }

  const rows = users.filter(
    (u) =>
      (roleId === "all" || u.detail?.role_id === roleId) &&
      (query === "" ||
        (u.display_name + (u.detail?.email ?? "")).toLowerCase().includes(query.toLowerCase()))
  )
  const selectedUser = users.find((u) => u.id === selectedUserId) ?? null
  const columnCount = 4 + (showRoleColumn ? 1 : 0)

  return (
    <SectionCard bodyClassName="p-0">
      <div className="flex flex-wrap items-center gap-2 border-b border-border p-3">
        <div className="relative min-w-0 flex-1 basis-64">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" strokeWidth={1.75} />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={showIdentityColumns ? "Rechercher un nom ou un email…" : "Rechercher un nom…"}
            className="pl-9"
          />
        </div>
        {showRoleColumn && (
          <Select value={roleId} onValueChange={setRoleId}>
            <SelectTrigger className="w-[13rem]"><SelectValue placeholder="Rôle" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les rôles</SelectItem>
              {roles.map((r) => (
                <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Utilisateur</TableHead>
            {showRoleColumn && <TableHead>Rôle</TableHead>}
            <TableHead>Application</TableHead>
            <TableHead>Équipe fonctionnelle</TableHead>
            <TableHead>Statut</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.length === 0 ? (
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={columnCount} className="py-8 text-center whitespace-normal text-sm text-muted-foreground">
                Aucun utilisateur ne correspond à ces critères.
              </TableCell>
            </TableRow>
          ) : (
            rows.map((u) => {
              const activation = activationLabel(u)
              const isSelf = currentUser?.id === u.id
              return (
                <TableRow
                  key={u.id}
                  className={cn(
                    canOpenDetails && "cursor-pointer",
                    isHighlightActive && u.id === highlightUserId && "bg-primary/5"
                  )}
                  onClick={() => canOpenDetails && setManualSelectedUserId(u.id)}
                >
                  <TableCell>
                    <div className="flex min-w-0 items-center gap-3">
                      <Avatar className="shrink-0">
                        <AvatarImage src={u.avatar_url ?? undefined} alt={u.display_name} />
                        <AvatarFallback>{initials(u.display_name)}</AvatarFallback>
                      </Avatar>
                      <div className="min-w-0">
                        <p className="truncate font-medium">{u.display_name}</p>
                        {showIdentityColumns && (
                          <p className="truncate text-xs text-muted-foreground">{u.detail?.email}</p>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  {showRoleColumn && (
                    <TableCell>{getRoleName(u.detail?.role_id, roles)}</TableCell>
                  )}
                  <TableCell className="text-muted-foreground">{getPrimaryApplication(u) ?? "—"}</TableCell>
                  <TableCell className="text-muted-foreground">{functionalTeamLabels[u.functional_team]}</TableCell>
                  <TableCell><ActiveBadge active={u.active} /></TableCell>
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    {(canOpenDetails || activation !== null) && (
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon-sm" aria-label="Actions utilisateur">
                            <MoreHorizontal className="size-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          {canOpenDetails && (
                            <DropdownMenuItem onSelect={() => setManualSelectedUserId(u.id)}>
                              Voir les détails
                            </DropdownMenuItem>
                          )}
                          {/* Deactivation is refused on the actor's own account by
                              UserAccessPolicy: it can strip their own access, and roles are
                              seeded reference data, so a self-lockout takes the seeder to undo.
                              Activation carries no such risk and is not self-restricted. */}
                          {activation !== null && !(u.active && isSelf) && (
                            <DropdownMenuItem
                              className={u.active ? "text-destructive focus:text-destructive" : undefined}
                              onSelect={() => handleToggleActive(u)}
                            >
                              {activation}
                            </DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    )}
                  </TableCell>
                </TableRow>
              )
            })
          )}
        </TableBody>
      </Table>

      <UserDetailsSheet
        key={selectedUserId ?? "none"}
        user={selectedUser}
        capabilities={capabilities}
        onOpenChange={(open) => !open && closeSheet()}
        onSaveRole={onChangeRole}
        onSaveOrganizationalIdentity={onSaveOrganizationalIdentity}
        onSavePermissions={onSavePermissions}
        onToggleActive={onToggleActive}
      />
    </SectionCard>
  )
}

export { UsersTable }
