"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useQueryClient, type QueryClient } from "@tanstack/react-query"

import { useAuthSession } from "@/lib/auth"
import { toast } from "@/hooks/use-toast"
import { ToastAction } from "@/components/ui/toast"
import { connectToNotificationStream } from "@/services/sse/notifications"
import { markNotificationRead, type NotificationResponse } from "@/services/api/notifications"

import {
  notificationsListQueryKey,
  notificationsUnreadCountQueryKey,
  applyNotificationRead,
} from "./use-notifications"
import { parseNotificationAction, resolveNotificationHref } from "./notification-actions"

/**
 * Keeps the notification list/unread-count query caches in sync with the live SSE
 * stream — every incoming notification is brand new (never read yet), so it's always
 * prepended to the list and always increments the unread count by one. Also surfaces a
 * toast for each one while the tab is open, so a new notification isn't only visible as
 * a dot on the bell. Mounted once near the app root (see NotificationsSseBridge) rather
 * than by the bell itself, so the connection survives across route changes and dropdown
 * open/close instead of reconnecting every time.
 */
function useNotificationStream() {
  const queryClient = useQueryClient()
  const router = useRouter()
  const { isLoaded, isSignedIn } = useAuthSession()

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return

    const close = connectToNotificationStream((notification) => {
      queryClient.setQueryData<NotificationResponse[]>(notificationsListQueryKey, (current) => {
        if (!current || current.some((n) => n.id === notification.id)) return current
        return [notification, ...current]
      })
      queryClient.setQueryData<number>(notificationsUnreadCountQueryKey, (count) => (count ?? 0) + 1)

      showNotificationToast(notification, queryClient, router)
    })

    return close
  }, [isLoaded, isSignedIn, queryClient, router])
}

function showNotificationToast(
  notification: NotificationResponse,
  queryClient: QueryClient,
  router: ReturnType<typeof useRouter>,
): void {
  const action = parseNotificationAction(notification.action)

  // `handleActionClick` only runs later, on click — by then `controls` (declared via the
  // `toast()` call below, in the same scope) is always assigned, so this forward
  // reference through the closure is safe despite the textual ordering.
  async function handleActionClick() {
    if (!action) return
    try {
      const updated = await markNotificationRead(notification.id)
      applyNotificationRead(queryClient, updated)
    } finally {
      router.push(resolveNotificationHref(action))
      controls.dismiss()
    }
  }

  const controls = toast({
    title: notification.title,
    description: notification.message,
    action: action ? (
      <ToastAction altText="Voir la notification" onClick={handleActionClick}>
        Voir
      </ToastAction>
    ) : undefined,
  })
}

export { useNotificationStream }
