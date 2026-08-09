"use client"

import * as React from "react"
import { Popover as PopoverPrimitive } from "radix-ui"
import { CheckIcon, ChevronDownIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"

interface ComboboxProps {
  options: string[]
  value: string | undefined
  onValueChange: (value: string) => void
  placeholder?: string
  searchPlaceholder?: string
  emptyText?: string
  className?: string
}

/**
 * A searchable single-select, for enums with too many members for a plain Select
 * to stay usable (e.g. Offer's ~180 values). Built on Popover rather than a
 * dedicated combobox/command library since none is a project dependency yet.
 */
function Combobox({
  options,
  value,
  onValueChange,
  placeholder = "Sélectionner…",
  searchPlaceholder = "Rechercher…",
  emptyText = "Aucun résultat.",
  className,
}: ComboboxProps) {
  const [open, setOpen] = React.useState(false)

  return (
    <PopoverPrimitive.Root open={open} onOpenChange={setOpen}>
      <PopoverPrimitive.Trigger asChild>
        <button
          type="button"
          className={cn(
            "flex h-8 w-full items-center justify-between gap-1.5 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm whitespace-nowrap transition-colors outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-input/30 dark:hover:bg-input/50",
            className
          )}
        >
          <span className={cn("truncate", !value && "text-muted-foreground")}>{value || placeholder}</span>
          <ChevronDownIcon className="size-4 shrink-0 text-muted-foreground" />
        </button>
      </PopoverPrimitive.Trigger>
      <PopoverPrimitive.Portal>
        <PopoverPrimitive.Content
          align="start"
          sideOffset={4}
          className="z-50 w-(--radix-popover-trigger-width) origin-(--radix-popover-content-transform-origin) overflow-hidden rounded-lg bg-popover text-popover-foreground shadow-md ring-1 ring-foreground/10 duration-100 data-open:animate-in data-open:fade-in-0 data-open:zoom-in-95 data-closed:animate-out data-closed:fade-out-0 data-closed:zoom-out-95"
        >
          <ComboboxList
            options={options}
            value={value}
            searchPlaceholder={searchPlaceholder}
            emptyText={emptyText}
            onSelect={(option) => {
              onValueChange(option)
              setOpen(false)
            }}
          />
        </PopoverPrimitive.Content>
      </PopoverPrimitive.Portal>
    </PopoverPrimitive.Root>
  )
}

interface ComboboxListProps {
  options: string[]
  value: string | undefined
  searchPlaceholder: string
  emptyText: string
  onSelect: (option: string) => void
}

// Only mounted while the popover is open, so `search` always starts fresh — same
// pattern used by JiraDetailsDialog to avoid syncing state back via an effect.
function ComboboxList({ options, value, searchPlaceholder, emptyText, onSelect }: ComboboxListProps) {
  const [search, setSearch] = React.useState("")
  const filtered = React.useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return options
    return options.filter((option) => option.toLowerCase().includes(term))
  }, [options, search])

  return (
    <>
      <div className="border-b border-border p-1.5">
        <Input
          autoFocus
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={searchPlaceholder}
          className="h-7"
        />
      </div>
      {/* Sheet/Dialog's scroll lock (react-remove-scroll) intercepts wheel events on the
          document; stopping propagation here — before it reaches that document-level
          listener — is what lets the mouse wheel scroll this list while the Combobox is
          opened from inside a Sheet (Radix Select avoids this by scrolling via JS instead
          of native overflow, which this plain div doesn't have). */}
      <div className="max-h-64 overflow-y-auto p-1" onWheel={(e) => e.stopPropagation()}>
        {filtered.length === 0 ? (
          <p className="px-2 py-4 text-center text-sm text-muted-foreground">{emptyText}</p>
        ) : (
          filtered.map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => onSelect(option)}
              className="flex w-full items-center gap-1.5 rounded-md py-1 pr-8 pl-1.5 text-left text-sm outline-hidden select-none hover:bg-accent hover:text-accent-foreground"
            >
              <span className="relative flex size-4 shrink-0 items-center justify-center">
                {option === value && <CheckIcon className="size-4" />}
              </span>
              <span className="truncate">{option}</span>
            </button>
          ))
        )}
      </div>
    </>
  )
}

export { Combobox }
