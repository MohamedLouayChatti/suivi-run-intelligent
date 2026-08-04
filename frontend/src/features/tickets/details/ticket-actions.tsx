"use client"

import { useState } from "react"
import { Archive, ArchiveRestore, ArrowRightLeft, Lock, RotateCcw, SignalHigh, UserRoundCog } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
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
import { priorityOptions, transferDestinationOptions } from "@/features/tickets/constants"
import { ResolveTicketDialog } from "@/features/tickets/details/resolve-ticket-dialog"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]
type Priority = components["schemas"]["Priority"]
type TransferDestination = components["schemas"]["TransferDestination"]
type UserSummary = components["schemas"]["UserDirectoryResponse"]

interface TicketActionsProps {
  ticket: TicketDetail
  users: UserSummary[]
  canStart: boolean
  canResolve: boolean
  canResume: boolean
  canClose: boolean
  canTransfer: boolean
  canReassign: boolean
  canChangePriority: boolean
  canArchive: boolean
  canRestore: boolean
  onStart: () => void
  onResolve: (resolutionNotes: string) => void
  onResume: () => void
  onClose: () => void
  onArchive: () => void
  onRestore: () => void
  onReassign: (assigneeId: string) => void
  onChangePriority: (priority: Priority) => void
  onTransfer: (destination: TransferDestination) => void
}

function TicketActions({
  ticket,
  users,
  canStart,
  canResolve,
  canResume,
  canClose,
  canTransfer,
  canReassign,
  canChangePriority,
  canArchive,
  canRestore,
  onStart,
  onResolve,
  onResume,
  onClose,
  onArchive,
  onRestore,
  onReassign,
  onChangePriority,
  onTransfer,
}: TicketActionsProps) {
  const isArchived = ticket.archived_at !== null
  const [resolveOpen, setResolveOpen] = useState(false)
  const [pendingReassignee, setPendingReassignee] = useState<UserSummary | null>(null)

  return (
    <div className="flex flex-wrap items-center gap-2">
      {canStart && (
        <Button size="sm" onClick={onStart}>
          Démarrer
        </Button>
      )}
      {canResolve && (
        <>
          <Button size="sm" onClick={() => setResolveOpen(true)}>
            Résoudre
          </Button>
          <ResolveTicketDialog open={resolveOpen} onOpenChange={setResolveOpen} onConfirm={onResolve} />
        </>
      )}
      {canResume && (
        <Button size="sm" onClick={onResume}>
          <RotateCcw className="size-4" /> Reprendre
        </Button>
      )}
      {canClose && (
        <Button size="sm" variant="outline" onClick={onClose}>
          <Lock className="size-4" /> Fermer
        </Button>
      )}

      {canTransfer && (
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
      )}

      {canReassign && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button size="sm" variant="outline">
              <UserRoundCog className="size-4" /> Réaffecter
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {users.map((u) => (
              <DropdownMenuItem key={u.id} onSelect={() => setPendingReassignee(u)}>
                {u.display_name}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      )}

      {canChangePriority && (
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
      )}

      {isArchived
        ? canRestore && (
            <Button size="sm" variant="ghost" onClick={onRestore}>
              <ArchiveRestore className="size-4" /> Restaurer
            </Button>
          )
        : canArchive && (
            <Button size="sm" variant="ghost" onClick={onArchive}>
              <Archive className="size-4" /> Archiver
            </Button>
          )}

      <AlertDialog open={pendingReassignee !== null} onOpenChange={(open) => !open && setPendingReassignee(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Êtes-vous sûr ?</AlertDialogTitle>
            <AlertDialogDescription>
              Réaffecter ce ticket à {pendingReassignee?.display_name} ?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (pendingReassignee) onReassign(pendingReassignee.id)
                setPendingReassignee(null)
              }}
            >
              Confirmer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export { TicketActions }
