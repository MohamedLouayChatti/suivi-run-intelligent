"use client"

import { useState } from "react"
import { ChevronDown, FileSpreadsheet } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"
import {
  applicationFieldRules,
  headerAliases,
  IMPORT_ACCEPTED_EXTENSIONS,
  IMPORT_MAX_MEGABYTES,
  IMPORT_MAX_ROWS,
  lifecycleRules,
  optionalColumns,
  rejectedColumns,
  requiredColumns,
  type ImportColumn,
} from "@/features/knowledge-base/import-columns"
import type { components } from "@/types/api"

type Application = components["schemas"]["Application"]

interface FileFormatGuideProps {
  /** The application selected for the upload — its own rules are shown expanded, not buried. */
  application: Application
}

/**
 * Everything the uploaded file must contain, so that a validation error is always the
 * consequence of not having read this rather than of not having been told.
 *
 * Collapsed by default because it is long, and long is the point: the alternative to a wall of
 * detail here is the same detail discovered one rejected upload at a time. The three facts that
 * apply to every upload — the accepted formats, the limits, and the rules of the chosen
 * application — stay visible above the collapsed sections.
 */
function FileFormatGuide({ application }: FileFormatGuideProps) {
  return (
    <SectionCard
      title="Format attendu du fichier"
      description="À lire avant le premier dépôt. Toutes les règles ci-dessous sont vérifiées à l'import."
    >
      <div className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <FactTile label="Formats acceptés">
            {IMPORT_ACCEPTED_EXTENSIONS.join(", ")} — un CSV doit être encodé en UTF-8, un classeur
            Excel est lu sur sa première feuille.
          </FactTile>
          <FactTile label="Limites">
            {IMPORT_MAX_MEGABYTES} Mo au maximum, et {IMPORT_MAX_ROWS.toLocaleString("fr-FR")} lignes
            au maximum. Au-delà, découpez le fichier.
          </FactTile>
        </div>

        <div className="rounded-md border border-primary/30 bg-primary/5 p-4">
          <p className="text-xs font-medium tracking-wide text-primary uppercase">
            Colonnes spécifiques à {application}
          </p>
          <p className="mt-1.5 text-sm text-foreground">{applicationFieldRules[application]}</p>
        </div>

        <div className="rounded-md border border-border bg-surface p-4">
          <p className="text-sm font-medium">Le principe de l&apos;import</p>
          <ul className="mt-2 space-y-1.5 text-sm text-muted-foreground">
            <li className="flex gap-2">
              <span aria-hidden>•</span>
              <span>
                <strong className="font-medium text-foreground">Tout ou rien.</strong> Une seule
                ligne invalide fait refuser le fichier entier&nbsp;: aucun ticket n&apos;est créé, et
                toutes les erreurs vous sont rendues d&apos;un coup.
              </span>
            </li>
            <li className="flex gap-2">
              <span aria-hidden>•</span>
              <span>
                <strong className="font-medium text-foreground">Une application par fichier.</strong>{" "}
                Elle est choisie au moment du dépôt et s&apos;applique à toutes les lignes.
              </span>
            </li>
            <li className="flex gap-2">
              <span aria-hidden>•</span>
              <span>
                <strong className="font-medium text-foreground">Les doublons sont refusés</strong>,
                dans le fichier comme vis-à-vis de la base. Deux incidents sont considérés identiques
                lorsqu&apos;ils partagent à la fois « id genergy », « id oceane » et « description ».
                Redéposer un fichier déjà importé est donc sans effet plutôt que destructeur.
              </span>
            </li>
            <li className="flex gap-2">
              <span aria-hidden>•</span>
              <span>
                <strong className="font-medium text-foreground">Les dates sont en ISO-8601</strong>,
                uniquement&nbsp;: <code className="font-mono text-xs">2025-10-01</code> ou{" "}
                <code className="font-mono text-xs">2025-10-01T14:30:00Z</code>. Un format comme
                03/04/2025 est refusé, car il désigne deux jours différents selon le pays d&apos;origine
                du fichier. Dans Excel, une cellule mise au format Date convient telle quelle.
              </span>
            </li>
            <li className="flex gap-2">
              <span aria-hidden>•</span>
              <span>
                <strong className="font-medium text-foreground">Les intitulés sont tolérants.</strong>{" "}
                La casse, les accents et la ponctuation sont ignorés&nbsp;: « Date d&apos;ouverture »,
                « DATE D OUVERTURE » et « date douverture » désignent la même colonne. En revanche une
                colonne inconnue fait refuser le fichier, plutôt que d&apos;être ignorée en silence.
              </span>
            </li>
          </ul>
        </div>

        <ColumnSection
          title="Colonnes obligatoires"
          count={requiredColumns.length}
          columns={requiredColumns}
          defaultOpen
        />
        <ColumnSection
          title="Colonnes optionnelles"
          count={optionalColumns.length}
          columns={optionalColumns}
        />

        <GuideSection title="Règles de cycle de vie" subtitle="Selon la valeur de « statut »">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[36rem] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs tracking-wide text-muted-foreground uppercase">
                  <th className="py-2 pr-4 font-medium">Statut</th>
                  <th className="py-2 pr-4 font-medium">Colonnes exigées</th>
                  <th className="py-2 font-medium">Colonnes à laisser vides</th>
                </tr>
              </thead>
              <tbody>
                {lifecycleRules.map((rule) => (
                  <tr key={rule.status} className="border-b border-border/60 last:border-0">
                    <td className="py-2.5 pr-4 font-medium whitespace-nowrap">{rule.status}</td>
                    <td className="py-2.5 pr-4 text-muted-foreground">{rule.requires}</td>
                    <td className="py-2.5 text-muted-foreground">{rule.forbids}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            Les dates doivent aussi se suivre&nbsp;: « date de résolution » et « date de clôture » ne
            peuvent pas être antérieures à « date d&apos;ouverture », ni la clôture à la résolution.
          </p>
        </GuideSection>

        <GuideSection
          title="Colonnes refusées"
          subtitle="Leur présence fait refuser le fichier avant même la lecture des lignes"
        >
          <ul className="space-y-2.5">
            {rejectedColumns.map((column) => (
              <li key={column.name} className="text-sm">
                <code className="font-mono text-xs text-foreground">{column.name}</code>
                <span className="ml-2 text-muted-foreground">{column.reason}</span>
              </li>
            ))}
          </ul>
        </GuideSection>

        <GuideSection
          title="Intitulés alternatifs acceptés"
          subtitle="Au-delà de la casse, des accents et de la ponctuation, déjà tolérés partout"
        >
          <ul className="space-y-2">
            {headerAliases.map((entry) => (
              <li key={entry.column} className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-sm">
                <code className="font-mono text-xs font-medium">{entry.column}</code>
                <span className="text-xs text-muted-foreground">accepte aussi</span>
                {entry.aliases.map((alias) => (
                  <code key={alias} className="font-mono text-xs text-muted-foreground">
                    {alias}
                  </code>
                ))}
              </li>
            ))}
          </ul>
        </GuideSection>
      </div>
    </SectionCard>
  )
}

function FactTile({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <p className="flex items-center gap-1.5 text-xs tracking-wide text-muted-foreground uppercase">
        <FileSpreadsheet className="size-3.5" strokeWidth={1.75} />
        {label}
      </p>
      <p className="mt-1.5 text-sm text-foreground">{children}</p>
    </div>
  )
}

function GuideSection({
  title,
  subtitle,
  defaultOpen = false,
  badge,
  children,
}: {
  title: string
  subtitle?: string
  defaultOpen?: boolean
  badge?: React.ReactNode
  children: React.ReactNode
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className="rounded-md border border-border bg-surface"
    >
      <CollapsibleTrigger className="flex w-full items-center gap-2 px-4 py-3 text-left">
        <ChevronDown
          className={cn("size-4 shrink-0 text-muted-foreground transition-transform", isOpen && "rotate-180")}
        />
        <span className="text-sm font-medium">{title}</span>
        {badge}
        {subtitle && (
          <span className="ml-auto hidden text-xs text-muted-foreground sm:block">{subtitle}</span>
        )}
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="border-t border-border px-4 py-4">{children}</div>
      </CollapsibleContent>
    </Collapsible>
  )
}

function ColumnSection({
  title,
  count,
  columns,
  defaultOpen,
}: {
  title: string
  count: number
  columns: ImportColumn[]
  defaultOpen?: boolean
}) {
  return (
    <GuideSection
      title={title}
      defaultOpen={defaultOpen}
      badge={
        <Badge variant="secondary" className="bg-primary/10 text-primary">
          {count}
        </Badge>
      }
    >
      <ul className="space-y-4">
        {columns.map((column) => (
          <li key={column.name}>
            <div className="flex flex-wrap items-center gap-2">
              <code className="rounded bg-background px-1.5 py-0.5 font-mono text-xs font-medium">
                {column.name}
              </code>
              {column.scope && (
                <Badge variant="secondary" className="bg-foreground/10 text-foreground/70">
                  {column.scope}
                </Badge>
              )}
            </div>
            <p className="mt-1.5 text-sm text-muted-foreground">{column.description}</p>
            {column.accepted && (
              <p className="mt-1 text-xs text-muted-foreground">
                <span className="font-medium text-foreground/70">Valeurs acceptées&nbsp;:</span>{" "}
                {column.accepted}
              </p>
            )}
          </li>
        ))}
      </ul>
    </GuideSection>
  )
}

export { FileFormatGuide }
