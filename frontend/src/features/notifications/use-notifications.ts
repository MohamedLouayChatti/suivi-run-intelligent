"use client"

import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query"

import {
  listNotifications,
  countUnreadNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  type NotificationResponse,
} from "@/services/api/notifications"

const notificationsListQueryKey = ["notifications", "list"] as const
const notificationsUnreadCountQueryKey = ["notifications", "unread-count"] as const

/**
 * Removes a freshly-marked-read notification from the list/unread-count caches — the
 * dropdown only ever shows unread notifications, so a read one drops out rather than
 * staying visible in a dimmed state. Shared by the mark-read mutation below and by the
 * notification toast's "Voir" action (which calls the API directly rather than mounting
 * its own useMutation), so both paths update the cache identically.
 */
function applyNotificationRead(queryClient: QueryClient, updated: NotificationResponse): void {
  let wasPresent = false
  queryClient.setQueryData<NotificationResponse[]>(notificationsListQueryKey, (current) => {
    if (!current) return current
    const next = current.filter((n) => n.id !== updated.id)
    wasPresent = next.length !== current.length
    return next
  })
  if (wasPresent) {
    queryClient.setQueryData<number>(notificationsUnreadCountQueryKey, (count) => Math.max(0, (count ?? 1) - 1))
  }
}

/**
 * Backs the notification bell dropdown. List and unread-count are separate REST
 * queries (matching the backend's own split), kept in sync with each other through
 * direct cache writes on every mutation — never a refetch — so marking a notification
 * read never causes a visible reload. The list only ever fetches unread notifications:
 * once one is read, it's removed from the cache rather than shown dimmed. The live
 * stream (useNotificationStream) writes into the same two cache entries for the
 * real-time path.
 */
function useNotifications() {
  const queryClient = useQueryClient()

  const listQuery = useQuery({
    queryKey: notificationsListQueryKey,
    queryFn: () => listNotifications(true),
  })
  const unreadCountQuery = useQuery({
    queryKey: notificationsUnreadCountQueryKey,
    queryFn: () => countUnreadNotifications(),
  })

  const markReadMutation = useMutation({
    mutationFn: (notificationId: string) => markNotificationRead(notificationId),
    onSuccess: (updated) => applyNotificationRead(queryClient, updated),
  })

  const markAllReadMutation = useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: () => {
      queryClient.setQueryData<NotificationResponse[]>(notificationsListQueryKey, [])
      queryClient.setQueryData(notificationsUnreadCountQueryKey, 0)
    },
  })

  return {
    notifications: listQuery.data ?? [],
    isLoading: listQuery.isPending,
    unreadCount: unreadCountQuery.data ?? 0,
    markRead: (notificationId: string) => markReadMutation.mutate(notificationId),
    markAllRead: () => markAllReadMutation.mutate(),
    isMarkingAllRead: markAllReadMutation.isPending,
  }
}

export { useNotifications, applyNotificationRead, notificationsListQueryKey, notificationsUnreadCountQueryKey }
