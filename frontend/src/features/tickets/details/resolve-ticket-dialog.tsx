"use client"

import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface ResolveTicketDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (resolutionNotes: string) => void
}

function ResolveTicketDialog({ open, onOpenChange, onConfirm }: ResolveTicketDialogProps) {
  const [notes, setNotes] = useState("")

  function handleOpenChange(next: boolean) {
    if (!next) setNotes("")
    onOpenChange(next)
  }

  function handleConfirm() {
    if (!notes.trim()) return
    onConfirm(notes.trim())
    handleOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Résoudre le ticket</DialogTitle>
          <DialogDescription>
            Décrivez la résolution apportée. Ces notes sont requises et resteront attachées au ticket.
          </DialogDescription>
        </DialogHeader>
        <Textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Notes de résolution…"
          rows={5}
          autoFocus
        />
        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Annuler
          </Button>
          <Button onClick={handleConfirm} disabled={!notes.trim()}>
            Résoudre
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export { ResolveTicketDialog }
