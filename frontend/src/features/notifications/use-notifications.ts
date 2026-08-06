"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

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
 * Backs the notification bell dropdown. List and unread-count are separate REST
 * queries (matching the backend's own split), kept in sync with each other through
 * direct cache writes on every mutation — never a refetch — so marking a notification
 * read never causes a visible reload. The live stream (useNotificationStream) writes
 * into the same two cache entries for the real-time path.
 */
function useNotifications() {
  const queryClient = useQueryClient()

  const listQuery = useQuery({
    queryKey: notificationsListQueryKey,
    queryFn: () => listNotifications(),
  })
  const unreadCountQuery = useQuery({
    queryKey: notificationsUnreadCountQueryKey,
    queryFn: () => countUnreadNotifications(),
  })

  const markReadMutation = useMutation({
    mutationFn: (notificationId: string) => markNotificationRead(notificationId),
    onSuccess: (updated) => {
      let wasUnread = false
      queryClient.setQueryData<NotificationResponse[]>(notificationsListQueryKey, (current) => {
        if (!current) return current
        return current.map((n) => {
          if (n.id !== updated.id) return n
          wasUnread = n.read_at === null
          return updated
        })
      })
      if (wasUnread) {
        queryClient.setQueryData<number>(notificationsUnreadCountQueryKey, (count) => Math.max(0, (count ?? 1) - 1))
      }
    },
  })

  const markAllReadMutation = useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: () => {
      const now = new Date().toISOString()
      queryClient.setQueryData<NotificationResponse[]>(notificationsListQueryKey, (current) =>
        current?.map((n) => (n.read_at ? n : { ...n, read_at: now })),
      )
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

export { useNotifications, notificationsListQueryKey, notificationsUnreadCountQueryKey }
