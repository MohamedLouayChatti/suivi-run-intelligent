"use client"

import { useEffect } from "react"
import { useQueryClient } from "@tanstack/react-query"

import { useAuthSession } from "@/lib/auth"
import { connectToNotificationStream } from "@/services/sse/notifications"
import type { NotificationResponse } from "@/services/api/notifications"

import { notificationsListQueryKey, notificationsUnreadCountQueryKey } from "./use-notifications"

/**
 * Keeps the notification list/unread-count query caches in sync with the live SSE
 * stream — every incoming notification is brand new (never read yet), so it's always
 * prepended to the list and always increments the unread count by one. Mounted once
 * near the app root (see NotificationsSseBridge) rather than by the bell itself, so the
 * connection survives across route changes and dropdown open/close instead of
 * reconnecting every time.
 */
function useNotificationStream() {
  const queryClient = useQueryClient()
  const { isLoaded, isSignedIn } = useAuthSession()

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return

    const close = connectToNotificationStream((notification) => {
      queryClient.setQueryData<NotificationResponse[]>(notificationsListQueryKey, (current) => {
        if (!current || current.some((n) => n.id === notification.id)) return current
        return [notification, ...current]
      })
      queryClient.setQueryData<number>(notificationsUnreadCountQueryKey, (count) => (count ?? 0) + 1)
    })

    return close
  }, [isLoaded, isSignedIn, queryClient])
}

export { useNotificationStream }
