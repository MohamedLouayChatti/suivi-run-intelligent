import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FormField } from "@/features/tickets/create-ticket/form-field"
import { vioAppOptions } from "@/features/tickets/constants"
import type { CreateTicketFormState } from "@/features/tickets/create-ticket/use-create-ticket-form"

interface ReferencesFieldsProps {
  values: CreateTicketFormState
  setField: <K extends keyof CreateTicketFormState>(key: K, value: CreateTicketFormState[K]) => void
}

function ReferencesFields({ values, setField }: ReferencesFieldsProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Identifiant Oceane" htmlFor="oceane-id">
          <Input
            id="oceane-id"
            value={values.oceaneId}
            onChange={(e) => setField("oceaneId", e.target.value)}
          />
        </FormField>

        <FormField label="Identifiant Genergy" htmlFor="genergy-id">
          <Input
            id="genergy-id"
            value={values.genergyId}
            onChange={(e) => setField("genergyId", e.target.value)}
          />
        </FormField>
      </div>

      <div className="flex items-center gap-2">
        <Switch
          id="requires-jira"
          checked={values.requiresJira}
          onCheckedChange={(checked) => {
            setField("requiresJira", checked === true)
            // The backend rejects a jira_id/jira_delivery_date when requires_jira is false —
            // clear both so a value entered before un-checking can't linger into the request.
            if (checked !== true) {
              setField("jiraId", "")
              setField("jiraDeliveryDate", "")
            }
          }}
        />
        <Label htmlFor="requires-jira">Nécessite un ticket Jira</Label>
      </div>

      {values.requiresJira && (
        <>
          <FormField label="Identifiant Jira" htmlFor="jira-id" required>
            <Input
              id="jira-id"
              value={values.jiraId}
              onChange={(e) => setField("jiraId", e.target.value)}
            />
          </FormField>

          <FormField label="Date de livraison Jira" htmlFor="jira-delivery-date">
            <Input
              id="jira-delivery-date"
              type="date"
              value={values.jiraDeliveryDate}
              onChange={(e) => setField("jiraDeliveryDate", e.target.value)}
            />
          </FormField>
        </>
      )}

      {values.application === "VIO" && (
        <FormField label="Application VIO" required>
          <Select
            value={values.vioApp || undefined}
            onValueChange={(v) => setField("vioApp", v as CreateTicketFormState["vioApp"])}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Sélectionner une application VIO" />
            </SelectTrigger>
            <SelectContent>
              {vioAppOptions.map((app) => (
                <SelectItem key={app} value={app}>
                  {app}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>
      )}
    </div>
  )
}

export { ReferencesFields }
