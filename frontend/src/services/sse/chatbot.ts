import { getAuthToken } from "@/lib/auth"
import { API_BASE_URL } from "@/services/api/client"
import type { MessageResponse } from "@/services/api/chatbot"

import { connectSse } from "./client"

interface MessageDeltaEvent {
  content: string
}

interface ToolCallEvent {
  name: string
  status: "started" | "completed" | "failed"
}

interface RunFailedEvent {
  run_id: string
  failure_reason: string
}

/**
 * The generated title of the conversation this run belongs to. The one event on this stream that
 * is not about the run: naming a conversation is its own background job, started by the same
 * request and finished independently, and it rides this connection because the client already
 * holds it. Not terminal, and not guaranteed — a title generated after the run resolves finds the
 * stream closed, which is why the conversation list is still what reconciles it.
 */
interface ConversationTitleEvent {
  conversation_id: string
  title: string
}

interface AgentRunStreamHandlers {
  onDelta: (event: MessageDeltaEvent) => void
  onToolCall?: (event: ToolCallEvent) => void
  onComplete: (message: MessageResponse) => void
  onFailed: (event: RunFailedEvent) => void
  onTitle?: (event: ConversationTitleEvent) => void
  onConnectionChange?: (connected: boolean) => void
}

/**
 * Live delivery for one agent run (GET /conversational-assistant/runs/{run_id}/stream).
 * Emits `message_delta`/`tool_call` while the run is in flight, then exactly one of
 * `message_complete`/`run_failed` before the backend closes the stream — a run resolves once,
 * unlike the open-ended notification feed. `conversation_title` may also arrive at any point
 * before that terminal event, from a job that is not the run (see ConversationTitleEvent).
 * Returns a `close()` function; callers should invoke it
 * once a terminal event has been handled (or on unmount), so the reconnect loop in `connectSse`
 * does not keep retrying a run that has already resolved.
 */
function connectToAgentRunStream(runId: string, handlers: AgentRunStreamHandlers): () => void {
  return connectSse({
    buildUrl: () => `${API_BASE_URL}/conversational-assistant/runs/${runId}/stream`,
    getAuthToken,
    onConnectionChange: handlers.onConnectionChange,
    onEvent: (event) => {
      try {
        switch (event.event) {
          case "message_delta":
            handlers.onDelta(JSON.parse(event.data) as MessageDeltaEvent)
            return
          case "tool_call":
            handlers.onToolCall?.(JSON.parse(event.data) as ToolCallEvent)
            return
          case "message_complete":
            handlers.onComplete(JSON.parse(event.data) as MessageResponse)
            return
          case "run_failed":
            handlers.onFailed(JSON.parse(event.data) as RunFailedEvent)
            return
          case "conversation_title":
            handlers.onTitle?.(JSON.parse(event.data) as ConversationTitleEvent)
            return
          default:
            return
        }
      } catch {
        // Malformed event payload — drop it rather than crash the stream loop.
      }
    },
  })
}

export { connectToAgentRunStream }
export type {
  AgentRunStreamHandlers,
  MessageDeltaEvent,
  ToolCallEvent,
  RunFailedEvent,
  ConversationTitleEvent,
}
