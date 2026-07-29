import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { components } from "@/types/api"

type Status = components["schemas"]["Status"]
type Priority = components["schemas"]["Priority"]

// Enterprise treatment: one hue (the app's orange) scaled by intensity to express
// urgency/activity, instead of scattering multiple semantic colors. Transferred/Closed
// (no longer active) break the scale into grey — same tones as the rest of the app's
// neutral/inactive states.
const statusConfig: Record<Status, { label: string; className: string }> = {
  RESOLVED: { label: "Résolu", className: "bg-primary/10 text-primary" },
  OPEN: { label: "Ouvert", className: "bg-primary/20 text-primary" },
  IN_PROGRESS: { label: "En cours", className: "bg-primary/30 text-primary" },
  TRANSFERRED: { label: "Transféré", className: "bg-foreground/10 text-foreground/70" },
  CLOSED: { label: "Clôturé", className: "bg-muted-foreground/10 text-muted-foreground" },
}

const priorityConfig: Record<Priority, { label: string; className: string }> = {
  P4: { label: "P4", className: "bg-primary/10 text-primary" },
  P3: { label: "P3", className: "bg-primary/20 text-primary" },
  P2: { label: "P2", className: "bg-primary/30 text-primary" },
  P1: { label: "P1", className: "bg-primary/40 text-primary" },
}

function StatusBadge({ status, className }: { status: Status; className?: string }) {
  const config = statusConfig[status]
  return (
    <Badge variant="secondary" className={cn(config.className, className)}>
      {config.label}
    </Badge>
  )
}

function PriorityBadge({ priority, className }: { priority: Priority; className?: string }) {
  const config = priorityConfig[priority]
  return (
    <Badge variant="secondary" className={cn(config.className, className)}>
      {config.label}
    </Badge>
  )
}

export { StatusBadge, PriorityBadge, statusConfig, priorityConfig }
