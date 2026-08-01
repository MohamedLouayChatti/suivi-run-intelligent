"use client"

import Link from "next/link"
import { ArrowUpRight, Plus } from "lucide-react"

import { PageHeader, PageBody } from "@/components/app/page"
import { Button } from "@/components/ui/button"
import { useCurrentUser } from "@/lib/auth"
import { getPrimaryApplication, getBackupApplication } from "@/services/api/auth"
import { useTicketsList } from "@/features/tickets/use-tickets-list"
import { mockTrend, mockConversations, mockKpis } from "@/features/dashboard/mock-data"
import { KpiCards } from "@/features/dashboard/kpi-cards"
import { MyAssignments } from "@/features/dashboard/my-assignments"
import { TicketStatusSummary } from "@/features/dashboard/ticket-status-summary"
import { IncidentTrendChart } from "@/features/dashboard/incident-trend-chart"
import { ContinueConversations } from "@/features/dashboard/continue-conversations"
import { RecentTickets } from "@/features/dashboard/recent-tickets"

const functionalTeamLabels: Record<string, string> = {
  SUPPORT: "Support",
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
  const { tickets } = useTicketsList()
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
            <Button variant="outline" size="sm" asChild>
              <Link href="/analytics">
                Voir les analyses <ArrowUpRight className="size-4" />
              </Link>
            </Button>
            <Button size="sm" asChild>
              <Link href="/tickets">
                <Plus className="size-4" /> Nouveau ticket
              </Link>
            </Button>
          </>
        }
      />
      <PageBody className="space-y-6">
        <KpiCards
          activeAssignments={myTickets.filter((t) => t.status === "OPEN" || t.status === "IN_PROGRESS").length}
          resolvedThisWeek={mockKpis.resolvedThisWeek}
          createdThisWeek={mockKpis.createdThisWeek}
          avgResolutionMinutes={mockKpis.avgResolutionMinutes}
        />

        <div className="grid gap-6 xl:grid-cols-3">
          <MyAssignments tickets={myTickets} />
          <TicketStatusSummary tickets={myTickets} />
        </div>

        <IncidentTrendChart data={mockTrend} />

        <div className="grid gap-6 xl:grid-cols-3">
          <div className="xl:col-span-2">
            <RecentTickets tickets={myTickets} />
          </div>
          <ContinueConversations conversations={mockConversations} />
        </div>
      </PageBody>
    </>
  )
}
