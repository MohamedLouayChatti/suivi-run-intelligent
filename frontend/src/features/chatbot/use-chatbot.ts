"use client"

import { useEffect, useRef, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"

import type { ChatMessage } from "@/features/chatbot/types"
import {
  createConversation,
  getConversationMessages,
  listConversations,
  sendMessage as sendMessageRequest,
  type MessageResponse,
  type RunSummaryResponse,
} from "@/services/api/chatbot"
import { connectToAgentRunStream } from "@/services/sse/chatbot"

const chatbotConversationsQueryKey = ["chatbot", "conversations"] as const
const GENERIC_SEND_ERROR = "Une erreur est survenue. Veuillez réessayer."

function toChatMessage(message: MessageResponse): ChatMessage {
  return { id: message.id, role: message.role, content: message.content }
}

/**
 * Real chat loop for the Chatbot page, backed by the conversational_assistant module and
 * streamed via SSE. A conversation is created lazily on the first message sent. Picking an
 * existing one from ConversationsPanel loads its history and reconciles whatever the latest run
 * was doing when the page was last open — GET .../messages' `latest_run` is the catch-up path a
 * client that missed (or never opened) the SSE stream relies on: PENDING/RUNNING re-opens the
 * stream at that run, FAILED replays the same failure bubble the live path would have shown.
 *
 * `initialConversationId` is the one another page can ask for (the Dashboard's "Reprendre une
 * conversation"), opened once on mount and then forgotten — the URL is not kept in step with the
 * panel afterwards, so it opens a conversation rather than naming the current one.
 */
function useChatbot(initialConversationId?: string | null) {
  const queryClient = useQueryClient()
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [isLoadingMessages, setIsLoadingMessages] = useState(false)
  const closeStreamRef = useRef<(() => void) | null>(null)
  const openedInitialConversationRef = useRef(false)

  const conversationsQuery = useQuery({
    queryKey: chatbotConversationsQueryKey,
    queryFn: () => listConversations(1, 50),
  })

  useEffect(() => {
    return () => {
      closeStreamRef.current?.()
    }
  }, [])

  function updateAssistantMessage(assistantMessageId: string, content: string) {
    setMessages((prev) =>
      prev.map((message) => (message.id === assistantMessageId ? { ...message, content } : message)),
    )
  }

  function finishStreaming() {
    setIsStreaming(false)
    closeStreamRef.current?.()
    closeStreamRef.current = null
  }

  function openStream(runId: string, assistantMessageId: string) {
    closeStreamRef.current?.()
    let content = ""
    closeStreamRef.current = connectToAgentRunStream(runId, {
      onDelta: (event) => {
        content += event.content
        updateAssistantMessage(assistantMessageId, content)
      },
      onComplete: (message) => {
        updateAssistantMessage(assistantMessageId, message.content)
        finishStreaming()
        queryClient.invalidateQueries({ queryKey: chatbotConversationsQueryKey })
      },
      onFailed: (event) => {
        updateAssistantMessage(assistantMessageId, event.failure_reason)
        finishStreaming()
      },
    })
  }

  // A run left PENDING/RUNNING/FAILED by the last page load, resolved here as of this fetch —
  // COMPLETED never reaches this: get_conversation_messages omits `latest_run` in that case since
  // the answer is already the last item in `messages`.
  function reconcileLatestRun(latestRun: RunSummaryResponse | null) {
    if (!latestRun) return
    if (latestRun.status === "PENDING" || latestRun.status === "RUNNING") {
      const assistantMessageId = crypto.randomUUID()
      setMessages((prev) => [...prev, { id: assistantMessageId, role: "ASSISTANT", content: "" }])
      setIsStreaming(true)
      openStream(latestRun.id, assistantMessageId)
    } else if (latestRun.status === "FAILED") {
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "ASSISTANT", content: latestRun.failure_reason ?? GENERIC_SEND_ERROR },
      ])
    }
  }

  async function ensureConversation(): Promise<string> {
    if (activeConversationId) return activeConversationId
    const conversation = await createConversation()
    setActiveConversationId(conversation.id)
    return conversation.id
  }

  async function sendMessage(content: string) {
    if (!content.trim() || isStreaming) return

    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "USER", content }])
    setIsStreaming(true)

    // The assistant bubble appears immediately, empty, and fills in live as message_delta
    // events arrive — there is no separate "thinking" placeholder outside `messages`.
    const assistantMessageId = crypto.randomUUID()
    setMessages((prev) => [...prev, { id: assistantMessageId, role: "ASSISTANT", content: "" }])

    try {
      const conversationId = await ensureConversation()
      const result = await sendMessageRequest(conversationId, content)
      queryClient.invalidateQueries({ queryKey: chatbotConversationsQueryKey })
      openStream(result.run_id, assistantMessageId)
    } catch {
      updateAssistantMessage(assistantMessageId, GENERIC_SEND_ERROR)
      setIsStreaming(false)
    }
  }

  async function selectConversation(conversationId: string) {
    if (conversationId === activeConversationId) return
    closeStreamRef.current?.()
    closeStreamRef.current = null
    setIsStreaming(false)
    setActiveConversationId(conversationId)
    setMessages([])
    setIsLoadingMessages(true)
    try {
      const result = await getConversationMessages(conversationId, 1, 200)
      setMessages(result.messages.items.map(toChatMessage))
      reconcileLatestRun(result.latest_run)
    } catch {
      setMessages([
        { id: crypto.randomUUID(), role: "ASSISTANT", content: "Impossible de charger cette conversation." },
      ])
    } finally {
      setIsLoadingMessages(false)
    }
  }

  // Deliberately keyed off nothing but the id, and guarded by a ref rather than by its dependency
  // list: `selectConversation` is rebuilt on every render, so listing it would reopen the
  // conversation continuously, and a user who then picked another one would be dragged back.
  useEffect(() => {
    if (openedInitialConversationRef.current || !initialConversationId) return
    openedInitialConversationRef.current = true
    void selectConversation(initialConversationId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialConversationId])

  function startNewConversation() {
    closeStreamRef.current?.()
    closeStreamRef.current = null
    setActiveConversationId(null)
    setMessages([])
    setIsStreaming(false)
  }

  return {
    messages,
    isStreaming,
    isLoadingMessages,
    sendMessage,
    startNewConversation,
    conversations: conversationsQuery.data?.items ?? [],
    isLoadingConversations: conversationsQuery.isPending,
    activeConversationId,
    selectConversation,
  }
}

export { useChatbot }
