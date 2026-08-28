"use client"

import Link from "next/link"
import { ArrowUpRight, Plus } from "lucide-react"

import { PageHeader, PageBody } from "@/components/app/page"
import { Button } from "@/components/ui/button"
import { useCurrentUser, usePermissions } from "@/lib/auth"
import { getPrimaryApplication, getBackupApplication } from "@/services/api/auth"
import { useTicketsList } from "@/features/tickets/use-tickets-list"
import { useMyActivityTrend, useMyKpiSnapshot } from "@/features/dashboard/use-dashboard-analytics"
import { useRecentConversations } from "@/features/dashboard/use-recent-conversations"
import { KpiCards } from "@/features/dashboard/kpi-cards"
import { MyAssignments } from "@/features/dashboard/my-assignments"
import { TicketStatusSummary } from "@/features/dashboard/ticket-status-summary"
import { IncidentTrendChart } from "@/features/dashboard/incident-trend-chart"
import { ContinueConversations } from "@/features/dashboard/continue-conversations"
import { RecentTickets } from "@/features/dashboard/recent-tickets"

const functionalTeamLabels: Record<string, string> = {
  SUPPORT: "SN3",
  CONFIGURATION: "Paramétrage",
}

const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
})

export default function DashboardPage() {
  const { data: user } = useCurrentUser()
  // These shortcuts cross into other pages, so they ask whether the destination opens rather
  // than naming its permissions again — one declaration, in `routeRequirements`.
  const { canAccessRoute } = usePermissions()
  const { tickets } = useTicketsList()
  const { data: myKpiSnapshot } = useMyKpiSnapshot()
  const { data: myActivityTrend } = useMyActivityTrend()
  const {
    conversations,
    isLoading: isLoadingConversations,
    canUseAssistant,
  } = useRecentConversations()
  const myTickets = tickets.filter((t) => t.assignee?.id === user?.id)
  const primaryApplication = user ? getPrimaryApplication(user) : null
  const backupApplication = user ? getBackupApplication(user) : null
  const today = dateFormatter.format(new Date())

  const descriptionParts = [
    today,
    `Équipe ${(user && functionalTeamLabels[user.functionalTeam]) ?? user?.functionalTeam ?? "—"}`,
    `App. principale ${primaryApplication ?? "—"}`,
  ]
  if (backupApplication) {
    descriptionParts.push(`App. secondaire ${backupApplication}`)
  }

  return (
    <>
      <PageHeader
        title="Tableau de bord opérationnel"
        description={descriptionParts.join(" · ")}
        actions={
          <>
            {canAccessRoute("/analytics") && (
              <Button variant="outline" size="sm" asChild>
                <Link href="/analytics">
                  Voir les analyses <ArrowUpRight className="size-4" />
                </Link>
              </Button>
            )}
            {canAccessRoute("/tickets") && (
              <Button size="sm" asChild>
                <Link href="/tickets">
                  <Plus className="size-4" /> Nouveau ticket
                </Link>
              </Button>
            )}
          </>
        }
      />
      <PageBody className="space-y-6">
        <KpiCards
          activeAssignments={myTickets.filter((t) => t.status === "OPEN" || t.status === "IN_PROGRESS").length}
          resolvedThisWeek={myKpiSnapshot?.resolved_this_week ?? 0}
          createdThisWeek={myKpiSnapshot?.created_this_week ?? 0}
          avgResolutionMinutes={Math.round((myKpiSnapshot?.avg_resolution_hours ?? 0) * 60)}
        />

        <div className="grid gap-6 xl:grid-cols-3">
          <MyAssignments tickets={myTickets} />
          <TicketStatusSummary tickets={myTickets} />
        </div>

        {myActivityTrend && (
          <IncidentTrendChart
            data={myActivityTrend.map((point) => ({
              date: point.bucket_start,
              created: point.created,
              resolved: point.resolved,
            }))}
          />
        )}

        <div className="grid gap-6 xl:grid-cols-3">
          {/* Recent tickets take the freed column when the assistant is not this user's to use,
              rather than leaving a gap where the card would have been. */}
          <div className={canUseAssistant ? "xl:col-span-2" : "xl:col-span-3"}>
            <RecentTickets tickets={myTickets} />
          </div>
          {canUseAssistant && (
            <ContinueConversations conversations={conversations} isLoading={isLoadingConversations} />
          )}
        </div>
      </PageBody>
    </>
  )
}
