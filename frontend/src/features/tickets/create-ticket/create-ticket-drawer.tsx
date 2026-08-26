"use client"

import { Loader2, Paperclip, X } from "lucide-react"

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { useCreateTicketForm } from "@/features/tickets/create-ticket/use-create-ticket-form"
import { useCreateTicketSubmission } from "@/features/tickets/create-ticket/use-create-ticket-submission"
import { IncidentFields } from "@/features/tickets/create-ticket/incident-fields"
import { AssignmentFields } from "@/features/tickets/create-ticket/assignment-fields"
import { BusinessFields } from "@/features/tickets/create-ticket/business-fields"
import { ReferencesFields } from "@/features/tickets/create-ticket/references-fields"
import { useCurrentUser } from "@/lib/auth"
import { getActionableApplications, getPrimaryApplication } from "@/services/api/auth"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]
type TicketCreateRequest = components["schemas"]["TicketCreateRequest"]

interface CreateTicketDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated: (payload: TicketCreateRequest) => Promise<TicketDetail>
  onUploadAttachment: (ticketId: string, file: File) => Promise<TicketDetail>
}

function CreateTicketDrawer({ open, onOpenChange, onCreated, onUploadAttachment }: CreateTicketDrawerProps) {
  const { data: currentUser } = useCurrentUser()
  const primaryApplication = currentUser ? getPrimaryApplication(currentUser) : null
  // Staffed applications only (primary/backup) — a read-only assignment grants reach without
  // staffing, and ticket creation is TicketCreationPolicy's, which requires the latter.
  const accessibleApplications = currentUser ? getActionableApplications(currentUser) : []
  const { values, setField, setApplication, addFiles, removeFile, reset, isValid } = useCreateTicketForm(
    primaryApplication ?? "FCI"
  )
  const { isSubmitting, progressLabel, isSlow, error, setError, submit } = useCreateTicketSubmission({
    onCreated,
    onUploadAttachment,
  })

  async function handleSubmit() {
    if (!isValid || !currentUser || isSubmitting) return
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
    // A failed submission leaves the drawer open on its error, so the user keeps what they typed.
    if (!(await submit(payload, values.files))) return
    reset()
    onOpenChange(false)
  }

  function handleOpenChange(next: boolean) {
    // Closing mid-submission would strand a ticket that is already being created and lose the
    // error if it fails — so ESC, the overlay and Annuler alike do nothing until it settles.
    if (isSubmitting) return
    // Re-seed the form (including the Application default) every time it opens or closes,
    // so a freshly-loaded currentUser is always reflected.
    setError(null)
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
          <Separator />
          <section className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Pièces jointes</h3>
            <Input
              type="file"
              multiple
              onChange={(e) => {
                const selected = Array.from(e.target.files ?? [])
                e.target.value = ""
                if (selected.length > 0) addFiles(selected)
              }}
            />
            {values.files.length > 0 && (
              <ul className="space-y-2">
                {values.files.map((file, index) => (
                  <li
                    key={`${file.name}-${index}`}
                    className="flex items-center justify-between gap-2 rounded-md border border-border px-3 py-2 text-sm"
                  >
                    <span className="flex min-w-0 items-center gap-2">
                      <Paperclip className="size-4 shrink-0 text-muted-foreground" />
                      <span className="truncate">{file.name}</span>
                    </span>
                    <Button variant="ghost" size="icon" onClick={() => removeFile(index)}>
                      <X className="size-4" />
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <SheetFooter className="border-t border-border">
          {error && <p className="text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => handleOpenChange(false)} disabled={isSubmitting}>
              Annuler
            </Button>
            <Button onClick={handleSubmit} disabled={!isValid || !currentUser || isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Création…
                </>
              ) : (
                "Créer le ticket"
              )}
            </Button>
          </div>
          {/* The button keeps a short, fixed label so it never resizes; what the backend is
              working on goes here, where a full sentence fits. */}
          {progressLabel && (
            <p className="text-right text-xs text-muted-foreground">
              {progressLabel}
              {isSlow && " C'est plus long que d'habitude — ne fermez pas cette fenêtre."}
            </p>
          )}
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

export { CreateTicketDrawer }
