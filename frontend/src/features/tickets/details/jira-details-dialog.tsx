"use client"

import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]
type JiraDetailsUpdateRequest = components["schemas"]["JiraDetailsUpdateRequest"]

interface JiraDetailsDialogProps {
  ticket: TicketDetail
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (payload: JiraDetailsUpdateRequest) => void
}

function JiraDetailsDialog({ ticket, open, onOpenChange, onConfirm }: JiraDetailsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Informations Jira</DialogTitle>
          <DialogDescription>
            Indiquez si ce ticket nécessite un ticket Jira et ses références associées.
          </DialogDescription>
        </DialogHeader>
        {/* Mounted only while open so its state initializes fresh from `ticket` on every
            open, instead of syncing an already-mounted form via an effect. */}
        {open && (
          <JiraDetailsForm
            ticket={ticket}
            onCancel={() => onOpenChange(false)}
            onConfirm={(payload) => {
              onConfirm(payload)
              onOpenChange(false)
            }}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

interface JiraDetailsFormProps {
  ticket: TicketDetail
  onCancel: () => void
  onConfirm: (payload: JiraDetailsUpdateRequest) => void
}

function JiraDetailsForm({ ticket, onCancel, onConfirm }: JiraDetailsFormProps) {
  const [requiresJira, setRequiresJira] = useState(ticket.requires_jira)
  const [jiraId, setJiraId] = useState(ticket.jira_id ?? "")
  const [jiraDeliveryDate, setJiraDeliveryDate] = useState(ticket.jira_delivery_date ?? "")

  const canConfirm = !requiresJira || jiraId.trim().length > 0

  function handleConfirm() {
    if (!canConfirm) return
    onConfirm({
      requires_jira: requiresJira,
      jira_id: requiresJira ? jiraId.trim() : null,
      jira_delivery_date: requiresJira && jiraDeliveryDate ? jiraDeliveryDate : null,
    })
  }

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Switch
            id="requires-jira"
            checked={requiresJira}
            onCheckedChange={(checked) => {
              setRequiresJira(checked === true)
              if (checked !== true) {
                setJiraId("")
                setJiraDeliveryDate("")
              }
            }}
          />
          <Label htmlFor="requires-jira">Nécessite un ticket Jira</Label>
        </div>

        {requiresJira && (
          <>
            <div className="space-y-1.5">
              <Label htmlFor="jira-id">Identifiant Jira</Label>
              <Input id="jira-id" value={jiraId} onChange={(e) => setJiraId(e.target.value)} autoFocus />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="jira-delivery-date">Date de livraison Jira</Label>
              <Input
                id="jira-delivery-date"
                type="date"
                value={jiraDeliveryDate}
                onChange={(e) => setJiraDeliveryDate(e.target.value)}
              />
            </div>
          </>
        )}
      </div>

      <DialogFooter>
        <Button variant="outline" onClick={onCancel}>
          Annuler
        </Button>
        <Button onClick={handleConfirm} disabled={!canConfirm}>
          Enregistrer
        </Button>
      </DialogFooter>
    </>
  )
}

export { JiraDetailsDialog }
