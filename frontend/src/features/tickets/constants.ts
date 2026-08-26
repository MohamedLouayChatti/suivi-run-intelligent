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

// Statuses that represent completed work — these belong to History, never to the active
// Tickets page (see the comment in filter-tickets.ts).
const completedStatusOptions: Status[] = ["CLOSED", "TRANSFERRED"]

const functionalTeamLabels: Record<FunctionalTeam, string> = {
  SUPPORT: "SN3",
  CONFIGURATION: "Paramétrage",
}

const functionalTeamOptions: FunctionalTeam[] = ["SUPPORT", "CONFIGURATION"]

// AERO and VIO are staffed by SN3 alone — they have no Paramétrage team, which is the same
// fact the transfer destinations encode by giving each of them one entry where FCI and COLORIS
// get one per team. The backend refuses the other combination outright (both on the User and on
// the Ticket), so this list only stops a form from offering a choice that would be rejected.
const supportOnlyApplications: Application[] = ["AERO", "VIO"]

function functionalTeamOptionsFor(application: Application | ""): FunctionalTeam[] {
  return functionalTeamOptionsForApplications([application])
}

// The rule is about *any* application a person holds, not just the one they run: a backup covers
// the application for real, so a Paramétrage engineer backing up AERO describes the same team that
// does not exist. The single-application form above is the signup case, where one is all that is
// ever declared.
function functionalTeamOptionsForApplications(
  applications: readonly (Application | "" | null)[]
): FunctionalTeam[] {
  const held = applications.filter((a): a is Application => a !== "" && a !== null)
  if (held.some((a) => supportOnlyApplications.includes(a))) return ["SUPPORT"]
  return functionalTeamOptions
}

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
  "Infrastructure",
]

const versionOptions: Version[] = [
  "V1",
  "V2",
  "V3",
  "V4",
  "V5",
  "V6",
  "V1R4",
  "V1R6",
  "V14",
  "V15",
  "V32",
  "V16",
  "V42",
  "V41",
  "V50",
  "V22",
  "Not Specified",
]

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

// Version and Offer both carry a "Not Specified" member (backend enum value, sent/received as-is
// over the API — see app/modules/ticket_management/domain/enums/{version,offer}.py) — the one
// member of either enum that is an English phrase rather than a code, so unlike "V2" or "GCFTTX"
// it needs a display translation. The import file's accepted-spellings text still shows the raw
// value, since that's what a user must literally type in the file for the backend to accept it.
function formatEnumValue(value: string): string {
  return value === "Not Specified" ? "Non spécifié" : value
}

// TransferDestination (backend enum, sent/received as-is over the API — see
// app/modules/ticket_management/domain/enums/transfer_destination.py) spells two of its members
// with the business's old "Support" name for the team the org now calls SN3. Display-only, like
// formatEnumValue above: the value posted to `transferTicket`/read back from ticket history stays
// "Support FCI"/"Support COLORIS" unchanged.
const TRANSFER_DESTINATION_LABELS: Partial<Record<TransferDestination, string>> = {
  "Support FCI": "SN3 FCI",
  "Support COLORIS": "SN3 COLORIS",
}

function formatTransferDestination(value: string): string {
  return TRANSFER_DESTINATION_LABELS[value as TransferDestination] ?? value
}

