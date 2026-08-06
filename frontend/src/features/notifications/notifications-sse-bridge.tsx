"use client"

import { useNotificationStream } from "./use-notification-stream"

/**
 * Mounted once near the app root (see AppProviders), same shape as AuthTokenBridge /
 * AuthFailureBridge — a null-rendering component whose only job is running an effect
 * for its whole lifetime.
 */
function NotificationsSseBridge(): null {
  useNotificationStream()
  return null
}

export { NotificationsSseBridge }
