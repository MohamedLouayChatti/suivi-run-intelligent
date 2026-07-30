import Link from "next/link"

import { SectionCard } from "@/components/app/page"
import { StatusBadge } from "@/components/app/status"
import { Button } from "@/components/ui/button"
import type { SimilarIncident } from "@/features/tickets/details/mock-similar-incidents"

interface SimilarIncidentsCardProps {
  incidents: SimilarIncident[]
}

function SimilarIncidentsCard({ incidents }: SimilarIncidentsCardProps) {
  return (
    <SectionCard
      title="Incidents similaires"
      description="Suggestions issues de la recherche sémantique (à venir)"
      bodyClassName="p-0"
    >
      {incidents.length === 0 ? (
        <div className="px-5 py-6 text-sm text-muted-foreground">
          <p>Aucun incident similaire trouvé.</p>
          <p className="mt-1 text-xs">
            Les suggestions d&apos;incidents similaires apparaîtront ici dès que le module
            d&apos;Incident Intelligence sera disponible.
          </p>
        </div>
      ) : (
        <ul className="divide-y divide-border">
          {incidents.map((incident) => (
            <li key={incident.id} className="space-y-2 px-5 py-3.5">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-muted-foreground">
                  {incident.id.slice(0, 8)}
                </span>
                <StatusBadge status={incident.status} />
              </div>
              <p className="truncate text-sm font-medium">{incident.title}</p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  {incident.similarity}% de similarité
                </span>
                <Button size="sm" variant="outline" asChild>
                  <Link href={`/tickets/${incident.id}`}>Voir</Link>
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  )
}

export { SimilarIncidentsCard }
