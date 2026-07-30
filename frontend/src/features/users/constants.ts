import type { components } from "@/types/api"

type FunctionalTeam = components["schemas"]["FunctionalTeam"]

const functionalTeamLabels: Record<FunctionalTeam, string> = {
  SUPPORT: "Support",
  CONFIGURATION: "Paramétrage",
}

export { functionalTeamLabels }
