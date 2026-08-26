"use client"

import * as React from "react"
import { CalendarIcon } from "lucide-react"
import type { DateRange } from "react-day-picker"

import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"

interface DateRangeValue {
  from: string
  to: string
}

interface DateRangeFilterProps {
  value: DateRangeValue
  onChange: (value: DateRangeValue) => void
  /** Earliest selectable date ("YYYY-MM-DD"). Omit for no lower bound. */
  minDate?: string
  /** Latest selectable date ("YYYY-MM-DD"). Defaults to today -- a range filter never offers a
   * date the data can't yet contain. */
  maxDate?: string
  placeholder?: string
  className?: string
}

const displayFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
})

// The rest of the app stores date-range filters as native <input type="date"> values
// ("YYYY-MM-DD", local calendar day, no time/timezone) -- these keep that exact contract so
// the API layer (which forwards them straight through as date_from/date_to) needs no change.
function parseISODate(value: string): Date | undefined {
  if (!value) return undefined
  const [year, month, day] = value.split("-").map(Number)
  if (!year || !month || !day) return undefined
  return new Date(year, month - 1, day)
}

function formatISODate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  return `${year}-${month}-${day}`
}

function startOfToday(): Date {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), now.getDate())
}

function daysAgo(days: number): Date {
  const date = startOfToday()
  date.setDate(date.getDate() - days)
  return date
}

function startOfMonth(): Date {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), 1)
}

interface Preset {
  label: string
  range: () => DateRange
}

const presets: Preset[] = [
  { label: "7 derniers jours", range: () => ({ from: daysAgo(6), to: startOfToday() }) },
  { label: "30 derniers jours", range: () => ({ from: daysAgo(29), to: startOfToday() }) },
  { label: "Ce mois-ci", range: () => ({ from: startOfMonth(), to: startOfToday() }) },
]

/**
 * Popover date-range picker shared by every filter bar that needs one -- a calendar
 * structurally rules out an end date before the start (react-day-picker's range mode always
 * orders the two ends) and an out-of-bounds date (both disabled via `minDate`/`maxDate`)
 * rather than accepting one and rejecting it after the fact.
 */
function DateRangeFilter({
  value,
  onChange,
  minDate,
  maxDate,
  placeholder = "Toute la période",
  className,
}: DateRangeFilterProps) {
  const [open, setOpen] = React.useState(false)

  const from = parseISODate(value.from)
  const to = parseISODate(value.to)
  const minDateObj = parseISODate(minDate ?? "")
  const maxDateObj = parseISODate(maxDate ?? "") ?? startOfToday()

  function apply(range: DateRange | undefined) {
    onChange({
      from: range?.from ? formatISODate(range.from) : "",
      to: range?.to ? formatISODate(range.to) : "",
    })
  }

  function applyPreset(preset: Preset) {
    apply(preset.range())
    setOpen(false)
  }

  function handleSelect(range: DateRange | undefined) {
    apply(range)
    if (range?.from && range?.to) setOpen(false)
  }

  const label =
    from && to
      ? `${displayFormatter.format(from)} – ${displayFormatter.format(to)}`
      : from
        ? `Depuis le ${displayFormatter.format(from)}`
        : to
          ? `Jusqu'au ${displayFormatter.format(to)}`
          : placeholder

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          className={cn(
            "justify-start gap-2 font-normal",
            !from && !to && "text-muted-foreground",
            className
          )}
        >
          <CalendarIcon className="size-4 shrink-0" />
          <span className="truncate">{label}</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-auto flex-row gap-0 p-0">
        <div className="flex flex-col gap-1 border-r border-border p-2">
          {presets.map((preset) => (
            <Button
              key={preset.label}
              type="button"
              variant="ghost"
              size="sm"
              className="justify-start font-normal"
              onClick={() => applyPreset(preset)}
            >
              {preset.label}
            </Button>
          ))}
        </div>
        <Calendar
          mode="range"
          selected={{ from, to }}
          onSelect={handleSelect}
          defaultMonth={from ?? maxDateObj}
          disabled={minDateObj ? [{ before: minDateObj }, { after: maxDateObj }] : { after: maxDateObj }}
          numberOfMonths={1}
          className="p-3"
        />
      </PopoverContent>
    </Popover>
  )
}

export { DateRangeFilter }
export type { DateRangeValue }
