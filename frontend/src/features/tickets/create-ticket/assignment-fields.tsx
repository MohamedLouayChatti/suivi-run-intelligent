import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FormField } from "@/features/tickets/create-ticket/form-field"
import { applicationOptions, functionalTeamLabels, functionalTeamOptions } from "@/features/tickets/constants"
import type { CreateTicketFormState } from "@/features/tickets/create-ticket/use-create-ticket-form"
import type { components } from "@/types/api"

type UserSummary = components["schemas"]["UserSummaryResponse"]

interface AssignmentFieldsProps {
  values: CreateTicketFormState
  setField: <K extends keyof CreateTicketFormState>(key: K, value: CreateTicketFormState[K]) => void
  users: UserSummary[]
}

function AssignmentFields({ values, setField, users }: AssignmentFieldsProps) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <FormField label="Application">
        <Select
          value={values.application}
          onValueChange={(v) => setField("application", v as CreateTicketFormState["application"])}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {applicationOptions.map((app) => (
              <SelectItem key={app} value={app}>
                {app}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FormField>

      <FormField label="Assigné à">
        <Select value={values.assigneeId} onValueChange={(v) => setField("assigneeId", v)}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Sélectionner un ingénieur" />
          </SelectTrigger>
          <SelectContent>
            {users.map((u) => (
              <SelectItem key={u.id} value={u.id}>
                {u.display_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FormField>

      <FormField label="Équipe fonctionnelle" className="col-span-2">
        <Select
          value={values.functionalTeam}
          onValueChange={(v) => setField("functionalTeam", v as CreateTicketFormState["functionalTeam"])}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {functionalTeamOptions.map((team) => (
              <SelectItem key={team} value={team}>
                {functionalTeamLabels[team]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FormField>
    </div>
  )
}

export { AssignmentFields }
