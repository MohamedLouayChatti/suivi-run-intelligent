"use client"

import { useEffect, useState } from "react"
import { Loader2, Play, RefreshCw, RotateCcw } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"
import { useRecalculationSchedule } from "@/features/knowledge-base/use-recalculation-schedule"
import type { RecalculationSchedule } from "@/services/api/knowledge-base"
import type { components } from "@/types/api"

type Weekday = components["schemas"]["Weekday"]

/** Monday first, matching the backend's own week order. */
const weekdays: { value: Weekday; short: string; long: string }[] = [
  { value: "mon", short: "L", long: "lundi" },
  { value: "tue", short: "M", long: "mardi" },
  { value: "wed", short: "M", long: "mercredi" },
  { value: "thu", short: "J", long: "jeudi" },
  { value: "fri", short: "V", long: "vendredi" },
  { value: "sat", short: "S", long: "samedi" },
  { value: "sun", short: "D", long: "dimanche" },
]

/**
 * The zones this schedule is realistically set in, rather than the machine's whole tz database.
 * Every value here is an IANA name the backend resolves; anything outside the list can still be
 * set through the API, and is displayed as-is if it ever is.
 */
const timezoneOptions: { value: string; label: string }[] = [
  { value: "Europe/Paris", label: "Europe/Paris (heure française)" },
  { value: "UTC", label: "UTC (temps universel)" },
  { value: "Africa/Tunis", label: "Africa/Tunis" },
  { value: "Europe/London", label: "Europe/London" },
]

const hourOptions = Array.from({ length: 24 }, (_, hour) => hour)
/** Quarter hours: a maintenance pass has no business being scheduled to the minute. */
const minuteOptions = [0, 15, 30, 45]

interface ScheduleForm {
  enabled: boolean
  days: Weekday[]
  hour: number
  minute: number
  timezone: string
}

function toForm(schedule: RecalculationSchedule): ScheduleForm {
  return {
    enabled: schedule.enabled,
    days: schedule.days_of_week,
    hour: schedule.hour,
    minute: schedule.minute,
    timezone: schedule.timezone,
  }
}

function isSameSchedule(a: ScheduleForm, b: ScheduleForm): boolean {
  return (
    a.enabled === b.enabled &&
    a.hour === b.hour &&
    a.minute === b.minute &&
    a.timezone === b.timezone &&
    a.days.length === b.days.length &&
    a.days.every((day) => b.days.includes(day))
  )
}

const dateTimeFormatter = new Intl.DateTimeFormat("fr-FR", {
  weekday: "long",
  day: "2-digit",
  month: "long",
  hour: "2-digit",
  minute: "2-digit",
})

interface RecalculationPanelProps {
  /** Mirrors `knowledge_base.manage_recalculation` — read access alone shows this read-only. */
  canManage: boolean
}

function RecalculationPanel({ canManage }: RecalculationPanelProps) {
  const { schedule, isLoading, isError, isSaving, isStarting, onSave, onRunNow } =
    useRecalculationSchedule({ canManage })

  if (isLoading) {
    return (
      <SectionCard title="Planification du recalcul">
        <div className="space-y-3">
          <Skeleton className="h-5 w-64" />
          <Skeleton className="h-10 w-full max-w-md" />
          <Skeleton className="h-10 w-full max-w-md" />
        </div>
      </SectionCard>
    )
  }

  if (isError || !schedule) {
    return (
      <SectionCard title="Planification du recalcul">
        <p className="text-sm text-muted-foreground">
          La planification n&apos;a pas pu être chargée. Rechargez la page pour réessayer.
        </p>
      </SectionCard>
    )
  }

  return (
    <div className="space-y-6">
      <StatusCard
        schedule={schedule}
        canManage={canManage}
        isStarting={isStarting}
        onRunNow={onRunNow}
      />
      <ScheduleForm schedule={schedule} canManage={canManage} isSaving={isSaving} onSave={onSave} />
    </div>
  )
}

