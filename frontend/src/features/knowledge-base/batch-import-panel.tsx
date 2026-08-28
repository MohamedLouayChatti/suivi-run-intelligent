"use client"

import { useRef, useState } from "react"
import { CheckCircle2, Download, FileUp, Loader2, RotateCcw, TriangleAlert, X } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { applicationOptions } from "@/features/tickets/constants"
import { FileFormatGuide } from "@/features/knowledge-base/file-format-guide"
import { ImportErrorReport } from "@/features/knowledge-base/import-error-report"
import {
  buildTemplateCsv,
  IMPORT_ACCEPTED_EXTENSIONS,
  IMPORT_MAX_MEGABYTES,
} from "@/features/knowledge-base/import-columns"
import { useBatchImport } from "@/features/knowledge-base/use-batch-import"
import { useTimedProgressSteps, type TimedProgressStep } from "@/hooks/use-timed-progress-steps"
import { usePermissions } from "@/lib/auth"
import type { BatchImportReport } from "@/services/api/knowledge-base"
import type { components } from "@/types/api"

type Application = components["schemas"]["Application"]

const MAX_UPLOAD_BYTES = IMPORT_MAX_MEGABYTES * 1024 * 1024

/**
 * What an import spends its time on, in the order the backend does it: the file is read into a
 * table, every row is validated, the tickets are committed in one transaction, and only then is
 * each one embedded into the knowledge base.
 *
 * That last phase is the long one and the only one that grows with the file — it costs a model
 * call per row — so it is the step that holds while the rest are paced to get out of its way. As
 * with ticket creation, these boundaries only decide when a message may *appear*; the response
 * always ends the sequence, wherever it had got to.
 *
 * One consequence worth knowing: a file rejected at validation comes back in a couple of seconds,
 * by which time this may be showing a later step than the backend actually reached. It is replaced
 * by the rejection report the instant it arrives, and no step ever claims to have completed.
 */
const importSteps: TimedProgressStep[] = [
  { after: 0, label: "Lecture du fichier…" },
  { after: 1500, label: "Vérification des lignes…" },
  { after: 5000, label: "Création des tickets…" },
  { after: 9000, label: "Indexation dans la base de connaissances…" },
]

/** An import is expected to be slow; this is where "slow" becomes worth remarking on. */
const IMPORT_SLOW_AFTER_MS = 45_000

/**
 * Two checks the backend also enforces, repeated here only to answer instantly instead of after a
 * round trip that uploads megabytes to say "wrong extension". Never a substitute for the backend's
 * own refusal — anything that gets past these is still validated there, in full.
 */
function rejectLocally(file: File): string | null {
  const dot = file.name.lastIndexOf(".")
  const extension = dot === -1 ? "" : file.name.slice(dot).toLowerCase()
  if (!IMPORT_ACCEPTED_EXTENSIONS.includes(extension as (typeof IMPORT_ACCEPTED_EXTENSIONS)[number])) {
    return `« ${file.name} » n'est pas un type de fichier accepté. Formats acceptés : ${IMPORT_ACCEPTED_EXTENSIONS.join(", ")}.`
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return `« ${file.name} » dépasse les ${IMPORT_MAX_MEGABYTES} Mo qu'un import accepte.`
  }
  return null
}

