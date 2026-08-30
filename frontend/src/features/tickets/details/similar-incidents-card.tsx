"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowUpRight, ChevronDown, Loader2 } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { StatusBadge } from "@/components/app/status"
import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import type { SimilarIncident } from "@/services/api/knowledge-base"

/**
 * Past this many characters an expanded resolution stops informing and starts pushing the rest
 * of the sidebar off screen. The full text is one click away on the incident's own page, which
 * the row links to — so this truncates a preview, never the only copy.
 */
const RESOLUTION_PREVIEW_LIMIT = 320

interface SimilarIncidentsCardProps {
  incidents: SimilarIncident[]
  isLoading: boolean
  isError: boolean
  /**
   * The analysis behind this ticket has not produced results yet — it runs as a background job
   * once the ticket is created, so a reader who opens a brand-new ticket gets here first. Distinct
   * from `isLoading`, which is about this request; this is about the work the request asks after.
   */
  isAnalysisPending: boolean
  /** That work was still unfinished when we stopped waiting on it. */
  hasTimedOut: boolean
  /** The ticket being viewed — carried into each link so the target page can show the way back. */
  sourceTicketId: string
}

function SimilarIncidentsCard({
  incidents,
  isLoading,
  isError,
  isAnalysisPending,
  hasTimedOut,
  sourceTicketId,
}: SimilarIncidentsCardProps) {
  return (
    <SectionCard
      title="Incidents similaires"
      description="Incidents passés dont la description ressemble à celle-ci"
      bodyClassName="p-0"
    >
      {isLoading ? (
        <div className="space-y-4 px-5 py-4">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-full" />
            </div>
          ))}
        </div>
      ) : isError ? (
        <div className="px-5 py-6 text-sm text-muted-foreground">
          <p className="font-medium text-foreground">Recherche indisponible</p>
          <p className="mt-1 text-xs">
            La base de connaissances n&apos;a pas pu être interrogée. Réessayez en rechargeant la
            page&nbsp;; le ticket reste consultable normalement.
          </p>
        </div>
      ) : isAnalysisPending ? (
        <div className="px-5 py-6 text-sm text-muted-foreground">
          <p className="flex items-center gap-2 font-medium text-foreground">
            <Loader2 className="size-3.5 animate-spin" aria-hidden />
            Analyse en cours
          </p>
          <p className="mt-1 text-xs">
            La recherche d&apos;incidents similaires démarre à la création du ticket et prend
            quelques instants. Les résultats s&apos;afficheront ici automatiquement.
          </p>
        </div>
      ) : hasTimedOut ? (
        <div className="px-5 py-6 text-sm text-muted-foreground">
          <p className="font-medium text-foreground">Analyse non aboutie</p>
          <p className="mt-1 text-xs">
            Ce ticket n&apos;a pas encore été analysé. Il le sera lors de la prochaine
            reconstruction de la base de connaissances&nbsp;; rechargez la page plus tard pour voir
            les incidents similaires.
          </p>
        </div>
      ) : incidents.length === 0 ? (
        <div className="px-5 py-6 text-sm text-muted-foreground">
          <p className="font-medium text-foreground">Aucun incident similaire</p>
          <p className="mt-1 text-xs">
            Aucun incident déjà enregistré n&apos;est suffisamment proche de cette description.
          </p>
        </div>
      ) : (
        <ul className="divide-y divide-border">
          {incidents.map((incident) => (
            <SimilarIncidentRow
              key={incident.ticket_id}
              incident={incident}
              sourceTicketId={sourceTicketId}
            />
          ))}
        </ul>
      )}
    </SectionCard>
  )
}

function SimilarIncidentRow({
  incident,
  sourceTicketId,
}: {
  incident: SimilarIncident
  sourceTicketId: string
}) {
  const [isOpen, setIsOpen] = useState(false)
  const href = `/tickets/${incident.ticket_id}?from=${sourceTicketId}`
  const resolution = incident.resolution_notes?.trim()
  const isTruncated = (resolution?.length ?? 0) > RESOLUTION_PREVIEW_LIMIT
  const preview = isTruncated ? `${resolution!.slice(0, RESOLUTION_PREVIEW_LIMIT).trimEnd()}…` : resolution

  return (
    <li className="px-5 py-3.5">
      <Link href={href} className="group block focus-visible:outline-none">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-muted-foreground">
            {incident.ticket_id.slice(0, 8)}
          </span>
          <StatusBadge status={incident.status} />
          {incident.matched_reference ? (
            <Badge variant="info" className="ml-auto">
              Cité dans ce ticket
            </Badge>
          ) : (
            <span className="ml-auto text-xs tabular text-muted-foreground">
              {formatSimilarity(incident.similarity_score)}
            </span>
          )}
        </div>
        <p className="mt-1.5 flex items-start gap-1 text-sm font-medium group-hover:text-primary">
          <span className="min-w-0 flex-1">{incident.title}</span>
          <ArrowUpRight
            className="mt-0.5 size-3.5 shrink-0 text-muted-foreground transition-colors group-hover:text-primary"
            strokeWidth={2}
          />
        </p>
      </Link>

      {resolution ? (
        <Collapsible open={isOpen} onOpenChange={setIsOpen} className="mt-2">
          <CollapsibleTrigger className="flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground">
            <ChevronDown className={cn("size-3.5 transition-transform", isOpen && "rotate-180")} />
            {isOpen ? "Masquer la résolution" : "Voir la résolution"}
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="mt-2 rounded-md border border-border bg-surface px-3 py-2">
              <p className="text-xs leading-relaxed whitespace-pre-line text-muted-foreground">
                {preview}
              </p>
              {isTruncated && (
                <Link
                  href={href}
                  className="mt-2 inline-block text-xs font-medium text-primary hover:underline"
                >
                  Lire la résolution complète
                </Link>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>
      ) : (
        <p className="mt-2 text-xs text-muted-foreground">
          Cet incident n&apos;a pas encore de résolution consignée.
        </p>
      )}
    </li>
  )
}

/** The backend's cosine score, 0–1, shown the way a reader thinks about it. */
function formatSimilarity(score: number): string {
  return `${Math.round(score * 100)} % de similarité`
}

export { SimilarIncidentsCard }
