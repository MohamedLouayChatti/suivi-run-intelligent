import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FormField } from "@/features/tickets/create-ticket/form-field"
import { priorityOptions, categoryOptions } from "@/features/tickets/constants"
import type { CreateTicketFormState } from "@/features/tickets/create-ticket/use-create-ticket-form"

interface IncidentFieldsProps {
  values: CreateTicketFormState
  setField: <K extends keyof CreateTicketFormState>(key: K, value: CreateTicketFormState[K]) => void
}

function IncidentFields({ values, setField }: IncidentFieldsProps) {
  return (
    <div className="space-y-4">
      <FormField label="Titre" htmlFor="title" required>
        <Input
          id="title"
          value={values.title}
          onChange={(e) => setField("title", e.target.value)}
          placeholder="Résumé court de l'incident"
        />
      </FormField>

      <FormField label="Description" htmlFor="description" required>
        <Textarea
          id="description"
          value={values.description}
          onChange={(e) => setField("description", e.target.value)}
          placeholder="Contexte, impact, étapes déjà réalisées…"
          rows={4}
        />
      </FormField>

      <div className="grid grid-cols-2 gap-4">
        <FormField label="Priorité">
          <Select value={values.priority} onValueChange={(v) => setField("priority", v as CreateTicketFormState["priority"])}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {priorityOptions.map((p) => (
                <SelectItem key={p} value={p}>
                  {p}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>

        <FormField label="Catégorie">
          <Select value={values.category} onValueChange={(v) => setField("category", v as CreateTicketFormState["category"])}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {categoryOptions.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>
      </div>
    </div>
  )
}

export { IncidentFields }
