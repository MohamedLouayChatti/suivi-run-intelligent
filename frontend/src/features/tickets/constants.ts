import type { components } from "@/types/api"

type Application = components["schemas"]["Application"]
type Category = components["schemas"]["Category"]
type FunctionalTeam = components["schemas"]["FunctionalTeam"]
type Priority = components["schemas"]["Priority"]
type Status = components["schemas"]["Status"]
type Version = components["schemas"]["Version"]
type Element = components["schemas"]["Element"]
type VioApp = components["schemas"]["VioApp"]
type Offer = components["schemas"]["Offer"]
type TransferDestination = components["schemas"]["TransferDestination"]

const applicationOptions: Application[] = ["FCI", "COLORIS", "AERO", "VIO"]

const priorityOptions: Priority[] = ["P1", "P2", "P3", "P4"]

const activeStatusOptions: Status[] = ["OPEN", "IN_PROGRESS", "RESOLVED"]

const functionalTeamLabels: Record<FunctionalTeam, string> = {
  SUPPORT: "Support",
  CONFIGURATION: "Paramétrage",
}

const functionalTeamOptions: FunctionalTeam[] = ["SUPPORT", "CONFIGURATION"]

const categoryOptions: Category[] = [
  "Bug",
  "Anomalie applicatif",
  "Manque d'information",
  "Assistance client",
  "Bon usage",
  "vide",
  "Synchronisation des données",
  "Opération de service",
  "Habilitation",
  "Hors périmètre",
]

const versionOptions: Version[] = ["V1", "V2", "V3", "V4", "V5"]

const elementOptions: Element[] = [
  "API",
  "Connexion impossible",
  "Cuivre IHM",
  "Données absentes ou incorrectes",
  "Droit Habilitation",
  "Fibre IHM FTTE",
  "Fibre IHM FTTH",
  "Fibre IHM FTTO",
  "Message d'erreur ou résultat inattendu",
  "Orange-Eligibility KO",
  "Retour sur ticket",
]

const vioAppOptions: VioApp[] = ["FOP", "PARC", "SAGIC", "VIGIE"]

// Offer is a ~180-value VIO-specific code list; only the most common codes are
// surfaced here to keep the select usable. The full enum still validates on submit.
const offerOptions: Offer[] = [
  "GCFTTX",
  "NRAZO",
  "MCIFO",
  "GCRIA",
  "TEMP",
  "GCNRASR",
  "MUTUFTTH",
  "IPCNX",
  "RIPPD",
  "INFPR",
  "PRMUT",
  "DEGPG",
  "MUTMD",
  "HBNRO",
  "MADPC",
  "GCBLO",
]

const transferDestinationOptions: TransferDestination[] = [
  "Support FCI",
  "Paramétrage FCI",
  "Support COLORIS",
  "Paramétrage COLORIS",
  "AERO",
  "VIO",
  "EEP",
  "CLIP",
  "BANCO",
  "Ulysse",
  "ACACIA",
  "SantaFE",
  "Proxima",
  "Habilitation",
]

export {
  applicationOptions,
  priorityOptions,
  activeStatusOptions,
  functionalTeamLabels,
  functionalTeamOptions,
  categoryOptions,
  versionOptions,
  elementOptions,
  vioAppOptions,
  offerOptions,
  transferDestinationOptions,
}
