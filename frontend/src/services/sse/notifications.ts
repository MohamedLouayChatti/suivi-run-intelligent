import { API_BASE_URL } from "@/services/api/client"
import { getAuthToken } from "@/lib/auth"
import type { NotificationResponse } from "@/services/api/notifications"

import { connectSse } from "./client"

/**
 * Live notification stream (GET /notifications/stream, scoped to the connected user
 * server-side). Backend emits one `event: notification` per new notification, JSON-encoded
 * NotificationResponse as `data`. Returns a `close()` function — callers must invoke it on
 * unmount/sign-out to stop the reconnect loop.
 */
function connectToNotificationStream(
  onNotification: (notification: NotificationResponse) => void,
  onConnectionChange?: (connected: boolean) => void,
): () => void {
  return connectSse({
    buildUrl: () => `${API_BASE_URL}/notifications/stream`,
    getAuthToken,
    onConnectionChange,
    onEvent: (event) => {
      if (event.event !== "notification") return
      try {
        onNotification(JSON.parse(event.data) as NotificationResponse)
      } catch {
        // Malformed event payload — drop it rather than crash the stream loop.
      }
    },
  })
}

export { connectToNotificationStream }
