"use client"

import { useMemo, useRef, useState } from "react"
import { Check, ChevronRight, Lock } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Label } from "@/components/ui/label"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"
import { groupPermissions, type PermissionGraph } from "@/lib/auth"
import type { components } from "@/types/api"

type PermissionResponse = components["schemas"]["PermissionResponse"]

const EMPTY_SET: ReadonlySet<string> = new Set()

interface PermissionGroupListProps {
  permissions: readonly PermissionResponse[]
  /** Mirrors the backend's dependency graph — see `lib/auth/permission-graph.ts`. */
  graph: PermissionGraph
  /**
   * The set a permission is checked against, both for its own tick mark and for whether its
   * prerequisites are satisfied. Callers that stage edits locally (the user sheet) pass the
   * staged set; callers that write straight through (the role panel) pass what is actually
   * granted — either way, "checked" and "prerequisites satisfied" read the same set, which is
   * what keeps a permission's checkbox and its requirement badges from ever disagreeing.
   */
  heldIds: ReadonlySet<string>
  isEditable: (permission: PermissionResponse, checked: boolean) => boolean
  onToggle: (permission: PermissionResponse, checked: boolean) => void
  renderTrailing?: (permission: PermissionResponse, checked: boolean) => React.ReactNode
  /** Prefixes each checkbox/label `id` so two instances on the same page never collide. */
  idPrefix: string
  className?: string
}

/**
 * The permission catalog grouped by module (`lib/auth/permission-groups.ts`), each permission's
 * direct requirements shown as small badges next to its name instead of a "Nécessite …"
 * sentence. A held requirement is a quiet confirmation; a missing one is a click target that
 * opens its group and scrolls it into view — nobody has to scan the full 40-permission list by
 * eye to find what a locked checkbox is waiting on.
 */
function PermissionGroupList({
  permissions,
  graph,
  heldIds,
  isEditable,
  onToggle,
  renderTrailing,
  idPrefix,
  className,
}: PermissionGroupListProps) {
  const groups = useMemo(() => groupPermissions(permissions, graph), [permissions, graph])
  const byId = useMemo(() => new Map(permissions.map((permission) => [permission.id, permission])), [permissions])
  const groupIdOf = useMemo(
    () => new Map(groups.flatMap((group) => group.permissions.map((permission) => [permission.id, group.id]))),
    [groups]
  )

  const [collapsedGroups, setCollapsedGroups] = useState<ReadonlySet<string>>(EMPTY_SET)
  const [highlightedId, setHighlightedId] = useState<string | null>(null)
  const rowRefs = useRef(new Map<string, HTMLLIElement>())
  const highlightTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)

  function setGroupOpen(groupId: string, open: boolean) {
    setCollapsedGroups((prev) => {
      const next = new Set(prev)
      if (open) next.delete(groupId)
      else next.add(groupId)
      return next
    })
  }

  function jumpTo(targetId: string) {
    const targetGroup = groupIdOf.get(targetId)
    if (targetGroup) setGroupOpen(targetGroup, true)

    setHighlightedId(targetId)
    if (highlightTimeout.current) clearTimeout(highlightTimeout.current)
    highlightTimeout.current = setTimeout(() => setHighlightedId(null), 1600)

    // Give the collapsible a tick to expand and lay out before scrolling to it.
    setTimeout(() => rowRefs.current.get(targetId)?.scrollIntoView({ behavior: "smooth", block: "center" }), 50)
  }

  return (
    <div className={cn("divide-y divide-border", className)}>
      {groups.map((group) => {
        const grantedCount = group.permissions.filter((permission) => heldIds.has(permission.id)).length
        const open = !collapsedGroups.has(group.id)
        return (
          <Collapsible key={group.id} open={open} onOpenChange={(next) => setGroupOpen(group.id, next)}>
            <CollapsibleTrigger className="flex w-full items-center justify-between gap-2 px-5 py-2.5 text-left transition-colors hover:bg-surface">
              <span className="flex items-center gap-1.5 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                <ChevronRight className={cn("size-3.5 shrink-0 transition-transform", open && "rotate-90")} />
                {group.label}
              </span>
              <span className="tabular shrink-0 text-xs text-muted-foreground">
                {grantedCount}/{group.permissions.length}
              </span>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <ul className="divide-y divide-border">
                {group.permissions.map((permission) => {
                  const checked = heldIds.has(permission.id)
                  const missing = checked ? EMPTY_SET : graph.missingPrerequisites(permission.id, heldIds)
                  const blocked = missing.size > 0
                  const editable = isEditable(permission, checked)
                  const inputId = `${idPrefix}-${permission.id}`
                  return (
                    <li
                      key={permission.id}
                      ref={(el) => {
                        if (el) rowRefs.current.set(permission.id, el)
                        else rowRefs.current.delete(permission.id)
                      }}
                      className={cn(
                        "flex items-start gap-3 px-5 py-3 transition-colors duration-300",
                        highlightedId === permission.id && "bg-primary/10"
                      )}
                    >
                      <Checkbox
                        id={inputId}
                        checked={checked}
                        disabled={!editable || blocked}
                        className="mt-0.5"
                        onCheckedChange={() => onToggle(permission, !checked)}
                      />
                      <div className="min-w-0 flex-1 space-y-1.5">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Label
                              htmlFor={inputId}
                              className={cn("font-mono text-xs", editable && !blocked && "cursor-pointer")}
                            >
                              {permission.name}
                            </Label>
                          </TooltipTrigger>
                          <TooltipContent side="top">{permission.description}</TooltipContent>
                        </Tooltip>
                        {permission.required_permission_ids.length > 0 && (
                          <div className="flex flex-wrap items-center gap-1">
                            {permission.required_permission_ids.map((requiredId) => {
                              const required = byId.get(requiredId)
                              const requiredHeld = heldIds.has(requiredId)
                              return (
                                <Badge
                                  key={requiredId}
                                  asChild
                                  variant={requiredHeld ? "success" : "warning"}
                                  className="cursor-pointer gap-1 font-mono"
                                >
                                  <button type="button" onClick={() => jumpTo(requiredId)}>
                                    {requiredHeld ? <Check className="size-3" /> : <Lock className="size-3" />}
                                    {required?.name ?? requiredId}
                                  </button>
                                </Badge>
                              )
                            })}
                          </div>
                        )}
                      </div>
                      {renderTrailing?.(permission, checked)}
                    </li>
                  )
                })}
              </ul>
            </CollapsibleContent>
          </Collapsible>
        )
      })}
    </div>
  )
}

export { PermissionGroupList }
