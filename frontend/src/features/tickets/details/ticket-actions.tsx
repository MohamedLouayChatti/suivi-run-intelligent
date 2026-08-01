"use client"

import { Archive, ArchiveRestore, ArrowRightLeft, SignalHigh, UserRoundCog } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { priorityOptions, transferDestinationOptions } from "@/features/tickets/constants"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]
type Priority = components["schemas"]["Priority"]
type TransferDestination = components["schemas"]["TransferDestination"]
type UserSummary = components["schemas"]["UserSummaryResponse"]

interface TicketActionsProps {
  ticket: TicketDetail
  users: UserSummary[]
  onStart: () => void
  onResolve: () => void
  onArchive: () => void
  onRestore: () => void
  onReassign: (assigneeId: string) => void
  onChangePriority: (priority: Priority) => void
  onTransfer: (destination: TransferDestination) => void
}

function TicketActions({
  ticket,
  users,
  onStart,
  onResolve,
  onArchive,
  onRestore,
  onReassign,
  onChangePriority,
  onTransfer,
}: TicketActionsProps) {
  const isArchived = ticket.archived_at !== null

  return (
    <div className="flex flex-wrap items-center gap-2">
      {ticket.status === "OPEN" && (
        <Button size="sm" onClick={onStart}>
          Démarrer
        </Button>
      )}
      {ticket.status === "IN_PROGRESS" && (
        <Button size="sm" onClick={onResolve}>
          Résoudre
        </Button>
      )}

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button size="sm" variant="outline">
            <ArrowRightLeft className="size-4" /> Transférer
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {transferDestinationOptions.map((dest) => (
            <DropdownMenuItem key={dest} onSelect={() => onTransfer(dest)}>
              {dest}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button size="sm" variant="outline">
            <UserRoundCog className="size-4" /> Réaffecter
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {users.map((u) => (
            <DropdownMenuItem key={u.id} onSelect={() => onReassign(u.id)}>
              {u.display_name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button size="sm" variant="outline">
            <SignalHigh className="size-4" /> Priorité
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {priorityOptions.map((p) => (
            <DropdownMenuItem key={p} onSelect={() => onChangePriority(p)}>
              {p}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {isArchived ? (
        <Button size="sm" variant="ghost" onClick={onRestore}>
          <ArchiveRestore className="size-4" /> Restaurer
        </Button>
      ) : (
        <Button size="sm" variant="ghost" onClick={onArchive}>
          <Archive className="size-4" /> Archiver
        </Button>
      )}
    </div>
  )
}

export { TicketActions }
