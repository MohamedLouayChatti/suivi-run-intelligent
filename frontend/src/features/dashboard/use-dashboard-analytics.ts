"use client"

import { useQuery } from "@tanstack/react-query"

import { getMyActivityTrend, getMyKpiSnapshot } from "@/services/api/analytics"

function useMyKpiSnapshot() {
  return useQuery({
    queryKey: ["analytics", "my-kpi-snapshot"],
    queryFn: getMyKpiSnapshot,
  })
}

function useMyActivityTrend() {
  return useQuery({
    queryKey: ["analytics", "my-activity-trend"],
    queryFn: getMyActivityTrend,
  })
}

export { useMyKpiSnapshot, useMyActivityTrend }
