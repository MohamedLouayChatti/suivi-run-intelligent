"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useQueryClient, type QueryClient } from "@tanstack/react-query"

import { useAuthSession } from "@/lib/auth"
import { invalidateGroups } from "@/lib/cache-invalidation"
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
import { groupsForNotification } from "./notification-invalidation"

/**
 * Keeps the notification list/unread-count query caches in sync with the live SSE
 * stream — every incoming notification is brand new (never read yet), so it's always
 * prepended to the list and always increments the unread count by one. Also surfaces a
 * toast for each one while the tab is open, so a new notification isn't only visible as
 * a dot on the bell. Mounted once near the app root (see NotificationsSseBridge) rather
 * than by the bell itself, so the connection survives across route changes and dropdown
 * open/close instead of reconnecting every time.
 *
 * It also invalidates whatever the notification says has changed, which is the whole of
 * this app's answer to somebody else's action reaching an open tab. The signal already
 * arrived here — the connection is open, the event is delivered, the toast is raised —
 * and everything past the bell was left holding data the notification had just announced
 * was wrong. A revoked permission was told to the user and disproved by every control
 * still on screen.
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

      invalidateGroups(queryClient, groupsForNotification(notification.type))

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
