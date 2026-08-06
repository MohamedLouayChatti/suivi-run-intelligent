"use client"

import { useRouter } from "next/navigation"
import { X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { NotificationResponse } from "@/services/api/notifications"

import { parseNotificationAction, resolveNotificationHref } from "./notification-actions"
import { notificationTypeIcons } from "./notification-icons"

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

interface NotificationItemProps {
  notification: NotificationResponse
  onMarkRead: (notificationId: string) => void
  onNavigate: () => void
}

function NotificationItem({ notification, onMarkRead, onNavigate }: NotificationItemProps) {
  const router = useRouter()
  const isUnread = notification.read_at === null
  const action = parseNotificationAction(notification.action)
  const Icon = notificationTypeIcons[notification.type]

  function handleRowClick() {
    if (isUnread) onMarkRead(notification.id)
    if (action) {
      router.push(resolveNotificationHref(action))
      onNavigate()
    }
  }

  function handleDismiss(e: React.MouseEvent) {
    e.stopPropagation()
    onMarkRead(notification.id)
  }

  return (
    <div
      role={action ? "button" : undefined}
      tabIndex={action ? 0 : undefined}
      onClick={handleRowClick}
      onKeyDown={(e) => {
        if (action && (e.key === "Enter" || e.key === " ")) {
          e.preventDefault()
          handleRowClick()
        }
      }}
      className={cn(
        "group/notification relative flex gap-3 rounded-md px-2 py-2.5 text-left outline-hidden",
        action && "cursor-pointer hover:bg-accent focus-visible:bg-accent",
      )}
    >
      <span
        className={cn(
          "mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full",
          isUnread ? "bg-primary/10 text-primary" : "bg-muted-foreground/10 text-muted-foreground",
        )}
      >
        <Icon className="size-4" />
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex items-start gap-1.5">
          <p className={cn("text-sm", isUnread ? "font-medium text-foreground" : "text-muted-foreground")}>
            {notification.title}
          </p>
          {isUnread && <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />}
        </div>
        <p className="text-sm text-muted-foreground">{notification.message}</p>
        <p className="mt-0.5 text-xs text-muted-foreground">{formatRelativeTime(notification.created_at)}</p>
      </div>

      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Marquer comme lu"
        onClick={handleDismiss}
        className="shrink-0 text-muted-foreground opacity-0 group-hover/notification:opacity-100 focus-visible:opacity-100"
      >
        <X className="size-3.5" />
      </Button>
    </div>
  )
}

export { NotificationItem }
