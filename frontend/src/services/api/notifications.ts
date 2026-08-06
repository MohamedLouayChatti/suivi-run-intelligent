import type { components } from "@/types/api"

import { httpClient } from "./client"

type NotificationResponse = components["schemas"]["NotificationResponse"]
type UnreadCountResponse = components["schemas"]["UnreadCountResponse"]
type MarkAllReadResponse = components["schemas"]["MarkAllReadResponse"]

async function listNotifications(pageSize = 50): Promise<NotificationResponse[]> {
  const { data } = await httpClient.get<NotificationResponse[]>("/notifications", {
    params: { page: 1, page_size: pageSize },
  })
  return data
}

async function countUnreadNotifications(): Promise<number> {
  const { data } = await httpClient.get<UnreadCountResponse>("/notifications/unread-count")
  return data.count
}

async function markNotificationRead(notificationId: string): Promise<NotificationResponse> {
  const { data } = await httpClient.post<NotificationResponse>(`/notifications/${notificationId}/read`)
  return data
}

async function markAllNotificationsRead(): Promise<number> {
  const { data } = await httpClient.post<MarkAllReadResponse>("/notifications/read-all")
  return data.marked_read
}

export { listNotifications, countUnreadNotifications, markNotificationRead, markAllNotificationsRead }
export type { NotificationResponse }
