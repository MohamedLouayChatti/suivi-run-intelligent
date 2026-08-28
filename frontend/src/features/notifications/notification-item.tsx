"use client"

import { useRouter } from "next/navigation"
import { X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { formatRelativeTime } from "@/lib/format/relative-time"
import { cn } from "@/lib/utils"
import type { NotificationResponse } from "@/services/api/notifications"

import { parseNotificationAction, resolveNotificationHref } from "./notification-actions"
import { notificationTypeIcons } from "./notification-icons"

interface NotificationItemProps {
  notification: NotificationResponse
  onMarkRead: (notificationId: string) => void
  onNavigate: () => void
}

function NotificationItem({ notification, onMarkRead, onNavigate }: NotificationItemProps) {
  const router = useRouter()
  const action = parseNotificationAction(notification.action)
  const Icon = notificationTypeIcons[notification.type]

  function handleRowClick() {
    if (!action) return
    onMarkRead(notification.id)
    router.push(resolveNotificationHref(action))
    onNavigate()
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
      <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
        <Icon className="size-4" />
      </span>

      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-foreground">{notification.title}</p>
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
