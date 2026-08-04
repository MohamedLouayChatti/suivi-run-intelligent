import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { FormField } from "@/features/tickets/create-ticket/form-field"
import { offerOptions, versionOptions, elementOptions } from "@/features/tickets/constants"
import type { CreateTicketFormState } from "@/features/tickets/create-ticket/use-create-ticket-form"

interface BusinessFieldsProps {
  values: CreateTicketFormState
  setField: <K extends keyof CreateTicketFormState>(key: K, value: CreateTicketFormState[K]) => void
}

function BusinessFields({ values, setField }: BusinessFieldsProps) {
  return (
    <div className="space-y-4">
      {values.application === "COLORIS" && (
        <div className="grid grid-cols-2 gap-4">
          <FormField label="Offre" required>
            <Select
              value={values.offer || undefined}
              onValueChange={(v) => setField("offer", v as CreateTicketFormState["offer"])}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Sélectionner une offre" />
              </SelectTrigger>
              <SelectContent>
                {offerOptions.map((o) => (
                  <SelectItem key={o} value={o}>
                    {o}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>

          <FormField label="Version" required>
            <Select
              value={values.version || undefined}
              onValueChange={(v) => setField("version", v as CreateTicketFormState["version"])}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Sélectionner une version" />
              </SelectTrigger>
              <SelectContent>
                {versionOptions.map((v) => (
                  <SelectItem key={v} value={v}>
                    {v}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>
        </div>
      )}

      {values.application === "AERO" && (
        <FormField label="Élément" required>
          <Select
            value={values.element || undefined}
            onValueChange={(v) => setField("element", v as CreateTicketFormState["element"])}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Sélectionner un élément" />
            </SelectTrigger>
            <SelectContent>
              {elementOptions.map((e) => (
                <SelectItem key={e} value={e}>
                  {e}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>
      )}

      <div className="flex items-center gap-2">
        <Switch
          id="operational-highlight"
          checked={values.operationalHighlight}
          onCheckedChange={(checked) => setField("operationalHighlight", checked === true)}
        />
        <Label htmlFor="operational-highlight">Point d&apos;attention opérationnel</Label>
      </div>
    </div>
  )
}

export { BusinessFields }
