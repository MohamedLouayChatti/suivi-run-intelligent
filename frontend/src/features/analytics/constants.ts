type TimeRange = "30D" | "3M" | "6M" | "1Y"

const timeRangeOptions: TimeRange[] = ["30D", "3M", "6M", "1Y"]

const timeRangeLabels: Record<TimeRange, string> = {
  "30D": "30 derniers jours",
  "3M": "3 derniers mois",
  "6M": "6 derniers mois",
  "1Y": "12 derniers mois",
}

export { timeRangeOptions, timeRangeLabels }
export type { TimeRange }
