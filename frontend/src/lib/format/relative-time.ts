const RELATIVE_TIME_FORMATTER = new Intl.RelativeTimeFormat("fr", { numeric: "auto" })

const RELATIVE_TIME_DIVISIONS: { amount: number; unit: Intl.RelativeTimeFormatUnit }[] = [
  { amount: 60, unit: "second" },
  { amount: 60, unit: "minute" },
  { amount: 24, unit: "hour" },
  { amount: 7, unit: "day" },
  { amount: 4.34524, unit: "week" },
  { amount: 12, unit: "month" },
  { amount: Number.POSITIVE_INFINITY, unit: "year" },
]

/**
 * An ISO timestamp as "il y a 18 min". Lives here rather than in a feature because three lists —
 * notifications, the chatbot's conversations, and the dashboard's — all date the same way and had
 * begun keeping their own identical copies of it.
 *
 * Not to be confused with `RecentTickets`' own `formatRelativeCompletion`, which deliberately
 * coarsens everything to hours or days: a ticket closed "il y a 43 secondes" is noise on a card
 * summarising a week's work.
 */
function formatRelativeTime(iso: string): string {
  let duration = (new Date(iso).getTime() - Date.now()) / 1000
  for (const division of RELATIVE_TIME_DIVISIONS) {
    if (Math.abs(duration) < division.amount) {
      return RELATIVE_TIME_FORMATTER.format(Math.round(duration), division.unit)
    }
    duration /= division.amount
  }
  return RELATIVE_TIME_FORMATTER.format(Math.round(duration), "year")
}

export { formatRelativeTime }
