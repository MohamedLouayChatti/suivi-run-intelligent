// No /analytics endpoint exists yet — mocked and isolated here for a later one-file swap.
function buildMockTrend(days: number) {
  const points: { date: string; created: number; resolved: number }[] = []
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000)
    const base = 3 + Math.round(2 * Math.sin(i / 4))
    points.push({
      date: date.toISOString().slice(0, 10),
      created: Math.max(0, base + (i % 5 === 0 ? 2 : 0)),
      resolved: Math.max(0, base - (i % 7 === 0 ? 1 : 0)),
    })
  }
  return points
}

const mockTrend = buildMockTrend(30)

const mockConversations = [
  { id: "conv-1", title: "Procédure de lag des consumers Kafka", relativeTime: "il y a 18 min" },
  { id: "conv-2", title: "Comment rejouer la dead-letter queue", relativeTime: "il y a 2 h" },
  { id: "conv-3", title: "Politique SLA pour les incidents Sev2", relativeTime: "hier" },
]

// activeAssignments is now computed from the real tickets list on the dashboard page —
// only the true aggregate figures (no /analytics backend yet) stay mocked here.
const mockKpis = {
  resolvedThisWeek: 5,
  createdThisWeek: 7,
  avgResolutionMinutes: 375,
}

export { mockTrend, mockConversations, mockKpis }
