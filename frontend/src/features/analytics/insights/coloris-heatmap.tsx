import { Fragment } from "react"

import { SectionCard } from "@/components/app/page"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { versionOptions, formatEnumValue } from "@/features/tickets/constants"
import type { ColorisHeatmapCell } from "@/features/analytics/types"

interface ColorisHeatmapProps {
  cells: ColorisHeatmapCell[]
}

// Sequential magnitude, one hue (primary) fading into the muted surface — replaces the
// historical Excel matrix (rows = Offers, columns = Versions).
function ColorisHeatmap({ cells }: ColorisHeatmapProps) {
  const offers = Array.from(new Set(cells.map((c) => c.offer)))
  const max = Math.max(1, ...cells.map((c) => c.count))

  const cellFor = (offer: string, version: string) =>
    cells.find((c) => c.offer === offer && c.version === version)?.count ?? 0

  return (
    <SectionCard
      title="Matrice Offres × Versions"
      description="Nombre de tickets par offre et version — remplace la matrice Excel"
    >
      <div className="overflow-x-auto">
        <div
          className="grid min-w-[520px] gap-1"
          style={{ gridTemplateColumns: `140px repeat(${versionOptions.length}, minmax(56px, 1fr))` }}
        >
          <div />
          {versionOptions.map((version) => (
            <div key={version} className="pb-2 text-center text-xs font-medium text-muted-foreground">
              {formatEnumValue(version)}
            </div>
          ))}
          {offers.map((offer) => (
            <Fragment key={offer}>
              <div
                className="flex items-center truncate pr-3 text-xs font-medium text-muted-foreground"
                title={formatEnumValue(offer)}
              >
                {formatEnumValue(offer)}
              </div>
              {versionOptions.map((version) => {
                const count = cellFor(offer, version)
                const intensity = count / max
                return (
                  <Tooltip key={version}>
                    <TooltipTrigger asChild>
                      <div
                        className="flex aspect-square items-center justify-center rounded-md text-xs font-medium tabular-nums"
                        style={{
                          backgroundColor:
                            count === 0
                              ? "var(--color-muted)"
                              : `color-mix(in oklch, var(--color-primary) ${Math.max(15, Math.round(intensity * 90))}%, var(--color-muted))`,
                          color: intensity > 0.55 ? "var(--color-primary-foreground)" : "var(--color-foreground)",
                        }}
                      >
                        {count > 0 ? count : ""}
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      {offer} · {version} : {count} ticket{count > 1 ? "s" : ""}
                    </TooltipContent>
                  </Tooltip>
                )
              })}
            </Fragment>
          ))}
        </div>
      </div>
    </SectionCard>
  )
}

export { ColorisHeatmap }
