type TimeRange = "30D" | "3M" | "6M" | "1Y"

const timeRangeOptions: TimeRange[] = ["30D", "3M", "6M", "1Y"]

const timeRangeLabels: Record<TimeRange, string> = {
  "30D": "30 derniers jours",
  "3M": "3 derniers mois",
  "6M": "6 derniers mois",
  "1Y": "12 derniers mois",
}

// Days of history each range represents — drives the mock generators' magnitude and
// bucketing granularity. Swap for real backend aggregation windows later.
const timeRangeDays: Record<TimeRange, number> = {
  "30D": 30,
  "3M": 90,
  "6M": 182,
  "1Y": 365,
}

export { timeRangeOptions, timeRangeLabels, timeRangeDays }
export type { TimeRange }
