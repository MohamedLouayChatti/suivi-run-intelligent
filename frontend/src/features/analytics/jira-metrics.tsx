import { SectionCard } from "@/components/app/page"
import type { JiraMetrics } from "@/features/analytics/types"

interface JiraMetricsCardProps {
  metrics: JiraMetrics
}

function JiraMetricsCard({ metrics }: JiraMetricsCardProps) {
  const tiles = [
    { label: "Nécessite Jira", value: String(metrics.requiresJira) },
    { label: "Transférés vers Jira", value: String(metrics.transferredToJira) },
    { label: "En attente de livraison", value: String(metrics.awaitingDelivery) },
    { label: "Délai de livraison moyen", value: `${metrics.avgDeliveryDelayDays.toFixed(1)} j` },
  ]

  return (
    <SectionCard title="Indicateurs Jira" description="Suivi des tickets liés à Jira">
      <div className="grid grid-cols-2 gap-3">
        {tiles.map((tile) => (
          <div key={tile.label} className="rounded-lg border border-border bg-background p-4">
            <p className="text-xs font-medium text-muted-foreground">{tile.label}</p>
            <p className="mt-2 text-2xl font-semibold tabular-nums">{tile.value}</p>
          </div>
        ))}
      </div>
    </SectionCard>
  )
}

export { JiraMetricsCard }
