"use client"

import { SectionCard } from "@/components/app/page"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useTheme, type Theme } from "@/hooks/use-theme"

const themeLabels: Record<Theme, string> = {
  light: "Clair",
  dark: "Sombre",
  system: "Système",
}

function AppearanceTab() {
  const { theme, setTheme } = useTheme()

  return (
    <SectionCard title="Apparence" description="Thème de l'interface">
      <div className="space-y-2">
        <Label>Thème</Label>
        <Select value={theme} onValueChange={(value) => setTheme(value as Theme)}>
          <SelectTrigger className="max-w-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(themeLabels) as Theme[]).map((key) => (
              <SelectItem key={key} value={key}>
                {themeLabels[key]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </SectionCard>
  )
}

export { AppearanceTab }