// ~190-value COLORIS offer code list; the full enum is rendered through a searchable
// Combobox (not a plain Select) so this many options stays usable.
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
  "RFHLA",
  "PCOZO",
  "MUTSP",
  "RFHCA",
  "RFHGD",
  "RFHAU",
  "RFHBR",
  "REBTD",
  "RFHMO",
  "DGRPG",
  "RFHGE",
  "REGSC",
  "REMNU",
  "REVTD",
  "RFHVE",
  "RELOA",
  "RFHLO",
  "SNCFR",
  "RFPBR",
  "NROPB",
  "RFRBR",
  "RFHAR",
  "RFHAX",
  "RFHBC",
  "RFHCM",
  "RFHGI",
  "RFHMA",
  "RFHOM",
  "REMAY",
  "RFRAX",
  "PCNAO",
  "REART",
  "REAXT",
  "REBFC",
  "RECMT",
  "REGTD",
  "REOMT",
  "RFROM",
  "RFRGI",
  "RFHSY",
  "RFHVI",
  "RFRPS",
  "REAPS",
  "RFHVT",
  "REVAR",
  "REVIE",
  "REDSN",
  "LNPMB",
  "LPMCD",
  "RFPAX",
  "RFIAX",
  "RFLAX",
  "RE1AX",
  "REHAU",
  "RFPMA",
  "RFPAR",
  "RFPBC",
  "RFPOM",
  "RFPLA",
  "RFRLA",
  "RELTD",
  "ROPDM_MONU",
  "RFRGD",
  "ROPDM_VTHD",
  "ROPDM_OMTD",
  "ROPDM_AXTD",
  "ROPDM_MAYE",
  "RFULA",
  "RFRAU",
  "RFPVT",
  "RFPMO",
  "RFHRT",
  "ROPDM_ATHD_HEB",
  "ROPDM_ATHD_LC",
  "RONZO_THDB",
  "REDAX",
  "RERRT",
  "RFPVI",
  "RFPVE",
  "RFPLN",
  "RFPGD",
  "RFPGN",
  "RFPDS",
  "RFPCM",
  "RFPPS",
  "RFPAU",
  "RFNRA_CAPS",
  "LPMSP",
  "RFNRA_THDB",
  "RFNRA_LTHD",
  "RFNRA_VTHD",
  "RORAC_IND_GTHD",
  "RORAC_IRU_GTHD",
  "RFRAR",
  "RFCOL_GTHD",
  "RFRVT",
  "CSMFON",
  "RFHKF",
  "RFPKF",
  "RECHD",
  "ROPDM_CORS",
  "NRA_NRO_RIP",
  "ROPAP_HASF",
  "ROHEB_HASF",
  "RORAC_HASF",
  "RFMUT_HASF",
  "ROPDM_HASF",
  "ROHPO_AXTD",
  "ROHPO_VTHD",
  "BSNRO",
  "RFMUT_YANA",
  "RORAC_GERS",
  "ROHEB_YANA",
  "ROHPA_HASF",
  "ROHEB_LOAN",
  "ROPAP_YANA",
  "RORAC_YANA",
  "ROPAP_MAYO",
  "GCBLO_IFP",
  "ROHPO_LTHD",
  "RONZO_HASF",
  "DSRIT",
  "RVOPT",
  "HEBEP",
  "ROHEB_GDHD",
  "CMS_SUPPORT",
  "OPTSV",
  "NRA_NRO_RIP_2",
  "EVOL_GC",
  "ROGCI_MONU",
  "ROGCI_AXTD",
  "ROGCI_CMTD",
  "ROGCI_HASF",
  "ROGCI_VTHD",
  "ROGCI_OMTD",
  "ROGCI_GERS",
  "ROGCI_YANA",
  "ROGCI_RRTH",
  "ROGCI_ARTD",
  "ROGCI_KOUR",
  "ROGCI_THDB",
  "ROGCI_BFCF",
  "ROGCI_GTHD",
  "ROGCI_CAPS",
  "ROGCI_ATHD",
  "ROGCI_MAYE",
  "ROGCI_SY79",
  "ROGCI_VIEN",
  "ROHEB_THDB",
  "ROHEB_SY79",
  "ROHEB_VIEN",
  "ROHEB_LTHD",
  "ROHEB_ARTD",
  "ROHEB_AXTD",
  "ROHEB_BFCF",
  "ROHEB_VTHD",
  "ROHEB_CAPS",
  "ROHEB_GTHD",
  "ROHEB_YANA22",
  "ROHEB_GERS",
  "ROHEB_MAYE",
  "ROHEB_RRTH",
  "ROHEB_MONU",
  "CPMFO",
  "DEPOS",
  "ITDMX",
  "ROGCI_RTBM",
  "ROHEB_RTBM",
  "ROHPO_RTBM",
  "ROHPO_RTRM",
  "Not Specified",
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
  "Équipe Développement",
]

export {
  applicationOptions,
  priorityOptions,
  activeStatusOptions,
  completedStatusOptions,
  functionalTeamLabels,
  functionalTeamOptions,
  functionalTeamOptionsFor,
  functionalTeamOptionsForApplications,
  supportOnlyApplications,
  formatEnumValue,
  formatTransferDestination,
  categoryOptions,
  versionOptions,
  elementOptions,
  vioAppOptions,
  offerOptions,
  transferDestinationOptions,
}
