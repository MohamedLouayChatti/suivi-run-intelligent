import {
  categoryOptions,
  elementOptions,
  offerOptions,
  priorityOptions,
  transferDestinationOptions,
  versionOptions,
  vioAppOptions,
} from "@/features/tickets/constants"
import type { components } from "@/types/api"

type Application = components["schemas"]["Application"]

/**
 * The batch import's column contract, mirrored for display and for the downloadable template.
 *
 * This is a mirror, exactly like `lib/auth/permissions.ts` mirrors the backend's instance
 * policies: the contract itself lives in the backend (the column names and aliases in the ticket
 * module's `import_tickets/columns.py`, the accepted values and lifecycle rules in its
 * `record_parser.py`) and is enforced there on every upload. Nothing here validates anything — a
 * file is accepted or refused by the backend alone. What this buys is that an operator can read
 * what is expected *before* uploading, and can start from a file whose header row is already right.
 *
 * When the backend contract changes, change this too.
 */

const IMPORT_MAX_ROWS = 5000
const IMPORT_MAX_MEGABYTES = 10
const IMPORT_ACCEPTED_EXTENSIONS = [".csv", ".xlsx", ".xlsm"] as const

interface ImportColumn {
  /** The header as the contract spells it. Matching forgives case, accents and punctuation. */
  name: string
  /** What the column holds, in one sentence. */
  description: string
  /** Accepted values, when the column is not free text. */
  accepted?: string
  /** The value written into the downloadable template's example row. */
  example: string | ((application: Application) => string)
  /** Set when the column only applies to some applications. */
  scope?: string
}

const requiredColumns: ImportColumn[] = [
  {
    name: "titre",
    description: "Titre de l'incident. Ne doit pas être vide.",
    example: "Erreur 500 lors du calcul d'éligibilité",
  },
  {
    name: "description",
    description:
      "Description de l'incident. C'est ce texte, et lui seul, qui sert à retrouver les incidents similaires — plus il est précis, plus les suggestions le sont.",
    example: "Le calcul d'éligibilité renvoie une erreur 500 pour toute adresse du département 44.",
  },
  {
    name: "priorité",
    description: "Niveau de priorité de l'incident.",
    accepted: priorityOptions.join(", "),
    example: "P2",
  },
  {
    name: "catégorie",
    description: "Nature de l'incident.",
    accepted: categoryOptions.join(", "),
    example: "Bug",
  },
  {
    name: "équipe fonctionnelle",
    description: "Équipe en charge de l'incident.",
    accepted: "Support, Configuration ou Paramétrage (SUPPORT et CONFIGURATION sont aussi acceptés)",
    example: "Support",
  },
  {
    name: "acteur",
    description:
      "Nom d'affichage de la personne à qui le ticket est affecté. Il doit correspondre à un utilisateur déjà enregistré, et à un seul : un nom porté par deux personnes fait échouer l'import plutôt que de choisir au hasard. Les utilisateurs désactivés sont acceptés.",
    example: "Jean Dupont",
  },
  {
    name: "date d'ouverture",
    description: "Date de création de l'incident.",
    accepted: "ISO-8601 uniquement : 2025-10-01 ou 2025-10-01T14:30:00Z",
    example: "2025-10-01T09:15:00Z",
  },
]

const optionalColumns: ImportColumn[] = [
  {
    name: "statut",
    description:
      "Statut atteint par le ticket. Absente, la colonne vaut Ouvert. Chaque statut impose ses propres colonnes (voir les règles de cycle de vie).",
    accepted: "Ouvert, En cours, Transféré, Résolu, Clôturé ou Fermé (OPEN … CLOSED aussi acceptés)",
    example: "Résolu",
  },
  {
    name: "id genergy",
    description: "Identifiant du ticket dans GENERGY, s'il en a un.",
    example: "2510123456",
  },
  {
    name: "id oceane",
    description: "Identifiant du ticket dans OCEANE, s'il en a un.",
    example: "OCE-88214",
  },
  {
    name: "jira requis",
    description: "Indique qu'un ticket Jira accompagne l'incident.",
    accepted:
      "oui, non, vrai, faux, true, false — vide équivaut à non. Les valeurs 1 et 0 sont refusées.",
    example: "oui",
  },
  {
    name: "id jira",
    description:
      "Référence du ticket Jira. Obligatoire dès que « jira requis » vaut oui, interdite sinon.",
    example: "PROJ-1423",
  },
  {
    name: "date de livraison jira",
    description: "Date de livraison prévue côté Jira.",
    accepted: "Date ISO-8601 : 2025-11-15",
    example: "2025-11-15",
  },
  {
    name: "point d'attention",
    description: "Marque l'incident comme point d'attention opérationnel.",
    accepted: "oui, non, vrai, faux, true, false — vide équivaut à non.",
    example: "non",
  },
  {
    name: "offre",
    description: "Code de l'offre concernée.",
    accepted: `${offerOptions.length} codes du référentiel COLORIS (GCFTTX, NRAZO, MCIFO, RIPPD…)`,
    scope: "COLORIS uniquement",
    example: (application) => (application === "COLORIS" ? "GCFTTX" : ""),
  },
  {
    name: "version",
    description: "Version concernée.",
    accepted: versionOptions.join(", "),
    scope: "COLORIS uniquement",
    example: (application) => (application === "COLORIS" ? "V2" : ""),
  },
  {
    name: "élément",
    description: "Élément fonctionnel concerné.",
    accepted: elementOptions.join(", "),
    scope: "AERO uniquement",
    example: (application) => (application === "AERO" ? "API" : ""),
  },
  {
    name: "application vio",
    description: "Application VIO concernée.",
    accepted: vioAppOptions.join(", "),
    scope: "VIO uniquement",
    example: (application) => (application === "VIO" ? "FOP" : ""),
  },
  {
    name: "date de résolution",
    description: "Date à laquelle l'incident a été résolu.",
    accepted: "ISO-8601 : 2025-10-02 ou 2025-10-02T16:00:00Z",
    example: "2025-10-02T16:40:00Z",
  },
  {
    name: "date de clôture",
    description: "Date à laquelle l'incident a été clôturé.",
    accepted: "ISO-8601 : 2025-10-03 ou 2025-10-03T09:00:00Z",
    example: "",
  },
  {
    name: "actions réalisées",
    description: "Ce qui a été fait pour résoudre l'incident. Obligatoire pour un ticket résolu.",
    example: "Purge du cache Orange puis relance du connecteur d'éligibilité.",
  },
  {
    name: "transféré à",
    description: "Équipe ou application vers laquelle l'incident a été transféré.",
    accepted: transferDestinationOptions.join(", "),
    example: "",
  },
]

