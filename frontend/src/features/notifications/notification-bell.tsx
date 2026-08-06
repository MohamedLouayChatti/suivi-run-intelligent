"use client"

import { useState } from "react"
import { Bell } from "lucide-react"

import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

import { useNotifications } from "./use-notifications"
import { NotificationItem } from "./notification-item"

function NotificationBell() {
  const [open, setOpen] = useState(false)
  const { notifications, isLoading, unreadCount, markRead, markAllRead, isMarkingAllRead } = useNotifications()

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" aria-label="Notifications">
          <Bell />
          {unreadCount > 0 && <span className="absolute right-2 top-2 size-1.5 rounded-full bg-primary" />}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 p-0 sm:w-96">
        <div className="flex items-center justify-between gap-2 px-3 py-2.5">
          <p className="text-sm font-medium">Notifications</p>
          <Button
            variant="ghost"
            size="sm"
            className="h-auto px-1.5 py-1 text-xs text-muted-foreground hover:text-foreground"
            disabled={unreadCount === 0 || isMarkingAllRead}
            onClick={() => markAllRead()}
          >
            Tout marquer comme lu
          </Button>
        </div>
        <DropdownMenuSeparator className="my-0" />

        {isLoading ? (
          <div className="space-y-3 p-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex gap-3">
                <Skeleton className="size-8 shrink-0 rounded-full" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-3.5 w-3/4" />
                  <Skeleton className="h-3 w-full" />
                </div>
              </div>
            ))}
          </div>
        ) : notifications.length === 0 ? (
          <p className="px-3 py-8 text-center text-sm text-muted-foreground">
            Aucune notification non lue.
          </p>
        ) : (
          <ScrollArea className="max-h-[420px]">
            <div className="space-y-0.5 p-1.5">
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onMarkRead={markRead}
                  onNavigate={() => setOpen(false)}
                />
              ))}
            </div>
          </ScrollArea>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export { NotificationBell }
