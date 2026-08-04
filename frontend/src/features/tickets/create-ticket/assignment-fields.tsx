import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FormField } from "@/features/tickets/create-ticket/form-field"
import type { CreateTicketFormState } from "@/features/tickets/create-ticket/use-create-ticket-form"
import type { components } from "@/types/api"

type Application = components["schemas"]["Application"]

interface AssignmentFieldsProps {
  values: CreateTicketFormState
  setApplication: (application: CreateTicketFormState["application"]) => void
  /** The creating user's own applications (primary, + backup if any) — the ticket can only be
   * filed against an application they're assigned to. */
  accessibleApplications: Application[]
}

function AssignmentFields({ values, setApplication, accessibleApplications }: AssignmentFieldsProps) {
  return (
    <FormField label="Application">
      <Select
        value={values.application}
        onValueChange={(v) => setApplication(v as CreateTicketFormState["application"])}
        disabled={accessibleApplications.length < 2}
      >
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {accessibleApplications.map((app) => (
            <SelectItem key={app} value={app}>
              {app}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </FormField>
  )
}

export { AssignmentFields }
