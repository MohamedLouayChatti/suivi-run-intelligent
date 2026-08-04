"use client"

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useCreateTicketForm } from "@/features/tickets/create-ticket/use-create-ticket-form"
import { IncidentFields } from "@/features/tickets/create-ticket/incident-fields"
import { AssignmentFields } from "@/features/tickets/create-ticket/assignment-fields"
import { BusinessFields } from "@/features/tickets/create-ticket/business-fields"
import { ReferencesFields } from "@/features/tickets/create-ticket/references-fields"
import { useCurrentUser } from "@/lib/auth"
import { getAccessibleApplications, getPrimaryApplication } from "@/services/api/auth"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]
type TicketCreateRequest = components["schemas"]["TicketCreateRequest"]

interface CreateTicketDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated: (payload: TicketCreateRequest) => Promise<TicketDetail>
}

function CreateTicketDrawer({ open, onOpenChange, onCreated }: CreateTicketDrawerProps) {
  const { data: currentUser } = useCurrentUser()
  const primaryApplication = currentUser ? getPrimaryApplication(currentUser) : null
  const accessibleApplications = currentUser ? getAccessibleApplications(currentUser) : []
  const { values, setField, setApplication, reset, isValid } = useCreateTicketForm(primaryApplication ?? "FCI")

  async function handleSubmit() {
    if (!isValid || !currentUser) return
    // The creator is always the assignee and their own functional team, both fixed by the
    // backend/business rules — never user-editable fields on this form.
    const payload: TicketCreateRequest = {
      title: values.title.trim(),
      description: values.description.trim(),
      priority: values.priority,
      application: values.application,
      category: values.category,
      functional_team: currentUser.functionalTeam,
      genergy_id: values.genergyId || null,
      oceane_id: values.oceaneId || null,
      jira_id: values.jiraId || null,
      jira_delivery_date: values.jiraDeliveryDate || null,
      requires_jira: values.requiresJira,
      operational_highlight: values.operationalHighlight,
      offer: values.offer || null,
      version: values.version || null,
      element: values.element || null,
      vio_app: values.vioApp || null,
    }
    await onCreated(payload)
    reset()
    onOpenChange(false)
  }

  function handleOpenChange(next: boolean) {
    // Re-seed the form (including the Application default) every time it opens or closes,
    // so a freshly-loaded currentUser is always reflected.
    reset()
    onOpenChange(next)
  }

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetContent className="flex w-full flex-col gap-0 data-[side=right]:sm:max-w-xl">
        <SheetHeader className="border-b border-border">
          <SheetTitle>Créer un ticket</SheetTitle>
          <SheetDescription>
            Consignez un incident pris en charge sur un système externe.
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 space-y-6 overflow-y-auto px-4 py-4">
          <section className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Incident</h3>
            <IncidentFields values={values} setField={setField} />
          </section>
          <Separator />
          <section className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Affectation</h3>
            <AssignmentFields values={values} setApplication={setApplication} accessibleApplications={accessibleApplications} />
          </section>
          <Separator />
          <section className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Métier</h3>
            <BusinessFields values={values} setField={setField} />
          </section>
          <Separator />
          <section className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Références</h3>
            <ReferencesFields values={values} setField={setField} />
          </section>
        </div>

        <SheetFooter className="flex-row justify-end border-t border-border">
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Annuler
          </Button>
          <Button onClick={handleSubmit} disabled={!isValid || !currentUser}>
            Créer le ticket
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

export { CreateTicketDrawer }