const allImportColumns: ImportColumn[] = [...requiredColumns, ...optionalColumns]

/** Columns the import refuses outright, each for a reason worth stating rather than just listing. */
const rejectedColumns: { name: string; reason: string }[] = [
  {
    name: "application",
    reason:
      "L'application est choisie au moment du dépôt et vaut pour tout le fichier — une colonne pourrait la contredire.",
  },
  { name: "id, identifiant", reason: "Les identifiants de ticket sont générés par l'import." },
  { name: "date de mise à jour", reason: "Cette date est tenue à jour par le ticket lui-même." },
  { name: "date d'archivage", reason: "L'archivage ne fait pas partie d'un import." },
]

/** Alternative header spellings accepted beyond case, accents and punctuation. */
const headerAliases: { column: string; aliases: string[] }[] = [
  { column: "date d'ouverture", aliases: ["date ouverture", "date de creation", "date creation"] },
  { column: "date de résolution", aliases: ["date resolution"] },
  { column: "date de clôture", aliases: ["date cloture", "date de fermeture", "date fermeture"] },
  { column: "date de livraison jira", aliases: ["date livraison jira", "date de livraison"] },
  { column: "point d'attention", aliases: ["point attention"] },
  { column: "actions réalisées", aliases: ["actions réalisés", "actions"] },
  { column: "id genergy", aliases: ["id ticket genergy", "genergy"] },
  { column: "id oceane", aliases: ["id ticket oceane", "oceane"] },
  { column: "offre", aliases: ["offre composée"] },
  { column: "catégorie", aliases: ["catégorie d'incident", "categorie incident"] },
  { column: "acteur", aliases: ["assigné à", "assignee"] },
  { column: "équipe fonctionnelle", aliases: ["équipe"] },
  { column: "application vio", aliases: ["app vio"] },
  { column: "transféré à", aliases: ["transféré vers", "transfert"] },
]

/** What each status requires and forbids. */
const lifecycleRules: { status: string; requires: string; forbids: string }[] = [
  {
    status: "Ouvert",
    requires: "Aucune colonne supplémentaire",
    forbids: "date de résolution, actions réalisées, date de clôture, transféré à",
  },
  {
    status: "En cours",
    requires: "Aucune colonne supplémentaire",
    forbids: "date de résolution, actions réalisées, date de clôture, transféré à",
  },
  {
    status: "Transféré",
    requires: "transféré à",
    forbids: "date de résolution, actions réalisées, date de clôture",
  },
  {
    status: "Résolu",
    requires: "date de résolution, actions réalisées",
    forbids: "date de clôture, transféré à",
  },
  {
    status: "Clôturé",
    requires:
      "date de clôture, plus soit (date de résolution + actions réalisées), soit transféré à — jamais les deux",
    forbids: "—",
  },
]

/** The application-specific columns, by application. */
const applicationFieldRules: Record<Application, string> = {
  FCI: "Aucune colonne spécifique : « offre », « version », « élément » et « application vio » doivent rester vides.",
  COLORIS:
    "« offre » et « version » sont obligatoires. « élément » et « application vio » doivent rester vides.",
  AERO: "« élément » est obligatoire. « offre », « version » et « application vio » doivent rester vides.",
  VIO: "« application vio » est obligatoire. « offre », « version » et « élément » doivent rester vides.",
}

function escapeCsvCell(value: string): string {
  return /[",\r\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value
}

/**
 * A model file: the header row exactly as the contract spells it, plus one example row filled in
 * for the chosen application — so a COLORIS template carries an offer and a version, and an FCI
 * one leaves those cells empty rather than showing values that would be refused.
 *
 * Written with a byte-order mark so Excel opens it as UTF-8 instead of mangling the accents; the
 * backend reads uploads as `utf-8-sig` and tolerates one.
 */
function buildTemplateCsv(application: Application): string {
  const header = allImportColumns.map((column) => escapeCsvCell(column.name)).join(",")
  const example = allImportColumns
    .map((column) =>
      escapeCsvCell(
        typeof column.example === "function" ? column.example(application) : column.example,
      ),
    )
    .join(",")
  return `﻿${header}\r\n${example}\r\n`
}

export {
  requiredColumns,
  optionalColumns,
  allImportColumns,
  rejectedColumns,
  headerAliases,
  lifecycleRules,
  applicationFieldRules,
  buildTemplateCsv,
  IMPORT_MAX_ROWS,
  IMPORT_MAX_MEGABYTES,
  IMPORT_ACCEPTED_EXTENSIONS,
}
export type { ImportColumn }
