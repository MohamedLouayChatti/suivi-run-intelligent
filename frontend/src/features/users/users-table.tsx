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
import { useRolesList } from "@/hooks/use-roles-list"
import type { components } from "@/types/api"

type UserResponse = components["schemas"]["UserResponse"]

function initials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase()
}

interface UsersTableProps {
  users: UserResponse[]
  highlightUserId?: string | null
  onChangeRole: (userId: string, roleId: string) => void
  onToggleActive: (userId: string) => void
  onSavePermissions: (userId: string, toGrant: string[], toRevoke: string[]) => void
}

function UsersTable({ users, highlightUserId, onChangeRole, onToggleActive, onSavePermissions }: UsersTableProps) {
  const { roles } = useRolesList()
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

  const rows = users.filter(
    (u) =>
      (roleId === "all" || u.role_ids.includes(roleId)) &&
      (query === "" || (u.display_name + u.email).toLowerCase().includes(query.toLowerCase()))
  )
  const selectedUser = users.find((u) => u.id === selectedUserId) ?? null

  return (
    <SectionCard bodyClassName="p-0">
      <div className="flex flex-wrap items-center gap-2 border-b border-border p-3">
        <div className="relative min-w-0 flex-1 basis-64">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" strokeWidth={1.75} />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Rechercher un nom ou un email…"
            className="pl-9"
          />
        </div>
        <Select value={roleId} onValueChange={setRoleId}>
          <SelectTrigger className="w-[13rem]"><SelectValue placeholder="Rôle" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les rôles</SelectItem>
            {roles.map((r) => (
              <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Utilisateur</TableHead>
            <TableHead>Rôle</TableHead>
            <TableHead>Application</TableHead>
            <TableHead>Équipe fonctionnelle</TableHead>
            <TableHead>Statut</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.length === 0 ? (
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={6} className="py-8 text-center whitespace-normal text-sm text-muted-foreground">
                Aucun utilisateur ne correspond à ces critères.
              </TableCell>
            </TableRow>
          ) : (
            rows.map((u) => (
              <TableRow
                key={u.id}
                className={cn("cursor-pointer", isHighlightActive && u.id === highlightUserId && "bg-primary/5")}
                onClick={() => setManualSelectedUserId(u.id)}
              >
                <TableCell>
                  <div className="flex min-w-0 items-center gap-3">
                    <Avatar className="shrink-0">
                      <AvatarImage src={u.avatar_url ?? undefined} alt={u.display_name} />
                      <AvatarFallback>{initials(u.display_name)}</AvatarFallback>
                    </Avatar>
                    <div className="min-w-0">
                      <p className="truncate font-medium">{u.display_name}</p>
                      <p className="truncate text-xs text-muted-foreground">{u.email}</p>
                    </div>
                  </div>
                </TableCell>
                <TableCell>{getRoleName(u, roles)}</TableCell>
                <TableCell className="text-muted-foreground">{getPrimaryApplication(u) ?? "—"}</TableCell>
                <TableCell className="text-muted-foreground">{functionalTeamLabels[u.functional_team]}</TableCell>
                <TableCell><ActiveBadge active={u.active} /></TableCell>
                <TableCell onClick={(e) => e.stopPropagation()}>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon-sm" aria-label="Actions utilisateur">
                        <MoreHorizontal className="size-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onSelect={() => setManualSelectedUserId(u.id)}>
                        Voir les détails
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className={u.active ? "text-destructive focus:text-destructive" : undefined}
                        onSelect={() => onToggleActive(u.id)}
                      >
                        {u.active ? "Désactiver" : "Activer"}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      <UserDetailsSheet
        key={selectedUserId ?? "none"}
        user={selectedUser}
        onOpenChange={(open) => !open && closeSheet()}
        onSaveRole={onChangeRole}
        onSavePermissions={onSavePermissions}
      />
    </SectionCard>
  )
}

export { UsersTable }