function BatchImportPanel() {
  const { isLoading: isLoadingUser, canImportForApplication } = usePermissions()
  // Mirrors BatchImportPolicy: every application for a holder of the breadth permission,
  // otherwise the single one the user runs. Permission-aware UX only — the route refuses an
  // application outside this list with a 403 regardless of what the form offers.
  const importableApplications = applicationOptions.filter(canImportForApplication)
  // COLORIS stays the default wherever it is still on offer, and is the whole list for a user
  // scoped to it; anyone else lands on the one application they may import for.
  const defaultApplication: Application | null =
    (importableApplications.includes("FCI") ? "FCI" : importableApplications[0]) ?? null
  const [chosenApplication, setChosenApplication] = useState<Application | null>(null)
  // Derived rather than stored, so the default follows GET /auth/me resolving without an effect
  // to reconcile the two — a choice the user has made always wins over it.
  const application = chosenApplication ?? defaultApplication
  const [file, setFile] = useState<File | null>(null)
  const [localError, setLocalError] = useState<string | null>(null)
  const [isDraggingOver, setIsDraggingOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { outcome, isImporting, runImport, reset } = useBatchImport()
  const { label: progressLabel, isSlow } = useTimedProgressSteps({
    steps: importSteps,
    isActive: isImporting,
    slowAfterMs: IMPORT_SLOW_AFTER_MS,
  })

  function selectFile(candidate: File | undefined) {
    if (!candidate) return
    reset()
    const problem = rejectLocally(candidate)
    setLocalError(problem)
    setFile(problem ? null : candidate)
    // Clearing the input is what makes re-picking the *same* filename fire onChange again, and
    // that is the normal path here: a rejected import is fixed in place and uploaded again under
    // the name it already had.
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  function clearSelection() {
    setFile(null)
    setLocalError(null)
    reset()
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  function downloadTemplate(target: Application) {
    const blob = new Blob([buildTemplateCsv(target)], { type: "text/csv;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = `modele_import_tickets_${target.toLowerCase()}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  // A null application means there is nothing to import *for*: either the profile that decides
  // that has not arrived yet, or the user holds the import permission without running any
  // application. The second is a real state — an assignment can be cleared, and the permission
  // can be granted directly to someone who has none — so it is answered rather than left as an
  // empty picker above a working upload button.
  if (application === null) {
    return isLoadingUser ? null : <NoImportableApplicationNotice />
  }

  return (
    <div className="space-y-6">
      <SectionCard
        title="Déposer un fichier de tickets"
        description="Les tickets sont créés puis indexés dans la base de connaissances, en une seule opération."
        action={
          <Button variant="outline" size="sm" onClick={() => downloadTemplate(application)}>
            <Download className="size-4" /> Télécharger un modèle
          </Button>
        }
      >
        <div className="space-y-4">
          <div className="grid gap-2 sm:max-w-xs">
            <Label htmlFor="import-application">Application</Label>
            <Select
              value={application}
              onValueChange={(value) => setChosenApplication(value as Application)}
              disabled={isImporting || importableApplications.length < 2}
            >
              <SelectTrigger id="import-application">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {importableApplications.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Elle s&apos;applique à toutes les lignes du fichier. Le modèle téléchargé est adapté à
              l&apos;application choisie.
              {importableApplications.length === 1 && (
                <> Vous importez pour l&apos;application dont vous avez la charge.</>
              )}
            </p>
          </div>

          <div
            onDragOver={(event) => {
              event.preventDefault()
              if (!isImporting) setIsDraggingOver(true)
            }}
            onDragLeave={() => setIsDraggingOver(false)}
            onDrop={(event) => {
              event.preventDefault()
              setIsDraggingOver(false)
              if (isImporting) return
              selectFile(event.dataTransfer.files[0])
            }}
            className={cn(
              "rounded-md border-2 border-dashed border-border bg-surface px-6 py-8 text-center transition-colors",
              isDraggingOver && "border-primary bg-primary/5",
              isImporting && "opacity-60",
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={IMPORT_ACCEPTED_EXTENSIONS.join(",")}
              className="hidden"
              onChange={(event) => selectFile(event.target.files?.[0])}
            />
            {file ? (
              <div className="flex flex-wrap items-center justify-center gap-3">
                <FileUp className="size-5 text-primary" strokeWidth={1.75} />
                <span className="text-sm font-medium">{file.name}</span>
                <span className="text-xs text-muted-foreground tabular">
                  {(file.size / 1024).toLocaleString("fr-FR", { maximumFractionDigits: 0 })} Ko
                </span>
                {!isImporting && (
                  <Button variant="ghost" size="sm" onClick={clearSelection}>
                    <X className="size-4" /> Retirer
                  </Button>
                )}
              </div>
            ) : (
              <>
                <FileUp className="mx-auto size-6 text-muted-foreground" strokeWidth={1.5} />
                <p className="mt-2 text-sm font-medium">
                  Glissez un fichier ici, ou{" "}
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isImporting}
                    className="text-primary underline-offset-2 hover:underline disabled:opacity-50"
                  >
                    parcourez vos fichiers
                  </button>
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {IMPORT_ACCEPTED_EXTENSIONS.join(", ")} — {IMPORT_MAX_MEGABYTES} Mo au maximum
                </p>
              </>
            )}
          </div>

          {localError && (
            <p className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm">
              <TriangleAlert className="mt-0.5 size-4 shrink-0 text-destructive" strokeWidth={2} />
              <span>{localError}</span>
            </p>
          )}

          <div className="flex flex-wrap items-center gap-3">
            <Button
              onClick={() => file && runImport(application, file)}
              disabled={!file || isImporting}
            >
              {isImporting ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Import en cours…
                </>
              ) : (
                <>
                  <FileUp className="size-4" /> Importer les tickets
                </>
              )}
            </Button>
            {isImporting && progressLabel && (
              <p className="text-xs text-muted-foreground">
                {progressLabel} Ne fermez pas cet onglet.
                {isSlow && " Sur un fichier volumineux, l'indexation peut prendre plusieurs minutes."}
              </p>
            )}
          </div>
        </div>
      </SectionCard>

      {outcome?.kind === "success" && (
        <ImportSuccessReport report={outcome.report} fileName={outcome.fileName} onReset={clearSelection} />
      )}
      {outcome?.kind === "rejected" && (
        <ImportErrorReport rejection={outcome.rejection} fileName={outcome.fileName} />
      )}
      {outcome?.kind === "failed" && (
        <SectionCard>
          <div className="flex items-start gap-3">
            <TriangleAlert className="mt-0.5 size-5 shrink-0 text-destructive" strokeWidth={2} />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium">Import interrompu</p>
              <p className="mt-1 text-sm text-muted-foreground">{outcome.message}</p>
            </div>
          </div>
        </SectionCard>
      )}

      <FileFormatGuide application={application} />
    </div>
  )
}

function ImportSuccessReport({
  report,
  fileName,
  onReset,
}: {
  report: BatchImportReport
  fileName: string
  onReset: () => void
}) {
  return (
    <SectionCard>
      <div className="flex items-start gap-3">
        <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-primary" strokeWidth={2} />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">
            {report.tickets_imported.toLocaleString("fr-FR")}{" "}
            {report.tickets_imported > 1 ? "tickets importés" : "ticket importé"} depuis {fileName}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Application {report.application}
            {report.sheet_name && <> — feuille « {report.sheet_name} »</>}.
          </p>

          <dl className="mt-4 grid gap-3 sm:grid-cols-3">
            <ReportStat label="Tickets créés" value={report.tickets_imported} />
            <ReportStat label="Indexés dans la base" value={report.knowledge_items_written} />
            <ReportStat label="Sans texte à indexer" value={report.skipped_empty_text} />
          </dl>

          {report.skipped_empty_text > 0 && (
            <p className="mt-3 text-xs text-muted-foreground">
              Les tickets sans texte exploitable existent bien, mais n&apos;apparaîtront pas dans les
              suggestions d&apos;incidents similaires&nbsp;: leur description ne contenait aucun terme
              indexable une fois nettoyée.
            </p>
          )}

          <p className="mt-3 text-xs text-muted-foreground">
            {report.recalculation_enqueued
              ? "Un recalcul complet du graphe de similarité a été lancé en arrière-plan : les suggestions se mettront à jour d'elles-mêmes une fois la passe terminée."
              : "Aucun recalcul n'a pu être lancé : les nouveaux tickets seront pris en compte à la prochaine passe planifiée."}
          </p>

          <Button variant="outline" size="sm" className="mt-4" onClick={onReset}>
            <RotateCcw className="size-4" /> Importer un autre fichier
          </Button>
        </div>
      </div>
    </SectionCard>
  )
}

function NoImportableApplicationNotice() {
  return (
    <SectionCard>
      <div className="flex items-start gap-3">
        <TriangleAlert className="mt-0.5 size-5 shrink-0 text-destructive" strokeWidth={2} />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">Aucune application à importer</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Un import est rattaché à une application, et vous n&apos;êtes affecté à aucune en tant
            qu&apos;application principale. Demandez à un administrateur de vous affecter une
            application principale, ou de vous accorder l&apos;import pour toutes les applications.
          </p>
        </div>
      </div>
    </SectionCard>
  )
}

function ReportStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border bg-surface p-3">
      <dt className="text-xs tracking-wide text-muted-foreground uppercase">{label}</dt>
      <dd className="mt-1 text-lg font-semibold tabular">{value.toLocaleString("fr-FR")}</dd>
    </div>
  )
}

export { BatchImportPanel }