function StatusCard({
  schedule,
  canManage,
  isStarting,
  onRunNow,
}: {
  schedule: RecalculationSchedule
  canManage: boolean
  isStarting: boolean
  onRunNow: () => void
}) {
  const [isConfirming, setIsConfirming] = useState(false)

  return (
    <>
      <SectionCard
        title="État du graphe de similarité"
        description="Le recalcul complet reconstruit les suggestions d'incidents similaires sur l'ensemble du corpus."
        action={
          canManage && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsConfirming(true)}
              disabled={schedule.running || isStarting}
            >
              {isStarting ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
              Lancer maintenant
            </Button>
          )
        }
      >
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-md border border-border bg-surface p-4">
            <p className="text-xs tracking-wide text-muted-foreground uppercase">Passe en cours</p>
            <div className="mt-1.5 flex items-center gap-2">
              {schedule.running ? (
                <>
                  <RefreshCw className="size-4 animate-spin text-primary" strokeWidth={2} />
                  <span className="text-sm font-medium text-primary">Recalcul en cours</span>
                </>
              ) : (
                <span className="text-sm text-muted-foreground">Aucune — le graphe est au repos</span>
              )}
            </div>
          </div>
          <div className="rounded-md border border-border bg-surface p-4">
            <p className="text-xs tracking-wide text-muted-foreground uppercase">Prochaine passe</p>
            <p className="mt-1.5 text-sm">
              {schedule.next_run_at ? (
                <span className="font-medium">
                  {dateTimeFormatter.format(new Date(schedule.next_run_at))}
                </span>
              ) : (
                <span className="text-muted-foreground">
                  Aucune — la planification est désactivée
                </span>
              )}
            </p>
          </div>
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          Une seule passe s&apos;exécute à la fois. Tant qu&apos;elle tourne, une nouvelle demande —
          comme un import de tickets — est refusée plutôt que mise en file d&apos;attente. Les
          suggestions restent consultables pendant ce temps&nbsp;: elles sont simplement celles de la
          passe précédente jusqu&apos;à la fin de celle-ci.
        </p>
      </SectionCard>

      <AlertDialog open={isConfirming} onOpenChange={setIsConfirming}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Lancer un recalcul complet ?</AlertDialogTitle>
            <AlertDialogDescription>
              La passe parcourt l&apos;intégralité du corpus et reconstruit toutes les suggestions
              d&apos;incidents similaires. Elle s&apos;exécute en arrière-plan et peut durer plusieurs
              minutes. Pendant ce temps, aucun import de tickets ne pourra être accepté.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction onClick={onRunNow}>Lancer le recalcul</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

function ScheduleForm({
  schedule,
  canManage,
  isSaving,
  onSave,
}: {
  schedule: RecalculationSchedule
  canManage: boolean
  isSaving: boolean
  onSave: (payload: {
    enabled: boolean
    days_of_week: Weekday[]
    hour: number
    minute: number
    timezone: string
  }) => void
}) {
  const saved = toForm(schedule)
  const [form, setForm] = useState<ScheduleForm>(saved)

  // The schedule is refetched on an interval and after every save, so the form follows the server
  // whenever the server's answer changes — a save elsewhere, or the one just made here.
  useEffect(() => {
    setForm(toForm(schedule))
  }, [schedule])

  const isDirty = !isSameSchedule(form, saved)
  // The backend requires at least one day; saying so before the request is friendlier than a 422.
  const hasNoDay = form.days.length === 0

  function toggleDay(day: Weekday) {
    setForm((current) => ({
      ...current,
      days: current.days.includes(day)
        ? current.days.filter((value) => value !== day)
        : [...current.days, day],
    }))
  }

  const timezoneChoices = timezoneOptions.some((option) => option.value === form.timezone)
    ? timezoneOptions
    : [...timezoneOptions, { value: form.timezone, label: form.timezone }]

  return (
    <SectionCard
      title="Planification"
      description="Quand la passe complète doit se déclencher d'elle-même."
    >
      <fieldset disabled={!canManage || isSaving} className="space-y-6">
        <div className="flex items-start justify-between gap-4 rounded-md border border-border bg-surface p-4">
          <div className="min-w-0">
            <Label htmlFor="schedule-enabled" className="text-sm font-medium">
              Recalcul planifié
            </Label>
            <p className="mt-1 text-xs text-muted-foreground">
              Désactivé, le graphe n&apos;est plus rafraîchi que par un import ou par un lancement
              manuel — les suggestions vieillissent alors sans que rien ne le signale.
            </p>
          </div>
          <Switch
            id="schedule-enabled"
            checked={form.enabled}
            onCheckedChange={(enabled) => setForm((current) => ({ ...current, enabled }))}
          />
        </div>

        <div className={cn("space-y-6", !form.enabled && "opacity-50")}>
          <div className="space-y-2">
            <Label>Jours de la semaine</Label>
            <div className="flex flex-wrap gap-2">
              {weekdays.map((day) => {
                const isSelected = form.days.includes(day.value)
                return (
                  <button
                    key={day.value}
                    type="button"
                    aria-pressed={isSelected}
                    aria-label={day.long}
                    onClick={() => toggleDay(day.value)}
                    disabled={!canManage || isSaving || !form.enabled}
                    className={cn(
                      "size-10 rounded-md border text-sm font-medium transition-colors disabled:cursor-not-allowed",
                      isSelected
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border bg-surface text-muted-foreground hover:border-primary/40 hover:text-foreground",
                    )}
                  >
                    {day.short}
                  </button>
                )
              })}
            </div>
            {hasNoDay ? (
              <p className="text-xs text-destructive">
                Sélectionnez au moins un jour, sinon la planification n&apos;a aucune date de
                déclenchement.
              </p>
            ) : (
              <p className="text-xs text-muted-foreground">
                {describeDays(form.days)} — une seule heure vaut pour tous les jours sélectionnés.
              </p>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-[8rem_8rem_minmax(0,20rem)]">
            <div className="space-y-2">
              <Label htmlFor="schedule-hour">Heure</Label>
              <Select
                value={String(form.hour)}
                onValueChange={(value) => setForm((current) => ({ ...current, hour: Number(value) }))}
                disabled={!canManage || isSaving || !form.enabled}
              >
                <SelectTrigger id="schedule-hour">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {hourOptions.map((hour) => (
                    <SelectItem key={hour} value={String(hour)}>
                      {String(hour).padStart(2, "0")} h
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="schedule-minute">Minutes</Label>
              <Select
                value={String(form.minute)}
                onValueChange={(value) => setForm((current) => ({ ...current, minute: Number(value) }))}
                disabled={!canManage || isSaving || !form.enabled}
              >
                <SelectTrigger id="schedule-minute">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {minuteOptions.map((minute) => (
                    <SelectItem key={minute} value={String(minute)}>
                      {String(minute).padStart(2, "0")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="schedule-timezone">Fuseau horaire</Label>
              <Select
                value={form.timezone}
                onValueChange={(timezone) => setForm((current) => ({ ...current, timezone }))}
                disabled={!canManage || isSaving || !form.enabled}
              >
                <SelectTrigger id="schedule-timezone">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {timezoneChoices.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="rounded-md border border-border bg-surface p-4">
            <p className="text-xs tracking-wide text-muted-foreground uppercase">Récapitulatif</p>
            <p className="mt-1.5 text-sm">
              {form.enabled && !hasNoDay ? (
                <>
                  Le recalcul complet se déclenchera{" "}
                  <span className="font-medium">
                    {describeDays(form.days)} à {String(form.hour).padStart(2, "0")}h
                    {String(form.minute).padStart(2, "0")}
                  </span>{" "}
                  ({form.timezone}). L&apos;heure locale est conservée lors des changements
                  d&apos;heure.
                </>
              ) : (
                <span className="text-muted-foreground">
                  Aucun déclenchement automatique ne sera programmé.
                </span>
              )}
            </p>
          </div>
        </div>

        {canManage && (
          <div className="flex flex-wrap items-center gap-3">
            <Button
              onClick={() =>
                onSave({
                  enabled: form.enabled,
                  days_of_week: form.days,
                  hour: form.hour,
                  minute: form.minute,
                  timezone: form.timezone,
                })
              }
              disabled={!isDirty || hasNoDay || isSaving}
            >
              {isSaving && <Loader2 className="size-4 animate-spin" />}
              Enregistrer la planification
            </Button>
            {isDirty && (
              <Button variant="ghost" onClick={() => setForm(saved)} disabled={isSaving}>
                <RotateCcw className="size-4" /> Annuler les modifications
              </Button>
            )}
            {isDirty && (
              <Badge variant="secondary" className="bg-foreground/10 text-foreground/70">
                Modifications non enregistrées
              </Badge>
            )}
          </div>
        )}
      </fieldset>

      {!canManage && (
        <p className="mt-4 text-xs text-muted-foreground">
          Vous consultez cette planification en lecture seule. La modifier requiert la permission
          <code className="mx-1 font-mono">knowledge_base.manage_recalculation</code>.
        </p>
      )}
    </SectionCard>
  )
}

/** "mardi et vendredi", "tous les jours", "lundi, mercredi et jeudi". */
function describeDays(days: Weekday[]): string {
  if (days.length === 0) return "aucun jour"
  if (days.length === 7) return "tous les jours"
  const names = weekdays.filter((day) => days.includes(day.value)).map((day) => day.long)
  if (names.length === 1) return names[0]
  return `${names.slice(0, -1).join(", ")} et ${names[names.length - 1]}`
}

export { RecalculationPanel }
